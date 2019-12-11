#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

#------------------------------
# 数据库管理类
#------------------------------
import public,db,re,time,os,sys,panelMysql,panelMssql
from BTPanel import session
import datatool
class database(datatool.datatools):
    _setup_path = None
    _version = None
    def __init__(self):
        ndb = public.M('databases').order("id desc").field('id,pid,name,username,password,accept,ps,addtime,type').select()
        if type(ndb) == str:
            public.M('databases').execute("alter TABLE databases add type TEXT DEFAULT MySQL",());

        if public.get_server_status("mysql") >=0 :       
            self._version = re.search('([MySQL|MariaDB-]+\d+\.\d+)',public.get_server_path('mysql')).groups()[0] 
            self._setup_path  = public.GetConfigValue('setup_path') + '/mysql/' + self._version

    def get_mysql_conf(self):
        if public.get_server_status("mysql") >=0 :       
            data = {}
            data['version'] = re.search('([MySQL|MariaDB-]+\d+\.\d+)',public.get_server_path('mysql')).groups()[0] 
            data['path']  = public.GetConfigValue('setup_path') + '/mysql/' + self._version
            return data
        return False

    #检测是否6.x安装的服务
    def check_server(self):
         if public.get_server_status("mysql") < 0 or not os.path.exists(self._setup_path + '/my.ini')  :       
             return False
         return True

    #添加数据库
    def AddDatabase(self,get):
        #try:
        
        data_name = get['name'].strip()
        if self.CheckRecycleBin(data_name): return public.returnMsg(False,'数据库['+data_name+']已在回收站，请从回收站恢复!');
        if len(data_name) > 16: return public.returnMsg(False, 'DATABASE_NAME_LEN')
        reg = "^\w+$"
        if not re.match(reg, data_name): return public.returnMsg(False,'DATABASE_NAME_ERR_T')
        if not hasattr(get,'db_user'): get.db_user = data_name;
        username = get.db_user.strip();
        checks = ['root','mysql','test','sys','panel_logs']
        if username in checks or len(username) < 1: return public.returnMsg(False,'数据库用户名不合法!');
        if data_name in checks or len(data_name) < 1: return public.returnMsg(False,'数据库名称不合法!');
        data_pwd = get['password']
        if len(data_pwd)<1:
            data_pwd = public.md5(str(time.time()))[0:8]
            
        if public.M('databases').where("name=? or username=?",(data_name,username)).count(): return public.returnMsg(False,'DATABASE_NAME_EXISTS')
        address = get['address'].strip()
        user = '是'
        password = data_pwd
            
        codeing = get['codeing']            
        wheres={
                'utf8'      :   'utf8_general_ci',
                'utf8mb4'   :   'utf8mb4_general_ci',
                'gbk'       :   'gbk_chinese_ci',
                'big5'      :   'big5_chinese_ci'
                }
        codeStr=wheres[codeing]
        dtype = 'MySQL'
        if hasattr(get,'dtype') and get['dtype'] == 'SQLServer':   
          
            if re.match("^\d+",data_name): return public.returnMsg(False,'SQLServer数据库不能以数字开头!')                
            dtype = get['dtype']
            #添加SQLServer
            mssql_obj = panelMssql.panelMssql()
            result = mssql_obj.execute("CREATE DATABASE %s" % data_name)
            isError = self.IsSqlError(result)
            if  isError != None: return isError
            mssql_obj.execute("DROP LOGIN %s" % username)
        else:
            #添加MYSQL
            if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')

            mysql_obj = panelMysql.panelMysql()
            result = mysql_obj.execute("create database `" + data_name + "` DEFAULT CHARACTER SET " + codeing + " COLLATE " + codeStr)        
            isError = self.IsSqlError(result)
            if  isError != None: return isError
            mysql_obj.execute("drop user '" + username + "'@'localhost'")
            for a in address.split(','):
                mysql_obj.execute("drop user '" + username + "'@'" + a + "'")
        #添加用户
        self.__CreateUsers(dtype,data_name,username,password,address)

        if not hasattr(get,'ps'): get['ps'] = public.getMsg('INPUT_PS');
        addTime = time.strftime('%Y-%m-%d %X',time.localtime())
            
        pid = 0
        if hasattr(get,'pid'): pid = get.pid

        if hasattr(get,'contact'):                
            site = public.M('sites').where("id=?",(get.contact,)).field('id,name').find()
            if site:
                pid = int(get.contact)    
                get['ps'] = site['name']
        #添加入SQLITE
        public.M('databases').add('pid,name,username,password,accept,ps,addtime,type',(pid,data_name,username,password,address,get['ps'],addTime,dtype))
        public.WriteLog("TYPE_DATABASE", 'DATABASE_ADD_SUCCESS',(data_name,))
        return public.returnMsg(True,'ADD_SUCCESS')
        #except Exception as ex:
        #    public.WriteLog("TYPE_DATABASE",'DATABASE_ADD_ERR', (data_name,str(ex)))
        #    return public.returnMsg(False,'ADD_ERROR')
    
    #本地创建数据库
    def __CreateUsers(self,type,data_name,username,password,address):
        if type == 'SQLServer':          
            #添加SQLServer
            mssql_obj = panelMssql.panelMssql()
            mssql_obj.execute("use %s create login %s with password ='%s' , default_database = %s" % (data_name,username,password,data_name))
            mssql_obj.execute("use %s create user %s for login %s with default_schema=dbo" % (data_name,username,username))
            mssql_obj.execute("use %s exec sp_addrolemember 'db_owner','%s'" % (data_name,data_name))
            mssql_obj.execute("ALTER DATABASE %s SET MULTI_USER" % data_name)
        else:
            if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')

            mysql_obj = panelMysql.panelMysql()
            mysql_obj.execute("CREATE USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username,password))
            mysql_obj.execute("grant all privileges on `%s`.* to `%s`@`localhost`" % (data_name,username))
            for a in address.split(','):
                if a:                    
                    mysql_obj.execute("CREATE USER `%s`@`%s` IDENTIFIED BY '%s'" % (username,a,password))
                    mysql_obj.execute("grant all privileges on `%s`.* to `%s`@`%s`" % (data_name,username,a))
            mysql_obj.execute("flush privileges")
        
    #检查是否在回收站
    def CheckRecycleBin(self,name):
        try:
            for n in os.listdir('/www/Recycle_bin'):
                if n.find('BTDB_'+name+'_t_') != -1: return True;
            return False;
        except:
            return False;

    #检测数据库执行错误
    def IsSqlError(self,mysqlMsg):      
        if mysqlMsg:
            mysqlMsg = str(mysqlMsg)
            if "MySQLdb" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_MYSQLDB')
            if "2002," in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_CONNECT')
            if "2003," in mysqlMsg: return public.returnMsg(False,'数据库连接超时，请检查配置是否正确.')
            if "1045," in mysqlMsg: return public.returnMsg(False,'MySQL密码错误.')
            if "1040," in mysqlMsg: return public.returnMsg(False,'超过最大连接数，请稍后重试.')
            if "1130," in mysqlMsg: return public.returnMsg(False,'数据库连接失败，请检查root用户是否授权127.0.0.1访问权限.')
            if "using password:" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_PASS')
            if "Connection refused" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_CONNECT')
            if "1133" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_NOT_EXISTS')
            if "2005_login_error" == mysqlMsg: return public.returnMsg(False,'连接超时,请手动开启TCP/IP功能(开始菜单->SQL 2005->配置工具->2005网络配置->TCP/IP->启用)')
            if "DB-Lib error message 20018" in mysqlMsg: return public.returnMsg(False,'创建失败，SQL Server需要GUI支持，请通过远程桌面连接连接上SQL Server管理工具，依次找到安全性 -> 登录名 -> NT AUTHORITY\SYSTEM -> 属性 -> 服务器角色 -> 勾选列表中的sysadmin后重启SQL Server服务，重新操作添加数据库。')
            
        return None
    
    #删除数据库
    def DeleteDatabase(self,get):
        try:
            id=get['id']
            name = get['name']
    
            find = public.M('databases').where("id=?",(id,)).field('id,pid,name,username,password,type,accept,ps,addtime').find();
            accept = find['accept'];
            username = find['username'];
            if find['type'] == 'SQLServer':
                mssql_obj = panelMssql.panelMssql()
                mssql_obj.execute("ALTER DATABASE %s SET SINGLE_USER with ROLLBACK IMMEDIATE" % name)
                result = mssql_obj.execute("DROP DATABASE %s" % name)
                isError=self.IsSqlError(result)
                if  isError != None: return isError
                mssql_obj.execute("DROP LOGIN %s" % username)
                
            else:
                if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')
                #删除MYSQL
                mysql_obj = panelMysql.panelMysql()
                result = mysql_obj.execute("drop database `" + name + "`")
                isError=self.IsSqlError(result)
                if  isError != None: return isError
                users = mysql_obj.query("select Host from mysql.user where User='" + username + "' AND Host!='localhost'")
                mysql_obj.execute("drop user '" + username + "'@'localhost'")
                for us in users:
                    mysql_obj.execute("drop user '" + username + "'@'" + us[0] + "'")
                mysql_obj.execute("flush privileges")
            #删除SQLITE
            public.M('databases').where("id=?",(id,)).delete()
            public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS',(name,))
            return public.returnMsg(True, 'DEL_SUCCESS')
        except Exception as ex:
            public.WriteLog("TYPE_DATABASE",'DATABASE_DEL_ERR',(get.name , str(ex)))
            return public.returnMsg(False,'DEL_ERROR')
    
    #删除数据库到回收站  
    def DeleteToRecycleBin(self,name):
        import json
        data = public.M('databases').where("name=?",(name,)).field('id,pid,name,username,password,accept,ps,addtime').find();
        username = data['username'];
        panelMysql.panelMysql().execute("drop user '" + username + "'@'localhost'");
        users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + username + "' AND Host!='localhost'")
        for us in users:
            panelMysql.panelMysql().execute("drop user '" + username + "'@'" + us[0] + "'")
        panelMysql.panelMysql().execute("flush privileges");
        rPath = '/www/Recycle_bin/';
        public.writeFile(rPath + 'BTDB_' + name +'_t_' + str(time.time()),json.dumps(data));
        public.M('databases').where("name=?",(name,)).delete();
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS',(name,));
        return public.returnMsg(True,'RECYCLE_BIN_DB');
    
    #永久删除数据库
    def DeleteTo(self,filename):
        import json
        data = json.loads(public.readFile(filename))
        if public.M('databases').where("name=?",( data['name'],)).count():
            os.remove(filename);
            return public.returnMsg(True,'DEL_SUCCESS');
        result = panelMysql.panelMysql().execute("drop database `" + data['name'] + "`")
        isError=self.IsSqlError(result)
        if  isError != None: return isError
        panelMysql.panelMysql().execute("drop user '" + data['username'] + "'@'localhost'")
        users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + data['username'] + "' AND Host!='localhost'")
        for us in users:
            panelMysql.panelMysql().execute("drop user '" + data['username'] + "'@'" + us[0] + "'")
        panelMysql.panelMysql().execute("flush privileges")
        os.remove(filename);
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS',(data['name'],))
        return public.returnMsg(True,'DEL_SUCCESS');
    
    #恢复数据库
    def RecycleDB(self,filename):
        import json
        data = json.loads(public.readFile(filename))
        if public.M('databases').where("name=?",( data['name'],)).count():
            os.remove(filename);
            return public.returnMsg(True,'RECYCLEDB');
        result = panelMysql.panelMysql().execute("grant all privileges on `" + data['name'] + "`.* to '" + data['username'] + "'@'localhost' identified by '" + data['password'] + "'")
        isError=self.IsSqlError(result)
        if isError != None: return isError
        panelMysql.panelMysql().execute("grant all privileges on `" + data['name'] + "`.* to '" + data['username'] + "'@'" + data['accept'] + "' identified by '" + data['password'] + "'")
        panelMysql.panelMysql().execute("flush privileges")
        
        public.M('databases').add('id,pid,name,username,password,accept,ps,addtime',(data['id'],data['pid'],data['name'],data['username'],data['password'],data['accept'],data['ps'],data['addtime']))
        os.remove(filename);
        return public.returnMsg(True,"RECYCLEDB");
    
    #获取sa密码
    def GetSaPass(self,get):
        sa_path = 'data/sa.pl'
        if os.path.exists(sa_path):
            password = public.readFile(sa_path)
            return public.returnMsg(True,password)
        return public.returnMsg(False,'请先安装SQLServer.')

    #设置sa密码
    def SetSaPassword(self,get):
        password = get['password'].strip()
        rep = "^[\w@\.]+$"
        if not re.match(rep, password): return public.returnMsg(False, 'DATABASE_NAME_ERR_T')
        mssql_obj = panelMssql.panelMssql()
        result = mssql_obj.execute("EXEC sp_password NULL, '%s', 'sa'" % password)
        isError = self.IsSqlError(result)
        if  isError != None: return isError

        public.writeFile('data/sa.pl',password)
        msg = '修改sa密码成功！';
        session['config']['mssql_sa'] = password
        return public.returnMsg(True,msg)

    #设置ROOT密码
    def SetupPassword(self,get):       
        if not hasattr(get, 'password'):return public.returnMsg(False, '修改失败,参数传递错误.')

        password = get['password'].strip()
        if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')
        if not password:  return public.returnMsg(False, '修改失败，root密码不能为空.')
       
        #try:
        rep = "^[\w@\.]+$"
        if not re.match(rep, password): return public.returnMsg(False, 'root密码不能带有特殊符号!')
        mysql_root = public.M('config').where("id=?",(1,)).getField('mysql_root')
        #修改MYSQL
        mysql_obj = panelMysql.panelMysql()
        result = mysql_obj.query("show databases")
        isError=self.IsSqlError(result)
        is_modify = True
        if  isError != None: 
            #尝试使用新密码
            public.M('config').where("id=?",(1,)).setField('mysql_root',password)
            result = mysql_obj.query("show databases")
            isError=self.IsSqlError(result)
            if  isError != None: 
                setup_path = public.GetConfigValue('setup_path')
                shell = public.get_run_python("%s && cd %s/panel && [PYTHON] tools.py root %s" % (setup_path[0:2],setup_path,password));
                os.system(shell)
                is_modify = False
        if is_modify:
            if self._version.find('5.7') >= 0  or self._version.find('8.0') == 0:
                panelMysql.panelMysql().execute("UPDATE mysql.user SET authentication_string='' WHERE user='root'")
                panelMysql.panelMysql().execute("ALTER USER 'root'@'localhost' IDENTIFIED BY '%s'" % password)
                panelMysql.panelMysql().execute("ALTER USER 'root'@'127.0.0.1' IDENTIFIED BY '%s'" % password)
            else:
                result = mysql_obj.execute("update mysql.user set Password=password('" + password + "') where User='root'")
            mysql_obj.execute("flush privileges")

        msg = public.getMsg('DATABASE_ROOT_SUCCESS');
        #修改SQLITE
        public.M('config').where("id=?",(1,)).setField('mysql_root',password)  
        public.WriteLog("TYPE_DATABASE", "DATABASE_ROOT_SUCCESS")
        session['config']['mysql_root']= password
        return public.returnMsg(True,msg)
        #except Exception as ex:
        #    return public.returnMsg(False,'EDIT_ERROR' + str(ex));
    
    #修改用户密码
    def ResDatabasePassword(self,get):
        try:
            newpassword = get['password']
            username = get['name']
            id = get['id']

            if not newpassword: return public.returnMsg(False, '修改失败，数据库[' + username + ']密码不能为空.');
   
            find = public.M('databases').where("id=?",(id,)).field('id,pid,name,username,password,type,accept,ps,addtime').find();
            name = find['name']
            
            rep = "^[\w@\.]+$"
            if len(re.search(rep, newpassword).groups()) > 0: return public.returnMsg(False, 'DATABASE_NAME_ERR_T')
        
            if find['type'] == 'SQLServer':
                 mssql_obj = panelMssql.panelMssql()
                 mssql_obj.execute("EXEC sp_password NULL, '%s', '%s'" % (newpassword,username))
            else:
                if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')
                #修改MYSQL
                mysql_obj = panelMysql.panelMysql()
                m_version = public.readFile(self._setup_path + '/version.pl')
                if m_version.find('5.7') == 0  or m_version.find('8.0') == 0:
                    accept = self.map_to_list(panelMysql.panelMysql().query("select Host from mysql.user where User='" + name + "' AND Host!='localhost'"));
                    mysql_obj.execute("update mysql.user set authentication_string='' where User='" + username + "'")                                                                                                                                                        
                    result = mysql_obj.execute("ALTER USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username,newpassword))
                    for my_host in accept:
                        mysql_obj.execute("ALTER USER `%s`@`%s` IDENTIFIED BY '%s'" % (username,my_host[0],newpassword))
                else:
                    result = mysql_obj.execute("update mysql.user set Password=password('" + newpassword + "') where User='" + username + "'")
            
                isError=self.IsSqlError(result)
                if  isError != None: return isError
                mysql_obj.execute("flush privileges")

            #修改SQLITE
            if int(id) > 0:
                public.M('databases').where("id=?",(id,)).setField('password',newpassword)
            else:
                public.M('config').where("id=?",(id,)).setField('mysql_root',newpassword)
                session['config']['mysql_root'] = newpassword
            
            public.WriteLog("TYPE_DATABASE",'DATABASE_PASS_SUCCESS',(name,))
            return public.returnMsg(True,'DATABASE_PASS_SUCCESS',(name,))
        except Exception as ex:
            public.WriteLog("TYPE_DATABASE", str(ex))
            return public.returnMsg(False,str(ex))  

    def setMyCnf(self,action = True):
        myFile = '/etc/my.cnf'
        mycnf = public.readFile(myFile)
        root = session['config']['mysql_root']
        pwdConfig = "\n[mysqldump]\nuser=root\npassword=root"
        rep = "\n\[mysqldump\]\nuser=root\npassword=.+"
        if action:
            if mycnf.find(pwdConfig) > -1: return
            if mycnf.find("\n[mysqldump]\nuser=root\n") > -1:
                mycnf = mycnf.replace(rep, pwdConfig)
            else:
                mycnf  += "\n[mysqldump]\nuser=root\npassword=root"            
        else:
            mycnf = mycnf.replace(rep, '')
        public.writeFile(myFile,mycnf)
        
    #检测备份目录并赋值权限（MSSQL需要Authenticated Users）
    def CheckBackupPath(self,get):
        backupFile = session['config']['backup_path'] + '/database'
        if not os.path.exists(backupFile): 
            os.makedirs(backupFile)            
            get.filename = backupFile
            get.user = 'Authenticated Users'
            get.access = 2032127
            import files
            files.files().SetFileAccess(get)

    #备份
    def ToBackup(self,get):
        try:            
            id = get['id']
            find = public.M('databases').where("id=?",(id,)).field('name,type').find()
            if not find: return public.returnMsg(False,'数据库不存在!')
        
            self.CheckBackupPath(get);

            fileName = find['name'] + '_' + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.sql'
            if find['type'] == 'SQLServer': fileName = fileName.replace('.sql','.bak')

            backupName = session['config']['backup_path'] + '/database/' + fileName
            if find['type'] == 'SQLServer':
                #sqlserver .bak文件          
                mssql_obj = panelMssql.panelMssql()
                ret = mssql_obj.execute("backup database %s To disk='%s'" % (find['name'],backupName)) 
            else:
                if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')
                root = public.M('config').where('id=?',(1,)).getField('mysql_root');            
                try:
                    myconf = public.readFile(self._setup_path + '/my.ini')
                    rep = "port\s*=\s*([0-9]+)"
                    port = re.search(rep,myconf).groups()[0].strip();
                except :
                    port = '3306'

                public.ExecShell(self._setup_path + "/bin/mysqldump.exe --force --default-character-set="+ public.get_database_character(find['name']) +" -P" + port + " -uroot -p" + root + " -R " + find['name'] + " > " + backupName)

            if not os.path.exists(backupName): return public.returnMsg(False,'BACKUP_ERROR');

            sql = public.M('backup')
            addTime = time.strftime('%Y-%m-%d %X',time.localtime())
            sql.add('type,name,pid,filename,size,addtime',(1,fileName,id,backupName,0,addTime))
            public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS",(find['name'],))
            return public.returnMsg(True, 'BACKUP_SUCCESS')
        except Exception as ex:
            public.WriteLog("数据库管理", "备份数据库失败 => "  +  str(ex))
            return public.returnMsg(False,public.format_error(str(ex)))
    
    #删除备份文件
    def DelBackup(self,get):
        try:
            name=''
            id = get.id
            where = "id=?"
            filename = public.M('backup').where(where,(id,)).getField('filename')
            if os.path.exists(filename): os.remove(filename)
            
            if filename == 'qiniu':
                name = public.M('backup').where(where,(id,)).getField('name');
                
                public.ExecShell(public.get_run_python("[PYTHON] "+public.GetConfigValue('setup_path') + '/panel/script/backup_qiniu.py delete_file ' + name))
            
            public.M('backup').where(where,(id,)).delete()
            public.WriteLog("TYPE_DATABASE", 'DATABASE_BACKUP_DEL_SUCCESS',(name,filename))
            return public.returnMsg(True, 'DEL_SUCCESS');
        except Exception as ex:
            public.WriteLog("TYPE_DATABASE", 'DATABASE_BACKUP_DEL_ERR',(name,filename,str(ex)))
            return public.returnMsg(False,'DEL_ERROR')
    
    #导入
    def InputSql(self,get):
        try:
            name = get.name
            file = get.file

            find = public.M('databases').where("name=?",(name,)).field('name,type').find()
            if not find: return public.returnMsg(False,'数据库不存在!')

            tmp = file.split('.')
            exts = ['sql','zip','bak']
            ext = tmp[len(tmp) -1]
            if ext not in exts:
                return public.returnMsg(False, 'DATABASE_INPUT_ERR_FORMAT')
        
            backupPath = session['config']['backup_path'] + '/database'
       
            if ext == 'zip':
                try:
                    import zipfile
                    zip_file = zipfile.ZipFile(file)  
                    for names in zip_file.namelist():  
                        zip_file.extract(names,backupPath )      
                    zip_file.close()
                except : return public.returnMsg(False,'导入失败，该文件不是有效的zip格式的文件。')

            if find['type'] == 'SQLServer':
                mssql_obj = panelMssql.panelMssql()
                data = mssql_obj.query("use %s ;select filename from sysfiles" % find['name']) 
        
                mssql_obj.execute("ALTER DATABASE %s SET OFFLINE WITH ROLLBACK IMMEDIATE" % (find['name']))
                if ext != 'bak':
                    tmp = file.split('/')
                    tmpFile = tmp[len(tmp)-1]
                    tmpFile = tmpFile.replace('.' + ext, '.bak')
                    if not os.path.exists(backupPath + '/' + tmpFile) or tmpFile == '': return public.returnMsg(False, 'FILE_NOT_EXISTS',(tmpFile,))

                    mssql_obj.execute("use master;restore database %s from disk='%s' with replace, MOVE N'%s' TO N'%s',MOVE N'%s_Log'  TO N'%s' " % (find['name'],backupPath + '/' + tmpFile,find['name'],data[0][0],find['name'],data[1][0]))
                else:
                    mssql_obj.execute("use master;restore database %s from disk='%s' with replace, MOVE N'%s' TO N'%s',MOVE N'%s_Log'  TO N'%s' " % (find['name'],file,find['name'],data[0][0],find['name'],data[1][0]))
                mssql_obj.execute("ALTER DATABASE %s SET ONLINE" % (find['name']))
            else:
                if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')
         
                root = public.M('config').where('id=?',(1,)).getField('mysql_root');
                if ext != 'sql':
                    tmp = file.split('/')
                    tmpFile = tmp[len(tmp)-1]
                    tmpFile = tmpFile.replace('.' + ext, '.sql')
                    if not os.path.exists(backupPath + '/' + tmpFile) or tmpFile == '': return public.returnMsg(False, 'FILE_NOT_EXISTS',(tmpFile,))
                    public.ExecShell(self._setup_path + "/bin/mysql.exe -uroot -p" + root + " --force --default-character-set=utf8 " + name + "  < " + backupPath + '/' +tmpFile)
                else:
                    public.ExecShell(self._setup_path + "/bin/mysql.exe -uroot -p" + root + " --force --default-character-set=utf8 " + name + " < " + file)

            public.WriteLog("TYPE_DATABASE", 'DATABASE_INPUT_SUCCESS',(name,))
            return public.returnMsg(True, 'DATABASE_INPUT_SUCCESS');
        except Exception as ex:
            public.WriteLog("TYPE_DATABASE", 'DATABASE_INPUT_ERR',(name,str(ex)))
            return public.returnMsg(False,str(ex))
    
    #同步数据库到服务器
    def SyncToDatabases(self,get):
        type = int(get['type'])
        n = 0
        sql = public.M('databases')
        if type == 0:
            data = sql.field('id,name,username,password,accept,type').select()
            for value in data:
                #if value['type'] == 'SQLServer': return public.returnMsg(False,'SQLServer不支持同步功能.')                          
                result = self.ToDataBase(value)
                if result == 1: n +=1
        else:
            import json
            data = json.loads(get.ids)
            for value in data:
                find = sql.where("id=?",(value,)).field('id,name,username,password,accept,type').find()   
                #if find['type'] == 'SQLServer':  return public.returnMsg(False,'SQLServer不支持同步功能.')         
                result = self.ToDataBase(find)
                if result == 1: n +=1
        
        return public.returnMsg(True,'DATABASE_SYNC_SUCCESS',(str(n),))

    
    #添加到服务器
    def ToDataBase(self,find):
        if find['username'] == 'bt_default': return 0
        if len(find['password']) < 3 :
            find['username'] = find['name']
            find['password'] = public.md5(str(time.time()) + find['name'])[0:10]
            public.M('databases').where("id=?",(find['id'],)).save('password,username',(find['password'],find['username']))
        if find['type'] == 'SQLServer':

            mssql_obj = panelMssql.panelMssql()
            mssql_obj.execute("CREATE DATABASE %s" % find['name'])
            mssql_obj.execute("use %s create login %s with password ='%s' , default_database = %s" % (find['name'],find['username'],find['password'],find['name']))
            mssql_obj.execute("use %s create user %s for login %s with default_schema=dbo" % (find['name'],find['username'],find['username']))
            mssql_obj.execute("use %s exec sp_addrolemember 'db_owner','%s'" % (find['name'],find['name']))
            mssql_obj.execute("ALTER DATABASE %s SET MULTI_USER" % find['name'])

        else:
            if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')

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
            return 1
        
    #从服务器获取数据库
    def SyncGetDatabases(self,get):
        sql = public.M('databases')
        n = 0
        s = 0

        nameArr = ['information_schema','performance_schema','mysql','sys','master','model','msdb','tempdb']
        if public.get_server_status("mysql") >= 0:    
            if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')
            data = panelMysql.panelMysql().query("show databases")
            if not data: return public.returnMsg(False,'数据库连接失败，请检查配置是否正确.')

            isError = self.IsSqlError(data)
            if isError != None: return isError
            users = panelMysql.panelMysql().query("select User,Host from mysql.user where User!='root' AND Host!='localhost' AND Host!=''")
            
            try:
                for value in data:
                    b = False
                    for key in nameArr:
                        if value[0] == key:
                            b = True 
                            break
                    if b:continue
                    if sql.where("name=?",(value[0],)).count(): continue
                    host = '127.0.0.1'
                    for user in users:
                        if value[0] == user[0]:
                            host = user[1]
                            break
                
                    ps = public.getMsg('INPUT_PS')
                    if value[0] == 'test':
                            ps = public.getMsg('DATABASE_TEST')
                    addTime = time.strftime('%Y-%m-%d %X',time.localtime())
                    if sql.table('databases').add('name,username,password,accept,ps,addtime,type',(value[0],value[0],'',host,ps,addTime,'MySQL')): n +=1

            except Exception as ex:    
                public.submit_panel_bug('同步数据库异常 --> ' + str(data) + '  --------->' + str(ex))

               
        if public.get_server_status("MSSQLSERVER") >= 0:
            data = panelMssql.panelMssql().query('SELECT name FROM MASTER.DBO.SYSDATABASES ORDER BY name')
            if data:                
                for item in data:    
                    dbname = item[0]
                    if sql.where("name=?",(dbname,)).count(): continue
                    if not dbname in nameArr:
                        ps = public.getMsg('INPUT_PS')
                        addTime = time.strftime('%Y-%m-%d %X',time.localtime())
                        if sql.table('databases').add('name,username,password,accept,ps,addtime,type',(dbname,dbname,'','',ps,addTime,'SQLServer')): s +=1

        return public.returnMsg(True,'DATABASE_GET_SUCCESS',(str(n),))
        
    #获取数据库权限
    def GetDatabaseAccess(self,get):
        if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')

        name = get['name']
        users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + name + "' AND Host!='localhost'")
        isError = self.IsSqlError(users)
        if isError != None: return isError
        users = self.map_to_list(users)

        if len(users)<1: return public.returnMsg(True,"127.0.0.1")
        
        accs = []
        for c in users:
            accs.append(c[0]);
        userStr = ','.join(accs);
        return public.returnMsg(True,userStr)
    
    #设置数据库权限
    def SetDatabaseAccess(self,get):
        users = None
        try:
            if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')

            name = get['name']
            db_name = public.M('databases').where('username=?',(name,)).getField('name');
            access = get['access']
            #if access != '%' and filter_var(access, FILTER_VALIDATE_IP) == False: return public.returnMsg(False, '权限格式不合法')
            password = public.M('databases').where("username=?",(name,)).getField('password')
            users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + name + "' AND Host!='localhost'")
            for us in users:
                panelMysql.panelMysql().execute("drop user '" + name + "'@'" + us[0] + "'")
            for a in access.split(','):
                panelMysql.panelMysql().execute("grant all privileges on " + db_name + ".* to '" + name + "'@'" + a + "' identified by '" + password + "'")
            panelMysql.panelMysql().execute("flush privileges")
            return public.returnMsg(True, 'SET_SUCCESS')
        except Exception as ex:
            public.submit_panel_bug('设置数据库权限错误 --> ' + str(users) + ' error --> ' + str(ex))
            #public.WriteLog("TYPE_DATABASE",'DATABASE_ACCESS_ERR',(name ,str(ex)))
            return public.returnMsg(False,'SET_ERROR')
    
    #修改sqlserver端口
    def SetMsSQLPort(self,get):
        mssql_obj = panelMssql.panelMssql()    
        key = mssql_obj.get_mssql_reg_path()        
        if key:
            os.system("net stop MSSQLSERVER")
            public.WriteReg(key,'TcpPort',get.port)
            time.sleep(0.01)            
            os.system("net start MSSQLSERVER")
            return public.returnMsg(True, 'SQLServer端口修改成功！')
        return public.returnMsg(False, 'SQLServer端口修改失败,未知版本！')

    #获取mssql配置
    def GetMsSQLInfo(self,get):
        data = {}
        data['port'] = '1433';
        try:
            mssql_obj = panelMssql.panelMssql()     
            data['port'] = mssql_obj.get_port()
        except : pass               
        return data
    
    #获取数据库配置信息
    def GetMySQLInfo(self,get):
        data = {}          
        try:        
            if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')
            path = public.get_server_path('mysql');
            file = None;
            if path:
                file = re.search('([MySQL|MariaDB-]+\d+\.\d+)',path).groups()[0]
                
                myfile = public.GetConfigValue('setup_path') + '/mysql/'+file+'/my.ini'
                mycnf = public.readFile(myfile);
                
                rep = "datadir\s*?=\s?\"(.+)\"\s?"               
                data['datadir'] = re.search(rep,mycnf).groups()[0];

                rep = "port\s*=\s*([0-9]+)\s*\n"
                data['port'] = re.search(rep,mycnf).groups()[0];
        except:
            data['datadir'] = '';
            data['port'] = '3306';
        return data;
    
    #修改数据库目录
    def SetDataDir(self,get):
        return public.returnMsg(True,'暂不支持修改！');
    
    #修改数据库端口
    def SetMySQLPort(self,get):
        myfile = self._setup_path + '/my.ini';
        if not self._setup_path: return public.returnMsg(False,'修改失败，请检查是否安装MySQL');
    
        if not os.path.exists(myfile): return public.returnMsg(False,'修改失败，请检查是否安装MySQL');
            
        mycnf = public.readFile(myfile);
        rep = "port\s*=\s*([0-9]+)\s*\n"
        mycnf = re.sub(rep,'port = ' + get.port + '\n',mycnf);
        public.writeFile(myfile,mycnf);
        os.system('net stop mysql')
        os.system('net start mysql')

        return public.returnMsg(True,'EDIT_SUCCESS');
    
    #获取错误日志
    def GetErrorLog(self,get):
        info = self.GetMySQLInfo(get)
        if not info or not 'datadir' in info: return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')

        path = info['datadir'];
        filename = '';
        for n in os.listdir(path):
            if len(n) < 5: continue;
           
            if n[-9:] == 'error.log': 
                filename = path + '/' + n;
                break;
        if not os.path.exists(filename): return public.returnMsg(False,'FILE_NOT_EXISTS');
        if hasattr(get,'close'): 
            public.writeFile(filename,'')
            return public.returnMsg(True,'LOG_CLOSE');
       
        return public.GetNumLines(filename,1000);
    
    #二进制日志开关
    def BinLog(self,get):
        if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')

        myfile = self._setup_path + '/my.ini';
        mycnf = public.readFile(myfile);
        if mycnf.find('#log-bin=mysql-bin') != -1:
            if hasattr(get,'status'): return public.returnMsg(False,'0');
            mycnf = mycnf.replace('#log-bin=mysql-bin','log-bin=mysql-bin')
            mycnf = mycnf.replace('#binlog_format=mixed','binlog_format=mixed')
        else:
            info = self.GetMySQLInfo(get)
            if not info: return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')
            path = info['datadir'];
            if not os.path.exists(path): return public.returnMsg(False,'数据库目录不存在，请检查配置是否正确.')

            if hasattr(get,'status'): 
                dsize = 0;

                for n in os.listdir(path):
                    if len(n) < 9: continue;
                    if n[0:9] == 'mysql-bin':
                        dsize += os.path.getsize(path + '/' + n);
                return public.returnMsg(True,dsize);
            
            mycnf = mycnf.replace('log-bin=mysql-bin','#log-bin=mysql-bin')
            mycnf = mycnf.replace('binlog_format=mixed','#binlog_format=mixed')
            public.set_server_status('mysql','restart');
        
        public.writeFile(myfile,mycnf);
        return public.returnMsg(True,'SUCCESS');
    
    #获取MySQL配置状态
    def GetDbStatus(self,get):     
        if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')    
        
        result = {};
        data = self.map_to_list(panelMysql.panelMysql().query('show variables'));
        gets = ['table_open_cache','thread_cache_size','query_cache_type','key_buffer_size','query_cache_size','tmp_table_size','max_heap_table_size','innodb_buffer_pool_size','innodb_additional_mem_pool_size','innodb_log_buffer_size','max_connections','sort_buffer_size','read_buffer_size','read_rnd_buffer_size','join_buffer_size','thread_stack','binlog_cache_size'];
        result['mem'] = {}
        for d in data:
            try:
                for g in gets:
                    if d[0] == g: result['mem'][g] = d[1];
            except: continue
        if 'query_cache_type' in result['mem']:
            if result['mem']['query_cache_type'] != 'ON': result['mem']['query_cache_size'] = '0';
        return result;
    
    #设置MySQL配置参数
    def SetDbConf(self,get):
        if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')

        gets = ['key_buffer_size','query_cache_size','tmp_table_size','max_heap_table_size','innodb_buffer_pool_size','innodb_log_buffer_size','max_connections','query_cache_type','table_open_cache','thread_cache_size','sort_buffer_size','read_buffer_size','read_rnd_buffer_size','join_buffer_size','thread_stack','binlog_cache_size'];
        emptys = ['max_connections','query_cache_type','thread_cache_size','table_open_cache']
        mycnf = public.readFile(self._setup_path + '/my.ini');
        n = 0;
        for g in gets:
            s = 'M';
            if n > 5: s = 'K';
            if g in emptys: s = '';
            rep = '\s*'+g+'\s*=\s*\d+(M|K|k|m|G)?\n';
            c = g+' = ' + get[g] + s +'\n'
            if mycnf.find(g) != -1:
                mycnf = re.sub(rep,'\n'+c,mycnf,1);
            else:
                mycnf = mycnf.replace('[mysqld]\n','[mysqld]\n' +c)
            n+=1;
        public.writeFile(self._setup_path + '/my.ini',mycnf);
        return public.returnMsg(True,'SET_SUCCESS');
    
    #获取MySQL运行状态
    def GetRunStatus(self,get):
        if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')

        import time;
        result = {}
        data = panelMysql.panelMysql().query('show global status');

        isError = self.IsSqlError(data)
        if  isError != None: return isError

        gets = ['Max_used_connections','Com_commit','Com_rollback','Questions','Innodb_buffer_pool_reads','Innodb_buffer_pool_read_requests','Key_reads','Key_read_requests','Key_writes','Key_write_requests','Qcache_hits','Qcache_inserts','Bytes_received','Bytes_sent','Aborted_clients','Aborted_connects','Created_tmp_disk_tables','Created_tmp_tables','Innodb_buffer_pool_pages_dirty','Opened_files','Open_tables','Opened_tables','Select_full_join','Select_range_check','Sort_merge_passes','Table_locks_waited','Threads_cached','Threads_connected','Threads_created','Threads_running','Connections','Uptime']        
        try:
            for d in data:          
                for g in gets:
                    try:
                        if d[0].lower() == g.lower(): result[g] = d[1];
                    except : pass
            result['Run'] = int(time.time()) - int(result['Uptime'])
            tmp = panelMysql.panelMysql().query('show variables');
        except :
            public.submit_panel_bug('获取数据库状态失败 --> ' + str(data))                

        try:
            result['File'] = tmp[0][0];
            result['Position'] = tmp[0][1];
        except:
            result['File'] = 'OFF';
            result['Position'] = 'OFF';
        return result;
    
    #取慢日志
    def GetSlowLogs(self,get):
        if not self.check_server(): return public.returnMsg(False,'MySQL服务未安装或不是通过宝塔6.x以上版本安装的.')
        path = self._setup_path + '/data/mysql-slow.log';
        if not os.path.exists(path): return public.returnMsg(False,'日志文件不存在!');
        return public.returnMsg(True,public.GetNumLines(path,1000));
