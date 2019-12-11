#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com> 
# +-------------------------------------------------------------------
import os ,public ,json ,sys #line:9
from flask import request ,redirect ,g #line:11
from BTPanel import session ,cache #line:12
from datetime import datetime #line:13
class dict_obj :#line:15
    def __contains__ (O0O00OOOO00000O0O ,OOO000O0O0O0OO0O0 ):#line:16
        return getattr (O0O00OOOO00000O0O ,OOO000O0O0O0OO0O0 ,None )#line:17
    def __setitem__ (OOO0O00O0O000O0OO ,OO0O00OO0OO0O0OO0 ,O0O0O0O000OOOOO00 ):setattr (OOO0O00O0O000O0OO ,OO0O00OO0OO0O0OO0 ,O0O0O0O000OOOOO00 )#line:18
    def __getitem__ (OOOOO0O00O00O0O0O ,OO0O00OOOOO0O00O0 ):return getattr (OOOOO0O00O00O0O0O ,OO0O00OOOOO0O00O0 ,None )#line:19
    def __delitem__ (OOO00O0O00OO0OO0O ,OOO0O0OO0O0O00OO0 ):delattr (OOO00O0O00OO0OO0O ,OOO0O0OO0O0O00OO0 )#line:20
    def __delattr__ (O0OO00OOO0O0O0000 ,OO0OOO0OOO000O00O ):delattr (O0OO00OOO0O0O0000 ,OO0OOO0OOO000O00O )#line:21
    def get_items (OOOO00O00O000OOOO ):return OOOO00O00O000OOOO #line:22
class panelSetup :#line:25
    def init (O00O0O00OO0OOO0O0 ):#line:26
        O0O0O00OOOO0O0OOO =request .headers .get ('User-Agent')#line:27
        if O0O0O00OOOO0O0OOO :#line:28
            O0O0O00OOOO0O0OOO =O0O0O00OOOO0O0OOO .lower ();#line:29
            if O0O0O00OOOO0O0OOO .find ('spider')!=-1 or O0O0O00OOOO0O0OOO .find ('bot')!=-1 :return redirect ('https://www.baidu.com');#line:30
        g .version ='6.5.0'#line:32
        g .title =public .GetConfigValue ('title')#line:33
        g .uri =request .path #line:34
        g .setup_path =public .GetConfigValue ('setup_path')#line:35
        g .recycle_bin_open =0 #line:36
        if os .path .exists ("data/recycle_bin.pl"):g .recycle_bin_open =1 #line:37
        public .writeFile ("data/panel.version",g .version )#line:39
        session ['version']=g .version ;#line:41
        session ['title']=g .title #line:42
        return None #line:43
