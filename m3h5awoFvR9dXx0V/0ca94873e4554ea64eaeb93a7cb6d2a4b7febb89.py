#!/usr/bin/python
#coding: utf-8
#-----------------------------
# 宝塔Windows面板网站备份工具
#-----------------------------

import sys,os
panelPath = os.getenv('BT_PANEL')
sys.path.insert(0,panelPath + "/class/")
import public,db,time,panelMssql

class backupTools:
    
    def backupSite(self,name,count):
        sql = db.Sql();
        path = sql.table('sites').where('name=?',(name,)).getField('path');
        startTime = time.time();
        if not path:
            endDate = time.strftime('%Y/%m/%d %X',time.localtime())
            log = u"网站["+name+"]不存在!"
            print(u"★["+endDate+"] "+log)
            print("----------------------------------------------------------------------------")
            return;
        
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/site';
        if not os.path.exists(backup_path):  os.makedirs(backup_path)

        filename= backup_path + "/Web_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.zip'
        self.Zip(path,filename);

        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        
        if not os.path.exists(filename):
            log = u"网站["+name+u"]备份失败!"
            print(u"★["+endDate+"] "+log)
            print(u"----------------------------------------------------------------------------")
            return;
        
        outTime = time.time() - startTime
        pid = sql.table('sites').where('name=?',(name,)).getField('id');
        sql.table('backup').add('type,name,pid,filename,addtime,size',('0',os.path.basename(filename),pid,filename,endDate,os.path.getsize(filename)))
        log = u"网站["+name+u"]备份成功,用时["+str(round(outTime,2))+u"]秒";
        public.WriteLog(u'计划任务',log)
        print(u"★["+endDate+"] " + log)
        print(u"|---保留最新的["+count+u"]份备份")
        print(u"|---文件名:"+filename)
        
        #清理多余备份     
        backups = sql.table('backup').where('type=? and pid=?',('0',pid)).field('id,filename').select();
        
        num = len(backups) - int(count)
        if  num > 0:
            for backup in backups:      
                if os.path.exists(backup['filename']): os.remove(backup['filename'])
                sql.table('backup').where('id=?',(backup['id'],)).delete();
                num -= 1;
                print(u"|---已清理过期备份文件：" + backup['filename'])
                if num < 1: break;
    
    def backupDatabase(self,name,count):    
        import re
        sql = db.Sql();
        find = sql.table('databases').where('name=?',(name,)).field('id,type').find();
        startTime = time.time();
        if not find:
            endDate = time.strftime('%Y/%m/%d %X',time.localtime())
            log = u"数据库["+name+u"]不存在!"
            print(u"★["+endDate+"] "+log)
            print(u"----------------------------------------------------------------------------")
            return;
        
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/database';
        if not os.path.exists(backup_path): os.makedirs(backup_path);
        
        sqlfile = backup_path + "/Db_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime())+".sql"    
        
        #执行MySQL备份
        if find['type'] == 'MySQL':            
            mysql_root = sql.table('config').where("id=?",(1,)).getField('mysql_root')        
            if public.get_server_status('mysql') < 0:
                log = u"未安装MySQL服务!"
                print(u"★["+endDate+"] "+log)
                print(u"----------------------------------------------------------------------------")
                return;
        
            #取mysql安装目录
            _version = re.search('([MySQL|MariaDB-]+\d+\.\d+)',public.get_server_path('mysql')).groups()[0] 
            _setup_path  = public.GetConfigValue('setup_path') + '/mysql/' + _version

            try:
                myconf = public.readFile(_setup_path + '/my.ini')
                rep = "port\s*=\s*([0-9]+)"
                port = re.search(rep,myconf).groups()[0].strip();
            except :
                port = '3306'

            public.ExecShell(_setup_path + "/bin/mysqldump.exe --force --default-character-set="+ public.get_database_character(name) +" -P" + port + " -uroot -p" + mysql_root + " -R " + name + " > " + sqlfile)
            if not os.path.exists(sqlfile):
                endDate = time.strftime('%Y/%m/%d %X',time.localtime())
                log = u"数据库["+name+u"]备份失败!"
                print(u"★["+endDate+"] "+log)
                print(u"----------------------------------------------------------------------------")
                return;   
        else:
            if public.get_server_status('MSSQLSERVER') < 0:
                log = u"未安装SQLServer服务!"
                print(u"★["+endDate+"] "+log)
                print(u"----------------------------------------------------------------------------")
                return;

            sqlfile = sqlfile.replace('.sql','.bak')                 
            mssql_obj = panelMssql.panelMssql()
            mssql_obj.execute("backup database %s To disk='%s'" % (name,sqlfile))

        filename = sqlfile.replace(".bak",".zip").replace(".sql",".zip")
        self.Zip(sqlfile,filename);
        os.remove(sqlfile)

        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        outTime = time.time() - startTime
        pid = sql.table('databases').where('name=?',(name,)).getField('id');

        
        sql.table('backup').add('type,name,pid,filename,addtime,size',(1,os.path.basename(filename),pid,filename,endDate,os.path.getsize(filename)))
        log = u"数据库["+name+u"]备份成功,用时["+str(round(outTime,2))+u"]秒";
        public.WriteLog(u'计划任务',log)
        print("★["+endDate+"] " + log)
        print(u"|---保留最新的["+count+u"]份备份")
        print(u"|---文件名:"+filename)
        
        #清理多余备份     
        backups = sql.table('backup').where('type=? and pid=?',('1',pid)).field('id,filename').select();
        
        num = len(backups) - int(count)
        if  num > 0:            
            for backup in backups:
                sql.table('backup').where('id=?',(backup['id'],)).delete();               
                if os.path.exists(backup['filename']): os.remove(backup['filename'])
                num -= 1;
                print(u"|---已清理过期备份文件：" + backup['filename'])
                if num < 1: break;
    
    #备份指定目录
    def backupPath(self,path,count):
        sql = db.Sql();
        startTime = time.time();
        name = os.path.basename(path)
        backup_path = sql.table('config').where("id=?",(1,)).getField('backup_path') + '/path';
        if not os.path.exists(backup_path): os.makedirs(backup_path);
        filename= backup_path + "/Path_" + name + "_" + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.zip'
        print(filename)

        self.Zip(path,filename);                

        endDate = time.strftime('%Y/%m/%d %X',time.localtime())
        if not os.path.exists(filename):
            log = u"目录["+path+"]备份失败"
            print(u"★["+endDate+"] "+log)
            print(u"----------------------------------------------------------------------------")
            return;
        
        outTime = time.time() - startTime
        sql.table('backup').add('type,name,pid,filename,addtime,size',('2',path,'0',filename,endDate,os.path.getsize(filename)))
        log = u"目录["+path+"]备份成功,用时["+str(round(outTime,2))+"]秒";
        public.WriteLog(u'计划任务',log)
        print(u"★["+endDate+"] " + log)
        print(u"|---保留最新的["+count+u"]份备份")
        print(u"|---文件名:"+filename)
        
        #清理多余备份     
        backups = sql.table('backup').where('type=? and pid=?',('2',0)).field('id,filename').select();
        
        num = len(backups) - int(count)
        if  num > 0:
            for backup in backups:
                if os.path.exists(backup['filename']): os.remove(backup['filename'])
                sql.table('backup').where('id=?',(backup['id'],)).delete();
                num -= 1;
                print(u"|---已清理过期备份文件：" + backup['filename'])
                if num < 1: break;
        
    
    def backupSiteAll(self,save):
        sites = public.M('sites').field('name').select()
        for site in sites:
            self.backupSite(site['name'],save)
        

    def backupDatabaseAll(self,save):
        databases = public.M('databases').field('name').select()
        for database in databases:
            self.backupDatabase(database['name'],save)
        
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

if __name__ == "__main__":
    backup = backupTools()
    type = sys.argv[1];
    if type == 'site':
        if sys.argv[2] == 'all':
             backup.backupSiteAll(sys.argv[3])
        else:
            backup.backupSite(sys.argv[2], sys.argv[3])
    elif type == 'path':
        backup.backupPath(sys.argv[2],sys.argv[3])
    elif type == 'database':
        if sys.argv[2] == 'all':
            backup.backupDatabaseAll(sys.argv[3])
        else:
            backup.backupDatabase(sys.argv[2], sys.argv[3])
    