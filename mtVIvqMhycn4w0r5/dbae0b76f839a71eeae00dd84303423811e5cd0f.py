import public,db,re,os,time
import zipfile    

class panelBackup:
    def __init__(self):
        pass

    #备份网站
    def backupSite(self,name):
       
        sql = db.Sql();
        path = sql.table('sites').where('name=?',(name,)).getField('path');
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        if not path:            
            log = "网站["+name+"]不存在!"
            print("★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return;
        
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/site';
        if not os.path.exists(backup_path): os.makedirs(backup_path)        
        filename = backup_path + "/Web_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.zip'

        #ZIP压缩
        self.Zip(path,filename);
        
        if not os.path.exists(filename):
            log = "网站["+name+"]备份失败!"
            print("★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return False;       

        return filename

    #备份数据库
    def backupDatabase(self,name):

        sql = db.Sql();
        find = sql.table('databases').where('name=?',(name,)).field('id,type').find();
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        if not find['id']:            
            log = u"数据库["+name+u"]不存在!"
            print(u"★["+endDate+"] "+log)
            print(u"----------------------------------------------------------------------------")
            return False;
        
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/database';
        if not os.path.exists(backup_path): os.makedirs(backup_path);
        
        sqlfile = backup_path + "/Db_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime())+".sql"      

        if find['type'] == 'MySQL':
            mysql_root = sql.table('config').where("id=?",(1,)).getField('mysql_root')        
            if public.get_server_status('mysql') < 0:
                log = u"未安装MySQL服务!"
                print(u"★["+endDate+"] "+log)
                print(u"----------------------------------------------------------------------------")
                return False;
        
            #去mysql安装目录
            _version = re.search('([MySQL|MariaDB-]+\d+\.\d+)',public.get_server_path('mysql')).groups()[0] 
            _setup_path  = public.GetConfigValue('setup_path') + '/mysql/' + _version

            try:
                myconf = public.readFile(_setup_path + '/my.ini')
                rep = "port\s*=\s*([0-9]+)"
                port = re.search(rep,myconf).groups()[0].strip();
            except :
                port = '3306'

            public.ExecShell(_setup_path + "/bin/mysqldump.exe --force --default-character-set="+ public.get_database_character(name) +" -uroot -p" + mysql_root + " -R " + name + " > " + sqlfile)
            if not os.path.exists(sqlfile):
                endDate = time.strftime('%Y/%m/%d %X',time.localtime())
                log = u"数据库["+name+u"]备份失败!"
                print(u"★[" + endDate + "] "+log)
                print(u"----------------------------------------------------------------------------")
                return False; 
        else:
            if public.get_server_status('MSSQLSERVER') < 0:
                log = u"未安装SQLServer服务!"
                print(u"★["+endDate+"] "+log)
                print(u"----------------------------------------------------------------------------")
                return;
            import panelMssql
            sqlfile = sqlfile.replace('.sql','.bak')                 
            mssql_obj = panelMssql.panelMssql()
            mssql_obj.execute("backup database %s To disk='%s'" % (name,sqlfile))
        
        filename = sqlfile.replace(".bak",".zip").replace(".sql",".zip")
        self.Zip(sqlfile,filename);
        os.remove(sqlfile)

        return filename
    
    #备份指定目录
    def backupPath(self,path):
        sql = db.Sql();

        if path[-1:] == '/': path = path[:-1]
        name = os.path.basename(path)
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/path';
        if not os.path.exists(backup_path): os.makedirs(backup_path);
        filename = backup_path + "/Path_" + name + "_" + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.zip'

        self.Zip(path,filename)    
        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        if not os.path.exists(filename):
            log = u"目录["+path+"]备份失败"
            print(u"★["+endDate+"] "+log)
            print(u"----------------------------------------------------------------------------")
            return False;

        return filename


    #文件压缩
    def Zip(self,sfile,dfile) :           
        try:
            import zipfile
            filelists = []
            path = sfile;
            if os.path.isdir(sfile): 
                self.GetFileList(sfile, filelists)
            else:
                path = os.path.dirname(sfile)
                filelists.append(sfile)
       
            f = zipfile.ZipFile(dfile,'w',zipfile.ZIP_DEFLATED)
            for item in filelists:
                f.write(item,item.replace(path,''))       
            f.close()   
            return True
        except :
            return False      
    
    #获取所有文件列表
    def GetFileList(self,path, list):        
        files = os.listdir(path)
        list.append(path)
        for file in files:
            if os.path.isdir(path + '/' + file):
                self.GetFileList(path + '/' + file, list)
            else:
                list.append(path + '/' + file)