class panelAdmin (panelSetup ):#line:46
    setupPath =os .getenv ("BT_SETUP")#line:47
    def local (OOOO000O00000O0OO ):#line:50
        OOOOO00O0O0O0O0OO =panelSetup ().init ()#line:51
        if OOOOO00O0O0O0O0OO :return OOOOO00O0O0O0O0OO #line:52
        OOOOO00O0O0O0O0OO =OOOO000O00000O0OO .checkLimitIp ()#line:53
        if OOOOO00O0O0O0O0OO :return OOOOO00O0O0O0O0OO #line:54
        OOOOO00O0O0O0O0OO =OOOO000O00000O0OO .setSession ();#line:55
        if OOOOO00O0O0O0O0OO :return OOOOO00O0O0O0O0OO #line:56
        OOOOO00O0O0O0O0OO =OOOO000O00000O0OO .checkClose ();#line:57
        if OOOOO00O0O0O0O0OO :return OOOOO00O0O0O0O0OO #line:58
        OOOOO00O0O0O0O0OO =OOOO000O00000O0OO .checkWebType ();#line:59
        if OOOOO00O0O0O0O0OO :return OOOOO00O0O0O0O0OO #line:60
        OOOOO00O0O0O0O0OO =OOOO000O00000O0OO .checkDomain ();#line:61
        if OOOOO00O0O0O0O0OO :return OOOOO00O0O0O0O0OO #line:62
        OOOOO00O0O0O0O0OO =OOOO000O00000O0OO .checkConfig ();#line:63
        OOOO000O00000O0OO .GetOS ();#line:65
    def checkAddressWhite (O00O0OOOO00O00000 ):#line:69
        OOOOO0OOOOOO0OO00 =O00O0OOOO00O00000 .GetToken ();#line:70
        if not OOOOO0OOOOOO0OO00 :return redirect ('/login');#line:71
        if not request .remote_addr in OOOOO0OOOOOO0OO00 ['address']:return redirect ('/login');#line:72
    def checkLimitIp (OOO0O0O0O0OO0OO0O ):#line:76
        if os .path .exists ('data/limitip.conf'):#line:77
            O0OOO000000000OOO =public .ReadFile ('data/limitip.conf')#line:78
            if O0OOO000000000OOO :#line:79
                O0OOO000000000OOO =O0OOO000000000OOO .strip ();#line:80
                if not public .GetClientIp ()in O0OOO000000000OOO .split (','):return redirect ('/login')#line:81
    def setSession (OOO0OOO0000O0O00O ):#line:85
        session ['menus']=sorted (json .loads (public .ReadFile ('config/menu.json')),key =lambda OOOO0OO0OO00OOO00 :OOOO0OO0OO00OOO00 ['sort'])#line:86
        session ['yaer']=datetime .now ().year #line:87
        session ['download_url']='http://download.bt.cn';#line:88
        if not 'brand'in session :#line:89
            session ['brand']=public .GetConfigValue ('brand');#line:90
            session ['product']=public .GetConfigValue ('product');#line:91
            session ['rootPath']='/www'#line:92
            session ['download_url']='http://download.bt.cn';#line:93
            session ['setupPath']=public .GetConfigValue ('setup_path');#line:94
            session ['logsPath']=public .GetConfigValue ('setup_path')+'/wwwlogs';#line:95
            session ['yaer']=datetime .now ().year #line:96
            print (session )#line:97
        if not 'menu'in session :#line:98
            session ['menu']=public .GetLan ('menu');#line:99
        if not 'lan'in session :#line:100
            session ['lan']=public .GetLanguage ();#line:101
        if not 'home'in session :#line:102
            session ['home']='http://www.bt.cn';#line:103
    def checkWebType (O00O000O00O00O000 ):#line:107
        session ['webserver']='iis';#line:109
        if public .get_server_status ('nginx')>=0 :#line:110
            session ['webserver']='nginx'#line:111
        elif public .get_server_status ('apache')>=0 :#line:112
            session ['webserver']='apache';#line:113
        if os .path .exists (O00O000O00O00O000 .setupPath +'/'+session ['webserver']+'/version.pl'):#line:115
            session ['webversion']=public .ReadFile (O00O000O00O00O000 .setupPath +'/'+session ['webserver']+'/version.pl').strip ()#line:116
        OOOO0OO00O0O00000 =O00O000O00O00O000 .setupPath +'/data/phpmyadminDirName.pl'#line:117
        if os .path .exists (OOOO0OO00O0O00000 ):#line:118
            session ['phpmyadminDir']=public .ReadFile (OOOO0OO00O0O00000 ).strip ()#line:119
    def checkClose (OO0O0OO000O0O000O ):#line:122
        if os .path .exists ('data/close.pl'):#line:123
            return redirect ('/close');#line:124
    def checkDomain (O00OOO00000O00OO0 ):#line:127
        try :#line:128
            O00O00O00O000OOOO =True #line:129
            if not 'login'in session :#line:130
                O00O00O00O000OOOO =O00OOO00000O00OO0 .get_sk ()#line:131
                if O00O00O00O000OOOO :return O00O00O00O000OOOO #line:132
            else :#line:133
                if session ['login']==False :return redirect ('/login')#line:134
            OO0OOOOOO0O00O0OO =public .GetHost ()#line:135
            O0O0OOO000000O000 =public .ReadFile ('data/domain.conf')#line:136
            if O0O0OOO000000O000 :#line:137
                if (OO0OOOOOO0O00O0OO .strip ().lower ()!=O0O0OOO000000O000 .strip ().lower ()):return redirect ('/login')#line:138
            OO0O00OO0O00O00O0 ='data/login_token.pl'#line:140
            if os .path .exists (OO0O00OO0O00O00O0 ):#line:141
                OO000O0O000000OOO =public .readFile (OO0O00OO0O00O00O0 ).strip ()#line:142
                if 'login_token'in session :#line:143
                    if session ['login_token']!=OO000O0O000000OOO :#line:144
                        return redirect ('/login?dologin=True')#line:145
        except :#line:146
            return redirect ('/login')#line:147
    def get_sk (OOOOO0O000O0OO00O ,):#line:150
        OOO00O00O00OOO0OO =OOOOO0O000O0OO00O .setupPath +'/panel/config/api.json'#line:151
        if not os .path .exists (OOO00O00O00OOO0OO ):return redirect ('/login')#line:152
        O0OOO0O00O0O00O00 =json .loads (public .ReadFile (OOO00O00O00OOO0OO ))#line:153
        if not O0OOO0O00O0O00O00 ['open']:return redirect ('/login')#line:154
        from BTPanel import get_input #line:155
        OOOO0O00O000O0O0O =get_input ()#line:156
        if not 'request_token'in OOOO0O00O000O0O0O or not 'request_time'in OOOO0O00O000O0O0O :return redirect ('/login')#line:157
        O0OOO0OOOO00OO000 =public .GetClientIp ()#line:158
        if not O0OOO0OOOO00OO000 in O0OOO0O00O0O00O00 ['limit_addr']:return public .returnJson (False ,'IP校验失败,您的访问IP为['+O0OOO0OOOO00OO000 +']')#line:159
        OO00000O0OO0OOO00 =public .md5 (OOOO0O00O000O0O0O .request_time +O0OOO0O00O0O00O00 ['token'])#line:160
        if OOOO0O00O000O0O0O .request_token ==OO00000O0OO0OOO00 :return False #line:161
        return public .returnJson (False ,'密钥校验失败')#line:162
    def checkConfig (O00O00O000O0O0O00 ):#line:165
        if not 'config'in session :#line:166
            session ['config']=public .M ('config').where ("id=?",('1',)).field ('webserver,sites_path,backup_path,status,mysql_root').find ();#line:167
            O0OOOOO0O0OO000O0 ='data/sa.pl'#line:168
            if os .path .exists (O0OOOOO0O0OO000O0 ):#line:169
                session ['config']['mssql_sa']=public .readFile (O0OOOOO0O0OO000O0 )#line:170
            print (session ['config'])#line:171
            if not 'email'in session ['config']:#line:172
                session ['config']['email']=public .M ('users').where ("id=?",('1',)).getField ('email');#line:173
            if not 'address'in session :#line:174
                session ['address']=public .GetLocalIp ()#line:175
    def checkSafe (OO0000O000OO0OOO0 ):#line:177
        O0OOOOOO000O000OO =['/','/site','/ftp','/database','/plugin','/soft','/public'];#line:178
        if not os .path .exists (os .getenv ("BT_SETUP")+'/data/userInfo.json'):#line:179
            if 'vip'in session :del (session .vip );#line:180
        if not request .path in O0OOOOOO000O000OO :return True #line:181
        if 'vip'in session :return True #line:182
        import panelAuth #line:184
        O000O000OOOOO00O0 =panelAuth .panelAuth ().get_order_status (None );#line:185
        try :#line:186
            if O000O000OOOOO00O0 ['status']==True :#line:187
                session .vip =O000O000OOOOO00O0 #line:188
                return True #line:189
            return redirect ('/vpro');#line:190
        except :pass #line:191
        return False #line:192
    def GetOS (OO0OO0OO000OO0OO0 ):#line:195
        if not 'server_os'in session :#line:196
            OOO0OOOOOOO0OO000 ={}#line:197
            OOO0OOOOOOO0OO000 ['x']='Windows';#line:198
            OOO0OOOOOOO0OO000 ['osname']=''#line:199
            session ['server_os']=OOO0OOOOOOO0OO000 