import sys,os,re
import public
class panel_phplib:
    _name = None
    _version = None
    _setup_path = None
    _filename = None
    _extpath = None

    def __init__(self,name,version,setup_path):
        if len(sys.argv) > 4:
            self._name = sys.argv[4].lower()       
            self._version = version
            self._setup_path = setup_path
            self._filename = 'php_' + self._name + '.dll'
            #处理特殊扩展名称
            other_ext =  { "sg11":"ixed."+ version +".win", "zendguardloader":"ZendLoader.dll"}
            if self._name in other_ext.keys(): self._filename = other_ext[self._name]
            self._extpath = 'extension=' + self._filename

            if self._name == 'zendoptimizer': #php 5.2 zend
                self._filename = 'ZendExtensionManager.dll'
                self._extpath = 'zend_extension_ts="' + (self._setup_path + '/php/' + self._version).replace('/','\\') + '\ZendOptimizer\ZendExtensionManager.dll"'
             
            #处理zend扩展路径
            zend_list = ['opcache','ioncube','xdebug','zendguardloader']        
            if self._name in zend_list:
                if version == '53' or version == '54':
                   self._extpath = 'zend_extension=./ext/' + self._filename
                else:
                   self._extpath = 'zend_extension=' + self._filename
        else:
            exit('非法请求')

    def install_soft(self,downurl):       
        self._version = self._version.replace('.','')

        localpath = self._setup_path + '/php/' + self._version + '/ext/' + self._filename
        if not os.path.exists(localpath):
            server_url = downurl + '/win/php/' + self._version + '/' + self._filename
            public.downloadFile(server_url,localpath)
            if not os.path.exists(localpath): return public.returnMsg(False,'文件下载失败,请检查网络!');

        iniPath = self._setup_path + '/php/' + self._version + '/php.ini'
        conf = public.readFile(iniPath)

        path_ext = [ "pathinfo","path_info" ]
        #处理path_info
        if self._name in path_ext: 
            reg = ';*(\w+.*fix_pathinfo=).*'
            temp = re.search(reg,conf)
            if temp:  conf = conf.replace(temp.group(),'cgi.fix_pathinfo=1')
        else:
            reg = ';*\w+.*' + self._filename + '.*'
            temp = re.search(reg,conf)
            if temp:
                conf = conf.replace(temp.group(),self._extpath)
            else:
                conf = conf + '\n' + self._extpath
        public.writeFile(iniPath,conf)
        print('安装' + self._name + '成功.')
        return True;

    def uninstall_soft(self,downurl):
        self._version = sys.argv[3].replace('.','');        
        iniPath = self._setup_path + '/php/' + self._version + '/php.ini'
        conf = public.readFile(iniPath)

        path_ext = [ "pathinfo","path_info" ]
        #处理path_info
        if self._name in path_ext: 
            reg = ';*(\w+.*fix_pathinfo=).*'
            temp = re.search(reg,conf)
            if temp:  conf = conf.replace(temp.group(),'cgi.fix_pathinfo=1')
        else:
            reg = ';*\w+.*' + self._filename + '.*'
            temp = re.search(reg,conf)
            if temp: conf = conf.replace(temp.group(),';' + self._extpath)

        public.writeFile(iniPath,conf)
        print('安装成功.')

    def update_soft(self):
        pass
