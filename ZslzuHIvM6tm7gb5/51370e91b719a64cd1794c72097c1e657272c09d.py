#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

#------------------------------
# 工具箱
#------------------------------
import sys,os,shutil
setup_path = os.getenv("BT_PANEL")
if not setup_path: 
    setup_path = os.path.dirname(sys.argv[0])
    if not setup_path :
        setup_path = os.getcwd()
        os.environ['BT_PANEL'] = setup_path

os.chdir(setup_path);
sys.path.insert(0,setup_path+"/class/")

import public,time,json,psutil
#设置MySQL密码
def set_mysql_root(password):
    import db,os,pymysql,re
    from subprocess import PIPE
    sql = db.Sql()

    public.ExecShell("taskkill /f /t /im mysqld.exe");
    try:
        fname = re.search('([MySQL|MariaDB-]+\d+\.\d+)',public.get_server_path('mysql')).groups()[0] 
        _setup_path  = public.GetConfigValue('setup_path') + '/mysql/' + fname

        os.system("START /b " + _setup_path + '/bin/mysqld.exe --skip-grant-tables')
        while not public.process_exists('mysqld.exe'):
            time.sleep(0.1)
        time.sleep(2)

        myfile = _setup_path + '/my.ini'
        mycnf = public.readFile(myfile);

        rep = "port\s*=\s*([0-9]+)\s*\n"
        port = re.search(rep,mycnf).groups()[0];
    
        try:
            db = pymysql.connect(host = "localhost",port = int(port),user = "root",passwd = "",db = "mysql")
        except :
            time.sleep(5)
            db = pymysql.connect(host = "localhost",port = int(port),user = "root",passwd = "",db = "mysql")
    
        cursor = db.cursor()
        if fname.find("5.7") >= 0:
            cursor.execute("UPDATE mysql.user SET authentication_string='' WHERE user='root'")
            cursor.execute("FLUSH PRIVILEGES")
            cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY '%s';" % password)
        else:
            cursor.execute("UPDATE mysql.user set password=PASSWORD('" + password + "') WHERE User='root'")
            cursor.execute("FLUSH PRIVILEGES")
        
        print("|-MySQL新root密码: " + password);
    except :
        print("|-连接超时。MySQL的root密码修改失败. ");
            
    public.ExecShell("taskkill /f /t /im mysqld.exe");
    time.sleep(1)
    public.set_server_status('mysql','start')
    result = sql.table('config').where('id=?',(1,)).setField('mysql_root',password)

#设置面板密码
def set_panel_pwd(password,ncli = False):
    import db
    sql = db.Sql()
    result = sql.table('users').where('id=?',(1,)).setField('password',public.md5(password))
    username = sql.table('users').where('id=?',(1,)).getField('username')
    if ncli:
        print("|-用户名: " + username);
        print("|-新密码: " + password);
    else:
        print(username)


#自签证书
def CreateSSL():
    import OpenSSL
    key = OpenSSL.crypto.PKey()
    key.generate_key( OpenSSL.crypto.TYPE_RSA, 2048 )
    cert = OpenSSL.crypto.X509()
    cert.set_serial_number(0)
    cert.get_subject().CN = public.GetLocalIp();
    cert.set_issuer(cert.get_subject())
    cert.gmtime_adj_notBefore( 0 )
    cert.gmtime_adj_notAfter( 10*365*24*60*60 )
    cert.set_pubkey( key )
    cert.sign( key, 'md5' )
    cert_ca = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
    if len(cert_ca) > 100 and len(private_key) > 100:
        public.writeFile('ssl/certificate.pem',cert_ca)
        public.writeFile('ssl/privateKey.pem',private_key)
        print('success');
        return;
    print('error');

#清理系统垃圾
def ClearSystem():
    count = total = 0;
    tmp_total,tmp_count = ClearMail();
    count += tmp_count;
    total += tmp_total;
    print('=======================================================================')
    tmp_total,tmp_count = ClearSession();
    count += tmp_count;
    total += tmp_total;
    print('=======================================================================')
    tmp_total,tmp_count = ClearOther();
    count += tmp_count;
    total += tmp_total;
    print('=======================================================================')
    print('\033[1;32m|-系统垃圾清理完成，共删除['+str(count)+']个文件,释放磁盘空间['+ToSize(total)+']\033[0m');


#清空回收站
def ClearRecycle_Bin():
    import files
    f = files.files();
    f.Close_Recycle_bin(None);
    

#字节单位转换
def ToSize(size):
    ds = ['b','KB','MB','GB','TB']
    for d in ds:
        if size < 1024: return str(size)+d;
        size = size / 1024;
    return '0b';

