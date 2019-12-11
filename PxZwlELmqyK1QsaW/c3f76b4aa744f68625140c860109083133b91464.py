
class panel_apache:
    _name = 'apache'
    _version = None
    _setup_path = None

    def __init__(self,name,version,setup_path):
        self._name = name
        self._version = version
        self._setup_path = setup_path
    
    def install_soft(self,downurl):       
        vc_version = '2008'
        print('正在检测vc++库..')
        if not public.check_setup_vc(vc_version):
            print('正在安装vc' + vc_version + '...')
            if not public.setup_vc(vc_version): return public.returnMsg(False,'VC' + vc_version + '安装失败!');
        
        if public.get_server_status(self._name) >= 0: public.delete_server(self._name)

        path = self._websoft 
        temp = self._websoft + '/temp/' + self._name + self._version +'.rar'

        print(sys.argv)
        print('正在下载安装包...')
       
        public.downloadFile(self._download_url + '/win/apache/'+ self._name + self._version +'.rar',temp)
        if not os.path.exists(temp): return public.returnMsg(False,'文件下载失败,请检查网络!');

        print('正在解压...')
        from unrar import rarfile
        rar = rarfile.RarFile(temp)  
        rar.extractall(path)

        print('正在配置' + self._name + '...')
        iniPath = self._websoft + '/' + self._name + '/conf/httpd.conf'
        config = public.readFile(iniPath).replace('[PATH]',self._websoft + '\\apache')
        public.writeFile(iniPath,config)

        print('正在安装' + self._name + '服务...')
        rRet = public.create_server(self._name,self._name,self._websoft.replace('/','\\') + '\\' + self._name + '\\bin\\httpd.exe','-k runservice',"Apache是世界使用排名第一的Web服务器软件。它可以运行在几乎所有广泛使用的计算机平台上，由于其跨平台和安全性被广泛使用，是最流行的Web服务器端软件之一")
        time.sleep(1);
        if public.get_server_status(self._name) >= 0:
            if public.set_server_status(self._name,'start'):
                print('安装成功.')
                return public.returnMsg(True,self._name + '安装成功')
            else:
                return public.returnMsg(False,'启动失败，请检查配置文件是否错误!')
        return rRet;        

    def uninstall_soft(self):
        if public.exists_server(self._name): public.delete_server(self._name)        
        if public.exists_server(self._name): return public.returnMsg(False,'卸载失败,请检查是否被占用!');
        return public.returnMsg(True,'卸载成功!');

    def update_soft(self):

        sfile = self._websoft + '\\' + self._name + '\\conf\\httpd.conf'
        dfile =  self._websoft + '\\' + self._name + '\\conf\\httpd.conf.backup'
        shutil.copy (sfile,dfile)
        rRet = self.install_soft()
        if not rRet['status'] : rRet;
        
        shutil.copy (dfile,sfile)
        os.remove(dfile);
        return public.returnMsg(True,'更新成功!');

