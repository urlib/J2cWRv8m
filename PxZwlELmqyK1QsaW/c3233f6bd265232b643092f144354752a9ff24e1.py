#coding: utf-8
#-----------------------------
# 安装脚本
#-----------------------------
import sys,os,shutil
panelPath = os.getenv('BT_PANEL')
os.chdir(panelPath)
sys.path.append("class/")
import public,tarfile,time,re

class panel_nginx:
    _name = 'nginx'
    _version = None
    _setup_path = None

    def __init__(self,name,version,setup_path):
        self._name = name
        self._version = version
        self._setup_path = setup_path
    
    def install_soft(self,downurl):       
        status = public.get_server_status('W3SVC')
        if status >=0:
            public.bt_print('准备卸载IIS..')
            os.system("iisreset /stop")          
            public.change_server_start_type('W3SVC',-1)

        if public.get_server_status(self._name) >= 0: 
            public.delete_server(self._name)

        path = self._setup_path 
        temp = self._setup_path + '/temp/' + self._name + self._version +'.rar'

        #配置PHP上传路径
        public.bt_print('正在更改PHP上传路径...')
        self.set_php_upload_path()

        public.bt_print('正在下载安装包...')       
        public.downloadFile(downurl + '/win/nginx_new/'+ self._name + '.rar',temp)
        if not os.path.exists(temp): return public.returnMsg(False,'文件下载失败,请检查网络!');

        public.bt_print('正在解压...')
        from unrar import rarfile
        try:            
            rar = rarfile.RarFile(temp)  
            rar.extractall(path)
        except :
            time.sleep(1)
            rar = rarfile.RarFile(temp)  
            rar.extractall(path)

        #设置启动权限
        public.bt_print('正在配置目录权限...')
        self.set_webserver_access()

        public.bt_print('正在配置' + self._name + '...')
        phps = self.get_php_versions()
        public.bt_print(phps)
        phps_str =  ','.join(phps)
        
        import psutil
        cpuCount = psutil.cpu_count() / 2
        if cpuCount < 2: cpuCount = 2
        if cpuCount > 6: cpuCount = 6
        cpuCount = int(cpuCount)

        iniPath = self._setup_path + '/' + self._name + '/config.ini'
        conf = public.readFile(iniPath)
        conf = re.sub('path\s?=.+','path = ' + public.format_path(self._setup_path),conf);
        conf = re.sub('php_versions\s?=.+','php_versions = ' + phps_str,conf);
        conf = re.sub('php_cgi_thread\s?=.+','php_cgi_thread = ' + str(cpuCount),conf);
        public.writeFile(iniPath,conf)

        public.bt_print('正在安装' + self._name + '服务...')
        password = public.readFile('data/www')
        if os.path.exists(self._setup_path + '/' + self._name + '/version.pl'): os.remove(self._setup_path + '/' + self._name + '/version.pl')       

        #zend需要授权c:/Windows目录，无法www用户无法授权
        rRet = public.create_server(self._name,self._name,self._setup_path + '/' + self._name + '/nginx_server.exe','',"nginx是一款轻量级的Web 服务器/反向代理服务器及电子邮件（IMAP/POP3）代理服务器，并在一个BSD-like 协议下发行")
        time.sleep(1);
        if public.get_server_status(self._name) >= 0:
            public.M('config').where("id=?",('1',)).setField('webserver','nginx')
            if public.set_server_status(self._name,'start'):
                public.bt_print('安装成功.')
                return public.returnMsg(True,self._name + '安装成功')
            else:
                return public.returnMsg(False,'启动失败，请检查配置文件是否错误!')        
        return rRet;        

    def uninstall_soft(self):
        try:
            if os.path.exists(self._setup_path + '/phpmyadmin'):  shutil.rmtree(self._setup_path + '/phpmyadmin')
        except :
            pass
        if public.get_server_status(self._name) >= 0: 
            public.delete_server(self._name)   
            time.sleep(2)
            shutil.rmtree(self._setup_path  + '/' + self._name)

        return public.returnMsg(True,'卸载成功!');

    #更新软件
    def update_soft(self,downurl):
        files = ['config.ini','config/nginx.conf']
        for filename in files:
            filepath =  self._setup_path + '/' + self._name + '/' + filename
            if os.path.exists(filepath): shutil.copy(filepath,filepath + '.backup');
        rRet = self.install_soft(downurl)
        if not rRet['status'] : rRet;
        
        for filename in files:
             filepath =  self._setup_path + '/' + self._name + '/' + filename + '.backup'
             if os.path.exists(filepath): 
                 shutil.copy(filepath,filepath.replace('.backup',''));
                 os.remove(filepath)
        
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

    #由于C:/Windows无法增加www权限，故修改上传目录到C:/Temp
    def set_php_upload_path(self):        
        phps = self.get_php_versions()
        for version in phps:
            iniPath = self._setup_path + '/php' + '/' + version + '/php.ini'
         
            if os.path.exists(iniPath):
                conf = public.readFile(iniPath)                
                conf = re.sub(';?upload_tmp_dir.+','upload_tmp_dir="C:/Temp"',conf);
                public.writeFile(iniPath,conf)
        return True


    #恢复网站权限（仅适配nginx下www权限）
    def set_webserver_access(self):
        if not os.path.exists('C:/Temp'): os.makedirs('C:/Temp')        
        public.set_file_access("C:/Temp","IIS_IUSRS",public.file_all,False)
        user = 'www'
        data = public.M('config').where("id=?",('1',)).field('sites_path').find();

        if data['sites_path'].find('/www/') >=0 :
            wwwroot = os.getenv("BT_SETUP")[:2] + '/wwwroot'
            if not os.path.exists(wwwroot): os.makedirs(wwwroot)

            backup_path = os.getenv("BT_SETUP")[:2] + '/backup'
            if not os.path.exists(backup_path): os.makedirs(backup_path)
            
            public.M('config').where('id=?',(1,)).setField('backup_path',backup_path)
            public.M('config').where('id=?',(1,)).setField('sites_path',wwwroot)

            data = public.M('config').where("id=?",('1',)).field('sites_path').find();

        #完全控制权限
        paths = ["C:/Temp", public.GetConfigValue('logs_path'), public.GetConfigValue('setup_path') + '/nginx' ,data['sites_path'] ]        

        #只读权限
        flist = []
        for x in paths: public.get_paths(x,flist)        
        #批量设置上层目录只读权限 
        for f in flist:
            print("正在设置 %s 权限" % f)
            public.set_file_access(f,user,public.file_read,False)

        for f in paths: 
            print("正在设置 %s 权限" % f)
            public.set_file_access(f,user,public.file_all,False)

        public.set_file_access(os.getenv("BT_SETUP") + '/nginx',user,public.file_all)

        return public.returnMsg(True,'权限恢复成功，当前仅恢复Nginx启动所需权限，网站权限需要手动恢复!')
