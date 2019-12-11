#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

#------------------------------
# 网站管理类
#------------------------------
import io,re,public,os,sys,shutil,json,time,xmltodict
import xml.etree.ElementTree as ET
from xml.dom import minidom
from BTPanel import session 
from common import dict_obj
from flask import request
import site_dir_auth

import xml.etree.ElementTree as ET
class panelSite:
    siteName = None #网站名称
    sitePath = None #根目录
    sitePort = None #端口
    phpVersion = None #PHP版本
    setupPath = None #安装路径
    isWriteLogs = None #是否写日志
    serverType = None #web服务器类型
    is_ipv6 = False  #不支持IPV6

    conf_bak = None
    def __init__(self):
  
        ndb = public.M('sites').order("id desc").field('iid,name,path,status,ps,addtime,edate,type').select()
        if type(ndb) == str:
            public.M('sites').execute("alter TABLE sites add type TEXT DEFAULT PHP",());

        self.serverType = public.get_webserver()
        self.setupPath = public.GetConfigValue('setup_path')
        self.is_ipv6 = False
        self.conf_bak = 'data/backup_' + self.serverType + '.conf'
        if self.serverType == 'iis':            
            self._iis_root = os.getenv("SYSTEMDRIVE") + '\\Windows\\System32\\inetsrv'
            self._appcmd = self._iis_root + '\\appcmd.exe'            
        else:
            pass

    #添加网站
    def AddSite(self,get):  
        try:
            import json,files
            siteMenu = json.loads(get.webname)
            self.siteName     = self.ToPunycode(siteMenu['domain'].split(':')[0]);
            self.sitePath     = self.ToPunycodePath(self.GetPath(get.path.replace(' ',''))).strip();
            self.sitePort     = get.port.replace(' ','');
            type_id = 0
            if hasattr(get,'type_id'): type_id = get.type_id
    
            if self.sitePort == "": get.port = "80";
            if not public.checkPort(self.sitePort): return public.returnMsg(False,'SITE_ADD_ERR_PORT');
            
            if not public.check_win_path(self.sitePath): return public.returnMsg(False,'不能以磁盘作为网站目录，或网站目录不是有效的Windows路径格式，不能包含(: * ? " < > |)');

            if hasattr(get,'version'):
                self.phpVersion   = get.version.replace(' ','');
            else:
                self.phpVersion   = '00';

            domain = None
            if not files.files().CheckDir(self.sitePath): return public.returnMsg(False,'PATH_ERROR');
            if len(self.phpVersion) < 2: return public.returnMsg(False,'SITE_ADD_ERR_PHPEMPTY');
            reg = "^([\w\-\*]{1,100}\.){1,4}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$";
            if not re.match(reg, self.siteName): return public.returnMsg(False,'SITE_ADD_ERR_DOMAIN');
            if self.siteName.find('*') != -1: return public.returnMsg(False,'SITE_ADD_ERR_DOMAIN_TOW');
        
            if not domain: domain = self.siteName;

            time.sleep(0.01);
            #是否重复
            sql = public.M('sites');
            if sql.where("name=?",(self.siteName,)).count(): return public.returnMsg(False,'SITE_ADD_ERR_EXISTS');
            opid = public.M('domain').where("name=?",(self.siteName,)).getField('pid');
        
            if opid:
                if public.M('sites').where('id=?',(opid,)).count():
                    return public.returnMsg(False,'SITE_ADD_ERR_DOMAIN_EXISTS');
                public.M('domain').where('pid=?',(opid,)).delete();

            #创建根目录
            if not os.path.exists(self.sitePath): 
                os.makedirs(self.sitePath)
            if not os.path.exists(self.sitePath + '/.htaccess'):  public.writeFile(self.sitePath + '/.htaccess', ' ');

            if hasattr(get,'check_dir'):
                filesize =  public.get_path_size(self.sitePath)
                #大于2g 2147483648
                if filesize >= 2147483648:
                    return { 'status':False,'msg':'当前网站目录大小为：' + public.to_size(filesize) + '，设置目录权限将会耗费大量时间，是否继续创建网站？','code':'-2'}
            siteType = 'PHP'
            if hasattr(get,'type'): siteType = get.type
            siteObj = { 'siteName' : self.siteName ,'siteDomain': self.siteName ,'sitePort':self.sitePort,'sitePath':self.sitePath ,'phpVersion':self.phpVersion,'type':siteType }
            if self.serverType == 'iis':                        
                result = self.iisAdd(siteObj)
            elif self.serverType == 'apache':
                result = self.apacheAdd(siteObj)
            elif self.serverType == 'nginx':
                if re.match("\s", self.sitePath): 
                    return public.returnMsg(False,'网站目录不能带有空格.');
                result = self.nginxAdd(siteObj)
            else:
                return public.returnMsg(False,'未识别的web服务器');
                
            #检查处理结果
            if not result['status']: return result;
    
            #创建basedir
            self.DelUserInI(self.sitePath);
    
            #创建默认文档
            index = self.sitePath + '/index.html'
            if not os.path.exists(index):
                if not os.path.exists('data/defaultDoc.html'):
                    downurl = public.get_url()
                    public.downloadFile(downurl + '/win/panel/data/defaultDoc.html','data/defaultDoc.html')
                
                defaultHtml = public.readFile('data/defaultDoc.html')
                public.writeFile(index,defaultHtml)
        
            #创建自定义404页
            doc404 = self.sitePath + '/404.html'
            if not os.path.exists(doc404):
                if not os.path.exists('data/404.html'):
                    downurl = public.get_url()
                    public.downloadFile(downurl + '/win/panel/data/404.html','data/404.html')

                html404 = public.readFile('data/404.html')
                public.writeFile(doc404, html404);
      
            ps = get.ps
            #添加放行端口
            if self.sitePort != '80':
                import firewalls
                get.port = self.sitePort
                get.ps = self.siteName;
                firewalls.firewalls().AddAcceptPort(get);
        
            #写入数据库
            get.pid = sql.table('sites').add('name,path,status,ps,type_id,addtime,type',(self.siteName,self.sitePath,'1',ps,type_id,public.getDate(),siteType))
       
            #添加更多域名
            for domain in siteMenu['domainlist']:
                get.domain = domain
                get.webname = self.siteName
                get.id = str(get.pid)
                self.AddDomain(get)
        
            sql.table('domain').add('pid,name,port,addtime',(get.pid,self.siteName,self.sitePort,public.getDate()))
        
            data = {}
            data['siteStatus'] = True
            
            #添加FTP
            data['ftpStatus'] = False
            if get.ftp == 'true':
                import ftp
                get.ps = self.siteName
                result = ftp.ftp().AddUser(get)
                if result['status']: 
                    data['ftpStatus'] = True
                    data['ftpUser'] = get.ftp_username
                    data['ftpPass'] = get.ftp_password
        
            #添加数据库
            data['databaseStatus'] = False
            if get.sql == 'true' or get.sql =='MySQL' or get.sql == 'SQLServer':
                import database
                if len(get.datauser) > 16: get.datauser = get.datauser[:16]
                get.name = get.datauser
                get.db_user = get.datauser
                get.password = get.datapassword
                get.address = '127.0.0.1'
                get.ps = self.siteName
                get.dtype = get.sql
                result = database.database().AddDatabase(get)

                if result['status']: 
                    data['databaseStatus'] = True
                    data['databaseUser'] = get.datauser
                    data['databasePass'] = get.datapassword
     
            if self.serverType != 'iis':public.serviceReload()

            public.WriteLog('TYPE_SITE','SITE_ADD_SUCCESS',(self.siteName,))
            return data
        except Exception as ex:
            return public.returnMsg(False,str(ex))

    #删除网站
    def DeleteSite(self,get):
    
        id = get.id;
        siteName = get.webname;
        get.siteName = siteName    
        if self.serverType == 'iis':
            public.ExecShell(self._appcmd + ' delete site "' + siteName + '"')
            public.ExecShell(self._appcmd + ' delete apppool "' + siteName + '"')
        else:
            #删除配置文件
            confPath = self.get_conf_path(siteName)
            if os.path.exists(confPath): os.remove(confPath)
        
            dirs = ['redirect','proxy','rewrite']
            for filename in dirs:
                rpath = self.setupPath+'/'+ self.serverType +'/conf/'+ filename +'/'+ siteName
                if os.path.exists(rpath): shutil.rmtree(rpath)

        #删除根目录
        if hasattr(get,'path'):
            import files
            sitePath = public.M('sites').where("id=?",(id,)).getField('path');
            if sitePath and os.path.exists(sitePath):
                get.path = sitePath
                files.files().DeleteDir(get)        

        if self.serverType != 'iis':public.serviceReload()

        #从数据库删除
        public.M('sites').where("id=?",(id,)).delete();
        public.M('binding').where("pid=?",(id,)).delete();
        public.M('domain').where("pid=?",(id,)).delete();
        public.WriteLog('TYPE_SITE', "SITE_DEL_SUCCESS",(siteName,));
        
        #是否删除关联数据库
        if hasattr(get,'database'):
            find = public.M('databases').where("pid=?",(id,)).field('id,name').find()
            if find:
                import database
                get.name = find['name']
                get.id = find['id']
                database.database().DeleteDatabase(get)
        
        #是否删除关联FTP
        if hasattr(get,'ftp'):
            find = public.M('ftps').where("pid=?",(id,)).field('id,name').find()
            if find:
                import ftp
                get.username = find['name']
                get.id = find['id']
                ftp.ftp().DeleteUser(get)
            
        return public.returnMsg(True,'SITE_DEL_SUCCESS')

      #添加子目录绑定
    def AddDirBinding(self,get):
        import shutil
        id = get.id
        tmp = get.domain.split(':')
        domain = self.ToPunycode(tmp[0]);
        port = '80'
        if len(tmp) > 1: port = tmp[1];
        
        self.sitePort = port
        if not public.checkPort(self.sitePort): return public.returnMsg(False,'SITE_ADD_ERR_PORT');

        if not hasattr(get,'dirName'): public.returnMsg(False, 'DIR_EMPTY');
        dirName = get.dirName; 
        
        reg = "^([\w\-\*]{1,100}\.){1,4}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$";
        if not re.match(reg, domain): return public.returnMsg(False,'SITE_ADD_ERR_DOMAIN');
        
        siteInfo = public.M('sites').where("id=?",(id,)).field('id,path,name,type').find();
        webdir = siteInfo['path'] + '/' + dirName;
        sql = public.M('binding');
        if sql.where("domain=?",(domain,)).count() > 0: return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_EXISTS');
        if public.M('domain').where("name=?",(domain,)).count() > 0: return public.returnMsg(False, 'SITE_ADD_ERR_DOMAIN_EXISTS');
        
        get.siteName = siteInfo['name']
        self.siteName = siteInfo['name']
        phpVersion  = self.GetSitePHPVersion(get)
        if not phpVersion or not 'phpversion' in phpVersion: return public.returnMsg(False, '主站PHP版本获取失败.');
        
        siteObj = { 'siteName' : self.siteName + '_' + dirName,'siteDomain': domain ,'sitePort':port,'sitePath':webdir ,'phpVersion': phpVersion['phpversion'],'type':siteInfo['type'] }
        if self.serverType == 'iis':
            result = self.iisAdd(siteObj)
        elif self.serverType == 'apache':     
            self.siteName = self.siteName + '_' + dirName
            self.sitePath = webdir
            result = self.apacheAdd(siteObj)
        else:
            self.siteName = self.siteName + '_' + dirName
            self.sitePath = webdir
            result = self.nginxAdd(siteObj)

        if not result['status']: return result;

        #创建默认文档
        index = webdir + '/index.html'
        if not os.path.exists(index):
            defaultHtml = public.readFile('data/defaultDoc.html')
            public.writeFile(index,defaultHtml)

        public.M('binding').add('pid,domain,port,path,addtime',(id,domain,port,dirName,public.getDate()));
        
        if self.serverType != 'iis': public.serviceReload()
        public.WriteLog('TYPE_SITE', 'SITE_BINDING_ADD_SUCCESS',(siteInfo['name'],dirName,domain));
        return public.returnMsg(True, 'ADD_SUCCESS');

    #删除子目录绑定
    def DelDirBinding(self,get):
        id = get.id
        binding = public.M('binding').where("id=?",(id,)).field('id,pid,domain,path').find();
        siteFind = public.M('sites').where("id=?",(binding['pid'],)).field('id,name,path').find()
        
        if self.serverType == 'iis':
            import shutil
            webpath = siteFind['path'] + '/' + binding['path']
            path1 = webpath + '/web.config'
            path2 = webpath + '/web_config'
            if os.path.exists(path1):os.remove(path1)
            if os.path.exists(path2): shutil.rmtree(webpath + '/web_config')
            webname = binding['domain'] + '_' + binding['path']
                            
            public.ExecShell(self._appcmd + ' delete site "' + webname + '"')
            public.ExecShell(self._appcmd + ' delete apppool "' + webname + '"')

            webname = siteFind['name'] + '_' + binding['path']
            public.ExecShell(self._appcmd + ' delete site "' + webname + '"')
            public.ExecShell(self._appcmd + ' delete apppool "' + webname + '"')

        else:
            webname = binding['domain'] + '_' + binding['path']
            filename = self.get_conf_path(webname)
            if os.path.exists(filename): os.remove(filename)

            webname = siteFind['name'] + '_' + binding['path']
            filename = self.get_conf_path(webname)
            if os.path.exists(filename): os.remove(filename)

        public.M('binding').where("id=?",(id,)).delete();
        if self.serverType != 'iis':public.serviceReload()

        public.WriteLog('TYPE_SITE', 'SITE_BINDING_DEL_SUCCESS',(siteFind['name'],binding['path']));
        return public.returnMsg(True,'DEL_SUCCESS')

    #取子目录Rewrite
    def GetDirRewrite(self,get):
        id = get.id;
        find = public.M('binding').where("id=?",(id,)).field('id,pid,domain,path').find();
        site = public.M('sites').where("id=?",(find['pid'],)).field('id,name,path').find();
        
        data = {}
        data['status'] = False;

        if(self.serverType == 'iis'):
            new_get = dict_obj();
            new_get.siteName  = find['domain'] + '_' + find['path']

            data =  self.GetSiteRewrite(new_get)
        else:
            if(self.serverType == 'apache'):
                filename = site['path'] + '/' + find['path'] + '/.htaccess';
            else:
                filename = self.setupPath + '/nginx/conf/rewrite/'+ site['name'] + '_' + find['path'] + '.conf';

            if os.path.exists(filename):
                data['status'] = True;
                data['data'] = public.readFile(filename);
                data['filename'] = filename;
          
        data['rlist'] = []
        for ds in os.listdir('rewrite/' +self.serverType):
            if ds == 'list.txt': continue;
            data['rlist'].append(ds[0:len(ds)-5]);
        
        return data

    #添加apache端口
    def apacheAddPort(self,port):
     
        filename = self.setupPath+'/apache/conf/httpd.conf';
        if not os.path.exists(filename): return;
        allConf = public.readFile(filename);
        rep = "Listen\s+([0-9]+)\n";
        tmp = re.findall(rep,allConf);
        if not tmp: return False;
        for key in tmp:
            if key == port: return False
        
        listen = "\nListen "+tmp[0]
        listen_ipv6 = ''
        if self.is_ipv6: listen_ipv6 = "\nListen [::]:" + port
        allConf = allConf.replace(listen,listen + "\nListen " + port + listen_ipv6)
        public.writeFile(filename, allConf)
  
        return True
    

    #获取根目录列表
    def get_paths(self,path,list):
        try:
            path = os.path.dirname(path)
            if not path in list:
                list.append(path)
                self.get_paths(path,list)
        except :
            pass

    #递归设置目录权限
    def set_site_paths(self,user,access,path,level = True):
        try:
            import files
            file_obj =  files.files()
            get = dict_obj();
            get.user = user
            get.access = access
            if level:            
                get.level = '1'
            else:
                get.level = '0'
            flist = []
            self.get_paths(path,flist)
            for f in flist:    
                get.filename = f     
                file_obj.SetFileAccess(get)
        
            #设置当前目录权限
            get.access = 2032127
            get.level = '1'
            get.filename = path 
            file_obj.SetFileAccess(get)
        except :
            pass

    #添加到nginx
    def nginxAdd(self,siteObj):

        if not self.sitePort: 
            self.sitePort = siteObj['sitePort']
            self.siteName = siteObj['siteName']
            self.sitePath = siteObj['sitePath']

        listen_ipv6 = ''
        if self.is_ipv6: listen_ipv6 = "\n    listen [::]:%s;" % self.sitePort

        rpath = self.setupPath+'/nginx/conf/redirect/' + self.siteName
        if not os.path.exists(rpath): os.makedirs(rpath)
            
        ppath = self.setupPath+'/nginx/conf/proxy/'+self.siteName
        if not os.path.exists(ppath): os.makedirs(ppath)

        rpath = self.setupPath+'/nginx/conf/rewrite/'+self.siteName
        if not os.path.exists(rpath): os.makedirs(rpath)

        conf='''server 
{
    listen %s;%s
    server_name %s; 
    index index.php index.html index.htm default.php default.htm default.html;
    root %s;
		
	#START-ERROR-PAGE
	#error_page 403 /403.html;
	error_page 404 /404.html;
    #error_page 502 /502.html;
	#END-ERROR-PAGE
    
    #HTTP_TO_HTTPS_START
    #HTTP_TO_HTTPS_END

    #LIMIT_INFO_START
    #LIMIT_INFO_END

    #SSL-INFO-START
    #SSL-INFO-END
        
    #反代清理缓存配置
    location ~ /purge(/.*) {
        proxy_cache_purge cache_one $1$is_args$args;
    }
    #proxy 反向代理
    include proxy/%s/*.conf;

    #PHP-INFO-START 
    include php/%s.conf;
    #PHP-INFO-END
    
    #REWRITE-START
    include rewrite/%s/*.conf;
    #REWRITE-END

    #redirect 重定向
    include redirect/%s/*.conf;

    #禁止访问的文件或目录
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)
    {
        return 404;
    }
    
    #一键申请SSL证书验证目录相关设置
    location ~ \.well-known{
        allow all;
    }

	access_log  %s.log;
    error_log  %s.error.log;
}
''' % (siteObj['sitePort'],listen_ipv6,siteObj['siteName'],siteObj['sitePath'],siteObj['siteName'],siteObj['phpVersion'],siteObj['siteName'],siteObj['siteName'],public.GetConfigValue('logs_path')+'/'+siteObj['siteName'],public.GetConfigValue('logs_path')+'/'+siteObj['siteName'])
        
        #写配置文件
        filename = self.setupPath+'/nginx/conf/vhost/'+self.siteName+'.conf'     
        public.writeFile(filename,conf);

        get = dict_obj();
        get.siteName = siteObj['siteName']
        get.version = siteObj['phpVersion']
        self.SetPHPVersion(get)
   
        return public.returnMsg(True,'添加成功!');

    #添加到apache
    def apacheAdd(self,siteObj):
        try:
            import time
            listen = '';
    
            #兼容phpmyadmin
            if not self.sitePort: 
                self.sitePort = siteObj['sitePort']
                self.siteName = siteObj['siteName']
                self.sitePath = siteObj['sitePath']
         
            if self.sitePort != '80': self.apacheAddPort(self.sitePort);
            acc = public.md5(str(time.time()))[0:8];
           
            rpath = self.setupPath + '/apache/conf/redirect/' + self.siteName
            if not os.path.exists(rpath): os.makedirs(rpath)
            
            ppath = self.setupPath+'/apache/conf/proxy/'+self.siteName
            if not os.path.exists(ppath): os.makedirs(ppath)
           
            #遍历网站每层目录，设置读取权限，否则Apache无法启动
            self.set_site_paths('www',1179785,siteObj['sitePath'],False)
 
            conf ='''<VirtualHost *:%s>
        ServerAdmin webmaster@example.com
	    DocumentRoot "%s"
	    ServerAlias %s
        ErrorLog "%s-error.log"
        CustomLog "%s-access.log" common

        #redirect 重定向
        IncludeOptional conf/redirect/%s/*.conf

        #proxy 反向代理
        IncludeOptional conf/proxy/%s/*.conf

	    ErrorDocument 404 /404.html
	
	    #DENY FILES
	    <Files ~ (\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)$>
	       Order allow,deny
	       Deny from all
	    </Files>
	
	    #PHP
	    Include conf/php/00.conf
	
	    #PATH
	    <Directory "%s">
		    Options FollowSymLinks ExecCGI
		    AllowOverride All
		    Require all granted
		    DirectoryIndex index.php default.php index.html index.htm default.html default.htm
		
	    </Directory>
    </VirtualHost>
    ''' % (siteObj['sitePort'],siteObj['sitePath'],siteObj['siteDomain'],public.GetConfigValue('logs_path')+'/'+self.siteName,public.GetConfigValue('logs_path')+'/'+self.siteName,siteObj['siteName'],siteObj['siteName'],siteObj['sitePath'])
            
            htaccess = self.sitePath + '/.htaccess'
            if not os.path.exists(htaccess): public.writeFile(htaccess, ' ');

            filename = self.setupPath+'/apache/conf/vhost/'+self.siteName+'.conf'     
            public.writeFile(filename,conf)
            
            get = dict_obj();
            get.siteName = siteObj['siteName']
            get.version = siteObj['phpVersion']
            self.SetPHPVersion(get)

            return public.returnMsg(True,'添加成功!');
        except Exception as ex:       
            print(str(ex))
            return public.returnMsg(False,'SITE_ADD_ERR_WRITE');

    #iis添加网站
    def iisAdd(self,siteObj):      
        if self.CreatePool(siteObj['siteName']):
            try:     
                get = dict_obj();
                get.filename = siteObj['sitePath']
                get.user = siteObj['siteName']
                get.access = 2032127
                import files
                rRet = files.files().SetFileAccess(get)
                if rRet['status']:          
                    list = self.get_iis_sites()
                    if not siteObj['siteName'] in list.keys():
                        path = siteObj['sitePath'].replace('/','\\')
                   
                        public.ExecShell(self._appcmd + ' add site /name:"' + siteObj['siteName'] + '" /bindings:"http/*:' + siteObj['sitePort'] +':' + self.DePunycode(siteObj['siteDomain']) + '" /physicalPath:"' + path + '"')  
                        public.ExecShell(self._appcmd + ' set app "' + siteObj['siteName'] + '/" /applicationPool:"' + siteObj['siteName'] + '"') 

                        old_config_path = siteObj['sitePath'] + '/web.config'
                        if os.path.exists(old_config_path + '.backup'):
                            os.remove(old_config_path + '.backup')
                        if os.path.exists(old_config_path): os.rename(old_config_path,old_config_path + '.backup')
                        
                        self.init_iisSite_config(siteObj['sitePath'] + '/web.config')
 
                        get = dict_obj();
                        get.siteName = siteObj['siteName']
                        get.version = siteObj['phpVersion']
                        self.SetPHPVersion(get)
                        #if siteObj['type'] == 'PHP':                        
                        #    self.set_config_locking(get)
                        return public.returnMsg(True,'添加成功!');
                    return public.returnMsg(False,'IIS存在该站点，请手动删除后重新添加!');                
            except :
                return public.returnMsg(False,'网站目录权限设置失败,IIS需要给网站目录设置%s权限，请关闭安全软件的目录防护功能后重试.' % siteObj['siteName']);
        return public.returnMsg(False,'网站应用程序池创建失败!');

    #创建应用程序池
    def CreatePool(self,name,version = '2.0',pipemodel= 'Integrated'):
        nget = dict_obj();
        plist = self.get_iis_net_versions(nget)
        if len(plist) <= 0:
            os.system("C:\\WINDOWS\\Microsoft.NET\\Framework\\v2.0.50727\\aspnet_regiis.exe -i")
            os.system("C:\\WINDOWS\\Microsoft.NET\\Framework\\v4.0.30319\\aspnet_regiis.exe -i")
            plist = self.get_iis_net_versions(nget)

        if public.get_server_status('AppHostSvc')< 1: os.system("net start AppHostSvc")

        list = self.GetPoolList();
        if not name in list.keys():
            rRet = public.ExecShell(self._appcmd + ' add apppool /name:'+ name +' /managedRuntimeVersion:v' + plist[0] + ' /managedPipelineMode:' + pipemodel + ' /enable32BitAppOnWin64:true /failure.rapidFailProtection:false /queueLength:65535')            
            list = self.GetPoolList();
            if name in list.keys():
                return True
            return False
        return True
    
    #获取应用程序池列表
    def GetPoolList(self):       
        rRet = public.ExecShell(self._appcmd + ' list apppool',None,None,None,True)
        tmps = re.findall('APPPOOL\s+\"(.+)\".+:v([\d\.]+).+MgdMode:(\w+).+state:(\w+)',rRet[0])
        data = {}
        for item in tmps:
            if len(item) >= 4:
                pool = { 'name': item[0],'version':item[1],'type':item[2],'status':item[3] }
                data[item[0]] = pool;
        return data
    
    #获取应用程序池net版本
    def get_net_version_byaspp(self,get):
       #try:
        if self.serverType != 'iis': return public.returnMsg(False,'应用程序池仅支持IIS!');

        plist = self.GetPoolList()
        if not get.name in plist:  return public.returnMsg(False,'获取应用程序池信息失败!');
        
        data = plist[get.name]
        rRet = public.ExecShell(self._appcmd + ' list apppool %s /config:*' % get.name)

        #基础配置
        slist = ['queueLength','enable32BitAppOnWin64']
        for key1 in slist:
            tmp3 = re.search(key1 + '=\"(.*?)\"',rRet[0])
            if tmp3: data[key1] = tmp3.groups()[0] 

        #进程模型
        data['processModel'] = {}
        proList = ['maxProcesses','shutdownTimeLimit','startupTimeLimit','idleTimeout']
        for key5 in proList:
            tmp5 = re.search(key5 + '=\"(.*?)\"',rRet[0])
            if tmp5: 
                if key5 == 'maxProcesses':
                    data['processModel'][key5] = int(tmp5.groups()[0])
                else:
                    data['processModel'][key5] = public.time_to_int(tmp5.groups()[0])

        #进程回收
        data['periodicRestart'] = {}
        rlist = ['privateMemory','requests','time']
        for key1 in rlist:
            tmp3 = re.search(key1 + '=\"(.*?)\"',rRet[0])
            if tmp3: 
                if key1 == 'time':
                    data['periodicRestart'][key1] = public.time_to_int(tmp3.groups()[0]) 
                else:
                    data['periodicRestart'][key1] = tmp3.groups()[0] 
            
        #固定时间回收
        data['periodicRestart']['schedule'] = []
        tmps = re.findall("<add\s*value=\"(\d+:\d+:\d+)\"",rRet[0])
        for item in tmps: 
            data['periodicRestart']['schedule'].append(item)

        #故障防护
        data['failure'] = {}
        flist = ['rapidFailProtectionInterval','rapidFailProtectionMaxCrashes','rapidFailProtection','autoShutdownExe','autoShutdownParams']
        for key1 in flist:
            tmp3 = re.search(key1 + '=\"(.*?)\"',rRet[0])
            if tmp3: 
                if key1 == 'rapidFailProtectionInterval':        
                    data['failure'][key1] = public.time_to_int(tmp3.groups()[0]) / 60
                else:
                    data['failure'][key1] = tmp3.groups()[0] 
        
        data['failure']['failure_type'] = 'false'
        try:
            if data['failure']['autoShutdownParams'].find('start apppool') >=0:
                data['failure']['failure_type'] = 'start_pool'
            elif data['failure']['autoShutdownParams'].find('restart') >=0:
                 data['failure']['failure_type'] = 'restart_iis'
        except : pass
  
        return data
       #except :
       #     return public.returnMsg(False,'获取应用程序池信息失败!');

    #获取活动进程
    def get_iis_process_list(self,get):
        import psutil
        siteName = get.siteName
        lRet = public.ExecShell(self._appcmd + ' list wps /apppool.name:"' + siteName + '"')
        
        temp = re.findall("WP\s\"(\d+)\"\s+\(applicationPool:(.+)\)",lRet[0])
        data = {}
        data['total_memory'] = 0
        data['total_cpu'] = 0
        data['total_request'] = 0
        data['apps'] = []
        for val in temp:            
            p = psutil.Process(int(val[0]))
            cpu = round(float(p.cpu_percent(interval=0.1) / psutil.cpu_count()),2)            
            memory = p.memory_info().peak_pagefile / 1024;           

            rRet = public.ExecShell(self._appcmd + ' list request /wp.name:"' + val[0] + '"',None,None,None,True)
            tmp2 = re.findall("REQUEST.*\(url:(.+),\s+time:(\d+).+?,\s+client:(.+),\s+stage:(.+),\s+module:(.+)\)",rRet[0])

            request = len(tmp2);
            data['apps'].append({'name':val[1],'pid':val[0],'cpu':cpu ,'memory':memory,'request':request })

            data['total_memory'] += memory
            data['total_cpu'] += cpu
            data['total_request'] += request

        return data

    #设置网站进程模型
    def set_site_app_process(self,get):
        idleTimeout = int(get.idleTimeout)
        maxProcesses = int(get.maxProcesses)
        shutdownTimeLimit = int(get.shutdownTimeLimit)
        startupTimeLimit = int(get.startupTimeLimit)

        if idleTimeout < 0 or maxProcesses <0 or shutdownTimeLimit<0 or startupTimeLimit < 0:  return public.returnMsg(False,'参数传递错误,参数必须是正整数!');
        
        shell = self._appcmd + ' set apppool "%s" /processModel.idleTimeout:%s /processModel.maxProcesses:"%s" /processModel.shutdownTimeLimit:"%s" /processModel.startupTimeLimit:"%s"' % (get.siteName,public.int_to_time(idleTimeout),maxProcesses,public.int_to_time(shutdownTimeLimit),public.int_to_time(startupTimeLimit))        
        public.ExecShell(shell)
        return public.returnMsg(True,"操作成功!");


    #获取故障处理方式
    def get_iis_failure_exe(self,failure_type,siteName):
        if failure_type == 'start_pool':
            return [ self._appcmd,'start apppool "' + siteName + '"']
        elif  failure_type == 'restart_iis':
            return ['C:\Windows\System32\iisreset.exe','/restart']
        return ['','']


    #设置进程回收        
    def set_site_recycling_bytime(self,get):
        siteName = get.siteName
        recycling_time = get.recycling_time
        stype = get.stype

        if not re.match("\d+:\d+:\d+", recycling_time): return public.returnMsg(False,'不是有效的时间格式,格式为:01:00:00');
        opt = '-'
        msg = '删除成功！'
        if stype == '1': 
            msg = '添加成功！'
            opt = '+'

        shell = self._appcmd + ' set config -section:system.applicationHost/applicationPools /%s"[name=\'%s\'].recycling.periodicRestart.schedule.[value=\'%s\']" /commit:apphost' % (opt, siteName,recycling_time)
  
        public.ExecShell(shell)
        return public.returnMsg(True,msg);


    #设置程序池故障防护
    def set_iis_app_failure(self,get):       
        
        rapidFailProtectionInterval = int(get.rapidFailProtectionInterval) * 60
        if rapidFailProtectionInterval <= 0 : 
            return public.returnMsg(False,'故障间隔时间必须是正整数!');
        
        rapidFailProtection = get.rapidFailProtection
        rapidFailProtectionInterval = public.int_to_time(rapidFailProtectionInterval)
        rapidFailProtectionMaxCrashes = get.rapidFailProtectionMaxCrashes

  
        is_global = get.is_global
        if not is_global:
            sRet = self.get_iis_failure_exe(get.failure_type,get.siteName)
            if not sRet: return public.returnMsg(False,'未识别的命令!');
            
            shell = self._appcmd + ' set apppool "%s" /failure.rapidFailProtection:%s /failure.rapidFailProtectionInterval:"%s" /failure.rapidFailProtectionMaxCrashes:"%s" /failure.autoShutdownExe:"%s" /failure.autoShutdownParams:"%s"' % (get.siteName,rapidFailProtection,rapidFailProtectionInterval,rapidFailProtectionMaxCrashes,sRet[0],sRet[1])        
            rRet = public.ExecShell(shell)
        else:
            plist = self.GetPoolList()
            for pool in plist:   
                sRet = self.get_iis_failure_exe(get.failure_type,pool)
                if not sRet: return public.returnMsg(False,'未识别的命令!');

                shell = self._appcmd + ' set apppool "%s" /failure.rapidFailProtection:%s /failure.rapidFailProtectionInterval:"%s" /failure.rapidFailProtectionMaxCrashes:"%s" /failure.autoShutdownExe:"%s" /failure.autoShutdownParams:"%s"' % (pool,rapidFailProtection,rapidFailProtectionInterval,rapidFailProtectionMaxCrashes,sRet[0],sRet[1])        
                rRet = public.ExecShell(shell)

        return public.returnMsg(True,'修改程序池故障防护信息成功!');

    #设置程序池自动回收
    def set_iis_app_recycling(self,get):
        privateMemory = int(get.privateMemory);
        requests = int(get.requests)
        ttime = int(get.time);
        is_global = get.is_global

        if privateMemory < 0 or requests < 0  or ttime < 0:
            return public.returnMsg(False,'参数错误，必须为非负数.');
        
        ttime = public.int_to_time(ttime)
        if not is_global:
             shell = self._appcmd + ' set apppool "%s" /recycling.periodicRestart.privateMemory:%s /recycling.periodicRestart.requests:"%s" /recycling.periodicRestart.time:"%s"' % (get.siteName,privateMemory,requests,ttime)  
             rRet = public.ExecShell(shell)
        else:
            plist = self.GetPoolList()
            for pool in plist:
                shell = self._appcmd + ' set apppool "%s" /recycling.periodicRestart.privateMemory:%s /recycling.periodicRestart.requests:"%s" /recycling.periodicRestart.time:"%s"' % (pool,privateMemory,requests,ttime)  
                rRet = public.ExecShell(shell)
        return public.returnMsg(True,'设置应用程序池回收设置成功!');


    #设置程序池信息
    def set_iis_apppool(self,get):
        try:
            pipemodel = get.model;
            version = get.net_version;
            rRet = public.ExecShell(self._appcmd + ' set apppool "'+ get.name +'" /managedRuntimeVersion:v' + version + ' /managedPipelineMode:' + pipemodel + ' /enable32BitAppOnWin64:' + get.enable32BitAppOnWin64 + ' /queueLength:' + get.queueLength)
            get['status'] = 'restart'
            self.set_apppool_status(get);

            return public.returnMsg(True,'修改程序池信息成功!');
        except :
            return public.returnMsg(False,'修改程序池信息失败!');

    #修改程序池状态
    def set_apppool_status(self,get):
       try:
            status = get.status
            if status == 'restart':
                public.ExecShell(self._appcmd + ' stop apppool /apppool.name:"'+get.name +'"')   
                time.sleep(2)   
                public.ExecShell(self._appcmd + ' start apppool /apppool.name:"'+get.name +'"')
            else:
                public.ExecShell(self._appcmd + ' '+ status +' apppool /apppool.name:"'+get.name +'"')
            return public.returnMsg(True,'操作成功!');
       except :
           return public.returnMsg(False,'操作失败!');

    #获取所有iis所有net版本
    def get_iis_net_versions(self,get):
        rRet = public.ExecShell("%windir%\\Microsoft.NET\\Framework\\v2.0.50727\\aspnet_regiis.exe -lv")
        tmps = re.findall("v[1-9]\\d*.[0-9]\\d*",rRet[0])
        data = []
        for item in tmps:
            item = item.replace('v','')
            if not item in data: data.append(item)
        if len(data) == 0:
            data.append("4.0")
        return data

    #添加域名
    def AddDomain(self,get):
      
        if len(get.domain) < 3: return public.returnMsg(False,'SITE_ADD_DOMAIN_ERR_EMPTY');
        domains = get.domain.split(',')
        for domain in domains:
            if domain == "": continue;
            
            domain = domain.split(':')
            get.zh_domain = domain[0]
            get.domain = self.ToPunycode(domain[0])
            get.port = '80'
            
            reg = "^([\w\-\*]{1,100}\.){1,4}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$";
            if not re.match(reg, get.domain): return public.returnMsg(False,'SITE_ADD_DOMAIN_ERR_FORMAT');            

            if len(domain) == 2: get.port = domain[1];
            if get.port == "": get.port = "80";
         
            if not public.checkPort(get.port): return public.returnMsg(False,'SITE_ADD_DOMAIN_ERR_POER');

            time.sleep(0.01);
            #检查域名是否存在
            sql = public.M('domain');
            opid = sql.where("name=? AND (port=?)",(get.domain,get.port)).getField('pid');
            if opid:
                if public.M('sites').where('id=?',(opid,)).count():
                    return public.returnMsg(False,'SITE_ADD_DOMAIN_ERR_EXISTS');
                sql.where('pid=?',(opid,)).delete();
            if self.serverType == 'iis':    
                self.iisDomain(get)
            elif self.serverType == 'apache':
                self.ApacheDomain(get)
            else:
                self.NginxDomain(get)
            #添加放行端口
            if get.port != '80':
                import firewalls
                get.ps = get.domain;

            public.WriteLog('TYPE_SITE', 'DOMAIN_ADD_SUCCESS',(get.webname,get.domain));
            sql.table('domain').add('pid,name,port,addtime',(get.id,get.domain,get.port,public.getDate()));

        if self.serverType != 'iis':public.serviceReload()
        return public.returnMsg(True,'SITE_ADD_DOMAIN');

    #Nginx写域名配置
    def NginxDomain(self,get):
        file = self.get_conf_path(get.webname);
        conf = public.readFile(file);
        if not conf: return;
        
        #添加域名
        rep = "server_name\s*(.*);";
        tmp = re.search(rep,conf).group()
        domains = tmp.replace(';','').strip().split(' ')
        if not public.inArray(domains,get.domain):
            newServerName = tmp.replace(';',' ' + get.domain + ';')
            conf = conf.replace(tmp,newServerName)
        
        #添加端口
        rep = "listen\s+([0-9]+)\s*[default_server]*\s*;";
        tmp = re.findall(rep,conf);
        if not public.inArray(tmp,get.port):
            listen = re.search(rep,conf).group()
            listen_ipv6 = ''
            if self.is_ipv6: listen_ipv6 = "\n\tlisten [::]:"+get.port+';'
            conf = conf.replace(listen,listen + "\n\tlisten "+get.port+';' + listen_ipv6)

        if get.port != '80' and get.port != '888': self.apacheAddPort(get.port)
        #保存配置文件
        public.writeFile(file,conf)
        return True

    #Apache写域名配置
    def ApacheDomain(self,get):
        file = self.get_conf_path(get.webname);
        conf = public.readFile(file);
        if not conf: return False;
        
        port = get.port;
        siteName = get.webname;
        newDomain = get.domain
        find = public.M('sites').where("id=?",(get.id,)).field('id,name,path').find();
        if not find: return False
            
        sitePath = find['path'];
        siteIndex = 'index.php index.html index.htm default.php default.html default.htm'
      
        #添加域名
        if conf.find('<VirtualHost *:'+port+'>') != -1:
            repV = "<VirtualHost\s+\*\:"+port+">(.|\n)*</VirtualHost>";
            domainV = re.search(repV,conf).group()
            rep = "ServerAlias\s*(.*)\n";
            tmp = re.search(rep,domainV).group(0)
            domains = tmp.strip().split(' ')
            if not public.inArray(domains,newDomain):
                rs = tmp.replace("\n","")
                newServerName = rs+' '+newDomain+"\n";
                myconf = domainV.replace(tmp,newServerName);
                conf = re.sub(repV, myconf, conf);
            if conf.find('<VirtualHost *:443>') != -1:
                repV = "<VirtualHost\s+\*\:443>(.|\n)*</VirtualHost>";
                domainV = re.search(repV,conf).group()
                rep = "ServerAlias\s*(.*)\n";
                tmp = re.search(rep,domainV).group(0)
                domains = tmp.strip().split(' ')
                if not public.inArray(domains,newDomain):
                    rs = tmp.replace("\n","")
                    newServerName = rs+' '+newDomain+"\n";
                    myconf = domainV.replace(tmp,newServerName);
                    conf = re.sub(repV, myconf, conf);
        else:
            get.siteName = siteName
            phpVersion  = self.GetSitePHPVersion(get)['phpversion']
            if len(phpVersion) < 2: return public.returnMsg(False,'PHP_GET_ERR')
            newconf ='''<VirtualHost *:%s>
    ServerAdmin webmaster@example.com
	DocumentRoot "%s"
	ServerAlias %s
    ErrorLog "%s-error.log"
    CustomLog "%s-access.log" common

    #redirect 重定向
    IncludeOptional conf/redirect/%s/*.conf

    #proxy 反向代理
    IncludeOptional conf/proxy/%s/*.conf

	ErrorDocument 404 /404.html
	
	#DENY FILES
	<Files ~ (\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)$>
	   Order allow,deny
	   Deny from all
	</Files>
	
	#PHP
    Include conf/php/%s.conf

	#PATH
	<Directory "%s">
		Options FollowSymLinks ExecCGI
		AllowOverride All
		Require all granted
		DirectoryIndex index.php default.php index.html index.htm default.html default.htm
		
	</Directory>
</VirtualHost>
''' % (port,sitePath,newDomain,public.GetConfigValue('logs_path')+'/'+ siteName,public.GetConfigValue('logs_path')+'/'+ siteName,siteName,siteName,phpVersion,sitePath)
            conf += "\n"+newconf;
        
        #添加端口
        if port != '80' and port != '888': self.apacheAddPort(port)
        
        #保存配置文件
        public.writeFile(file,conf)
        return True

    #iis添加域名
    def iisDomain(self,get):
               
        public.ExecShell(self._appcmd + " set site " + get.webname + " /+bindings.[protocol='http',bindingInformation='*:" + get.port + ":" + get.zh_domain + "']")
        rRet =  public.ExecShell(self._appcmd + ' list site "' + get.webname + '"')
        if rRet[0].find("*:443") >=0:
            public.ExecShell(self._appcmd + " set site " + get.webname + " /+bindings.[protocol='https',bindingInformation='*:443:" + get.zh_domain + "']")
        return True

    #删除域名
    def DelDomain(self,get):
        sql = public.M('domain');
        id= get['id'];
        port = 80
        if hasattr(get, 'port'): port = get.port;
        if not hasattr(get, 'domain'): return public.returnMsg(False,'请选择需要删除的域名.')

        find = sql.where("pid=? AND name=? AND port=?",(get.id,get.domain,port)).field('id,name').find();
        domain_count = sql.table('domain').where("pid=?",(id,)).count();
        if domain_count == 1: return public.returnMsg(False,'SITE_DEL_DOMAIN_ERR_ONLY');
        if self.serverType == 'iis':            
            shell = " set site " + get.webname + " /-bindings.[protocol='http',bindingInformation='*:" + get.port + ":" + self.DePunycode(get.domain) + "']"
            rRet = public.ExecShell(self._appcmd + shell)
            rRet = public.ExecShell(self._appcmd +  " set site " + get.webname + " /-bindings.[protocol='https',bindingInformation='*:443:" + self.DePunycode(get.domain) + "']")
        elif self.serverType == 'apache':
            file = self.get_conf_path(get.webname)
            conf = public.readFile(file);
            #删除域名
            try:
                rep = "\n*<VirtualHost \*\:" + port + ">(.|\n)*?</VirtualHost>";
                tmp = re.search(rep, conf).group()
                
                rep1 = "ServerAlias\s+(.+)\n";
                tmp1 = re.findall(rep1,tmp);
                tmp2 = tmp1[0].split(' ')
              
                if len(tmp2) < 2:
                    conf = re.sub(rep,'',conf);       
                else:
                    newServerName = tmp.replace(' '+get['domain']+"\n","\n");
                    newServerName = newServerName.replace(' '+get['domain']+' ',' ');
                    conf = conf.replace(tmp,newServerName)                
                #保存配置
                public.writeFile(file,conf)
            except:
                pass;
        else:
            file = self.get_conf_path(get.webname)
            conf = public.readFile(file);
            try:
                #删除域名
                rep = "server_name\s+(.+);";
                tmp = re.search(rep,conf).group()
                newServerName = tmp.replace(' '+get['domain']+';',';');
                newServerName = newServerName.replace(' '+get['domain']+' ',' ');
                conf = conf.replace(tmp,newServerName);
            
                #删除端口
                rep = "listen\s+([0-9]+);";
                tmp = re.findall(rep,conf);
                port_count = sql.table('domain').where('pid=? AND port=?',(get.id,get.port)).count()
                if public.inArray(tmp,port) == True and  port_count < 2:
                    rep = "\n*\s+listen\s+"+port+";";
                    conf = re.sub(rep,'',conf);
                    rep = "\n*\s+listen\s+\[::\]:"+port+";";
                    conf = re.sub(rep,'',conf);
                #保存配置
                public.writeFile(file,conf)
            except :pass

        if find : sql.table('domain').where("id=?",(find['id'],)).delete();
        if self.serverType != 'iis':public.serviceReload()
        public.WriteLog('TYPE_SITE', 'DOMAIN_DEL_SUCCESS',(get.webname,get.domain));
        return public.returnMsg(True,'DEL_SUCCESS');

    #启动站点
    def SiteStart(self,get):
        id = get.id
        Path = self.setupPath + '/stop';
        sitePath = public.M('sites').where("id=?",(id,)).getField('path');

        #iis        
        webserver = public.get_webserver()  
        if webserver == 'iis':
            runFiles = Path + '/' + id;
            if os.path.exists(runFiles):
                runPath = public.readFile(runFiles)
                sitePath = sitePath + runPath
                os.remove(runFiles)

            public.ExecShell(self._appcmd + ' set app "' + get.name + '/" -[path=\'/\'].physicalPath:' + sitePath.replace('/','\\'))
        else:
            file = self.get_conf_path(get.name);
            conf = public.readFile(file)
            if conf:
                conf = conf.replace(Path, sitePath);
                public.writeFile(file,conf)

        public.M('sites').where("id=?",(id,)).setField('status','1');

        if self.serverType != 'iis':public.serviceReload()

        public.WriteLog('TYPE_SITE','SITE_START_SUCCESS',(get.name,))
        return public.returnMsg(True,'SITE_START_SUCCESS')

    #停止站点
    def SiteStop(self,get):
        path = self.setupPath + '/stop';

        if not hasattr(get, 'id'): return public.returnMsg(False,'缺少必要参数网站ID.')
        id = get.id
        
        import files
        nget = dict_obj();
        nget.path = path + '/index.html'
        files.files().check_stop_page(nget)

        binding = public.M('binding').where('pid=?',(id,)).field('id,pid,domain,path,port,addtime').select();
        for b in binding:
            bpath = path + '/' + b['path'];
            if not os.path.exists(bpath): 
                os.makedirs(bpath)
                public.writeFile(bpath + '/index.html',public.readFile(path + '/index.html'))
        
        sitePath = public.M('sites').where("id=?",(id,)).getField('path');        

        #iis        
        webserver = public.get_webserver()  
        if webserver == 'iis':
            runData = self.GetSiteRunPath(get)
            if not runData: return public.returnMsg(False,'获取网站运行目录失败，请查看面板日志排除错误.')
            runPath = runData['runPath']
            if runPath != '/': public.writeFile(path + '/' + id,runPath)
           
            public.ExecShell(self._appcmd + ' set app "' + get.name + '/" -[path=\'/\'].physicalPath:' + path.replace('/','\\'))
        else:
            file = self.get_conf_path(get.name);
            conf = public.readFile(file);
            if conf:
                conf = conf.replace(sitePath, path);
                public.writeFile(file,conf)

        public.M('sites').where("id=?",(id,)).setField('status','0');
        
        if self.serverType != 'iis': public.serviceReload();

        public.WriteLog('TYPE_SITE','SITE_STOP_SUCCESS',(get.name,))
        return public.returnMsg(True,'SITE_STOP_SUCCESS')
    
    #获取站点目录
    def get_site_path(self,siteName):
        path = None
        rRet = public.ExecShell(self._appcmd + ' list vdir /app.name:"' + siteName + '/" /text:physicalPath')
        if rRet[0]:
            path = rRet[0].strip()
        return path
    
    #修改物理路径
    def SetPath(self,get):
        try:
            id = get.id
            Path = self.GetPath(get.path);
            if Path == "" or id == '0': return public.returnMsg(False,  "DIR_EMPTY");

            import files
            f = files.files()
            if not f.CheckDir(Path): return public.returnMsg(False,  "PATH_ERROR");

            SiteFind = public.M("sites").where("id=?",(id,)).field('path,name').find();
            if SiteFind["path"] == Path: return public.returnMsg(False,  "SITE_PATH_ERR_RE");
            Name = SiteFind['name'];

            if not os.path.exists(Path): os.makedirs(Path)        
            get.filename = Path
            get.user = 'www'
            get.access = 2032127
            rRet = f.SetFileAccess(get)

            if self.serverType == 'iis':
                get.user = Name
                rRet = f.SetFileAccess(get)
                public.ExecShell(self._appcmd + ' set app "' + Name + '/" -[path=\'/\'].physicalPath:' + Path.replace('/','\\'))
                self.init_iisSite_config(Path + '/web.config')
            elif self.serverType == 'apache':            
                file = self.get_conf_path(Name)
                conf = public.readFile(file);
                if conf:
                    rep = "DocumentRoot\s+.+\n";
                    conf = re.sub(rep,'DocumentRoot "' + Path + '"\n',conf);
                    rep = "<Directory\s+.+\n";
                    conf = re.sub(rep,'<Directory "' + Path + "\">\n",conf);
                    public.writeFile(file,conf);
            else:
                file = self.get_conf_path(Name)
                conf = public.readFile(file);
                if conf:
                    conf = conf.replace(SiteFind['path'],Path );
                    public.writeFile(file,conf);

            if self.serverType != 'iis': public.serviceReload();

            public.M("sites").where("id=?",(id,)).setField('path',Path);
            public.WriteLog('TYPE_SITE', 'SITE_PATH_SUCCESS',(Name,));
            return public.returnMsg(True,  "SET_SUCCESS");
        except Exception as ex:
            return public.returnMsg(False,  '操作失败,' + str(ex));


    #从IIS获取站点
    def get_iis_sites(self):        
        rRet = public.ExecShell(self._appcmd + ' list sites',None,None,None,True)
        temp = re.findall("SITE\s+\"(.+)\"\s+\((.*)\)",rRet[0])
        list = {}
        for item in temp:
            site = {}
            site['name'] = item[0]
            attrs = re.findall("(\w+:\w+)(,|$)|(bindings:https?/\*:\d+:.+),",item[1])
            for attr in attrs:
               vstr = attr[0] + attr[2]
               arr_groups = re.search("(.+?):(.*)",vstr).groups()
               if len(arr_groups) == 2:
                    if arr_groups[0] == 'bindings':
                        site[arr_groups[0]] = []
                        domains = arr_groups[1].split(',')
                        for ditem in domains:
                            d_list = re.search("(\w+)/.:(\d+):(.*)",ditem)
                            if d_list:
                                list_group = d_list.groups()
                                site[arr_groups[0]].append({ 'port':list_group[1],'domain':list_group[2],'protocol':list_group[0] }) 
                    else:
                        site[arr_groups[0]] =  arr_groups[1]            
            list[item[0]] = site
        return list

    #清除多余user.ini
    def DelUserInI(self,path,up = 0):
        for p1 in os.listdir(path):
            try:
                npath = path + '/' + p1;
                if os.path.isdir(npath):
                    if up < 100: self.DelUserInI(npath, up + 1);
                else:
                    continue;
                useriniPath = npath + '/.user.ini';
                if not os.path.exists(useriniPath): continue;
                os.remove(useriniPath)
            except: pass;
        return True;
    
    #设置目录防御
    def SetDirUserINI(self,get):
        try:
            path = get.path
            filename = path + '/.user.ini';
            self.DelUserInI(path);
            if os.path.exists(filename):           
                os.remove(filename)
                return public.returnMsg(True, 'SITE_BASEDIR_CLOSE_SUCCESS');
            public.writeFile(filename, 'open_basedir="' + path +'/;C:/Windows/Temp/;C:/Temp/;' + self.setupPath + '/temp/session/"');
            public.serviceReload();
            return public.returnMsg(True,'SITE_BASEDIR_OPEN_SUCCESS');
        except Exception as ex:
            return public.returnMsg(False,str(ex));


    #域名编码转换
    def ToPunycode(self,domain):
        import re;

        tmp = domain.split('.');
        newdomain = '';
        for dkey in tmp:
            #匹配非ascii字符
            match = re.search(u"[\x80-\xff]+",dkey);
            if not match: match = re.search(u"[\u4e00-\u9fa5]+",dkey);
            if not match:
                newdomain += dkey + '.';
            else:
                newdomain += 'xn--' + dkey.encode('punycode').decode('utf-8') + '.'
        return newdomain[0:-1];

    #punycode 转中文
    def DePunycode(self,domain):

        tmp = domain.split('.');
        newdomain = '';
        for dkey in tmp:
            if dkey.find('xn--') >=0:
                newdomain += dkey.replace('xn--','').encode('utf-8').decode('punycode') + '.'
            else:
                newdomain += dkey + '.'
        return newdomain[0:-1];

    
    #中文路径处理
    def ToPunycodePath(self,path):
        if sys.version_info[0] == 2: path = path.encode('utf-8');
        if os.path.exists(path): return path;
        import re;
        match = re.search(u"[\x80-\xff]+",path);
        if not match: return path;
        npath = '';
        for ph in path.split('/'):
            npath += '/' + self.ToPunycode(ph);
        return npath.replace('//','/')

    #获取当前可用php版本
    def GetPHPVersion(self,get):
        phpVersions = ('00','52','53','54','55','56','70','71','72','73','74','75','76')
        data = []
        for val in phpVersions:
            tmp = {}
            checkPath = self.setupPath+'/php/'+val+'/php.exe';
            tmp['version'] = val;
            tmp['name'] = 'PHP-'+val;
            if val == '00':
                if val == '00': tmp['name'] = '纯静态';
                data.append(tmp)
            else:
                if os.path.exists(checkPath):
                    data.append(tmp)
        return data
    
    #是否开启目录防御
    def GetDirUserINI(self,get):    
        if not hasattr(get,'path'): return public.returnMsg(False,'获取失败,参数传递错误.');
            
        path = get.path;
        data = {}
        id = get.id;
        get.name = public.M('sites').where("id=?",(id,)).getField('name');           
        info = self.get_site_info(get.name)
        if not info: return public.returnMsg(False,'网站信息获取失败，请检查 %s 是否存在此站点.' % self.serverType);
           
        data['logs'] = self.GetLogsStatus(get);
        data['userini'] = False;
        if os.path.exists(path+'/.user.ini'):
            data['userini'] = True;
        if os.path.exists(path):                        
            data['runPath'] = self.GetSiteRunPath(get);
            data['pass'] = self.GetHasPwd(get); 
        data['locking'] = self.get_config_locking(get.name)
        return data;
    
    #取目录加密状态
    def GetHasPwd(self,get):
        if not hasattr(get,'siteName'):
            get.siteName = public.M('sites').where('id=?',(get.id,)).getField('name');
        return False;

    #取日志状态
    def GetLogsStatus(self,get):
        webserver = public.get_webserver()
        if webserver == 'iis':
            data = self.get_site_info(get.name)
            if data: return data['logs']
            return False
        elif webserver == 'apache':
            filename = self.get_conf_path(get.name)
            if not os.path.exists(filename): return False;
            
            conf = public.readFile(filename);
            if conf.find('#ErrorLog') != -1: return False;
            if conf.find("access_log  off") != -1: return False;
            return True;
        else:
            filename = self.get_conf_path(get.name)       
            if not os.path.exists(filename): return False;
            conf = public.readFile(filename);
            if conf.find('#ErrorLog') != -1: return False;
            if conf.find("access_log  off") != -1: return False;
            return True;

    #取当站点前运行目录
    def GetSiteRunPath(self,get):
        try:
            SiteFind = public.M("sites").where("id=?",(get.id,)).field('path,name').find();
            info = self.get_site_info(SiteFind['name'])
            data = {}
            if info and info['path']:            
                if SiteFind['path'] == info['path']: 
                    data['runPath'] = '/';
                else:
                    data['runPath'] = info['path'].replace(SiteFind['path'],'').strip();
        
                dirnames = []
                dirnames.append('/');
                if not os.path.exists(SiteFind['path']): os.makedirs(SiteFind['path'])

                for filename in os.listdir(SiteFind['path']):
                    try:
                        filePath = SiteFind['path'] + '/' + filename
                        if os.path.islink(filePath): continue
                        if os.path.isdir(filePath):
                            dirnames.append('/' + filename)
                    except:
                        pass        
                data['dirs'] = dirnames;
            return data;
        except Exception as ex:
            public.WriteLog('TYPE_SITE', '获取网站运行目录失败 --> ' + str(ex));

    #设置当前站点运行目录
    def SetSiteRunPath(self,get):
        SiteFind = public.M("sites").where("id=?",(get.id,)).field('path,name').find();
      
        if self.serverType == 'iis':
            if get.runPath == '/web_config': return public.returnMsg(False,'不可以web_config目录作为运行目录，请重新选择.');
                
            data = self.get_site_info(SiteFind['name'])
            new_path = self.GetPath(SiteFind['path'] + get.runPath)
            path = SiteFind['path'] 
            if path != new_path:             
                if os.path.exists(data['path'] + '/web.config'): 
                    public.move(data['path'] + '/web.config', new_path + '/web.config')

                if os.path.exists(data['path'] + '/web_config'): 
                    public.move(data['path'] + '/web_config', new_path + '/web_config')

                if os.path.exists(data['path'] + '/404.html'): 
                    public.move(data['path'] + '/404.html', new_path + '/404.html')

            public.ExecShell(self._appcmd + ' set app "' + SiteFind['name'] + '/" -[path=\'/\'].physicalPath:' + new_path.replace('/','\\'))         
        elif self.serverType == 'apache':      
            #处理Apache
            filename = self.get_conf_path(SiteFind['name'])
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = '\s*DocumentRoot\s*"(.+)"\s*\n'
                path = re.search(rep,conf).groups()[0];
                new_path = SiteFind['path'] + get.runPath
                conf = conf.replace(path,new_path);
                public.writeFile(filename,conf);

                move_list = ['.user.ini','.htaccess','404.html']
                for filename in move_list:                    
                    if os.path.exists(path + '/' + filename): 
                        public.move(path + '/' + filename, new_path + '/'+ filename)
                
        elif self.serverType == 'nginx':
            #处理Nginx
            filename = self.get_conf_path(SiteFind['name'])
            conf = public.readFile(filename)
            rep = '\s*root\s*(.+);'
            path = re.search(rep,conf).groups()[0];
            new_path = SiteFind['path'] + get.runPath
            conf = conf.replace(path,new_path);

            public.writeFile(filename,conf);

            move_list = ['.user.ini','.htaccess','404.html']
            for filename in move_list:                    
                if os.path.exists(path + '/' + filename): public.move(path + '/' + filename, new_path + '/'+ filename)
                
        if self.serverType != 'iis':public.serviceReload()
        return public.returnMsg(True,'SET_SUCCESS');

    #路径处理
    def GetPath(self,path):        
        if path[-1] == '/':
            return path[0:-1];
        return path;

    #取指定站点的PHP版本
    def GetSitePHPVersion(self,get):   
        data = {}
        Name = get.siteName
        webserver = public.get_webserver()  
        if webserver == 'iis':
            check_ret = self.check_iis_config(Name)
            if not check_ret['status']: return check_ret 
            
            try:
                sitePath = self.get_site_path(Name)   
                if not sitePath: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % Name); 

                phpConf = public.readFile(sitePath + '/web_config/php.config')
                tmp = re.search('php\\\(\d{2})\\\php-cgi',phpConf).groups()
            
                data['phpversion'] = tmp[0];
            except :
                data['phpversion'] = '00';
        elif webserver == 'apache':
            data['phpversion'] = '00'
            filename = self.get_conf_path(Name)
            if os.path.exists(filename):          
                conf = public.readFile(filename)
                tmp = re.search('/php/(.+).conf',conf)            
                if tmp:data['phpversion'] = tmp.groups()[0]       
        else:
            filename = self.get_conf_path(Name)
            data['phpversion'] = '00'
            if os.path.exists(filename):          
                conf = public.readFile(filename)
                tmp = re.search('include php/(\d+).conf;',conf)
                data['phpversion'] = '00'
                if tmp: data['phpversion'] = tmp.groups()[0]                       
        return data;
      
    #设置指定站点的PHP版本
    def SetPHPVersion(self,get):
        siteName = get.siteName
        version = get.version
        
        if self.serverType == 'iis':
            #iis
            sitePath = self.get_site_path(siteName)
            if not sitePath: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % siteName); 
            
            phpPath = (self.setupPath + '/php/'+version+'/php-cgi.exe').replace('/','\\')
            phpVersions = ['52','53','54','55','56','70','71','72','73','74','75']
            
            hlist = []
            for v in phpVersions:
                hlist.append({'@name':'php_' + v })

            php_config = {"handlers": { "remove":hlist,"add": {"@name": "php_" + version, "@path": "*.php", "@verb": "*", "@modules": "FastCgiModule", "@scriptProcessor": phpPath, "@resourceType": "Unspecified", "@requireAccess": "Script"} }}
            public.writeFile(sitePath + '/web_config/php.config', self.format_xml(self.dumps_json(php_config)))
        elif self.serverType == 'apache':
            pPath = self.setupPath + '/apache/conf/php'
            if not os.path.exists(pPath): os.makedirs(pPath)
            if not os.path.exists(pPath+'/' + version + '.conf'):
                phpconfig = '''<Files ~ "\.php$">
	Options FollowSymLinks ExecCGI
	AddHandler fcgid-script .php
	FcgidWrapper "%s/php-cgi.exe" .php
</Files>''' % (self.setupPath + '/php/' + version)
                if version == '00': phpconfig = ''
                public.writeFile(pPath+'/' + version + '.conf',phpconfig)

            #apache
            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            if conf:
                rep = "(Include\s+conf/php.+.conf)";
                tmp = re.search(rep,conf)
                if tmp:                    
                    conf = conf.replace(tmp.group(),'Include conf/php/'+version+'.conf');
                    public.writeFile(file,conf)
                else:
                    return public.returnMsg(False,'操作失败，您的配置文件缺少宝塔默认创建的重要部分，请恢复后重新操作.');

        elif self.serverType == 'nginx':
            #nginx
            pPath = self.setupPath + '/nginx/conf/php'
            if not os.path.exists(pPath): os.makedirs(pPath)
            if not os.path.exists(pPath+'/' + version + '.conf'):
                phpconfig = '''location ~ \.php(.*)$ {
	fastcgi_pass   127.0.0.1:200%s;
	fastcgi_index  index.php;

    fastcgi_split_path_info  ^((?U).+\.php)(/?.+)$;
    fastcgi_param  SCRIPT_FILENAME  $document_root$fastcgi_script_name;
    fastcgi_param  PATH_INFO  $fastcgi_path_info;

	fastcgi_param  SCRIPT_FILENAME  $document_root$fastcgi_script_name;
	include        fastcgi_params;
}''' % (version)
                if version == '00': phpconfig = ''
                public.writeFile(pPath+'/' + version + '.conf',phpconfig)

            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            if conf:
               
                rep = "(include\s+php/.+conf)\;";
                tmp = re.search(rep,conf)
                if tmp:                    
                    conf = conf.replace(tmp.group(),'include php/' + version + '.conf;');
                    public.writeFile(file,conf)
                else:
                    return public.returnMsg(False,'操作失败，您的配置文件缺少宝塔默认创建的重要部分，请恢复后重新操作.');
        public.serviceReload(siteName);
        public.WriteLog("TYPE_SITE", "SITE_PHPVERSION_SUCCESS",(siteName,version));
        return public.returnMsg(True,'SITE_PHPVERSION_SUCCESS',(siteName,version));

    #设置默认文档
    def SetIndex(self,get):
        id = get.id;
        if get.Index.find('.') == -1: return public.returnMsg(False,  'SITE_INDEX_ERR_FORMAT')
        
        Index = get.Index.replace(' ', '')
        Index = get.Index.replace(',,', ',')
        
        if len(Index) < 3: return public.returnMsg(False,  'SITE_INDEX_ERR_EMPTY')
                
        Name = public.M('sites').where("id=?",(id,)).getField('name');
        #准备指令
        Index_L = Index.replace(",", " ");
        
        if self.serverType == 'iis':
            #iis
            sitePath = self.get_site_path(Name)
            if not sitePath: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % Name); 
            
            list = Index.split(',')
            newfiles = []
            for x in list:
                if x:  newfiles.append({"@value":x})
            data = {"defaultDocument": {"files": {"clear": {}, "add": newfiles }}}
            public.writeFile(sitePath+'/web_config/default.config', self.format_xml(self.dumps_json(data)))
        elif self.serverType == 'apache':
            #apache
            file = self.get_conf_path(Name)
            conf = public.readFile(file);
            if conf:
                rep = "DirectoryIndex\s+.+\n";
                conf = re.sub(rep,'DirectoryIndex ' + Index_L + "\n",conf);
                public.writeFile(file,conf);
        elif self.serverType == 'nginx':
            #nginx
            file = self.get_conf_path(Name)
            conf = public.readFile(file);
            if conf:
                rep = "\s+index\s+.+;";
                conf = re.sub(rep,"\n\tindex " + Index_L + ";",conf);
                public.writeFile(file,conf);

        public.serviceReload(Name);
        public.WriteLog('TYPE_SITE', 'SITE_INDEX_SUCCESS',(Name,Index_L));
        return public.returnMsg(True,  'SET_SUCCESS')

    #读取网站配置
    def get_site_config(self,get):
        Name = get.siteName
        webserver = public.get_webserver()        
        get = dict_obj();
        if webserver == 'iis':
            sitePath = self.get_site_path(Name)
            if not sitePath: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % Name);    
           
            if not public.check_win_path(sitePath): 
                return public.returnMsg(False,'不能以磁盘作为网站目录，或网站目录不是有效的Windows路径格式，不能包含(: * ? " < > |)');

            get.path = sitePath + '\\web.config'
            if not os.path.exists(get.path):
                    self.init_iisSite_config(get.path)
        else:
            get.path = self.get_conf_path(Name)
        if not os.path.exists(get.path): return public.returnMsg(False,  '网站【%s】配置文件不存在。 ' % Name)
        import files        
        result = files.files().GetFileBody(get)
        return result

    #保存网站配置
    def set_site_config(self,get):       
        if not hasattr(get, 'siteName'):  return public.returnMsg(False, '操作失败，缺少必要参数.');

        Name = get.siteName
        webserver = public.get_webserver()        
        if webserver == 'iis':
            sitePath = self.get_site_path(Name)
            if not sitePath: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % Name);    
                
            get.path = public.format_path(sitePath + '/web.config')
            try:
                xmltodict.parse(get.data)
            except :
                return public.returnMsg(False,  '修改失败，配置文件格式不正确，请确保配置文件是有效的XML格式！')
        else:
            get.path = self.get_conf_path(Name)
        import files
        result = files.files().SaveFileBody(get)
        public.serviceReload(Name);
        return result
    
    #恢复网站配置
    def set_re_site_config(self,get):
        Name = get.siteName
        webserver = public.get_webserver()        
        if webserver == 'iis':
            sitePath = self.get_site_path(Name)
            if not sitePath: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % Name);  
            try:
                get.version = self.GetSitePHPVersion(get)['phpversion']
            except :
                get.version = '00'            
            self.init_iisSite_config(sitePath + '/web.config',True)            
            self.SetPHPVersion(get);
     
            return public.returnMsg(True,  '恢复网站[%s]配置成功！' % Name)
        else:
            return public.returnMsg(False,  '恢复失败，恢复配置仅用于恢复IIS默认配置！')

    #取默认文档
    def GetIndex(self,get):
        id = get.id;
        Name = public.M('sites').where("id=?",(id,)).getField('name');

        list = ['index.aspx','index.asp','index.php','default.html','default.htm','index.htm','index.html','default.aspx']
        if self.serverType == 'iis':
            check_ret = self.check_iis_config(Name)
            if not check_ret['status']: return check_ret

            list = ['index.aspx','index.asp','index.php','default.html','default.htm','index.htm','index.html','default.aspx']
            sitePath = self.get_site_path(Name)
            if not sitePath: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % Name);  

            confPath = sitePath + '/web_config/default.config'
            if os.path.exists(confPath):
                conf = public.readFile(confPath)
                tmps = re.findall('<add\s+value=\"(.+)\"\s?/>',conf)
                list = []
                for item in tmps:
                    list.append(item)
            return ','.join(list)
        else:
            info = self.get_site_info(Name)
            if info:
                return info['index'].replace(' ',',')
            return ','.join(list) 

    #取子目录绑定
    def GetDirBinding(self,get):
        path = public.M('sites').where('id=?',(get.id,)).getField('path')
        if not path: return public.returnMsg(False, '获取失败，请检查网站是否存在.');
            
        if not os.path.exists(path): 
            import files
            if not files.files().CheckDir(path):
                data = {}
                data['dirs'] = []
                data['binding'] = []
                return data;
            os.makedirs(path)
            siteName = public.M('sites').where('id=?',(get.id,)).getField('name')
            public.WriteLog('网站管理','站点['+siteName+'],根目录['+path+']不存在,已重新创建!');
        dirnames = []
        for filename in os.listdir(path):
            try:
                filePath = path + '/' + filename
                if os.path.islink(filePath): continue
                if os.path.isdir(filePath):
                    dirnames.append(filename)
            except:
                pass
        
        data = {}
        data['dirs'] = dirnames
        data['binding'] = public.M('binding').where('pid=?',(get.id,)).field('id,pid,domain,path,port,addtime').select()
        return data

    #取伪静态规则应用列表
    def GetRewriteList(self,get):     
        rewriteList = {}

        rewriteList['rewrite'] = []
        rewriteList['rewrite'].append('0.'+public.getMsg('SITE_REWRITE_NOW'))
        for ds in os.listdir('rewrite/' + public.get_webserver()):
            if ds == 'list.txt': continue;
            rewriteList['rewrite'].append(ds[0:len(ds)-5]);
        rewriteList['rewrite'] = sorted(rewriteList['rewrite']);
        return rewriteList
    
    #保存伪静态模板
    def SetRewriteTel(self,get):
        #get.name = get.name.encode('utf-8');
        filename = 'rewrite/' + public.get_webserver() + '/' + get.name + '.conf';
        public.writeFile(filename,get.data);
        return public.returnMsg(True, 'SITE_REWRITE_SAVE');
    
    #获取伪静态内容
    def GetSiteRewrite(self,get):
        Name =  get.siteName;

        result = {}
        result['status'] = False
        result['data'] = ''
        if self.serverType == 'iis':
            check_ret = self.check_iis_config(Name)
            if not check_ret['status']: return check_ret
            
            sitePath = self.get_site_path(Name)
            if not sitePath: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % Name);  
                
            old_data = self.get_config_rules(Name)           
            rules = []
            for rule in old_data['rules']['rule']:
                if rule['@name'].find('_rewrite') >= 0: rules.append(rule)

            result['status'] = True
            if len(rules):
                data = {}    
                data['rules'] = {};
                data['rules']['rule'] = rules
                result['data'] =  self.format_xml(self.dumps_json(data))
        elif self.serverType == 'apache':
            result['status'] = True
            info = self.get_site_info(Name)
            if info:     
                if os.path.exists(info['path']):
                    result['data'] = public.readFile(info['path'] + '/.htaccess')
        else:
            result['status'] = True
            filename = self.setupPath + '/nginx/conf/rewrite/' + Name + '/' + Name + '.conf'   
            if os.path.exists(filename):
                result['data'] = public.readFile(filename)

        return result

    #保存伪静态
    def SetSiteRewrite(self,get):
        if not hasattr(get, 'siteName'):  return public.returnMsg(False, '操作失败，缺少必要参数.');

        Name =  get.siteName;
        if self.serverType == 'iis':
            data = None
            #try:      
            sitePath = self.get_site_path(Name)
            if not sitePath: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % Name);  
            new_list = []
            sucess = 0
            if get.data.strip():                
                #组装新的伪静态规则          
                tmps = re.findall('<rule[\s+>][\w\W]+?/rule>',get.data)
                if len(tmps) <= 0:  return public.returnMsg(False, '不是有效的IIS伪静态规则，使用对应的规则。');

                for nVal in tmps:
                    try:
                        item = xmltodict.parse(nVal)
                        if item['rule']:
                            if '@name' in item['rule']:
                                item['rule']['@name'] = item['rule']['@name'].replace('_rewrite','') + '_rewrite'
                            else:
                                item['rule']['@name'] = public.GetRandomString(6) + '_rewrite'
                            new_list.append(item['rule'])
                            sucess = sucess + 1
                    except :
                        pass

            #清理旧的伪静态规则          
            old_data = self.get_config_rules(Name)    
    
            for x in range(len(old_data['rules']['rule'])-1,-1,-1):
                rule = old_data['rules']['rule'][x]
                if rule['@name'].find('_rewrite') >= 0:
                    old_data['rules']['rule'].pop(x)       
                                      
            for new_rule in new_list: old_data['rules']['rule'].append(new_rule)
             
            self.set_config_rules(Name,old_data)
            if sucess or not get.data.strip():               
                return public.returnMsg(True, 'SITE_REWRITE_SAVE');
            else:
                return public.returnMsg(False, 'iis伪静态格式不正确,不是有效的xml格式');
            #except :
            #    return public.returnMsg(False, 'iis伪静态格式不正确,不是有效的xml格式');
        elif self.serverType == 'apache':
            info = self.get_site_info(Name)
            if not info: return public.returnMsg(True, '获取网站信息失败，请检查Apache是否存在此网站.');
            if os.path.exists(info['path']):
                public.writeFile(info['path'] + '/.htaccess', get.data.strip())
                public.serviceReload();
                return public.returnMsg(True, 'SITE_REWRITE_SAVE');

            return public.returnMsg(False, '站点目录不存在！');
        else:
            filename = self.setupPath + '/nginx/conf/rewrite/' + Name + '/' + Name + '.conf'          
            public.writeFile(filename, get.data.strip())
            public.serviceReload();
            return public.returnMsg(True, 'SITE_REWRITE_SAVE');

    #读取xml文件
    def read_xml(self,confPath):
        if os.path.exists(confPath):            
            try:
                tree = ET.parse(confPath)
                return tree
            except :              
                public.writeFile(confPath + '.bt',public.readFile(confPath))            
        return False      
     
    #从文件读取xml转为json对象
    def loads_json(self,xml_path):
        data = {}
        try:
            xml_str = public.readFile(xml_path)
            data = xmltodict.parse(xml_str)
        except :  pass
        return data

    #json对象转为xml文件
    def dumps_json(self,jsonstr):
        xmlstr = xmltodict.unparse(jsonstr)
        return xmlstr

    #格式化xml
    def format_xml(self,xmlStr):
        b = minidom.parseString(xmlStr)
        c = b.toprettyxml(indent = "\t")
        return c
    
    #检测新版配置
    def check_iis_config(self,siteName):
        webType = public.M('sites').where("name=?",(siteName,)).getField('type');        
        if webType == 'PHP' or webType == 'Asp': 
            nget = dict_obj();
            nget.siteName = siteName
            ret = self.get_site_config(nget)         
            if not ret['status']:  return ret;
            config = ret['data']  
            try:
                public.format_xml(config)                
                path = self.get_site_path(siteName)
                if not path: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % siteName); 

                if not os.path.exists(path + '/web_config'): return public.returnMsg(False, '缺少必要目录web_config，您的部分操作将无法生效,请先通过 配置文件->恢复默认配置.<a style="color:#20a53a;" href="https://www.bt.cn/bbs/thread-33097-1-1.html" target="_blank">请求帮助</a>'); 
                if config.find("rewrite.config") >=0:
                    return public.returnMsg(True, '格式正确.'); 

                return public.returnMsg(False, '配置文件格式无法识别，部分功能无法使用，<br/>解决方法：<br/>1、请先通过 配置文件->恢复默认配置.<br/>2、<a style="color:#20a53a;"  href="javascript:;" onclick="site.set_iis_multiple(\''+siteName+'\')">自动解析配置</a> 自动拆分为6.X文件格式。<br/><br/>如不理解请参照 <a style="color:#20a53a;" href="https://www.bt.cn/bbs/thread-33097-1-1.html" target="_blank">IIS6.X配置文件说明</a>'); 
            except :
                return public.returnMsg(False, 'web.config配置文件不是有效的IIS配置格式,请先通过 配置文件->恢复默认配置 <a style="color:#20a53a;" href="https://www.bt.cn/bbs/thread-33097-1-1.html" target="_blank">请求帮助</a>'); 
        else:
            return public.returnMsg(False, '为了防止Asp.Net自带的web.config配置出错，Asp.net程序不支持一键设置此功能，请手动修改web.config文件实现'); 
        return public.returnMsg(True, '非PHP站点跳过检测.'); 
   
    #拆分web.config
    def set_iis_multiple(self,get):
        siteName = get.siteName
        path = self.get_site_path(siteName)
        if not path: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % siteName); 
        if not os.path.exists(path + '/web.config'):
            return public.returnMsg(True, 'web.config配置文件不存在.'); 

        data = public.loads_json(path + '/web.config')    
        self.init_iisSite_config(path + '/web.config',True)
        try:     
            get.data = self.dumps_json(data['configuration']['system.webServer']['rewrite'])
            self.SetSiteRewrite(get)               
        except : pass

        try:
            public.writeFile(path + '/web_config/default.config', self.format_xml(self.dumps_json(data['configuration']['system.webServer']['defaultDocument'])))           
        except : pass

        try:
            public.writeFile(path + '/web_config/httpErrors.config', self.format_xml(self.dumps_json(data['configuration']['system.webServer']['httpErrors'])))           
        except : pass

        public.serviceReload(siteName)
        return public.returnMsg(True, '操作成功，请检查配置文件是否正常.');


    #初始化web.config
    def init_iisSite_config(self,confPath,is_re = False):
        #合并主配置文件
        default_config = {"configuration": {"location": {"@path": ".", "@allowOverride": "false", "@inheritInChildApplications": "false", "system.webServer": {"rewrite": {"rules": {"@configSource": "web_config\\rewrite.config"}}, "defaultDocument": {"@configSource": "web_config\\default.config"}, "httpErrors": {"@configSource": "web_config\\httpErrors.config"}, "handlers": {"@configSource": "web_config\\php.config"}}}}}      
        #创建单个配置文件
        webPath = confPath.replace('web.config','web_config')
        if not os.path.exists(webPath):  os.makedirs(webPath)
        list = [
                { "path":confPath ,"data":default_config},
                { "path":webPath + '/rewrite.config',"data": {"rules": {"clear": {}}}},
                { "path":webPath + '/default.config' ,"data": {"defaultDocument": {"files": {"clear": {}, "add": [{"@value": "index.php"}, {"@value": "index.aspx"}, {"@value": "index.asp"}, {"@value": "default.html"}, {"@value": "Default.htm"}, {"@value": "Default.asp"}, {"@value": "index.htm"}, {"@value": "index.html"}, {"@value": "iisstart.htm"}, {"@value": "default.aspx"}]}}}},
                { "path":webPath + '/httpErrors.config' ,"data":  {"httpErrors": {"@errorMode": "DetailedLocalOnly"}}},
                { "path":webPath + '/php.config' ,"data": {"handlers": {}} }        
            ]

        for x in list:
            if not os.path.exists(x['path']) or is_re:
                public.writeFile(x['path'], self.format_xml(self.dumps_json(x['data'])))              
        return True

    #获取网站默认错误页
    def get_site_error_pages(self,get):
        siteName = get.name
        serverType = public.get_webserver();      
        if serverType == 'iis':            
            check_ret = self.check_iis_config(siteName)
            if not check_ret['status']: return check_ret
       
            lRet = public.ExecShell(self._appcmd + ' list config "' + siteName + '/" /section:httpErrors /config:*',None,None,None,True)
            tmps = re.findall('error\s+statusCode="(\d+)".+subStatusCode="(.+)".+prefixLanguageFilePath="(.*)".+path="(.+)".+responseMode="(.+)"',lRet[0])
            data = []
            for item in tmps:
                if len(item) >= 4:
                    error = { 'statusCode': item[0],'subStatusCode':item[1],'prefixLanguageFilePath':item[2],'path':item[3],'responseMode':item[4] }
                    data.append(error)
            error_model = 'DetailedLocalOnly'
            tmp =  re.search('errorMode="(.+)"\s+existingResponse',lRet[0])
            if tmp: error_model = tmp.groups()[0]
                
            result = {}
            result['list'] = data;
            result['error_model'] = error_model
            return result
        return public.returnMsg(False, '错误页设置仅支持IIS');

    #设置错误页显示模式
    def set_site_error_model(self,get):
        SiteFind = public.M("sites").where("name=?",(get.name,)).field('path,name').find();
        if not SiteFind: return public.returnMsg(False, '操作失败，站点不存在！');

        public.ExecShell(self._appcmd + ' set config "' + get.name + '" -section:system.webServer/httpErrors /errorMode:' + get.error_model)
        return public.returnMsg(True, '修改错误页显示模式成功！');

    #恢复指定编码错误页
    def re_error_page_bycode(self,get):
        code = get.code
        sitePath = self.get_site_path(get.name)
        if not sitePath: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % get.name); 
        
        error_page = sitePath + '/web_config/httpErrors.config';
        config = public.readFile(error_page)
        reg = '\s+.+statusCode="%s.+' % code
        config = re.sub(reg,"",config)
        public.writeFile(error_page,config)
        return public.returnMsg(True, '还原错误页成功！');


    #设置错误页显示
    def set_error_page_bycode(self,get):
        try:
            siteName = get.name
            code = get.code
            SiteFind = public.M("sites").where("name=?",(siteName,)).field('path,name').find();
            if not SiteFind: return public.returnMsg(False, '操作失败，站点不存在！');

            shell = self._appcmd +  ' set config "%s" /section:httpErrors /[statusCode=\'%s\'].path:%s /[statusCode=\'%s\'].prefixLanguageFilePath:"%s" /[statusCode=\'%s\'].responseMode:%s ' % (siteName,code,get.path,code,'',code,get.responseMode)  
            public.ExecShell(shell);
            return public.returnMsg(True, '设置成功！');
        except :
            return public.returnMsg(False, '设置失败！');


    #获取网站详情
    def get_site_info(self,siteName):
        try:
            data = {}
            serverType = public.get_webserver();     
            
            if serverType == 'iis':            
                rRet = public.ExecShell(self._appcmd + ' list site "' + siteName + '" /config',None,None,None,True)
                if not rRet[0]: return False

                data['name'] = siteName          
                data['id'] = re.search('id=\"(\d+)\"',rRet[0]).groups()[0]                       
                try:
                    data['pool'] = re.search('applicationPool=\"(.+)\"',rRet[0]).groups()[0]
                except :
                    data['pool'] = 'DefaultAppPool'

                data['path'] = re.search('physicalPath=\"(.+)\"',rRet[0]).groups()[0].replace('\\','/')

                lRet = public.ExecShell(self._appcmd + ' list config "' + siteName + '/" /section:httpLogging /config:*',None,None,None,True)
                data['logs'] = True
                if lRet[0].find('dontLog="true"') >=0 : data['logs'] = False                    

                data['start'] = True
                if rRet[0].find('serverAutoStart="false"') >=0 : data['start'] = False    
                        
                limit = {}
                connectionTimeout = 0
                tmp1 = re.search('connectionTimeout=\"([\d:]+)\"?',rRet[0])
                if tmp1:
                    timeout = tmp1.groups()[0]
                    ts = time.strptime(timeout,"%H:%M:%S")
                    connectionTimeout = ts.tm_hour * 3600 + ts.tm_min * 60 + ts.tm_sec
                
                maxConnections = 0
                tmp2 = re.search('maxConnections=\"(\d+)\"',rRet[0])
                if tmp2:
                        maxConnections = int(tmp2.groups()[0])
               
                maxBandwidth = 0
                tmp3 = re.search('maxBandwidth=\"(\d+)\"',rRet[0])
                if tmp3:
                        maxBandwidth = int(tmp3.groups()[0])

                if maxConnections == 4294967295: maxConnections = 0
                if maxBandwidth == 4294967295: maxBandwidth = 0              

                limit['perserver'] = maxConnections;
                limit['timeout'] = connectionTimeout
                limit['limit_rate'] = maxBandwidth / 1024
                data['limit'] = limit
                tmps = re.findall('<binding\s+.+/>',rRet[0])
                data['domains'] = []
                for binds in tmps:
                    try:
                        binding = {}
                        b_tmps = re.search('protocol=\"(\w+)\".+:(\d+):(.*)\"',binds).groups()
                        binding['protocol'] = b_tmps[0]
                        binding['port'] = b_tmps[1]
                        binding['domain'] = b_tmps[2]
                        data['domains'].append(binding)   
                    except :
                        pass   
            elif self.serverType == 'apache':
                filename = self.get_conf_path(siteName)
                print(filename)
                conf = public.readFile(filename)
                if not conf: return False
                data['start'] = True
                data['name'] = siteName      
                data['path'] = re.search('DocumentRoot\s"(.+)"',conf).groups()[0]
                data['index'] = re.search('DirectoryIndex\s*(.+)\n',conf).groups()[0]
                data['domains'] = []
            
                list = re.findall("<VirtualHost.*>[\w\W]*?</VirtualHost>",conf)
                for vhost_conf in list:
                    port = re.search('<VirtualHost \*:(\d+)>',vhost_conf).groups()[0]
                    domainstr = re.search('ServerAlias\s+(.+)\n',vhost_conf).groups()[0]
                    for d in domainstr.split(' '):
                        if d:
                            binding = {}
                            arrs = d.split(':')                    
                            binding['domain'] = arrs[0]
                            binding['port'] = port                    
                            data['domains'].append(binding)  
            else:
                filename = self.get_conf_path(siteName)
   
                conf = public.readFile(filename)
                if not conf: return False
                data['start'] = True
                data['name'] = siteName 
                data['path'] = re.search('\s+root(.+);',conf).groups()[0]
                data['index'] = re.search('\s+index\s(.+);',conf).groups()[0]
                data['domains'] = []
                binds = re.search('\s?server_name\s(.+);',conf).groups()[0]
                for d in binds.split(' '):
                    binding = {}
                    arrs = d.split(':')                    
                    binding['domain'] = arrs[0]
                    binding['port'] = 80

                    rep = "listen\s+([0-9]+)\s*;";
                    rtmp = re.search(rep,conf);
                    if rtmp:
                        binding['port'] = rtmp.groups()[0];
                    data['domains'].append(binding)  
    
            return data
        except Exception as ex:
            print(str(ex))
            public.WriteLog("网站信息",str(ex))
            return False

    #日志开关
    def logsOpen(self,get):
        get.name = public.M('sites').where("id=?",(get.id,)).getField('name');
        serverType = public.get_webserver();      
        if serverType == 'iis':
            data = self.get_site_info(get.name)
            dontLog = 'False'
            if data['logs']:  dontLog = 'True'                
            public.ExecShell(self._appcmd + ' set config "' + get.name + '" -section:system.webServer/httpLogging /dontLog:"' + dontLog + '" /commit:apphost')
        elif serverType == 'apache':
            filename = self.get_conf_path(get.name)
            conf = public.readFile(filename);
            if conf.find('#ErrorLog') != -1:
                conf = conf.replace("#ErrorLog","ErrorLog").replace('#CustomLog','CustomLog');
            else:
                conf = conf.replace("ErrorLog","#ErrorLog").replace('CustomLog','#CustomLog');
            public.writeFile(filename,conf);
        else:
            filename = self.get_conf_path(get.name)
            conf = public.readFile(filename);
            rep = public.GetConfigValue('logs_path') + "/"+get.name+".log";
            if conf.find(rep) != -1:
                conf = conf.replace(rep,"off");
            else:
                conf = conf.replace('access_log  off','access_log  ' + rep);
            public.writeFile(filename,conf);

        public.serviceReload(get.name);
        return public.returnMsg(True, 'SUCCESS');

    #取网站日志
    def GetSiteLogs(self,get):       
        logPath = ''
        if self.serverType == 'iis':
            data = self.get_site_info(get.siteName)
            if not data: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % get.siteName); 
       
            tm = time.localtime()

            name = 'u_in'+ str(tm.tm_year)[-2:] + ('%02d' % tm.tm_mon) + ('%02d' % tm.tm_mday)
            logPath = self.setupPath + '/wwwlogs/W3SVC' + data['id'] + '/' + name + '.log';
            if not os.path.exists(logPath):        
                name = 'u_ex'+ str(tm.tm_year)[-2:] + ('%02d' % tm.tm_mon) + ('%02d' % tm.tm_mday)
                logPath = self.setupPath + '/wwwlogs/W3SVC' + data['id'] + '/' + name + '.log';

        elif self.serverType == 'apache':
             logPath = self.setupPath + '/wwwlogs/' + get.siteName + '-access.log'
        else:
            logPath = self.setupPath + '/wwwlogs/' + get.siteName + '.log'
        
        data = {}
        data['path'] = ''
        data['path'] = os.path.dirname(logPath)
        if os.path.exists(logPath):             
            data['status'] = True
            data['msg'] = public.GetNumLines(logPath,1000)
            
            return data;  
        data['status'] = False
        data['msg'] = '日志为空'
        return data; 
    
    #校对IIS日志，部分服务器使用格林时区，校对为北京时区
    def check_log_time(self,get):
        public.ExecShell(self._appcmd + ' set config -section:system.applicationHost/sites /siteDefaults.logFile.localTimeRollover:"true" /siteDefaults.logFile.logFormat:"IIS" /commit:apphost')
        public.serviceReload();
        return public.returnMsg(True, "操作成功"); 

    #取流量限制值
    def GetLimitNet(self,get):
        id = get.id        
        #取回配置文件
        siteName = public.M('sites').where("id=?",(id,)).getField('name');
        data = {}       

        try:
            if self.serverType == 'iis':           
                info = self.get_site_info(siteName)
                data = info['limit']         
               
            elif self.serverType == 'nginx':
                file = self.get_conf_path(siteName)
                conf = public.readFile(file);
            
                rep = "\s+limit_conn\s+perserver\s+([0-9]+);";
                tmp = re.search(rep, conf).groups()
                data['perserver'] = int(tmp[0]);
            
                #IP并发限制
                rep = "\s+limit_conn\s+perip\s+([0-9]+);";
                tmp = re.search(rep, conf).groups()
                data['perip'] = int(tmp[0]);
            
                #请求并发限制
                rep = "\s+limit_rate\s+([0-9]+)\w+;";
                tmp = re.search(rep, conf).groups()
                data['limit_rate'] = int(tmp[0]);
            else:
                return public.returnMsg(False, '流量限制不支持%s' % self.serverType);
        except :
            data['perserver'] = 0
            data['perip'] = 0
            data['limit_rate'] = 0  

        return data;
    
    
    #设置流量限制
    def SetLimitNet(self,get):

        id = get.id;
        siteName = public.M('sites').where("id=?",(id,)).getField('name');
        if siteName:           
            if self.serverType == 'iis':                
                m, s = divmod(int(get.timeout), 60)
                h, m = divmod(m, 60)
                ts = "%02d:%02d:%02d" % (h, m, s)
                public.ExecShell(self._appcmd + ' set config -section:system.applicationHost/sites "/[name=\''+ siteName +'\'].limits.maxConnections:'+ get.perserver +'" /commit:apphost')
                public.ExecShell(self._appcmd + ' set config -section:system.applicationHost/sites "/[name=\''+ siteName +'\'].limits.maxBandwidth:'+ str((int(get.limit_rate) * 1024)) +'" /commit:apphost')
                public.ExecShell(self._appcmd + ' set config -section:system.applicationHost/sites "/[name=\''+ siteName +'\'].limits.connectionTimeout:'+ ts +'" /commit:apphost')
            elif self.serverType == 'nginx':      
                file = self.get_conf_path(siteName)
                conf = public.readFile(file);

                limit_conf = 'limit_conn perserver %s;\n\tlimit_conn perip %s;\n\tlimit_rate %sk;' %  (get.perserver,get.perip,get.limit_rate)
                nconf = ('''#LIMIT_INFO_START
    %s
    #LIMIT_INFO_END''' % (limit_conf))

                rep = "#LIMIT_INFO_START(.|\n)*?#LIMIT_INFO_END";
                conf = re.sub(rep, nconf, conf);
                public.writeFile(file,conf)
                public.serviceReload();
            else:
                return public.returnMsg(False, 'SITE_NETLIMIT_ERR');

            public.WriteLog('TYPE_SITE','SITE_NETLIMIT_OPEN_SUCCESS',(siteName,))
            return public.returnMsg(True, 'SET_SUCCESS');
        return public.returnMsg(False, '设置失败，站点不存在！');
    
    #关闭流量限制
    def CloseLimitNet(self,get):
        id = get.id
        #取回配置文件
        siteName = public.M('sites').where("id=?",(id,)).getField('name');
        if siteName:           
            if self.serverType == 'iis':                                
                public.ExecShell(self._appcmd + ' set config -section:system.applicationHost/sites "/[name=\''+ siteName +'\'].limits.maxBandwidth:4294967295" /commit:apphost')
                public.ExecShell(self._appcmd + ' set config -section:system.applicationHost/sites "/[name=\''+ siteName +'\'].limits.maxConnections:4294967295" /commit:apphost')
                public.ExecShell(self._appcmd + ' set config -section:system.applicationHost/sites "/[name=\''+ siteName +'\'].limits.connectionTimeout:00:02:00" /commit:apphost')
            else:
                file = self.get_conf_path(siteName)
                conf = public.readFile(file);

                rep = "#LIMIT_INFO_START(.|\n)*?#LIMIT_INFO_END";
                conf = re.sub(rep, '''#LIMIT_INFO_START  
    #LIMIT_INFO_END''', conf);
                public.writeFile(file,conf)
                public.serviceReload();

        public.WriteLog('TYPE_SITE','SITE_NETLIMIT_CLOSE_SUCCESS',(siteName,))
        return public.returnMsg(True, 'SITE_NETLIMIT_CLOSE_SUCCESS');   



    #取SSL状态
    def GetSSL(self,get):
        siteName = get.siteName
        serverType = public.get_webserver(); 
        data = {}
        data['status'] = False
        data['httpTohttps'] = False
        data['type'] = -1
        data['cert_data'] = '';
        certPath = self.setupPath + '/panel/vhost/cert/'+ siteName

        import panelSSL
        ss = panelSSL.panelSSL();
        if self.serverType == 'iis':  
            data['data'] = []            
            info = self.get_site_info(siteName)
            if not info: return public.returnMsg(False, '获取网站信息失败，请检查IIS是否存在此网站.');   
            for domain in info['domains']:
                if domain['protocol'] == 'https':
                    data['status'] = True;
                    break;

            #其他证书列表
            ret = self.get_iis_cert_data(get,self.setupPath + '/temp/ssl',data['status'] )
            data['data'] = ret['list']
            data['cert_data'] = ret['cert_data']

        elif self.serverType == 'apache':
            path = os.getenv("BT_SETUP") + '/apache/conf/ssl/' + siteName 
            if not os.path.exists(path): os.makedirs(path)

            file = self.get_conf_path(siteName)
            conf = public.readFile(file)
            if conf:
                if conf.find('SSLCertificateFile') >=0 : data['status'] = True

            csrpath = path + "/fullchain.pem"
            key = public.readFile(path + "/privkey.pem");
            csr = public.readFile(csrpath);
            cert_data = ''
            if csr:
                get.certPath = csrpath               
                cert_data = ss.GetCertName(get)
            data['cert_data'] = cert_data
            data['key'] = key
            data['csr'] = csr 
        else:
            path = os.getenv("BT_SETUP") + '/nginx/conf/ssl/' + siteName 
            if not os.path.exists(path): os.makedirs(path)

            file = self.get_conf_path(siteName)
            conf = public.readFile(file)
            if conf:
                if conf.find('ssl_certificate') >=0 : data['status'] = True

            csrpath = path + "/fullchain.pem"
            key = public.readFile(path + "/privkey.pem");
            csr = public.readFile(csrpath);
            cert_data = ''
            if csr:
                get.certPath = csrpath               
                cert_data = ss.GetCertName(get)
            data['cert_data'] = cert_data
            data['key'] = key
            data['csr'] = csr 
            
        id = public.M('sites').where("name=?",(siteName,)).getField('id');
        data['domain'] = public.M('domain').where("pid=?",(id,)).field('name').select();
        if data['status']: 
            data['type'] = 0           
            if os.path.exists(certPath + '/partnerOrderId'): data['type'] = 2
            if os.path.exists(certPath + '/README'):
                data['type'] = 1
                if self.serverType == 'iis':  
                    ret = self.get_iis_cert_data(get,certPath)
                    data['cert_data'] = ret['cert_data']
            
            #检测是否2008系统
            if not data['cert_data']:
                sys_versions = public.get_sys_version()       
                if int(sys_versions[0]) == 6 and int(sys_versions[1]) == 1:
                    get.certPath = self.setupPath + '/panel/vhost/cert/localhost/fullchain.pfx'
                    data['cert_data'] = ss.GetCertName(get)

        data['httpTohttps'] = self.IsToHttps(siteName);
        return data

    #删除其他证书
    def del_iis_other_ssl(self,get):
        filename = self.setupPath + '/temp/ssl/' + get.filename
        if not os.path.exists(filename): return public.returnMsg(False, '删除失败,文件不存在。');           
        os.remove(filename)
        return public.returnMsg(True, '删除成功。');          

    #获取证书详情
    def get_cert_hasdata(self,siteName):
        try:
            if self.serverType == 'iis':  
                sys_versions = public.get_sys_version()
                bind_exec = 'netsh http show sslcert hostnameport=' + siteName + ':443'                          
                if int(sys_versions[0]) == 6 and int(sys_versions[1]) == 1:
                    bind_exec = 'netsh http show sslcert ipport=0.0.0.0:443'                
                rRet = public.ExecShell(bind_exec)     
                  
                hashStr = re.search(':\s+(\w{40})',rRet[0]).groups()[0].upper()
                return hashStr
        except :
            return None

    #遍历目录获取已部署证书
    def get_iis_cert_data(self,get,tmp_path,status = False):
        import panelSSL
        ss = panelSSL.panelSSL();

        siteName = get.siteName        
        hashStr = self.get_cert_hasdata(siteName)        
        if not os.path.exists(tmp_path): os.makedirs(tmp_path)    
       
        result = {}
        result['list'] = []
        result['cert_data'] = None
        for name in os.listdir(tmp_path):                
            if name[-4:].strip() == '.pfx':
                cert = { 'name' : name, 'password' :'', 'setup':False }
                if os.path.exists(tmp_path + '/' + name[:-4]): cert['password'] = public.readFile(tmp_path + '/' + name[:-4])                    
                       
                get.certPath = tmp_path + '/' + name
                get.password = cert['password']                      
                hashData = ss.GetCertName(get)                   
                if hashData :
                    if hashStr == hashData['hash']: 
                        if status: cert['setup'] = True
                        result['cert_data'] = hashData
                result['list'].append(cert)
        return result

    #获取站点所有域名
    def GetSiteDomains(self,get):
        data = {}
        domains = public.M('domain').where('pid=?',(get.id,)).field('name,id').select()
        binding = public.M('binding').where('pid=?',(get.id,)).field('domain,id').select()
        if type(binding) == str: return binding
        for b in binding:
            tmp = {}
            tmp['name'] = b['domain']
            tmp['id'] = b['id']
            domains.append(tmp)
        data['domains'] = domains
        data['email'] = public.M('users').getField('email')
        if data['email'] == '314866873@qq.com': data['email'] = ''
        return data


     #添加SSL配置
    def SetSSLConf(self,get):         
        siteName = get.siteName                 
        path = self.setupPath + '/panel/vhost/cert/'+ siteName;

        if self.serverType == 'iis':   
            password = ''
            if os.path.exists(path + "/password"):  password = public.readFile(path + "/password")            
            get.certPath = path + "/fullchain.pfx"
            get.password = password            
            result = self.set_cert(get)
            if not result['status']: return result;
        elif self.serverType == 'apache':
            if hasattr(get,'onkey'):
                certpath = '%s/apache/conf/ssl/%s/fullchain.pem' % (self.setupPath,siteName)
                keypath = '%s/apache/conf/ssl/%s/privkey.pem' % (self.setupPath,siteName)

                public.writeFile(certpath,public.readFile(path + '/fullchain.pem'))
                public.writeFile(keypath,public.readFile(path + '/privkey.pem'))
                
            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            if conf:
                if conf.find('SSLCertificateFile') == -1:    
                    
                    phpVersion  = self.GetSitePHPVersion(get)['phpversion']
                    if len(phpVersion) < 2: return public.returnMsg(False,'PHP_GET_ERR')

                    find = public.M('sites').where("name=?", (siteName,)).field('id,path').find()
                    tmp = public.M('domain').where('pid=?', (find['id'],)).field('name').select()
                    domains = ''
                    for key in tmp: domains += key['name'] + ' '
                   
                    info = self.get_site_info(siteName)
                    sslStr = '''<VirtualHost *:443>
	ServerAdmin webmaster@example.com
	DocumentRoot "%s"
	ServerAlias %s
	ErrorLog "%s-error.log"
	CustomLog "%s-access.log" common

	#redirect 重定向
	IncludeOptional conf/redirect/%s/*.conf

	#proxy 反向代理
	IncludeOptional conf/proxy/%s/*.conf
	   
	ErrorDocument 404 /404.html

	#SSL
	SSLEngine On
	SSLCertificateFile conf/ssl/%s/fullchain.pem
	SSLCertificateKeyFile conf/ssl/%s/privkey.pem
	SSLCipherSuite EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH
	SSLProtocol All -SSLv2 -SSLv3
	SSLHonorCipherOrder On

	#DENY FILES
	<Files ~ (\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)$>
		Order allow,deny
		Deny from all
	</Files>

	#PHP
	Include conf/php/%s.conf

	#PATH
	<Directory "%s">
		Options FollowSymLinks ExecCGI
		AllowOverride All
		Require all granted
		DirectoryIndex index.php default.php index.html index.htm default.html default.htm	
	</Directory>
	
</VirtualHost>''' % (info['path'],domains,public.GetConfigValue('logs_path') + '/' + siteName,public.GetConfigValue('logs_path') + '/' + siteName,siteName,siteName,siteName,siteName,phpVersion,info['path'])

                    conf = conf + "\n" + sslStr;
                    self.apacheAddPort('443');   
                    shutil.copyfile(file, self.conf_bak)
                    public.writeFile(file, conf)
        else:
            if hasattr(get,'onkey'):
                certpath = '%s/nginx/conf/ssl/%s/fullchain.pem' % (self.setupPath,siteName)
                keypath = '%s/nginx/conf/ssl/%s/privkey.pem' % (self.setupPath,siteName)

                public.writeFile(certpath,public.readFile(path + '/fullchain.pem'))
                public.writeFile(keypath,public.readFile(path + '/privkey.pem'))

            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            if conf:
                if conf.find('ssl_certificate') == -1:
                    sslStr = """#SSL-INFO-START
    ssl_certificate    ssl/%s/fullchain.pem;
    ssl_certificate_key    ssl/%s/privkey.pem;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!RC4:!DHE;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    error_page 497  https://$host$request_uri; """ % (siteName, siteName);
                    if (conf.find('ssl_certificate') != -1):
                        return public.returnMsg(True, 'SITE_SSL_OPEN_SUCCESS');

                    conf = conf.replace('#SSL-INFO-START', sslStr);
                    # 添加端口
                    rep = "listen\s+([0-9]+)\s*[default_server]*;";
                    tmp = re.findall(rep, conf);
                    if not public.inArray(tmp, '443'):
                       
                        tmp2 = re.search(rep,conf)
                        if tmp2:
                            listen = tmp2.group()
                            default_site = '';
                            if conf.find('default_server') != -1: default_site = ' default_server'

                            listen_ipv6 = ';'
                            if self.is_ipv6: listen_ipv6 = ";\n\tlisten [::]:443 ssl"+ default_site+";"
                            conf = conf.replace(listen,listen + "\n\tlisten 443 ssl" + default_site + listen_ipv6)
                        shutil.copyfile(file, self.conf_bak)
                        public.writeFile(file, conf)

             
        isError = public.checkWebConfig();
        if (isError != True):                       
            if os.path.exists(self.conf_bak): 
                shutil.copyfile(self.conf_bak, file)
                os.remove(self.conf_bak)
                public.serviceReload();
            return public.returnMsg(False, '证书错误: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>');

        sql = public.M('firewall');
        import firewalls
        get.port = '443'
        get.ps = 'HTTPS'
        firewalls.firewalls().AddAcceptPort(get)
        if self.serverType != 'iis':public.serviceReload()

        public.WriteLog('TYPE_SITE', 'SITE_SSL_OPEN_SUCCESS',(siteName,));
        return public.returnMsg(True,'SITE_SSL_OPEN_SUCCESS');

    #保存第三方证书
    def SetSSL(self,get): 
        siteName = get.siteName;
        path = self.setupPath + '/panel/vhost/cert/'+ siteName;
        if not os.path.exists(path): os.makedirs(path)

        if self.serverType == 'iis':          
            if not hasattr(get, 'cerName'):  return public.returnMsg(False, '参数传递错误。');
                
            get.certPath = self.setupPath + '/temp/ssl/' + get.cerName
            result = self.set_cert(get)
            if not result['status']: return result;
            if get.password:  public.writeFile(get.certPath[:-4],get.password)
        else:
            path = os.getenv("BT_SETUP") + '/'+ self.serverType +'/conf/ssl/' + siteName 
            if not os.path.exists(path): os.makedirs(path)
            csrpath = path + "/fullchain.pem";
            keypath = path + "/privkey.pem";

            import panelSSL
            ssl = panelSSL.panelSSL();         

            if (get.key.find('KEY') == -1): return public.returnMsg(False, 'SITE_SSL_ERR_PRIVATE');
            if (get.csr.find('CERTIFICATE') == -1): return public.returnMsg(False, 'SITE_SSL_ERR_CERT');
            public.writeFile('data/cert.pl', get.csr);         
            get.certPath = 'data/cert.pl'
            if not ssl.GetCertName(get): return public.returnMsg(False, '证书错误,请粘贴正确的PEM格式证书!');
            
            #保存站点配置
            public.writeFile(keypath, get.key);
            public.writeFile(csrpath, get.csr);
            result = self.SetSSLConf(get);

            #保存证书夹
            get.keyPath = keypath
            get.certPath = csrpath
            ssl.SaveCert(get);

        
        #清理证书链
        if os.path.exists(path + '/partnerOrderId'): os.remove(path + '/partnerOrderId')
        if os.path.exists(path + '/README'): os.remove(path + '/README')
        if os.path.exists(path + '/account_key.key'): os.remove(path + '/account_key.key')

        public.WriteLog('TYPE_SITE','SITE_SSL_SAVE_SUCCESS');
        return public.returnMsg(True,'SITE_SSL_SUCCESS');

    #设置证书
    def set_cert(self,get):
        siteName = get.siteName;
        serverType = public.get_webserver(); 
        if serverType == 'iis':                       
            import panelSSL,uuid 
            appid = str(uuid.uuid1())
            ssl = panelSSL.panelSSL();
            hashData = ssl.GetCertName(get)
         
            if not hashData: return public.returnMsg(False,'password error');
            p = ' -p ""'
            if get.password: p = ' -p ' + get.password          
            rest = public.ExecShell('certutil ' + p + ' -importPFX ' + get.certPath)
 
            #2008系统特别处理
            version2008 = False
            sys_versions = public.get_sys_version()       
            if int(sys_versions[0]) == 6 and int(sys_versions[1]) == 1:
                version2008 = True
                #08系统保存公用文件
                get.local = '1'
            
            site = public.M('sites').where('name=?',(siteName,)).field('id').find()
            if site:           
                domains = public.M('domain').where('pid=?',(site['id'],)).field('name').select();
                for dom in domains:  
                    new_name = self.DePunycode(dom['name'])

                    public.ExecShell('netsh http delete sslcert hostnameport='+ new_name +':443')
                    public.ExecShell('netsh http delete sslcert ipport=0.0.0.0:443')

                    bind_exec = 'netsh http add sslcert hostnameport=' + new_name + ':443 certhash='+ hashData['hash'] +' certstorename=MY appid={' + appid + '}'
                    if version2008: bind_exec = 'netsh http add sslcert ipport=0.0.0.0:443 certhash='+ hashData['hash'] +' appid={' + appid + '}'
                    public.ExecShell(bind_exec)    
                    
                    public.ExecShell(self._appcmd + " set site " + siteName + " /-bindings.[protocol='https',bindingInformation='*:443:" + new_name + "']")
                    if version2008: public.ExecShell(self._appcmd + " set site " + siteName + " /-bindings.[protocol='https',bindingInformation='*:443:']")
                        
                    ret = public.ExecShell(self._appcmd + " set site " + siteName + " /+bindings.[protocol='https',sslFlags='1',bindingInformation='*:443:" + new_name + "']")
                    if ret[0].find("sslFlags") >=0:
                        public.ExecShell(self._appcmd + " set site " + siteName + " /+bindings.[protocol='https',bindingInformation='*:443:" + new_name + "']")
                     
            ssl.SaveCert(get);
        return public.returnMsg(True,'SITE_SSL_SUCCESS'); 


    #获取域名ssl状态
    def get_iis_ssl_bydomain(self,get):
        if self.serverType != 'iis': return public.returnMsg(False,'此功能仅限IIS使用.');
        
        sys_versions = public.get_sys_version()       
        if int(sys_versions[0]) == 6 and int(sys_versions[1]) == 1: return public.returnMsg(False,'此功能仅限IIS8.5+使用.');

        data = []
        siteName = get.siteName          
        site = public.M('sites').where('name=?',(siteName,)).field('id').find()
        if site: 
           
            slist = self.get_iis_cert_bysitename(siteName)
            domains = public.M('domain').where('pid=?',(site['id'],)).field('name').select();
            for dom in domains:  
                item = {}
                new_name = self.DePunycode(dom['name'])
                hashStr = self.get_cert_hasdata(new_name)

                item['name'] = dom['name']
                item['status'] = False
                if hashStr:                   
                    item['status'] = True                   
                    for cert_data in slist:
                        if  hashStr == cert_data['hash']: 
                            item['cert'] = cert_data;
                            break;  
                    if not 'cert' in item: item['status'] = False
                data.append(item)
   
        return data
    
    #设置单个域名证书
    def set_domain_iis_byfile(self,get):
        domain = get.domain
        path = get.path

        get.certPath = path
        import panelSSL,uuid 
        appid = str(uuid.uuid1())
        ssl = panelSSL.panelSSL();
        hashData = ssl.GetCertName(get)
         
        if not hashData: return public.returnMsg(False,'password error');
        p = ' -p ""'
        if hasattr(get, 'password'): p = ' -p ' + get.password          
        rest = public.ExecShell('certutil ' + p + ' -importPFX ' + get.certPath)
        
        public.ExecShell('netsh http delete sslcert hostnameport='+ domain +':443')
        bind_exec = 'netsh http add sslcert hostnameport=' + domain + ':443 certhash='+ hashData['hash'] +' certstorename=MY appid={' + appid + '}'
        public.ExecShell(bind_exec)
        return public.returnMsg(True,'[%s]部署成功.' % domain);

 

    #获取iis证书文件列表
    def get_iis_ssl_file_list(self,get):
        return self.get_iis_cert_bysitename(get.siteName)

    #获取所有站点目录下证书详情
    def get_iis_cert_bysitename(self,siteName):
        slist = []
        tmp_path = self.setupPath + '/panel/vhost/cert/'+ siteName                                            
        slist = self.get_iis_ssl_bydomain_hash(tmp_path,slist)

        tmp_path  = self.setupPath + '/temp/ssl'
        slist = self.get_iis_ssl_bydomain_hash(tmp_path,slist)

        tmp_path  = self.setupPath + '/panel/vhost/ssl/' + siteName
        slist = self.get_iis_ssl_bydomain_hash(tmp_path,slist)
        return slist;

    #解析网站下所有pfx文件
    def get_iis_ssl_bydomain_hash(self,tmp_path,slist):
        import panelSSL
        ss = panelSSL.panelSSL();
        if not os.path.exists(tmp_path): os.makedirs(tmp_path)
            
        for name in os.listdir(tmp_path):                
            if name[-4:].strip() == '.pfx':
                password = ''
                #主域名
                if name == 'fullchain.pfx':
                    if os.path.exists(tmp_path + '/password'): password = public.readFile(tmp_path + '/password')  
                else:
                    #其他域名
                    if os.path.exists(tmp_path + '/' + name[:-4]): password = public.readFile(tmp_path + '/' + name[:-4])                    
                
                nget = dict_obj();            
                nget.certPath = tmp_path + '/' + name
                nget.password = password              
             
                hashData = ss.GetCertName(nget) 
                if hashData: 
                    hashData['path'] = nget.certPath 
                    #过滤重复
                    is_true = False
                    for x in slist:
                        if x['hash'] == hashData['hash']:
                            is_true = True;
                            break
                    if not is_true: slist.append(hashData) 
                        
        return slist

    #清理SSL配置
    def CloseSSLConf(self,get):
        siteName = get.siteName         
        partnerOrderId =  self.setupPath + '/panel/vhost/cert/'+ siteName + '/partnerOrderId';     
        if os.path.exists(partnerOrderId): os.remove(partnerOrderId)

        letpath =  self.setupPath + '/panel/vhost/cert/'+ siteName + '/README';
        if os.path.exists(letpath): os.remove(letpath)


        if self.serverType == 'iis':            
            public.ExecShell(self._appcmd + " set site " + siteName + " /-bindings.[protocol='https',bindingInformation='*:443:" + siteName + "']")
            site = public.M('sites').where('name=?',(siteName,)).field('id').find()
            if site:           
                domains = public.M('domain').where('pid=?',(site['id'],)).field('name').select();
                for dom in domains:    
                    public.ExecShell(self._appcmd + " set site " + siteName + " /-bindings.[protocol='https',bindingInformation='*:443:" + dom['name'] + "']")

        elif self.serverType == 'apache':
            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            if conf:
                rep = "\n<VirtualHost \*\:443>(.|\n)*?<\/VirtualHost>";
                conf = re.sub(rep, '', conf);
                rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,250}#HTTP_TO_HTTPS_END";
                conf = re.sub(rep, '', conf);   
                public.writeFile(file, conf)       
        else:
            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            rep = "#SSL-INFO-START(.|\n)*?#SSL-INFO-END";
            conf = re.sub(rep, '''#SSL-INFO-START
    #SSL-INFO-END
            ''', conf);
            public.writeFile(file, conf)   
            
        public.WriteLog('TYPE_SITE', 'SITE_SSL_CLOSE_SUCCESS',(siteName,));
        self.CloseToHttps(get);
        return public.returnMsg(True,'SITE_SSL_CLOSE_SUCCESS');

    #设置到期时间
    def SetEdate(self,get):
        result = public.M('sites').where('id=?',(get.id,)).setField('edate',get.edate);
        siteName = public.M('sites').where('id=?',(get.id,)).getField('name');
        public.WriteLog('TYPE_SITE','SITE_EXPIRE_SUCCESS',(siteName,get.edate));
        return public.returnMsg(True,'SITE_EXPIRE_SUCCESS');

    #取网站分类
    def get_site_types(self,get):
        data = public.M("site_types").field("id,name").order("id asc").select()
        if not data: data = []     
        data.insert(0,{"id":0,"name":"默认分类"})
        return data

    #添加网站分类
    def add_site_type(self,get):
        get.name = get.name.strip()
        if not get.name: return public.returnMsg(False,"分类名称不能为空")
        if len(get.name) > 18: return public.returnMsg(False,"分类名称长度不能超过6个汉字或18位字母")
        type_sql = public.M('site_types')
        if type_sql.count() >= 10: return public.returnMsg(False,'最多添加10个分类!')
        if type_sql.where('name=?',(get.name,)).count()>0: return public.returnMsg(False,"指定分类名称已存在!")
        type_sql.add("name",(get.name,))
        return public.returnMsg(True,'添加成功!')

    #删除网站分类
    def remove_site_type(self,get):
        type_sql = public.M('site_types')
        if type_sql.where('id=?',(get.id,)).count()==0: return public.returnMsg(False,"指定分类不存在!")
        type_sql.where('id=?',(get.id,)).delete()
        public.M("sites").where("type_id=?",(get.id,)).save("type_id",(0,))
        return public.returnMsg(True,"分类已删除!")

    #修改网站分类名称
    def modify_site_type_name(self,get):
        get.name = get.name.strip()
        if not get.name: return public.returnMsg(False,"分类名称不能为空")
        if len(get.name) > 18: return public.returnMsg(False,"分类名称长度不能超过6个汉字或18位字母")
        type_sql = public.M('site_types')
        if type_sql.where('id=?',(get.id,)).count()==0: return public.returnMsg(False,"指定分类不存在!")
        type_sql.where('id=?',(get.id,)).setField('name',get.name)
        return public.returnMsg(True,"修改成功!")

    #设置指定站点的分类
    def set_site_type(self,get):
        site_ids = json.loads(get.site_ids)
        site_sql = public.M("sites")
        for s_id in site_ids:
            site_sql.where("id=?",(s_id,)).setField("type_id",get.id)
        return public.returnMsg(True,"设置成功!") 

    #设置防盗链
    def SetSecurity(self,get):
        if self.serverType == 'iis':
            rules = []
            if get.status == 'true':                
                fix = get.fix.replace(',','|')
                domains = []
                for domain in get.domains.split(','):  domains.append({"@input": "{HTTP_REFERER}", "@pattern": "://" + domain + "/.*", "@negate": "true"})
               
                security = {"@name": "iis_security", "match": {"@url": "^.*\\.(" + fix + ")$", "@ignoreCase": "true"}, "conditions": {"add": domains }, "action": {"@type": "Rewrite", "@url": "/404.htm"}}
                rules = [ security ]
            
            data = self.get_config_rules(get.name)
            for x in data['rules']['rule']:
                    if x['@name'] != 'iis_security': rules.append(x)
            data['rules']['rule'] = rules            
            self.set_config_rules(get.name,data)

            return public.returnMsg(True,"修改网站["+ get.name +"]防盗链成功！") 
        elif self.serverType == 'apache':     
            file = self.get_conf_path(get.name)
            if os.path.exists(file):
                conf = public.readFile(file);
                if conf.find('SECURITY-START') != -1:
                    rep = "#SECURITY-START(\n|.){1,500}#SECURITY-END\n";
                    conf = re.sub(rep,'',conf);
                else:
                    tmp = "    RewriteCond %{HTTP_REFERER} !{DOMAIN} [NC]";
                    tmps = [];
                    for d in get.domains.split(','):
                        tmps.append(tmp.replace('{DOMAIN}',d));
                    domains = "\n".join(tmps);
                    rconf = "common\n    #SECURITY-START 防盗链配置\n    RewriteEngine on\n    RewriteCond %{HTTP_REFERER} !^$ [NC]\n" + domains + "\n    RewriteRule .("+get.fix.strip().replace(',','|')+") /404.html [R=404,NC,L]\n    #SECURITY-END"
                    conf = conf.replace('common',rconf)
                public.writeFile(file,conf);  
                public.serviceReload();
            return public.returnMsg(True,"修改网站["+ get.name +"]防盗链成功！") 
        elif self.serverType == 'nginx':
            file = self.get_conf_path(get.name)
            conf = public.readFile(file);
            if conf:
                if conf.find('SECURITY-START') != -1:
                    rep = "\s{0,4}#SECURITY-START(\n|.){1,500}#SECURITY-END\n?";
                    conf = re.sub(rep,'',conf);
                    public.WriteLog('网站管理','站点['+get.name+']已关闭防盗链设置!');
                else:
                    rconf = '''#SECURITY-START 防盗链配置
    location ~ .*\.(%s)$
    {
        expires      30d;
        access_log off;
        valid_referers none blocked %s;
        if ($invalid_referer){
            return 404;
        }
    }
    #SECURITY-END

    #LIMIT_INFO_START''' % (get.fix.strip().replace(',','|'),get.domains.strip().replace(',',' '))
                    conf = re.sub("#LIMIT_INFO_START",rconf,conf);
                    public.WriteLog('网站管理','站点['+get.name+']已开启防盗链!');
            public.writeFile(file,conf);
            public.serviceReload();

    #获取防盗链状态
    def GetSecurity(self,get):
       
        data = {}
        if self.serverType == 'iis':
            check_ret = self.check_iis_config(get.name)
            if not check_ret['status']: return check_ret
   
            config = self.get_config_rules(get.name)
            if not config:  return public.returnMsg(False, '网站目录获取失败，请检查IIS是否存在此网站.')

            security = None
            for x in config['rules']['rule']:
                if x['@name'] == 'iis_security':  security = x                    
            
            if security:                
                list = security['conditions']['add'];
                if type(list) != type([1,]): list = [list]
            
                domains = []
                for item in list:
                    match = re.search(':/+(.+)/.+',item['@pattern'])
                    if match:domains.append(match.groups()[0])
                data['domains'] =  ','.join(domains);    
                fix = ''
                match = re.search('\((.+)\)',security['match']['@url'])
                if match: fix = match.groups()[0].replace('|',',')
                data['fix'] = fix
                data['status'] = True        
                return data;

        elif self.serverType == 'apache':
            file = self.get_conf_path(get.name)
            if os.path.exists(file):
                conf = public.readFile(file)
                if conf.find('SECURITY-START') != -1:
                    rep = "#SECURITY-START(\n|.){1,500}#SECURITY-END";
                    tmp = re.search(rep,conf).group()
                    data['fix'] = re.search("\(([\w|]+)\)\s+",tmp).group().replace('(','').replace(') ','').replace('|',',');
                    domains = []
                    list = re.findall("{HTTP_REFERER}\s+!(.+)\s+\[NC",tmp)
                    for x in list:
                        if x == '^$': continue;
                        domains.append(x)
                    data['domains'] = ','.join(domains);
                    data['status'] = True;
                    return data;
        else:
            file = self.get_conf_path(get.name)
            conf = public.readFile(file)
            if conf:                
                if conf.find('SECURITY-START') != -1:
                    rep = "#SECURITY-START(\n|.){1,500}#SECURITY-END";
                    tmp = re.search(rep,conf)
                    if tmp:
                        tmp = tmp.group()
                        tmp2 = re.search("\(.+\)\$",tmp)
                                  
                        data['fix'] = tmp2.group().replace('(','').replace(')$','').replace('|',',');
                        data['domains'] = ','.join(re.search("valid_referers\s+none\s+blocked\s+(.+);\n",tmp).groups()[0].split());
                        data['status'] = True;
                        return data
        
        data['fix'] = 'jpg,jpeg,gif,png,js,css';
        domains = public.M('domain').where('pid=?',(get.id,)).field('name').select();
        tmp = [];
        for domain in domains:
            tmp.append(domain['name']);
        data['domains'] = ','.join(tmp);
        data['status'] = 0
        return data;


    #获取https配置json
    def get_site_https(self,siteName):             
        old_data = self.get_config_rules(siteName)
        rules = []
        for rule in old_data['rules']['rule']:
            if rule['@name'].find('_toHttps') < 0:
                rules.append(rule)
       
        old_data['rules']['rule'] = rules   
        return old_data

    #HttpToHttps
    def HttpToHttps(self,get):
        siteName = get.siteName;
        if self.serverType == 'iis':  
            check_ret = self.check_iis_config(siteName)
            if not check_ret['status']: return check_ret

            sitePath = self.get_site_path(siteName)
            if not sitePath: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % siteName); 

            data = self.get_site_https(siteName)
            https = {"@name": "http_toHttps", "@stopProcessing": "true", "match": {"@url": "(.*)"}, "conditions": {"add": {"@input": "{HTTPS}", "@pattern": "off", "@ignoreCase": "true"}}, "action": {"@type": "Redirect", "@redirectType": "Permanent", "@url": "https://{HTTP_HOST}/{R:1}"}}
            data['rules']['rule'].insert(0,https)    
          
            self.set_config_rules(siteName,data)
        elif self.serverType == 'apache':
            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            if conf:
                httpTohttos = '''common
    #HTTP_TO_HTTPS_START
    <IfModule mod_rewrite.c>
        RewriteEngine on
        RewriteCond %{SERVER_PORT} !^443$
        RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
    </IfModule>
    #HTTP_TO_HTTPS_END'''
                conf = re.sub('common',httpTohttos,conf,1);
                public.writeFile(file,conf);
            public.serviceReload();
        else:
            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            if conf:
                httpTohttos = '''#HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }'''
                conf = re.sub('#HTTP_TO_HTTPS_START',httpTohttos,conf,1);
                public.writeFile(file,conf);
            public.serviceReload();
        return public.returnMsg(True,'SET_SUCCESS');
    
    #CloseToHttps
    def CloseToHttps(self,get):
        siteName = get.siteName;
        if self.serverType == 'iis':   

            data = self.get_site_https(siteName)             
            self.set_config_rules(siteName,data)
        elif self.serverType == 'apache':          
            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            if conf:
                rep = "\n\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END";
                conf = re.sub(rep,'',conf);
                public.writeFile(file,conf);
            public.serviceReload();
        else:
            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            rep = "#HTTP_TO_HTTPS_START(.|\n)*?#HTTP_TO_HTTPS_END";
            conf = re.sub(rep, '''#HTTP_TO_HTTPS_START
    #HTTP_TO_HTTPS_END''', conf);
            public.writeFile(file, conf)   
            public.serviceReload();
        return public.returnMsg(True,'SET_SUCCESS');

    #是否跳转到https
    def IsToHttps(self,siteName):
        if self.serverType == 'iis':     
            try:
                check_ret = self.check_iis_config(siteName)
                if not check_ret['status']: return False

                old_data = self.get_config_rules(siteName)
                for rule in old_data['rules']['rule']:                           
                    if rule['@name'].find('_toHttps') >= 0: return True
            except :
                return False
        else:
            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            if conf:
                if self.serverType == 'apache':    
                    if conf.find('HTTP_TO_HTTPS_START') != -1: return True;
                else:
                    if conf.find('$server_port !~ 443') != -1: return True;
        return False;


      #打包
    def ToBackup(self,get):
        id = get.id;
        find = public.M('sites').where("id=?",(id,)).field('name,path,id').find();
        if not find: return public.returnMsg(False, '缺少必要参数网站ID，请重新操作.');
            
        import time,files
        fileName = find['name']+'_'+time.strftime('%Y%m%d_%H%M%S',time.localtime())+'.zip';
        backupPath = session['config']['backup_path'] + '/site'
        zipName = backupPath + '/'+fileName;
        if not (os.path.exists(backupPath)): os.makedirs(backupPath)

        zipget  = dict_obj();
        zipget.path = find['path']
        zipget.sfile = ''
        zipget.dfile = zipName
        rRet = files.files().Zip(zipget)
        if not rRet['status']:  return rRet

        sql = public.M('backup').add('type,name,pid,filename,size,addtime',(0,fileName,find['id'],zipName,0,public.getDate()));
        public.WriteLog('TYPE_SITE', 'SITE_BACKUP_SUCCESS',(find['name'],));
        return public.returnMsg(True, 'BACKUP_SUCCESS');
        
    #删除备份文件
    def DelBackup(self,get):
        id = get.id
        where = "id=?";
        filename = public.M('backup').where(where,(id,)).getField('filename');
        if os.path.exists(filename): os.remove(filename)
        name = '';
        if filename == 'qiniu':
            name = public.M('backup').where(where,(id,)).getField('name');
            public.ExecShell(public.get_run_python("[PYTHON] "+self.setupPath + '/panel/script/backup_qiniu.py delete_file ' + name))
        
        public.WriteLog('TYPE_SITE', 'SITE_BACKUP_DEL_SUCCESS',(name,filename));
        public.M('backup').where(where,(id,)).delete();
        return public.returnMsg(True, 'DEL_SUCCESS');

    #取默认站点
    def GetDefaultSite(self,get):
        data = {}
        data['sites'] = public.M('sites').field('name').order('id desc').select();
        data['defaultSite'] = ''
        if self.serverType == 'iis':
            siteName = 'Default Web Site'
            info = self.get_site_info(siteName)
            if not info:
                self.CreatePool('DefaultAppPool')             
                public.ExecShell(self._appcmd + ' add site /name:"' + siteName + '" /bindings:"http/*:80:" /physicalPath:"%SystemDrive%\\inetpub\\wwwroot"' )  
                public.ExecShell(self._appcmd + ' set app "' + siteName + '/" /applicationPool:"DefaultAppPool"') 

                data['defaultSite'] = siteName
            else:
                data['defaultSite'] = public.readFile('data/defaultSite.pl');
        elif self.serverType == 'apache':
            path = self.setupPath + '/apache/htdocs/.htaccess';         
            if os.path.exists(path):                
                conf = public.readFile(path)
                if conf:
                    data['defaultSite'] = public.readFile('data/defaultSite.pl');
        else:
            data['defaultSite'] = public.readFile('data/defaultSite.pl');
        return data;


     #设置默认站点
    def SetDefaultSite(self,get):
        import time, files      
        #清理旧的
        defaultSite = public.readFile('data/defaultSite.pl')
        if self.serverType == 'iis':
            fileObj =  files.files()
            if defaultSite:
                find = public.M('sites').where('name=?',(defaultSite,)).field('name,path').find();
                if find:
                    get_new = dict_obj();
                    get_new.filename = find['path']
                    get_new.user = 'DefaultAppPool'
                    fileObj.DelFileAccess(get_new)

            #处理新的
            find = public.M('sites').where('name=?',(get.name,)).field('name,path').find();
            default_path = '%SystemDrive%\\inetpub\\wwwroot'
            if find: default_path = find['path']
            result = public.ExecShell(self._appcmd + ' set app "Default Web Site/" -[path=\'/\'].physicalPath:' + default_path.replace('/','\\'))

            get_new = dict_obj();
            get_new.filename = default_path
            get_new.user = 'DefaultAppPool'
            get_new.access = 2032127
            fileObj.SetFileAccess(get_new)
        elif self.serverType == 'apache':
            #处理新的
            path = self.setupPath + '/apache/htdocs';
            if os.path.exists(path):
                conf = '''<IfModule mod_rewrite.c>
      RewriteEngine on
      RewriteRule (.*) http://%s/$1 [L]
    </IfModule>''' % (get.name,)
                if get.name == 'off': conf = '';
                public.writeFile(path + '/.htaccess',conf);

            http_conf = public.readFile(self.setupPath + '/apache/conf/httpd.conf')
            temp = re.search('<Directory.*htdocs([\w\W]+?)</\Directory>', http_conf).group();
            if temp:
                if temp.find("AllowOverride None") >= 0:
                    new_conf = temp.replace('AllowOverride None','AllowOverride all')
                    http_conf = http_conf.replace(temp,new_conf)
                    public.writeFile(self.setupPath + '/apache/conf/httpd.conf',http_conf)
        elif self.serverType == 'nginx':
            if defaultSite:
                path = self.get_conf_path(defaultSite);
                conf = public.readFile(path);
                if conf: 
                    conf = conf.replace("default_server","");
                    public.writeFile(path,conf);
                #处理新的
                path = self.get_conf_path(get.name);
                if not path or not os.path.exists(path): return public.returnMsg(False,'操作失败，请检查Nginx是否存在此网站.');
                    
                conf = public.readFile(path);
                rep = "listen\s+80\s*;"
                conf = re.sub(rep,'listen 80 default_server;',conf,1);
                rep = "listen\s+443\s*ssl\s*\w*\s*;"
                conf = re.sub(rep,'listen 443 ssl default_server;',conf,1);
                public.writeFile(path,conf);

        public.writeFile('data/defaultSite.pl',get.name);
        if self.serverType != 'iis':public.serviceReload()
        return public.returnMsg(True,'SET_SUCCESS');

    
    #检测参数
    def check_proxy_config(self,get):
        name = get.proxyname;
        tourl = get.tourl;
        if not name or not tourl:
            return public.returnMsg(False,'参数传递错误！')

        rep = "^((https|http)?:\/\/)[^\s]+"
        if not re.match(rep, get.tourl):
            return public.returnMsg(False, '目标URL格式不对 %s' + get.tourl)

    # 取重定向配置文件
    def GetProxyFile(self,get):
        import files
    
        sitename = get.sitename
        proxyname = get.proxyname
        get.path = self.setupPath + '/'+self.serverType + '/conf/proxy/' + sitename+'/'+ proxyname + '.conf'
       
        f = files.files()
        return f.GetFileBody(get),get.path

    # 保存代理配置文件
    def SaveProxyFile(self,get):
        import files
        f = files.files()
        ret = f.SaveFileBody(get)
        public.serviceReload();
        return ret


    #获取反向代理列表
    def GetProxyList(self,get):
        siteName = get.sitename
        if self.serverType == 'iis':
            check_ret = self.check_iis_config(siteName)
            if not check_ret['status']: return check_ret

            lRet = public.ExecShell(self._appcmd + ' list config /section:proxy /config:*')
            if lRet[0].find('ERROR') >=0:  
                return public.returnMsg(False,'扩展未安装，请在软件管理->IIS设置进行安装<a href="/soft" style="color:#20a53a; float: left;">去安装</a>.'); 

        rpath = 'data/proxy';
        if not os.path.exists(rpath): os.makedirs(rpath)
        
        path = rpath + '/'+ siteName +'.conf'
        data = []
        if os.path.exists(path):
            data = json.loads(public.readFile(path))        
        return data
   
    #获取反向代理参数
    def get_proxy_args(self,get):
        self.check_proxy_config(get)      
       
        obj =  {
            "sitename":get.sitename,
            "proxyname":get.proxyname,
            "tourl":get.tourl.rstrip('/'),
            "proxydomains":json.loads(get.proxydomains),
            "to_domian":get.to_domian,           
            "open":int(get.open),
            "root_path":'',
            "cache_open":int(get.cache_open),
            "path_open":int(get.path_open),
            "sub1":'',
            "sub2":''
        }

        if hasattr(get,'root_path'): obj["root_path"] = get.root_path

        if hasattr(get,'sub1'):
            obj["sub1"] = get.sub1
            obj["sub2"] = get.sub2

        return obj

    #创建反向代理
    def CreateProxy(self,get):
        obj = self.get_proxy_args(get)

        if self.serverType == 'apache':
            obj['cache_open'] = 0;

        Name =  get.sitename;      
        list = self.GetProxyList(get)
        list.append(obj)        
        public.writeFile('data/proxy/' + Name +'.conf',json.dumps(list))

        if self.serverType == 'iis':
            if obj['open'] == 1:    
                root_path = ''
                if obj['path_open'] == 1:
                    root_path = obj['root_path']
                    if root_path == '/': root_path = '';

                    if not re.match('^/.+', root_path):
                        return public.returnMsg(False, '代理目录格式不正确,应以/开头 %s' + root_path)
                old_paths = []
                for x in obj['proxydomains']: old_paths.append({"@input": "{HTTP_HOST}", "@pattern": "^" + x + root_path})
   
                proxys = {"@name": obj['proxyname'] + "_proxy", "match": {"@url": "^(.*)"}, "conditions": {"@logicalGrouping": "MatchAny", "add": old_paths }, "action": {"@type": "Rewrite", "@url": obj['tourl'] + "/{R:1}"}}
                data = self.get_config_rules(Name)
                data['rules']['rule'].append(proxys)            
                self.set_config_rules(Name,data)

            return public.returnMsg(True,'添加反向代理成功！')
        elif self.serverType == 'apache':
            pPath = self.setupPath + '/apache/conf/proxy/' + Name
            if not os.path.exists(pPath): os.makedirs(pPath)
            if obj['open'] == 1: 
                root_path = '/'
                if obj['path_open'] == 1:
                    root_path = obj['root_path']
                proxys = '''<IfModule mod_proxy.c>
    ProxyRequests Off
    SSLProxyEngine on
    ProxyPass %s %s/
    ProxyPassReverse %s %s/
</IfModule>
    ''' % (root_path,obj['tourl'],root_path,obj['tourl'])
                public.writeFile(pPath + '/' + obj['proxyname'] + '.conf',proxys)
            public.serviceReload();
            return public.returnMsg(True,'添加反向代理成功！')    
        else:
            pPath = self.setupPath + '/nginx/conf/proxy/' + Name
            if not os.path.exists(pPath): os.makedirs(pPath)
            if obj['open'] == 1: 
                root_path = '/'
                if obj['path_open'] == 1:
                    root_path = obj['root_path']

                substr = ''
                sub1s = obj['sub1'].split(',')
                sub2s = obj['sub2'].split(',')
                for i in range(len(sub1s)):
                    if sub1s[i]:
                        substr += 'sub_filter "'+ sub1s[i] +'" "'+ sub2s[i] +'";\n\t'
                proxys = '''location %s
{
    expires 12h;
    if ($request_uri ~* "(php|jsp|cgi|asp|aspx)")
    {
         expires 0;
    }
    proxy_pass %s;
    proxy_set_header Host %s;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header REMOTE-HOST $remote_addr;

    add_header Cache-Control no-cache;
    add_header X-Cache $upstream_cache_status;
        
    proxy_set_header Accept-Encoding "";
	%s
    sub_filter_once off;
    
    #开启缓存
    #proxy_cache cache_one;
    #proxy_cache_key $host$uri$is_args$args;
    #proxy_cache_valid 200 304 301 302 12h;
}''' % (root_path,obj['tourl'],obj['to_domian'],substr.strip())
                public.writeFile(pPath + '/' + obj['proxyname'] + '.conf',proxys)
                public.serviceReload();
                return public.returnMsg(True,'添加反向代理成功！')   

    #修改反向代理
    def ModifyProxy(self,get):      
        obj = self.get_proxy_args(get)

        Name =  get.sitename;
        list = self.GetProxyList(get)
        new_list = [obj]
        for x in list:
            if x['proxyname'] != obj['proxyname']: new_list.append(x)
        public.writeFile('data/proxy/' + Name +'.conf',json.dumps(new_list))
        
        if self.serverType == 'iis':
            rules = []
            if obj['open'] == 1:  
                root_path = ''
                if obj['path_open'] == 1:
                    root_path = obj['root_path']
                    if root_path == '/': root_path = '';
                    if not re.match('^/.+', root_path):
                        return public.returnMsg(False, '代理目录格式不正确,应以/开头 %s' + root_path)
                old_paths = []
                for x in obj['proxydomains']: old_paths.append({"@input": "{HTTP_HOST}", "@pattern": "^" + x + root_path})
   
                proxys = {"@name": obj['proxyname'] + "_proxy", "match": {"@url": "^(.*)"}, "conditions": {"@logicalGrouping": "MatchAny", "add": old_paths }, "action": {"@type": "Rewrite", "@url": obj['tourl'] + "/{R:1}"}}                  
                rules = [proxys]

            data = self.get_config_rules(Name)
            for x in data['rules']['rule']:
                    if x['@name'] != (obj['proxyname'] + '_proxy'): rules.append(x)
            data['rules']['rule'] = rules            
            self.set_config_rules(Name,data)

            return public.returnMsg(True,'修改反向代理成功！')
        elif self.serverType == 'apache':
            pPath = self.setupPath + '/apache/conf/proxy/' + Name
            if not os.path.exists(pPath): os.makedirs(pPath)
            if obj['open'] == 1:  
                root_path = '/'
                if obj['path_open'] == 1:
                    root_path = obj['root_path']
                proxys = '''<IfModule mod_proxy.c>
    ProxyRequests Off
    SSLProxyEngine on
    ProxyPass %s %s/
    ProxyPassReverse %s %s/
</IfModule>
    ''' % (root_path,obj['tourl'],root_path,obj['tourl'])
                public.writeFile(pPath + '/' + obj['proxyname'] + '.conf',proxys)
            else:
                if os.path.exists(pPath + '/' + obj['proxyname'] + '.conf'): os.remove(pPath + '/' + obj['proxyname'] + '.conf')
            public.serviceReload();
            return public.returnMsg(True,'修改反向代理成功！') 
        else:
            pPath = self.setupPath + '/nginx/conf/proxy/' + Name
            if not os.path.exists(pPath): os.makedirs(pPath)
            if obj['open'] == 1: 
                root_path = '/'
                if obj['path_open'] == 1:
                    root_path = obj['root_path']

                substr = ''
                sub1s = obj['sub1'].split(',')
                sub2s = obj['sub2'].split(',')
                for i in range(len(sub1s)):
                    if sub1s[i]:
                        substr += 'sub_filter "'+ sub1s[i] +'" "'+ sub2s[i] +'";\n\t'
                proxys = '''location %s
{
    expires 12h;
    if ($request_uri ~* "(php|jsp|cgi|asp|aspx)")
    {
         expires 0;
    }
    proxy_pass %s;
    proxy_set_header Host %s;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header REMOTE-HOST $remote_addr;

    add_header X-Cache $upstream_cache_status;
    
    proxy_set_header Accept-Encoding "";
	%s
    sub_filter_once off;
    
    proxy_cache cache_one;
    proxy_cache_key $host$uri$is_args$args;
    proxy_cache_valid 200 304 301 302 12h;
}''' % (root_path,obj['tourl'],obj['to_domian'],substr.strip())
                public.writeFile(pPath + '/' + obj['proxyname'] + '.conf',proxys)
            public.serviceReload();
            return public.returnMsg(True,'修改反向代理成功！') 


    #删除反向代理
    def RemoveProxy(self,get):
        siteName = get.sitename
        proxyname = get.proxyname
        if self.serverType == 'iis':
            data = self.get_config_rules(siteName)
            rules = []
            for x in data['rules']['rule']:               
                if x['@name'] != (proxyname + '_proxy'):  
                    rules.append(x)
            data['rules']['rule'] = rules
            self.set_config_rules(siteName,data)
        elif self.serverType == 'apache':
            pPath = self.setupPath + '/apache/conf/proxy/' + siteName
            if not os.path.exists(pPath): os.makedirs(pPath)
            if os.path.exists(pPath + '/' + proxyname + '.conf'): os.remove(pPath + '/' + proxyname + '.conf')
            public.serviceReload();
        else:
            pPath = self.setupPath + '/nginx/conf/proxy/' + siteName
            if not os.path.exists(pPath): os.makedirs(pPath)
            if os.path.exists(pPath + '/' + proxyname + '.conf'): os.remove(pPath + '/' + proxyname + '.conf')
            public.serviceReload();

        path = 'data/proxy/' + siteName + '.conf'
        data = []
        if os.path.exists(path):
            list = json.loads(public.readFile(path))
            for x in list:
                if x['proxyname'] != proxyname:
                    data.append(x)
        public.writeFile(path,json.dumps(data))        
        return public.returnMsg(True,'删除反向代理规则成功！')

    
    #获取重定向列表
    def GetRedirectList(self,get):
        siteName = get.sitename

        if self.serverType == 'iis':
            check_ret = self.check_iis_config(siteName)
            if not check_ret['status']: return check_ret

        rpath = 'data/redirect';
        if not os.path.exists(rpath): os.makedirs(rpath)
        
        path = rpath + '/'+ siteName +'.conf'
        data = []
        if os.path.exists(path):
            data = json.loads(public.readFile(path))        
        return data
   
    #获取重定向参数
    def get_redirect_args(self,get):
        self.check_redirect_config(get)
        obj =  {
            "sitename":get.sitename,
            "redirectname":get.redirectname,
            "tourl":get.tourl,
            "redirectdomain":json.loads(get.redirectdomain),
            "redirectpath":get.redirectpath,
            "redirecttype":get.redirecttype,
            "type":int(get.type),
            "domainorpath":get.domainorpath,
            "holdpath":int(get.holdpath)
        }
        return obj

    #创建重定向
    def CreateRedirect(self,get):
        obj = self.get_redirect_args(get)
        Name =  get.sitename;        
        list = self.GetRedirectList(get)
        list.append(obj)        
        public.writeFile('data/redirect/' + Name +'.conf',json.dumps(list))

        if self.serverType == 'iis':
            if obj['type'] == 1:    
                
                redirecttype = 'Permanent'
                if get.redirecttype == '302': redirecttype = 'Found'
                new_path = obj['tourl'];
                if obj['holdpath'] == 1: new_path = new_path.rstrip() + '/{R:0}' 

                old_paths = []
                if get.domainorpath == 'path':
                    old_paths.append({"@input": "{HTTP_HOST}", "@pattern": "^" + get.redirectpath})
                else:
                    for x in obj['redirectdomain']: old_paths.append({"@input": "{HTTP_HOST}", "@pattern": "^" + x})

                redirects = {"@name": obj['redirectname'] + "_redirect", "@stopProcessing": "true", "match": {"@url": "(.*)"}, "conditions": {"@logicalGrouping":"MatchAny","add": old_paths }, "action": {"@type": "Redirect", "@redirectType": redirecttype, "@url": new_path}}

                data = self.get_config_rules(Name)
                data['rules']['rule'].append(redirects)            
                self.set_config_rules(Name,data)

            return public.returnMsg(True,'添加重定向成功！')
        elif self.serverType == 'apache':
            pPath = self.setupPath + '/apache/conf/redirect/' + Name
            if not os.path.exists(pPath): os.makedirs(pPath)
            if obj['type'] == 1: 
                          
                new_path = obj['tourl']
                if obj['holdpath'] == 1: new_path = new_path.rstrip() + '$1' 

                redirectpath = ''   
                config = ''
                if get.domainorpath == 'path': 
                    redirectpath = get.redirectpath
                    redirects = '''<IfModule mod_rewrite.c>
	RewriteEngine on
	RewriteRule ^%s(.*) %s [L,R=%s]
</IfModule>''' % (redirectpath,new_path,get.redirecttype)
                    config += redirects + '\n\n'
                else:
                   
                    for x in obj['redirectdomain']:                       
                        redirects = '''<IfModule mod_rewrite.c>
	RewriteEngine on
	%s
	RewriteRule ^%s(.*) %s [L,R=%s]
</IfModule>''' % ('RewriteCond %{HTTP_HOST} ^'+ x +' [NC]',redirectpath,new_path,get.redirecttype)

                        config += redirects + '\n\n'

                public.writeFile(pPath + '/' + obj['redirectname'] + '.conf',config)
                public.serviceReload();
                return public.returnMsg(True,'添加重定向成功！')    
        else:
            pPath = self.setupPath + '/nginx/conf/redirect/' + Name
            if not os.path.exists(pPath): os.makedirs(pPath)
            if obj['type'] == 1: 
                      
                redirectpath = ''   
                config = ''
                if get.domainorpath == 'path': 
                    new_path = obj['tourl']
                    if obj['holdpath'] == 1: new_path = new_path.rstrip() + '$1'
                    
                    redirecttype = 'permanent'
                    if get.redirecttype == '302': redirecttype = 'redirect'
                    redirects = 'rewrite ^%s(.*) %s %s;' % (get.redirectpath,new_path,redirecttype)  

                    config += redirects + '\n\n'      
                else:
                    new_path = obj['tourl']
                    if obj['holdpath'] == 1: new_path = new_path.rstrip() + '$request_uri'

                    for x in obj['redirectdomain']:    
                        redirects = '''if ($host ~ '^%s'){
    return %s %s;
}''' % (x,get.redirecttype,new_path)
                        config += redirects + '\n\n'

            public.writeFile(pPath + '/' + obj['redirectname'] + '.conf',config)
            public.serviceReload();
            return public.returnMsg(True,'添加重定向成功！')
    
    #修改重定向
    def ModifyRedirect(self,get):
        obj = self.get_redirect_args(get)

        Name =  get.sitename;  
        list = self.GetRedirectList(get)
        new_list = [obj]
        for x in list:
            if x['redirectname'] != obj['redirectname']: new_list.append(x)
        public.writeFile('data/redirect/' + Name +'.conf',json.dumps(new_list))
        
        if self.serverType == 'iis':
            rules = []
            if obj['type'] == 1:                               
                redirecttype = 'Permanent'
                if get.redirecttype == '302': redirecttype = 'Found'
                new_path = obj['tourl'];
                if obj['type'] == 1: new_path = new_path.rstrip() + '/{R:0}' 

                old_paths = []
                if get.domainorpath == 'path':
                    old_paths.append({"@input": "{HTTP_HOST}", "@pattern": "^" + get.redirectpath})
                else:
                    for x in obj['redirectdomain']: old_paths.append({"@input": "{HTTP_HOST}", "@pattern": "^" + x})

                redirects = {"@name": obj['redirectname'] + "_redirect", "@stopProcessing": "true", "match": {"@url": "(.*)"}, "conditions": {"@logicalGrouping":"MatchAny","add": old_paths }, "action": {"@type": "Redirect", "@redirectType": redirecttype, "@url": new_path}}            
                rules = [redirects]

            data = self.get_config_rules(Name)
            for x in data['rules']['rule']:
                    if x['@name'] != (get.redirectname + '_redirect'): rules.append(x)
            data['rules']['rule'] = rules            
            self.set_config_rules(Name,data)
            return public.returnMsg(True,'修改重定向成功！')
        elif self.serverType == 'apache':
            pPath = self.setupPath + '/apache/conf/redirect/' + Name
            if not os.path.exists(pPath): os.makedirs(pPath)
            if obj['type'] == 1: 
                new_path = obj['tourl']
                if obj['holdpath'] == 1: new_path = new_path.rstrip() + '$1' 

                redirectpath = ''   
                config = ''
                if get.domainorpath == 'path': 
                    redirectpath = get.redirectpath
                    redirects = '''<IfModule mod_rewrite.c>
	RewriteEngine on
	RewriteRule ^%s(.*) %s [L,R=%s]
</IfModule>''' % (redirectpath,new_path,get.redirecttype)
                    config += redirects + '\n\n'
                else:
                   
                    for x in obj['redirectdomain']:                       
                        redirects = '''<IfModule mod_rewrite.c>
	RewriteEngine on
	%s
	RewriteRule ^%s(.*) %s [L,R=%s]
</IfModule>''' % ('RewriteCond %{HTTP_HOST} ^'+ x +' [NC]',redirectpath,new_path,get.redirecttype)

                        config += redirects + '\n\n'
                
                public.writeFile(pPath + '/' + obj['redirectname'] + '.conf',config)
            else:
                if os.path.exists(pPath + '/' + obj['redirectname'] + '.conf'): os.remove(pPath + '/' + obj['redirectname'] + '.conf')
            public.serviceReload();
            return public.returnMsg(True,'修改重定向成功！')   
        else:
            pPath = self.setupPath + '/nginx/conf/redirect/' + Name
            if not os.path.exists(pPath): os.makedirs(pPath)
            config = ''
            if obj['type'] == 1:                       
                redirectpath = ''                   
                if get.domainorpath == 'path': 
                    new_path = obj['tourl']
                    if obj['holdpath'] == 1: new_path = new_path.rstrip() + '$1'
                    
                    redirecttype = 'permanent'
                    if get.redirecttype == '302': redirecttype = 'redirect'
                    redirects = 'rewrite ^%s(.*) %s %s;' % (get.redirectpath,new_path,redirecttype)  

                    config += redirects + '\n\n'      
                else:
                    new_path = obj['tourl']
                    if obj['holdpath'] == 1: new_path = new_path.rstrip() + '$request_uri'

                    for x in obj['redirectdomain']:    
                        redirects = '''if ($host ~ '^%s'){
    return %s %s;
}''' % (x,get.redirecttype,new_path)
                        config += redirects + '\n\n'
            if config:                
                public.writeFile(pPath + '/' + obj['redirectname'] + '.conf',config)
                public.serviceReload();
                return public.returnMsg(True,'修改重定向成功！')
            else:
                return public.returnMsg(False,'修改失败，无法读取配置文件！')


    #删除重定向
    def DeleteRedirect(self,get):
        siteName = get.sitename
        redirectname = get.redirectname
        if self.serverType == 'iis':
            data = self.get_config_rules(siteName)
            rules = []
            for x in data['rules']['rule']:               
                if x['@name'] != (redirectname + '_redirect'):  
                    rules.append(x)
            data['rules']['rule'] = rules
            self.set_config_rules(siteName,data)
        elif self.serverType == 'apache':
            pPath = self.setupPath + '/apache/conf/redirect/' + siteName
            if not os.path.exists(pPath): os.makedirs(pPath)
            if os.path.exists(pPath + '/' + redirectname + '.conf'): os.remove(pPath + '/' + redirectname + '.conf')
            public.serviceReload();

        else:
            pPath = self.setupPath + '/nginx/conf/redirect/' + siteName
            if not os.path.exists(pPath): os.makedirs(pPath)
            if os.path.exists(pPath + '/' + redirectname + '.conf'): os.remove(pPath + '/' + redirectname + '.conf')
            public.serviceReload();

        path = 'data/redirect/' + siteName + '.conf'
        data = []
        if os.path.exists(path):
            list = json.loads(public.readFile(path))
            for x in list:
                if x['redirectname'] != redirectname:
                    data.append(x)
        public.writeFile(path,json.dumps(data))
        
        return public.returnMsg(True,'删除重定向规则成功！')

    # 取重定向配置文件
    def GetRedirectFile(self,get):
        import files
    
        sitename = get.sitename
        redirectname = get.redirectname
        get.path = self.setupPath + '/'+self.serverType + '/conf/redirect/' + sitename+'/'+ redirectname + '.conf'
       
        f = files.files()
        return f.GetFileBody(get),get.path

    #保存重定向配置
    def SaveRedirectFile(self,get):
        import files
        f = files.files()
        ret = f.SaveFileBody(get)
        public.serviceReload();
        return ret

    #检测参数
    def check_redirect_config(self,get):
        #检测是否选择域名
        if hasattr(get, 'domainorpath') and get.domainorpath == "domain":
            if not json.loads(get.redirectdomain):
                return public.returnMsg(False, '请选择重定向域名')
        else:
            if not get.redirectpath:
                return public.returnMsg(False, '请输入重定向路径')
        rep = "^((https|http)?:\/\/)[^\s]+"
        if not re.match(rep, get.tourl):
            return public.returnMsg(False, '目标URL格式不对 %s' + get.tourl)

    #获取站点url重写规则
    def get_config_rules(self,siteName):        
        try:          
            try:
                sitePath = self.get_site_path(siteName)        
                config_path = sitePath + '/web_config/rewrite.config'

                data = self.loads_json(config_path)
                if not 'rules' in data: data['rules'] = []                    
            except :
                data = {}
                data['rules'] = []
   
            if not 'rule' in data['rules']:
                data['rules']['rule'] = []
            else:
                list = data['rules']['rule'];
                if type(list) != type([1,]):
                    data['rules']['rule'] = [list]
            return data
        except Exception as ex:       
            error = str(ex)
            sitePath = self.get_site_path(siteName)  
            if sitePath:
                error = error + ' | ' + sitePath + ' | ' + str(os.path.exists(sitePath + '/web_config'))

                config_path = sitePath + '/web_config/rewrite.config'
                if os.path.exists(config_path):
                    error = error + ' | ' + public.readFile(config_path)

              #是否重复
            siteType = public.M('sites').where("name=?",(siteName,)).getField('type')
            error = error + '|' + siteType

            public.submit_panel_bug("获取IIS伪静态失败 --> " + error)
            return False
    
    #保存URL重写规则
    def set_config_rules(self,siteName,data):
        sitePath = self.get_site_path(siteName)

        config_path = sitePath + '/web_config/rewrite.config'
        public.writeFile(config_path, self.format_xml(self.dumps_json(data)))
        public.serviceReload(siteName)
        return True

    #获取配置文件权限
    def get_config_access(self,siteName):    
        list = []
        sitePath = self.get_site_path(siteName)
        if sitePath:
            filename = public.format_path(sitePath + '/web.config')
            if os.path.exists(filename):                
                import files           
                new_get = dict_obj();
                new_get.filename = filename

                file_obj = files.files();
                data = file_obj.GetFileAccess(new_get)
            
                arrs = ['administrator','']
                if 'list' in data:                    
                    for access in data['list']:
                        if access['user'].lower().find('administrator')>=0 or access['group'] == 'IIS APPPOOL': 
                            list.append(access)
        return list

    #获取配置文件是否锁定
    def get_config_locking(self,siteName):
        if self.serverType == 'iis':  
            is_locking = True
            data = self.get_config_access(siteName)
            for item in data:
                if item['access'] != 1179817:  
                    is_locking = False
                    break
            return is_locking
        return False

    #锁定网站配置文件
    def set_config_locking(self,get):
        siteName = get.siteName
        try:
            access = 2032127
            msgobj = {'1179817':'锁定','2032127':'解锁'}
            if self.serverType == 'iis':                 
                if not self.get_config_locking(siteName): access = 1179817
        
                sitePath = self.get_site_path(siteName)
                if not sitePath: return public.returnMsg(False, '【%s】网站路径获取失败，请检查IIS是否存在此站点，如IIS不存在请通过面板删除此网站后重新创建.' % siteName); 

                filename = public.format_path(sitePath + '/web.config')           
                import files           
                new_get = dict_obj();
                new_get.filename = filename
                new_get.access = access                

                filename = public.format_path(sitePath + '/web.config')
                data = self.get_config_access(siteName)
                for item in data:
                    if item['access'] != access:  
                        new_get.user = item['user']
                        files.files().SetFileAccess(new_get)
                return public.returnMsg(True, msgobj[str(access)] + '站点【'+ siteName +'】配置文件成功！')
            
            return public.returnMsg(False, msgobj[str(access)] + '站点【'+ siteName +'】配置文件失败1！')
        except :
            return public.returnMsg(False, '操作异常,请修复面板后重试！')
    
    #获取网站配置文件路径
    def get_conf_path(self,siteName):
         path = self.setupPath
         if self.serverType == 'apache':
             path  = path + '/apache/conf/vhost/' + siteName + '.conf'
             return path
         elif self.serverType == 'nginx':
             path  = path + '/nginx/conf/vhost/' + siteName + '.conf'
             return path
         return None

     
    #判断DNS-API是否设置
    def Check_DnsApi(self,dnsapi):
        dnsapis = self.GetDnsApi(None)
        for dapi in dnsapis:
            if dapi['name'] == dnsapi:
                if not dapi['data']: return True
                for d in dapi['data']:
                    if d['key'] == '': return False
        return True
    
    #获取DNS-API列表
    def GetDnsApi(self,get):
        if not os.path.exists('config/dns_api.json'):
            public.writeFile('config/dns_api.json',public.readFile('config/dns_api_init.json'))
        apis = json.loads(public.ReadFile('config/dns_api.json'))
        return apis

    #设置DNS-API
    def SetDnsApi(self,get):
        #path = '/root/.acme.sh'
        #if not os.path.exists(path + '/account.conf'): path = "/.acme.sh"
        #filename = path + '/account.conf'
        pdata = json.loads(get.pdata)
        apis = json.loads(public.ReadFile('config/dns_api.json'))
        is_write = False
        for key in pdata.keys():
            for i in range(len(apis)):
                if not apis[i]['data']: continue
                for j in range(len(apis[i]['data'])):
                    if apis[i]['data'][j]['key'] != key: continue
                    apis[i]['data'][j]['value'] = pdata[key]
                    is_write = True
                    #kvalue = key + "='" + pdata[key] + "'"
                    #public.ExecShell("sed -i '/%s/d' %s" % (key,filename))
                    #public.ExecShell("echo \"%s\" >> %s" % (kvalue,filename))

        if is_write: public.writeFile('config/dns_api.json',json.dumps(apis))
        return public.returnMsg(True,"设置成功!")
    
    def __check_let_ssl(self,get):
        # 检查是否设置301和反向代理
        get.sitename = get.siteName
        if self.GetRedirectList(get): return public.returnMsg(False, 'SITE_SSL_ERR_301');
        if self.GetProxyList(get): return public.returnMsg(False,'已开启反向代理的站点无法申请SSL!');

        return public.returnMsg(True,"通过!")
    
    # 创建Let's Encrypt免费证书
    def CreateLet(self,get):

        domains = json.loads(get.domains)
        if not len(domains): 
            return public.returnMsg(False, '请选择域名');

        file_auth =  True
        if hasattr(get, 'dnsapi'): 
            file_auth = False
        
        if not hasattr(get, 'dnssleep'): 
            get.dnssleep = 10

        email = public.M('users').getField('email');
        if hasattr(get, 'email'):
            if get.email.find('@') >= 0: email = get.email
              
        for domain in domains:
            if public.checkIp(domain): continue;
            if domain.find('*.') >=0 and file_auth:
                return public.returnMsg(False, '泛域名不能使用【文件验证】的方式申请证书!');

        if file_auth:
            data = self.get_site_info(get.siteName)
            if not data: return public.returnMsg(False, '网站配置文件不存在!');
                
            get.site_dir = data['path'].strip()
        else:          
            dns_api_list = self.GetDnsApi(get)
            get.dns_param = None
            for dns in dns_api_list:                
                if dns['name'] == get.dnsapi:        
                    param = [];
                    if not dns['data']: continue 
                    for val in dns['data']:
                        param.append(val['value'])
                    get.dns_param  = '|'.join(param)                  
            n_list = ['dns' , 'dns_bt']
            if not get.dnsapi in n_list:
                if len(get.dns_param) < 16: return public.returnMsg(False, '请先设置【%s】的API接口参数.' % get.dnsapi);
            if get.dnsapi == 'dns_bt':
                if not os.path.exists('plugin/dns/dns_main.py'):
                    return public.returnMsg(False, '请先到软件商店安装【云解析】，并完成域名NS绑定.');
        try:
            import panelLets
        except :
            os.system(public.get_run_pip('[PIP] install sewer'))
            os.system(public.get_run_pip('[PIP] install tldextract'))
            os.system(public.get_run_pip("[PIP] install sewer[aliyun]"))
            import panelLets
       
        lets = panelLets.panelLets()
        result = lets.apple_lest_cert(get)         
        if 'code' in result: return result
            
        if result['status']:       
            get.onkey = 1;
            result = self.SetSSLConf(get)
        return result

    # 设置目录保护
    def set_dir_auth(self,get):
        if self.serverType == 'iis': return public.returnMsg(False, '目录保护仅支持Apache或nginx。');
            
        sd = site_dir_auth.SiteDirAuth()
        return sd.set_dir_auth(get)

    # 删除目录保护
    def delete_dir_auth(self,get):

        sd = site_dir_auth.SiteDirAuth()
        return sd.delete_dir_auth(get)

    # 获取目录保护列表
    def get_dir_auth(self,get):
        if self.serverType == 'iis': return public.returnMsg(False, '目录保护仅支持Apache或nginx。');

        sd = site_dir_auth.SiteDirAuth()
        return sd.get_dir_auth(get)

    # 修改目录保护密码
    def modify_dir_auth_pass(self,get):
        if self.serverType == 'iis': return public.returnMsg(False, '目录保护仅支持Apache或nginx。');

        sd = site_dir_auth.SiteDirAuth()
        return sd.modify_dir_auth_pass(get)