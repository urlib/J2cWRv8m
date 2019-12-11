#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   自动部署网站
#+--------------------------------------------------------------------

import public,json,os,time,sys,re,shutil
from BTPanel import session
class obj: id=0;
class plugin_deployment:
    __setupPath = 'data';
    __panelPath = os.getenv("BT_PANEL")
    logPath = 'data/deployment_speed.json'
    __tmp = os.getenv("BT_PANEL") +'/temp'
    timeoutCount = 0;
    oldTime = 0;
    
    #获取列表
    def GetList(self,get):
        self.GetCloudList(get);
        jsonFile = self.__panelPath + '/data/deployment_list.json';
        if not os.path.exists(jsonFile): return public.returnMsg(False,'配置文件不存在!');
        data = {}
        data = self.get_input_list(json.loads(public.readFile(jsonFile)));
            
        if not hasattr(get,'type'): 
            get.type = 0;
        else:
            get.type = int(get.type)
        if not hasattr(get,'search'): 
            search = None
            m = 0
        else:
            if sys.version_info[0] == 2:
                search = get.search.encode('utf-8').lower();
            else:
                search = get.search.lower();
            m = 1
            
        tmp = [];
        for d in data['list']:
            i=0;
            if get.type > 0:
                if get.type == d['type']: i+=1
            else:
                i+=1
            if search:
                if d['name'].lower().find(search) != -1: i+=1;
                if d['title'].lower().find(search) != -1: i+=1;
                if d['ps'].lower().find(search) != -1: i+=1;
                if get.type > 0 and get.type != d['type']: i -= 1;

            if i>m:
                del(d['versions'][0]['download'])
                del(d['versions'][0]['md5'])
                d = self.get_icon(d)
                tmp.append(d);
            
        data['list'] = tmp;
        return data;

    #获取图标
    def get_icon(self,pinfo):
        path = self.__panelPath + '/BTPanel/static/img/dep_ico'
        if not os.path.exists(path): os.makedirs(path,384)
        filename = path + '/' + pinfo['name'] + '.png'
        m_uri = pinfo['min_image']
        pinfo['min_image'] = '/static/img/dep_ico/' + pinfo['name'] + '.png'
        if os.path.exists(filename): 
            if os.path.getsize(filename) > 1024: return pinfo
        public.downloadFile(public.GetConfigValue('home') + m_uri,filename)
        return pinfo
    
    #获取插件列表
    def GetDepList(self,get):
        jsonFile = self.__setupPath + '/deployment_list.json';
        if not os.path.exists(jsonFile): return public.returnMsg(False,'配置文件不存在!');
        data = {}
        data = json.loads(public.readFile(jsonFile));
        return self.get_input_list(data);

    #获取本地导入的插件
    def get_input_list(self,data):
        try:
            jsonFile = self.__setupPath + '/deployment_list_other.json';
            if not os.path.exists(jsonFile): return data
            i_data = json.loads(public.readFile(jsonFile))
            for d in i_data:
                data['list'].append(d)
            return data
        except:return data
    
    #从云端获取列表
    def GetCloudList(self,get):
        try:
            jsonFile = self.__setupPath + '/deployment_list.json';
            if not 'package' in session or not os.path.exists(jsonFile) or hasattr(get,'force'):
                downloadUrl = public.GetConfigValue('home') + '/api/panel/get_deplist';
                tmp = json.loads(public.httpGet(downloadUrl,3));
                if not tmp: return public.returnMsg(False,'从云端获取失败!');
                public.writeFile(jsonFile,json.dumps(tmp));
                session['package'] = True
                return public.returnMsg(True,'更新成功!');
            return public.returnMsg(True,'无需更新!');
        except:
            return public.returnMsg(False,'从云端获取失败!');
        
        
    
    #导入程序包
    def AddPackage(self,get):
        jsonFile = self.__setupPath + '/deployment_list_other.json';
        if not os.path.exists(jsonFile):
            public.writeFile(jsonFile,'[]')
        pinfo = {}
        pinfo['name'] = get.name;
        pinfo['title'] = get.title;
        pinfo['version'] = get.version;
        pinfo['php'] = get.php;
        pinfo['ps'] = get.ps;
        pinfo['official'] = '#'
        pinfo['sort'] = 1000;
        pinfo['min_image'] = ''
        pinfo['id'] = 0
        pinfo['type'] = 100
        pinfo['enable_functions'] = get.enable_functions
        pinfo['author'] = '本地导入'
        from werkzeug.utils import secure_filename
        from flask import request
        f = request.files['dep_zip']
        s_path = self.__panelPath + '/package'
        if not os.path.exists(s_path): os.makedirs(s_path,384)
        s_file = s_path + '/' + pinfo['name'] + '.zip'
        if os.path.exists(s_file): os.remove(s_file)
        f.save(s_file)
        os.chmod(s_file,384)
        pinfo['versions'] = []
        version = {"cpu_limit": 1,
                "dependnet": "",
                "m_version":pinfo['version'],
                "mem_limit": 32,
                "os_limit": 0,
                "size": os.path.getsize(s_file),
                "version": "0",
                "download":"",
                "version_msg": "测试2"}
        version['md5'] = self.GetFileMd5(s_file)
        pinfo['versions'].append(version)
        data = json.loads(public.readFile(jsonFile));
        is_exists = False
        for i in range(len(data)):
            if data[i]['name'] == pinfo['name']: 
                data[i] = pinfo
                is_exists = True

        if not is_exists: data.append(pinfo);

        public.writeFile(jsonFile,json.dumps(data));
        return public.returnMsg(True,'导入成功!');

    #取本地包信息
    def GetPackageOther(self,get):
        p_name = get.p_name
        jsonFile = self.__setupPath + '/deployment_list_other.json';
        if not os.path.exists(jsonFile): public.returnMsg(False,'没有找到[%s]' % p_name)
        data = json.loads(public.readFile(jsonFile));        
        for i in range(len(data)):
            if data[i]['name'] == p_name: return data[i]
        return public.returnMsg(False,'没有找到[%s]' % p_name)
                
    
    #删除程序包
    def DelPackage(self,get):
        jsonFile = self.__setupPath + '/deployment_list_other.json';
        if not os.path.exists(jsonFile): return public.returnMsg(False,'配置文件不存在!');
        
        data = {}
        data = json.loads(public.readFile(jsonFile));
        
        tmp = [];
        for d in data:
            if d['name'] == get.dname: 
                s_file = self.__panelPath + '/package/' + d['name'] + '.zip'
                if os.path.exists(s_file): os.remove(s_file)
                continue;
            tmp.append(d);
        
        data = tmp;
        public.writeFile(jsonFile,json.dumps(data));
        return public.returnMsg(True,'删除成功!');
    
    #下载文件
    def DownloadFile(self,url,filename):
        try:
            path = os.path.dirname(filename)
            if not os.path.exists(path): os.makedirs(path)
            import urllib,socket
            socket.setdefaulttimeout(10)
            self.pre = 0;
            self.oldTime = time.time();
            if sys.version_info[0] == 2:
                urllib.urlretrieve(url,filename=filename,reporthook= self.DownloadHook)
            else:
                urllib.request.urlretrieve(url,filename=filename,reporthook= self.DownloadHook)
            self.WriteLogs(json.dumps({'name':'下载文件','total':0,'used':0,'pre':0,'speed':0}));
        except:
            if self.timeoutCount > 5: return;
            self.timeoutCount += 1
            time.sleep(5)
            self.DownloadFile(url,filename)
            
    #下载文件进度回调  
    def DownloadHook(self,count, blockSize, totalSize):
        used = count * blockSize
        pre1 = int((100.0 * used / totalSize))
        if self.pre != pre1:
            dspeed = used / (time.time() - self.oldTime);
            speed = {'name':'下载文件','total':totalSize,'used':used,'pre':self.pre,'speed':dspeed}
            self.WriteLogs(json.dumps(speed))
            self.pre = pre1
    
    #写输出日志
    def WriteLogs(self,logMsg):
        fp = open(self.logPath,'w+');
        fp.write(logMsg)
        fp.close()
    
    #一键安装网站程序
    #param string name 程序名称
    #param string site_name 网站名称
    #param string php_version PHP版本
    def SetupPackage(self,get):
        name = get.dname
        site_name = get.site_name;
        php_version = get.php_version;
        #取基础信息
        find = public.M('sites').where('name=?',(site_name,)).field('id,path,name').find();
        if not find:
            return public.returnMsg(False,'指定网站不存在!')
        path = find['path'];
        if path.replace('//','/') == '/': return public.returnMsg(False,'危险的网站根目录!')
        
        #获取包信息
        pinfo = self.GetPackageInfo(name);
        if not pinfo: return public.returnMsg(False,'指定软件包不存在1!');
            
        id = pinfo['id']
        if not pinfo: return public.returnMsg(False,'指定软件包不存在2!');
        
        #检查本地包
        self.WriteLogs(json.dumps({'name':'正在校验软件包...','total':0,'used':0,'pre':0,'speed':0}));
        pack_path = self.__panelPath + '/package'
        if not os.path.exists(pack_path): os.makedirs(pack_path,384)
        packageZip =  pack_path + '/'+ name + '.zip';
        isDownload = False;
        if os.path.exists(packageZip):
            md5str = self.GetFileMd5(packageZip);
            if md5str != pinfo['versions'][0]['md5']: isDownload = True;
        else:
            isDownload = True;
            
        #下载文件
        if isDownload:
            self.WriteLogs(json.dumps({'name':'正在下载文件 ...','total':0,'used':0,'pre':0,'speed':0}));
            if pinfo['versions'][0]['download']: self.DownloadFile(public.GetConfigValue('home') + '/api/Pluginother/get_file?fname=' + pinfo['versions'][0]['download'], packageZip);

        if not os.path.exists(packageZip): return public.returnMsg(False,'文件下载失败!' + packageZip);

        pinfo = self.set_temp_file(packageZip,path)
        if not pinfo: return public.returnMsg(False,'在安装包中找不到【宝塔自动部署配置文件】')
                
        #安装PHP扩展
        self.WriteLogs(json.dumps({'name':'安装必要的PHP扩展','total':0,'used':0,'pre':0,'speed':0}));
        import files
        mfile = files.files();
        pinfo['php_ext'] = pinfo['php_ext'].strip().split(',')
        for ext in pinfo['php_ext']:
            if ext == 'pathinfo': 
                import config
                con = config.config();
                get.version = php_version;
                get.type = 'on';
                con.setPathInfo(get);
            else:
                get.name = ext
                get.version = php_version
                get.type = '1';
                mfile.InstallSoft(get);
                
        #解禁PHP函数
        if 'enable_functions' in pinfo:
            try:
                php_f = public.GetConfigValue('setup_path') + '/php/' + php_version + '/php.ini'
                php_c = public.readFile(php_f)
                rep = "disable_functions\s*=\s{0,1}(.*)\n"
                tmp = re.search(rep,php_c).groups();
                disable_functions = tmp[0].split(',');
                for fun in pinfo['enable_functions']:
                    fun = fun.strip()
                    if fun in disable_functions: disable_functions.remove(fun)
                disable_functions = ','.join(disable_functions)
                php_c = re.sub(rep, 'disable_functions = ' + disable_functions + "\n", php_c);
                public.writeFile(php_f,php_c)
                public.phpReload(php_version)
            except:pass

        import panelSite;
        siteObj = panelSite.panelSite();

        #写伪静态
        self.WriteLogs(json.dumps({'name':'设置伪静态','total':0,'used':0,'pre':0,'speed':0}));
        webserver = public.get_webserver()
        tmp_data = None
        if webserver == 'iis':
            tmp_data = public.readFile(path + '/iis.rewrite')
        elif webserver == 'nginx':
            tmp_data = public.readFile(path + '/nginx.rewrite')
            
        if tmp_data:
            mobj = obj();
            mobj.siteName = site_name
            mobj.data = tmp_data
            siteObj.SetSiteRewrite(mobj)

        #删除多余文件
        rm_file = path + '/index.html'
        if os.path.exists(rm_file): 
            rm_file_body = public.readFile(rm_file)
            if rm_file_body.find('panel-heading') != -1: os.remove(rm_file)
        
        #设置运行目录
        self.WriteLogs(json.dumps({'name':'设置运行目录','total':0,'used':0,'pre':0,'speed':0}));
        if pinfo['run_path'] != '/':           
            mobj = obj();
            mobj.id = find['id'];
            mobj.runPath = pinfo['run_path'];
            siteObj.SetSiteRunPath(mobj);
            
        #导入数据
        self.WriteLogs(json.dumps({'name':'导入数据库','total':0,'used':0,'pre':0,'speed':0}));
        if os.path.exists(path+'/import.sql'):
            databaseInfo = public.M('databases').where('pid=?',(find['id'],)).field('username,password').find();
            if databaseInfo:                
                import database
                sql_obj = database.database()
                sobj = obj();
                sobj.name = databaseInfo['username']
                sobj.file = path + '/import.sql'              
                sql_obj.InputSql(sobj)

                siteConfigFile = path + '/' + pinfo['db_config'].replace('//','/');
                if os.path.exists(siteConfigFile):
                    siteConfig = public.readFile(siteConfigFile)
                    siteConfig = siteConfig.replace('BT_DB_USERNAME',databaseInfo['username'])
                    siteConfig = siteConfig.replace('BT_DB_PASSWORD',databaseInfo['password'])
                    siteConfig = siteConfig.replace('BT_DB_NAME',databaseInfo['username'])
                    public.writeFile(siteConfigFile,siteConfig)

        #清理文件和目录
        self.WriteLogs(json.dumps({'name':'清理多余的文件','total':0,'used':0,'pre':0,'speed':0}));
        for f_path in pinfo['remove_file']:
            filename = (path + '/' + f_path).replace('//','/')
            if os.path.exists(filename):
                if not os.path.isdir(filename):                  
                    os.remove(filename)
                else:
                    import shutil
                    shutil.rmtree(filename,True)                
        public.serviceReload();
        if id: self.depTotal(id);
        self.WriteLogs(json.dumps({'name':'准备部署','total':0,'used':0,'pre':0,'speed':0}));
        return public.returnMsg(True,pinfo);


    #处理临时文件
    def set_temp_file(self,filename,path):               
        self.clear_dir(self.__tmp)
        self.WriteLogs(json.dumps({'name':'正在解压软件包...','total':0,'used':0,'pre':0,'speed':0}));
      
        #解压
        try:
            import zipfile
            zip_file = zipfile.ZipFile(filename)  
            for names in zip_file.namelist():              
                zip_file.extract(names,self.__tmp)            
            zip_file.close()
        except : return None

        auto_config = 'auto_install.json'
        p_info = self.__tmp + '/' + auto_config
        p_tmp = self.__tmp
        p_config = None
        if not os.path.exists(p_info):
            d_path = None
            for df in os.walk(self.__tmp):
                if len(df[2]) < 3: continue
                if not auto_config in df[2]: continue
                if not os.path.exists(df[0] + '/' + auto_config): continue
                d_path = df[0]
            if d_path: 
                tmp_path = d_path
                auto_file = tmp_path + '/' + auto_config
                if os.path.exists(auto_file):
                    p_info = auto_file
                    p_tmp = tmp_path
        if os.path.exists(p_info):
            try:
                p_config = json.loads(public.readFile(p_info))
                os.remove(p_info)
                i_ndex_html = path + '/index.html'
                if os.path.exists(i_ndex_html): os.remove(i_ndex_html)
                os.system("xcopy /s /c /e /y /r %s %s" % (public.to_path(p_tmp),public.to_path(path))) 
            except: pass
        self.clear_dir(self.__tmp)
        return p_config
                
    
    #提交安装统计
    def depTotal(self,id):
        import panelAuth
        p = panelAuth.panelAuth()
        pdata = p.create_serverid(None);
        pdata['pid'] = id;
        p_url = public.GetConfigValue('home') + '/api/pluginother/create_order_okey'
        public.httpPost(p_url,pdata)
    
    #获取进度
    def GetSpeed(self,get):
        try:
            if not os.path.exists(self.logPath): return public.returnMsg(False,'当前没有部署任务!');
            return json.loads(public.readFile(self.logPath));
        except:
            return {'name':'准备部署','total':0,'used':0,'pre':0,'speed':0}
     
    #获取包信息
    def GetPackageInfo(self,name):
        data = self.GetDepList(None);
        if not data: return False;
        for info in data['list']:
            if info['name'] == name:
                return info;
        return False;
    
    #检查指定包是否存在
    def CheckPackageExists(self,name):
        data = self.GetDepList(None);
        if not data: return False;
        for info in data['list']:
            if info['name'] == name: return True;
        
        return False;
    
    #文件的MD5值
    def GetFileMd5(self,filename):
        if not os.path.isfile(filename): return False;
        import hashlib;
        myhash = hashlib.md5()
        f = open(filename,'rb')
        while True:
            b = f.read(8096)
            if not b :
                break
            myhash.update(b)
        f.close()
        return myhash.hexdigest();
    
    #获取站点标识
    def GetSiteId(self,get):
        return public.M('sites').where('name=?',(get.webname,)).getField('id');
    
    #清空目录
    def clear_dir(self,path):
        try:
            if os.path.exists(path):
                shutil.rmtree(path,True)
            os.makedirs(path);
        except :pass