#设置默认目录
def set_panel_default_dir(dir = None):
    
    dir = setup_path[:2] + '/'  
    if os.path.exists(dir):
        import db
        sql = db.Sql()
        backup_path = dir + 'backup'
        www_path = dir + 'wwwroot'

        sql.table('config').where('id=?',(1,)).setField('backup_path',backup_path)
        sql.table('config').where('id=?',(1,)).setField('sites_path',www_path)
   
        if not os.path.exists(backup_path): 
            os.makedirs(backup_path)

        if not os.path.exists(www_path): 
            os.makedirs(www_path)

        print("|-修改默认建站目录和默认备份目录成功")
        return;
    else:
        print("|-错误，目录不存在")
        return

#随机面板用户名
def set_panel_username(username = None):
    import db
    sql = db.Sql()
    if username:
        if len(username) < 5:
            print("|-错误，用户名长度不能少于5位")
            return;
        if username in ['admin','root']:
            print("|-错误，不能使用过于简单的用户名")
            return;

        sql.table('users').where('id=?',(1,)).setField('username',username)
        print("|-新用户名: %s" % username)
        return;
    
    username = sql.table('users').where('id=?',(1,)).getField('username')
    if username == 'admin': 
        username = public.GetRandomString(8).lower()
        sql.table('users').where('id=?',(1,)).setField('username',username)
    print('username: ' + username)
   
#设定idc
def setup_idc():
    try:
        panelPath = '/www/server/panel'
        filename = panelPath + '/data/o.pl'
        if not os.path.exists(filename): return False
        o = public.readFile(filename).strip()
        c_url = 'http://www.bt.cn/api/idc/get_idc_info_bycode?o=%s' % o
        idcInfo = json.loads(public.httpGet(c_url))
        if not idcInfo['status']: return False
        pFile = panelPath + '/static/language/Simplified_Chinese/public.json'
        pInfo = json.loads(public.readFile(pFile))
        pInfo['BRAND'] = idcInfo['msg']['name']
        pInfo['PRODUCT'] = u'与宝塔联合定制版'
        pInfo['NANE'] = pInfo['BRAND'] + pInfo['PRODUCT']
        public.writeFile(pFile,json.dumps(pInfo))
        tFile = panelPath + '/data/title.pl'
        titleNew = (pInfo['BRAND'] + u'面板').encode('utf-8')
        if os.path.exists(tFile):
            title = public.readFile(tFile).strip()
            if title == '宝塔Linux面板' or title == '': public.writeFile(tFile,titleNew)
        else:
            public.writeFile(tFile,titleNew)
        return True
    except:pass

def RepPanel():
    version  = public.readFile(setup_path + '/data/panel.version')
    if not version: version = public.httpGet("http://www.bt.cn/api/wpanel/get_version?is_version=1")

    downUrl = 'http://download.bt.cn' + '/win/panel/panel_' + version + '.zip'
    httpUrl = public.get_url();
    if httpUrl: downUrl =  httpUrl + '/win/panel/panel_' + version + '.zip';
        
    setupPath = public.GetConfigValue('setup_path');

    public.downloadFile(downUrl,setupPath + '/panel.zip');
    if os.path.getsize(setupPath + '/panel.zip') < 1048576: return public.returnMsg(False,"PANEL_UPDATE_ERR_DOWN");
        
    #处理临时文件目录   
    tmpPath = (setupPath + "/temp/panel")
    tcPath = (tmpPath + '\class').replace('/','\\')

    if not os.path.exists(tmpPath): os.makedirs(tmpPath)
    os.system("del /s %s\*.pyd" % tcPath)
     
    #解压到临时目录
    import zipfile
    zip_file = zipfile.ZipFile(setupPath + '/panel.zip')  
    for names in zip_file.namelist():              
        zip_file.extract(names,tmpPath)            
    zip_file.close()

    for name in os.listdir(tcPath): 
        if name.find('cp36-win_amd64.pyd') >=0: os.rename(os.path.join(tcPath,name),os.path.join(tcPath,name.replace('.cp36-win_amd64.pyd','.pyd')))    
        
    #过滤文件
    file_list = ['config/config.json','config/index.json','data/libList.conf','data/plugin.json']
    for ff_path in file_list:
        if os.path.exists(tmpPath + '/' + ff_path): os.remove(tmpPath + '/' + ff_path)  

    os.system("taskkill /im BtTools.exe /f")    

    #兼容不同版本工具箱
    toolPath = tmpPath + '/script/BtTools.exe'
    if os.path.exists(toolPath):
        os.remove(toolPath)
        netV = ''
        if os.path.exists('data/net'): netV = public.readFile('data/net')                
        public.downloadFile(httpUrl + '/win/panel/BtTools' + netV + '.exe',toolPath);

    #处理面板程序目录文件
    pPath = setupPath + '/panel' 
    cPath = (pPath + '/class').replace('/','\\')
    os.system("del /s %s\*.pyc" % cPath)
    os.system("del /s %s\*.pyt" % cPath)
    for name in os.listdir(cPath):
        try:
            if name.find('.pyd') >=0: os.rename(os.path.join(cPath,name),os.path.join(cPath,name.replace('.pyd','.pyt'))) 
        except : pass      

    tmpPath = tmpPath.replace("/","\\")
    panelPath = (setupPath + "/panel").replace("/","\\")
    os.system("xcopy /s /c /e /y /r %s %s" % (tmpPath,panelPath))

    os.system("bt restart")
    return public.returnMsg(True,"修复成功");

