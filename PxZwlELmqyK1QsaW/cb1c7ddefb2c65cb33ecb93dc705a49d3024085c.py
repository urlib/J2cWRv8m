#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 安装脚本
#-----------------------------

import sys,os,shutil
panelPath = os.getenv('BT_PANEL')
os.chdir(panelPath)
sys.path.append("class/")
import public,tarfile

class panel_ftpserver:
    _name = 'FileZilla Server'
    _version = None
    _setup_path = None

    def __init__(self,name,version,setup_path): 
        self._version = version
        self._setup_path = setup_path
    
    def install_soft(self,downurl):
        if public.get_server_status(self._name) >= 0:  public.delete_server(self._name)

        temp = self._setup_path + '/temp/ftpServer.rar'
        public.downloadFile(downurl + '/win/ftpServer.rar',temp)
        if not os.path.exists(temp): return public.returnMsg(False,'文件下载失败,请检查网络!');

        from unrar import rarfile
        rar = rarfile.RarFile(temp)  
        rar.extractall(self._setup_path)

        rRet = public.create_server(self._name,self._name,self._setup_path + '\\ftpServer\\FileZilla_Server.exe','',"FileZilla是一个免费开源的FTP软件，分为客户端版本和服务器版本，具备所有的FTP软件功能")
        if public.get_server_status(self._name) == 0:
            if public.set_server_status(self._name,'start'): 
                public.bt_print('ftp启动成功.')
            else:
                return public.returnMsg(False,'启动失败，请检查配置文件是否错误!');
        public.bt_print('ftp安装成功.')
        return public.returnMsg(True,'安装成功!');
        return rRet;

    def uninstall_soft(self):
        if public.get_server_status(self._name) >= 0:  public.delete_server(self._name)

        return public.returnMsg(True,'卸载成功!');

    def update_soft(self,downurl):
        path = self._setup_path + '/ftpServer'
        sfile = path +'/FileZilla Server.xml'
        dfile = path + '/FileZilla Server.xml.backup'
        shutil.copy (sfile,dfile)
        rRet = self.install_soft(downurl)
        if not rRet['status'] : rRet;
        if public.set_server_status(self._name,'stop'):
            shutil.copy (dfile,sfile)
            os.remove(dfile);
            if public.set_server_status(self._name,'start'):
                 return public.returnMsg(True,'更新成功!');
        return public.returnMsg(False,'更新失败!');



