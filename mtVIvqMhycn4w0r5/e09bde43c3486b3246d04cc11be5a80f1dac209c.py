#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

#------------------------------
# SSL接口
#------------------------------
import public,os,sys,binascii,urllib,json,time,datetime

class panelSSL:
    __APIURL = 'http://www.bt.cn/api/Auth';
    __UPATH = 'data/userInfo.json';
    __userInfo = None;
    __PDATA = None;
    setupPath = None #安装路径
    
    #构造方法
    def __init__(self):
        self.setupPath = public.GetConfigValue('setup_path')
        pdata = {}
        data = {}
        if os.path.exists(self.__UPATH):
            try:
                self.__userInfo = json.loads(public.readFile(self.__UPATH));
                if self.__userInfo:
                    pdata['access_key'] = self.__userInfo['access_key'];
                    data['secret_key'] = self.__userInfo['secret_key'];
            except :
                self.__userInfo = None        
        else:
            pdata['access_key'] = 'test';
            data['secret_key'] = '123456';
        pdata['data'] = data;
        self.__PDATA = pdata;

    #获取Token
    def GetToken(self,get):
        rtmp = ""
        data = {}
        data['username'] = get.username;
        data['password'] = public.md5(get.password);
        pdata = {}
        pdata['data'] = self.De_Code(data);
        try:
            rtmp = public.httpPost(self.__APIURL+'/GetToken',pdata)
            result = json.loads(rtmp);
            result['data'] = self.En_Code(result['data']);
            if result['data']: public.writeFile(self.__UPATH,json.dumps(result['data']));
            del(result['data']);
            return result;
        except Exception as ex:
            return public.returnMsg(False,'连接服务器失败!<br>' + str(rtmp))
    
    #删除Token
    def DelToken(self,get):
        if os.path.exists(self.__UPATH):            
            os.remove(self.__UPATH)
        return public.returnMsg(True,"SSL_BTUSER_UN");
    
    #获取用户信息
    def GetUserInfo(self,get):
        result = {}
        if self.__userInfo:
            userTmp = {}
            userTmp['username'] = self.__userInfo['username'][0:3]+'****'+self.__userInfo['username'][-4:];
            result['status'] = True;
            result['msg'] = public.getMsg('SSL_GET_SUCCESS');
            result['data'] = userTmp;
        else:
            userTmp = {}
            userTmp['username'] = public.getMsg('SSL_NOT_BTUSER');
            result['status'] = False;
            result['msg'] = public.getMsg('SSL_NOT_BTUSER');
            result['data'] = userTmp;
        return result;
    
    #获取订单列表
    def GetOrderList(self,get):         

        #暂不开启本地缓存
        get.focre = 1;

        focre  = 0
        if hasattr(get,'force'): focre = int(get.force)
        lcoalTmp = 'data/ssl_order_list.json'
     
        result = None
        #if os.path.exists(lcoalTmp): result = json.loads(public.readFile(lcoalTmp))

        if not result or  focre > 0:
            lcoalTmp = 'data/ssl_order_list.json'
            if hasattr(get,'siteName'):
                path =  self.setupPath + '/panel/vhost/cert/'+ get.siteName + '/partnerOrderId';
                if os.path.exists(path):
                    self.__PDATA['data']['partnerOrderId'] = public.readFile(path);
        
            self.__PDATA['data'] = self.De_Code(self.__PDATA['data']);
            data = ""
            try:
                data = public.httpPost(self.__APIURL + '/GetSSLList',self.__PDATA)
                result = json.loads(data)
            except Exception as ex:
                return public.returnMsg(False,'连接服务器失败!<br>' + str(data)) 

            result['data'] = self.En_Code(result['data']);
            for i in range(len(result['data'])):
                result['data'][i]['endtime'] =   self.add_months(result['data'][i]['createTime'],result['data'][i]['validityPeriod'])
          
            if result: public.writeFile(lcoalTmp,json.dumps(result))

        return result;

    
    #计算日期增加(月)
    def add_months(self,dt,months):
        import calendar
        dt = datetime.datetime.fromtimestamp(dt/1000);
        month = dt.month - 1 + months
        year = dt.year + month // 12
        month = month % 12 + 1

        day = min(dt.day,calendar.monthrange(year,month)[1])
        return (time.mktime(dt.replace(year=year, month=month, day=day).timetuple()) + 86400) * 1000
    
    
    #申请证书
    def GetDVSSL(self,get):
        get.id = public.M('domain').where('name=?',(get.domain,)).getField('pid');
        if hasattr(get,'siteName'):
            get.path = public.M('sites').where('id=?',(get.id,)).getField('path');
        else:
            get.siteName = public.M('sites').where('id=?',(get.id,)).getField('name');
        
        runPath = self.GetRunPath(get);
        if runPath != False and runPath != '/': get.path +=  runPath;
        authfile = get.path + '/.well-known/pki-validation/fileauth.txt';
        if not self.CheckDomain(get):
            if not os.path.exists(authfile): return public.returnMsg(False,'无法创建['+authfile+']');
        
        action = 'GetDVSSL';
        if hasattr(get,'partnerOrderId'):
            self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId;
            action = 'ReDVSSL';
        
        self.__PDATA['data']['domain'] = get.domain;
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data']);
        result = public.httpPost(self.__APIURL + '/' + action,self.__PDATA)
        try:
            result = json.loads(result);
        except: return result;
        result['data'] = self.En_Code(result['data']);
        if hasattr(result['data'],'authValue'):
            public.writeFile(authfile,result['data']['authValue']);
        
        return result;
    
    #获取运行目录
    def GetRunPath(self,get):
        if hasattr(get,'siteName'):
            get.id = public.M('sites').where('name=?',(get.siteName,)).getField('id');
        else:
            get.id = public.M('sites').where('path=?',(get.path,)).getField('id');
        if not get.id: return False;
        import panelSite
        result = panelSite.panelSite().GetSiteRunPath(get);
        if 'runPath' in result:            
            return result['runPath'];
        return '/'
    
    #检查域名是否解析
    def CheckDomain(self,get):
        try:
            epass = public.GetRandomString(32);
            spath = get.path + '/.well-known/pki-validation';
            if not os.path.exists(spath): os.makedirs(spath)
            public.writeFile(spath + '/fileauth.txt',epass);
            result = public.httpGet('http://' + get.domain + '/.well-known/pki-validation/fileauth.txt');
            if result == epass: return True
            return False
        except:
            return False
    
    #确认域名
    def Completed(self,get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId;
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data']);
        if hasattr(get,'siteName'):
            get.path = public.M('sites').where('name=?',(get.siteName,)).getField('path');
            runPath = self.GetRunPath(get);
            if runPath != False and runPath != '/': get.path +=  runPath;
           
            sslInfo = json.loads(public.httpPost(self.__APIURL + '/SyncOrder',self.__PDATA));
            sslInfo['data'] = self.En_Code(sslInfo['data']);  
            try:
                public.writeFile(get.path + '/.well-known/pki-validation/fileauth.txt',sslInfo['data']['authValue']);
            except:
                return public.returnMsg(False,'SSL_CHECK_WRITE_ERR');       
        public.httpPost(self.__APIURL + '/Completed',self.__PDATA)     

        n = 0
        while True:
            if n > 8: break  
            try:
                time.sleep(3)           
                rRet = json.loads(public.httpPost(self.__APIURL + '/SyncOrder',self.__PDATA));
           
                rRet['data'] = self.En_Code(rRet['data']);
                if rRet['data']['stateCode'] == 'COMPLETED': break                
                n += 1
            except : pass

        return rRet;
    
    #同步指定订单
    def SyncOrder(self,get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId;
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data']);
        result = json.loads(public.httpPost(self.__APIURL + '/SyncOrder',self.__PDATA));
        result['data'] = self.En_Code(result['data']);
        return result;
    
    #获取证书
    def GetSSLInfo(self,get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId;
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data']);

        serverType = public.get_webserver(); 
        if serverType == 'iis':   
            result = json.loads(public.httpPost(self.__APIURL + '/GetPKCS12',self.__PDATA));
        else:
            result = json.loads(public.httpPost(self.__APIURL + '/GetSSLInfo',self.__PDATA)); 
        rets = result
        result['data'] = self.En_Code(result['data']);

         #写配置到站点
        if hasattr(get,'siteName'):            
            try:
                if result['status']:                    
                    siteName = get.siteName;
                    path = self.setupPath + '/panel/vhost/cert/'+ siteName;
                    if not os.path.exists(path): os.makedirs(path)
                    pidpath = path + "/partnerOrderId";
                    if serverType == 'iis':   
                        pwdpath = path + "/password"
                        pfxpath = path + "/fullchain.pfx"
                        import base64
                        public.writeFile(pwdpath,result['data']['password'])
                        #写入pfx证书
                        public.writeFile2(pfxpath,base64.b64decode(result['data']['fileData']),'wb+')

                        #处理一个网站多个域名证书
                        get.certPath = pfxpath
                        get.password = result['data']['password']
                        cert_data = self.GetCertName(get)
                        if cert_data:
                            domain = cert_data['dns'][0]
                            if domain.find("*") < 0:                        
                                if len(cert_data['dns']) > 1 : domain = cert_data['dns'][len(cert_data['dns']) - 1]
                    
                                pwdpath = path + "/" + domain
                                pfxpath = path + "/" + domain + ".pfx"

                                public.writeFile(pwdpath,result['data']['password'])
                                public.writeFile2(pfxpath,base64.b64decode(result['data']['fileData']),'wb+')

                    elif serverType == 'apache':
                        path = os.getenv("BT_SETUP") + '/apache/conf/ssl/' + siteName 
                        if not os.path.exists(path): os.makedirs(path)

                        csrpath = path + "/fullchain.pem";
                        keypath = path + "/privkey.pem";

                        public.writeFile(keypath,result['data']['privateKey']);
                        public.writeFile(csrpath,result['data']['cert'] + result['data']['certCa']);

                    else:
                        path = os.getenv("BT_SETUP") + '/nginx/conf/ssl/' + siteName 
                        if not os.path.exists(path): os.makedirs(path)

                        csrpath = path + "/fullchain.pem";
                        keypath = path + "/privkey.pem";

                        public.writeFile(keypath,result['data']['privateKey'].strip());
                        public.writeFile(csrpath,result['data']['cert'] + result['data']['certCa'].strip());

                    public.writeFile(pidpath,get.partnerOrderId);
                    import panelSite
                    result = panelSite.panelSite().SetSSLConf(get);         
                    return result;
                else:
                    return public.returnMsg(False,result['msg']);
            except Exception as ex:               
                return public.returnMsg(False,'SET_ERROR,' + str(ex));
        return result;
    
    #部署证书夹证书
    def SetCertToSite(self,get):
        try:
            import shutil
            siteName = get.siteName;
            path = self.setupPath + '/panel/vhost/cert/'+ siteName;
            if not os.path.exists(path): os.makedirs(path)         

            d_path = self.setupPath + '/panel/vhost/ssl/' + get.certName
            d_path = d_path.replace("*.","")

            serverType = public.get_webserver(); 
            if serverType == 'iis':    
                shutil.copyfile( d_path + "/fullchain.pfx",path + '/fullchain.pfx')
                if os.path.exists(d_path + '/password'): shutil.copyfile(d_path + '/password',path + '/password')
            elif serverType == 'apache':
                npath = os.getenv("BT_SETUP") + '/apache/conf/ssl/' + siteName 
                if not os.path.exists(npath): os.makedirs(npath)

                shutil.copyfile( d_path + "/fullchain.pem",npath + '/fullchain.pem')
                shutil.copyfile( d_path + "/privkey.pem",npath + '/privkey.pem')

            if os.path.exists(path + '/partnerOrderId'): os.remove(path + '/partnerOrderId')
            if os.path.exists(d_path + '/partnerOrderId'): shutil.copyfile(d_path + '/partnerOrderId',path + '/partnerOrderId')

            import panelSite
            panelSite.panelSite().SetSSLConf(get);
            public.serviceReload();
            return public.returnMsg(True,'SET_SUCCESS');
        except Exception as ex:
            return public.returnMsg(False,'SET_ERROR,' + str(ex));
    
    #获取证书列表
    def GetCertList(self,get):
        try:
            vpath = self.setupPath + '/panel/vhost/ssl'
            if not os.path.exists(vpath): os.makedirs(vpath)
            data = []
            for d in os.listdir(vpath):
                mpath = vpath + '/' + d + '/info.json';
           
                if not os.path.exists(mpath): continue;
                tmp = public.readFile(mpath)
                if not tmp: continue;
                tmp1 = json.loads(tmp)
                data.append(tmp1)
            return data;
        except:
            return [];
    
    #删除证书
    def RemoveCert(self,get):
        try:
            vpath = self.setupPath + '/panel/vhost/ssl/' + get.certName
            vpath = vpath.replace("*.","")
            if not os.path.exists(vpath): return public.returnMsg(False,'证书不存在!');
            import shutil
            shutil.rmtree(vpath)
            return public.returnMsg(True,'证书已删除!');
        except:
            return public.returnMsg(False,'删除失败!');
    
    #保存证书
    def SaveCert(self,get):
        try:
            certInfo = self.GetCertName(get)
            if not certInfo: return public.returnMsg(False,'证书解析失败!');
            vpath = self.setupPath + '/panel/vhost/ssl/' + certInfo['subject'];           
            if not os.path.exists(vpath):  os.makedirs(vpath);

            vpath = vpath.replace("*.","")
            serverType = public.get_webserver(); 
            if serverType == 'iis': 
                import shutil
                if get.password: public.writeFile(vpath + '/password',get.password)
                shutil.copyfile(get.certPath,vpath + '/fullchain.pfx')
                if hasattr(get,'local'):
                    local_path = self.setupPath + '/panel/vhost/cert/localhost'
                    if not os.path.exists(local_path):  os.makedirs(local_path);

                    shutil.copyfile(get.certPath,local_path + '/fullchain.pfx')
            else:              
                public.writeFile(vpath + '/privkey.pem',public.readFile(get.keyPath));
                public.writeFile(vpath + '/fullchain.pem',public.readFile(get.certPath));
            public.writeFile(vpath + '/info.json',json.dumps(certInfo));

            if os.path.exists(vpath + '/partnerOrderId'): os.remove(vpath + '/partnerOrderId')       
            if get.partnerOrderId: public.writeFile(vpath + '/partnerOrderId',get.partnerOrderId)

            return public.returnMsg(True,'证书保存成功!');
        except:
            return public.returnMsg(False,'证书保存失败!');
    

    
    #获取证书名称
    def GetCertName(self,get):
        try:                  
            try:
                from OpenSSL import crypto 
                from urllib3.contrib import pyopenssl as reqs
            except :
                os.system(public.get_run_pip('[PIP] install crypto'))
                os.system(public.get_run_pip('[PIP] install pyopenssl'))

                from OpenSSL import crypto 
                from urllib3.contrib import pyopenssl as reqs
            
            certPath = get.certPath     
            if os.path.exists(certPath):
                data = {}
                f = open(certPath,'rb') 
                pfx_buffer = f.read() 
                cret_data = pfx_buffer
                if certPath[-4:] == '.pfx':   
                    if hasattr(get, 'password'):
                        p12 = crypto.load_pkcs12(pfx_buffer,get.password)
                    else:
                        p12 = crypto.load_pkcs12(pfx_buffer)
                    x509 = p12.get_certificate()
                    data['type'] = 'pfx'     
                else:
                    x509 = crypto.load_certificate(crypto.FILETYPE_PEM, pfx_buffer)
                    data['type'] = 'pem'
                buffs = x509.digest('sha1')            
                data['hash'] =  bytes.decode(buffs).replace(':','')
                data['number'] = x509.get_serial_number()
                issuser = x509.get_issuer()

                is_key = 'O'
                if len(issuser.get_components()) == 1: is_key = 'CN'                
                for item in issuser.get_components():                 
                    if bytes.decode(item[0]) == is_key:                   
                        data['issuer'] = bytes.decode(item[1])
                        break
            
                data['notAfter'] = self.strfToTime(bytes.decode( x509.get_notAfter())[:-1])
                data['notBefore'] = self.strfToTime(bytes.decode(x509.get_notBefore())[:-1])
                data['version'] = x509.get_version()
                data['timeout'] = x509.has_expired()
                x509name = x509.get_subject()
                data['subject'] = x509name.commonName.replace('*','_')
                data['dns'] = []
                alts = reqs.get_subj_alt_name(x509)
                for x in alts:  
                    data['dns'].append(x[1])
              
            return data;
        except:
            return None;
    
    #转换时间
    def strfToTime(self,sdate):
        import time
        return time.strftime('%Y-%m-%d',time.strptime(sdate,'%Y%m%d%H%M%S'))
        
    
    #获取产品列表
    def GetSSLProduct(self,get):
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data']);
        result = json.loads(public.httpPost(self.__APIURL + '/GetSSLProduct',self.__PDATA));
        result['data'] = self.En_Code(result['data']);
        return result;
    
    #加密数据
    def De_Code(self,data):
        if sys.version_info[0] == 2:
            pdata = urllib.urlencode(data);
        else:
            pdata = urllib.parse.urlencode(data);
            if type(pdata) == str: pdata = pdata.encode('utf-8')
        return binascii.hexlify(pdata);
    
    #解密数据
    def En_Code(self,data):
        if sys.version_info[0] == 2:
            result = urllib.unquote(binascii.unhexlify(data));
        else:
            if type(data) == str: data = data.encode('utf-8')
            tmp = binascii.unhexlify(data)
            if type(tmp) != str: tmp = tmp.decode('utf-8')
            result = urllib.parse.unquote(tmp)

        if type(result) != str: result = result.decode('utf-8')
        return json.loads(result);
    
    # 手动一键续签
    def renew_lets_ssl(self, get):
        if not os.path.exists('vhost/crontab.json'):  
            return public.returnMsg(False,'当前没有可以续订的证书!')      
        
        old_list = json.loads(public.ReadFile("vhost/crontab.json"))
        cron_list = old_list
        if hasattr(get, 'siteName'):
            if not get.siteName in old_list:
                return public.returnMsg(False,'当前网站没有可以续订的证书.')  
            cron_list = {}
            cron_list[get.siteName] = old_list[get.siteName]

        import panelLets
        lets = panelLets.panelLets()

        result = {}
        result['status'] = True
        result['sucess_list']  = []
        result['err_list'] = []
        for siteName in cron_list:
            data = cron_list[siteName]
           
            ret = lets.renew_lest_cert(data)
            if ret['status']:
                result['sucess_list'].append(siteName)
            else:
                result['err_list'].append({"siteName":siteName,"msg":ret['msg']})
        return result;
    