#解压文件
def set_unzip(src,dist):
    #解压到临时目录
    import zipfile
    zip_file = zipfile.ZipFile(src)  
    for names in zip_file.namelist():  
        zip_file.extract(names,dist)      
    zip_file.close()

def get_panel_config(is_json = True):
    import db
    data = {}
    data['url'] = public.GetLocalIp();
    sql = db.Sql()
    username = sql.table('users').where('id=?',(1,)).getField('username')  
    data['username'] = username
    if is_json:
        print(json.dumps(data))
    else:
        print('|%s|%s|' % (data['username'],data['url']))

#修改面板端口
def set_panel_port(input_port):
    oldPort = public.readFile('data/port.pl');
    if int(oldPort) != int(input_port):    
        import time
        public.writeFile('data/port.pl',str(input_port))
        ps = public.getMsg('PORT_CHECK_PS');        

        #放行新端口
        version = public.get_sys_version()          
        shell = 'netsh firewall set portopening tcp %s "%s"' % (input_port,ps)
        if int(version[0]) == 6:            
            shell = 'netsh advfirewall firewall add rule name="%s" dir=in action=allow protocol=tcp localport=%s' % (ps,input_port)
        public.ExecShell(shell)
        addtime = time.strftime('%Y-%m-%d %X',time.localtime())
        public.M('firewall').add('port,ps,addtime',(str(input_port),ps,addtime))
  
        #删除老端口
        public.M('firewall').where("port=?",(oldPort,)).delete()
        shell = "netsh firewall delete portopening protocol=tcp port=" +  str(oldPort)
        if int(version[0]) == 6:
            shell = "netsh advfirewall firewall delete rule name=all protocol=tcp localport=" +  str(oldPort)
        public.ExecShell(shell)

