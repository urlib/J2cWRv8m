#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

import public,db,os,time,re
import threading
class panelCrontab:

    _reload = False;
    _ctime = {}
    def __init__(self):
        self._ctime = self.get_ctime()

    #处理任务
    def process_fun(self,item):
        try:   
            #print( self._ctime)
            if item['status'] == 1:
                runtime = item['nexttime']
                stype = item['type']          
                if not runtime:  
                    loacl_time = self._ctime['local_time']
                   
                    if stype == 'day':    
                        runtime = self.get_local_time('%s-%s-%s %s:%s:00' % (loacl_time.tm_year,loacl_time.tm_mon,loacl_time.tm_mday,item['where_hour'],item['where_minute']))                                               
                    elif stype=='day-n':
                        runtime =  self.get_local_time('%s-%s-%s %s:%s:00' % (loacl_time.tm_year,loacl_time.tm_mon,loacl_time.tm_mday,item['where_hour'],item['where_minute']))          
                    elif stype == 'hour':
                        runtime = self.get_local_time('%s-%s-%s %s:%s:00' % (loacl_time.tm_year,loacl_time.tm_mon,loacl_time.tm_mday,loacl_time.tm_hour,item['where_minute']))       
                    elif stype == 'hour-n':
                        runtime =  self.get_local_time('%s-%s-%s %s:%s:00' % (loacl_time.tm_year,loacl_time.tm_mon,loacl_time.tm_mday,loacl_time.tm_hour,item['where_minute'])) 
                    elif stype == 'minute-n':
                        runtime = int(time.time())                        
                    elif stype == 'week': 
                        #处理周任务
                        total_day = 0
                        week = int(item['where1'])
                        if week >= int(self._ctime['week']):
                            total_day = week - int(self._ctime['week'])
                        else:
                            total_day = week + 7 - int(self._ctime['week'])                        
                        ttime = self.calc_time(int(time.time()),total_day,'day')                        
                        loacl_time = time.localtime(ttime)                 
                        next_time = self.get_local_time('%s-%s-%s %s:%s:00' % (loacl_time.tm_year,loacl_time.tm_mon,loacl_time.tm_mday,item['where_hour'],item['where_minute']))   
                        runtime = self.calc_time(next_time,-1,stype)
                    elif stype == 'month':
                        runtime = self.get_local_time('%s-%s-%s %s:%s:00' % (loacl_time.tm_year,loacl_time.tm_mon,item['where1'],item['where_hour'],item['where_minute']))     

                if int(self._ctime['long_time']) >= int(runtime):                   
                    t = threading.Thread(target=self.run_threading,args=(item,runtime))
                    t.setDaemon(True)
                    t.start()            
        except :
            pass
        return True

    #执行线程
    def run_threading(self,sdata,runtime):

        #获取下次运行时间
        next_time = self.get_next_time(runtime,sdata)
        ctime = int(self._ctime['long_time'])
        while next_time <= ctime:
            next_time = self.get_next_time(next_time,sdata)

        public.M('crontab').where('id=?',(sdata['id'],)).save("pretime,nexttime",(ctime,int(next_time)))

        path =  public.GetConfigValue('setup_path') + '/cron/' + sdata['echo']
        if os.path.exists(path):
            shell = public.readFile(path)
            
            import subprocess
            sub = subprocess.Popen(shell+' >> ' + path + '.log' + ' 2>&1', cwd=None, stdin = subprocess.PIPE,shell = True,bufsize=4096)
            while sub.poll() is None:
               time.sleep(0.1)
            return sub.returncode   
    
    #获取下次更新时间
    def get_next_time(self,runtime,item):
        next_time = 0
        runtime = int(runtime)
        loacl_time = self._ctime['local_time']
        stype = item['type']     
        if stype == 'day':                                 
            next_time = self.calc_time(runtime,1,stype)                          
        elif stype=='day-n':            
            next_time = self.calc_time(runtime,int(item['where1']),'day')   
        elif stype == 'hour':                 
            next_time = self.calc_time(runtime,1,stype)
        elif stype == 'hour-n':           
            next_time = self.calc_time(runtime,int(item['where1']),'hour')   
        elif stype == 'minute-n':           
            next_time = self.calc_time(runtime,int(item['where1']),'minute')
        elif stype == 'week': 
            next_time = self.calc_time(runtime,1,stype)
        elif stype == 'month':           
            next_time = self.calc_time(runtime,1,stype) 
        return next_time

    #计算时间
    def calc_time(self,ctime,cycle = 1,unit = 'day'):
        rtime = 0
        if unit == 'day':
            rtime = ctime + cycle * 86400
        elif unit == 'hour':
            rtime = ctime + cycle * 3600
        elif unit == 'minute':
            rtime = ctime + cycle * 60
        elif unit == 'month':            
            import datetime
            try:                
                from dateutil.relativedelta import relativedelta
            except :
                os.system(public.get_run_pip('[PIP] install python-dateutil'))                
                from dateutil.relativedelta import relativedelta          
            dt =  datetime.datetime.fromtimestamp(ctime)  
            ndt = dt + relativedelta(months=+1)
            rtime = time.mktime(ndt.timetuple())
        elif unit == 'week':
            rtime = ctime + cycle * 7 * 86400    
        return rtime


    #获取更新时间
    def get_ctime(self):
        data = {}
        data['long_time'] = int(time.time())
        data['local_time'] = time.localtime()            
        data['week'] =  time.strftime('%w', data['local_time'])
        return data

    #格式化时间
    def get_local_time(self,now_time):

        time_array = time.strptime(now_time, "%Y-%m-%d %H:%M:%S")
        timestamp = time.mktime(time_array)
        return timestamp
