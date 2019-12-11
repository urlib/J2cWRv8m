#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

#------------------------------
# 计划任务
#------------------------------

import win32serviceutil,win32service,win32event,os,sys,json,psutil,time

global pre,timeoutCount,logPath,isTask,isCron,oldEdate,isCheck
pre = 0
timeoutCount = 0
isCheck = 0
oldEdate = None


class MyBad():
    _msg = None
    def __init__(self,msg):
        self._msg = msg
    def __repr__(self):
        return self._msg
        

def ExecShell(cmdstring, cwd=None, timeout=None, shell=True):
    try:
        global logPath
        import shlex
        import datetime
        import subprocess
        import time
    
        if timeout:
            end_time = datetime.datetime.now() + datetime.timedelta(seconds=timeout)

        sub = subprocess.Popen(cmdstring+' > '+logPath+' 2>&1', cwd=cwd, stdin=subprocess.PIPE,shell=shell,bufsize=4096)
        
        while sub.poll() is None:
            time.sleep(0.1)
                
        return sub.returncode
    except:
        return None

#下载文件
def DownloadFile(url,filename):
    try:
        public.downloadFile(url,filename)
        WriteLogs('done')
    except:
        WriteLogs('done')


#下载文件进度回调  
def DownloadHook(count, blockSize, totalSize):
    global pre
    used = count * blockSize
    pre1 = int((100.0 * used / totalSize))
    if pre == pre1:
        return
    speed = {'total':totalSize,'used':used,'pre':pre}
    WriteLogs(json.dumps(speed))
    pre = pre1

#写输出日志
def WriteLogs(logMsg):
    try:
        global logPath
        fp = open(logPath,'w+');
        fp.write(logMsg)
        fp.close()
    except:
        pass;

#任务队列 
def startTask():
    global isTask
    import time,public
    try:
        while True:
            #try:       
            if os.path.exists(isTask):
                sql = db.Sql()
                sql.table('tasks').where("status=?",('-1',)).setField('status','0')
        
                taskArr = sql.table('tasks').where("status=?",('0',)).field('id,type,execstr').order("id asc").select();          
                for value in taskArr:
                    start = int(time.time());
                   
                    if not sql.table('tasks').where("id=?",(value['id'],)).count(): continue;
                    sql.table('tasks').where("id=?",(value['id'],)).save('status,start',('-1',start))
                    if value['type'] == 'download':
                        argv = value['execstr'].split('|bt|')
                        DownloadFile(argv[0],argv[1])
                    elif value['type'] == 'execshell':                    
                        ExecShell(value['execstr'])
                    end = int(time.time())
                    sql.table('tasks').where("id=?",(value['id'],)).save('status,end',('1',end))
                    if(sql.table('tasks').where("status=?",('0')).count() < 1): os.remove(isTask)
            #except:            
            siteEdate();
            time.sleep(2)
    except:
        time.sleep(5);
        startTask();
        
#网站到期处理
def siteEdate():
    global oldEdate
    try:
        if not oldEdate: oldEdate = public.readFile('data/edate.pl');
        if not oldEdate: oldEdate = '0000-00-00';
        mEdate = time.strftime('%Y-%m-%d',time.localtime())
        if oldEdate == mEdate: return False;
        edateSites = public.M('sites').where('edate>? AND edate<? AND (status=? OR status=?)',('0000-00-00',mEdate,1,u'正在运行')).field('id,name').select();
        import panelSite;
        siteObject = panelSite.panelSite();
        for site in edateSites:
            get = MyBad('');
            get.id = site['id'];
            get.name = site['name'];
            siteObject.SiteStop(get);
        oldEdate = mEdate;
        public.writeFile('data/edate.pl',mEdate);
    except:
         pass;

