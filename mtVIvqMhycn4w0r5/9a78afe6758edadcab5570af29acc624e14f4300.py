#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

import public,db,re,os,firewalls
from BTPanel import session
class ftp:
    __xmlPath = None
    setupPath = None
    def __init__(self):
        self.setupPath = public.GetConfigValue('setup_path')
        self.__xmlPath = self.setupPath + '/ftpServer/FileZilla Server.xml'
    
    #添加FTP
    def AddUser(self,get):
        try:

            if not self.check_server(): return public.returnMsg(False,'FileZilla Server软件未安装或不是通过宝塔6.x以上版本安装的.')

            import files,time
            fileObj = files.files()
            if re.search("\W + ",get['ftp_username']): return {'status':False,'code':501,'msg':public.getMsg('FTP_USERNAME_ERR_T')}
            if len(get['ftp_username']) < 3: return {'status':False,'code':501,'msg':public.getMsg('FTP_USERNAME_ERR_LEN')}
            if not fileObj.CheckDir(get['path']): return {'status':False,'code':501,'msg':public.getMsg('FTP_USERNAME_ERR_DIR')}
            if public.M('ftps').where('name=?',(get.ftp_username.strip(),)).count(): return public.returnMsg(False,'FTP_USERNAME_ERR_EXISTS',(get.ftp_username,))
            username = get['ftp_username'].replace(' ','')
            password = get['ftp_password']
            get.path = get['path'].replace(' ','')
            get.path = get.path.replace("\\", "/")
            fileObj.CreateDir(get)
            Down = get['down']           
            Up = get['up']          
            access = get['access']

            if not Down: Down = 1024 #默认1024K
            if not Up: Up = 1024  #默认1024K
            if not access: access = '1' #默认读写权限                

            user = {"@Name": username , "Option": [{"@Name": "Pass", "#text": public.Md5(password) }, {"@Name": "Group"}, {"@Name": "Bypass server userlimit", "#text": "1"}, {"@Name": "User Limit", "#text": "5"}, {"@Name": "IP Limit", "#text": "10"}, {"@Name": "Enabled", "#text": "1"}, {"@Name": "Comments"}, {"@Name": "ForceSsl", "#text": "0"}], "IpFilter": {"Disallowed": "", "Allowed": ""}, "Permissions": {"Permission": {"@Dir": get.path , "Option": [{"@Name": "FileRead", "#text": "1"}, {"@Name": "FileWrite", "#text": access}, {"@Name": "FileDelete", "#text": access}, {"@Name": "FileAppend", "#text": "1"}, {"@Name": "DirCreate", "#text": access }, {"@Name": "DirDelete", "#text": access}, {"@Name": "DirList", "#text": "1"}, {"@Name": "DirSubdirs", "#text": "1"}, {"@Name": "IsHome", "#text": "1"}, {"@Name": "AutoCreate", "#text": "1"}]}}, "SpeedLimits": {"@DlType": "2", "@DlLimit": Down, "@ServerDlLimitBypass": "0", "@UlType": "2", "@UlLimit": Up, "@ServerUlLimitBypass": "0", "Download": "", "Upload": ""}}
            data = self.get_ftp_config()           
            data['FileZillaServer']['Users']['User'].append(user)   
            public.writeFile(self.__xmlPath, public.format_xml(public.dumps_json(data)))

            self.FtpReload()

            ps=get['ps']
            if get['ps']=='': ps= public.getMsg('INPUT_PS');
            addtime=time.strftime('%Y-%m-%d %X',time.localtime())
            
            pid = 0
            if hasattr(get,'pid'): pid = get.pid
            public.M('ftps').add('pid,name,password,path,status,ps,addtime',(pid,username,password,get.path,1,ps,addtime))
            public.WriteLog('TYPE_FTP', 'FTP_ADD_SUCCESS',(username,))
            return public.returnMsg(True,'ADD_SUCCESS')
        except Exception as ex:        
            return public.returnMsg(False,'ADD_ERROR')
    
    #删除用户
    def DeleteUser(self,get):
        #try:

        if not self.check_server(): return public.returnMsg(False,'FileZilla Server软件未安装或不是通过宝塔6.x以上版本安装的.')

        username = get['username']
        id = get['id']
           
        data = self.get_ftp_config() 
        users = []
        for user in  data['FileZillaServer']['Users']['User']:            
            if user['@Name'] != username: users.append(user)            
        data['FileZillaServer']['Users']['User'] = users
        public.writeFile(self.__xmlPath, public.format_xml(public.dumps_json(data)))
        
        self.FtpReload()
        public.M('ftps').where("id=?",(id,)).delete()
        public.WriteLog('TYPE_FTP', 'FTP_DEL_SUCCESS',(username,))
        return public.returnMsg(True, "DEL_SUCCESS")
        #except Exception as ex:
        #    public.WriteLog('TYPE_FTP', 'FTP_DEL_ERR',(username,str(ex)))
        #    return public.returnMsg(False,'DEL_ERROR')
    
    
    #修改用户密码
    def SetUserPassword(self,get):
        #try:
        if not self.check_server(): return public.returnMsg(False,'FileZilla Server软件未安装或不是通过宝塔6.x以上版本安装的.')

        id = get['id']
        username = get['ftp_username']
        password = get['new_password']

        data = self.set_user_config(username,'Pass',public.Md5(password))      
        self.FtpReload()

        public.M('ftps').where("id=?",(id,)).setField('password',password)
        public.WriteLog('TYPE_FTP', 'FTP_PASS_SUCCESS',(username,))
        return public.returnMsg(True,'EDIT_SUCCESS')
        #except Exception as ex:
        #public.WriteLog('TYPE_FTP', 'FTP_PASS_ERR',(username,str(ex)))
        #return public.returnMsg(False,'EDIT_ERROR')
    
    
    #设置用户状态
    def SetStatus(self,get):
        if not self.check_server(): return public.returnMsg(False,'FileZilla Server软件未安装或不是通过宝塔6.x以上版本安装的.')

        msg = public.getMsg('OFF');
        if get.status != '0': msg = public.getMsg('ON');
        try:
            id = get['id']
            username = get['username']
            status = get['status']
            
            self.set_user_config(username,'Enabled',status)      
            
            self.FtpReload()
            public.M('ftps').where("id=?",(id,)).setField('status',status)
            public.WriteLog('TYPE_FTP','FTP_STATUS', (msg,username))
            return public.returnMsg(True, 'SUCCESS')
        except Exception as ex:
            public.WriteLog('TYPE_FTP','FTP_STATUS_ERR', (msg,username,str(ex)))
            return public.returnMsg(False,'FTP_STATUS_ERR',(msg,))
    
    def check_server(self):
        if public.get_server_status("FileZilla Server") < 0 or not os.path.exists(self.__xmlPath): 
            return False
        return True

    '''
     * 设置FTP端口
     * @param Int _GET['port'] 端口号 
     * @return bool
     '''
    def setPort(self,get):
        try:
            if not self.check_server(): return public.returnMsg(False,'FileZilla Server软件未安装或不是通过宝塔6.x以上版本安装的.')

            port = get['port']
            if int(port) < 1 or int(port) > 65535: return public.returnMsg(False,'PORT_CHECK_RANGE')

            self.set_pub_config('Serverports',port)
            self.FtpReload()
            public.WriteLog('TYPE_FTP', "FTP_PORT",(port,))
            #添加防火墙
            #data = ftpinfo(port=port,ps = 'FTP端口')
            get.port=port
            get.ps = public.getMsg('FTP_PORT_PS');
            firewalls.firewalls().AddAcceptPort(get)
            session['port']=port
            return public.returnMsg(True, 'EDIT_SUCCESS')
        except Exception as ex:
            public.WriteLog('TYPE_FTP', 'FTP_PORT_ERR',(str(ex),))
            return public.returnMsg(False,'EDIT_ERROR')
    
    #格式化ftp配置        
    def get_ftp_config(self):
        data = public.loads_json(self.__xmlPath)
        try:             
            if data:                
                list = data['FileZillaServer']['Users']['User']
                if type(list) != type([1,]): 
                    data['FileZillaServer']['Users']['User'] = [list]
            else:
                data = {'FileZillaServer':{'Users':{'User':[]}}}
        except :

            if not data['FileZillaServer']['Users']:
                user = {}
                user["User"] = [];
                data['FileZillaServer']['Users'] = user
        return data

    #设置用户配置
    def set_user_config(self,username,key,val):
        data = self.get_ftp_config()
        for user in  data['FileZillaServer']['Users']['User']:            
            if user['@Name'] == username:
                for item in user['Option']:
                    if item["@Name"] == key: 
                        item['#text'] = val           
                        break
        public.writeFile(self.__xmlPath, public.format_xml(public.dumps_json(data)))
        return True
    
    #设置公用配置
    def set_pub_config(self,key,val):
        data = self.get_ftp_config()
        for item in  data['FileZillaServer']['Settings']['Item']:
            if item['@name'] == key:
                item['#text'] = val
                break
        public.writeFile(self.__xmlPath, public.format_xml(public.dumps_json(data)))
        return True;
    
    #获取公用配置
    def get_pub_config(self,key):
        data = self.get_ftp_config()
        for item in  data['FileZillaServer']['Settings']['Item']:
            if item['@name'] == key:
               return item['#text']      
        return None;

    #重载配置
    def FtpReload(self):
        public.set_server_status('FileZilla Server','restart')