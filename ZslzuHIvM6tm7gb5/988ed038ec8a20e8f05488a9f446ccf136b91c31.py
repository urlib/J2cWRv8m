#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 黄文良 <287962566@qq.com>
# +-------------------------------------------------------------------

import sys,json,os,time
sys.path.append('class/')
from datetime import datetime
from flask import render_template,send_file,request,redirect,g,url_for
from BTPanel import app,session,cache,socketio
from flask_socketio import SocketIO,emit,send
#from runserver import socketio
import socket
import paramiko

import public,common,db
comm = common.panelAdmin()
method_all = ['GET','POST']
method_get = ['GET']
method_post = ['POST']
json_header = {'Content-Type':'application/json; charset=utf-8'}

@app.route('/',methods=method_all)
def home():
    comReturn = comm.local()
    if comReturn: return comReturn
    data = {}
    data['siteCount'] = public.M('sites').count()
    data['ftpCount'] = public.M('ftps').count()
    data['databaseCount'] = public.M('databases').count()
    data['lan'] = public.GetLan('index')
    return render_template(public.GetConfigValue('template') + '/index.html',data = data)

@app.route('/login',methods=method_all)
def login():
    comReturn = common.panelSetup().init()
    if comReturn: return comReturn
    import userlogin
    "登陆"
    if request.method == method_post[0]:
        return userlogin.userlogin().request_post(get_input())

    if request.method == method_get[0]:
        result = userlogin.userlogin().request_get(get_input())
        if result: return result
        data = {}
        data['lan'] = public.GetLan('login')
        return render_template(
            public.GetConfigValue('template') + '/login.html',
            data=data
            )