#系统监控任务
def systemTask():
    #try:
        import psutil,time
        filename = 'data/control.conf';
        sql = db.Sql().dbfile('system')
        csql = '''CREATE TABLE IF NOT EXISTS `load_average` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pro` REAL,
  `one` REAL,
  `five` REAL,
  `fifteen` REAL,
  `addtime` INTEGER
)'''
        sql.execute(csql,())
        cpuIo = cpu = {}
        cpuCount = psutil.cpu_count()
        used = count = 0
        reloadNum=0
        network_up = network_down = diskio_1 = diskio_2 = networkInfo = cpuInfo = diskInfo = None
        while True:
            if not os.path.exists(filename):
                time.sleep(10);
                continue;
            
            day = 30;
            try:
                day = int(public.readFile(filename));
                if day < 1:
                    time.sleep(10)
                    continue;
            except:
                day  = 30
            
            
            tmp = {}
            #取当前CPU Io     
            tmp['used'] = psutil.cpu_percent(interval=1)
            
            if not cpuInfo:
                tmp['mem'] = GetMemUsed()
                cpuInfo = tmp 
            
            if cpuInfo['used'] < tmp['used']:
                tmp['mem'] = GetMemUsed()
                cpuInfo = tmp 
            
            
            
            #取当前网络Io
            networkIo = psutil.net_io_counters()[:4]
            if not network_up:
                network_up   =  networkIo[0]
                network_down =  networkIo[1]
            tmp = {}
            tmp['upTotal']      = networkIo[0]
            tmp['downTotal']    = networkIo[1]
            tmp['up']           = round(float((networkIo[0] - network_up) / 1024),2)
            tmp['down']         = round(float((networkIo[1] - network_down) / 1024),2)
            tmp['downPackets']  = networkIo[3]
            tmp['upPackets']    = networkIo[2]
            
            network_up   =  networkIo[0]
            network_down =  networkIo[1]
            
            if not networkInfo: networkInfo = tmp
            if (tmp['up'] + tmp['down']) > (networkInfo['up'] + networkInfo['down']): networkInfo = tmp
            
            #取磁盘Io
            #if os.path.exists('/proc/diskstats'):
            diskio_2 = psutil.disk_io_counters()
            if not diskio_2: 
                public.ExecShell('diskperf -y') #启用IO计数器
                diskio_2 = psutil.disk_io_counters()
                
            if not diskio_1: diskio_1 = diskio_2
            tmp = {}
            tmp['read_count']   = diskio_2.read_count - diskio_1.read_count
            tmp['write_count']  = diskio_2.write_count - diskio_1.write_count
            tmp['read_bytes']   = diskio_2.read_bytes - diskio_1.read_bytes
            tmp['write_bytes']  = diskio_2.write_bytes - diskio_1.write_bytes
            tmp['read_time']    = diskio_2.read_time - diskio_1.read_time
            tmp['write_time']   = diskio_2.write_time - diskio_1.write_time
                
            if not diskInfo: 
                diskInfo = tmp
            else:
                diskInfo['read_count']   += tmp['read_count']
                diskInfo['write_count']  += tmp['write_count']
                diskInfo['read_bytes']   += tmp['read_bytes']
                diskInfo['write_bytes']  += tmp['write_bytes']
                diskInfo['read_time']    += tmp['read_time']
                diskInfo['write_time']   += tmp['write_time']
                
            diskio_1 = diskio_2
            
            if count >= 12:
                try:
                    addtime = int(time.time())
                    deltime = addtime - (day * 86400)
                    
                    data = (cpuInfo['used'],cpuInfo['mem'],addtime)
                    sql.table('cpuio').add('pro,mem,addtime',data)
                    sql.table('cpuio').where("addtime<?",(deltime,)).delete();
                    
                    data = (round(networkInfo['up'] / 5,2),round(networkInfo['down'] / 5 ,2),networkInfo['upTotal'],networkInfo['downTotal'],networkInfo['downPackets'],networkInfo['upPackets'],addtime)
                    sql.table('network').add('up,down,total_up,total_down,down_packets,up_packets,addtime',data)
                    sql.table('network').where("addtime<?",(deltime,)).delete();
                    #if os.path.exists('/proc/diskstats'):
                    data = (diskInfo['read_count'],diskInfo['write_count'],diskInfo['read_bytes'],diskInfo['write_bytes'],diskInfo['read_time'],diskInfo['write_time'],addtime)
                    sql.table('diskio').add('read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime',data)
                    sql.table('diskio').where("addtime<?",(deltime,)).delete();
                    
                   
                    lpro = None
                    load_average = None
                    cpuInfo = None
                    networkInfo = None
                    diskInfo = None
                    count = 0
                    reloadNum += 1;
                    if reloadNum > 1440:
                        reloadNum = 0;
                except Exception as ex:
                    print(str(ex))
            del(tmp)
            
            time.sleep(5);
            count +=1
    #except:
    #    time.sleep(30);
    #    systemTask();
            

#取内存使用率
def GetMemUsed():
    try:
        import psutil

        #取内存信息
        mem = psutil.virtual_memory()
        return mem.percent
    except:
        return 1;

            
