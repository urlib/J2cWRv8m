#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

import sys,os,public,re,time
from BTPanel import session,cache
class firewalls:
    __version = [];
    def __init__(self):
        self.__version = public.get_sys_version()       
      
        if not cache.get('firewall_init'):
            self.firewall_init();     
        
    
    #获取服务端列表
    def GetList(self):
        try:
            data = {}
            data['ports'] = self.__Obj.GetAcceptPortList();
            addtime = time.strftime('%Y-%m-%d %X',time.localtime())
            for i in range(len(data['ports'])):
                tmp = self.CheckDbExists(data['ports'][i]['port']);
                if not tmp: public.M('firewall').add('port,ps,addtime',(data['ports'][i]['port'],'',addtime))
                          
            data['iplist'] = self.__Obj.GetDropAddressList();
            for i in range(len(data['iplist'])):
                try:
                    tmp = self.CheckDbExists(data['iplist'][i]['address']);
                    if not tmp: public.M('firewall').add('port,ps,addtime',(data['iplist'][i]['address'],'',addtime))
                except:
                    pass
        except:
            pass
    
    #检查数据库是否存在
    def CheckDbExists(self,port):
        data = public.M('firewall').field('id,port,ps,addtime').select();
        for dt in data:
            if dt['port'] == port: return dt;
        return False;
        

    #添加屏蔽IP
    def AddDropAddress(self,get):
        import time
        import re
        rep = "^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$"
        if not re.search(rep,get.port): return public.returnMsg(False,'FIREWALL_IP_FORMAT');
        address = get.port
        if public.M('firewall').where("port=?",(address,)).count() > 0: return public.returnMsg(False,'FIREWALL_IP_EXISTS')
        public.ExecShell("netsh ipsec static add filter filterlist=IpList srcaddr=" + address + " srcport=0 dstaddr=me dstport=0 protocol=ANY mirrored=no description=\"" + get.ps + "\"")

        public.WriteLog("TYPE_FIREWALL", 'FIREWALL_DROP_IP',(address,))
        addtime = time.strftime('%Y-%m-%d %X',time.localtime())
        public.M('firewall').add('port,ps,addtime',(address,get.ps,addtime))
        return public.returnMsg(True,'ADD_SUCCESS')
    
    
    #删除IP屏蔽
    def DelDropAddress(self,get):
        address = get.port
        id = get.id      
        public.ExecShell("netsh ipsec static delete filter filterlist=IpList srcaddr=" + address + " srcport=0 dstaddr=me dstport=0 protocol=any mirrored=no");
       
        public.WriteLog("TYPE_FIREWALL",'FIREWALL_ACCEPT_IP',(address,))
        public.M('firewall').where("id=?",(id,)).delete()
        return public.returnMsg(True,'DEL_SUCCESS')
    
    
    #添加放行端口
    def AddAcceptPort(self,get):
        import re
        rep = "^\d{1,5}(:\d{1,5})?$"
        if not re.search(rep,get.port): return public.returnMsg(False,'PORT_CHECK_RANGE');
        import time
        port = get.port
        ps = get.ps
        if public.M('firewall').where("port=?",(port,)).count() > 0: return public.returnMsg(False,'FIREWALL_PORT_EXISTS')
        notudps = ['80','443','8888','888','39000:40000','21','22']
        shell = 'netsh firewall set portopening tcp '+ port.replace(':','-') +' '+ ps
        if int(self.__version[0]) == 6:            
            shell = 'netsh advfirewall firewall add rule name='+ps+' dir=in action=allow protocol=tcp localport=' + port.replace(':','-')
  
        result = public.ExecShell(shell);
        public.WriteLog("TYPE_FIREWALL", 'FIREWALL_ACCEPT_PORT',(port,))
        addtime = time.strftime('%Y-%m-%d %X',time.localtime())
        public.M('firewall').add('port,ps,addtime',(port,ps,addtime))
        
        return public.returnMsg(True,'ADD_SUCCESS')
    
    
    #删除放行端口
    def DelAcceptPort(self,get):
        if not hasattr(get, 'port'): return public.returnMsg(False,'缺少必要参数.')
        port = get.port
        id = get.id
        try:      
            public.WriteLog("TYPE_FIREWALL", 'FIREWALL_DROP_PORT',(port,))
            public.M('firewall').where("id=?",(id,)).delete()           
            shell = "netsh firewall delete portopening protocol=tcp port=" +  port.replace(':','-')
            if int(self.__version[0]) == 6:
                shell = "netsh advfirewall firewall delete rule name=all protocol=tcp localport=" +  port.replace(':','-')      
            result = public.ExecShell(shell);
            public.WriteLog("TYPE_FIREWALL", 'FIREWALL_DROP_PORT',(port,))

            public.M('firewall').where("id=?",(id,)).delete()
            return public.returnMsg(True,'DEL_SUCCESS')
        except:
            return public.returnMsg(False,'DEL_ERROR')

       
    #取SSH信息
    def GetSshInfo(self,get):
        # ssh状态 1：关闭 0：开启
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE ,r"SYSTEM\CurrentControlSet\Control\Terminal Server\Wds\rdpwd\Tds\tcp")
            port,type = winreg.QueryValueEx(key, "PortNumber")
        except :
            port = 3389

        keys = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE ,r"SYSTEM\CurrentControlSet\Control\Terminal Server")
        status,type = winreg.QueryValueEx(keys, "fDenyTSConnections")
  
        if int(status) == 1:
           status = False
        else:
           status = True
        ping = True;
        if os.path.exists("data/ping.pl"): ping = False
        data = { "ping":ping,"status":status,"port":port }

        return data
    
    #设置远程端口状态
    def SetSshStatus(self,get):
        status = int(get['status'])
        if int(status) == 1:
            if os.path.exists('data/close.pl'):
                return public.returnMsg(False,'请勿同时关闭远程桌面和面板！')
            msg = public.getMsg('FIREWALL_SSH_STOP')
        else:
            msg = public.getMsg('FIREWALL_SSH_START')

        for x in [0,1,2,3,4,5,6,7,8,9,10]:
            public.ExecShell("ECHO Y|logoff " + str(x))

        public.WriteReg(r'SYSTEM\CurrentControlSet\Control\Terminal Server','fDenyTSConnections',status)
        public.WriteLog("TYPE_FIREWALL", msg)
        return public.returnMsg(True,'SUCCESS')

    
    #设置ping
    def SetPing(self,get):
        path = 'data/ping.pl'
        if get.status == '1':
            if int(self.__version[0]) == 6:
                public.ExecShell('netsh advfirewall firewall delete rule name="禁PING"')
            public.ExecShell("netsh firewall set service fileandprint enable")
            public.ExecShell('netsh ipsec static delete rule name =禁止PING Policy = "宝塔IP安全策略"')
            public.ExecShell('netsh ipsec static delete filterlist name =PortList');
            if os.path.exists(path): os.remove(path)
        
            return public.returnMsg(True,'解除禁PING成功！')
        else:
             result = public.ExecShell('Netsh ipsec static show filterlist name=PortList')
             if result[0].find('ERR')!=-1:
                public.ExecShell("Netsh ipsec static add filteraction name = 阻止 action =block")
                public.ExecShell('Netsh ipsec static add filter filterlist=PortList srcaddr=122.226.158.132 srcport=0 dstaddr=me dstport=0 protocol=ANY mirrored=no description="初始化"')
             public.ExecShell("netsh ipsec static add rule name =禁止PING Policy = 宝塔IP安全策略 filterlist =PortList filteraction = 阻止")
             public.ExecShell("netsh ipsec static add filter filterlist=PortList srcaddr=any dstaddr=me protocol=icmp  description=禁止PING mirrored=yes")
             public.writeFile(path,'True')
             return public.returnMsg(True,'禁PING成功！')
        return public.returnMsg(True,'SUCCESS') 
        
    
    
    #改远程端口
    def SetSshPort(self,get):
        port = get.port
        if not public.checkPort(port): return public.returnMsg(False,'FIREWALL_SSH_PORT_ERR');

        ports = ['21','25','80','443','8080','888','8888'];
        if port in ports: return public.returnMsg(False,'');

        for x in [0,1,2,3,4,5,6,7,8,9,10]:
            public.ExecShell("ECHO Y|logoff " + str(x))
        regPath = r'SYSTEM\CurrentControlSet\Control\Terminal Server';
        public.WriteReg(regPath,'fDenyTSConnections',1)
        public.WriteReg(r"SYSTEM\CurrentControlSet\Control\Terminal Server\Wds\rdpwd\Tds\tcp",'PortNumber',int(port))
        public.WriteReg(r'SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp','PortNumber',int(port))
        time.sleep(0.2)
        public.WriteReg(regPath,'fDenyTSConnections',0)
        
        old_port = public.M('firewall').where("ps=?",('远程桌面管理服务',)).getField('port')
        if old_port != port:            
            public.M('firewall').where("ps=?",('远程桌面管理服务',)).delete()
            get['ps'] = "远程桌面管理服务"
            self.AddAcceptPort(get)
        
        public.WriteLog("TYPE_FIREWALL", "FIREWALL_SSH_PORT",(port,))
        return public.returnMsg(True,'EDIT_SUCCESS') 

        
        
    #初始化IP安全策略
    def firewall_init(self):
        public.ExecShell('Netsh ipsec static add policy name =宝塔IP安全策略 description="用于过滤IP,禁PING,请不要删除"')       
        result = public.ExecShell("Netsh ipsec static show filterlist name=IpList")
        if result[0].find('ERR')!=-1:
            public.ExecShell("Netsh ipsec static add filteraction name = 阻止IP访问 action =block")
            public.ExecShell('Netsh ipsec static add filterlist name=IpList description="禁止列表内的IP访问这台服务器"')
            public.ExecShell('Netsh ipsec static add filter filterlist=IpList srcaddr=122.226.158.132 srcport=0 dstaddr=me dstport=0 protocol=ANY mirrored=no description="初始化"')
        public.ExecShell("netsh ipsec static add rule name =屏蔽IP Policy = 宝塔IP安全策略 filterlist =IpList filteraction =  阻止IP访问")
        public.ExecShell("Netsh ipsec static set policy name = 宝塔IP安全策略 assign = y")
        cache.set('firewall_init',1)
        return True