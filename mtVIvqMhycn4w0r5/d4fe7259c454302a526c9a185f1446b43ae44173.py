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

class iis:
    setupPath = os.getenv('BT_SETUP')
    def __init__(self):
        self._iis_root = os.getenv("SYSTEMDRIVE") + '\\Windows\\System32\\inetsrv'
        self._appcmd = self._iis_root + '\\appcmd.exe'            

    def GetProcessCpuPercent(self,i,process_cpu):
        try:
            pp = psutil.Process(i)
            if pp.name() not in process_cpu.keys():
                process_cpu[pp.name()] = float(pp.cpu_percent(interval=0.1))
            process_cpu[pp.name()] += float(pp.cpu_percent(interval=0.1))
        except:
            pass

    def get_iis_status(self,get):
        lRet = public.ExecShell(self._appcmd + ' list wp',None,None,None,True)
        temp = re.findall("WP\s\"(\d+)\"\s+\(applicationPool:(.+)\)",lRet[0])
        data = {}
        data['total_memory'] = 0
        data['total_cpu'] = 0
        data['total_request'] = 0
        data['apps'] = []
        for val in temp:            
            p = psutil.Process(int(val[0]))
            cpu = round(float(p.cpu_percent(interval=0.1) / psutil.cpu_count()),2)            
            memory = p.memory_info().peak_pagefile / 1024;           

            rRet = public.ExecShell(self._appcmd + ' list request /wp.name:"' + val[0] + '"',None,None,None,True)
            tmp2 = re.findall("REQUEST.*\(url:(.+),\s+time:(\d+).+?,\s+client:(.+),\s+stage:(.+),\s+module:(.+)\)",rRet[0])

            request = len(tmp2);
            data['apps'].append({'name':val[1],'pid':val[0],'cpu':cpu ,'memory':memory,'request':request })

            data['total_memory'] += memory
            data['total_cpu'] += cpu
            data['total_request'] += request

        print(data)
        return data

    #获取请求详情
    def get_iis_request_list(self,get):
        pid = get.pid
        
        rRet = public.ExecShell(self._appcmd + ' list request /wp.name:"' + pid + '"',None,None,None,True)
        tmp2 = re.findall("REQUEST.*\(url:(.+),\s+time:(\d+).+?,\s+client:(.+),\s+stage:(.+),\s+module:(.+)\)",rRet[0])
        
        req_list = []
        for item in tmp2:
            arrs = item[0].split(' ')
            req_list.append({ 'method':arrs[0],'url':arrs[1],'time':item[1],'client':item[2],'stage':item[3],'module':item[4] })

        return  req_list


    #安装IIS反向代理
    def setup_iis_proxy(self,get):
        downUrl = public.get_url()
        tmpPath = self.setupPath + '/temp/requestRouter.msi'
        public.downloadFile(downUrl + '/win/panel/data/requestRouter_x64.msi',tmpPath)
        if os.path.exists(tmpPath):
            os.system(tmpPath + ' /qb')
        return public.returnMsg(True,'安装反向代理扩展成功！');  

    #获取反向代理配置信息
    def get_iis_proxy_config(self,get):       
        lRet = public.ExecShell(self._appcmd + ' list config /section:proxy /config:*')
        if lRet[0].find('ERROR') >=0:  
            return public.returnMsg(False,'反向代理扩展未安装.'); 
 
        gets = [
            {'name':'enabled','type':1,'ps': '反向代理启用状态'},
            {'name':'httpVersion','type':3,'ps':'HTTP协议版本。'},
            {'name':'keepAlive','type':1,'ps':'使用HTTP keep-alive'},
            {'name':'timeout','type':5,'ps':'超时时间(以秒为单位)'},
            {'name':'reverseRewriteHostInResponseHeaders','type':1,'ps':'重写主机头'},
            {'name':'xForwardedForHeaderName','type':2,'ps':'保留客户端IP地址'},
            {'name':'includePortInXForwardedFor','type':1,'ps':'保留IP地址中的TCP端口。'},
            {'name':'minResponseBuffer','type':2,'ps':'可以缓存内容最小阈值(KB)'},
            {'name':'maxResponseHeaderSize','type':2,'ps':'可以缓存内容最大阈值(KB)'},
            {'name':'proxy','type':2,'ps':'代理服务器，不懂留空'},
            {'name':'proxyBypass','type':2,'ps':'代理服务器密码，不懂留空'},
            {'name':'cache_enabled','type':1,'ps': '开启缓存'},
            {'name':'cache_validationInterval','type':5,'ps': '缓存时间(以秒为单位，最大86400)'},
        ]

        result = []
        for g in gets:
            if g['name'].find('_') >= 0:
                t1,t2 = g['name'].split('_')
                rep =  t1 + '.+'+ t2 +'="(.+?)"';
                tmp = re.search(rep,lRet[0]) 
            else:
                rep =  'proxy.+'+g['name']+'="(.+?)"';
                tmp = re.search(rep,lRet[0])   
            if not tmp: continue;
            g['value'] = tmp.groups()[0];
            if g['type'] == 5:
                g['value'] = public.time_to_int(g['value'])
            result.append(g);
        
        return result;

    #修改反向代理默认配置
    def set_iis_proxy_config(self,get):
        gets = ['enabled','httpVersion','keepAlive','timeout','reverseRewriteHostInResponseHeaders','xForwardedForHeaderName','includePortInXForwardedFor','minResponseBuffer','maxResponseHeaderSize','proxy','proxyBypass','cache_enabled','cache_validationInterval']
        shell = self._appcmd + ' set config /section:proxy'
        ttyps = ['cache_validationInterval','timeout']
        for key in gets:
            name = key           
            if key.find('_') >=0:
                a1,a2 = key.split('_')
                name = '%s.%s' % (a1,a2)
            val = get[key]
            if key in ttyps: val = public.int_to_time(int(val))
            shell =  shell + ' /' + name + ':' + val
        shell = shell + ' /commit:apphost'
        lRet = public.ExecShell(shell)
        if lRet[0].find('APPHOST') >=0:
            return public.returnMsg(True,'修改IIS反向代理配置成功！'); 
        return public.returnMsg(False,'修改IIS反向代理配置失败.'); 

    #获取iis下mime列表
    def get_mimes(self,get):
        import xmltodict
        try:
            out = public.ExecShell(self._appcmd + " list config -section:staticContent",None,None,None,True)     
            data = xmltodict.parse(out)
            result = [];     
            for x in data["system.webServer"]["staticContent"]["mimeMap"]:
                sdata = {}
                sdata['name'] = x['@fileExtension']
                sdata['type'] = x['@mimeType']
                result.insert(0,sdata)

            return result
        except :
            return []


    #添加mime类型
    def add_mimes(self,get):
        name = get.name.strip()
        type = get.type.strip()
        if not name or not type:
            return public.returnMsg(False,'参数传递错误！');

        list = self.get_mimes(get)
        for x in list:
            if x['name'] == name:
                return public.returnMsg(False,'请勿重复添加！')

        public.ExecShell(self._appcmd + " set config /section:staticContent /+[fileExtension='" + name + "',mimeType='" + type + "']")
        return public.returnMsg(True,'添加MIME类型成功！')
            
    #添加mime类型
    def del_mimes(self,get):
        name = get.name.strip()
        type = get.type.strip()
        if not name or not type:
            return public.returnMsg(False,'参数传递错误！');

        public.ExecShell(self._appcmd + " set config /section:staticContent /-[fileExtension='" + name + "',mimeType='" + type + "']")
        return public.returnMsg(True,'删除MIME类型成功！')