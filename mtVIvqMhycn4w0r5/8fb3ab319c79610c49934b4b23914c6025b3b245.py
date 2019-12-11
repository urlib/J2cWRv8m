#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

import os,sys,binascii,urllib,json,time,datetime
setup_path = os.getenv("BT_PANEL")
os.chdir(setup_path)
sys.path.insert(0,setup_path + "/class/")
import requests,sewer,public,re
from OpenSSL import crypto

if __name__ != "__main__":
    import BTPanel

class panelLets:
    let_url = "https://acme-v02.api.letsencrypt.org/directory"
    #let_url = "https://acme-staging-v02.api.letsencrypt.org/directory"

    setupPath = None #安装路径  
    server_type = None
    
    #构造方法
    def __init__(self):
        self.setupPath = public.GetConfigValue('setup_path')
        self.server_type = public.get_webserver()
    
    #拆分根证书
    def split_ca_data(self,cert):
        datas = cert.split('-----END CERTIFICATE-----')
        return {"cert":datas[0] + "-----END CERTIFICATE-----\n","ca_data":datas[1] + '-----END CERTIFICATE-----\n' }

    #证书转为pkcs12
    def dump_pkcs12(self,key_pem=None,cert_pem = None, ca_pem=None, friendly_name=None):
        p12 = crypto.PKCS12()
        if cert_pem:
            ret = p12.set_certificate(crypto.load_certificate(crypto.FILETYPE_PEM, cert_pem.encode()))
            assert ret is None
        if key_pem:
            ret = p12.set_privatekey(crypto.load_privatekey(crypto.FILETYPE_PEM, key_pem.encode()))
            assert ret is None
        if ca_pem:
            ret = p12.set_ca_certificates((crypto.load_certificate(crypto.FILETYPE_PEM, ca_pem.encode()),) )
        if friendly_name:
            ret = p12.set_friendlyname(friendly_name.encode())
        return p12  

    #域名编码转换
    def ToPunycode(self,domain):
        import re;
        tmp = domain.split('.');
        newdomain = '';
        for dkey in tmp:
            #匹配非ascii字符
            match = re.search(u"[\x80-\xff]+",dkey);
            if not match: match = re.search(u"[\u4e00-\u9fa5]+",dkey);
            if not match:
                newdomain += dkey + '.';
            else:
                newdomain += 'xn--' + dkey.encode('punycode').decode('utf-8') + '.'
        return newdomain[0:-1];

    #punycode 转中文
    def DePunycode(self,domain):
        tmp = domain.split('.');
        newdomain = '';
        for dkey in tmp:
            if dkey.find('xn--') >=0:
                newdomain += dkey.replace('xn--','').encode('utf-8').decode('punycode') + '.'
            else:
                newdomain += dkey + '.'
        return newdomain[0:-1];

    #获取根域名
    def get_root_domain(self,domain_name):
        if domain_name.count(".") != 1:  
            pos = domain_name.rfind(".", 0, domain_name.rfind("."))
            subd = domain_name[:pos]
            domain_name =  domain_name[pos + 1 :]
        return domain_name
    
    #获取acmename
    def get_acme_name(self,domain_name):
        domain_name = domain_name.lstrip("*.")
        if domain_name.count(".") > 1:
            zone, middle, last = str(domain_name).rsplit(".", 2)
            root = ".".join([middle, last])
            acme_name = "_acme-challenge.%s.%s" % (zone,root)
        else:          
            root = domain_name
            acme_name = "_acme-challenge.%s" % root
        return acme_name

    #格式化错误输出
    def get_error(self,error):
        if error.find("Max checks allowed") >= 0 :
            return "CA无法验证您的域名，请检查域名解析是否正确，或等待5-10分钟后重试."
        elif error.find("Max retries exceeded with") >= 0:
            return "CA服务器连接超时，请稍候重试."
        elif error.find("The domain name belongs") >= 0:
            return "域名不属于此DNS服务商，请确保域名填写正确."
        elif error.find('login token ID is invalid') >=0:
            return 'DNS服务器连接失败，请检查密钥是否正确.'
        elif "too many certificates already issued for exact set of domains" in error:
            return '签发失败,该域名%s超出了每周的重复签发次数限制!' % re.findall("exact set of domains: (.+):",error)
        elif "Error creating new account :: too many registrations for this IP" in error:
            return '签发失败,当前服务器IP已达到每3小时最多创建10个帐户的限制.'
        elif "DNS problem: NXDOMAIN looking up A for" in error:
            return '验证失败,没有解析域名,或解析未生效!'
        elif "Invalid response from" in error:
            return '验证失败,域名解析错误或验证URL无法被访问!'
        elif error.find('TLS Web Server Authentication') != -1:
            public.restart_panel()
            return "连接CA服务器失败，请稍候重试."
        elif error.find('Name does not end in a public suffix') !=-1:
            return "不支持的域名%s，请检查域名是否正确!" % re.findall("Cannot issue for \"(.+)\":",error)
        elif error.find('No valid IP addresses found for') != -1:
            return "域名%s没有找到解析记录，请检查域名是否解析生效!" % re.findall("No valid IP addresses found for (.+)",error)
        elif error.find('No TXT record found at') != -1:
            return "没有在域名%s中找到有效的TXT解析记录,请检查是否正确解析TXT记录,如果是DNSAPI方式申请的,请10分钟后重试!" % re.findall("No TXT record found at (.+)",error)
        elif error.find('Incorrect TXT record') != -1:
            return "在%s上发现错误的TXT记录:%s,请检查TXT解析是否正确,如果是DNSAPI方式申请的,请10分钟后重试!" % (re.findall("found at (.+)",error),re.findall("Incorrect TXT record \"(.+)\"",error))
        elif error.find('Domain not under you or your user') != -1:
            return "这个dnspod账户下面不存在这个域名，添加解析失败!"
        elif error.find('SERVFAIL looking up TXT for') != -1:
            return "没有在域名%s中找到有效的TXT解析记录,请检查是否正确解析TXT记录,如果是DNSAPI方式申请的,请10分钟后重试!" % re.findall("looking up TXT for (.+)",error)
        elif error.find('Timeout during connect') != -1:
            return "连接超时,CA服务器无法访问您的网站!"
        elif error.find("DNS problem: SERVFAIL looking up CAA for") != -1:
            return "域名%s当前被要求验证CAA记录，请手动解析CAA记录，或1小时后重新尝试申请!" % re.findall("looking up CAA for (.+)",error)
        else:
            return error;

    #获取DNS服务器
    def get_dns_class(self,data):
        if data['dnsapi'] == 'dns_ali':
            try:
                dns_class = sewer.AliyunDns(key = data['dns_param'][0], secret = data['dns_param'][1])
            except :            
                os.system(public.get_run_pip("[PIP] install sewer[aliyun]"))          
                dns_class = sewer.AliyunDns(key = data['dns_param'][0], secret = data['dns_param'][1])
            return dns_class
        elif data['dnsapi'] == 'dns_dp':
            dns_class = sewer.DNSPodDns(DNSPOD_ID = data['dns_param'][0] ,DNSPOD_API_KEY = data['dns_param'][1])
            return dns_class
        elif data['dnsapi'] == 'dns_cx':   
            import panelDnsapi
            public.mod_reload(panelDnsapi)
            dns_class = panelDnsapi.CloudxnsDns(key = data['dns_param'][0] ,secret =data['dns_param'][1])
            result = dns_class.get_domain_list()
            if result['code'] == 1:                
                return dns_class
        elif data['dnsapi'] == 'dns_bt':
            import panelDnsapi
            public.mod_reload(panelDnsapi)
            dns_class = panelDnsapi.Dns_com()
            return dns_class
        return False

    #续签证书
    def renew_lest_cert(self,data):  
        
        #续签网站
        path = self.setupPath + '/panel/vhost/cert/'+ data['siteName'];
        if not os.path.exists(path):  return public.returnMsg(False, '续签失败,证书目录不存在.') 

        account_path = path + "/account_key.key"
        if not os.path.exists(account_path): return public.returnMsg(False, '续签失败,缺少account_key.') 

        #续签
        data['account_key'] = public.readFile(account_path)

        if not 'first_domain' in data:  data['first_domain'] = data['domains'][0]

        if 'dnsapi' in data:                
            certificate = self.crate_let_by_dns(data)
        else:            
            certificate = self.crate_let_by_file(data)       

        if not certificate['status']: return public.returnMsg(False, certificate['msg'])
                 
        #存储证书
        public.writeFile(path + "/privkey.pem",certificate['key'])
        public.writeFile(path + "/fullchain.pem",certificate['cert'] + certificate['ca_data'])
        public.writeFile(path + "/account_key.key", certificate['account_key']) #续签KEY

        #转为IIS证书
        p12 = self.dump_pkcs12(certificate['key'], certificate['cert'] + certificate['ca_data'],certificate['ca_data'],data['first_domain'])
        pfx_buffer = p12.export()
        public.writeFile2(path + "/fullchain.pfx",pfx_buffer,'wb+')

        #iis多证书处理
        pfx_name = data['first_domain'].replace("*","_")
        public.writeFile2(path + "/"+ pfx_name +".pfx",pfx_buffer,'wb+')

        #更新证书
        ret = self.set_cert_data(data['siteName'])
        if ret['status']:  
            return public.returnMsg(True, '[%s]证书续签成功.' % data['siteName']) 
        return public.returnMsg(False, '[%s]证书续签失败.' % data['siteName']) 

    #申请证书
    def apple_lest_cert(self,get):
   
        data = {}        
        data['siteName'] = get.siteName
        data['domains'] = json.loads(get.domains)
        data['email'] = get.email
        data['dnssleep'] = get.dnssleep
             
        if len(data['domains']) <=0 : return public.returnMsg(False, '申请域名列表不能为空.')
        
        data['first_domain'] = data['domains'][0]       
     
        path = self.setupPath + '/panel/vhost/cert/'+ data['siteName'];
        if not os.path.exists(path): os.makedirs(path)

        # 检查是否自定义证书
        partnerOrderId = path + '/partnerOrderId';
        if os.path.exists(partnerOrderId): os.remove(partnerOrderId)
        #清理续签key
        re_key = path + '/account_key.key';
        if os.path.exists(re_key): os.remove(re_key)

        re_password = path + '/password';
        if os.path.exists(re_password): os.remove(re_password)
        
        data['account_key'] = None   
        if hasattr(get, 'dnsapi'): 
            data['app_root'] = get.app_root   
            domain_list = data['domains']
            if data['app_root'] == '1':
                domain_list = []
                data['first_domain'] = self.get_root_domain(data['first_domain'])               

                for domain in data['domains']:
                    rootDoamin = self.get_root_domain(domain)
                    if not rootDoamin in domain_list: domain_list.append(rootDoamin)
                    if not "*." + rootDoamin in domain_list: domain_list.append("*." + rootDoamin)
                data['domains'] = domain_list

            if get.dnsapi == 'dns':     
                domain_path = path + '/domain_txt_dns_value.json'
                if hasattr(get, 'renew'): #验证
                    data['renew'] = True
                    dns = json.loads(public.readFile(domain_path))
                    data['dns'] = dns
                  
                    certificate = self.crate_let_by_oper(data)
                else:
                   
                    #手动解析提前返回
                    result = self.crate_let_by_oper(data)
                    if 'status' in result and not result['status']:  return result

                    result['status'] = True
                    public.writeFile(domain_path, json.dumps(result)) 
                    result['msg'] = '获取成功,请手动解析域名'
                    result['code'] = 2;

                    return result
            elif get.dnsapi == 'dns_bt':
                data['dnsapi'] = get.dnsapi
                certificate = self.crate_let_by_dns(data)
            else:
                data['dnsapi'] = get.dnsapi
                data['dns_param'] = get.dns_param.split('|')
                certificate = self.crate_let_by_dns(data)
        else:
            #文件验证
            data['site_dir'] = get.site_dir;     
            certificate = self.crate_let_by_file(data)       

        if not certificate['status']: return public.returnMsg(False, certificate['msg'])
        
        #保存续签
        cpath = self.setupPath + '/panel/vhost/crontab.json'
        config = {}
        if os.path.exists(cpath):
            config = json.loads(public.readFile(cpath))
        config[data['siteName']] = data
        public.writeFile(cpath,json.dumps(config))

        #存储证书
        public.writeFile(path + "/privkey.pem",certificate['key'])
        public.writeFile(path + "/fullchain.pem",certificate['cert'] + certificate['ca_data'])
        public.writeFile(path + "/account_key.key",certificate['account_key']) #续签KEY

        #转为IIS证书
        p12 = self.dump_pkcs12(certificate['key'], certificate['cert'] + certificate['ca_data'],certificate['ca_data'],data['first_domain'])
        pfx_buffer = p12.export()
        public.writeFile2(path + "/fullchain.pfx",pfx_buffer,'wb+')        
        public.writeFile(path + "/README","let") 
        
        #计划任务续签
        echo = public.md5(public.md5('renew_lets_ssl_bt'))
        crontab = public.M('crontab').where('echo=?',(echo,)).find()
        if not crontab:
            cronPath = public.GetConfigValue('setup_path') + '/cron/' + echo    
            shell = public.get_run_python('[PYTHON] -u %s/panel/class/panelLets.py renew_lets_ssl ' % (self.setupPath))
            public.writeFile(cronPath,shell)
            public.M('crontab').add('name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sType,sName,sBody,urladdress',("续签Let's Encrypt证书",'day','','0','10',echo,time.strftime('%Y-%m-%d %X',time.localtime()),1,'','localhost','toShell','',shell,''))
        
        return public.returnMsg(True, '申请成功.')

    #手动解析
    def crate_let_by_oper(self,data):
        result = {}
        result['status'] = False
        try:                      
            #手动解析记录值
            if not 'renew' in data:
                BTPanel.dns_client = sewer.Client(domain_name = data['first_domain'],dns_class = None,account_key = data['account_key'],domain_alt_names = data['domains'],contact_email = str(data['email']) ,ACME_AUTH_STATUS_WAIT_PERIOD = 15,ACME_AUTH_STATUS_MAX_CHECKS = 5,ACME_REQUEST_TIMEOUT = 20,ACME_DIRECTORY_URL = self.let_url)

                domain_dns_value = "placeholder"
                dns_names_to_delete = []

                BTPanel.dns_client.acme_register()
                authorizations, finalize_url = BTPanel.dns_client.apply_for_cert_issuance()
                responders = []
                for url in authorizations:
                    identifier_auth = BTPanel.dns_client.get_identifier_authorization(url)
                    authorization_url = identifier_auth["url"]
                    dns_name = identifier_auth["domain"]
                    dns_token = identifier_auth["dns_token"]
                    dns_challenge_url = identifier_auth["dns_challenge_url"]

                    acme_keyauthorization, domain_dns_value = BTPanel.dns_client.get_keyauthorization(dns_token)
                 
                    acme_name = self.get_acme_name(dns_name)

                    dns_name = self.DePunycode(dns_name)      
                    acme_name = self.DePunycode(acme_name)     

                    dns_names_to_delete.append({"dns_name": dns_name,"acme_name":acme_name, "domain_dns_value": domain_dns_value})
                    responders.append(
                        {
                            "authorization_url": authorization_url,
                            "acme_keyauthorization": acme_keyauthorization,
                            "dns_challenge_url": dns_challenge_url
                        }
                    )
             
                dns = {}
                dns['dns_names'] = dns_names_to_delete
                dns['responders'] = responders
                dns['finalize_url'] = finalize_url

                dns['certificate_key'] = BTPanel.dns_client.certificate_key           
                dns['account_key'] = BTPanel.dns_client.account_key
               
                return dns
            else:
                dns = data['dns']                
                responders = dns['responders']
                dns_names_to_delete = dns['dns_names']
                finalize_url = dns['finalize_url']

                for i in responders:                    
                    auth_status_response = BTPanel.dns_client.check_authorization_status(i["authorization_url"])
                    if auth_status_response.json()["status"] == "pending":
                         BTPanel.dns_client.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])

                for i in responders:
                    BTPanel.dns_client.check_authorization_status(i["authorization_url"], ["valid"])

                certificate_url = BTPanel.dns_client.send_csr(finalize_url)
                certificate = BTPanel.dns_client.download_certificate(certificate_url)

                if certificate:
                    certificate = self.split_ca_data(certificate)
                    result['cert'] = certificate['cert']
                    result['ca_data'] = certificate['ca_data']
                    result['key'] = BTPanel.dns_client.certificate_key
                    result['account_key'] = BTPanel.dns_client.account_key
                    result['status'] = True
                else:
                    result['msg'] = '证书获取失败，请稍后重试.'
                BTPanel.dns_client = None
        except Exception as e:
            print(str(e))
            result['msg'] =  self.get_error(str(e)) 
        return result
    

    #dns验证
    def crate_let_by_dns(self,data):        
        dns_class = self.get_dns_class(data)  
        if not dns_class: 
            return public.returnMsg(False, 'DNS连接失败，请检查密钥是否正确.')
     
        result = {}
        result['status'] = False
        try:
            log_level = "INFO"
            if data['account_key']: log_level = 'ERROR'
 
            client = sewer.Client(domain_name = data['first_domain'],domain_alt_names = data['domains'],account_key = data['account_key'],contact_email = data['email'],LOG_LEVEL = log_level,ACME_AUTH_STATUS_WAIT_PERIOD = 15,ACME_AUTH_STATUS_MAX_CHECKS = 5,ACME_REQUEST_TIMEOUT = 20, dns_class = dns_class,ACME_DIRECTORY_URL = self.let_url)

            domain_dns_value = "placeholder"
            dns_names_to_delete = []
            try:
                client.acme_register()
                authorizations, finalize_url = client.apply_for_cert_issuance()
                
                responders = []
                for url in authorizations:
                    identifier_auth = client.get_identifier_authorization(url)
                    authorization_url = identifier_auth["url"]
                    dns_name = identifier_auth["domain"]
                    dns_token = identifier_auth["dns_token"]
                    dns_challenge_url = identifier_auth["dns_challenge_url"]

                    acme_keyauthorization, domain_dns_value = client.get_keyauthorization(dns_token)

                    dns_name = self.DePunycode(dns_name)                   
                    dns_class.create_dns_record(dns_name, domain_dns_value)
                    acme_name = self.get_acme_name(dns_name)
                    dns_names_to_delete.append({"dns_name": dns_name, "domain_dns_value": domain_dns_value})
                    responders.append({"authorization_url": authorization_url, "acme_keyauthorization": acme_keyauthorization,"dns_challenge_url": dns_challenge_url} )               
                    self.check_dns(acme_name,domain_dns_value)

                #n = 0
                #while n < 3:
                    #print("nslookup_check_" + str(n))
                try:
                    for i in responders:     
                        auth_status_response = client.check_authorization_status(i["authorization_url"])
                        r_data = auth_status_response.json()
                        if r_data["status"] == "pending":
                            client.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])

    
                    for i in responders: client.check_authorization_status(i["authorization_url"], ["valid"])
                    print("nslookup_check_sucess")
                    #break
                except Exception as e:                        
                    for i in responders:     
                        auth_status_response = client.check_authorization_status(i["authorization_url"])
                        r_data = auth_status_response.json()
                        if r_data["status"] == "pending":
                            client.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])

    
                    for i in responders: client.check_authorization_status(i["authorization_url"], ["valid"])
                    print("nslookup_check_sucess")  

                certificate_url = client.send_csr(finalize_url)
                certificate = client.download_certificate(certificate_url)

                if certificate:
                    certificate = self.split_ca_data(certificate)
                    result['cert'] = certificate['cert']
                    result['ca_data'] = certificate['ca_data']
                    result['key'] = client.certificate_key
                    result['account_key'] = client.account_key
                    result['status'] = True
            except Exception as e:               
                raise e
            finally: 
               
                try:
                    for i in dns_names_to_delete: 
                        print(i["dns_name"], i["domain_dns_value"])
                        dns_class.delete_dns_record(i["dns_name"], i["domain_dns_value"])
                except :
                    pass

        except Exception as err:  
            print(str(err))
            result['msg'] =  self.get_error(str(err)) 
        return result

    #文件验证
    def crate_let_by_file(self,data):
        result = {}
        result['status'] = False
        result['clecks'] = []
        try:
            log_level = "INFO"
            if data['account_key']: log_level = 'ERROR'

            client = sewer.Client(domain_name = data['first_domain'],dns_class = None,account_key = data['account_key'],domain_alt_names = data['domains'],contact_email = data['email'],LOG_LEVEL = log_level,ACME_AUTH_STATUS_WAIT_PERIOD = 15,ACME_AUTH_STATUS_MAX_CHECKS = 5,ACME_REQUEST_TIMEOUT = 20,ACME_DIRECTORY_URL = self.let_url)
            
            client.acme_register()
            authorizations, finalize_url = client.apply_for_cert_issuance()
            responders = []
            sucess_domains = []
            for url in authorizations:
                identifier_auth = self.get_identifier_authorization(client,url)
             
                authorization_url = identifier_auth["url"]
                http_name = identifier_auth["domain"]
                http_token = identifier_auth["http_token"]
                http_challenge_url = identifier_auth["http_challenge_url"]

                acme_keyauthorization, domain_http_value = client.get_keyauthorization(http_token)   

                acme_dir = '%s/.well-known/acme-challenge' % (data['site_dir']);
                if not os.path.exists(acme_dir): os.makedirs(acme_dir)
               
                #写入token
                wellknown_path = acme_dir + '/' + http_token
                public.writeFile(wellknown_path,acme_keyauthorization)              
                wellknown_url = "http://{0}/.well-known/acme-challenge/{1}".format(http_name, http_token)   
                
                result['clecks'].append({'wellknown_url':wellknown_url,'http_token':http_token});
                is_check = False
                n = 0
                while n < 5:
                    print("wait_check_authorization_status")
                    try:                       
                        retkey = public.httpGet(wellknown_url,20)     
                        if retkey == acme_keyauthorization:
                            is_check = True
                            break;
                    except :
                        pass
                    n += 1;
                    time.sleep(10)
                #if is_check:                    
                sucess_domains.append(http_name) 
                responders.append({"authorization_url": authorization_url, "acme_keyauthorization": acme_keyauthorization,"http_challenge_url": http_challenge_url})

            if len(sucess_domains) > 0: 
                #验证
                for i in responders:
                    auth_status_response = client.check_authorization_status(i["authorization_url"])          
                    if auth_status_response.json()["status"] == "pending":
                        client.respond_to_challenge(i["acme_keyauthorization"], i["http_challenge_url"])

                for i in responders:
                    client.check_authorization_status(i["authorization_url"], ["valid"])

                certificate_url = client.send_csr(finalize_url)
                certificate = client.download_certificate(certificate_url)
               
                if certificate:
                    certificate = self.split_ca_data(certificate)
                    result['cert'] = certificate['cert']
                    result['ca_data'] = certificate['ca_data']
                    result['key'] = client.certificate_key
                    result['account_key'] = client.account_key
                    result['status'] = True
                else:
                    result['msg'] = '证书获取失败，请稍后重试.'
            else:
                result['msg'] = "签发失败,我们无法验证您的域名:<p>1、检查域名是否绑定到对应站点</p><p>2、检查域名是否正确解析到本服务器,或解析还未完全生效</p><p>3、如果您的站点设置了反向代理,或使用了CDN,请先将其关闭</p><p>4、如果您的站点设置了301重定向,请先将其关闭</p><p>5、如果之前申请不通过CA服务器将会存在缓存，请等待3小时候重试。</><p>6、如果以上检查都确认没有问题，请尝试更换DNS服务商"
        except Exception as e:
            result['msg'] =  self.get_error(str(e)) 
        return result

    #检查DNS记录
    def check_dns(self,domain,value,type='TXT'):
        try:
            import dns.resolver
        except :
            os.system(public.get_run_pip("[PIP] install dnspython"))            
            import dns.resolver
        time.sleep(5)
        n = 0
        while n < 10:
            try:
                import dns.resolver
                ns = dns.resolver.query(domain,type)
                for j in ns.response.answer:
                    for i in j.items:
                        txt_value = i.to_text().replace('"','').strip()           
                        if txt_value == value:                           
                            return True
            except:
                pass
            n += 1
            time.sleep(6)
        return True

    def get_identifier_authorization(self,client, url):
        
        print('identifier_authorization')
        headers = {"User-Agent": client.User_Agent}
        get_identifier_authorization_response = requests.get(url, timeout = client.ACME_REQUEST_TIMEOUT, headers=headers,verify=False)
       
        if get_identifier_authorization_response.status_code not in [200, 201]:
            raise ValueError("Error getting identifier authorization: status_code={status_code}".format(status_code=get_identifier_authorization_response.status_code ) )
        res = get_identifier_authorization_response.json()
        domain = res["identifier"]["value"]
        wildcard = res.get("wildcard")
        if wildcard:
            domain = "*." + domain

        for i in res["challenges"]:
            if i["type"] == "http-01":
                http_challenge = i
        http_token = http_challenge["token"]
        http_challenge_url = http_challenge["url"]
        identifier_auth = {
            "domain": domain,
            "url": url,
            "wildcard": wildcard,
            "http_token": http_token,
            "http_challenge_url": http_challenge_url,
        }
        print('identifier_authorization_sucess')
        return identifier_auth

    #部署证书文件
    def set_cert_data(self,siteName):
        serverType = public.get_webserver()    
        old_path = self.setupPath + '/panel/vhost/cert/'+ siteName

        if serverType == 'iis':
            public.ExecShell('netsh http delete sslcert hostnameport='+ siteName +':443')
            public.ExecShell('netsh http delete sslcert ipport=0.0.0.0:443')

            #导入
            pfx_path = old_path + '/fullchain.pfx'
            data = self.get_cert_data(pfx_path)
            if not data: return public.returnMsg(False,'证书解析错误.')
                            
            rest = public.ExecShell('certutil -p "" -importPFX ' + pfx_path)
            import uuid
            appid = str(uuid.uuid1())
            bind_exec = 'netsh http add sslcert hostnameport=' + siteName + ':443 certhash='+ data['hash'] +' certstorename=MY appid={' + appid + '}'
            sys_versions = public.get_sys_version()      
            if int(sys_versions[0]) == 6 and int(sys_versions[1]) == 1:
                bind_exec = 'netsh http add sslcert ipport=0.0.0.0:443 certhash='+ data['hash'] +' appid={' + appid + '}'
            public.ExecShell(bind_exec)              
            return public.returnMsg(True,'更新证书成功.')
        else:
            if serverType == 'apache':
                path = self.setupPath + '/apache/conf/ssl/' + siteName 
                if not os.path.exists(path): os.makedirs(path)
            else:
                path = self.setupPath + '/nginx/conf/ssl/' + siteName 
                if not os.path.exists(path): os.makedirs(path)
            #替换证书文件
            if os.path.exists(old_path + '/fullchain.pem'):
                old_pem = public.readFile(old_path + '/fullchain.pem')
                public.writeFile(path + "/fullchain.pem",old_pem)
           
            if os.path.exists(old_path + '/privkey.pem'):
                old_pem = public.readFile(old_path + '/privkey.pem')
                public.writeFile(path + "/privkey.pem",old_pem)

            return public.returnMsg(True,'更新证书成功.')

    #获取证书哈希
    def get_cert_data(self,path):
        try:
            if path[-4:] == '.pfx':   
                f = open(path,'rb') 
                pfx_buffer = f.read() 
                p12 = crypto.load_pkcs12(pfx_buffer,'')
                x509 = p12.get_certificate()
            else:
                cret_data = public.readFile(path)
                x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cret_data)
            
            buffs = x509.digest('sha1')
            hash =  bytes.decode(buffs).replace(':','')
            data = {}
            data['hash'] = hash
            data['timeout'] = bytes.decode(x509.get_notAfter())[:-1]
            return data
        except :
            return False      

    #验证证书哈希
    def get_site_cert_hasdata(self,siteName):
        serverType = public.get_webserver()           
        if serverType == 'iis':  
            import re
            sys_versions = public.get_sys_version()
            bind_exec = 'netsh http show sslcert hostnameport=' + siteName + ':443'                          
            if int(sys_versions[0]) == 6 and int(sys_versions[1]) == 1:
                bind_exec = 'netsh http show sslcert ipport=0.0.0.0:443'                
            rRet = public.ExecShell(bind_exec)     
            hashStr = re.search(':\s+(\w{40})',rRet[0]).groups()[0].upper()          
            return hashStr
        elif serverType == 'apache':
            npath =  self.setupPath + '/apache/conf/ssl/' + siteName + '/fullchain.pem'
            hashStr = self.get_cert_hash_bypath(npath)
            return hashStr
        else:
            npath =  self.setupPath + '/nginx/conf/ssl/' + siteName + '/fullchain.pem'
            hashStr = self.get_cert_hash_bypath(npath)
            return hashStr
        return False

    #获取快过期的证书
    def get_renew_lets_bytimeout(self,cron_list):
        tday = 30
        path = self.setupPath + '/panel/vhost/cert'      
        nlist = {}
        new_list = {}
        for siteName in cron_list:   
            spath =  path + '/' + siteName
            #验证是否存在续签KEY
            if os.path.exists(spath + '/account_key.key'):
                if public.M('sites').where("name=?",(siteName,)).count():        
                    new_list[siteName] = cron_list[siteName]
                    data = self.get_cert_data(self.setupPath + '/panel/vhost/cert/' + siteName + '/fullchain.pem')
                    hash = self.get_site_cert_hasdata(siteName)
               
                    if hash == data['hash']:                                       
                        timeout = int(time.mktime(time.strptime(data['timeout'],'%Y%m%d%H%M%S')))
                        eday = (timeout - int(time.time())) / 86400                          
                        if eday < 30:                                            
                            nlist[siteName] = cron_list[siteName]
        #清理过期配置
        public.writeFile(self.setupPath + '/panel/vhost/crontab.json',json.dumps(new_list))
        return nlist

    #===================================== 计划任务续订证书 =====================================#
    #续订
    def renew_lets_ssl(self):        
        cpath = self.setupPath + '/panel/vhost/crontab.json'
        if not os.path.exists(cpath):  
            print("|-当前没有可以续订的证书. " );        
        else:
            old_list = json.loads(public.ReadFile(cpath))    
            print('=======================================================================')
            print('|-%s 共计[%s]续签证书任务.' % (time.strftime('%Y-%m-%d %X',time.localtime()),len(old_list)))                        
            cron_list = self.get_renew_lets_bytimeout(old_list)

            tlist = []  
            for siteName in old_list:                 
                if not siteName in cron_list: tlist.append(siteName)                    
            print('|-[%s]未到期,网站未使用Let\'s Encrypt证书或未找到account_key.' % (','.join(tlist)))               
            print('|-%s 等待续签[%s].' % (time.strftime('%Y-%m-%d %X',time.localtime()),len(cron_list)))   
            
            sucess_list  = []
            err_list = []
            for siteName in cron_list:
                data = cron_list[siteName]
                ret = self.renew_lest_cert(data)
                if ret['status']:
                    sucess_list.append(siteName)
                else:
                    err_list.append({"siteName":siteName,"msg":ret['msg']})
            print("|-任务执行完毕，共需续订[%s]，续订成功[%s]，续订失败[%s]. " % (len(cron_list),len(sucess_list),len(err_list)));        
            if len(sucess_list) > 0:       
                print("|-续订成功：%s" % (','.join(sucess_list)))
            if len(err_list) > 0:       
                print("|-续订失败：")
                for x in err_list:
                    print("    %s ->> %s" % (x['siteName'],x['msg']))

            if len(sucess_list) > 0:
                print('|-%s 准备替换网站证书文件.' % (time.strftime('%Y-%m-%d %X',time.localtime())))              
                for siteName in sucess_list:
                    ret = self.set_cert_data(siteName)
                    msg = 'error'
                    if ret['status']:
                        msg = 'sucess'
                    print('|-%s --> %s' % (siteName,msg))
            print('=======================================================================')
            print(" ");

if __name__ == "__main__":

    if len(sys.argv) > 1:
        type = sys.argv[1]
        if type == 'renew_lets_ssl':
            panelLets().renew_lets_ssl()
