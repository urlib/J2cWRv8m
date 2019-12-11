#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 安装脚本
#-----------------------------

import sys,os,shutil,re
panelPath = os.getenv('BT_PANEL')
os.chdir(panelPath)
sys.path.append("class/")
import public,tarfile,time

class panel_mysql:
    _name = 'MySQL'
    _version = None
    _setup_path = None

    def __init__(self,name,version,setup_path):
        self._name = name
        self._version = version
        self._setup_path = setup_path

    def install_soft(self,downurl):

        if public.get_server_status(self._name) >= 0:  public.delete_server(self._name)
        public.ExecShell("taskkill /f /t /im mysqld.exe");

        try:
            if self._version == '5.5':
                public.bt_print('检测vc版本库2008..')
                if not public.check_setup_vc('52','x64'):                    
                    if not public.setup_vc('2008','x64'):  return public.returnMsg(False,'VC++2008安装失败!'); 
        except :
             return public.returnMsg(False,'安装失败,mysql密码错误!');

        public.bt_print('正在设置目录权限!')      
        path = self._setup_path + '/mysql'
        if not os.path.exists(path):  os.makedirs(path)

        #只读权限
        files = []
        public.get_paths(path,files)        
        #批量设置上层目录只读权限 
        for f in files: public.set_file_access(f,'mysql',public.file_read,False)

        public.set_file_access(path,'mysql',2032127,True)

        temp = self._setup_path + '/temp/MySQL.zip'
        __name = 'MySQL' + self._version
        if self._version.find('mariadb') >= 0:
            __name = 'MariaDB-' + re.search('\d+\.\d+',self._version).group()
     
        try:
            public.downloadFile(downurl + '/win/mysql/'+ __name +'_x64.zip',temp)
        except :
            public.downloadFile(downurl + '/win/mysql/'+ __name +'_x64.zip',temp)
        
        if not os.path.exists(temp): return public.returnMsg(False,'文件下载失败,请检查网络!');

        public.bt_print('正在解压文件.')  

        import zipfile
        zip_file = zipfile.ZipFile(temp)  
        for names in zip_file.namelist():  
            zip_file.extract(names,path)   

        public.bt_print('正在配置MySQL配置文件.')
        sPath =  path + '/' + __name
        iniPath = sPath + '/my.ini'
        config = public.readFile(iniPath).replace('[PATH]',self._setup_path + '/mysql/' + __name)
        public.writeFile(iniPath,config)
        if os.path.exists(sPath + '/version.pl'): os.remove(sPath + '/version.pl')       

        password = None
        if os.path.exists('data/mysql'):
            password = public.readFile('data/mysql')

            public.bt_print('正在创建MySQL服务.')
            #rRet = public.create_server(self._name,self._name, public.to_path(path + '/' + __name + '/bin/mysqld.exe'),'--defaults-file='+ public.to_path(iniPath) +' MySQL',"MySQL数据库服务","mysql",password)
            rRet = public.create_server(self._name,self._name, public.to_path(path + '/' + __name + '/bin/mysqld.exe'),'--defaults-file='+ public.to_path(iniPath) +' MySQL',"MySQL数据库服务")
            if public.get_server_status(self._name) >= 0:                

                public.bt_print('正在生成随机root密码.')
                old_pwd = public.M('config').where("id=?",(1,)).getField('mysql_root')
                if old_pwd.strip() == 'admin': 
                    rootPwd = public.GetRandomString(16)               
                else:
                    rootPwd = old_pwd
                ret = public.ExecShell('%s && cd %s && "C:/Program Files/python/python.exe" tools.py root %s' % (panelPath[0:2],panelPath,rootPwd))              
                public.set_server_status('mysql','start')
                public.bt_print('正在同步数据库资料')
                self.sync_database()
                public.bt_print('安装成功!')
                return public.returnMsg(True,'安装成功!');
            return rRet;
        public.bt_print('安装失败,mysql密码错误!')
        return public.returnMsg(False,'安装失败,mysql密码错误!');

    def uninstall_soft(self):
        if public.get_server_status(self._name) >= 0:  public.delete_server(self._name)
        return public.returnMsg(True,'卸载成功!');

    def sync_database(self):
        import panelMysql;
        data = public.M('databases').field('id,name,username,password,accept').select()
        for find in data:  
            try:
                public.bt_print('正在同步' + find['name'] + '.')
                if len(find['password']) < 3 :
                    find['username'] = find['name']
                    find['password'] = public.md5(str(time.time()) + find['name'])[0:10]
                    public.M('databases').where("id=?",(find['id'],)).save('password,username',(find['password'],find['username']))

                result = panelMysql.panelMysql().execute("create database " + find['name'])
                if "using password:" in str(result): return -1
                if "Connection refused" in str(result): return -1
                panelMysql.panelMysql().execute("drop user '" + find['username'] + "'@'localhost'")
                panelMysql.panelMysql().execute("drop user '" + find['username'] + "'@'" + find['accept'] + "'")
                password = find['password']
                if find['password']!="" and len(find['password']) > 20:
                    password = find['password']
        
                panelMysql.panelMysql().execute("grant all privileges on " + find['name'] + ".* to '" + find['username'] + "'@'localhost' identified by '" + password + "'")
                panelMysql.panelMysql().execute("grant all privileges on " + find['name'] + ".* to '" + find['username'] + "'@'" + find['accept'] + "' identified by '" + password + "'")
                panelMysql.panelMysql().execute("flush privileges")          
            except :
                pass
                #public.bt_print(find['name'] + ' 同步失败.')


    def update_soft(self,downurl):
        path = self._setup_path + '\\mysql'
        __name = 'MySQL' + sys.argv[3]       
        if sys.argv[1] == 'MariaDB': __name = 'MariaDB-'+ sys.argv[3]

        sfile = '%s/%s/my.ini' % (path,__name)
        dfile = '%s/%s/my.ini.backup' % (path,__name)
        shutil.copy (sfile,dfile)

        rRet = self.install_soft(downurl)
        if not rRet['status'] : rRet;
        if public.set_server_status(self._name,'stop'):
            shutil.copy (dfile,sfile)
            os.remove(dfile);
            time.sleep(3)
            if public.set_server_status(self._name,'start'):
                
                
                return public.returnMsg(True,'更新成功!');
        return public.returnMsg(False,'更新失败!');