#处理指定PHP版本   
def startPHPVersion(version):
    try:
        fpm = '/etc/init.d/php-fpm-'+version
        if not os.path.exists(fpm): return False;
        
        #尝试重载服务
        os.system(fpm + ' reload');
        if checkPHPVersion(version): return True;
        
        #尝试重启服务
        cgi = '/tmp/php-cgi-'+version
        pid = '/www/server/php'+version+'/php-fpm.pid';
        os.system('pkill -9 php-fpm-'+version)
        time.sleep(0.5);
        if not os.path.exists(cgi): os.system('rm -f ' + cgi);
        if not os.path.exists(pid): os.system('rm -f ' + pid);
        os.system(fpm + ' start');
        if checkPHPVersion(version): return True;
        
        #检查是否正确启动
        if os.path.exists(cgi): return True;
    except:
        return True;
    
    

#自动结束异常进程
def btkill():
    import btkill
    b = btkill.btkill()
    b.start();

#格式化时间
def get_local_time(now_time):
    import time
    time_array = time.strptime(now_time, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(time_array)
    return timestamp

#获取计划任务
def get_list():
    try:
        import json
        field = 'id,name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sName,sBody,sType,urladdress,pretime,nexttime'
        data = public.M('crontab').where("id>?",(0,)).field(field).select()
        if type(data) == str:
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'status' INTEGER DEFAULT 1",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save' INTEGER DEFAULT 3",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'backupTo' TEXT DEFAULT off",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sName' TEXT",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sBody' TEXT",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sType' TEXT",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'urladdress' TEXT",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'pretime' TEXT",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'nexttime' TEXT",())
            data = public.M('crontab').order("id desc").field(field).select()
        return data
    except :
        return []

#重启面板服务
def restart_panel_service():
    rtips = 'data/restart.pl'
    reload_tips = 'data/reload.pl'
    while True:
        if os.path.exists(rtips):
            os.remove(rtips)
            os.system("bt restart")
            os.system("del /s %s\class\*.pyc" % setup_path.replace('/','\\'))
        if os.path.exists(reload_tips):
            os.remove(reload_tips)
            os.system("bt reload")
            os.system("del /s %s\class\*.pyc" % setup_path.replace('/','\\'))
        time.sleep(1)

#处理线程
def process_thread():
    import time

    interval = 1
    total = 0

    global isCron
    try:
        data = get_list()
        import panelCrontab
        while(True):           
            try:
                #12小时重启一次 43200
                if total >= 43200: 
                    break

                if total == 0 or total % 60 == 0:     
                    data = get_list()
                    for item in data: 
                        panelCrontab.panelCrontab().process_fun(item)     
            except :
                pass                 
            time.sleep(interval)
            total += interval
    except :
        pass
    process_thread()  

class taskService(win32serviceutil.ServiceFramework): 
    #服务名 
    _svc_name_ = "btTask"
    #服务在windows系统中显示的名称 
    _svc_display_name_ = "btTask"
    #服务的描述 
    _svc_description_ = "用于运行宝塔Windows面板安装,计划任务等队列程序,停止后软件安装,计划任务等将无法执行."  

    def __init__(self, args): 
        win32serviceutil.ServiceFramework.__init__(self, args) 
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None) 
        self.run = True

    def SvcDoRun(self): 
        # 把自己的代码放到这里，就OK 
        path = os.getenv('BT_PANEL')
        import subprocess
        self.p = subprocess.Popen(['C:\Program Files\python\python.exe', path + '/task.py'])

        # 等待服务被停止 
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE) 
     
    def SvcStop(self): 
        os.system("taskkill /t /f /pid %s" % self.p.pid)
        # 先告诉SCM停止这个过程 
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING) 
        # 设置事件 
        win32event.SetEvent(self.hWaitStop)
        self.run = False


if __name__ == "__main__":
    path = os.getenv('BT_PANEL')
    if len(sys.argv) >= 2:
        if not path:            
            path = os.path.dirname(sys.argv[0])
            os.environ['BT_PANEL'] = path

            if not path:
                print('ERROR:安装失败，找不到环境变量【BT_PANEL】.')
                exit()    
        win32serviceutil.HandleCommandLine(taskService) 
    else:
        os.chdir(path)

        sys.path.insert(0,path + "/class/")
        import db,public,panelTask

        logPath = path + '/data/panelExec.log'
        isTask = path + '/data/panelTask.pl'
        isCron = path + '/data/panelCron.pl'

        import threading
        t = threading.Thread(target=systemTask)
        t.setDaemon(True)
        t.start()

        p = threading.Thread(target=process_thread)
        p.setDaemon(True)
        p.start()

        p = threading.Thread(target=restart_panel_service)
        p.setDaemon(True)
        p.start()

        task_obj = panelTask.bt_task()
        p = threading.Thread(target=task_obj.start_task)
        p.setDaemon(True)
        p.start()
        
        #p = threading.Thread(target=btkill)
        #p.setDaemon(True)
        #p.start()
    
        startTask()


