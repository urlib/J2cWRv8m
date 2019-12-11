#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2019-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 黄文良 <287962566@qq.com>
#-------------------------------------------------------------------

#------------------------------
# 消息队列
#------------------------------
import sys,os,shutil,re
panelPath = os.getenv('BT_PANEL')
os.chdir(panelPath)
sys.path.append("class/")
import public,time,downloadFile,json

class bt_task:
    __table = 'task_list'
    __task_tips = 'data/bt_task_now.pl'
    __task_path = panelPath + '/tmp/'
    def __init__(self):

        #创建数据表
        sql = '''CREATE TABLE IF NOT EXISTS `task_list` (
  `id`              INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` 			TEXT,
  `type`			TEXT,
  `status` 			INTEGER,
  `shell` 			TEXT,
  `other`           TEXT,
  `exectime` 	  	INTEGER,
  `endtime` 	  	INTEGER,
  `addtime`			INTEGER
);'''
        public.M(None).execute(sql,())

        #创建临时目录
        if not os.path.exists(self.__task_path): os.makedirs(self.__task_path,384)

    #取任务列表
    def get_task_list(self,status=-3):
        sql = public.M(self.__table)
        if status != -3:
            sql = sql.where('status=?',(status,))
        data = sql.field('id,name,type,shell,other,status,exectime,endtime,addtime').select();
        return data

    #取任务列表前端
    def get_task_lists(self,get):
        sql = public.M(self.__table)
        if 'status' in get:
            if get.status == '-3':
                sql = sql.where('status=? OR status=?',(-1,0))
            else:
                sql = sql.where('status=?',(get.status,))
        data = sql.field('id,name,type,shell,other,status,exectime,endtime,addtime').order('id asc').limit('10').select();
        if not 'num' in get: get.num = 15
        num = int(get.num)
        for i in range(len(data)):
            data[i]['log'] = ''
            if data[i]['status'] == -1: 
                data[i]['log'] = self.get_task_log(data[i]['id'],data[i]['type'],num)
            elif data[i]['status'] == 1:
                data[i]['log'] = self.get_task_log(data[i]['id'],data[i]['type'],10)
            if data[i]['type'] == '3':
                data[i]['other'] = json.loads(data[i]['other'])
        return data

    #创建任务
    def create_task(self,task_name,task_type,task_shell,other=''):
        self.clean_log()
        public.M(self.__table).add('name,type,shell,other,addtime,status',(task_name,task_type,task_shell,other,int(time.time()),0))
        public.WriteFile(self.__task_tips,'True')
        os.system('net stop btTask')
        os.system('net start btTask')
        return True
    

    #修改任务
    def modify_task(self,id,key,value):
        public.M(self.__table).where('id=?',(id,)).setField(key,value)
        return True

    #删除任务
    def remove_task(self,get):
        task_info = self.get_task_find(get.id)
        public.M(self.__table).where('id=?',(get.id,)).delete();
        os.system('net stop btTask')
        os.system('net start btTask')
        return public.returnMsg(True,'任务已取消!')

    #取一条任务
    def get_task_find(self,id):
        data = public.M(self.__table).where('id=?',(id,)).field('id,name,type,shell,other,status,exectime,endtime,addtime').find()
        return data

    #执行任务
    #task_type  0.执行shell  1.下载文件  2.解压文件  3.压缩文件
    def execute_task(self,id,task_type,task_shell,other=''):
        if not os.path.exists(self.__task_path): os.makedirs(self.__task_path,384)
        log_file = self.__task_path + str(id) + '.log'

        #标记状态执行时间
        self.modify_task(id,'status',-1)
        self.modify_task(id,'exectime',int(time.time()))
        task_type = int(task_type)
        #开始执行
        if task_type == 0:      #执行命令
            os.system(task_shell + ' > ' + log_file + '  2>&1')
            print(task_shell + ' > ' + log_file + '  2>&1')
        elif task_type == 1:    #下载文件
            down_file = downloadFile.downloadFile()
            down_file.logPath = log_file
            print(down_file.DownloadFile(task_shell,other))
        elif task_type == 2:    #解压文件
            zip_info = json.loads(other)
            self._unzip(task_shell,zip_info['dfile'],zip_info['password'],log_file)
        elif task_type == 3:    #压缩文件
            zip_info = json.loads(other)
            if not 'z_type' in zip_info: zip_info['z_type'] = 'zip'
            print(self._zip(task_shell,zip_info['sfile'],zip_info['dfile'],log_file,zip_info['z_type']))
        elif task_type == 4:    #备份数据库
            self.backup_database(task_shell,log_file)
        elif task_type == 5:    #导入数据库
            self.input_database(task_shell,other,log_file)
        elif task_type == 6:    #备份网站
            self.backup_site(task_shell,log_file)
        elif task_type == 7:    #恢复网站
            pass
        
        #标记状态与结束时间
        self.modify_task(id,'status',1)
        self.modify_task(id,'endtime',int(time.time()))

    #开始检测任务
    def start_task(self):       
        noe = False
        while True: 
           
            try:
                time.sleep(1);
                if not os.path.exists(self.__task_tips) and noe: continue;
                if os.path.exists(self.__task_tips): os.remove(self.__task_tips)
                public.M(self.__table).where('status=?',('-1',)).setField('status',0)
                task_list = self.get_task_list(0)
                for task_info in task_list:
                    self.execute_task(task_info['id'],task_info['type'],task_info['shell'],task_info['other'])
                noe = True
            except: print(public.get_error_info())

    #取任务执行日志
    def get_task_log(self,id,task_type,num=5):
        log_file = self.__task_path + str(id) + '.log'
        if not os.path.exists(log_file):
            data = ''
            if(task_type == '1'): data = {'name':'下载文件','total':0,'used':0,'pre':0,'speed':0}
            return data
        data = public.GetNumLines(log_file,num)
        n = 0
        if(task_type == '1'): 
            try:
                data = json.loads(data)
            except:
                if n < 3:
                    time.sleep(2);
                    n+=1
                    self.get_task_log(id,task_type,num)
                else:
                    data = {'name':'下载文件','total':0,'used':0,'pre':0,'speed':0}
            if data == [] and n < 3: 
                time.sleep(1);
                n+=1
                self.get_task_log(id,task_type,num)
        else:
            if type(data) == list: return ''
            data = data.replace('\x08','').replace('\n','<br>')

        return data
    
    #清理任务日志
    def clean_log(self):
        s_time = int(time.time())
        timeout = 86400
        for f in os.listdir(self.__task_path):
            filename = self.__task_path + f
            c_time = os.stat(filename).st_ctime
            if s_time - c_time > timeout: 
                if os.path.isdir(filename):
                    shutil.rmtree(filename)
                else:
                    os.remove(filename)
        return True

    #文件压缩
    def _zip(self,path,sfile,dfile,log_file):
        old_path = path + '/' + sfile       
        if not os.path.exists(old_path): return public.returnMsg(False,'FILE_NOT_EXISTS');
               
        filelists = []
        if os.path.isdir(old_path):
            public.get_file_list(old_path, filelists)
        else:
            filelists.append(old_path)
 
        import zipfile  
        f = zipfile.ZipFile(dfile,'w',zipfile.ZIP_DEFLATED)
        for item in filelists:     
            print(item)
            f.write(item,item.replace(path,""))       
        f.close()  
        public.WriteLog("TYPE_FILE", 'ZIP_SUCCESS',(sfile,dfile));
        return public.returnMsg(True,'ZIP_SUCCESS')
    
    
    #文件解压
    def _unzip(self,sfile,dfile,password,log_file):
        if not os.path.exists(sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS');
              
        import zipfile
        zip_file = zipfile.ZipFile(sfile)  
        for names in zip_file.namelist():  
            zip_file.extract(names,dfile)  
        zip_file.close()

        public.WriteLog("TYPE_FILE", 'UNZIP_SUCCESS',(sfile,dfile));
        return public.returnMsg(True,'UNZIP_SUCCESS');

    #备份网站
    def backup_site(self,id,log_file):
        find = public.M('sites').where("id=?",(id,)).field('name,path,id').find();
        fileName = find['name']+'_'+time.strftime('%Y%m%d_%H%M%S',time.localtime())+'.zip';
        backupPath = public.M('config').where('id=?',(1,)).getField('backup_path') + '/site'

        zipName = backupPath + '/'+ fileName;
        if not (os.path.exists(backupPath)): os.makedirs(backupPath)
  
        dir_name = os.path.basename(find['path'])
        root_path = find['path'].replace(dir_name,'')
        self._zip(root_path,dir_name,zipName,log_file)       
       
        sql = public.M('backup').add('type,name,pid,filename,size,addtime',(0,fileName,find['id'],zipName,0,public.getDate()));
        public.WriteLog('TYPE_SITE', 'SITE_BACKUP_SUCCESS',(find['name'],));
        return public.returnMsg(True, 'BACKUP_SUCCESS');

    #备份数据库
    def backup_database(self,id,log_file):
        dfind = public.M('databases').where("id=?",(id,)).field('name,type').find();
        find = public.M('config').where('id=?',(1,)).field('mysql_root,backup_path').find()

        if not os.path.exists(find['backup_path'] + '/database'): os.makedirs(find['backup_path'] + '/database')
 
        fileName = dfind['name'] + '_' + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.sql'
        backupName = find['backup_path'] + '/database/' + fileName

        if dfind['type'] == 'MySQL':
            _version = re.search('([MySQL|MariaDB-]+\d+\.\d+)',public.get_server_path('mysql')).groups()[0] 
            _setup_path  = public.GetConfigValue('setup_path') + '/mysql/' + _version

            try:
                myconf = public.readFile(_setup_path + '/my.ini')
                rep = "port\s*=\s*([0-9]+)"
                port = re.search(rep,myconf).groups()[0].strip();
            except :
                port = '3306'

            public.ExecShell(_setup_path + "/bin/mysqldump.exe --default-character-set="+ public.get_database_character(dfind['name']) +" -uroot -p" + find['mysql_root'] + " -R " + dfind['name'] + " > " + backupName)
            if not os.path.exists(backupName):
                return public.returnMsg(False, '数据库备份失败。')
        else:
            import panelMssql
            backupName = backupName.replace('.sql','.bak')                 
            mssql_obj = panelMssql.panelMssql()
            mssql_obj.execute("backup database %s To disk='%s'" % (dfind['name'],backupName))

        filename = backupName.replace(".bak",".zip").replace(".sql",".zip")
        
        dir_name = os.path.basename(backupName)
        root_path = backupName.replace(dir_name,'')
        self._zip(root_path,dir_name,filename,log_file)     
        os.remove(backupName)
        sql = public.M('backup')
        addTime = time.strftime('%Y-%m-%d %X',time.localtime())
        sql.add('type,name,pid,filename,size,addtime',(1,fileName,id,backupName,0,addTime))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS",(dfind['name'],))
        return public.returnMsg(True, 'BACKUP_SUCCESS')

    #导入数据库
    def input_database(self,id,file,log_file):
        find = public.M('databases').where("id=?",(id,)).field('name,type').find()
       
        if not find: return public.returnMsg(False,'数据库不存在!')

        tmp = file.split('.')
        exts = ['sql','zip','bak']
        ext = tmp[len(tmp) -1]
        if ext not in exts:
            return public.returnMsg(False, 'DATABASE_INPUT_ERR_FORMAT')
        
        backupPath = public.M('config').where('id=?',(1,)).getField('backup_path') + '/database'
        if ext == 'zip':
            import zipfile
            zip_file = zipfile.ZipFile(file)  
            for names in zip_file.namelist():  
                zip_file.extract(names,backupPath )      
            zip_file.close()

        if find['type'] == 'SQLServer':
            import panelMssql
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
            root = public.M('config').where('id=?',(1,)).getField('mysql_root');

            _version = re.search('([MySQL|MariaDB-]+\d+\.\d+)',public.get_server_path('mysql')).groups()[0] 
            _setup_path  = public.GetConfigValue('setup_path') + '/mysql/' + _version

            if ext != 'sql':
                tmp = file.split('/')
                tmpFile = tmp[len(tmp)-1]
                tmpFile = tmpFile.replace('.' + ext, '.sql')
                if not os.path.exists(backupPath + '/' + tmpFile) or tmpFile == '': return public.returnMsg(False, 'FILE_NOT_EXISTS',(tmpFile,))
                public.ExecShell(_setup_path + "/bin/mysql.exe -uroot -p" + root + " --default-character-set=utf8 " + find['name'] + "  < " + backupPath + '/' +tmpFile)
            else:
                public.ExecShell(_setup_path + "/bin/mysql.exe -uroot -p" + root + " --default-character-set=utf8 " + find['name'] + " < " + file)

        public.WriteLog("TYPE_DATABASE", 'DATABASE_INPUT_SUCCESS',(find['name'],))
        return public.returnMsg(True, 'DATABASE_INPUT_SUCCESS');



if __name__ == '__main__':
    p = bt_task()
    #p.create_task('测试执行SHELL',0,'yum install wget -y','')
    #print(p.get_task_list())
    #p.modify_task(3,'status',0)
    #p.modify_task(3,'shell','bash /www/server/panel/install/install_soft.sh 0 update php 5.6')
    #p.modify_task(1,'other','{"sfile":"BTPanel","dfile":"/www/test.rar","z_type":"rar"}')
    #p.start_task()
    #p._zip("C:\wwwroot\node1.ffce.cn","node1.ffce.cn","web.zip","")
    p.input_database(2,"C:/backup/database/teeeees_20190717_162828.zip",'')
    #p.backup_database(2,'')
