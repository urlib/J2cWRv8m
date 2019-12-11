#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

import re,os,sys,public

class panelMssql:
    __DB_PASS = None
    __DB_USER = 'sa'
    __DB_PORT = 1433
    __DB_HOST = '127.0.0.1'
    __DB_CONN = None
    __DB_CUR  = None
    __DB_ERR  = None
    __DB_SERVER = 'MSSQLSERVER'
    #连接MSSQL数据库
    def __Conn(self):
        try:
            import pymssql
        except :
            os.system(public.get_run_pip("[PIP] install pymssql==2.1.4"))
            import pymssql        
               
        sa_path = 'data/sa.pl'
        if os.path.exists(sa_path):
            self.__DB_PASS = public.readFile(sa_path)
            self.__DB_PORT = self.get_port()
            try: 
                self.__DB_CONN = pymssql.connect(server = self.__DB_HOST, port= str(self.__DB_PORT),login_timeout = 30,timeout = 0,autocommit = True)            
                self.__DB_CUR = self.__DB_CONN.cursor()  #将数据库连接信息，赋值给cur。
                if self.__DB_CUR:
                    return True
                else:
                    self.__DB_ERR = '连接数据库失败'
                    return False
            except Exception as ex:
              
                public.WriteLog('执行异常', str(ex));
                version = public.readFile(os.getenv("BT_SETUP") + '/sqlserver/version.pl')
                if version == '2005':
                    self.__DB_ERR = '2005_login_error'
                else:
                    self.__DB_ERR = str(ex)
       
        return False

    def get_mssql_reg_path(self):
        version = public.readFile(public.GetConfigValue('setup_path') + '/sqlserver/version.pl')
        if version == '2005':
            key = 'SOFTWARE\Wow6432Node\Microsoft\Microsoft SQL Server\MSSQL.1\MSSQLServer\SuperSocketNetLib\Tcp\IPAll'
        else:
            key = 'SOFTWARE\Wow6432Node\Microsoft\MSSQLServer\MSSQLServer\SuperSocketNetLib\Tcp'
        return key

    #获取端口
    def get_port(self):        
        try:
            key = self.get_mssql_reg_path()
            if key: 
                port = public.ReadReg(key,'TcpPort')
                return port
        except :
            pass
        return "1433"
    
    def execute(self,sql):
       
        if public.get_server_status(self.__DB_SERVER) == 0 :
            public.set_server_status(self.__DB_SERVER,'start')
       
        #执行SQL语句返回受影响行
        if not self.__Conn(): return self.__DB_ERR
        try:
            result = self.__DB_CUR.execute(sql)
          
            self.__Close()
            return result;    
        except Exception as ex:
            self.__DB_ERR = str(ex)
            return self.__DB_ERR
    
    def query(self,sql):
        #执行SQL语句返回数据集
        if not self.__Conn(): return self.__DB_ERR
        try:
            self.__DB_CUR.execute(sql)
            result = self.__DB_CUR.fetchall()
            #print(result)
            #将元组转换成列表
            data = list(map(list,result))
            self.__Close()
            return data
        except Exception as ex:
            self.__DB_ERR = str(ex)
            #public.WriteLog('SQL Server查询异常', self.__DB_ERR);
            return str(ex)
        
     
    #关闭连接        
    def __Close(self):
        self.__DB_CUR.close()
        self.__DB_CONN.close()