@app.route('/sites/<action>',methods=method_all)
@app.route('/sites',methods=method_all)
def sites(action = None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import sites
    siteObject = sites.sites()
    defs = ('create_site','remove_site','add_domain','remove_domain','open_ssl','close_ssl')
    return publicObject(siteObject,defs,action);

@app.route('/site',methods=method_all)
def site():
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        data = {}
        data['isSetup'] = True;
        data['lan'] = public.getLan('site');
        if os.path.exists(public.GetConfigValue('setup_path')+'/nginx') == False and os.path.exists(public.GetConfigValue('setup_path')+'/apache') == False: data['isSetup'] = False;
        return render_template( public.GetConfigValue('template') +'/site.html',data=data)
    import panelSite
    siteObject = panelSite.panelSite()
        
    defs = ('GetSiteLogs','GetSiteDomains','GetSecurity','SetSecurity','ProxyCache','CloseToHttps','HttpToHttps','SetEdate','SetRewriteTel','GetCheckSafe','CheckSafe','GetDefaultSite','SetDefaultSite','CloseTomcat','SetTomcat','apacheAddPort','AddSite','GetPHPVersion','SetPHPVersion','DeleteSite','AddDomain','DelDomain','GetDirBinding','AddDirBinding','GetDirRewrite','DelDirBinding'
            ,'UpdateRulelist','SetSiteRunPath','GetSiteRunPath','SetPath','SetIndex','GetIndex','GetDirUserINI','SetDirUserINI','GetRewriteList','SetSSL','SetSSLConf','CreateLet','CloseSSLConf','GetSSL','SiteStart','SiteStop'
            ,'Set301Status','Get301Status','CloseLimitNet','SetLimitNet','GetLimitNet','SetProxy','GetProxy','ToBackup','DelBackup','GetSitePHPVersion','logsOpen','GetLogsStatus','CloseHasPwd','SetHasPwd','GetHasPwd')
    return publicObject(siteObject,defs);

@app.route('/ftp',methods=method_all)
def ftp():
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        FtpPort()
        data = {}
        data['isSetup'] = True;
        if os.path.exists(public.GetConfigValue('setup_path') + '/pure-ftpd') == False: data['isSetup'] = False;
        data['lan'] = public.GetLan('ftp')
        return render_template( public.GetConfigValue('template') +'/ftp.html',data=data)
    import ftp
    ftpObject = ftp.ftp()
    defs = ('AddUser','DeleteUser','SetUserPassword','SetStatus','setPort')
    return publicObject(ftpObject,defs);

#取端口
def FtpPort():
    if session.get('port'):return
    import re
    try:
        file = public.GetConfigValue('setup_path')+'/pure-ftpd/etc/pure-ftpd.conf'
        conf = public.readFile(file)
        rep = "\n#?\s*Bind\s+[0-9]+\.[0-9]+\.[0-9]+\.+[0-9]+,([0-9]+)"
        port = re.search(rep,conf).groups()[0]
    except:
        port='21'
    session['port'] = port

@app.route('/database',methods=method_all)
def database():
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        pmd = get_phpmyadmin_dir();
        session['phpmyadminDir'] = False
        if pmd: 
            session['phpmyadminDir'] = 'http://' + public.GetHost() + ':'+ pmd[1] + '/' + pmd[0];
        data = {}
        data['isSetup'] = True;
        data['mysql_root'] = public.M('config').where('id=?',(1,)).getField('mysql_root');
        data['lan'] = public.GetLan('database')
        return render_template(public.GetConfigValue('template') +'/database.html',data=data)
    import database
    databaseObject = database.database()
    defs = ('GetSlowLogs','GetRunStatus','SetDbConf','GetDbStatus','BinLog','GetErrorLog','GetMySQLInfo','SetDataDir','SetMySQLPort','AddDatabase','DeleteDatabase','SetupPassword','ResDatabasePassword','ToBackup','DelBackup','InputSql','SyncToDatabases','SyncGetDatabases','GetDatabaseAccess','SetDatabaseAccess')
    return publicObject(databaseObject,defs);

def get_phpmyadmin_dir():
        path = public.GetConfigValue('setup_path') + '/phpmyadmin'
        if not os.path.exists(path): return None
        
        phpport = '888';
        try:
            import re;
            if session['webserver'] == 'nginx':
                filename =public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf';
                conf = public.readFile(filename);
                rep = "listen\s+([0-9]+)\s*;";
                rtmp = re.search(rep,conf);
                if rtmp:
                    phpport = rtmp.groups()[0];
            else:
                filename = public.GetConfigValue('setup_path') + '/apache/conf/extra/httpd-vhosts.conf';
                conf = public.readFile(filename);
                rep = "Listen\s+([0-9]+)\s*\n";
                rtmp = re.search(rep,conf);
                if rtmp:
                    phpport = rtmp.groups()[0];
        except:
            pass
            
        for filename in os.listdir(path):
            filepath = path + '/' + filename
            if os.path.isdir(filepath):
                if filename[0:10] == 'phpmyadmin':
                    return str(filename),phpport
        return None

@app.route('/control',methods=method_all)
def control():
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        data = {}
        data['lan'] = public.GetLan('control')
        return render_template( public.GetConfigValue('template') +'/control.html',data=data)

@app.route('/firewall',methods=method_all)
def firewall():
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        data = {}
        data['lan'] = public.GetLan('firewall')
        return render_template( public.GetConfigValue('template') +'/firewall.html',data=data)
    import firewalls
    firewallObject = firewalls.firewalls()
    defs = ('GetList','AddDropAddress','DelDropAddress','FirewallReload','SetFirewallStatus','AddAcceptPort','DelAcceptPort','SetSshStatus','SetPing','SetSshPort','GetSshInfo')
    return publicObject(firewallObject,defs);

@app.route('/files',methods=method_all)
def files():
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not request.args.get('path'):
        data = {}
        data['lan'] = public.GetLan('files')
        return render_template(public.GetConfigValue('template') +'/files.html',data=data)
    import files
    filesObject = files.files()
    defs = ('CheckExistsFiles','GetExecLog','GetSearch','ExecShell','GetExecShellMsg','UploadFile','GetDir','CreateFile','CreateDir','DeleteDir','DeleteFile',
            'CopyFile','CopyDir','MvFile','GetFileBody','SaveFileBody','Zip','UnZip',
            'GetFileAccess','SetFileAccess','GetDirSize','SetBatchData','BatchPaste',
            'DownloadFile','GetTaskSpeed','CloseLogs','InstallSoft','UninstallSoft',
            'RemoveTask','ActionTask','Re_Recycle_bin','Get_Recycle_bin','Del_Recycle_bin','Close_Recycle_bin','Recycle_bin')
    return publicObject(filesObject,defs);

@app.route('/crontab',methods=method_all)
def crontab():
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        data = {}
        data['lan'] = public.GetLan('crontab')
        return render_template( public.GetConfigValue('template') +'/crontab.html',data=data)
    import crontab
    crontabObject = crontab.crontab()
    defs = ('GetCrontab','AddCrontab','GetDataList','GetLogs','DelLogs','DelCrontab','StartTask','set_cron_status')
    return publicObject(crontabObject,defs);

@app.route('/soft',methods=method_all)
def soft():
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        data={}
        data['lan'] = public.GetLan('soft')
        return render_template( public.GetConfigValue('template') +'/soft.html',data=data)

@app.route('/config',methods=method_all)
def config():
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        import system,wxapp
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('config')
        data['wx'] = wxapp.wxapp().get_user_info(None)['msg']
        return render_template( public.GetConfigValue('template') +'/config.html',data=data)
    import config
    configObject = config.config()
    defs = ('SavePanelSSL','GetPanelSSL','GetPHPConf','SetPHPConf','GetPanelList','AddPanelInfo','SetPanelInfo','DelPanelInfo','ClickPanelInfo','SetPanelSSL','SetTemplates','Set502','setPassword','setUsername','setPanel','setPathInfo','setPHPMaxSize','getFpmConfig','setFpmConfig','setPHPMaxTime','syncDate','setPHPDisable','SetControl','ClosePanel','AutoUpdatePanel','SetPanelLock')
    return publicObject(configObject,defs);

@app.route('/ajax',methods=method_all)
def ajax():
    comReturn = comm.local()
    if comReturn: return comReturn
    import ajax
    ajaxObject = ajax.ajax()
    defs = ('GetCloudHtml','get_load_average','GetOpeLogs','GetFpmLogs','GetFpmSlowLogs','SetMemcachedCache','GetMemcachedStatus','GetRedisStatus','GetWarning','SetWarning','CheckLogin','GetSpeed','GetAd','phpSort','ToPunycode','GetBetaStatus','SetBeta','setPHPMyAdmin','delClose','KillProcess','GetPHPInfo','GetQiniuFileList','UninstallLib','InstallLib','SetQiniuAS','GetQiniuAS','GetLibList','GetProcessList','GetNetWorkList','GetNginxStatus','GetPHPStatus','GetTaskCount','GetSoftList','GetNetWorkIo','GetDiskIo','GetCpuIo','CheckInstalled','UpdatePanel','GetInstalled','GetPHPConfig','SetPHPConfig')
    return publicObject(ajaxObject,defs);

@app.route('/system',methods=method_all)
def system():
    comReturn = comm.local()
    if comReturn: return comReturn
    import system
    sysObject = system.system()
    defs = ('get_io_info','UpdatePro','GetAllInfo','GetNetWorkApi','GetLoadAverage','ClearSystem','GetNetWorkOld','GetNetWork','GetDiskInfo','GetCpuInfo','GetBootTime','GetSystemVersion','GetMemInfo','GetSystemTotal','GetConcifInfo','ServiceAdmin','ReWeb','RestartServer','ReMemory','RepPanel')
    return publicObject(sysObject,defs);

@app.route('/data',methods=method_all)
def data():
    comReturn = comm.local()
    if comReturn: return comReturn
    import data
    dataObject = data.data()
    defs = ('setPs','getData','getFind','getKey')
    return publicObject(dataObject,defs);

    
@app.route('/code')
def code():
    import vilidate,time
    code_time = cache.get('codeOut')
    if code_time: return u'请不要频繁获取验证码';
    vie = vilidate.vieCode();
    codeImage = vie.GetCodeImage(80,4);
    if sys.version_info[0] == 2:
        try:
            from cStringIO import StringIO
        except:
            from StringIO import StringIO
        out = StringIO();
    else:
        from io import BytesIO
        out = BytesIO();
    codeImage[0].save(out, "png")
    cache.set("codeStr",public.md5("".join(codeImage[1]).lower()),180)
    cache.set("codeOut",1,0.2);
    out.seek(0)
    return send_file(out, mimetype='image/png', cache_timeout=0)


@app.route('/ssl',methods=method_all)
def ssl():
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelSSL
    toObject = panelSSL.panelSSL()
    defs = ('RemoveCert','SetCertToSite','GetCertList','SaveCert','GetCert','GetCertName','DelToken','GetToken','GetUserInfo','GetOrderList','GetDVSSL','Completed','SyncOrder','GetSSLInfo','downloadCRT','GetSSLProduct')
    result = publicObject(toObject,defs);
    return result;

@app.route('/plugin',methods=method_all)
def plugin():
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelPlugin
    pluginObject = panelPlugin.panelPlugin()
    defs = ('get_soft_list','get_cloud_list','CheckDep','flush_cache','GetCloudWarning','install','unInstall','getPluginList','getPluginInfo','getPluginStatus','setPluginStatus','a','getCloudPlugin','getConfigHtml','savePluginSort')
    return publicObject(pluginObject,defs);


def publicObject(toObject,defs,action=None):
    get = get_input()
    if action: get.action = action
    if hasattr(get,'path'):
            get.path = get.path.replace('//','/').replace('\\','/');
            if get.path.find('->') != -1:
                get.path = get.path.split('->')[0].strip();
    for key in defs:
        if key == get.action:
            fun = 'toObject.'+key+'(get)'
            if hasattr(get,'html'):
                return eval(fun)
            else:
                return public.GetJson(eval(fun)),{'Content-Type':'application/json; charset=utf-8'}
    return public.ReturnJson(False,'ARGS_ERR')

@app.route('/public',methods=method_all)
def panel_public():
    get = get_input();
    get.client_ip = public.GetClientIp();
    if get.fun in ['scan_login','login_qrcode','set_login','is_scan_ok','blind']:
        import wxapp
        pluwx = wxapp.wxapp()
        checks = pluwx._check(get)
        if type(checks) != bool: return public.getJson(checks),json_header
        data = public.getJson(eval('pluwx.'+get.fun+'(get)'))
        return data,json_header
        
    import panelPlugin
    plu = panelPlugin.panelPlugin();
    get.s = '_check';
        
    checks = plu.a(get)
    if type(checks) != bool: return public.getJson(checks),json_header
    get.s = get.fun
    comm.setSession()
    comm.checkWebType()
    comm.GetOS()
    result = plu.a(get)
    return public.getJson(result),json_header

@app.route('/wxapp',methods=method_all)
def panel_wxapp():
    import wxapp
    toObject = wxapp.wxapp()
    defs = ('blind','get_safe_log','blind_result','get_user_info','blind_del','blind_qrcode')
    result = publicObject(toObject,defs);
    return result;

@app.route('/hook',methods=method_all)
def panel_hook():
    get = get_input()
    if not os.path.exists('plugin/webhook'): return public.getJson(public.returnMsg(False,'请先安装WebHook组件!'));
    sys.path.append('plugin/webhook');
    import webhook_main
    return public.getJson(webhook_main.webhook_main().RunHook(get));

@app.route('/safe',methods=method_all)
def panel_safe():
    get = get_input()
    pluginPath = 'plugin/safelogin';
    if hasattr(get,'check'):
        if os.path.exists(pluginPath + '/safelogin_main.py'): return 'True';
        return 'False';
    get.data = self.check_token(get.data);
    if not get.data: return public.returnJson(False,'验证失败');
    sys.path.append(pluginPath);
    import safelogin_main;
    reload(safelogin_main);
    s = safelogin_main.safelogin_main();
    if not hasattr(s,get.data['action']): return public.returnJson(False,'方法不存在');
    defs = ('GetServerInfo','add_ssh_limit','remove_ssh_limit','get_ssh_limit','get_login_log','get_panel_limit','add_panel_limit','remove_panel_limit','close_ssh_limit','close_panel_limit','get_system_info','get_service_info','get_ssh_errorlogin')
    if not get.data['action'] in defs: return 'False';
    return public.getJson(eval('s.' + get.data['action'] + '(get)'));


#检查Token
def check_token(self,data):
    pluginPath = 'plugin/safelogin/token.pl';
    if not os.path.exists(pluginPath): return False;
    from urllib import unquote;
    from binascii import unhexlify;
    from json import loads;
        
    result = unquote(unhexlify(data));
    token = public.readFile(pluginPath).strip();
        
    result = loads(result);
    if not result: return False;
    if result['token'] != token: return False;
    return result;

@app.route('/yield',methods=method_all)
def panel_yield():
    get = get_input()
    import panelPlugin
    plu = panelPlugin.panelPlugin();
    get.s = '_check';
    get.client_ip = public.GetClientIp()
    checks = plu.a(get)
    if type(checks) != bool: return
    get.s = get.fun
    filename = plu.a(get);
    mimetype = 'application/octet-stream'
    return send_file(filename,mimetype=mimetype, as_attachment=True,attachment_filename=os.path.basename(filename))

@app.route('/downloadApi',methods=method_all)
def panel_downloadApi():
    get = get_input()
    if not public.checkToken(get): get.filename = str(time.time());
    filename = 'plugin/psync/backup/' + get.filename.encode('utf-8');
    mimetype = 'application/octet-stream'
    return send_file(filename,mimetype=mimetype, as_attachment=True,attachment_filename=os.path.basename(filename))


@app.route('/pluginApi',methods=method_all)
def panel_pluginApi():
    get = get_input()
    if not public.checkToken(get): return public.returnJson(False,'无效的Token!');
    infoFile = 'plugin/' + name + '/info.json';
    if not os.path.exists(infoFile): return False;
    import json
    info = json.loads(public.readFile(infoFile));
    if not info['api']:  return public.returnJson(False,'您没有权限访问当前插件!');

    import panelPlugin
    pluginObject = panelPlugin.panelPlugin();
    defs = ('install','unInstall','getPluginList','getPluginInfo','getPluginStatus','setPluginStatus','a','getCloudPlugin','getConfigHtml','savePluginSort')
    return publicObject(pluginObject,defs);

@app.route('/auth',methods=method_all)
def panel_auth():
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelAuth
    toObject = panelAuth.panelAuth()
    defs = ('get_re_order_status_plugin','get_voucher_plugin','create_order_voucher_plugin','get_product_discount_by','get_re_order_status','create_order_voucher','create_order','get_order_status','get_voucher','flush_pay_status','create_serverid','check_serverid','get_plugin_list','check_plugin','get_buy_code','check_pay_status','get_renew_code','check_renew_code','get_business_plugin','get_ad_list','check_plugin_end','get_plugin_price')
    result = publicObject(toObject,defs);
    return result;


@app.route('/robots.txt',methods=method_all)
def panel_robots():
    robots = '''User-agent: *
Disallow: /
'''
    return robots,{'Content-Type':'text/plain'}

@app.route('/download',methods=method_get)
def download():
    comReturn = comm.local()
    if comReturn: return comReturn
    filename = request.args.get('filename')
    if not filename: return public.ReturnJson(False,"参数错误!"),json_header
    if not os.path.exists(filename): return public.ReturnJson(False,"指定文件不存在!"),json_header
    mimetype = "application/octet-stream"
    extName = filename.split('.')[-1]
    if extName in ['png','gif','jpeg','jpg']: mimetype = None
    return send_file(filename,mimetype=mimetype, as_attachment=True,attachment_filename=os.path.basename(filename))

@app.route('/cloud',methods=method_get)
def panel_cloud():
    comReturn = comm.local()
    if comReturn: return comReturn
    get = get_input()
    if not os.path.exists('plugin/' + get.filename + '/' + get.filename+'_main.py'): return public.returnJson(False,'指定插件不存在!'),json_header
    if sys.version_info[0] != 2:
        from imp import reload
    sys.path.append('plugin/' + get.filename)
    plugin_main = __import__(get.filename+'_main')
    reload(plugin_main)
    tmp = eval("plugin_main.%s_main()" % get.filename)
    if not hasattr(tmp,'download_file'): return public.returnJson(False,'指定插件没有文件下载方法!'),json_header
    return redirect(tmp.download_file(get.name))

ssh = paramiko.SSHClient()
shell = None

@socketio.on('webssh')
def webssh(msg):
    if not check_login(): return None 
    global shell,ssh
    ssh_success = True
    if not shell: ssh_success = connect_ssh()
    if not shell:
        emit('server_response',{'data':'连接SSH服务失败!\r\n'})
        return;
    if shell.exit_status_ready(): ssh_success = connect_ssh()
    if not ssh_success:
        emit('server_response',{'data':'连接SSH服务失败!\r\n'})
        return;
    shell.send(msg)
    try:
        time.sleep(0.005)
        recv = shell.recv(4096)
        emit('server_response',{'data':recv.decode("utf-8")})
    except Exception as ex:
        pass

def connect_ssh():
    if not check_login(): return None 
    global shell,ssh
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect('127.0.0.1', public.GetSSHPort())
    except:
        if public.GetSSHStatus():
            try:
                ssh.connect('localhost', public.GetSSHPort())
            except:
                return False;
        import firewalls
        fw = firewalls.firewalls()
        get = common.dict_obj()
        get.status = '0';
        fw.SetSshStatus(get)
        ssh.connect('127.0.0.1', public.GetSSHPort())
        get.status = '1';
        fw.SetSshStatus(get);
    shell = ssh.invoke_shell(term='xterm', width=100, height=25)
    shell.setblocking(0)
    return True
    
@socketio.on('connect_event')
def connected_msg(msg):
    if not check_login(): return None 
    try:
        recv = shell.recv(8192)
        emit('server_response',{'data':recv.decode("utf-8")})
    except Exception as ex:
        pass

@socketio.on('test')
def websocket_test(msg):
    emit('server_response',{'data':request.url})

def check_login():
    token = public.md5(request.url)
    loginStatus = cache.get(token)
    if loginStatus: return loginStatus
    if 'login' in session: 
        loginStatus = session['login']
        cache.set(token,loginStatus,30)
        return loginStatus
    return False


@app.errorhandler(404)
def notfound(e):
    errorStr = '''<!doctype html>
<html lang="zh">
    <head>
        <meta charset="utf-8">
        <title>%s</title>
    </head>
    <body>
        <h1>%s</h1>
        <p>%s</p>
        <hr>
        <address>%s <a href="https://www.bt.cn/bbs" target="_blank">%s</a></address>
    </body>
</html>''' % (public.getMsg('PAGE_ERR_404_TITLE'),public.getMsg('PAGE_ERR_404_H1'),public.getMsg('PAGE_ERR_404_P1'),public.getMsg('NAME'),public.getMsg('PAGE_ERR_HELP'))
    return errorStr,404
  
@app.errorhandler(500)
def internalerror(e):
    errorStr = '''<!doctype html>
<html lang="zh">
    <head>
        <meta charset="utf-8">
        <title>%s</title>
    </head>
    <body>
        <h1>%s</h1>
        <p>%s</p>
        <hr>
        <address>%s <a href="https://www.bt.cn/bbs" target="_blank">%s</a></address>
    </body>
</html>'''  % (public.getMsg('PAGE_ERR_500_TITLE'),public.getMsg('PAGE_ERR_500_H1'),public.getMsg('PAGE_ERR_500_P1'),public.getMsg('NAME'),public.getMsg('PAGE_ERR_HELP'))
    return errorStr,500

#获取输入数据
def get_input():
    data = common.dict_obj()
    post = request.form.to_dict()
    get = request.args.to_dict()
    data.args = get
    for key in get.keys():
        data[key] = get[key]
    for key in post.keys():
        data[key] = post[key]
    return data