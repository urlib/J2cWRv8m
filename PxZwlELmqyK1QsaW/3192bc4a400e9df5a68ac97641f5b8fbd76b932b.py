import sys,os,shutil,re
panelPath = os.getenv('BT_PANEL')
os.chdir(panelPath);
sys.path.append("class/")
import public,tarfile,time

class panel_php:
    _name = 'php'
    _version = None
    _setup_path = None

    def __init__(self,name,version,setup_path):
        self._name = name
        self._version = version
        self._setup_path = setup_path
        self._iis_root = os.getenv("SYSTEMDRIVE") + '\\Windows\\System32\\inetsrv'
        self._app_cmd = self._iis_root + '\\appcmd.exe'

    def install_soft(self,downurl):     
    
        self._version = self._version.replace('.','')
        
        bit = 'x86'
        if int(self._version) >= 55: bit = 'x64'

        try:
            public.bt_print('准备安装php-' + self._version +'..')
            if not public.check_setup_vc(self._version,bit):
                vc_version = public.get_vc_version(self._version)
                if not public.setup_vc(vc_version,bit):  return public.returnMsg(False,'VC' + vc_version + '安装失败!'); 
        except :
            public.bt_print('请修复面板后重试..')

        #5.2 zend初始化
        if int(self._version) == 52:
            zend_memory_path = 'C:/Windows/ZendOptimizer.MemoryBase@www@3391924446'
            public.writeFile(zend_memory_path,"20000000")
            public.set_file_access(zend_memory_path,"www",public.file_modify,False)
        
        if int(self._version) > 56 and int(self._version) < 72:                 
            x_64path = 'C:/Windows/SysWOW64'  
            if not os.path.exists(x_64path + '/api-ms-win-crt-runtime-l1-1-0.dll') and not os.path.exists(x_64path + '/downlevel/api-ms-win-crt-runtime-l1-1-0.dll'):
                public.bt_print('vc2015安装失败,尝试修补系统..')
                temp = self._setup_path + '/temp/vc2015.zip'
                public.downloadFile(downurl + '/win/panel/data/vc2015_x64.zip',temp)

                tmpPath = self._setup_path + "/temp/vc2015"
                #解压到临时目录
                import zipfile
                zip_file = zipfile.ZipFile(temp)  
                for names in zip_file.namelist():  
                    zip_file.extract(names,tmpPath)      

                tmpPath = tmpPath.replace("/","\\")              
                os.system("xcopy /s /c /e /y /r %s %s" % (tmpPath,x_64path.replace("/","\\")))
        
        path = self._setup_path + '\\php'
        temp = self._setup_path + '/temp/' + self._version + '.rar'

        if int(self._version) >= 55:
            #下载64位安装包
            public.downloadFile(downurl + '/win/php/x64/'+ self._version +'.rar',temp)
            public.downloadFile(downurl + '/win/panel/data/phplib.win',"data/phplib.win")
        else:
            public.downloadFile(downurl + '/win/php/'+ self._version +'.rar',temp)

        if not os.path.exists(temp): return public.returnMsg(False,'文件下载失败,请检查网络!');

        public.bt_print('正在设置上传目录权限...')
        if not os.path.exists('C:/Temp'): 
            os.makedirs('C:/Temp')

        public.set_file_access("C:/Windows/Temp","IIS_IUSRS",public.file_all,False)
        public.set_file_access("C:/Temp","IIS_IUSRS",public.file_all,False)     
        public.set_file_access("C:/Temp","www",public.file_all,False)  
        public.set_file_access("C:/","www",public.file_all,False)
        try:
            from unrar import rarfile       
            try:            
                rar = rarfile.RarFile(temp)  
                rar.extractall(path)
            except :
                time.sleep(1)
                rar = rarfile.RarFile(temp)  
                rar.extractall(path)
        except :
            public.bt_print('php文件被占用，更新前请先确保没有网站程序调用此版本的php程序.')
            return False;


        iniPath = path + '\\' + self._version + '\\php.ini'
        config = public.readFile(iniPath).replace('[PATH]',self._setup_path.replace('/','\\'))        
        config = re.sub(';?upload_tmp_dir.+\n','upload_tmp_dir="C:/Temp"\n',config);

        public.writeFile(iniPath,config)

        self.update_php_ext()

        public.bt_print('安装成功.')
        return True;

    def uninstall_soft(self):
        self._version = sys.argv[3].replace('.','');
        if not self._version: return public.returnMsg(False,'卸载失败，版本号传递错误!');
        try:           
            dfile = self._setup_path + '\\php\\' + self._version
            webserver = public.GetWebServer()    
            if webserver == 'iis': 
                public.set_server_status("W3SVC","stop")   
                shutil.rmtree(dfile);
                public.set_server_status("W3SVC","start")   
                self.update_php_ext()
            elif webserver == 'apache':
                public.set_server_status("apache","stop")  
                shutil.rmtree(dfile);
                public.set_server_status("apache","start")  
            else:
                public.set_server_status("nginx","stop")  
                shutil.rmtree(dfile);
                self.update_php_ext()
                public.set_server_status("nginx","start") 
            

            if os.path.exists(dfile): 
                return public.returnMsg(False,'卸载失败,请检查是否被占用!'); 
        except :
            return public.returnMsg(False,'卸载失败,请检查程序是否被占用!');             
        return public.returnMsg(True,'卸载成功!');

    def update_soft(self,downurl):
        path = self._setup_path + '\\php'
        self._version = self._version.replace('.','');

        sfile =  path + '\\' + self._version + '\\php.ini'
        dfile =  path + '\\' + self._version + '\\php.ini.backup'
        shutil.copy(sfile,dfile)
        rRet = self.install_soft(downurl)
        if not rRet:  return public.returnMsg(False,'更新失败!');
        
        os.remove(sfile);
        shutil.copy(dfile,sfile)
        os.remove(dfile);
        if os.path.exists(path + '/' + self._version +"/version.pl"): 
            os.remove(path + '/' + self._version +"/version.pl")

        return public.returnMsg(True,'更新成功!');
    
    #获取所有php版本
    def get_php_versions(self):
        phpPath = self._setup_path + '/php'
        phps = []
        if os.path.exists(phpPath):                       
            for filename in  os.listdir(phpPath):               
                if os.path.isdir(phpPath + '/' + filename):
                    try:       
                        version = int(filename)
                        phps.append(filename)
                    except :
                        pass
        return phps;

    def update_php_ext(self):
        webserver = public.GetWebServer()    
        if webserver == 'iis': 
            pPath = self._setup_path + '/php'
            if os.path.exists(pPath):
                public.bt_print("正在更新IIS下PHP扩展...")
                try:
                    for x in [0,1,2,3,4,5,6,7,8,9]:
                        public.ExecShell(self._app_cmd + " set config /section:system.webServer/fastCGI /-[InstanceMaxRequests='10000']")
                        public.ExecShell(self._app_cmd + " set config /section:system.webServer/handlers /-[path='*.php']")
                except :
                    pass           
                for filename in os.listdir(pPath):
                    cgiPath = (pPath + '/'+ filename + "/php-cgi.exe").replace('/','\\')
                    iniPath = (pPath + '/'+ filename + "/php.ini").replace('/','\\')
                    if os.path.exists(cgiPath):
   
                        public.ExecShell(self._app_cmd + " set config /section:system.webServer/fastCGI /+[fullPath='" + cgiPath + "']")
                        public.ExecShell(self._app_cmd + " set config /section:system.webServer/handlers /+[name='PHP_FastCGI',path='*.php',verb='*',modules='FastCgiModule',scriptProcessor='" + cgiPath + "',resourceType='Unspecified']")

                        public.ExecShell(self._app_cmd + " set config -section:system.webServer/defaultDocument /+\"files.[value='index.php']\" /commit:apphost")
                        public.ExecShell(self._app_cmd + " set config -section:system.webServer/fastCGI /[fullPath='" + cgiPath + "'].instanceMaxRequests:10000")
                        public.ExecShell(self._app_cmd + " set config -section:system.webServer/fastCgi /[fullPath='" + cgiPath + "',arguments=''].activityTimeout:\"300\"  /commit:apphost")
                        public.ExecShell(self._app_cmd + " set config -section:system.webServer/fastCgi /[fullPath=''" + cgiPath + "',arguments=''].requestTimeout:\"300\"  /commit:apphost")
                        public.ExecShell(self._app_cmd + " set config -section:system.webServer/fastCgi /[fullPath='" + cgiPath + "'].monitorChangesTo:\"" + iniPath   + "\"")
                        public.ExecShell(self._app_cmd + " set config -section:system.webServer/fastCgi /[fullPath='" + cgiPath + "'].rapidFailsPerMinute:\"100\"")
                        public.ExecShell(self._app_cmd + " set config -section:system.webServer/fastCgi /+\"[fullPath='" + cgiPath + "'].environmentVariables.[name='PHP_FCGI_MAX_REQUESTS',value='10000']\"")
        elif webserver == 'nginx':     
            phps = self.get_php_versions()            
            phps_str =  ','.join(phps)
            print(phps_str)

            iniPath = self._setup_path + '/nginx/config.ini'
            conf = public.readFile(iniPath)
            conf = re.sub('php_versions\s?=.+','php_versions = ' + phps_str,conf);
            public.writeFile(iniPath,conf)
            public.serviceReload();

