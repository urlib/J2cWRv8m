#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 安装脚本
#-----------------------------
import public,os,time,re
class panel_iis:
    _name = None
    _version = None
    _setup_path = None
    _iis_root = None
    _app_cmd = None
    _local_path = None

    def __init__(self,name,version,setup_path):
        self._name = name
        self._version = version
        self._setup_path = setup_path
        self._iis_root = os.getenv("SYSTEMDRIVE") + '\\Windows\\System32\\inetsrv'
        self._app_cmd = self._iis_root + '\\appcmd.exe'
        self._local_path = self._setup_path + '/temp'

    def install_soft(self,downurl):
        print('正在安装IIS,需要5-10分钟...')
        rRet = public.ExecShell("start /w pkgmgr /iu:IIS-WebServerRole;IIS-WebServer;IIS-CommonHttpFeatures;IIS-StaticContent;IIS-DefaultDocument;IIS-DirectoryBrowsing;IIS-HttpErrors;IIS-HttpRedirect;IIS-ApplicationDevelopment;IIS-ASP;IIS-CGI;IIS-ISAPIExtensions;IIS-ISAPIFilter;IIS-ServerSideIncludes;IIS-HealthAndDiagnostics;IIS-HttpLogging;IIS-LoggingLibraries;IIS-RequestMonitor;IIS-HttpTracing;IIS-CustomLogging;IIS-ODBCLogging;IIS-Security;IIS-BasicAuthentication;IIS-WindowsAuthentication;IIS-DigestAuthentication;IIS-ClientCertificateMappingAuthentication;IIS-IISCertificateMappingAuthentication;IIS-URLAuthorization;IIS-RequestFiltering;IIS-IPSecurity;IIS-Performance;IIS-HttpCompressionStatic;IIS-HttpCompressionDynamic;IIS-WebServerManagementTools;IIS-ManagementScriptingTools;IIS-ASPNET;IIS-NetFxExtensibility;IIS-ManagementService;IIS-ManagementConsole;IIS-IIS6ManagementCompatibility; /norestart")

        status = public.get_server_status('W3SVC')
        if status == -1: public.returnMsg(False,'IIS安装失败...')
        
        print('正在设置iis日志目录...')
        logPath = (self._setup_path + '/wwwlogs').replace('/','\\')
        if not os.path.exists(logPath):
            os.makedirs(logPath)
        public.ExecShell(self._app_cmd + ' set config -section:system.applicationHost/sites /siteDefaults.logFile.directory:"' + logPath + '" /commit:apphost')

        print('正在启用asp...')
        public.ExecShell(self._app_cmd + ' set config /section:asp /enableParentPaths:True')
        public.ExecShell(self._app_cmd + ' set config /section:anonymousAuthentication /userName:\"\"')
        
        print('正在优化iis默认页...')
        default_list = ['default.html','default.asp','default.aspx','index.php','index.asp','index.aspx']
        for key in default_list:  public.ExecShell(self._app_cmd + " set config /section:defaultDocument /+files.[value='" + key + "']")
     
        try:
            iis_reg = 'SOFTWARE\Microsoft\InetStp'
            iisVersion = public.ReadReg(iis_reg,'MajorVersion')
            if iisVersion > 9:  public.WriteReg(iis_reg,'MajorVersion',9)
        except :
            pass

        if not public.isAppSetup("IIS URL"):            
            print('正在下载URLRewrite文件...')
            public.downloadFile(downurl + '/win/URLRewrite_x64.msi',self._local_path + '/URLRewrite.msi')
            if not os.path.exists(self._local_path + '/URLRewrite.msi'): public.returnMsg(False,'URL重写扩展下载失败,请检查网络是否正常..')
        
            print("正在启动iis...")
            public.ExecShell("iisreset /START")
            time.sleep(1)

            print("正在安装URLRewrite...")
            public.ExecShell(self._local_path + '/URLRewrite.msi /qb')
            time.sleep(1)

        pPath = self._setup_path + '/php'
        if os.path.exists(pPath):
            print("正在设置PHP扩展...")
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
                    print("正在安装PHP-" + filename + "扩展...")
                    public.ExecShell(self._app_cmd + " set config /section:system.webServer/fastCGI /+[fullPath='" + cgiPath + "']")
                    public.ExecShell(self._app_cmd + " set config /section:system.webServer/handlers /+[name='PHP_FastCGI',path='*.php',verb='*',modules='FastCgiModule',scriptProcessor='" + cgiPath + "',resourceType='Unspecified']")

                    public.ExecShell(self._app_cmd + " set config -section:system.webServer/defaultDocument /+\"files.[value='index.php']\" /commit:apphost")
                    public.ExecShell(self._app_cmd + " set config -section:system.webServer/fastCGI /[fullPath='" + cgiPath + "'].instanceMaxRequests:10000")
                    public.ExecShell(self._app_cmd + " set config -section:system.webServer/fastCgi /[fullPath='" + cgiPath + "',arguments=''].activityTimeout:\"90\"  /commit:apphost")
                    public.ExecShell(self._app_cmd + " set config -section:system.webServer/fastCgi /[fullPath=''" + cgiPath + "',arguments=''].requestTimeout:\"90\"  /commit:apphost")
                    public.ExecShell(self._app_cmd + " set config -section:system.webServer/fastCgi /[fullPath='" + cgiPath + "'].monitorChangesTo:\"" + iniPath   + "\"")
                    public.ExecShell(self._app_cmd + " set config -section:system.webServer/fastCgi /+\"[fullPath='" + cgiPath + "'].environmentVariables.[name='PHP_FCGI_MAX_REQUESTS',value='10000']\"")                    
    
        host_path = "C:\Windows\System32\drivers\etc\hosts"
        if os.path.exists(host_path):
            hosttxt = public.readFile(host_path)
            tmp = re.search('\n\s*127.0.0.1\s+localhost',hosttxt)
            if not tmp:
                public.writeFile(host_path,hosttxt +  '\n127.0.0.1 localhost')
        
        public.ExecShell(self._app_cmd + " unlock config -section:system.webServer/handlers")
        public.ExecShell("regsvr32 /u /s %windir%\system32\wshom.ocx")
        public.ExecShell("regsvr32 /u /s %windir%\system32\shell32.dll")

        if not public.change_server_start_type('W3SVC',1): public.returnMsg(False,'修改服务启动类型失败...')
        print("iis安装完成")
        public.returnMsg(True,'iis安装完成')

    def uninstall_soft(self):
        print("正在卸载iis...")
        if public.set_server_status("W3SVC","stop"):            
            if not public.change_server_start_type('W3SVC',1): 
                print("卸载成功.!")
                public.returnMsg(True,'iis卸载成功.')
        print("卸载失败.")
        public.returnMsg(False,'iis卸载失败.')
         
    def update_soft(self):
        pass
