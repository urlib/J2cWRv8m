#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

import public,os,sys,binascii,urllib,json,time,datetime
import requests
from OpenSSL import crypto

class CloudxnsDns(object):
    def __init__(self, key, secret, ):
        self.key = key
        self.secret = secret
        self.APIREQUESTDATE = time.ctime()

    def extract_zone(self,domain_name):
        domain_name = domain_name.lstrip("*.")
        if domain_name.count(".") > 1:
            zone, middle, last = str(domain_name).rsplit(".", 2)
            root = ".".join([middle, last])
            acme_txt = "_acme-challenge.%s" % zone
        else:
            zone = ""
            root = domain_name
            acme_txt = "_acme-challenge"
        return root, zone, acme_txt

    def get_headers(self, url, parameter=''):
        APIREQUESTDATE = self.APIREQUESTDATE
        APIHMAC = public.Md5(self.key + url + parameter + APIREQUESTDATE + self.secret)
        headers = {
            "API-KEY": self.key,
            "API-REQUEST-DATE": APIREQUESTDATE,
            "API-HMAC": APIHMAC,
            "API-FORMAT": "json"
        }
        return headers

    def get_domain_list(self):
        url = "https://www.cloudxns.net/api2/domain"
        headers = self.get_headers(url)
        req = requests.get(url=url, headers=headers,verify=False)
        req = req.json()
        
        return req

    def get_domain_id(self, domain_name):
        req = self.get_domain_list()
        for i in req["data"]:
            if domain_name.strip() == i['domain'][:-1]:
                return i['id']
        return False

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = self.extract_zone(domain_name)
        domain = self.get_domain_id(root)
        if not domain:
            raise ValueError('域名不存在这个cloudxns用户下面，添加解析失败。')

        print("create_dns_record,", acme_txt, domain_dns_value)
        url = "https://www.cloudxns.net/api2/record"
        data = {
            "domain_id": int(domain),
            "host": acme_txt,
            "value": domain_dns_value,
            "type": "TXT",
            "line_id": 1,
        }
        parameter = json.dumps(data)
        headers = self.get_headers(url, parameter)
        req = requests.post(url=url, headers=headers, data=parameter,verify=False)
        req = req.json()
       
        print("create_dns_record_end")
        return req

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = self.extract_zone(domain_name)
        print("delete_dns_record start: ", acme_txt, domain_dns_value)
        url = "https://www.cloudxns.net/api2/record/{}/{}".format(self.get_record_id(root), self.get_domain_id(root))
        headers = self.get_headers(url, )
        req = requests.delete(url=url, headers=headers,verify=False )
        req = req.json()
        print("delete_dns_record_success")
        return req

    def get_record_id(self, domain_name):
        url = "http://www.cloudxns.net/api2/record/{}?host_id=0&offset=0&row_num=2000".format(self.get_domain_id(domain_name))
        headers = self.get_headers(url, )
        req = requests.get(url=url, headers=headers,verify=False )
        req = req.json()
        for i in req['data']:
            if i['type'] == "TXT":
                return i['record_id']
        return False

class Dns_com(object):

    def extract_zone(self,domain_name):
        domain_name = domain_name.lstrip("*.")
        if domain_name.count(".") > 1:
            zone, middle, last = str(domain_name).rsplit(".", 2)
            root = ".".join([middle, last])
            acme_txt = "_acme-challenge.%s" % zone
        else:
            zone = ""
            root = domain_name
            acme_txt = "_acme-challenge"
        return root, zone, acme_txt
    
    def get_dns_obj(self):
        p_path = 'plugin/dns'
        if not os.path.exists(p_path +'/dns_main.py'): return None
        sys.path.insert(0,p_path)
        import dns_main
        return dns_main.dns_main()

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = self.extract_zone(domain_name)
        print("[DNS]创建TXT记录,", acme_txt, domain_dns_value)
        result = self.get_dns_obj().add_txt(acme_txt + '.' + root,domain_dns_value)
        if result == "False":
            raise ValueError('[DNS]当前绑定的宝塔DNS云解析账户里面不存在这个域名,添加解析失败!')
        print("[DNS]TXT记录创建成功")
        print("[DNS]尝试验证TXT记录")
        time.sleep(10)

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = self.extract_zone(domain_name)
        print("[DNS]准备删除TXT记录: ", acme_txt, domain_dns_value)
        result = self.get_dns_obj().remove_txt(acme_txt + '.' + root)
        print("[DNS]TXT记录删除成功")
