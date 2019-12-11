#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

import psutil,time,os,public,re,shutil
from BTPanel import session,cache
class system:
    setupPath = None;
    ssh = None
    shell = None
    
    def __init__(self):
        self.setupPath = public.GetConfigValue('setup_path');
    
    def GetConcifInfo(self,get=None):
        #取环境配置信息
        if not 'config' in session:
            session['config'] = public.M('config').where("id=?",('1',)).field('webserver,sites_path,backup_path,status,mysql_root').find();
        if not 'email' in session['config']:
            session['config']['email'] = public.M('users').where("id=?",('1',)).getField('email');
        data = {}
        data = session['config']
        data['webserver'] = session['config']['webserver']
        #PHP版本
        phpVersions = ('52','53','54','55','56','70','71','72','73','74')
        
        data['php'] = []
        
        for version in phpVersions:
            tmp = {}
            tmp['setup'] = os.path.exists(self.setupPath + '/php/'+version+'/php.exe');
            if tmp['setup']:
                phpConfig = self.GetPHPConfig(version)
                tmp['version'] = version
                tmp['max'] = phpConfig['max']
                tmp['maxTime'] = phpConfig['maxTime']
                tmp['pathinfo'] = phpConfig['pathinfo']
                tmp['status'] = True
                data['php'].append(tmp)
            

        #mysql
        tmp = {'setup':False,'setup':False,'status':False,'version':''}
        server_status = public.get_server_status('mysql')
        if  server_status >= 0:
            tmp['setup'] = True
            tmp['version'] = re.search('([MySQL|MariaDB-]+\d+\.\d+)',public.get_server_path('mysql')).groups()[0] 
            if server_status > 0: tmp['status'] = True
        data['mysql'] = tmp

        #sqlserver
        tmp = {'setup':False,'setup':False,'status':False,'version':''}
        server_status = public.get_server_status('MSSQLSERVER')
        if  server_status >= 0:
            tmp['setup'] = True
            tmp['version'] = public.readFile(self.setupPath  + '/sqlserver/version.pl')
            if server_status > 0: tmp['status'] = True
        data['sqlserver'] = tmp

        tmp = {'setup':False,'setup':False,'status':False,'version':''}
        server_status = public.get_server_status('FileZilla Server')
        if  server_status >= 0:
            tmp['setup'] = True
            tmp['version'] = public.readFile(self.setupPath  + '/ftpServer/version.pl')
            if server_status > 0: tmp['status'] = True
        data['ftp'] = tmp


        data['status'] = True
        data['panel'] = self.GetPanelInfo()
        data['systemdate'] =time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
        return data
    
    def GetPanelInfo(self,get=None):
        #取面板配置
        address = public.GetLocalIp()
        try:
            port = public.GetHost(True)
        except:
            port = '8888';
        domain = ''
        if os.path.exists('data/domain.conf'):
           domain = public.readFile('data/domain.conf');
        
        autoUpdate = ''
        if os.path.exists('data/autoUpdate.pl'): autoUpdate = 'checked';
        limitip = ''
        if os.path.exists('data/limitip.conf'): limitip = public.readFile('data/limitip.conf');
        admin_path = '/'
        if os.path.exists('data/admin_path.pl'): admin_path = public.readFile('data/admin_path.pl').strip()
        
        templates = []
        #for template in os.listdir('BTPanel/templates/'):
        #    if os.path.isdir('templates/' + template): templates.append(template);
        template = public.GetConfigValue('template')
        
        check502 = '';
        if os.path.exists('data/502Task.pl'): check502 = 'checked';
        return {'port':port,'address':address,'domain':domain,'auto':autoUpdate,'502':check502,'limitip':limitip,'templates':templates,'template':template,'admin_path':admin_path}
    
    def GetPHPConfig(self,version):
        #取PHP配置
        file = self.setupPath + "/php/"+version+"/php.ini"
        phpini = public.readFile(file)
        data = {}
        try:
            rep = "upload_max_filesize\s*=\s*([0-9]+)M"
            tmp = re.search(rep,phpini).groups()
            data['max'] = tmp[0]
        except:
            data['max'] = '50'
       
        data['maxTime'] = 0
        
        try:
            rep = r"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
            tmp = re.search(rep,phpini).groups()            
            if tmp[0] == '1':
                data['pathinfo'] = True
            else:
                data['pathinfo'] = False
        except:
            data['pathinfo'] = False
        
        return data

    
    def GetSystemTotal(self,get,interval = 1):
        #取系统统计信息
        data = self.GetMemInfo();
        cpu = self.GetCpuInfo(interval);
        data['cpuNum'] = cpu[1];
        data['cpuRealUsed'] = cpu[0];
        data['time'] = self.GetBootTime();
        data['system'] = self.GetSystemVersion();
        data['isuser'] = public.M('users').where('username=?',('admin',)).count();
        data['version'] = session['version'];
        return data
    
    def GetLoadAverage(self,get):
        #c = os.getloadavg()
        data = {};
        data['one'] = 0;
        data['five'] = 0
        data['fifteen'] = 0
        data['max'] = psutil.cpu_count() * 2;
        data['limit'] = data['max'];
        data['safe'] = data['max'] * 0.75;
        return data;
    
    def GetAllInfo(self,get):
        data = {}
        data['load_average'] = self.GetLoadAverage(get);
        data['title'] = self.GetTitle();
        data['network'] = self.GetNetWorkApi(get);
        data['cpu'] = self.GetCpuInfo(1);
        data['time'] = self.GetBootTime();
        data['system'] = self.GetSystemVersion();
        data['mem'] = self.GetMemInfo();
        data['version'] = session['version'];
        return data;
    
    def GetTitle(self):
        return public.GetConfigValue('title')
    
    def get_registry_value(self, key, subkey, value):
        import winreg
        key = getattr(winreg, key)
        handle = winreg.OpenKey(key, subkey)
        (value, type) = winreg.QueryValueEx(handle, value)
        return value

    def GetSystemVersion(self):
        try:
            #取操作系统版本
            import public,platform
            bit = 'x86';
            if public.is_64bitos(): bit = 'x64'

            def get(key):
                return self.get_registry_value("HKEY_LOCAL_MACHINE", "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", key)
            os = get("ProductName")
            build = get("CurrentBuildNumber")

            version = "%s (build %s) %s" % (os, build,bit)
            return version
        except Exception as ex:
            public.WriteLog('获取系统版', '获取系统版本失败,注册表无法打开,错误详情 ->>' + str(ex));
            return '未知系统版本.'

    
    def GetBootTime(self):
        #取系统启动时间
        import public,math
        
        tStr = time.time() - psutil.boot_time()
        min = tStr / 60;
        hours = min / 60;
        days = math.floor(hours / 24);
        hours = math.floor(hours - (days * 24));
        min = math.floor(min - (days * 60 * 24) - (hours * 60));
        return public.getMsg('SYS_BOOT_TIME',(str(int(days)),str(int(hours)),str(int(min))))
    
    def GetCpuInfo(self,interval = 1):
        #取CPU信息
        cpuCount = psutil.cpu_count()
        used = psutil.cpu_percent()
        return used,cpuCount

    def get_process_cpu_time(self):
        pids = psutil.pids()
        cpu_time = 0.00;
        for pid in pids:
            try:
                cpu_times = psutil.Process(pid).cpu_times()
                for s in cpu_times: cpu_time += s
            except:continue;
        return cpu_time;

    def get_cpu_time(self):
        cpu_time = 0.00
        cpu_times = psutil.cpu_times()
        for s in cpu_times: cpu_time += s
        return cpu_time;
    
    def GetMemInfo(self,get=None):
        #取内存信息
        mem = psutil.virtual_memory()
        memInfo = {'memTotal':int(mem.total/1024/1024),'memFree':int(mem.free/1024/1024),'memRealUsed':int(mem.used/1024/1024)}

        return memInfo
    
    def GetDiskInfo(self,get=None):
       
        #取磁盘分区信息
        diskIo = psutil.disk_partitions();
        diskInfo = []
        for disk in diskIo: 
            try:
                tmp = {}
                tmp['path'] = disk.mountpoint.replace("\\","/")
                usage = psutil.disk_usage(disk.mountpoint)                
                tmp['size'] = [public.to_size(usage.total),public.to_size(usage.used),public.to_size(usage.free),str(usage.percent) + '%']
                tmp['inodes'] = False
                diskInfo.append(tmp)
            except :
                pass
       
        return diskInfo

    #清理系统垃圾
    def ClearSystem(self,get):
        count = total = 0;
        tmp_total,tmp_count = self.ClearMail();
        count += tmp_count;
        total += tmp_total;
        tmp_total,tmp_count = self.ClearOther();
        count += tmp_count;
        total += tmp_total;
        return count,total
    
    #清理邮件日志
    def ClearMail(self):
        rpath = '/var/spool';
        total = count = 0;
        import shutil
        con = ['cron','anacron','mail'];
        for d in os.listdir(rpath):
            if d in con: continue;
            dpath = rpath + '/' + d
            time.sleep(0.2);
            num = size = 0;
            for n in os.listdir(dpath):
                filename = dpath + '/' + n
                fsize = os.path.getsize(filename);
                size += fsize
                if os.path.isdir(filename):
                    shutil.rmtree(filename)
                else:
                    os.remove(filename)
                print('\t\033[1;32m[OK]\033[0m')
                num += 1
            total += size;
            count += num;
        return total,count
    
    #清理其它
    def ClearOther(self):
        clearPath = [
                     {'path':'/www/server/panel','find':'testDisk_'},
                     {'path':'/www/wwwlogs','find':'log'},
                     {'path':'/tmp','find':'panelBoot.pl'},
                     {'path':'/www/server/panel/install','find':'.rpm'}
                     ]
        
        total = count = 0;
        for c in clearPath:
            for d in os.listdir(c['path']):
                if d.find(c['find']) == -1: continue;
                filename = c['path'] + '/' + d;
                fsize = os.path.getsize(filename);
                total += fsize
                if os.path.isdir(filename):
                    shutil.rmtree(filename)
                else:
                    os.remove(filename)
                count += 1;
        public.serviceReload();
        filename = '/www/server/nginx/off'
        if os.path.exists(filename): os.remove(filename)
        os.system('echo > /tmp/panelBoot.pl');
        return total,count
    
    def GetNetWork(self,get=None):
        networkIo = [0,0,0,0]
        cache_timeout = 86400
        try:
            networkIo = psutil.net_io_counters()[:4]
        except :pass
       
        otime = cache.get("otime")
        if not otime:
            otime = time.time()
            cache.set('up',networkIo[0],cache_timeout)
            cache.set('down',networkIo[1],cache_timeout)
            cache.set('otime',otime ,cache_timeout)
            
        ntime = time.time();
        networkInfo = {}
        networkInfo['upTotal']   = networkIo[0]
        networkInfo['downTotal'] = networkIo[1]
        try:
            networkInfo['up']        = round(float(networkIo[0] -  cache.get("up")) / 1024 / (ntime - otime),2)
            networkInfo['down']      = round(float(networkIo[1] -  cache.get("down")) / 1024 / (ntime -  otime),2)
        except :
            networkInfo['up'] = 0
            networkInfo['down'] = 0
    
        networkInfo['downPackets'] =networkIo[3]
        networkInfo['upPackets']   =networkIo[2]
            
        cache.set('up',networkIo[0],cache_timeout)
        cache.set('down',networkIo[1],cache_timeout)
        cache.set('otime', time.time(),cache_timeout)
        if get != False:
            networkInfo['cpu'] = self.GetCpuInfo()
            networkInfo['load'] = self.GetLoadAverage(get);
            networkInfo['mem'] = self.GetMemInfo(get)
            networkInfo['disk'] = self.GetDiskInfo()
        return networkInfo
        
    
    def GetNetWorkApi(self,get=None):
        return self.GetNetWork()
    
    def GetNetWorkOld(self):
        #取网络流量信息
        import time;
        pnet = public.readFile('/proc/net/dev');
        rep = '([^\s]+):[\s]{0,}(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)';
        pnetall = re.findall(rep,pnet);
        networkInfo = {}
        networkInfo['upTotal'] = networkInfo['downTotal'] = networkInfo['up'] = networkInfo['down'] = networkInfo['downPackets'] = networkInfo['upPackets'] = 0;


        for pnetInfo in pnetall:
            if pnetInfo[0] == 'io': continue;
            networkInfo['downTotal'] += int(pnetInfo[1]);
            networkInfo['downPackets'] += int(pnetInfo[2]);
            networkInfo['upTotal'] += int(pnetInfo[9]);
            networkInfo['upPackets'] += int(pnetInfo[10]);

        cache_timeout = 86400
        otime = cache.get("otime")
        if not otime:
            otime = time.time()
            cache.set('up',networkInfo['upTotal'],cache_timeout)
            cache.set('down',networkInfo['downTotal'],cache_timeout)
            cache.set('otime',otime ,cache_timeout)

        ntime = time.time();
        tmpDown = networkInfo['downTotal'] - cache.get("down");
        tmpUp = networkInfo['upTotal'] - cache.get("up");
        networkInfo['down'] = str(round(float(tmpDown) / 1024 / (ntime - otime),2));
        networkInfo['up']   = str(round(float(tmpUp) / 1024 / (ntime - otime),2));
        if networkInfo['down'] < 0: networkInfo['down'] = 0;
        if networkInfo['up'] < 0: networkInfo['up'] = 0;
        
        otime = time.time()
        cache.set('up',networkInfo['upTotal'],cache_timeout)
        cache.set('down',networkInfo['downTotal'],cache_timeout)
        cache.set('otime',ntime ,cache_timeout)

        networkInfo['cpu'] = self.GetCpuInfo()
        return networkInfo;


    #取IO读写信息
    def get_io_info(self,get = None):
        io_disk = psutil.disk_io_counters()
        ioTotal = {}
        ioTotal['write'] = self.get_io_write(io_disk.write_bytes)
        ioTotal['read'] = self.get_io_read(io_disk.read_bytes)
        return ioTotal

    #取IO写
    def get_io_write(self,io_write):
        disk_io_write = 0
        old_io_write = cache.get('io_write')
        if not old_io_write:
            cache.set('io_write',io_write)
            return disk_io_write;

        old_io_time = cache.get('io_time')
        new_io_time = time.time()
        if not old_io_time: old_io_time = new_io_time
        io_end = (io_write - old_io_write)
        time_end = (time.time() - old_io_time)
        if io_end > 0:
            if time_end < 1: time_end = 1;
            disk_io_write = io_end / time_end;
        cache.set('io_write',io_write)
        cache.set('io_time',new_io_time)
        if disk_io_write > 0: return int(disk_io_write)
        return 0

    #取IO读
    def get_io_read(self,io_read):
        disk_io_read = 0
        old_io_read = cache.get('io_read')
        if not old_io_read:
            cache.set('io_read',io_read)
            return disk_io_read;
        old_io_time = cache.get('io_time')
        new_io_time = time.time()
        if not old_io_time: old_io_time = new_io_time
        io_end = (io_read - old_io_read)
        time_end = (time.time() - old_io_time)
        if io_end > 0:
            if time_end < 1: time_end = 1;
            disk_io_read = io_end / time_end;
        cache.set('io_read',io_read)
        if disk_io_read > 0: return int(disk_io_read)
        return 0
    
    def ServiceAdmin(self,get=None):
        #服务管理        
        if get.name == 'mysqld': 
            get.name = 'mysql'           
        if get.name.find("php-") >=0:
            get.name = public.get_webserver();

        if get.name == 'iis': get.name = 'W3SVC'
        if get.name == "ftpserver": get.name = 'FileZilla Server'            
        if get.name == 'sqlserver':  get.name = 'MSSQLSERVER'

        if get.name == 'phpmyadmin':
            import ajax
            get.status = 'True';
            ajax.ajax().setPHPMyAdmin(get);
            return public.returnMsg(True,'SYS_EXEC_SUCCESS');
     
        if get.name == 'apache' or get.name == 'nginx':
      
            isError = public.checkWebConfig()            
            if isError != True:
                return public.returnMsg(False,'配置文件错误，错误详情：' + isError);

        public.set_server_status(get.name,get.type) 

        #查询执行结果
        status = public.get_server_status(get.name)

        if get.type == 'start' or get.type == 'restart':
            if status == 1:
                return public.returnMsg(True,'SYS_EXEC_SUCCESS');
            else:
                errors = public.server_err
                if errors:
                    if errors['code'] == 1455:
                        return public.returnMsg(False,'启动失败，系统内存不足，无法启动.');
                    elif errors['code'] == 1058:
                        return public.returnMsg(False,'启动失败，服务已被禁用，请重启面板或者服务器解除占用.');
                    elif errors['code'] == 1069:
                        return public.returnMsg(False,'启动失败，登录失败，请检查服务启动用户的密码是否正确.');
                    else:
                        return public.returnMsg(False,'启动失败，请检查启动配置文件是否配置正确.');
                 
                    
        return public.returnMsg(True,'SYS_EXEC_SUCCESS');

    def RestartServer(self,get):
        if not public.IsRestart(): return public.returnMsg(False,'EXEC_ERR_TASK');
        try:
            os.system("shutdown /r /f /t 0");
        except :pass
        
        return public.returnMsg(True,'SYS_REBOOT');

    #释放内存
    def ReMemory(self,get):
        os.system("BtTools clear_memory")
        return self.GetMemInfo();
    
    #重启面板     
    def ReWeb(self,get): 
        public.set_server_status("btTask","restart");
        public.writeFile('data/reload.pl','True')

        return public.returnMsg(True,'面板已重启')

    def connect_ssh(self):
        import paramiko
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect('127.0.0.1', public.GetSSHPort())
        except:
            if public.GetSSHStatus():
                try:
                    self.ssh.connect('localhost', public.GetSSHPort())
                except:
                    return False;
            import firewalls,common
            fw = firewalls.firewalls()
            get = common.dict_obj()
            get.status = '0';
            fw.SetSshStatus(get)
            self.ssh.connect('127.0.0.1', public.GetSSHPort())
            get.status = '1';
            fw.SetSshStatus(get);
        self.shell = self.ssh.invoke_shell(term='xterm', width=100, height=29)
        self.shell.setblocking(0)
        return True
    
    #修复面板
    def RepPanel(self,get):    
        try:
            downUrl = 'http://download.bt.cn' + '/win/panel/panel_' + session['version'] + '.zip'
            httpUrl = public.get_url();
            if httpUrl: downUrl =  httpUrl + '/win/panel/panel_' + session['version'] + '.zip';
        
            setupPath = public.GetConfigValue('setup_path');

            public.downloadFile(downUrl,setupPath + '/panel.zip');
            if os.path.getsize(setupPath + '/panel.zip') < 1048576: return public.returnMsg(False,"PANEL_UPDATE_ERR_DOWN");
        except :
            return public.returnMsg(False,"修复失败，无法连接到下载节点.");
        
        #处理临时文件目录   
        tmpPath = (setupPath + "/temp/panel")
        tcPath = (tmpPath + '\class').replace('/','\\')

        if not os.path.exists(tmpPath): os.makedirs(tmpPath)
        import shutil
        if os.path.exists(tcPath): shutil.rmtree(tcPath)

        #解压到临时目录
        import zipfile
        zip_file = zipfile.ZipFile(setupPath + '/panel.zip')  
        for names in zip_file.namelist():              
            zip_file.extract(names,tmpPath)            
        zip_file.close()
        time.sleep(0.2);

        for name in os.listdir(tcPath): 
            try:
                if name.find('cp36-win_amd64.pyd') >=0:
                    oldName = os.path.join(tcPath,name);
                    newName = os.path.join(tcPath,name.replace('.cp36-win_amd64.pyd','.pyd'))

                    if not os.path.exists(newName):os.rename(oldName,newName)
            except :pass
        
        #过滤文件
        file_list = ['config/config.json','config/index.json','data/libList.conf','data/plugin.json']
        for ff_path in file_list:
            if os.path.exists(tmpPath + '/' + ff_path): os.remove(tmpPath + '/' + ff_path)  

        os.system("taskkill /im BtTools.exe /f")    

        #兼容不同版本工具箱
        toolPath = tmpPath + '/script/BtTools.exe'
        if os.path.exists(toolPath):
            os.remove(toolPath)
            netV = ''
            if os.path.exists('data/net'): netV = public.readFile('data/net')                
            public.downloadFile(httpUrl + '/win/panel/BtTools' + netV + '.exe',toolPath);

        #处理面板程序目录文件
        pPath = setupPath + '/panel' 
        cPath = (pPath + '/class').replace('/','\\')
        os.system("del /s %s\*.pyc" % cPath)
        os.system("del /s %s\*.pyt" % cPath)
        for name in os.listdir(cPath):
            try:
                if name.find('.pyd') >=0: os.rename(os.path.join(cPath,name),os.path.join(cPath,name.replace('.pyd','.pyt'))) 
            except : pass      

        tmpPath = tmpPath.replace("/","\\")
        panelPath = (setupPath + "/panel").replace("/","\\")
        os.system("xcopy /s /c /e /y /r %s %s" % (tmpPath,panelPath))

        self.ReWeb(None)
        return public.returnMsg(True,"修复成功");
