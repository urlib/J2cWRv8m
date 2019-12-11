#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

import win32serviceutil,win32service,win32event,os,sys

class btService(win32serviceutil.ServiceFramework): 
    #服务名 
    _svc_name_ = "btPanel"
    #服务在windows系统中显示的名称 
    _svc_display_name_ = "btPanel"
    #服务的描述 
    _svc_description_ = "用于运行宝塔Windows面板主程序,停止后面板将无法访问."  

    def __init__(self, args): 
        win32serviceutil.ServiceFramework.__init__(self, args) 
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None) 
        self.run = True

    def SvcDoRun(self): 
        path = os.getenv('BT_PANEL')

        import subprocess
        self.p = subprocess.Popen(['C:\Program Files\python\python.exe', path + '/runserver.py'])
        # 等待服务被停止 
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE) 
     
    def SvcStop(self): 
        os.system("taskkill /t /f /pid %s" % self.p.pid)
        # 先告诉SCM停止这个过程 
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING) 
        # 设置事件 
        win32event.SetEvent(self.hWaitStop)
        self.run = False

if __name__ == '__main__':
    path = os.getenv('BT_PANEL')
    if len(sys.argv) >= 2:       
        if not path:            
            path = os.path.dirname(sys.argv[0])
            os.environ['BT_PANEL'] = path
            if not path:
                print('ERROR:安装失败，找不到环境变量【BT_PANEL】.')
                exit()
        win32serviceutil.HandleCommandLine(btService) 
    else:
        os.chdir(path)
        sys.path.insert(0,path + "/class/")
        from os import environ
        from BTPanel import app,sys

        PORT = 8888
        filename = path + '/data/port.pl'
        if os.path.exists(filename):
            fp = open(filename, 'r',encoding = 'utf-8')
            PORT = fp.read()
            fp.close()
        HOST = '0.0.0.0'     
        try:
            from gevent import monkey
            monkey.patch_all()  
            from gevent import pywsgi          
            server = pywsgi.WSGIServer((HOST, int(PORT)), app)
            server.serve_forever()
        except :
            app.run(host = HOST,port = int(PORT))
