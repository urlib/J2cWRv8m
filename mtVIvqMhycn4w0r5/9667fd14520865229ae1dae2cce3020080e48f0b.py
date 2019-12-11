 #coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------
from BTPanel import session,cache
import public,os,json,time,apache,iis
class ajax:
    def get_iis_status(self,get):
        return iis.iis().get_iis_status(get)
    
    def get_iis_request_list(self,get):
        return iis.iis().get_iis_request_list(get)

    #安装反向代理
    def setup_iis_proxy(self,get):
        a = iis.iis()
        return a.setup_iis_proxy(get)
    
    #获取反向代理安装状态
    def get_iis_proxy_config(self,get):
        a = iis.iis()
        return a.get_iis_proxy_config(get)
    
    #设置反向代理默认配置
    def set_iis_proxy_config(self,get):
        a = iis.iis()
        return a.set_iis_proxy_config(get)

    def set_iis_proxy_config(self,get):
        a = iis.iis()
        return a.set_iis_proxy_config(get)
    
    #mime类型
    def get_mimes(self,get):
        return iis.iis().get_mimes(get)

    #mime类型
    def add_mimes(self,get):
        return iis.iis().add_mimes(get)

    #mime类型
    def del_mimes(self,get):
        return iis.iis().del_mimes(get)

    def get_iis_request(self,get):
        try:
            import win32com,pythoncom
            try:
                import wmi            
            except :
                
                os.system(public.get_run_pip('[PIP] install wmi'))
                import wmi   
        
            pythoncom.CoInitialize()
            vim_obj = win32com.client.GetObject("winmgmts:/root/cimv2")        
            iiscon = vim_obj.ExecQuery('Select Name,TotalBytesReceived,TotalBytesSent,TotalBytesTransferred,TotalMethodRequests,TotalGetRequests,TotalPostRequests,CurrentConnections,MaximumConnections From Win32_PerfFormattedData_W3SVC_WebService where name="_Total"')
            data = {}
            for item in iiscon:
                data['TotalBytesReceived'] = item.TotalBytesReceived
                data['TotalBytesSent'] = item.TotalBytesSent
                data['TotalBytesTransferred'] = item.TotalBytesTransferred
                data['TotalMethodRequests'] = item.TotalMethodRequests
                data['TotalGetRequests'] = item.TotalGetRequests
                data['TotalPostRequests'] = item.TotalPostRequests
                data['CurrentConnections'] = item.CurrentConnections
                data['MaximumConnections'] = item.MaximumConnections

            return data
        except :
            return public.returnMsg(False,"获取IIS负载失败，请稍后重试。.")

    def GetApacheStatus(self,get):
        a = apache.apache()
        return a.GetApacheStatus()

    #cig管理器
    def get_nginx_cig_admin(self,get):
        ini_path = os.getenv("BT_SETUP") + '/nginx/config.ini'
        if not os.path.exists(ini_path):  return public.returnMsg(False,"配置文件不存在.")
        
        import re
        data = {}
        conf = public.readFile(ini_path);
        data['php_versions'] = re.search('php_versions\s?=(.+)',conf).groups()[0].strip();
        data['php_cgi_thread'] = re.search('php_cgi_thread\s?=(.+)',conf).groups()[0].strip();
        
        return data;

    def set_nginx_cig_admin(self,get):
        ini_path = os.getenv("BT_SETUP") + '/nginx/config.ini'
        if not os.path.exists(ini_path):  
            return public.returnMsg(False,"配置文件不存在.") 

        import re
        conf = public.readFile(ini_path)            
        conf = re.sub('php_versions\s?=.+','php_versions = ' + get.php_versions,conf);
        conf = re.sub('php_cgi_thread\s?=.+','php_cgi_thread = ' + get.php_cgi_thread,conf);
        public.writeFile(ini_path,conf)
        public.serviceReload();
        return public.returnMsg(True,"修改成功.") 

       
    def GetNginxStatus(self,get):
        #取Nginx负载状态
        worker = 0;
        workermen = 0
        if public.get_server_status('nginx') < 0: return public.returnMsg(False,"获取失败，服务未启动.") 

        result = public.HttpGet('http://127.0.0.1/nginx_status')
        tmp = result.split()
        if len(tmp) < 8: return  public.returnMsg(False,"获取失败，可能服务未启动，通过以下方式排除错误：<br>1、检查80端口是否被占用<br>2、检查配置文件是否存在错误")     
    
        data = {}
        if "request_time" in tmp:
            data['accepts']  = tmp[8]
            data['handled']  = tmp[9]
            data['requests'] = tmp[10]
            data['Reading']  = tmp[13]
            data['Writing']  = tmp[15]
            data['Waiting']  = tmp[17]
        else:
            data['accepts'] = tmp[9]
            data['handled'] = tmp[7]
            data['requests'] = tmp[8]
            data['Reading'] = tmp[11]
            data['Writing'] = tmp[13]
            data['Waiting'] = tmp[15]
        data['active'] = tmp[2]
        data['worker'] = worker

        return data
    
    def GetPHPStatus(self,get):
        #取指定PHP版本的负载状态
        return public.returnMsg(False,"暂不支持!") 
        
    def CheckStatusConf(self):
        return public.returnMsg(False,"暂不支持!") 
    
    
    def GetTaskCount(self,get):
        #取任务数量
        return public.M('tasks').where("status!=?",('1',)).count()
    
    def GetSoftList(self,get):
        #取软件列表
        import json,os
        tmp = public.readFile('data/softList.conf').replace("{SETUP_PATH}",public.format_path(os.getenv("BT_SETUP")));
        data = json.loads(tmp)
        for x in data['webs']:
            if x['name'] == 'IIS':
                x['versions'] = [{'status':False,'version':self.get_iis_verison()}]
        return data
    
    def get_iis_verison(self):
        import re
        sys_vs = public.get_sys_version()    
        if int(sys_vs[0]) == 6:
            version = '7.5'
            if int(sys_vs[1]) >= 2: 
                version = '8.5'  
                status = public.get_server_status('w3svc')  
                if status > -1:
                    version = public.ReadReg('SOFTWARE\\Microsoft\\InetStp','SetupString')
                    if version: 
                        version = re.search('(\d+\.\d+)',version).groups()[0]

        elif int(sys_vs[0]) == 10:
            version = '10.0'
        return version
    
    def GetLibList(self,get):
        #取插件列表
        import json,os
        tmp = public.readFile('data/libList.conf');
        data = json.loads(tmp)
        for i in range(len(data)):
            data[i]['status'] = self.CheckLibInstall(data[i]['check']);
            data[i]['optstr'] = self.GetLibOpt(data[i]['status'], data[i]['opt']);
        return data
    
    def CheckLibInstall(self,checks):
        for cFile in checks:
            if os.path.exists(cFile): return '已安装';
        return '未安装';
    
    #取插件操作选项
    def GetLibOpt(self,status,libName):
        optStr = '';
        if status == '未安装':
            optStr = '<a class="link" href="javascript:InstallLib(\''+libName+'\');">安装</a>';
        else:
            libConfig = '配置';
            if(libName == 'beta'): libConfig = '内测资料';
                                  
            optStr = '<a class="link" href="javascript:SetLibConfig(\''+libName+'\');">'+libConfig+'</a> | <a class="link" href="javascript:UninstallLib(\''+libName+'\');">卸载</a>';
        return optStr;
    
    #取插件AS
    def GetQiniuAS(self,get):
        filename = public.GetConfigValue('setup_path') + '/panel/data/'+get.name+'As.conf';
        if not os.path.exists(filename): public.writeFile(filename,'');
        data = {}
        data['AS'] = public.readFile(filename).split('|');
        data['info'] = self.GetLibInfo(get.name);
        if len(data['AS']) < 3:
            data['AS'] = ['','','',''];
        return data;


    #设置插件AS
    def SetQiniuAS(self,get):
        info = self.GetLibInfo(get.name);
        filename = public.GetConfigValue('setup_path') + '/panel/data/'+get.name+'As.conf';
        conf = get.access_key.strip() + '|' + get.secret_key.strip() + '|' + get.bucket_name.strip() + '|' + get.bucket_domain.strip();
        public.writeFile(filename,conf);
        public.ExecShell("chmod 600 " + filename)

        result = public.ExecShell(public.get_run_python("[PYTHON] " + public.GetConfigValue('setup_path') + "/panel/script/backup_"+get.name+".py list"))
        
        if result[0].find("ERROR:") == -1: 
            public.WriteLog("插件管理", "设置插件["+info['name']+"]AS!");
            return public.returnMsg(True, '设置成功!');
        return public.returnMsg(False, 'ERROR: 无法连接到'+info['name']+'服务器,请检查[AK/SK/存储空间]设置是否正确!');
    
    #设置内测
    def SetBeta(self,get):
        data = {}
        data['username'] = get.bbs_name
        data['qq'] = get.qq
        data['email'] = get.email
        result = public.httpPost(public.GetConfigValue('home') + '/Api/WindowsBeta',data);
        import json;
        data = json.loads(result);
        if data['status']:
            public.writeFile('data/beta.pl',get.bbs_name + '|' + get.qq + '|' + get.email);
        return data;
    #取内测资格状态
    def GetBetaStatus(self,get):
        try:
            return public.readFile('data/beta.pl').strip();
        except:
            return 'False';
               

    #获取指定插件信息
    def GetLibInfo(self,name):
        import json
        tmp = public.readFile('data/libList.conf');
        data = json.loads(tmp)
        for lib in data:
            if name == lib['opt']: return lib;
        return False;

    #获取文件列表
    def GetQiniuFileList(self,get):
        try:
            import json             
            
            result = public.ExecShell(public.get_run_python("[PYTHON] " + public.GetConfigValue('setup_path') + "/panel/script/backup_"+get.name+".py list"))
            return json.loads(result[0]);
        except:
            return public.returnMsg(False, '获取列表失败,请检查[AK/SK/存储空间]设是否正确!');

    
    
    #取网络连接列表
    def GetNetWorkList(self,get):
        import psutil
        netstats = psutil.net_connections()
        networkList = []
        for netstat in netstats:
            tmp = {}
            if netstat.type == 1:
                tmp['type'] = 'tcp'
            else:
                tmp['type'] = 'udp'
            tmp['family']   = netstat.family
            tmp['laddr']    = netstat.laddr
            tmp['raddr']    = netstat.raddr
            tmp['status']   = netstat.status
            p = psutil.Process(netstat.pid)
            tmp['process']  = p.name()
            tmp['pid']      = netstat.pid
            networkList.append(tmp)
            del(p)
            del(tmp)
        networkList = sorted(networkList, key=lambda x : x['status'], reverse=True);
        return networkList;
    
    #取进程列表
    def GetProcessList(self,get):
        import psutil,pwd
        Pids = psutil.pids();
        
        processList = []
        for pid in Pids:
            try:
                tmp = {}
                p = psutil.Process(pid);
                if p.exe() == "": continue;
                
                tmp['name'] = p.name();                             #进程名称
                if self.GoToProcess(tmp['name']): continue;
                
                
                tmp['pid'] = pid;                                   #进程标识
                tmp['status'] = p.status();                         #进程状态
                tmp['user'] = p.username();                         #执行用户
                cputimes = p.cpu_times()
                tmp['cpu_percent'] = p.cpu_percent(0.1);
                tmp['cpu_times'] = cputimes.user                             #进程占用的CPU时间
                tmp['memory_percent'] = round(p.memory_percent(),3)          #进程占用的内存比例
                pio = p.io_counters()
                tmp['io_write_bytes'] = pio.write_bytes             #进程总共写入字节数
                tmp['io_read_bytes'] = pio.read_bytes               #进程总共读取字节数
                tmp['threads'] = p.num_threads()                    #进程总线程数
                
                processList.append(tmp);
                del(p)
                del(tmp)
            except:
                continue;
        import operator
        processList = sorted(processList, key=lambda x : x['memory_percent'], reverse=True);
        processList = sorted(processList, key=lambda x : x['cpu_times'], reverse=True);
        return processList
    
    #结束指定进程
    def KillProcess(self,get):
        #return public.returnMsg(False,'演示服务器，禁止此操作!');
        import psutil
        p = psutil.Process(int(get.pid));
        name = p.name();
        if name == 'python': return public.returnMsg(False,'KILL_PROCESS_ERR');
        
        p.kill();
        public.WriteLog('TYPE_PROCESS','KILL_PROCESS',(get.pid,name));
        return public.returnMsg(True,'KILL_PROCESS',(get.pid,name));
    
    def GoToProcess(self,name):
        ps = ['sftp-server','login','nm-dispatcher','irqbalance','qmgr','wpa_supplicant','lvmetad','auditd','master','dbus-daemon','tapdisk','sshd','init','ksoftirqd','kworker','kmpathd','kmpath_handlerd','python','kdmflush','bioset','crond','kthreadd','migration','rcu_sched','kjournald','iptables','systemd','network','dhclient','systemd-journald','NetworkManager','systemd-logind','systemd-udevd','polkitd','tuned','rsyslogd']
        
        for key in ps:
            if key == name: return True
        
        return False
        
    
    def GetNetWorkIo(self,get):
        #取指定时间段的网络Io
        data =  public.M('network').dbfile('system').where("addtime>=? AND addtime<=?",(get.start,get.end)).field('id,up,down,total_up,total_down,down_packets,up_packets,addtime').order('id asc').select()
        return self.ToAddtime(data);
    
    def GetDiskIo(self,get):
        #取指定时间段的磁盘Io
        data = public.M('diskio').dbfile('system').where("addtime>=? AND addtime<=?",(get.start,get.end)).field('id,read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime').order('id asc').select()
        return self.ToAddtime(data);
    def GetCpuIo(self,get):
        #取指定时间段的CpuIo
        data = public.M('cpuio').dbfile('system').where("addtime>=? AND addtime<=?",(get.start,get.end)).field('id,pro,mem,addtime').order('id asc').select()

        return self.ToAddtime(data,True);
    
    def get_load_average(self,get):
        data = public.M('load_average').dbfile('system').where("addtime>=? AND addtime<=?",(get.start,get.end)).field('id,pro,one,five,fifteen,addtime').order('id asc').select()
        return self.ToAddtime(data);
    
    
    def ToAddtime(self,data,tomem = False):
        import time
        #格式化addtime列
        
        if tomem:
            import psutil
            mPre = (psutil.virtual_memory().total / 1024 / 1024) / 100
        length = len(data);
        he = 1;
        if length > 100: he = 1;
        if length > 1000: he = 3;
        if length > 10000: he = 15;
        if he == 1:
            for i in range(length):
                try:
                    data[i]['addtime'] = time.strftime('%m/%d %H:%M',time.localtime(float(data[i]['addtime'])))
                    if tomem and data[i]['mem'] > 100: data[i]['mem'] = data[i]['mem'] / mPre
                except : pass

            return data
        else:
            count = 0;
            tmp = []
            for value in data:
                if count < he: 
                    count += 1;
                    continue;
                value['addtime'] = time.strftime('%m/%d %H:%M',time.localtime(float(value['addtime'])))
                if tomem and value['mem'] > 100: value['mem'] = value['mem'] / mPre
                tmp.append(value);
                count = 0;
            return tmp;
        
    def GetInstalleds(self,softlist):
        softs = '';
        for soft in softlist['data']:
            try:
                for v in soft['versions']:
                    if v['status']: softs += soft['name'] + '-' + v['version'] + '|';
            except:
                pass
        return softs;
    
    #获取SSH爆破次数
    def get_ssh_intrusion(self):
       
        return 0;
    
    def UpdatePanel(self,get):
        #try:     
        #取回远程版本信息
        if 'updateInfo' in session and hasattr(get,'check') == False:
            updateInfo = session['updateInfo'];
        else:
            login_temp = 'data/login.temp';
            if os.path.exists(login_temp):
                logs = public.readFile(login_temp)
                os.remove(login_temp);
            else:
                logs = '';
            import psutil,panelPlugin,system;
            mem = psutil.virtual_memory();
            mplugin = panelPlugin.panelPlugin();
            mplugin.ROWS = 10000;
            panelsys = system.system();
            data = {}
            data['sites'] = str(public.M('sites').count());
            data['ftps'] = str(public.M('ftps').count());
            data['databases'] = str(public.M('databases').count());

            data['system'] = panelsys.GetSystemVersion() + '|' + str(mem.total / 1024 / 1024) + 'MB|' + public.getCpuType() + '*' + str(psutil.cpu_count()) + '|' + public.get_webserver() + '|' +session['version'];
            data['system'] += '||'+self.GetInstalleds(mplugin.getPluginList(None));
            data['logs'] = logs
            data['oem'] = ''
            data['intrusion'] = self.get_ssh_intrusion();
            msg = public.getMsg('PANEL_UPDATE_MSG');
            sUrl = public.GetConfigValue('home') + '/api/wpanel/updateWindows';
           
            updateInfo = json.loads(public.httpPost(sUrl,data));
          
            if not updateInfo: return public.returnMsg(False,"CONNECT_ERR");
            updateInfo['msg'] = msg;
            session['updateInfo'] = updateInfo;

        #检查是否需要升级
        if updateInfo['is_beta'] == 1:
            if updateInfo['beta']['version'] == session['version']: return public.returnMsg(False,updateInfo);
        else:
            if updateInfo['version'] == session['version']: return public.returnMsg(False,updateInfo);

        #是否执行升级程序 
        if(updateInfo['force'] == True or hasattr(get,'toUpdate') == True or os.path.exists('data/autoUpdate.pl') == True):
            if updateInfo['is_beta'] == 1: updateInfo['version'] = updateInfo['beta']['version']
            setupPath = public.GetConfigValue('setup_path');
            uptype = 'panel';
            httpUrl = public.get_url();
      
            if httpUrl: updateInfo['downUrl'] =  httpUrl + '/win/panel/' + uptype + '_' + updateInfo['version'] + '.zip';
         
            public.downloadFile(updateInfo['downUrl'],setupPath + '/panel.zip');
            if os.path.getsize(setupPath + '/panel.zip') < 1048576: return public.returnMsg(False,"PANEL_UPDATE_ERR_DOWN");            

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
                try:
                    zip_file.extract(names,tmpPath)      
                except : pass                
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
            panelPath = (setupPath+"/panel").replace("/","\\")
            os.system("xcopy /s /c /e /y /r %s %s" % (tmpPath,panelPath))
          
            session['version'] = updateInfo['version']
            if 'getCloudPlugin' in session: del(session['getCloudPlugin']);
            if updateInfo['is_beta'] == 1: self.to_beta()
            
            if os.path.exists(setupPath + '/panel.zip'):os.remove(setupPath + "/panel.zip")
            return public.returnMsg(True,'PANEL_UPDATE',(updateInfo['version'],));
            
        #输出新版本信息
        data = {
            'status' : True,
            'version': updateInfo['version'],
            'updateMsg' : updateInfo['updateMsg']
        };
            
        return public.returnMsg(True,updateInfo);
        #except Exception as ex:
        #    return public.returnMsg(False,"更新失败 --> " + str(ex));
         
    def to_beta(self):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            p_data = {}
            p_data['uid'] = userInfo['uid'];
            p_data['access_key'] = userInfo['access_key']
            p_data['username'] = userInfo['username']
            public.HttpPost(public.GetConfigValue('home') + '/api/wpanel/to_beta',p_data,5)
        except: pass

    #检查是否安装任何
    def CheckInstalled(self,get):
        checks = ['nginx','apache','W3SVC','FileZilla Server','mysql','MSSQLSERVER','phpmyadmin','php'];
        import os
        for name in checks:
            if name == 'phpmyadmin':
                filename = os.getenv("BT_SETUP") + '/' + name
                if os.path.exists(filename): return True;
            elif name == 'php':
                filename = os.getenv("BT_SETUP") + '/' + name
                if os.path.exists(filename): 
                    dirs = os.listdir(filename)
                    if len(dirs) > 0: return True;
            else:
                status = public.get_server_status(name)
                if status >= 0:
                    if name == 'W3SVC':
                        if os.path.exists('data/iis.setup'):
                            return True;
                    else:
                        return True;
        return False;
        
    #取已安装软件列表
    def GetInstalled(self,get):
        import system
        data = system.system().GetConcifInfo()
        return data;
    
    #取PHP配置
    def GetPHPConfig(self,get):
        import re,json
        
        filename = public.GetConfigValue('setup_path') + '/php/' + get.version + '/php.ini'
        if not os.path.exists(filename): return public.returnMsg(False,'PHP_NOT_EXISTS');
        phpini = public.readFile(filename);
  
        data = {}
        rep = "disable_functions\s*=\s{0,1}(.*)"
        tmp = re.search(rep,phpini).groups();
        data['disable_functions'] = tmp[0];
        
        rep = "upload_max_filesize\s*=\s*([0-9]+)(M|m|K|k)"
        tmp = re.search(rep,phpini).groups()
        data['max'] = tmp[0]
        
        rep = u"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
        tmp = re.search(rep,phpini).groups()
   
        if tmp[0] == '0':
            data['pathinfo'] = False
        else:
            data['pathinfo'] = True
        self.getCloudPHPExt(get)
        phplib = json.loads(public.readFile('data/phplib.win'));
        libs = [];
        tasks = public.M('tasks').where("status!=?",('1',)).field('status,name').select()
        for lib in phplib:
            lib['task'] = '1';
            for task in tasks:
                tmp = public.getStrBetween('[',']',task['name'])
                if not tmp:continue;
                tmp1 = tmp.split('-');
                if tmp1[0].lower() == lib['name'].lower():
                    lib['task'] = task['status'];
                    lib['phpversions'] = []
                    lib['phpversions'].append(tmp1[1])
            check_lib = re.search('\n+;?\w+.*' + lib['check'].replace('[version]',get.version) + '\s*',phpini)
            lib['status'] = False
            if check_lib:
                if check_lib.group().find(";") < 0:
                    lib['status'] = True                
                
            libs.append(lib)
        
        data['libs'] = libs;
        return data
       
    #获取当前下载节点
    def get_download_url(self):
        url = cache.get('download_url')
        if not url:
            cache.set('download_url',url,1800)
        return url

    #获取PHP扩展
    def getCloudPHPExt(self,get):
        import json
        try:
            if 'php_ext' in session: return True
         
            download_url = self.get_download_url() + '/install/lib/phplib.json'
            tstr = public.httpGet(download_url)
            data = json.loads(tstr);
            if not data: return False;
            public.writeFile('data/phplib.conf',json.dumps(data));
            session['php_ext'] = True
            return True;
        except:
            return False;
        
    #取PHPINFO信息
    def GetPHPInfo(self,get):
        version = get.version
        ext_path = os.getenv("BT_SETUP")  + '/php/' + version + '/php.exe'
        if os.path.exists(ext_path):
            rRet = public.ExecShell('%s -r "echo phpinfo();"' % ext_path,None,None,None,True)
            return public.returnMsg(True,rRet[0]);  
        return public.returnMsg(False,"请先安装PHP"+version); 
    
    #检测PHPINFO配置
    def CheckPHPINFO(self):
        php_versions = ['52','53','54','55','56','70','71','72','73','74','75'];
        return public.returnMsg(False,"暂不支持!") 
            
    
    #清理日志
    def delClose(self,get):
        public.M('logs').where('id>?',(0,)).delete();
        public.WriteLog('TYPE_CONFIG','LOG_CLOSE');
        return public.returnMsg(True,'LOG_CLOSE');
    
    #设置PHPMyAdmin
    def setPHPMyAdmin(self,get):
        if hasattr(get,'phpversion'):
            version = get.phpversion
            phpmyadmin_version = public.readFile(os.getenv("BT_SETUP") + '/phpmyadmin/version.pl')
            if phpmyadmin_version == '4.0' and (version != '53' and version != '54'):
                return public.returnMsg(False,'phpmyadmin 4.0经支持php5.3/5.4');   
            
            import panelSite
            get.siteName = 'phpmyadmin'
            get.version = version
            panelSite.panelSite().SetPHPVersion(get)

            return public.returnMsg(True,'修改phpmyadmin的php版本为[php-' + version + ']成功');
        elif hasattr(get,'port'): 
            import panelSite
            panel_site = panelSite.panelSite()

            get.siteName = 'phpmyadmin'
            try:
                phpVersion  = panel_site.GetSitePHPVersion(get)['phpversion']
            except :
                phpVersion = '00'
            
            port = get.port
     
            mainPort = public.readFile('data/port.pl').strip();
            rulePort = ['80','443','21','20','8080','8081','8089','11211','6379',mainPort]
            if port in rulePort:
                return public.returnMsg(False,'AJAX_PHPMYADMIN_PORT_ERR');

            #先删除，后添加
            webserver = public.GetWebServer()    
            if webserver == 'iis':
                _appcmd = os.getenv("SYSTEMDRIVE") + '\\Windows\\System32\\inetsrv\\appcmd.exe'
                public.ExecShell(_appcmd + ' delete site "phpmyadmin"')
                public.ExecShell(_appcmd + ' delete apppool "phpmyadmin"')
            elif webserver == 'apache': 
                confPath = panel_site.get_conf_path(get.siteName)
                if os.path.exists(confPath): os.remove(confPath)
            
            path = os.getenv("BT_SETUP") + '\\phpmyadmin\\' + public.readFile('data/phpmyadminDirName.pl')
           
            siteObj = { 'siteName' : 'phpmyadmin' ,'siteDomain': '' ,'sitePort': port,'sitePath':path ,'phpVersion':phpVersion,'type':'PHP' }
            if webserver == 'iis':                        
                result = panel_site.iisAdd(siteObj)
            elif webserver == 'apache':
                result = panel_site.apacheAdd(siteObj)
            print(result)
            #放行端口
            __version = public.get_sys_version()       
            ps = "phpmyadmin端口"
            if public.M('firewall').where("port=?",(port,)).count() <= 0:
                shell = 'netsh firewall set portopening tcp '+ port.replace(':','-') +' '+ ps
                if int(__version[0]) == 6:            
                    shell = 'netsh advfirewall firewall add rule name='+ ps +' dir=in action=allow protocol=tcp localport=' + port.replace(':','-')
                result = public.ExecShell(shell);
                public.WriteLog("TYPE_FIREWALL", 'FIREWALL_ACCEPT_PORT',(port,))
                addtime = time.strftime('%Y-%m-%d %X',time.localtime())
                public.M('firewall').add('port,ps,addtime',(port,ps,addtime))

            return public.returnMsg(True,'修改phpmyadmin的端口为[' + port + ']');
        elif hasattr(get,'status'):
            pass
        return public.returnMsg(False,"暂不支持!") 

    def ToPunycode(self,get):
        import re;
        get.domain = get.domain.encode('utf8');
        tmp = get.domain.split('.');
        newdomain = '';
        for dkey in tmp:
                #匹配非ascii字符
                match = re.search(u"[\x80-\xff]+",dkey);
                if not match:
                        newdomain += dkey + '.';
                else:
                        newdomain += 'xn--' + dkey.decode('utf-8').encode('punycode') + '.'

        return newdomain[0:-1];
    
    #保存PHP排序
    def phpSort(self,get):
        if public.writeFile(os.getenv("BT_SETUP") + '/php/sort.pl',get.ssort): return public.returnMsg(True,'SUCCESS');
        return public.returnMsg(False,'ERROR');
    
    #获取广告代码
    def GetAd(self,get):
        try:
            return public.HttpGet(public.GetConfigValue('home') + '/Api/GetAD?name='+get.name + '&soc=' + get.soc);
        except:
            return '';
        
    #获取进度
    def GetSpeed(self,get):
        return public.getSpeed();
    
    #检查登陆状态
    def CheckLogin(self,get):
        return True;
    
    #获取警告标识
    def GetWarning(self,get):
        warningFile = 'data/warning.json'
        if not os.path.exists(warningFile): return public.returnMsg(False,'警告列表不存在!');
        import json,time;
        wlist = json.loads(public.readFile(warningFile));
        wlist['time'] = int(time.time());
        return wlist;
    
    #设置警告标识
    def SetWarning(self,get):
        wlist = self.GetWarning(get);
        id = int(get.id);
        import time,json;
        for i in xrange(len(wlist['data'])):
            if wlist['data'][i]['id'] == id:
                wlist['data'][i]['ignore_count'] += 1;
                wlist['data'][i]['ignore_time'] = int(time.time());
        
        warningFile = 'data/warning.json'
        public.writeFile(warningFile,json.dumps(wlist));
        return public.returnMsg(True,'SET_SUCCESS');

    #获取memcached状态
    def GetMemcachedStatus(self,get):
        import telnetlib,re;
        config_path = public.GetConfigValue('setup_path') + '/memcached/config.json';
        conf = public.readFile(config_path);
        conf = json.loads(conf)

        bind = '127.0.0.1'
        array1 = conf['bind'].split(' ')
        if len(array1) >1: bind = array1[1]

        if public.get_server_status('memcached') <= 0: return public.returnMsg(False,"获取失败，服务未启动.") 

        port = 11211
        array2 = conf['port'].split(' ')
        if len(array1) >1: port = int(array2[1])

        tn = telnetlib.Telnet(bind,port);
        tn.write(b"stats\n");
        tn.write(b"quit\n");
        data = tn.read_all();
        if type(data) == bytes: data = data.decode('utf-8')

        data = data.replace('STAT','').replace('END','').split("\n");
        result = {}
        res = ['cmd_get','get_hits','get_misses','limit_maxbytes','curr_items','bytes','evictions','limit_maxbytes','bytes_written','bytes_read','curr_connections'];
        for d in data:
            if len(d)<3: continue;
            t = d.split();
            if not t[0] in res: continue;
            result[t[0]] = int(t[1]);
        result['hit'] = 1;
        if result['get_hits'] > 0 and result['cmd_get'] > 0:
            result['hit'] = float(result['get_hits']) / float(result['cmd_get']) * 100;
        
        conf = public.readFile(public.GetConfigValue('setup_path') + '/memcached/config.json');
        conf = json.loads(conf)
        for x in conf:
            result[x] = conf[x].split(' ')[1]
        return result;
    
    #设置memcached缓存大小
    def SetMemcachedCache(self,get):
        try:
            config_path = public.GetConfigValue('setup_path') + '/memcached/config.json';
            conf = public.readFile(config_path);
            conf = json.loads(conf)
            getdict = get.__dict__
            for i in getdict.keys():
                if i != "__module__" and i != "__doc__" and i != "data" and i != "args" and i != "action" and i != "s" and i != "name":
                    old_val = conf[i].split(' ')
                    if len(old_val) >1:
                        conf[i] = old_val[0] + ' ' + getdict[i]
            public.writeFile(config_path,json.dumps(conf))
      
            public.set_server_status('memcached','stop')               
            args = ''
            for x in conf:
                args += ' ' + conf[x]
            print( '%s -d runservice%s' % ('"' + public.GetConfigValue('setup_path')+'/memcached/memcached.exe"',args))
            public.WriteReg(r'SYSTEM\CurrentControlSet\services\memcached','ImagePath', '%s -d runservice%s' % ('"' + public.GetConfigValue('setup_path')+'/memcached/memcached.exe"',args))
            public.set_server_status('memcached','start')

            return public.returnMsg(True,"修改成功!") 
        except :
            return public.returnMsg(False,"修改失败!") 
    
    #申请内测版
    def apple_beta(self,get):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            p_data = {}
            p_data['uid'] = userInfo['uid'];
            p_data['access_key'] = userInfo['access_key']
            p_data['username'] = userInfo['username']
            result = public.HttpPost(public.GetConfigValue('home') + '/api/wpanel/apple_beta',p_data,5)
            try:
                return json.loads(result)
            except: return public.returnMsg(False,'AJAX_CONN_ERR')
        except: return public.returnMsg(False,'AJAX_USER_BINDING_ERR')

    #切回正式版
    def to_not_beta(self,get):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            p_data = {}
            p_data['uid'] = userInfo['uid'];
            p_data['access_key'] = userInfo['access_key']
            p_data['username'] = userInfo['username']
            result = public.HttpPost(public.GetConfigValue('home') + '/api/wpanel/to_not_beta',p_data,5)
            try:
                return json.loads(result)
            except: return public.returnMsg(False,'AJAX_CONN_ERR')
        except: return public.returnMsg(False,'AJAX_USER_BINDING_ERR')

    #升级测试版
    def to_beta(self):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            p_data = {}
            p_data['uid'] = userInfo['uid'];
            p_data['access_key'] = userInfo['access_key']
            p_data['username'] = userInfo['username']
            public.HttpPost(public.GetConfigValue('home') + '/api/wpanel/to_beta',p_data,5)
        except: pass

    #获取最新的5条测试版更新日志
    def get_beta_logs(self,get):
        try:
            data = json.loads(public.HttpGet(public.GetConfigValue('home') + '/api/wpanel/get_beta_logs'))
            return data
        except:
            return public.returnMsg(False,'AJAX_CONN_ERR')

    #取PHP-FPM日志
    def GetFpmLogs(self,get):
        return public.returnMsg(False,"暂不支持!") 
    
    #取PHP慢日志
    def GetFpmSlowLogs(self,get):
        return public.returnMsg(False,"暂不支持!") 
    
    #取指定日志
    def GetOpeLogs(self,get):
        if not os.path.exists(get.path): return public.returnMsg(False,'日志文件不存在!');
        return public.returnMsg(True,public.GetNumLines(get.path,1000));
    
        
        
        