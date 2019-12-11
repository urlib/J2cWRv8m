#coding: utf-8
#-----------------------------
# 安装脚本
#-----------------------------

import sys,os,re,win32service
panelPath = os.getenv("BT_PANEL")
os.chdir(panelPath);
sys.path.insert(0,panelPath + "/class/")
import public

if __name__ == "__main__":

    if not public.is_64bitos():
        exit('此程序不兼容x86系统，请更换至x64位系统..');
    if len(sys.argv) > 1:
        name = sys.argv[2]    
        version = ''
        if len(sys.argv) > 3:  version = sys.argv[3]

        public.bt_print("正在智能选择下载节点..");
        downurl = public.get_url()

        localPath = 'install/panel_' + name + '.py';
        public.downloadFile(downurl + '/win/install/panel_' + name + '.py',localPath)
       
        if not os.path.exists(localPath): exit()
        m = __import__('panel_' + name)
        
        temp_path = os.getenv("BT_SETUP") + '/temp'
        if not os.path.exists(temp_path):
            os.makedirs(temp_path)

        module = eval("m.panel_" + name + "('" + name + "','" + version + "','" + os.getenv("BT_SETUP").replace("\\",'/') + "')")        
        if sys.argv[1] == 'install':
            module.install_soft(downurl)
        elif sys.argv[1] == 'update':
            module.update_soft(downurl)
        else:
            module.uninstall_soft() 
    else:
        print(public.returnMsg(False,'操作失败,参数不匹配!'))        