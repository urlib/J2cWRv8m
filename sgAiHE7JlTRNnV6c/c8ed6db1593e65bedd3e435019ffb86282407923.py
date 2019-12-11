# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.

# +-------------------------------------------------------------------
import os
import sys
sys.path.append("class/")
import public
import db
import json
import time
import binascii 
import base64,system
from BTPanel import session
   
 
class btpatch_main:
    __setupPath = 'plugin/btpatch';
    __panelPath = os.getenv("BT_PANEL")

    __server_version = None;
    def __init__(self):
        import system
        self.__server_version = system.system().GetSystemVersion()


     #获取列表
    def get_list(self,get):
        self.get_cloud_list(get);
        jsonFile = self.__setupPath + '/list.json';
        if not os.path.exists(jsonFile): return public.returnMsg(False,'配置文件不存在!');
        data = {}
        data = json.loads(public.readFile(jsonFile));
        
        systeminfo = public.ExecShell('systeminfo | findstr KB',None,None,None,True)
        result = []
        for info in data:
            info['status'] = False
           
            downurl = "";
            for version in info['os']:
                if self.__server_version.lower().find(version.lower()) >= 0:
                    if version in info["downurl"]:                         
                       downurl = info["downurl"][version]     
                       if type(downurl) != str:
                           downurl = "|".join(downurl)
                    if type(info['patch']) != str:
                        info['patch'] = info['patch'][version]
                    break;
            if systeminfo[0].find(info['patch']) >=0 : info['status'] = True
            info["downurl"] = downurl
            result.append(info);
            print(result)
        return result;

    #安装补丁
    def setup_patch(self,get):
        url = get.url
        patch = get.patch;

        if not url:
            return public.returnMsg(False,'不在影响范围或未找到相应的补丁.');
        tmpPath = "C:/Temp/" + patch + ".msu"
        public.downloadFile(url,tmpPath)
        if not os.path.exists(tmpPath):
            return public.returnMsg(False,'补丁下载失败，请检查网络原因。');
        os.system("wusa.exe %s /quiet " % (tmpPath.replace("/","\\")))

        result = public.ExecShell('systeminfo | findstr KB',None,None,None,True)

        if result[0].find(patch) >=0 :
            return public.returnMsg(True,'安装补丁【'+ patch + '】成功');
        return public.returnMsg(False,'安装失败，请检查系统是否关闭更新，或手动运行【'+tmpPath+'】进行安装。');

        #从云端获取列表
    def get_cloud_list(self,get):
        try:
            jsonFile = self.__setupPath + '/list.json'
            if not 'patch' in session or not os.path.exists(jsonFile):
                downloadUrl = public.get_url() + '/win/install/plugin/btpatch/list.json';
         
                tmp = json.loads(public.httpGet(downloadUrl,3));

                if not tmp: return public.returnMsg(False,'从云端获取失败!');
                
                public.writeFile(jsonFile,json.dumps(tmp));
                
                session['patch'] = True
                return public.returnMsg(True,'更新成功!');
            return public.returnMsg(True,'无需更新!');
        except:
            return public.returnMsg(False,'从云端获取失败!');