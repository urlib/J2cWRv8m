#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------

import sys,os,public,time,json,cgi
from BTPanel import session,request

class files:
    
    #检查敏感目录
    def CheckDir(self,path):
        path = path.replace('//','/');
        if path[-1:] == '/':
            path = path[:-1]
        
        nDirs = ('',
                'C:/',
                'C:/Windows',
                public.GetConfigValue('root_path'),
                public.GetConfigValue('logs_path'),
                public.GetConfigValue('setup_path'))
        for dir in nDirs:
            if(dir == path):
                return False 
        return True
    
    #检测文件名
    def CheckFileName(self,filename):
        nots = ['\\','&','*','#','@','|']
        if filename.find('/') != -1: filename = filename.split('/')[-1]
        for n in nots:
            if n in filename: return False
        return True
    
    #上传文件
    def UploadFile(self,get):
        from werkzeug.utils import secure_filename
        from flask import request

        if not os.path.exists(get.path): os.makedirs(get.path)
        f = request.files['zunfile']
        filename = os.path.join(get.path, f.filename)
        s_path = get.path
        if os.path.exists(filename):s_path = filename
        p_stat = os.stat(s_path)
        f.save(filename)
       
        public.WriteLog('TYPE_FILE','FILE_UPLOAD_SUCCESS',(filename,get['path']));
        return public.returnMsg(True,'FILE_UPLOAD_SUCCESS');
    
    #上传文件2
    def upload(self,args):   

        if not 'f_name' in args:
            try:
                args.f_name = request.form.get('f_name')
                args.f_path = request.form.get('f_path')
                args.f_size = request.form.get('f_size')
                args.f_start = request.form.get('f_start')
            except : return public.returnMsg(False,'缺少必要参数.')
                
        if not args.f_name or args.f_name.find('./') != -1 or args.f_path.find('./') != -1: return public.returnMsg(False,'错误的参数')
        try:
            if not os.path.exists(args.f_path): os.makedirs(args.f_path)
        except Exception as ex:
            return public.returnMsg(False,str(ex))
        

        save_path =  os.path.join(args.f_path,args.f_name + '.' + str(int(args.f_size)) + '.upload.tmp')
        d_size = 0
        if os.path.exists(save_path): d_size = os.path.getsize(save_path)
        if d_size != int(args.f_start): return d_size
        
        try:
            upload_files = request.files.getlist("blob")

            f = open(save_path,'ab')
            for tmp_f in upload_files:
                f.write(tmp_f.read())
            f.close()
        except :
             return public.returnMsg(False,"上传失败，请检查文件是否被占用.")

        f_size = os.path.getsize(save_path)
        if f_size != int(args.f_size):  return f_size
        new_name = os.path.join(args.f_path ,args.f_name)
        try:
            if os.path.exists(new_name): os.remove(new_name)
            os.renames(save_path, new_name)
        except Exception as ex:
            return public.returnMsg(False,str(ex))

        public.WriteLog('TYPE_FILE','FILE_UPLOAD_SUCCESS',(args.f_name,args.f_path));
        return public.returnMsg(True,'上传成功!')
    
    #名称输出过滤
    def xssencode(self,text):
        list=['<','>']
        ret=[]
        for i in text:
            if i in list:
                i=''
            ret.append(i)
        str_convert = ''.join(ret)
        text2=cgi.escape(str_convert, quote=True)
        return text2

    def __get_stat(self,filename,path = None):
        stat = os.stat(filename)
        accept = str(oct(stat.st_mode)[-3:]);
        mtime = str(int(stat.st_mtime))
        user = ''
      
        user = str(stat.st_uid)
        size = str(stat.st_size)
        link = '';
        if os.path.islink(filename): link = ' -> ' + os.readlink(filename)
        tmp_path = (path + '/').replace('//','/')
        if path and tmp_path != '/':filename = filename.replace(tmp_path,'')
        filename = public.format_path(filename)
        return filename + ';' + size + ';' + mtime+ ';' +accept+ ';' +user+ ';' +link

    #查询子目录
    def SearchFiles(self,get):
        if not hasattr(get,'path'): get.path = 'C:/wwwroot'      
        if not os.path.exists(get.path): get.path = 'C:/BtSoft';
        search = get.search.strip().lower();
        my_dirs = []
        my_files = []
        count = 0
        max = 3000
        for d_list in os.walk(get.path):
            if count >= max: break;
            for d in d_list[1]:
                if count >= max: break;
                d = self.xssencode(d)
                if d.lower().find(search) != -1: 
                    my_dirs.append(self.__get_stat(d_list[0] + '/' + d,get.path))
                    count += 1
                    
            for f in d_list[2]:
                if count >= max: break;
                f = self.xssencode(f)
                if f.lower().find(search) != -1: 
                    my_files.append(self.__get_stat(d_list[0] + '/' + f,get.path))
                    count += 1
        data = {}
        data['DIR'] = sorted(my_dirs)
        data['FILES'] = sorted(my_files)
        data['PATH'] = str(get.path)
        data['PAGE'] = self.get_page(len(my_dirs) + len(my_files),1,max,'GetFiles')['page']
        return data

    # 构造分页
    def get_page(self,count,p=1,rows=12,callback='',result='1,2,3,4,5,8'):
        import page
        from BTPanel import request
        page = page.Page();
        info = { 'count':count,  'row':rows,  'p':p, 'return_js':callback ,'uri':request.full_path}
        data = { 'page': page.GetPage(info,result),  'shift': str(page.SHIFT), 'row': str(page.ROW) }
        return data

    #取文件/目录列表
    def GetDir(self,get):
        try:
            if not hasattr(get,'path'): get.path = 'C:/'
            if not os.path.exists(get.path): get.path = 'C:/';

            if get.path[1:] == ':': get.path = get.path + '/'
            
            dirnames = []
            filenames = []
       
            search = None
            if hasattr(get,'search'): search = get.search.strip().lower();
            if hasattr(get,'all'): return self.SearchFiles(get)
        
            #包含分页类
            import page
            #实例化分页类
            page = page.Page();
            info = {}
            info['count'] = self.GetFilesCount(get.path,search);
            info['row']   = 100
            info['p'] = 1
            if hasattr(get,'p'):
                try:
                    info['p']     = int(get['p'])
                except:
                    info['p'] = 1

            info['uri']   = {}
            info['return_js'] = ''
            if hasattr(get,'tojs'):
                info['return_js']   = get.tojs
            if hasattr(get,'showRow'):
                info['row'] = int(get.showRow);
        
            #获取分页数据
            data = {}
            data['PAGE'] = page.GetPage(info,'1,2,3,4,5,6,7,8')

            i = 0;
            n = 0;
   
            for filename in os.listdir(get.path):
                if search:
                    if filename.lower().find(search) == -1: continue;
                i += 1;
                if n >= page.ROW: break;
                if i < page.SHIFT: continue;
            
                try:
                    filePath = get.path+'/'+filename
                    link = '';
                    if os.path.islink(filePath): 
                        filePath = os.readlink(filePath);
                        link = ' -> ' + filePath;
                        if not os.path.exists(filePath): filePath = get.path + '/' + filePath;
                        if not os.path.exists(filePath): continue;
                
                    stat = os.stat(filePath)
                    accept = str(oct(stat.st_mode)[-3:]);
                    mtime = str(int(stat.st_mtime))
                    user = ''
                    
                    size = str(stat.st_size)
                    if os.path.isdir(filePath):
                        dirnames.append(filename+';'+size+';'+mtime+';'+accept+';'+user+';'+link);
                    else:
                        filenames.append(filename+';'+size+';'+mtime+';'+accept+';'+user+';'+link);
                    n += 1;
                except:
                    continue;
        
        
            data['DIR'] = sorted(dirnames);
            data['FILES'] = sorted(filenames);
            data['PATH'] = str(get.path).strip("/")
            data['STORE'] = self.get_files_store(None)
          
            if hasattr(get,'disk'):
                import system
                data['DISK'] = system.system().GetDiskInfo();
            return data
        except Exception as ex:
            return public.returnMsg(False,str(ex));
        
    
    #计算文件数量
    def GetFilesCount(self,path,search):
        i=0;
        for name in os.listdir(path):
            if search:
                if name.lower().find(search) == -1: continue;
            i += 1;
        return i;
    
    #创建文件
    def CreateFile(self,get):
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8').strip();
        try:
            if not self.CheckFileName(get.path): return public.returnMsg(False,'文件名中不能包含特殊字符!');
            if os.path.exists(get.path):
                return public.returnMsg(False,'FILE_EXISTS')
            path = os.path.dirname(get.path)
            if not os.path.exists(path):
                os.makedirs(path)
            open(get.path,'w+').close()  
            self.SetFileAccept(get.path);
            public.WriteLog('TYPE_FILE','FILE_CREATE_SUCCESS',(get.path,))
            return public.returnMsg(True,'FILE_CREATE_SUCCESS')
        except:
            return public.returnMsg(False,'FILE_CREATE_ERR')
    
    #创建目录
    def CreateDir(self,get):
        if sys.version_info[0] == 2: get.path = get.path.encode('utf-8').strip();
        try:
            if not self.CheckFileName(get.path): return public.returnMsg(False,'目录名中不能包含特殊字符!');
            if os.path.exists(get.path):
                return public.returnMsg(False,'DIR_EXISTS')
            os.makedirs(get.path)
            self.SetFileAccept(get.path);
            public.WriteLog('TYPE_FILE','DIR_CREATE_SUCCESS',(get.path,))
            return public.returnMsg(True,'DIR_CREATE_SUCCESS')
        except:
            return public.returnMsg(False,'DIR_CREATE_ERR')
        
    #删除目录
    def DeleteDir(self,get) :
        if not hasattr(get, 'path'): return public.returnMsg(False,'DIR_NOT_EXISTS')
     
        if not public.check_win_path(get.path): return public.returnMsg(False,'不是有效的Windows格式路径，不能包含(: * ? " < > |)');
            
        if not os.path.exists(get.path):  return public.returnMsg(False,'DIR_NOT_EXISTS')
        
        #检查是否敏感目录
        if not self.CheckDir(get.path):
            return public.returnMsg(False,'FILE_DANGER');
        
        try:
            if hasattr(get,'empty'):
                if not self.delete_empty(get.path): return public.returnMsg(False,'DIR_ERR_NOT_EMPTY');
            
            if os.path.exists('data/recycle_bin.pl'):
                if self.Mv_Recycle_bin(get): return public.returnMsg(True,'DIR_MOVE_RECYCLE_BIN');
            
            import shutil
            shutil.rmtree(get.path)
            public.WriteLog('TYPE_FILE','DIR_DEL_SUCCESS',(get.path,))
            return public.returnMsg(True,'DIR_DEL_SUCCESS')
        except:
            return public.returnMsg(False,'DIR_DEL_ERR')
    
    #删除 空目录 
    def delete_empty(self,path):
        for files in os.listdir(path):
            return False
        return True
    
    #删除文件
    def DeleteFile(self,get):
        if not os.path.exists(get.path):
            return public.returnMsg(False,'FILE_NOT_EXISTS')
        
        #检查是否为.user.ini
        try:
            if os.path.exists('data/recycle_bin.pl'):
                if self.Mv_Recycle_bin(get): return public.returnMsg(True,'FILE_MOVE_RECYCLE_BIN');
            os.remove(get.path)
            public.WriteLog('TYPE_FILE','FILE_DEL_SUCCESS',(get.path,))
            return public.returnMsg(True,'FILE_DEL_SUCCESS')
        except:
            return public.returnMsg(False,'FILE_DEL_ERR')
    
    #移动到回收站
    def Mv_Recycle_bin(self,get):
        rPath = os.getenv("BT_SETUP") + '/Recycle_bin/'
        if not os.path.exists(rPath): os.makedirs(rPath)
        rFile = rPath + get.path.replace('/','_bt_').replace(':','_m_') + '_t_' + str(time.time());
        try:
            import shutil
            public.move(get.path, rFile)
            public.WriteLog('TYPE_FILE','FILE_MOVE_RECYCLE_BIN',(get.path,))
            return True;
        except:
            public.WriteLog('TYPE_FILE','FILE_MOVE_RECYCLE_BIN_ERR',(get.path,))
            return False;
    
    #从回收站恢复
    def Re_Recycle_bin(self,get):
        rPath = os.getenv("BT_SETUP") + '/Recycle_bin/'
        dFile = get.path.replace('_bt_','/').replace('_m_',':').split('_t_')[0];
        get.path = rPath + get.path
        if dFile.find('BTDB_') != -1:
            import database;
            return database.database().RecycleDB(get.path);
        try:
            import shutil
            public.move(get.path, dFile)
            public.WriteLog('TYPE_FILE','FILE_RE_RECYCLE_BIN',(dFile,))
            return public.returnMsg(True,'FILE_RE_RECYCLE_BIN');
        except:
            public.WriteLog('TYPE_FILE','FILE_RE_RECYCLE_BIN_ERR',(dFile,))
            return public.returnMsg(False,'FILE_RE_RECYCLE_BIN_ERR');
    
    #获取回收站信息
    def Get_Recycle_bin(self,get):
        rPath = os.getenv("BT_SETUP") + '/Recycle_bin/'
        if not os.path.exists(rPath): os.makedirs(rPath)
        data = {};
        data['dirs'] = [];
        data['files'] = [];
        data['status'] = os.path.exists('data/recycle_bin.pl');
        data['status_db'] = os.path.exists('data/recycle_bin_db.pl');
        for file in os.listdir(rPath):
            try:
                tmp = {};
                fname = rPath + file;
                tmp1 = file.split('_bt_');
                tmp2 = tmp1[len(tmp1)-1].split('_t_');
                tmp['rname'] = file;
                tmp['dname'] = file.replace('_bt_','/').split('_t_')[0];
                tmp['name'] = tmp2[0];
                tmp['time'] = int(float(tmp2[1]));
                if os.path.islink(fname): 
                    filePath = os.readlink(fname);
                    link = ' -> ' + filePath;
                    if os.path.exists(filePath): 
                        tmp['size'] = os.path.getsize(filePath);
                    else:
                        tmp['size'] = 0;
                else:
                    tmp['size'] = os.path.getsize(fname);
                if os.path.isdir(fname):
                    data['dirs'].append(tmp);
                else:
                    data['files'].append(tmp);
            except:
                continue;
        return data;
    
    #彻底删除
    def Del_Recycle_bin(self,get):
        rPath = os.getenv("BT_SETUP") + '/Recycle_bin/'
        dFile = get.path.split('_t_')[0];
        if dFile.find('BTDB_') != -1:
            import database;
            return database.database().DeleteTo(rPath+get.path);
        if not self.CheckDir(rPath + get.path):
            return public.returnMsg(False,'FILE_DANGER');
  
        if os.path.isdir(rPath + get.path):
            import shutil
            shutil.rmtree(rPath + get.path);
        else:
            os.remove(rPath + get.path);
        
        tfile = get.path.replace('_bt_','/').split('_t_')[0];
        public.WriteLog('TYPE_FILE','FILE_DEL_RECYCLE_BIN',(tfile,));
        return public.returnMsg(True,'FILE_DEL_RECYCLE_BIN',(tfile,));
    
    #清空回收站
    def Close_Recycle_bin(self,get):
        try:
            rPath = os.getenv("BT_SETUP") + '/Recycle_bin/'
            import database,shutil;
            rlist = os.listdir(rPath)
            i = 0;
            l = len(rlist);
            for name in rlist:
                i += 1;
                path = rPath + name;
                public.writeSpeed(name,i,l);
                if name.find('BTDB_') != -1:
                    database.database().DeleteTo(path);
                    continue;
                if os.path.isdir(path):
                    shutil.rmtree(path);
                else:
                    os.remove(path);
            public.writeSpeed(None,0,0);
            public.WriteLog('TYPE_FILE','FILE_CLOSE_RECYCLE_BIN');
            return public.returnMsg(True,'FILE_CLOSE_RECYCLE_BIN');
        except Exception as ex:     
            return public.returnMsg(False,str(ex));

    
    #回收站开关
    def Recycle_bin(self,get):        
        c = 'data/recycle_bin.pl';
        if hasattr(get,'db'): 
            c = 'data/recycle_bin_db.pl';
            return public.returnMsg(False,'暂不支持数据库回收站功能！');
        if os.path.exists(c):
            os.remove(c)
            public.WriteLog('TYPE_FILE','FILE_OFF_RECYCLE_BIN');
            return public.returnMsg(True,'FILE_OFF_RECYCLE_BIN');
        else:
            public.writeFile(c,'True');
            public.WriteLog('TYPE_FILE','FILE_ON_RECYCLE_BIN');
            return public.returnMsg(True,'FILE_ON_RECYCLE_BIN');
    
    #复制文件
    def CopyFile(self,get) :
        if not os.path.exists(get.sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS')
        
        if os.path.isdir(get.sfile):
            return self.CopyDir(get)
        
        import shutil
        try:
            shutil.copyfile(get.sfile, get.dfile)
            public.WriteLog('TYPE_FILE','FILE_COPY_SUCCESS',(get.sfile,get.dfile))
            return public.returnMsg(True,'FILE_COPY_SUCCESS')
        except:
            return public.returnMsg(False,'FILE_COPY_ERR')
    
    #复制文件夹
    def CopyDir(self,get):
        if not os.path.exists(get.sfile):
            return public.returnMsg(False,'DIR_NOT_EXISTS');
        
        if os.path.exists(get.dfile):
            return public.returnMsg(False,'DIR_EXISTS');

        import shutil
        try:
            public.copytree(get.sfile, get.dfile)          
            public.WriteLog('TYPE_FILE','DIR_COPY_SUCCESS',(get.sfile,get.dfile))
            return public.returnMsg(True,'DIR_COPY_SUCCESS')
        except:
            return public.returnMsg(False,'DIR_COPY_ERR')

    
    #移动文件或目录
    def MvFile(self,get):

        if not self.CheckFileName(get.dfile): return public.returnMsg(False,'文件名中不能包含特殊字符!');
        if not os.path.exists(get.sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS')
        
        if not self.CheckDir(get.sfile):
            return public.returnMsg(False,'FILE_DANGER');
        try:
            public.move(get.sfile,get.dfile)
            if hasattr(get,'rename'):
                public.WriteLog('TYPE_FILE','[%s]重命名为[%s]' % (get.sfile,get.dfile))
                return public.returnMsg(True,'重命名成功!')
            else:
                public.WriteLog('TYPE_FILE','MOVE_SUCCESS',(get.sfile,get.dfile))
                return public.returnMsg(True,'MOVE_SUCCESS')
        except:
            return public.returnMsg(False,'MOVE_ERR')

    #检查文件是否存在
    def CheckExistsFiles(self,get):
        data = [];
        try:
            filesx = [];
            if not hasattr(get,'filename'):
                if not 'selected' in session: return []
                filesx = json.loads(session['selected']['data']);
            else:
                filesx.append(get.filename);
        
            for fn in filesx:
                if fn == '.': continue
                filename = get.dfile + '/' + fn;
                if os.path.exists(filename):
                    tmp = {}
                    stat = os.stat(filename)
                    tmp['filename'] = fn;
                    tmp['size'] = os.path.getsize(filename);
                    tmp['mtime'] = str(int(stat.st_mtime));
                    data.append(tmp);
        except : pass
        return data;
                
    #获取文件内容
    def GetFileBody(self,get) :
        self.check_stop_page(get)
        if not os.path.exists(get.path):
            if get.path.find('rewrite') == -1:
                return public.returnMsg(False,'FILE_NOT_EXISTS',(get.path,))
            public.writeFile(get.path,'');
        
        if os.path.getsize(get.path) > 2097152: return public.returnMsg(False,u'不能在线编辑大于2MB的文件!');
        if not os.path.isfile(get.path): return public.returnMsg(False,'这不是一个文件!')

        try:   
            fp = open(get.path,'rb')
            data = {}
            data['status'] = True

            srcBody = b""
            try:
                if fp:
                    from chardet.universaldetector import UniversalDetector
                    detector = UniversalDetector()
           
                    for line in fp.readlines():
                        detector.feed(line)
                        srcBody += line
                    detector.close()
                    char = detector.result
                    data['encoding'] = char['encoding']
                    if char['encoding'] == 'GB2312' or not char['encoding'] or char['encoding'] == 'TIS-620' or char['encoding'] == 'ISO-8859-9': data['encoding'] = 'GBK';
                    if char['encoding'] == 'ascii' or char['encoding'] == 'ISO-8859-1': data['encoding'] = 'utf-8';
                    if char['encoding'] == 'Big5': data['encoding'] = 'BIG5';
                    if not char['encoding'] in ['GBK','utf-8','BIG5']: data['encoding'] = 'utf-8';
                    try:
                        data['data'] = srcBody.decode(data['encoding'])
                    except:
                        data['encoding'] = char['encoding'];
                        data['data'] = srcBody.decode(data['encoding'])
                else:
                     return public.returnMsg(False,'文件打开失败，请检查文件是否被占用.');

                return data;
            except Exception as ex:
                return public.returnMsg(False,u'文件编码不被兼容，无法正确读取文件!' + str(ex));
        except Exception as ex:
            return public.returnMsg(False,'文件打开失败，请检查文件权限. 错误详情 --> ' + str(ex));
        
    #保存文件
    def SaveFileBody(self,get):
        if not hasattr(get, 'path'): return public.returnMsg(False,'参数传递错误.')   
        
        if not os.path.exists(get.path):
            if get.path.find('.htaccess') == -1:
                return public.returnMsg(False,'FILE_NOT_EXISTS')        
        try:
            data = get.data;            
            if get.encoding == 'ascii':get.encoding = 'utf-8';   
            fp = open(get.path,'wb')
            data = data.encode(get.encoding)
            
            fp.write(data)
            fp.close()
            public.WriteLog('TYPE_FILE','FILE_SAVE_SUCCESS',(get.path,));
            return public.returnMsg(True,'FILE_SAVE_SUCCESS');
        except Exception as ex:
            return public.returnMsg(False,'FILE_SAVE_ERR' + str(ex));
    
    #检查是否存在停止页
    def check_stop_page(self,get):        
        setup_path = (os.getenv('BT_SETUP') + '/stop/index.html').replace('\\','/')
        if get.path.find(setup_path) != -1:
            if not os.path.exists(setup_path):
                stopPath = os.getenv('BT_SETUP') + '/stop'  
                if not os.path.exists(stopPath): 
                    os.makedirs(stopPath)
           
                    get.filename = stopPath              
                    get.access = 2032127
                    get.user = 'IIS_IUSRS'
                    self.SetFileAccess(get)

                    get.user = 'www'
                    self.SetFileAccess(get)
                    public.downloadFile(public.get_url() + "/win/panel/data/stop.html",setup_path)

    #文件压缩
    def Zip(self,get) :             
        try:
            filelists = []        
            if get.sfile.find(',') == -1:
                #处理单目录
                path = get.path + '/' + get.sfile
                path = path.strip('/')
                if not os.path.exists(path): return public.returnMsg(False,'FILE_NOT_EXISTS');

                if os.path.isdir(path):
                    self.GetFileList(path, filelists)
                else:
                    filelists.append(path)
            else:
                #处理批量
                batch_list = get.sfile.split(',')
                for f in batch_list:
                    if f:
                        path = get.path + '/' + f
                        path = path.strip('/')
                        if os.path.isdir(path):
                            self.GetFileList(path, filelists)
                        else:
                            filelists.append(path)

            import zipfile  
            f = zipfile.ZipFile(get.dfile,'w',zipfile.ZIP_DEFLATED)
            for item in filelists:      
               
                f.write(item,item.replace(get.path,''))       
            f.close()  
            
            self.SetFileAccept(get.dfile);
            public.WriteLog("TYPE_FILE", 'ZIP_SUCCESS',(get.sfile,get.dfile));
            return public.returnMsg(True,'ZIP_SUCCESS')
        except:
            return public.returnMsg(False,'ZIP_ERR')
    
    #获取文件列表
    def GetFileList(self,path, list): 
        if os.path.exists(path):            
            files = os.listdir(path)
            list.append(path)
            for file in files:           
                if os.path.isdir(path + '/' + file):
                    self.GetFileList(path + '/' + file, list)
                else:
                    list.append(path + '/' + file)

    #文件解压
    def UnZip(self,get):
        if not os.path.exists(get.sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS');
        try:
            if not hasattr(get,'password'): get.password = '';               
            if not os.path.exists(get.dfile) : os.makedirs(get.dfile)

            ext = os.path.splitext(get.sfile)[-1]      
            if ext == '.zip': 
                import zipfile
                zip_file = zipfile.ZipFile(get.sfile)  
                for names in zip_file.namelist():  
                    zip_file.extract(names, get.dfile,get.password.encode('utf-8'))  
                zip_file.close()
            elif ext == '.rar':
                from unrar import rarfile
                rar = rarfile.RarFile(get.sfile)                               
                rar.extractall(path = get.dfile,pwd = get.password)                    
            elif  ext == '.gz':
                return public.returnMsg(False,'未识别压缩包格式!')
            
            public.WriteLog("TYPE_FILE", 'UNZIP_SUCCESS',(get.sfile,get.dfile));
            return public.returnMsg(True,'UNZIP_SUCCESS');
        except Exception as ex:
            return public.returnMsg(False,'文件解压失败 --> ' + str(ex))
        
    #获取文件/目录 权限信息
    def GetFileAccess(self,get):
        filename = get.filename

        if not os.path.exists(filename): return public.returnMsg(False,'文件不存在!')        
        try:
            import win32security
            sd = win32security.GetFileSecurity(filename, win32security.DACL_SECURITY_INFORMATION)
            dacl = sd.GetSecurityDescriptorDacl()
            ace_count = dacl.GetAceCount()
            data = {}
            data['path'] = filename
            arrs = []
            for i in range(0, ace_count):
                try:
                    temp = {}
                    rev, access, usersid = dacl.GetAce(i)
                    if len(rev)==2:
                        if access >= 1179785:
                            current = False
                            if rev[1] == 3: current = False
                            temp['current'] = current
                            temp['access'] = access
                            temp['user'],temp['group'],type = win32security.LookupAccountSid('', usersid)
                            is_true = False;
                            for user in arrs:
                                if user['user']==temp['user']:
                                    is_true  = True
                                    if access > user['access']:
                                        user['access'] = access                  
                            if not is_true: arrs.append(temp)
                except : pass
            data['list'] = arrs
            return data;
        except Exception as ex:
            return public.returnMsg(False,str(ex))

    #设置文件权限和所有者
    def SetFileAccess(self,get,all = '-R'):
        filename = get.filename
        try:
            access = int(get.access)
        except : return public.returnMsg(False,'设置文件权限失败，未识别的权限.')

        level = 1;
        if hasattr(get,'level'): level = int(get.level)

        if not os.path.exists(filename): return public.returnMsg(False,'FILE_NOT_EXISTS')
        self.SetFileAccept(filename)   

        try:
            #是否继承
            if level:            
                if os.path.isdir(filename):
                    list = []
                    self.GetFileList(filename,list)
                    for new_path in list: self.set_file_access(new_path,get.user,access)
                else:
                    self.set_file_access(filename,get.user,access)
            else:
                self.set_file_access(filename,get.user,access)
            
            public.WriteLog('TYPE_FILE','FILE_ACCESS_SUCCESS',(get.filename,str(get.access),get.user))
            return public.returnMsg(True,'SET_SUCCESS')
        except:
            return public.returnMsg(False,'SET_ERROR')

    #删除User权限
    def SetFileAccept(self,filename):
        self.del_file_access(filename,"users")
        return True

    #删除目录权限
    def DelFileAccess(self,get):
        filename = get.filename
        level = 1;
        if hasattr(get,'level'): level = int(get.level)

        #是否继承
        if level:            
            if os.path.isdir(filename):
                list = []
                self.GetFileList(filename,list)
                for new_path in list: self.del_file_access(new_path,get.user)
            else:
                self.del_file_access(filename,get.user)
        else:
            self.del_file_access(filename,get.user)
        return public.returnMsg(True,'删除【'+get.user+'】权限成功!')

    #设置文件权限
    def set_file_access(self,filename,user,access):
        import win32security
        sd = win32security.GetFileSecurity(filename, win32security.DACL_SECURITY_INFORMATION)
        dacl = sd.GetSecurityDescriptorDacl()
        ace_count = dacl.GetAceCount()

        for i in range(ace_count, 0,-1):  
            try:
                data = {}
                data['rev'], data['access'], usersid = dacl.GetAce(i-1)
                data['user'],data['group'], data['type'] = win32security.LookupAccountSid('', usersid)                
                if data['user'].lower() == user.lower(): dacl.DeleteAce(i-1) #删除旧的dacl
            except :
                dacl.DeleteAce(i-1)
        try:
            userx, domain, type = win32security.LookupAccountName("", user)
        except :
            userx, domain, type = win32security.LookupAccountName("", 'IIS APPPOOL\\' + user)       
        if access > 0:  dacl.AddAccessAllowedAceEx(win32security.ACL_REVISION, 3, access, userx)
            
        sd.SetSecurityDescriptorDacl(1, dacl, 0)
        win32security.SetFileSecurity(filename, win32security.DACL_SECURITY_INFORMATION, sd)

    #删除文件权限
    def del_file_access(self,filename,user):
        import win32security
        sd = win32security.GetFileSecurity(filename, win32security.DACL_SECURITY_INFORMATION)
        dacl = sd.GetSecurityDescriptorDacl()
        ace_count = dacl.GetAceCount()
        
        for i in range(ace_count ,0 ,-1):            
            try:
                data = {}
                data['rev'], data['access'], usersid = dacl.GetAce(i-1)
                data['user'],data['group'], data['type'] = win32security.LookupAccountSid('', usersid)     
                if data['user'].lower() == user.lower():
                    dacl.DeleteAce(i-1)
            except :
                try:
                    #处理拒绝访问
                    dacl.DeleteAce(i-1)
                except : pass                
        sd.SetSecurityDescriptorDacl(1, dacl, 0)
        win32security.SetFileSecurity(filename, win32security.DACL_SECURITY_INFORMATION, sd)
        return True

    #取目录大小
    def GetDirSize(self,get):
        total = 0
        try:
            filesize = 0
            fileList = []
            self.GetFileList(get.path,fileList)
            for filename in fileList:
                 if os.path.isfile(filename): 
                    filesize += os.path.getsize(filename)
            total = public.to_size(filesize)
        except :
            total = public.to_size(0)
        return total
    
    def CloseLogs(self,get):
        get.path = public.GetConfigValue('root_path')
        os.system('rm -f '+public.GetConfigValue('logs_path')+'/*')
        if public.get_webserver() == 'nginx':
            os.system('kill -USR1 `cat '+public.GetConfigValue('setup_path')+'/nginx/logs/nginx.pid`');
        else:
            os.system('/etc/init.d/httpd reload');
        
        public.WriteLog('TYPE_FILE','SITE_LOG_CLOSE')
        get.path = public.GetConfigValue('logs_path')
        return self.GetDirSize(get)
            
    #批量操作
    def SetBatchData(self,get):

        if get.type == '1' or get.type == '2':
            session['selected'] = get
            return public.returnMsg(True,'FILE_ALL_TIPS')
        elif get.type == '3':
            for key in json.loads(get.data):
                try:
                    filename = get.path+'/' + key;
                    if not self.CheckDir(filename): return public.returnMsg(False,'FILE_DANGER');
                except:
                    continue;
            public.WriteLog('TYPE_FILE','FILE_ALL_ACCESS')
            return public.returnMsg(True,'FILE_ALL_ACCESS')
        else:
            import shutil
            isRecyle = os.path.exists('data/recycle_bin.pl')
            path = get.path
            get.data = json.loads(get.data)
            l = len(get.data);
            i = 0;
            for key in get.data:
                try:
                    filename = path + '/'+ key;
                    get.path = filename;
                    if not os.path.exists(filename): continue
                    i += 1;
                    public.writeSpeed(key,i,l);
                    if os.path.isdir(filename):
                        if not self.CheckDir(filename): return public.returnMsg(False,'FILE_DANGER');
                        if isRecyle:
                            self.Mv_Recycle_bin(get)
                        else:
                            shutil.rmtree(filename)
                    else:
                        if isRecyle:                            
                            self.Mv_Recycle_bin(get)
                        else:
                            os.remove(filename)
                except: continue;
                public.writeSpeed(None,0,0);
            public.WriteLog('TYPE_FILE','FILE_ALL_DEL')
            return public.returnMsg(True,'FILE_ALL_DEL')
        
    #批量粘贴
    def BatchPaste(self,get):
        import shutil
        if not self.CheckDir(get.path): return public.returnMsg(False,'FILE_DANGER');
        i = 0;

        if not 'selected' in session:  return public.returnMsg(False,'操作失败，请重新操作.');

        try:
            myfiles = json.loads(session['selected']['data'])
            l = len(myfiles);
            if get.type == '1':
                for key in myfiles:
                    i += 1
                    public.writeSpeed(key,i,l);
                    #try:
                    if sys.version_info[0] == 2:
                        sfile = session['selected']['path'] + '/' + key.encode('utf-8')
                        dfile = get.path + '/' + key.encode('utf-8')
                    else:
                        sfile = session['selected']['path'] + '/' + key
                        dfile = get.path + '/' + key

                    if not os.path.exists(sfile): continue
         
                    if os.path.isdir(sfile):                
                        public.copytree(sfile,dfile)
                    else:
                        shutil.copyfile(sfile,dfile)
                    #except:
                        #continue;
                public.WriteLog('TYPE_FILE','FILE_ALL_COPY',(session['selected']['path'],get.path))
            else:
                for key in myfiles:
                    try:
                        i += 1
                        public.writeSpeed(key,i,l);
                        if sys.version_info[0] == 2:
                            sfile = session['selected']['path'] + '/' + key.encode('utf-8')
                            dfile = get.path + '/' + key.encode('utf-8')
                        else:
                            sfile = session['selected']['path'] + '/' + key
                            dfile = get.path + '/' + key
                        public.move(sfile,dfile)
                    except:
                        continue;
                public.WriteLog('TYPE_FILE','FILE_ALL_MOTE',(session['selected']['path'],get.path))
            public.writeSpeed(None,0,0);
            errorCount = len(myfiles) - i
            del(session['selected'])
            return public.returnMsg(True,'FILE_ALL',(str(i),str(errorCount)));
        except Exception as ex:
            return public.returnMsg(True,'批量粘贴失败 --> ' + str(ex));
            
    #下载文件
    def DownloadFile(self,get):

        import db,time
        isTask = 'data/panelTask.pl'
        execstr = get.url +'|bt|'+get.path+'/'+get.filename
        sql = db.Sql()
        sql.table('tasks').add('name,type,status,addtime,execstr',('下载文件['+get.filename+']','download','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
        public.writeFile(isTask,'True')
     
        public.WriteLog('TYPE_FILE','FILE_DOWNLOAD',(get.url , get.path));
        return public.returnMsg(True,'FILE_DOANLOAD')
    
    #删除任务队列
    def RemoveTask(self,get):
        try:
            name = public.M('tasks').where('id=?',(get.id,)).getField('name');
            status = public.M('tasks').where('id=?',(get.id,)).getField('status');
            public.M('tasks').delete(get.id);
            if status == '-1':
                pass
        except:
            public.set_server_status('btTask','restart')
        return public.returnMsg(True,'PLUGIN_DEL');
    
    #重新激活任务
    def ActionTask(self,get):
        isTask = os.getenv("BT_PANEL") + '/data/panelTask.pl'
        public.writeFile(isTask,'True');
        return public.returnMsg(True,'PLUGIN_ACTION');       
    
    #卸载软件
    def UninstallSoft(self,get):
        panel_path = os.getenv("BT_PANEL")

        execstr = public.get_run_python('%s && cd %s/install && [PYTHON] -u install_soft.py uninstall phplib %s %s' % (panel_path[0:2],panel_path,get.version,get.name))
   
        public.ExecShell(execstr)
        public.WriteLog('TYPE_SETUP','PLUGIN_UNINSTALL',(get.name,get.version));
        return public.returnMsg(True,"PLUGIN_UNINSTALL");
        
    #添加安装任务
    def InstallSoft(self,get):
        import db,time
        
        panel_path = panel_path = os.getenv("BT_PANEL")
        isTask = panel_path + '/data/panelTask.pl'

        execstr = public.get_run_python('%s && cd %s/install && [PYTHON] -u install_soft.py install phplib %s %s' % (panel_path[0:2],panel_path,get.version,get.name))
        sql = db.Sql()
        if hasattr(get,'id'):
            id = get.id;
        else:
            id = None;

        sql.table('tasks').add('id,name,type,status,addtime,execstr',(None,'安装['+get.name+'-'+get.version+']','execshell','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
        public.writeFile(isTask,'True')
        public.WriteLog('TYPE_SETUP','PLUGIN_ADD',(get.name,get.version));
        time.sleep(0.1);
        return public.returnMsg(True,'PLUGIN_ADD');
    
    #取任务队列进度
    def GetTaskSpeed(self,get):
        setup_path = public.GetConfigValue('setup_path')

        tempFile = setup_path + '/panel/data/panelExec.log'
        freshFile = setup_path + '/panel/data/panelFresh'
        import db
        find = db.Sql().table('tasks').where('status=? OR status=?',('-1','0')).field('id,type,name,execstr').find()
        if not len(find): return public.returnMsg(False,'当前没有任务队列在执行-2!')
        isTask = setup_path + '/panel/data/panelTask.pl'
        public.writeFile(isTask,'True');
        echoMsg = {}
        echoMsg['name'] = find['name']
        echoMsg['execstr'] = find['execstr']
        if find['type'] == 'download':
            try:
                tmp = public.readFile(tempFile)
                if len(tmp) < 10:
                    return public.returnMsg(False,'当前没有任务队列在执行-3!')
                echoMsg['msg'] = json.loads(tmp)
                echoMsg['isDownload'] = True
            except:
                db.Sql().table('tasks').where("id=?",(find['id'],)).save('status',('0',))
                return public.returnMsg(False,'当前没有任务队列在执行-4!')
        else:
            echoMsg['msg'] = self.GetLastLine(tempFile,20)
            echoMsg['isDownload'] = False
        
        echoMsg['task'] = public.M('tasks').where("status!=?",('1',)).field('id,status,name,type').order("id asc").select()
        return echoMsg
    
    #取执行日志
    def GetExecLog(self,get):
        return self.GetLastLine(public.GetConfigValue('setup_path') + '/panel/data/panelExec.log',100);
                 
    #读文件指定倒数行数
    def GetLastLine(self,inputfile,lineNum):
        result = public.GetNumLines(inputfile,lineNum)
        if len(result) < 1:
            return public.getMsg('TASK_SLEEP');
        return result        
    
    #执行SHELL命令
    def ExecShell(self,get):
        return False
    
    #取SHELL执行结果
    def GetExecShellMsg(self,get):
        fileName = os.getenv("BT_PANEL") + '/data/panelShell.pl';
        if not os.path.exists(fileName): return 'FILE_SHELL_EMPTY';
        return public.readFile(os.getenv("BT_PANEL") + '/data/panelShell.pl');
    
    #文件搜索
    def GetSearch(self,get):
        if not os.path.exists(get.path): return public.returnMsg(False,'DIR_NOT_EXISTS');
        return public.ExecShell("find "+get.path+" -name '*"+get.search+"*'");

    #保存草稿
    def SaveTmpFile(self,get):
        save_path = os.getenv("BT_PANEL") + '/temp'
        if not os.path.exists(save_path): os.makedirs(save_path)
        get.path = os.path.join(save_path,public.Md5(get.path) + '.tmp')
        public.writeFile(get.path,get.body)
        return public.returnMsg(True,'已保存')

    #获取草稿
    def GetTmpFile(self,get):
        self.CleanOldTmpFile()
        save_path = os.getenv("BT_PANEL") + '/temp'
        if not os.path.exists(save_path): os.makedirs(save_path)
        src_path = get.path
        get.path = os.path.join(save_path,public.Md5(get.path) + '.tmp')
        if not os.path.exists(get.path): return public.returnMsg(False,'没有可用的草稿!')
        data = self.GetFileInfo(get.path)
        data['file'] = src_path
        if 'rebody' in get: data['body'] = public.readFile(get.path)
        return data

    #清除过期草稿
    def CleanOldTmpFile(self):
        if 'clean_tmp_file' in session: return True
        save_path = os.getenv("BT_PANEL") + '/temp'
        max_time = 86400 * 30
        now_time = time.time()
        for tmpFile in os.listdir(save_path):
            filename = os.path.join(save_path,tmpFile)
            fileInfo = self.GetFileInfo(filename)
            if now_time - fileInfo['modify_time'] > max_time: os.remove(filename)
        session['clean_tmp_file'] = True
        return True   

    def get_store_data(self):
        data = {}
        path = 'data/file_store.json'
        try:
            if os.path.exists(path):
                data = json.loads(public.readFile(path))
        except :
            data = {}
        if not data:
            data['默认分类'] = []
        return data

    def set_store_data(self,data):
        public.writeFile('data/file_store.json',json.dumps(data))
        return True

    #添加收藏夹分类
    def add_files_store_types(self,get):
        file_type = get.file_type
        data = self.get_store_data()
        print(file_type,data)
        if file_type in data:  return public.returnMsg(False,'请勿重复添加分类!') 
        
        data[file_type] = []
        self.set_store_data(data)
        return public.returnMsg(True,'添加收藏夹分类成功!') 
     
    #删除收藏夹分类
    def del_files_store_types(self,get):
        file_type = get.file_type
        if file_type == '默认分类': return public.returnMsg(False,'默认分类不可被删除!') 
        data = self.get_store_data()
        del data[file_type]
        self.set_store_data(data)
        return public.returnMsg(True,'删除[' + file_type + ']成功!') 

    #获取收藏夹
    def get_files_store(self,get):
        data = self.get_store_data()
        result = []
        for key in data:
            rlist = []
            for path in data[key]:
                info = { 'path': path,'name':os.path.basename(path)}

                if os.path.isdir(path) :
                    info['type'] = 'dir'
                else:
                    info['type'] = 'file'
                rlist.append(info)
            result.append({'name':key,'data':rlist})           
        return result

    #添加收藏夹
    def add_files_store(self,get):
        file_type = get.file_type
        path = get.path
        if not os.path.exists(path):  return public.returnMsg(False,'文件或目录不存在!') 
            
        data = self.get_store_data()
        if path in data[file_type]:  return public.returnMsg(False,'请勿重复添加!') 
        
        data[file_type].append(path)
        self.set_store_data(data)
        return public.returnMsg(True,'添加成功!') 

    #删除收藏夹
    def del_files_store(self,get):
        file_type = get.file_type
        path = get.path

        data = self.get_store_data()
        if not file_type in data:  return public.returnMsg(False,'找不到此收藏夹分类!') 
        data[file_type].remove(path)
        if len(data[file_type]) <= 0: data[file_type] = []

        self.set_store_data(data)
        return public.returnMsg(True,'删除成功!') 

    #取指定文件信息
    def GetFileInfo(self,path):
        if not os.path.exists(path): return False
        stat = os.stat(path)
        fileInfo = {}
        fileInfo['modify_time'] = int(stat.st_mtime)
        fileInfo['size'] = os.path.getsize(path)
        return fileInfo

    #取目录大小
    def get_path_size(self,get):
        data = {}
        data['path'] = get.path
        data['size'] = public.get_path_size(get.path)
        return data

    #恢复网站权限（仅适配apache下www权限）
    def re_webserver_access(self,get):
        user = 'www'

        data = public.M('config').where("id=?",('1',)).field('sites_path').find();
        #完全控制权限
        paths = ["C:/Temp",public.GetConfigValue('logs_path'),os.getenv("BT_SETUP") + '/' + public.get_webserver(),data['sites_path']]        
        #只读权限
        flist = [  ]
        for x in paths: public.get_paths(x,flist)
        
        #批量设置只读权限
       
        get.user = user
        get.access = 1179785
        get.level = 0
        for f in flist:    
            get.filename = f     
            self.SetFileAccess(get)

        for f in paths:    
            get.level = 0
            get.access = 2032127
            get.filename = f     
            self.SetFileAccess(get)
       
        return public.returnMsg(True,'权限恢复成功，当前仅恢复Apache启动所需权限，网站权限需要手动恢复!')

        
       
