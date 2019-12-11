#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 安装脚本
#-----------------------------

import sys,os,shutil,re
panelPath = os.getenv('BT_PANEL')
os.chdir(panelPath)
sys.path.append("class/")
import public,tarfile,re,xmltodict,time
import xml.etree.ElementTree as ET
from xml.dom import minidom

class panel_phpmyadmin:
    _name = 'phpmyadmin'
    _version = None
    _setup_path = None

    def __init__(self,name,version,setup_path): 
        self._version = version
        self._setup_path = setup_path
        self._iis_root = os.getenv("SYSTEMDRIVE") + '\\Windows\\System32\\inetsrv'
        self._appcmd = self._iis_root + '\\appcmd.exe'
    
    def install_soft(self,downurl):

        self.del_phpmyadmin()
        path = (self._setup_path + '/phpmyadmin').replace('\\','/')
        os.makedirs(path)

        public.bt_print("正在下载%s" % self._name)
        temp = self._setup_path + '/temp/phpmyadmin.rar'
        public.downloadFile(downurl + '/win/phpmyadmin/phpmyadmin' + self._version + '.rar',temp)
        if not os.path.exists(temp): return public.returnMsg(False,'文件下载失败,请检查网络!');

        public.bt_print("正在解压%s" % self._name)
        from unrar import rarfile
        try:            
            rar = rarfile.RarFile(temp)  
            rar.extractall(path)
        except :
            time.sleep(1)
            rar = rarfile.RarFile(temp)  
            rar.extractall(path)

        srcPath = '%s/%s' % (path,self._name)
        nName = '%s_%s' % (self._name,public.GetRandomString(16))
        if os.path.exists(srcPath):
            os.rename(srcPath,'%s/%s' % (path,nName))
        
        public.writeFile(panelPath + '/data/phpmyadminDirName.pl',nName)

        public.bt_print("正在检测phpmyadmin%s所需要的PHP版本" % (self._version))
        phpVersion = None
        phps = [ 53, 54, 55, 56, 70, 71, 72, 73, 74, 75, 76];
        if self._version == '4.0':
            phps = [53, 54]
        elif self._version == '4.4':
            pass #全版本
        elif self._version == '4.6':
            phps = [55, 56, 70, 71, 72, 73]
        elif self._version == '4.7':
            phps = [70, 71, 72, 73]
        elif self._version == '4.8':
            phps = [70, 71, 72, 73]
        elif self._version == '4.9':
            phps = [70, 71, 72, 73]

        public.bt_print(phps)
        for x in phps:
            pPath = '%s/php/%s' % (os.getenv('BT_SETUP'),str(x))
            if os.path.exists(pPath):
                 phpVersion = x
                 break
        if phpVersion:
            siteData = { 'siteName' : 'phpmyadmin' ,'siteDomain': 'phpmyadmin' ,'sitePort':888,'sitePath':path ,'phpVersion':phpVersion }
            result = self.add_phpmyadmin(siteData)
            if result:
                public.writeFile(path + '/version.pl',self._version)
                public.bt_print("安装成功!")
                return public.returnMsg(True,'安装成功!');
        public.bt_print("安装异常，未找到php版本")
        return public.returnMsg(False,'安装失败!')

    def uninstall_soft(self):
        self.del_phpmyadmin()
        return public.returnMsg(True,'卸载成功!');

    def update_soft(self,downurl):
        pass

    #从IIS获取站点
    def get_iis_sites(self):
        rRet = public.ExecShell(self._appcmd + ' list sites')
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

    #初始化web.config
    def init_iisSite_config(self,confPath):
        #合并主配置文件
        default_config = {"configuration": {"system.webServer": {"rewrite": {"rules": {"@configSource": "web_config\\rewrite.config"}}, "defaultDocument": {"@configSource": "web_config\\default.config"}, "httpErrors": {"@configSource": "web_config\\httpErrors.config"}, "handlers": {"@configSource": "web_config\\php.config"}}}}
        data = public.loads_json(confPath)                
        for k1 in default_config:
            if not k1 in data: data[k1] = default_config[k1]                
            for k2 in default_config[k1]:
                if not k2 in data[k1]: data[k1][k2] = default_config[k1][k2]
                for k3 in default_config[k1][k2]:
                    data[k1][k2][k3] = default_config[k1][k2][k3]
                    for k4 in default_config[k1][k2][k3]:
                        data[k1][k2][k3][k4] = default_config[k1][k2][k3][k4]
        
        #创建单个配置文件
        webPath = confPath.replace('web.config','web_config')
        if not os.path.exists(webPath):  os.makedirs(webPath)
        list = [
                { "path":confPath ,"data":data},
                { "path":webPath + '/rewrite.config',"data": {"rules": {"clear": {}}}},
                { "path":webPath + '/default.config' ,"data": {"defaultDocument": {"files": {"clear": {}, "add": [{"@value": "index.php"}, {"@value": "index.aspx"}, {"@value": "index.asp"}, {"@value": "default.html"}, {"@value": "Default.htm"}, {"@value": "Default.asp"}, {"@value": "index.htm"}, {"@value": "index.html"}, {"@value": "iisstart.htm"}, {"@value": "default.aspx"}]}}}},
                { "path":webPath + '/httpErrors.config' ,"data":  {"httpErrors": {"@errorMode": "DetailedLocalOnly"}}},
                { "path":webPath + '/php.config' ,"data": {"handlers": {}} }        
            ]
        for x in list:
            public.writeFile(x['path'], public.format_xml(public.dumps_json(x['data'])))

        return True

    #获取所有iis所有net版本
    def get_iis_net_versions(self):
        rRet = public.ExecShell("%windir%\\Microsoft.NET\\Framework\\v2.0.50727\\aspnet_regiis.exe -lv")
        tmps = re.findall("v[1-9]\\d*.[0-9]\\d*",rRet[0])
        data = []
        for item in tmps:
            item = item.replace('v','')
            if not item in data: data.append(item)
        if len(data) == 0:
            data.append("4.0")
        return data


    def addFirewalls(self,port):
        __version = public.get_sys_version()       
       
        ps = "phpmyadmin端口"
        if public.M('firewall').where("port=?",(port,)).count() > 0: return public.returnMsg(False,'FIREWALL_PORT_EXISTS')

        shell = 'netsh firewall set portopening tcp '+ port.replace(':','-') +' '+ ps
        if int(__version[0]) == 6:            
            shell = 'netsh advfirewall firewall add rule name='+ps+' dir=in action=allow protocol=tcp localport=' + port.replace(':','-')
        result = public.ExecShell(shell);
        public.WriteLog("TYPE_FIREWALL", 'FIREWALL_ACCEPT_PORT',(port,))
        addtime = time.strftime('%Y-%m-%d %X',time.localtime())
        public.M('firewall').add('port,ps,addtime',(port,ps,addtime))

    #添加网站
    def add_phpmyadmin(self,siteObj):
        webserver = public.GetWebServer()    
        if webserver == 'iis':    
            path = siteObj['sitePath'].replace('/','\\')
            versions = self.get_iis_net_versions()
            public.ExecShell(self._appcmd + ' add apppool /name:'+ siteObj['siteName'] +' /managedRuntimeVersion:v' + versions[0] + ' /managedPipelineMode:Integrated /enable32BitAppOnWin64:true /failure.rapidFailProtection:false')          
            public.ExecShell(self._appcmd + ' add site /name:"' + siteObj['siteName'] + '" /bindings:"http/*:' + str(siteObj['sitePort']) +':" /physicalPath:"' + path + '"')  
            public.ExecShell(self._appcmd + ' set app "' + siteObj['siteName'] + '/" /applicationPool:"' + siteObj['siteName'] + '"') 

            public.set_file_access(path,siteObj['siteName'],public.file_all)
  
            self.init_iisSite_config(siteObj['sitePath'] + '/web.config')
            self.SetPHPVersion(siteObj['siteName'],siteObj['phpVersion'])  

            self.addFirewalls(str(siteObj['sitePort']));
            public.ExecShell('iisreset ')
            return True
        elif webserver == 'nginx':
            rpath = self._setup_path + '/nginx/conf/redirect/' + siteObj['siteName']
            if not os.path.exists(rpath): os.makedirs(rpath)
            
            ppath = self._setup_path + '/nginx/conf/proxy/'+siteObj['siteName']
            if not os.path.exists(ppath): os.makedirs(ppath)

            rpath = self._setup_path + '/nginx/conf/rewrite/'+siteObj['siteName']
            if not os.path.exists(rpath): os.makedirs(rpath)

            conf='''server 
    {
        listen %s;%s
        server_name %s;
        index index.php index.html index.htm default.php default.htm default.html;
        root %s;
		
	    #START-ERROR-PAGE
	    error_page 403 /403.html;
	    error_page 404 /404.html;
        error_page 502 /502.html;
	    #END-ERROR-PAGE
    
        #HTTP_TO_HTTPS_START
        #HTTP_TO_HTTPS_END

        #SSL-INFO-START
        #SSL-INFO-END

        #PHP-INFO-START 
        include php/%s.conf;
        #PHP-INFO-END
    
        #REWRITE-START
        include rewrite/%s/*.conf;
        #REWRITE-END

        #redirect 重定向
        include redirect/%s/*.conf;

        #proxy 反向代理
        include proxy/%s/*.conf;
    
        #禁止访问的文件或目录
        location ~ ^/(\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)
        {
            return 404;
        }
    
        #一键申请SSL证书验证目录相关设置
        location ~ \.well-known{
            allow all;
        }
    
        location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
        {
            expires      30d;
            error_log off;
            access_log off;
        }
    
        location ~ .*\\.(js|css)?$
        {
            expires      12h;
            error_log off;
            access_log off; 
        }

	    access_log  %s.log;
        error_log  %s.error.log;
    }
    ''' % (siteObj['sitePort'],'',siteObj['siteName'],siteObj['sitePath'],siteObj['phpVersion'],siteObj['siteName'],siteObj['siteName'],siteObj['siteName'],public.GetConfigValue('logs_path')+'/'+siteObj['siteName'],public.GetConfigValue('logs_path')+'/'+siteObj['siteName'])
        

            #写配置文件
            filename = self._setup_path + '/nginx/conf/vhost/'+siteObj['siteName']+'.conf'     
            public.writeFile(filename,conf);
            self.SetPHPVersion(siteObj['siteName'],siteObj['phpVersion'])  
            self.addFirewalls(str(siteObj['sitePort']));
            public.serviceReload()
            return True

        elif webserver == 'apache':
            port = siteObj['sitePort']
            #添加端口监听
            filename = self._setup_path + '/apache/conf/httpd.conf';
            if not os.path.exists(filename): return;
            allConf = public.readFile(filename);
            rep = "Listen\s+([0-9]+)\n";
            tmp = re.findall(rep,allConf);
            is_add = False
            for key in tmp:
                if key == str(port):
                    is_add = True
                    break
            if not is_add:                
                listen = "\nListen "+tmp[0]          
                allConf = allConf.replace(listen,listen + "\nListen " + str(port) )
                public.writeFile(filename, allConf)

            #添加网站
            import time
            listen = '';
            acc = public.md5(str(time.time()))[0:8];

            rpath = self._setup_path+'/apache/conf/redirect/' + siteObj['siteName']
            if not os.path.exists(rpath): os.makedirs(rpath)
            
            ppath = self._setup_path+'/apache/conf/proxy/'+ siteObj['siteName']
            if not os.path.exists(ppath): os.makedirs(ppath)

            #遍历网站每层目录，设置读取权限，否则Apache无法启动
            list = []
            public.get_paths(siteObj['sitePath'],list)
            for pitem in list: public.set_file_access(pitem,'www',public.file_read,False)
            public.set_file_access(siteObj['sitePath'],'www',public.file_all)
 
            conf ='''<VirtualHost *:%s>
        ServerAdmin webmaster@example.com
	    DocumentRoot "%s"
	    ServerName %s
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
    ''' % (siteObj['sitePort'],siteObj['sitePath'],siteObj['siteName'],siteObj['siteName'],public.GetConfigValue('logs_path')+'/'+siteObj['siteName'],public.GetConfigValue('logs_path')+'/'+siteObj['siteName'],siteObj['siteName'],siteObj['siteName'],siteObj['sitePath'])
    
            htaccess = siteObj['sitePath'] + '/.htaccess'
            if not os.path.exists(htaccess): public.writeFile(htaccess, ' ');

            filename = self._setup_path +'/apache/conf/vhost/'+siteObj['siteName']+'.conf'     
            public.writeFile(filename,conf)

            self.SetPHPVersion(siteObj['siteName'],siteObj['phpVersion'])  
            self.addFirewalls(str(siteObj['sitePort']));
            public.serviceReload()
            return True

    #获取网站配置文件路径
    def get_conf_path(self,siteName):
         path = self._setup_path
         if public.GetWebServer() == 'apache':
             path  = path + '/apache/conf/vhost/' + siteName + '.conf'
             return path
         else:
            path  = path + '/nginx/conf/vhost/' + siteName + '.conf'
            return path
         return None

    #删除网站
    def del_phpmyadmin(self):
        webserver = public.GetWebServer()    
        if webserver == 'iis':
            public.ExecShell(self._appcmd + ' delete site "%s"' % self._name)
            public.ExecShell(self._appcmd + ' delete apppool "%s"' % self._name)
        else: 
            confPath = self.get_conf_path(self._name)
            if os.path.exists(confPath): os.remove(confPath)

        if os.path.exists(self._setup_path + '/' + self._name): 
            shutil.rmtree(self._setup_path + '/' + self._name)

    #修改版本
    def SetPHPVersion(self,siteName,phpVersion):
        phpVersions = ['52','53','54','55','56','70','71','72','73','74','75']
        webserver = public.GetWebServer()    
        if webserver == 'iis':    
            phpPath = (os.getenv('BT_SETUP') + '/php/' + str(phpVersion) + '/php-cgi.exe').replace('/','\\')
            hlist = []
            for v in phpVersions:
                hlist.append({'@name':'php_' + v })

            php_config = {"handlers": { "remove":hlist,"add": {"@name": "php_" + str(phpVersion), "@path": "*.php", "@verb": "*", "@modules": "FastCgiModule", "@scriptProcessor": phpPath, "@resourceType": "Unspecified", "@requireAccess": "Script"} }}
            public.writeFile(self._setup_path + '/phpmyadmin/web_config/php.config', public.format_xml(public.dumps_json(php_config)))

        elif webserver == 'apache':
            phpVersion = str(phpVersion)
            pPath = self._setup_path + '/apache/conf/php'
            if not os.path.exists(pPath): os.makedirs(pPath)
            if not os.path.exists(pPath+'/' + phpVersion + '.conf'):
                phpconfig = '''<Files ~ "\.php$">
	Options FollowSymLinks ExecCGI
	AddHandler fcgid-script .php
	FcgidWrapper "%s/php-cgi.exe" .php
</Files>''' % (self._setup_path + '/php/' + phpVersion)
                if phpVersion == '00': phpconfig = ''
                public.writeFile(pPath+'/' + phpVersion + '.conf',phpconfig)

            #apache
            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            if conf:
                rep = "(Include\s+conf/php.+.conf)";
                tmp = re.search(rep,conf).group()
                conf = conf.replace(tmp,'Include conf/php/'+phpVersion+'.conf');
                public.writeFile(file,conf)
        elif webserver == 'nginx':
            phpVersion = str(phpVersion)
            pPath = self._setup_path + '/nginx/conf/php'
            if not os.path.exists(pPath): os.makedirs(pPath)
            if not os.path.exists(pPath+'/' + phpVersion + '.conf'):
                phpconfig = '''location ~ \.php$ {
	fastcgi_pass   127.0.0.1:200%s;
	fastcgi_index  index.php;
	fastcgi_param  SCRIPT_FILENAME  $document_root$fastcgi_script_name;
	include        fastcgi_params;
}''' % (phpVersion)
                if phpVersion == '00': phpconfig = ''
                public.writeFile(pPath+'/' + phpVersion + '.conf',phpconfig)

            file = self.get_conf_path(siteName)
            conf = public.readFile(file);
            if conf:
               
                rep = "(include\s+php/.+conf)\;";
                tmp = re.search(rep,conf).group()
                conf = conf.replace(tmp,'include php/' + phpVersion + '.conf;');
                public.writeFile(file,conf)