#命令行菜单
def bt_cli():
    raw_tip = "==============================================="
    print("===============宝塔面板命令行==================")
    print("(1)  重启面板服务           (8)  改面板端口")
    print("(2)  停止面板服务           (9)  清除面板缓存")
    print("(3)  启动面板服务           (10) 清除登录限制")
    print("(4)  重载面板服务           (11) 取消入口限制")
    print("(5)  修改面板密码           (12) 取消域名绑定限制")
    print("(6)  修改面板用户名         (13) 取消IP访问限制")
    print("(7)  强制修改MySQL密码      (14) 查看面板默认信息")
    print("(22) 显示面板错误日志       (15) 清理系统垃圾")
    print("(23) 关闭BasicAuth认证      (16) 修复面板程序")
    print("(24) 关闭Google身份认证     (25) 命令行启动面板")
    print("(0) 取消                    (0)  取消")
    print(raw_tip)
    try:
        u_input = input("请输入命令编号：")
        if sys.version_info[0] == 3: u_input = int(u_input)
    except: u_input = 0
    nums = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,22,23,24,25]
    if not u_input in nums:
        print(raw_tip)
        print("已取消!")
        exit()

    print(raw_tip)
    print("正在执行(%s)..." % u_input)
    print(raw_tip)

    if u_input == 1:
        os.system("bt restart")
    elif u_input == 2:
        os.system("bt stop")
    elif u_input == 3:
        os.system("bt start")
    elif u_input == 4:
        os.system("bt restart")
    elif u_input == 5:
        if sys.version_info[0] == 2:
            input_pwd = raw_input("请输入新的面板密码：")
        else:
            input_pwd = input("请输入新的面板密码：")
        set_panel_pwd(input_pwd.strip(),True)
    elif u_input == 6:
        if sys.version_info[0] == 2:
            input_user = raw_input("请输入新的面板用户名(>5位)：")
        else:
            input_user = input("请输入新的面板用户名(>5位)：")
        set_panel_username(input_user.strip())
    elif u_input == 7:
        if sys.version_info[0] == 2:
            input_mysql = raw_input("请输入新的MySQL密码：")
        else:
            input_mysql = input("请输入新的MySQL密码：")
        if not input_mysql:
            print("|-错误，不能设置空密码")
            return;

        if len(input_mysql) < 8:
            print("|-错误，长度不能少于8位")
            return;

        import re
        rep = "^[\w@\._]+$"
        if not re.match(rep, input_mysql):
            print("|-错误，密码中不能包含特殊符号")
            return;
        
        print(input_mysql)
        set_mysql_root(input_mysql.strip())
    elif u_input == 8:
        input_port = input("请输入新的面板端口：")
        if sys.version_info[0] == 3: input_port = int(input_port)
        if not input_port:
            print("|-错误，未输入任何有效端口")
            return;
        if input_port in [80,443,21,20,22,3389,3306]:
            print("|-错误，请不要使用常用端口作为面板端口")
            return;
        old_port = int(public.readFile('data/port.pl'))
        if old_port == input_port:
            print("|-错误，与面板当前端口一致，无需修改")
            return;
        is_exists = public.ExecShell("netstat -aon|findstr '%s'" % input_port)
        if len(is_exists[0]) > 5:
            print("|-错误，指定端口已被其它应用占用")
            return;
        
        self.set_panel_port(input_port)

        print("|-已将面板端口修改为：%s" % input_port)
        print("|-若您的服务器提供商是[阿里云][腾讯云][华为云]或其它开启了[安全组]的服务器,请在安全组放行[%s]端口才能访问面板" % input_port)
    elif u_input == 9:
        sess_file = 'data/session.db'
        if os.path.exists(sess_file): os.remove(sess_file)
        os.system("bt reload")
    elif u_input == 10:
        os.system("bt reload")
    elif u_input == 11:
        auth_file = 'data/admin_path.pl'
        if os.path.exists(auth_file): os.remove(auth_file)
        os.system("bt reload")
        print("|-已取消入口限制")
    elif u_input == 12:
        auth_file = 'data/domain.conf'
        if os.path.exists(auth_file): os.remove(auth_file)
        os.system("bt reload")
        print("|-已取消域名访问限制")
    elif u_input == 13:
        auth_file = 'data/limitip.conf'
        if os.path.exists(auth_file): os.remove(auth_file)
        os.system("bt reload")
        print("|-已取消IP访问限制")
    elif u_input == 14:
        os.system("bt default")
    elif u_input == 15:
        ClearSystem()
    elif u_input == 16:
        RepPanel()
    elif u_input == 22:
        print('tail -100 %s/data/panelError.log' % setup_path)
        os.system('tail -100 %s/data/panelError.log' % setup_path)
    elif u_input == 23:
        filename = 'config/basic_auth.json'
        if os.path.exists(filename): os.remove(filename)
        os.system('bt reload')
        print("|-已关闭BasicAuth认证")
    elif u_input == 24:
        filename = 'data/two_step_auth.txt'
        if os.path.exists(filename): os.remove(filename)
        print("|-已关闭Google身份认证")
    elif u_input == 25:
        os.system('"C:\Program Files\python\python.exe" %s/runserver.py' % os.getenv('BT_PANEL'))


if __name__ == "__main__":
  
    type = sys.argv[1];
    if type == 'root':
        set_mysql_root(sys.argv[2])
    elif type == 'panel':
        set_panel_pwd(sys.argv[2])
    elif type == 'username':
        if len(sys.argv) > 2:
            set_panel_username(sys.argv[2])
        else:
            set_panel_username()
    elif type == 'o':
        setup_idc()
    elif type == 'mysql_dir':
        set_mysql_dir(sys.argv[2])
    elif type == 'to':
        panel2To3()
    elif type == 'package':
        PackagePanel();
    elif type == 'ssl':
        CreateSSL();
    elif type == 'port':
        CheckPort();
    elif type == 'clear':
        ClearSystem();
    elif type == 'closelog':
        CloseLogs();
    elif type == 'update_to6':
        update_to6()
    elif type == 're_panel':
        RepPanel()
    elif type == "cli":
        bt_cli()
    elif type == "get_config":
        get_panel_config(True)
    elif type == "get_panel_config":
        get_panel_config(False)
    elif type == "unpanel":
        unpanel(sys.argv[2])
    elif type == "default_dir":
        set_panel_default_dir()
    elif type == "set_panel_port":
        set_panel_port(sys.argv[2])
    elif type == "unzip":
        set_unzip(sys.argv[2],sys.argv[3])
    else:
        print('ERROR: Parameter error')
    
