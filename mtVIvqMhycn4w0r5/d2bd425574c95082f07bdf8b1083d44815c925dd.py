#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Windows面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2018 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 曹觉心 <314866873@qq.com>
#-------------------------------------------------------------------

#------------------------------
# Apache管理模块
#------------------------------
import public,os,re,sys,shutil,math,psutil,time
panelPath = os.getenv('BT_PANEL')
os.chdir(panelPath)
sys.path.append("class/")

class apache:
    setupPath = os.getenv('BT_SETUP')
    apachedefaultfile = "%s/apache/conf/extra/httpd-default.conf" % (setupPath)
    apachempmfile = "%s/apache/conf/extra/httpd-mpm.conf" % (setupPath)

    def GetProcessCpuPercent(self,i,process_cpu):
        try:
            pp = psutil.Process(i)
            if pp.name() not in process_cpu.keys():
                process_cpu[pp.name()] = float(pp.cpu_percent(interval=0.1))
            process_cpu[pp.name()] += float(pp.cpu_percent(interval=0.1))
        except:
            pass

    def GetApacheStatus(self):
        process_cpu = {}

        if public.get_server_status('apache') <= 0: return public.returnMsg(False,"获取失败，服务未启动，通过以下方式排除错误：<br>1、检查80端口是否被占用<br>2、检查配置文件是否存在错误")    

        result = public.HttpGet('http://127.0.0.1/server-status?auto')
        workermen = 0
        for proc in psutil.process_iter():
            if proc.name() == "httpd.exe":
                workermen = proc.memory_info().rss
                self.GetProcessCpuPercent(proc.pid,process_cpu)
        time.sleep(0.5)

        tmp1 = re.search("ServerUptimeSeconds:\s+(.*)",result)
        if not tmp1: return public.returnMsg(False,"获取失败，请检查Apache服务是否通过宝塔面板安装的.")    
            
        data = {}
        # 计算启动时间
        Uptime = int(tmp1.group(1))
        min = Uptime / 60
        hours = min / 60
        days = math.floor(hours / 24)
        hours = math.floor(hours - (days * 24))
        min = math.floor(min - (days * 60 * 24) - (hours * 60))

        #格式化重启时间
        restarttime = re.search("RestartTime:\s+(.*)",result).group(1)
        rep = "\w+,\s([\w-]+)\s([\d\:]+)\s"
        date = re.search(rep,restarttime).group(1)
        timedetail = re.search(rep,restarttime).group(2)
        monthen = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        n = 0
        for m in monthen:
            if m in date:
                date = re.sub(m,str(n+1),date)
            n+=1
        date = date.split("-")
        date = "%s-%02d-%02d" % (date[2],int(date[1]),int(date[0]))

        reqpersec = re.search("ReqPerSec:\s+(.*)", result).group(1)
        if re.match("^\.", reqpersec):
            reqpersec = "%s%s" % (0,reqpersec)
        data["RestartTime"] = "%s %s" % (date,timedetail)
        data["UpTime"] = "%s天%s小时%s分钟" % (str(int(days)),str(int(hours)),str(int(min)))
        data["TotalAccesses"] = re.search("Total Accesses:\s+(\d+)",result).group(1)
        data["TotalKBytes"] = re.search("Total kBytes:\s+(\d+)",result).group(1)
        data["ReqPerSec"] = round(float(reqpersec), 2)
        data["BusyWorkers"] = re.search("BusyWorkers:\s+(\d+)",result).group(1)
        data["IdleWorkers"] = re.search("IdleWorkers:\s+(\d+)",result).group(1)
        data["workercpu"] = round(float(process_cpu["httpd.exe"] /psutil.cpu_count()),2)
        data["workermem"] = "%.2f%s" % ((float(workermen)/1024/1024),"MB")
        return data

    def GetApacheValue(self):
        if not os.path.exists(self.apachedefaultfile): return public.returnMsg(False,"获取失败，缺少配置文件,请检查Apache是否安装完整.")                
        if not os.path.exists(self.apachempmfile): return public.returnMsg(False,"获取失败，缺少配置文件,请检查Apache是否安装完整.")    

        apachedefaultcontent = public.readFile(self.apachedefaultfile)
        apachempmcontent = public.readFile(self.apachempmfile)

        ps = ["秒，请求超时时间","保持连接","秒，连接超时时间","单次连接最大请求数"]
        gets = ["Timeout","KeepAlive","KeepAliveTimeout","MaxKeepAliveRequests"]
        if public.get_webserver() == 'apache':
            shutil.copyfile(self.apachedefaultfile, 'data/apdefault_file_bk.conf')
            shutil.copyfile(self.apachempmfile, 'data/apmpm_file_bk.conf')
        conflist = []
        n = 0
        for i in gets:
            rep = "(%s)\s+(\w+)" % i

            k = re.search(rep, apachedefaultcontent).group(1)
            v = re.search(rep, apachedefaultcontent).group(2)
            psstr = ps[n]
            kv = {"name":k,"value":v,"ps":psstr}
            conflist.append(kv)
            n += 1

        ps = ["启动时默认进程数","最大进程数","最大连接数，0为无限大","最大并发进程数"]
        gets = ["StartServers","MaxSpareServers","MaxRequestsPerChild","MaxClients"]
        n = 0
        for i in gets:
            rep = "(%s)\s+(\w+)" % i
            
            k = re.search(rep, apachempmcontent).group(1)
            v = re.search(rep, apachempmcontent).group(2)
            psstr = ps[n]
            kv = {"name": k, "value": v, "ps": psstr}
            conflist.append(kv)
            n += 1
        return(conflist)

    def set_apache_config(self,get):
        
        httpdFile = "%s/apache/conf/httpd.conf" % (self.setupPath)
        if not os.path.exists(httpdFile): return False
            
        conf = public.readFile(httpdFile)
        dconf_list = ['#Include conf/extra/httpd-mpm.conf','#Include conf/extra/httpd-default.conf']
        for item in dconf_list:   
            if conf.find(item) >=0: conf = conf.replace(item,item.strip('#'))
        public.writeFile(httpdFile,conf)
        return True


    def SetApacheValue(self,get):

        if not self.set_apache_config(get): 
            return public.returnMsg(False, 'apache配置文件不存在，请检查是否正确安装.')

        apachedefaultcontent = public.readFile(self.apachedefaultfile)
        apachempmcontent = public.readFile(self.apachempmfile)
        conflist = []
        getdict = get.__dict__
        for i in getdict.keys():
            if i != "__module__" and i != "__doc__" and i != "data" and i != "args" and i != "action":
                getpost = {
                    "name": i,
                    "value": str(getdict[i])
                }
                conflist.append(getpost)
      
        public.writeFile("data/list",str(conflist))
        for c in conflist:
            if c["name"] == "KeepAlive":
                if not re.search("on|off", c["value"]):
                    return public.returnMsg(False, '参数值错误')
            else:               
                if not re.search("\d+", c["value"]):
                    return public.returnMsg(False, '参数值错误,请输入数字整数 %s %s' % (c["name"],c["value"]))

            rep = "%s\s+\w+" % c["name"]
            if re.search(rep,apachedefaultcontent):
                newconf = "%s %s" % (c["name"],c["value"])
                apachedefaultcontent = re.sub(rep,newconf,apachedefaultcontent)
            elif re.search(rep,apachempmcontent):
                newconf = "%s\t\t\t%s" % (c["name"], c["value"])
                apachempmcontent = re.sub(rep, newconf , apachempmcontent,count = 1)
        public.writeFile(self.apachedefaultfile,apachedefaultcontent)
        public.writeFile(self.apachempmfile, apachempmcontent)
        isError = public.checkWebConfig()
        if (isError != True):
            if os.path.exists('data/_file_bk.conf'): shutil.copyfile('data/_file_bk.conf', self.apachedefaultfile)
            if os.path.exists('data/proxyfile_bk.conf'): shutil.copyfile('data/proxyfile_bk.conf', self.apachempmfile)
            return public.returnMsg(False, 'ERROR: 配置出错<br><a style="color:red;">' + isError.replace("\n",'<br>') + '</a>')
        public.serviceReload()
        return public.returnMsg(True, '设置成功')
