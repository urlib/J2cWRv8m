#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 邹浩文 <627622230@qq.com>
#-------------------------------------------------------------------

#------------------------------
# 站点目录密码保护
#------------------------------
import public,re,os,json,shutil

class SiteDirAuth:
    webserver = None

    # 取目录加密状态
    def __init__(self):
        self.webserver = public.get_webserver()
        self.setup_path = public.GetConfigValue('setup_path')
        self.conf_file = self.setup_path + "/panel/data/site_dir_auth.json"

    #获取网站配置文件路径
    def get_conf_path(self,siteName):
         path = self.setup_path
         if self.webserver == 'apache':
             path  = path + '/apache/conf/vhost/' + siteName + '.conf'
             return path
         elif self.webserver == 'nginx':
             path  = path + '/nginx/conf/vhost/' + siteName + '.conf'
             return path
         return None


    #授权目录
    def get_auth_path(self,siteName):
        path = self.setup_path
        if self.webserver == 'apache':
            path  = path + '/apache/conf/dir_auth/' + siteName
            if not os.path.exists(path): os.makedirs(path)
            return path
        elif self.webserver == 'nginx':
            path  = path + '/nginx/conf/dir_auth/' + siteName
            if not os.path.exists(path): os.makedirs(path)
            return path
        return None

    # 读取配置
    def _read_conf(self,siteName):
        spath = 'data/conf/' + siteName
        if not os.path.exists(spath): os.makedirs(spath)
        
        auth_file = spath + '/dir_auth.json'
        conf = None
        if os.path.exists(auth_file):            
            conf = public.readFile(auth_file)
            conf = json.loads(conf)
        return conf

    #写入配置
    def _write_conf(self,siteName,conf):
        spath = 'data/conf/' + siteName
        if not os.path.exists(spath): os.makedirs(spath)
        auth_file = spath + '/dir_auth.json'
        public.writeFile(auth_file,json.dumps(conf))

    # 设置目录加密
    def set_dir_auth(self,get):

        name = get.name
        site_dir = get.site_dir

        if not hasattr(get,'password') or not get.password: return public.returnMsg(False, '请输入账号或密码')
        if not hasattr(get,'site_dir')  or not get.site_dir: return public.returnMsg(False, '请输入需要保护的目录')
        if  not hasattr(get,'name')  or not get.name: return public.returnMsg(False, '请输入名称')

        if site_dir[0] == "/":
            site_dir = site_dir[1:]
            if site_dir and site_dir[-1] == "/":
                site_dir = site_dir[:-1]

        site_info = self.get_site_info(get.id)
        if not site_info: return public.returnMsg(False, '参数传递错误.')

        data = self._read_conf(site_info["site_name"])
        if data and get.name in data:
            return public.returnMsg(False, '名称传递重复，请重新输入.')

        auth_path = self.get_auth_path(site_info["site_name"])
        public.writeFile(auth_path + '/' + name + '.pass'  ,get.username + ":" + get.password)

        auth_file = auth_path + '/' + name + '.conf' 

        conf_path =  self.get_conf_path(site_info["site_name"])
        conf = public.readFile(conf_path)
        if self.webserver == 'nginx':     
            #配置主配置文件
            if not re.search('include\s+dir_auth.+;',conf):
                conf = re.sub('#REWRITE-END\s+','#REWRITE-END\n\n\t#目录保护\n\tinclude dir_auth/' + site_info["site_name"] + '/*.conf;\n\n\t',conf)
                public.writeFile(conf_path,conf)
            
            #认证配置文件
            sub_conf = '''	location ~* ^/%s* {
		auth_basic "Authorization";
		auth_basic_user_file dir_auth/%s/%s.pass;
	}''' % (site_dir,site_info["site_name"],name)

            public.writeFile(auth_path + '/' + name + '.conf',sub_conf)

        else:            
            #配置主配置文件
            if not re.search('IncludeOptional\s+conf/dir_auth.+;',conf):
                conf = re.sub('common\s+','common\n\n\t\t#目录保护\n\t\tIncludeOptional conf/dir_auth/' + site_info["site_name"] + '/*.conf\n\n\t\t',conf)
                public.writeFile(conf_path,conf)

            #认证配置文件
            sub_conf = '''<Directory "%s/%s/">
    AuthType basic
    AuthName "Authorization"
    AuthUserFile conf/dir_auth/%s/%s.pass
    Require user %s
    SetOutputFilter DEFLATE
    Options FollowSymLinks
    AllowOverride All
    DirectoryIndex index.php index.html index.htm default.php default.html default.htm
</Directory>''' % (site_info['site_path'],site_dir,site_info["site_name"],name,get.username)

            public.writeFile(auth_path + '/' + name + '.conf',sub_conf)

        isError = public.checkWebConfig()              
        if (isError != True):
            os.remove(auth_file)  
            return public.returnMsg(False, 'ERROR: %s<br><a style="color:red;">' % public.GetMsg("CONFIG_ERROR") + isError.replace("\n", '<br>') + '</a>')

        if not data: data = {}

        data[name] = {"name":name,"site_dir": '/' + site_dir,"auth_file":auth_file,'username':get.username,'password':get.password}      
        self._write_conf(site_info["site_name"],data)
        public.serviceReload()
        return public.returnMsg(True,"创建成功")

    # 获取站点名
    def get_site_info(self,id):
        data = public.M('sites').where('id=?', (id,)).field('name as site_name,path as site_path').find()  
        return data

    # 删除密码保护
    def delete_dir_auth(self,get):

        name = get.name
        site_info = self.get_site_info(get.id)
        site_name = site_info["site_name"]
        data = self._read_conf(site_name)
        del data[name]
        self._write_conf(site_name,data)

        auth_path = self.get_auth_path(site_name)
        
        if os.path.exists(auth_path + '/' + name + '.conf'): os.remove(auth_path + '/' + name + '.conf')
        if os.path.exists(auth_path + '/' + name + '.pass'): os.remove(auth_path + '/' + name + '.pass')

        public.serviceReload()
        return public.returnMsg(True,"删除成功")

    # 修改目录保护密码
    def modify_dir_auth_pass(self,get):
        name = get.name
        site_info = self.get_site_info(get.id)
        site_name = site_info["site_name"]
  
        auth_path = self.get_auth_path(site_name)
        public.writeFile(auth_path + '/' + name + '.pass'  ,get.username + ":" + get.password)
        
        data = self._read_conf(site_name)      
        data[name]['username'] = get.username;
        data[name]['password'] = get.password;
        self._write_conf(site_name,data)

        public.serviceReload()
        return public.returnMsg(True,"修改成功")

    # 获取目录保护列表
    def get_dir_auth(self,get):     
        data = []
        site_info = self.get_site_info(get.id)
        if site_info:            
            site_name = site_info["site_name"]
            conf = self._read_conf(site_name)
            if conf:
                for x in conf:
                    data.append(conf[x])
            return data
