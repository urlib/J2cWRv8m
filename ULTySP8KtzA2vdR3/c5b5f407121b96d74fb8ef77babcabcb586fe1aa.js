var bt = {
	os : 'Linux',
	check_ip(ip) //验证ip
	{
		var reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
		return reg.test(ip);
	},
	check_ips(ips)//验证ip段
	{
		var reg = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$/;
		return reg.test(ip);
	},
	check_url(url) //验证url
	{
		var reg = /^((https|http|ftp|rtsp|mms)?:\/\/)[^\s]+/;
		return reg.test(url);
	},
	check_chinese(str)
	{
		var reg = /[\u4e00-\u9fa5]/;
		return reg.test(url);
	},
	check_domain(domain) //验证域名
	{	
		var reg = /^([\w\-\*]{1,100}\.){1,4}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$/;
		return reg.test(domain);
	},
	check_img(fileName) //验证是否图片
	{
		var exts = ['jpg','jpeg','png','bmp','gif','tiff','ico'];
		return bt.check_exts(fileName,exts);
	},
	check_zip(fileName)
	{
		var ext = fileName.split('.');
		var extName = ext[ext.length-1].toLowerCase();
		if( extName == 'zip') return 0;
		if( extName == 'gz' || extName == 'tgz') return 1;
		return -1;
	},
	check_text(fileName)
	{
		var exts = ['rar','zip','tar.gz','gz','iso','xsl','doc','xdoc','jpeg','jpg','png','gif','bmp','tiff','exe','so','7z','bz'];
		return bt.check_exts(fileName,exts)?false:true;
	},
	check_exts(fileName,ext)
	{
		var ext = fileName.split('.');
		if(ext.length < 2) return false;
		var extName = ext[ext.length-1].toLowerCase();
		for(var i=0;i<exts.length;i++){
			if(extName == exts[i]) return true;
		}
		return false;
	},
	get_file_ext(fileName)
	{
		var text = fileName.split(".");
		var n = text.length-1;
		text = text[n];
		return text;
	},	
	contains(str,substr) //验证是否包含字符串
	{
		return str.indexOf(substr) >= 0;
	},
	format_size(bytes ,is_unit = true,fixed = 2, end_unit = '') //字节转换，到指定单位结束 is_unit：是否显示单位  fixed：小数点位置 end_unit：结束单位
	{
		var unit = [' B',' KB',' MB',' GB','TB'];
		var c = 1024;
		for(var i=0;i<unit.length;i++){
			var cUnit = unit[i];		
			if(bytes < c || cUnit.trim() == end_unit.trim()){			
				return (i==0?bytes:bytes.toFixed(fixed)) + (is_unit?cUnit:'');
			}
			bytes /= c;
		}
	},
	format_data(tm)
	{
		tm  = tm.toString();
		if(tm.length > 10){
			tm = tm.substring(0,10);
		}	
		var data = new Date(parseInt(tm) * 1000);
		var format = "yyyy/MM/dd hh:mm:ss";
		 var o = {
		 "M+" : data.getMonth()+1, //month
		 "d+" : data.getDate(),    //day
		 "h+" : data.getHours(),   //hour
		 "m+" : data.getMinutes(), //minute
		 "s+" : data.getSeconds(), //second
		 "q+" : Math.floor((data.getMonth()+3)/3),  //quarter
		 "S" : data.getMilliseconds() //millisecond
		 }
		 if(/(y+)/.test(format)) format=format.replace(RegExp.$1,
		 (data.getFullYear()+"").substr(4 - RegExp.$1.length));
		 for(var k in o)if(new RegExp("("+ k +")").test(format))
		 format = format.replace(RegExp.$1,
		 RegExp.$1.length==1 ? o[k] : ("00"+ o[k]).substr((""+ o[k]).length));
		 
		return format;
	},
	get_random(len)
	{
		len = len || 32;
		var $chars = 'AaBbCcDdEeFfGHhiJjKkLMmNnPpRSrTsWtXwYxZyz2345678'; // 默认去掉了容易混淆的字符oOLl,9gq,Vv,Uu,I1  
		var maxPos = $chars.length;
		var pwd = '';
		for (i = 0; i < len; i++) {
			pwd += $chars.charAt(Math.floor(Math.random() * maxPos));
		}
		return pwd;
	},
	refresh_pwd(length,obj = '.MyPassword')
	{
		$(obj).val(bt.get_random(length))
	},
	get_random_num(min,max) //生成随机数
	{
		var range = max - min;
	    var rand = Math.random();
	    var num = min + Math.round(rand * range); //四舍五入
	    return num;
	},
	set_cookie(key,val)
	{
		var Days = 30;
		var exp = new Date();
		exp.setTime(exp.getTime() + Days*24*60*60*1000);
		document.cookie = key + "="+ escape (val) + ";expires=" + exp.toGMTString();
	},
	get_cookie(key)
	{
		var arr,reg=new RegExp("(^| )"+key+"=([^;]*)(;|$)");
		if(arr=document.cookie.match(reg)){
			return unescape(arr[2]);
		}else{
			return null;
		}
	},
	show_confirm(title, msg, fun, error) 
	{
		if(error == undefined) {
			error = ""
		}
		var d = Math.round(Math.random() * 9 + 1);
		var c = Math.round(Math.random() * 9 + 1);
		var e = "";
		e = d + c;
		sumtext = d + " + " + c;

		bt.set_cookie("vcodesum", e);

		var mess = layer.open({
			type: 1,
			title: title,
			area: ["350px","240px"],
			closeBtn: 1,
			shadeClose: true,
			content: "<div class='layui-form layui-show-confirm layui-form-alert'>\
								<div class='layui-confirm-title'>"+ msg + error +"</div>\
								<div class='layui-form-item layui-confirm-input'>\
									<label class='layui-form-label'>"+ lan.bt.cal_msg +"</label>\
									<div class='layui-input-block'><span class='layui-confirm-text'>" + sumtext + " = </span><input type='number' name='vcode' min='0'  autocomplete='off' class='layui-input'></div>\
								</div>\
								<div class='bt-form-submit-btn'>\
									<button type='button' class='layui-btn layui-btn-sm' lay-event='confirm_del'>"+ lan.public.submit +"</button>\
									<button type='button' class='layui-btn layui-btn-sm layui-btn-primary' onclick='layer.closeAll();'>"+ lan.public.cancel +"</button>\
								</div>\
							</div>"
		});

		$("[name='vcode']").keyup(function(a) {
			if(a.keyCode == 13) {
				$("[lay-event='confirm_del']").click()
			}
		});
		$("[lay-event='confirm_del']").click(function() {
			var a =$("[name='vcode']").val().replace(/ /g, "");
			if(a == undefined || a == "") {
				bt.msg({status:false,msg:lan.bt.cal_err});
				return
			}
			if(a != bt.get_cookie("vcodesum")) {
				bt.msg({status:false,msg:lan.bt.cal_err});
				return
			}
			layer.close(mess);
			fun();
		})
	},
	to_login()
	{
		bt.confirm({title:'会话已过期',msg:'您的登陆状态已过期，请重新登陆!',icon:2,closeBtn:1,shift:5},function(){
			location.reload();
		});
	},
	do_login()
	{
		bt.confirm({msg:lan.bt.loginout,closeBtn:1},function(){
			window.location.href = "/login?dologin=True"
		});
	},
	send(response,module,data,callback,sType=0)
	{
		console.time(response);
		if(!response) alert(lan.get('lack_param',['response']));
		modelTmp = module.split('/')
		if(modelTmp.length<2)   alert(lan.get('lack_param',['s_module','action']));	
		if(bt.os == 'Linux' && sType === 0)
		{		
			socket.on(response,function(rdata){
				socket.removeAllListeners(response);
				var rRet = rdata.data;
				if(rRet.status===-1)
				{
					bt.to_login();
					return;
				}
				console.timeEnd(response);
			    callback(rRet);
			});
			if(!data) data = {};
			data = bt.linux_format_param(data);
			data['s_response'] = response;
			data['s_module'] = modelTmp[0];
			data['action'] = modelTmp[1];
			console.log(data);
			socket.emit('panel',data)
		}
		else{
			data = bt.win_format_param(data);
			url = '/' + modelTmp[0] + '?action=' + modelTmp[1];
			$.post(url,data,function(rdata){
				callback(rdata);
			})
		}
	},
	linux_format_param(param)
	{		
		if(typeof param == 'string')
		{
			var data= {};
			arr = param.split('&');		
			var reg = /(^[^=]*)=(.*)/;
			var arr_p = ['path','file','fileName','filePath'];
			for (var i=0;i<arr.length;i++) {
				var tmp = arr[i].match(reg);
				if(tmp.length>=3){
					data[tmp[1]] =  tmp[2]=='undefined'?'': decodeURIComponent(tmp[2]);
				}
			}
			return data;	
		}
		return param;
	},
	win_format_param(param)
	{
		if(typeof data == 'object')
		{
			var data = '';
			for(var key in param){
			 	data+=key+'='+param[key]+'&';
			}
			if(data.length>0) data = data.substr(0,data.length-1);
			return data;
		}
		return param;
	},
	msg(config)
	{		
		var btns = new Array();  
		var btnObj =  {						
			title:config.title?config.title:false,						
			shadeClose: config.shadeClose?config.shadeClose:true,
			closeBtn: config.closeBtn?config.closeBtn:0,	
			scrollbar:true,
			shade:0.3,
		};
		if(!config.hasOwnProperty('time')) config.time = 2000;	
		if(config.hasOwnProperty('icon')){
			if(typeof config.icon=='boolean') config.icon = config.icon?1:2;
		}
		else if(config.hasOwnProperty('status'))
		{
			config.icon=config.status?1:2;
		}
		if(config.icon) btnObj.icon = config.icon;
		var msg = ''
		if(config.msg) msg += config.msg;
		if(config.msg_error) msg+=config.msg_error;
		if(config.msg_solve) msg+=config.msg_solve;
		
		console.log(btnObj)
		layer.msg(msg,btnObj);	
	},
	confirm(config,callback){
		var btnObj =  {						
			title:config.title?config.title:false,
			time : config.time?config.time:0,					
			shadeClose: config.shadeClose?config.shadeClose:true,
			closeBtn: config.closeBtn?config.closeBtn:1,	
			scrollbar:true,
			shade:0.3,
			icon:3
		};
		layer.confirm(config.msg, btnObj, function(index){
		  	callback(index);
		});
	},
	load(msg)  
	{
		if(!msg) msg = lan.public.the;
		var loadT = layer.msg(msg,{icon:16,time:0,shade: [0.3, '#000']});
		load = {
			form : loadT,
			close:function(){
				layer.close(load.form);
			}
		}
		return load;
	},
	open(config)
	{
		config.closeBtn = 1;
		var loadT = layer.open(config);
		var load = {
			form : loadT,
			close:function(){
				layer.close(load.form);
			}
		}
		return load;
	}
	
};

if(bt.os=='Linux') socket = io.connect();

bt.pub = {
	set_server_status(serverName,type)
	{
		if(!isNaN(serverName)) {
			serverName = "php-fpm-" + serverName
		}
		serverName = serverName.replace('_soft','');
		var data = "name=" + serverName + "&type=" + type;
		var msg = lan.bt[type];
		bt.confirm({msg:lan.get('service_confirm',[msg,serverName])},function(){
			
			var load = bt.load(lan.get('service_the',[msg,serverName]))		
			bt.send('system','system/ServiceAdmin',data,function(rdata){				
				load.close();
				var f = rdata.status ? lan.get('service_ok',[serverName,msg]):lan.get('service_err',[serverName,msg]);
				bt.msg({msg:f,icon:rdata.status})
			
				if(type != "reload" && rdata.status) {
					setTimeout(function() {
						window.location.reload()
					}, 1000)
				}
				if(!rdata.status) {
					bt.msg(rdata);
				}
			})
		})
	
	},		
	on_edit_file(type, fileName) {
		if(type != 0) {			
			var l = $("#PathPlace input").val();
			var body = encodeURIComponent($("#textBody").val());			
			var encoding = $("select[name=encoding]").val();
			var loadT = bt.load(lan.bt.save_file);
			bt.send('SaveFileBody','files/SaveFileBody',"data=" + body + "&path=" + fileName + "&encoding=" + encoding,function(rdata){
				if(type == 1) {
					loadT.close();
				}
				bt.msg(rdata);				
			})	
			return;
		}
		var loading = bt.load(lan.bt.read_file);
		ext = bt.get_file_ext(fileName);
		doctype = '';
		switch(ext)
		{
			case "html":
				var mixedMode = {
					name: "htmlmixed",
					scriptTypes: [{
						matches: /\/x-handlebars-template|\/x-mustache/i,
						mode: null
					}, {
						matches: /(text|application)\/(x-)?vb(a|script)/i,
						mode: "vbscript"
					}]
				};
				doctype = mixedMode;
				break;
			case "htm":
				var mixedMode = {
					name: "htmlmixed",
					scriptTypes: [{
						matches: /\/x-handlebars-template|\/x-mustache/i,
						mode: null
					}, {
						matches: /(text|application)\/(x-)?vb(a|script)/i,
						mode: "vbscript"
					}]
				};
				doctype = mixedMode;
				break;
			case "js":
				doctype = "text/javascript";
				break;
			case "json":
				doctype = "application/ld+json";
				break;
			case "css":
				doctype = "text/css";
				break;
			case "php":
				doctype = "application/x-httpd-php";
				break;
			case "tpl":
				doctype = "application/x-httpd-php";
				break;
			case "xml":
				doctype = "application/xml";
				break;
			case "sql":
				doctype = "text/x-sql";
				break;
			case "conf":
				doctype = "text/x-nginx-conf";
				break;
			default:
				var mixedMode = {
					name: "htmlmixed",
					scriptTypes: [{
						matches: /\/x-handlebars-template|\/x-mustache/i,
						mode: null
					}, {
						matches: /(text|application)\/(x-)?vb(a|script)/i,
						mode: "vbscript"
					}]
				};
				doctype = mixedMode;
				break;
		}		
		bt.send('GetFileBody','files/GetFileBody','path='+fileName,function(rdata){
			if(!rdata.status){
				rdata.icon = 5;
				bt.msg(rdata);
				return;
			}
			
			loading.close();
			var u = ["utf-8", "GBK", "GB2312", "BIG5"];
			var n = "";
			var m = "";
			var o = "";
			for(var p = 0; p < u.length; p++) {
				m = rdata.encoding == u[p] ? "selected" : "";
				n += '<option value="' + u[p] + '" ' + m + ">" + u[p] + "</option>"
			}
			var r = bt.open({
				type: 1,
				shift: 5,
				closeBtn: 1,
				maxmin: true,
				area: ["90%", "90%"],
				shade:false,
				title: lan.bt.edit_title+"[" + fileName + "]",
				content: '<form class="bt-form pd20 pb70"><div class="line"><p style="color:red;margin-bottom:10px">'+lan.bt.edit_ps
					+'			<select class="bt-input-text" name="encoding" style="width: 74px;position: absolute;top: 31px;right: 19px;height: 22px;z-index: 9999;border-radius: 0;">' 
					+ n + '</select></p><textarea class="mCustomScrollbar bt-input-text" id="textBody" style="width:100%;margin:0 auto;line-height: 1.8;position: relative;top: 10px;" value="" />			</div>			<div class="bt-form-submit-btn" style="position:absolute; bottom:0; width:100%">			<button type="button" class="btn btn-danger btn-sm btn-editor-close">'+lan.public.close+'</button>			<button id="OnlineEditFileBtn" type="button" class="btn btn-success btn-sm">'+lan.public.save+'</button>			</div>			</form>'
			})
			$("#textBody").text(rdata.data);
			var q = $(window).height() * 0.9;
			$("#textBody").height(q - 160);
			var t = CodeMirror.fromTextArea(document.getElementById("textBody"), {
				extraKeys: {
					"Ctrl-F": "findPersistent",
					"Ctrl-H": "replaceAll",
					"Ctrl-S": function() {
						$("#textBody").text(t.getValue());
						OnlineEditFile(2, f)
					}
				},
				mode: doctype,
				lineNumbers: true,
				matchBrackets: true,
				matchtags: true,
				autoMatchParens: true
			});
			t.focus();
			t.setSize("auto", q - 150);
			$("#OnlineEditFileBtn").click(function() {
				$("#textBody").text(t.getValue());
				OnlineEditFile(1, f);
			});
			$(".btn-editor-close").click(function() {
				r.close();
			});
		})
	},
	bind_btname(a,type)
	{
		var titleName = lan.config.config_user_binding;
		if(type == "b"){
			btn = "<button type='button' class='btn btn-success btn-sm' onclick=\"bindBTName(1,'b')\">"+lan.config.binding+"</button>";
		}
		else{
			titleName = lan.config.config_user_edit;
			btn = "<button type='button' class='btn btn-success btn-sm' onclick=\"bindBTName(1,'c')\">"+lan.public.edit+"</button>";
		}
		if(a == 1) {
			p1 = $("#p1").val();
			p2 = $("#p2").val();
			var loadT = bt.load(lan.config.token_get);
			bt.send('GetToken','ssl/GetToken',"username=" + p1 + "&password=" + p2,function(rdata){
				loadT.close();
				bt.msg(rdata);
				if(b.status) {
					window.location.reload();
					$("input[name='btusername']").val(p1);
				}
			})
			return;
		}
		bt.open({
			type: 1,
			area: "290px",
			title: titleName,
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content: "<div class='bt-form pd20 pb70'><div class='line'><span class='tname'>"+lan.public.user+"</span><div class='info-r'><input class='bt-input-text' type='text' name='username' id='p1' value='' placeholder='"+lan.config.user_bt+"' style='width:100%'/></div></div><div class='line'><span class='tname'>"+lan.public.pass+"</span><div class='info-r'><input class='bt-input-text' type='password' name='password' id='p2' value='' placeholder='"+lan.config.pass_bt+"' style='width:100%'/></div></div><div class='bt-form-submit-btn'><button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">"+lan.public.cancel+"</button> "+btn+"</div></div>"
		})
	},
	unbind_bt()
	{
		var name = $("input[name='btusername']").val();
		bt.confirm({msg:lan.config.binding_un_msg,title:lan.config.binding_un_title},function(){
			bt.send('DelToken','ssl/DelToken',{},function(rdata){
				bt.msg(rdata);
				$("input[name='btusername']").val('');
			})
		})
	}
};

bt.weixin = {
	settiming:'',
	relHeight:500,
	relWidth:500,
	userLength:'',
	init(){
		var _this = this;
		$('.layui-layer-page').css('display', 'none');
		$('.layui-layer-page').width(_this.relWidth);
		$('.layui-layer-page').height(_this.relHeight);
		$('.bt-w-menu').height((_this.relWidth - 1) - $('.layui-layer-title').height());
		var width = $(document).width();
		var height = $(document).height();
		var boxwidth =  (width / 2) - (_this.relWidth / 2);
		var boxheight =  (height / 2) - (_this.relHeight / 2);
		$('.layui-layer-page').css({
			'left':boxwidth +'px',
			'top':boxheight+'px'
		});
		$('.boxConter,.layui-layer-page').css('display', 'block');
		$('.layui-layer-close').click(function(event) {
			window.clearInterval(_this.settiming);
		});
		this.get_user_details();
		$('.iconCode').hide();
		$('.personalDetails').show();
	},
	// 获取二维码
	get_qrcode(){
		var _this = this;
		var qrLoading = bt.load(lan.config.config_qrcode);
		
		bt.send('blind_qrcode','panel_wxapp/blind_qrcode',{},function(res){
			qrLoading.close();
			if (res.status){
				$('#QRcode').empty();
				$('#QRcode').qrcode({
					render: "canvas", //也可以替换为table
					width: 200,
					height: 200,
					text:res.msg
				});
				_this.settiming =  setInterval(function(){
					_this.verify_binding();
				},2000);
			}else{
				bt.msg(res);
			}
		})
	},
	// 获取用户信息
	get_user_details(type){
		var _this = this;
		var conter = '';			
		bt.send('get_user_info','panel_wxapp/get_user_info',{},function(res){
			console.log('1111')
			console.log(res)
			clearInterval(_this.settiming);
			if (!res.status){
				res.time = 3000;
				bt.msg(res);
				$('.iconCode').hide();
				return false;
			}
			if (JSON.stringify(res.msg) =='{}'){
				if (type){
					bt.msg({msg:lan.config.config_qrcode_no_list,icon:2})
				}else{
					_this.get_qrcode();
				}
				$('.iconCode').show();
				$('.personalDetails').hide();
				return false;
			}
			$('.iconCode').hide();
			$('.personalDetails').show();
			var datas = res.msg;
			for(var item in datas){
				conter += '<li class="item">\
							<div class="head_img"><img src="'+datas[item].avatarUrl+'" title="用户头像" /></div>\
							<div class="nick_name"><span>昵称:</span><span class="nick"></span>'+datas[item].nickName+'</div>\
							<div class="cancelBind">\
								<a href="javascript:;" class="btlink" title="取消当前微信小程序的绑定" onclick="weixin.cancel_bind('+ item +')">取消绑定</a>\
							</div>\
						</li>'
			}
			conter += '<li class="item addweixin" style="height:45px;"><a href="javascript:;" class="btlink" onclick="weixin.add_wx_view()"><span class="glyphicon glyphicon-plus"></span>添加绑定账号</a></li>'
			$('.userList').empty().append(conter);
		})
	},
	// 添加绑定视图
	add_wx_view(){
		$('.iconCode').show();
		$('.personalDetails').hide();
		this.get_qrcode();
	},
	// 取消当前绑定
	cancel_bind(uid){
		var _this = this;
		var bdinding = layer.confirm('您确定要取消当前绑定吗？',{
			btn:['确认','取消'],
			icon:3,
			title:'取消绑定'
		},function(){
			bt.send("blind_del","panel_wxapp/blind_del",{uid:uid},function(res){
				bt.msg(res);
				_this.get_user_details();
			})
		},function(){
			layer.close(bdinding);
		});
	},
	// 监听是否绑定
	verify_binding(){
		var _this = this;
		bt.send('blind_result','panel_wxapp/blind_result',{},function(res){
			if(res){
				bt.msg(res);
				clearInterval(_this.settiming);
				_this.get_user_details();
			}
		})
	},
	open_wxapp(){
		var rhtml = '<div class="boxConter" style="display: none">\
						<div class="iconCode" >\
							<div class="box-conter">\
								<div id="QRcode"></div>\
								<div class="codeTip">\
									<ul>\
										<li>1、打开宝塔面板小程序<span class="btlink weixin">小程序二维码<div class="weixinSamll"><img src="https://app.bt.cn/static/app.png"></div></span></li>\
										<li>2、使用宝塔小程序扫描当前二维码，绑定该面板</li>\
									</ul>\
									<span><a href="javascript:;" title="返回面板绑定列表" class="btlink" style="margin: 0 auto" onclick="bt.weixin.get_user_details(true)">查看绑定列表</a></span>\
								</div>\
							</div>\
						</div>\
						<div class="personalDetails" style="display: none">\
							<ul class="userList"></ul>\
						</div>\
					</div>'
		
		bt.open({
			type: 1,
			title: "绑定微信",
			area: '500px',			
			shadeClose: false,
			content:rhtml
		})		
		bt.weixin.init();
	}
};

bt.ftp = {
	get_list(page,search,callback)
	{
		if(page == undefined) page = 1
		search = search == undefined ? '':search;
		search = $("#SearchValue").prop("value");
		order = bt.get_cookie('order');
		
		if(order){
			order = '&order=' + order;
		}else{
			order = '';
		}		
		if(!callback) var loadT = bt.load(lan.soft.get_list);		
		bt.send('getFtp','panel_data/getData','tojs=get_list&table=ftps&limit=15&p='+page+'&search='+search + order,function(rdata){
			if(!callback) loadT.close();
			if(callback) callback(rdata);
		})
	},
	add(type = 0, data = {},callback)
	{
		_this = this;
		if (type == 1) 
		{
			var loadT = bt.load(lan.public.the_get);
			bt.send('AddUser','ftp/AddUser',data,function(rdata){
				loadT.close();
				if(rdata.status) layer.closeAll();
				if(callback) callback(rdata);
				bt.msg(rdata);
			})
			return true;
		}
		
		var index = bt.open({
			type: 1,
			skin: 'demo-class',
			area:['520px','310px'],
			title: lan.ftp.add_title,
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content: "<form class='layui-form layui-form-alert add-ftp'>\
								<div class='layui-form-item'>\
									<label class='layui-form-label'>"+lan.ftp.add_user +"</label>\
									<div class='layui-input-block'>\
										<input type='text' name='ftp_username'   placeholder='"+lan.ftp.add_user_tips+"' autocomplete='off' class='layui-input'>\
									</div>\
								</div>\
								<div class='layui-form-item'>\
									<label class='layui-form-label'>"+lan.ftp.add_pass +"</label>\
									<div class='layui-input-block'>\
										<input type='text' name='ftp_password' value='"+ bt.get_random(16) +"'  placeholder='"+lan.ftp.add_pass_tips+"' autocomplete='off' class='layui-input MyPassword' >\
										<div class='layui-form-mid layui-word-aux'><i class='fa fa-refresh' aria-hidden='true' title='"+ lan.ftp.add_pass_rep +"' lay-event='repeat_pwd' onclick='bt.refresh_pwd(16)'></i></div>\
									</div>\
								</div>\
								<div class='layui-form-item'>\
									<label class='layui-form-label'>"+lan.ftp.add_path +"</label>\
									<div class='layui-input-block'>\
										<input type='text' name='path' value='"+ bt.config.sites_path +"'   placeholder='"+lan.ftp.add_path_tips+"' autocomplete='off' class='layui-input'>\
										<div class='layui-form-mid layui-word-aux'><i class='fa fa-folder-open' aria-hidden='true' title='"+ lan.ftp.add_path_rep +"' lay-event='change_path'></i></div>\
									</div>\
								</div>\
								<div class='bt-form-submit-btn'>\
									<button type='button' class='layui-btn layui-btn-sm' lay-event='submit_edit_port' >"+lan.public.submit+"</button>\
									<button type='button' class='layui-btn layui-btn-sm  layui-btn-primary' onclick='layer.closeAll()'>"+lan.public.close+"</button>\
								</div>\
							</form>"
		})
		setTimeout(function(){

			$("[name='ftp_username']").keyup(function(){
				var ftpName = $(this).val();
				len = bt.config.sites_path.trim().length;
				if($('[name="path"]').val().substr(0,len) == bt.config.sites_path.trim()){
					$('[name="path"]').val(bt.config.sites_path+'/'+ftpName);
				}	
			});

			// 选择文件目录
			$('[lay-event="change_path"]').click(function () {
				bt.msg({status:false,msg:'选择文件目录'})
			});
			// 提交
			$('[lay-event="submit_edit_port"]').click(function(){
				bt.ftp.add(1,$('.add-ftp').serialize(),callback);
			});

		},100);
		
	},
	edit(id, username, passwd,callback){
		var _this = this;	
		var  index = bt.open({
			type: 1,
			skin: 'demo-class',
			area: ['420px','240px'],
			title: lan.ftp.pass_title,
			shift: 5,
			shadeClose: false,
			content: "<div class='layui-form layui-form-alert'>\
								<div class='layui-form-item'>\
									<label class='layui-form-label'>"+lan.ftp.add_user +"</label>\
									<div class='layui-input-block'>\
										<input type='text' name='add_user' readonly='readonly' value='"+username  +"' autocomplete='off'  class='layui-input layui-input-readonly'>\
									</div>\
								</div>\
								<div class='layui-form-item'>\
									<label class='layui-form-label'>"+lan.ftp.pass_new +"</label>\
									<div class='layui-input-block'>\
										<input type='text' name='add_paw'  value='"+ passwd +"' placeholder='"+lan.ftp. add_pass_tips+"' autocomplete='off' class='layui-input MyPassword'>\
										<div class='layui-form-mid layui-word-aux'><i class='fa fa-refresh' aria-hidden='true' title='随机密码' lay-event='repeat_pwd' onclick='bt.refresh_pwd(16)'></i></div>\
									</div>\
								</div>\
								<div class='bt-form-submit-btn'>\
									<button type='button' class='layui-btn layui-btn-sm' lay-event='submit_edit_port' >"+lan.public.ok+"</button>\
									<button type='button' class='layui-btn layui-btn-sm  layui-btn-primary' onclick='layer.closeAll()'>"+lan.public.close+"</button>\
								</div>\
							</div>"
		});
		setTimeout(function(){
			// 提交
			$('[lay-event="submit_edit_port"]').click(function(){
				bt.confirm({msg:lan.ftp.pass_confirm,title: lan.ftp.stop_title,closeBtn:1},function(){
					var loadT = bt.load(lan.public.the);
					bt.send('SetUserPassword','ftp/SetUserPassword',{id:id,ftp_username:username,new_password:$('[name="add_paw"]').val()},function(rdata){
						loadT.close();
						if(rdata.status) index.close();
						if(callback) callback();
						bt.msg(rdata);
					})
				})
			});
		},100);
	},
	delete(dataList,callback)
	{
		var _this = this;
		var title = dataList.length == 1?lan.ftp.del_ftp_title:lan.ftp.del_ftp_all_title;
		var msg = dataList.length == 1?lan.get('del_ftp',[dataList[0].name]):lan.get('del_all_ftp',[dataList.length])
		bt.show_confirm(title,msg,function(){
			function delete_ftp(dataList,count = 0){
				if(dataList.length < 1) {		
					callback();
					layer.msg(lan.get('del_all_ftp_ok',[count]),{icon:1});			
					return;
				}
				loading = bt.load(lan.get('del_all_task_the',[dataList[0].name]));
				bt.send('DeleteUser','ftp/DeleteUser',{id:dataList[0].id,username:dataList[0].name},function(rdata){
					loading.close();
					if(rdata.status){
						count++;
					}
					dataList.splice(0,1);
					delete_ftp(dataList,count);
				});
			}
			delete_ftp(dataList);
		});

	// 	del(dataList,successCount = 0 ,errorMsg = '')
	// {
	// 	var _this = this;
	// 	if(dataList.length < 1) {			
	// 		layer.msg(lan.get('del_all_ftp_ok',[successCount]),{icon:1});			
	// 		return;
	// 	}
	// 	show_confirm(lan.public.del+"["+ftp_username+"]",lan.get('confirm_del',[ftp_username]),function(){
	// 		loading = bt.load(lan.get('del_all_task_del',[dataList[0].name]));
	// 		var data='id='+id+'&username='+ftp_username;
	// 		bt.send('DeleteUser','ftp/DeleteUser','id='+dataList[0].id+'&username='+dataList[0].name,function(rdata){
	// 			loading.close();
	// 			if(rdata.status){
	// 				successCount++;
	// 				$("input[title='"+dataList[0].name+"']").parents("tr").remove();
	// 			}
	// 			else{
	// 				if(!errorMsg){
	// 					errorMsg = '<br><p>'+lan.ftp.del_all_err+'</p>';
	// 				}
	// 				errorMsg += '<li>'+dataList[0].name+' -> '+frdata.msg+'</li>'
	// 			}
	// 			dataList.splice(0,1);
	// 			_this.del(dataList,successCount,errorMsg);
	// 		})
	// 	});
	// }
	},
	set_status(id, username,status,callback){
		var _this = this;
		var loadT = bt.load(lan.public.the);
		var data='id=' + id + '&username=' + username + '&status='+status;
		bt.confirm({title:'FTP账户',msg:!status?'您真的要停止'+ username +'的FTP吗?':'是否启动'+ username +'的FTP账号？',closeBtn:'1'},function () {
			bt.send('SetStatus','ftp/SetStatus',data,function(rdata){
				loadT.close();
				if (rdata.status) callback(rdata);
				bt.msg(rdata);
			});
		});
	},
	stop(id,username){
		var _this = this;
		bt.confirm({msg:lan.ftp.stop_confirm.replace('{1}',username),title:lan.ftp.stop_title},function(index){			
			if (index > 0) {
				_this.set_status(id,username,0);
			}
			else {
				layer.closeAll();
			}
		})
	},
	start(id, username){
		this.set_status(id,username,1);
	},
	set_port(port)
	{	
		var form_port  = bt.open({
			type: 1,
			skin: 'demo-class',
			area: ['400px','200px'],
			title: lan.ftp.port_title,
			closeBtn: 2,
			shadeClose: false,
			content: "<div class='layui-form layui-form-alert'>\
								<div class='layui-form-item'>\
									<label class='layui-form-label'>"+lan.ftp.port_name +"</label>\
									<div class='layui-input-block'>\
										<input type='text' name='port'  value='"+ port +"' placeholder='"+lan.ftp. port_tips+"' autocomplete='off' class='layui-input'>\
									</div>\
								</div>\
								<div class='bt-form-submit-btn'>\
									<button type='button' class='layui-btn layui-btn-sm' lay-event='submit_edit_port' >"+lan.public.submit+"</button>\
									<button type='button' class='layui-btn layui-btn-sm  layui-btn-primary' onclick='layer.closeAll()'>"+lan.public.close+"</button>\
								</div>\
				      		</div>"
		});
		setTimeout(function(){
			$('[lay-event="submit_edit_port"]').click(function (e) {
				edit_port($('[name="port"]').val());
			});
			$('[name="port"]').keyup(function (e) {
				if(e.keyCode == 13 ){
					edit_port($(this).val());
				}
			});
			function edit_port(port) {
				if(port == ''){
					bt.msg({msg:'端口地址不能为空',status:false});
					load.close();
					return false;
				}
				var load = bt.load(lan.public.the)
				bt.send('setPort','ftp/setPort',{port:port},function(rdata){
					load.close();
					bt.msg(rdata);
					if(rdata.status){
						form_port.close();
						setTimeout(function(){
							window.location.reload()	
						},3000)
					}
				})
			} 
		},100);
	}	
},

bt.files = {
	get_files(Path,searchV,callback){
		var searchtype = Path;
		if(isNaN(Path)){
			var p = '1';
		}else{
			var p = Path;
			Path = bt.get_cookie('Path');
		}		
		var search = '';
		if(searchV.length > 1 && searchtype == "1"){
			search = "&search="+searchV;
		}
		var showRow = bt.get_cookie('showRow');
		if(!showRow) showRow = '100';
		var totalSize = 0;
		var loadT = bt.load(lan.public.the);
		bt.send('get_files','files/GetDir','tojs=GetFiles&p=' + p + '&showRow=' + showRow + search+'&path='+ Path,function(rdata){
			loadT.close();
			callback(rdata);
		})
	},	
	del_file(path,callback)
	{
		_this = this;
		bt.confirm({msg:lan.get('recycle_bin_confirm',[fileName]),title:lan.files.del_file},function(){
			loading = bt.load(lan.public.the);
			bt.send('del_file','files/DeleteFile','path='+path,function(rdata){
				loading.close();
				bt.msg(rdata);
				callback(rdata);
			})
		})
		
	},
	get_right_click(fileType,path,fileName){
		
	}
}
bt.config = 
{
	close_panel(callback)
	{
		layer.confirm(lan.config.close_panel_msg,{title:lan.config.close_panel_title,closeBtn:1,icon:13,cancel:function(){
			if(callback) callback(false);
		}}, function() {
			loading = bt.load(lan.public.the);
			bt.send('ClosePanel','config/ClosePanel',{},function(rdata){
				loading.close();
				if(callback) callback(rdata);
			})
		},function(){
			if(callback) callback(false);
		});
	},
	set_auto_update(callback)
	{
		loading = bt.load(lan.public.the);
		bt.send('AutoUpdatePanel','config/AutoUpdatePanel',{},function(rdata){
			loading.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		})
	},
	sync_data(callback)
	{
		var loadT = bt.load(lan.config.config_sync);
		bt.send('syncDate','config/syncDate',{},function(rdata){
			loadT.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		});
	},
	save_config(data,callback)
	{
		loading = bt.load(lan.config.config_save);
		bt.send('setPanel','config/setPanel',data,function(rdata){
			loading.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		});
	},
	set_template(template,callback)
	{		
		var loadT = bt.load(lan.public.the);
		bt.send('SetTemplates','config/SetTemplates',{templates:template},function(rdata){
			loadT.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		});
	},
	set_panel_ssl(status,callback)
	{
		var msg = status?lan.config.ssl_close_msg:'<a style="font-weight: bolder;font-size: 16px;">'+lan.config.ssl_open_ps+'</a><li style="margin-top: 12px;color:red;">'+lan.config.ssl_open_ps_1+'</li><li>'+lan.config.ssl_open_ps_2+'</li><li>'+lan.config.ssl_open_ps_3+'</li><p style="margin-top: 10px;"><input type="checkbox" id="checkSSL" /><label style="font-weight: 400;margin: 3px 5px 0px;" for="checkSSL">'+lan.config.ssl_open_ps_4+'</label><a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-4689-1-1.html" style="float: right;">'+lan.config.ssl_open_ps_5+'</a></p>';
		layer.confirm(msg,{title:lan.config.ssl_title,closeBtn:1,icon:3,area:'550px',cancel:function(){
			if(callback) {
				if(status == 0){
					callback(false);
				}
				else{
					callback(true);
				}
			}
		}},function(){
			if(window.location.protocol.indexOf('https') == -1){
				if(!$("#checkSSL").prop('checked')){					
					bt.msg({msg:lan.config.ssl_ps,icon:2});
					if(callback)  callback(false);
				}
			}
			var loadT = bt.load(lan.config.ssl_msg);
			bt.send('SetPanelSSL','config/SetPanelSSL',{},function(rdata){
				loadT.close();
				bt.msg(rdata);
				if(callback)  callback(rdata);
			})			
		},function(){
			if(callback) {
				if(status == 0){
					callback(false);
				}
				else{
					callback(true);
				}
			}
		});
	},
	get_panel_ssl()
	{
		_this = this;
		loading = bt.load('正在获取证书信息...');
		bt.send('GetPanelSSL','config/GetPanelSSL',{},function(cert){
			loading.close();
			var certBody = '<div class="tab-con">\
				<div class="myKeyCon ptb15">\
					<div class="ssl-con-key pull-left mr20">密钥(KEY)<br>\
						<textarea id="key" class="bt-input-text">'+cert.privateKey+'</textarea>\
					</div>\
					<div class="ssl-con-key pull-left">证书(PEM格式)<br>\
						<textarea id="csr" class="bt-input-text">'+cert.certPem+'</textarea>\
					</div>\
					<div class="ssl-btn pull-left mtb15" style="width:100%">\
						<button class="btn btn-success btn-sm" id="btn_submit">保存</button>\
					</div>\
				</div>\
				<ul class="help-info-text c7 pull-left">\
					<li>粘贴您的*.key以及*.pem内容，然后保存即可<a href="http://www.bt.cn/bbs/thread-704-1-1.html" class="btlink" target="_blank">[帮助]</a>。</li>\
					<li>如果浏览器提示证书链不完整,请检查是否正确拼接PEM证书</li><li>PEM格式证书 = 域名证书.crt + 根证书(root_bundle).crt</li>\
				</ul>\
			</div>'
			bt.open({
				type: 1,
				area: "600px",
				title: '自定义面板证书',
				closeBtn: 1,
				shift: 5,
				shadeClose: false,
				content:certBody
			});
			
			$("#btn_submit").click(function(){
				key = $('#key').val();
				csr = $('#csr').val();
				_this.set_panel_ssl({privateKey:key,certPem:csr});
			})
		})
	},
	set_panel_ssl(data,callback)
	{		
		var loadT = bt.load(lan.config.ssl_msg);
		bt.send('SavePanelSSL','config/SavePanelSSL',data,function(rdata){
			loadT.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		})
	},
	get_bind_user(callback){
		var btusername = bt.get_cookie('btusername');
		if(btusername){
			callback(btusername);
			return;
		}
		var loadT = bt.load(lan.public.the_get);
		bt.send('GetUserInfo','ssl/GetUserInfo',{},function(rdata){
			loadT.close();
			if(!rdata.status){
				bt.msg(rdata.status);
				return
			}
			if(callback) callback(rdata);
			bt.set_cookie('btusername',JSON.stringify(rdata));
		})
	}
}

// 任务管理器
bt.crontab = {
	// 执行计划任务
	start_crontab_send(id,callback){
		var that = this,loading = bt.load();
		bt.send('start_crontab_send','crontab/StartTask',{id,id},function (rdata) {
			loading.close();
			rdata.time = 2000;
			bt.msg(rdata);
			if(callback) callback(rdata);
		});
	},
	
	// 删除计划任务
	del_crontab_send(id,name,callback){
		bt.show_confirm('删除['+ name +']','您确定要删除该任务吗?',function(){
			var loading = bt.load();
			bt.send('del_crontab_send','crontab/DelCrontab',{id,id},function (rdata) {
				loading.close();
				rdata.time = 2000;
				bt.msg(rdata);
				if(callback) callback(rdata);
			});
		});
	},
	
	// 设置计划任务状态
	set_crontab_status(id,status,callback){
		var that = this,loading = bt.load();
		bt.confirm({title:'提示',msg:status?'计划任务暂停后将无法继续运行，您真的要停用这个计划任务吗？':'该计划任务已停用，是否要启用这个计划任务？'},function () {
			bt.send('set_crontab_status','crontab/set_cron_status',{id,id},function (rdata) {
				loading.close();
				rdata.time = 1000;
				if(callback) callback(rdata);
			});
		});
	},

	// 编辑计划任务
	edit_crontab(id,data,callback){
		var that = this,loading = bt.load('提交数据中...');
		bt.send('edit_crontab','crontab/modify_crond',data,function(rdata){
			loading.close();
			rdata.time = 1000;
			bt.msg(rdata);
			if(callback) callback(rdata);
		});
	},
	
	// 获取计划任务日志
	get_crontab_logs(id,name,callback){
		var that = this;
		bt.send('get_logs_crontab','crontab/GetLogs',{id:id},function (rdata) {
			if(!rdata.status) {
				rdata.time = 1000;
				bt.msg(rdata);
			}else{
				bt.open({
					type:1,
					title:'查看日志-['+name+']',
					area: ['700px','520px'], 
					shadeClose:false,
					closeBtn:1,
					content:'<div class="setchmod bt-form pd20 pb70">'
							+'<pre class="crontab-log" style="overflow: auto; border: 0px none; line-height:23px;padding: 15px; margin: 0px; height: 405px; background-color: rgb(51,51,51);color:#f1f1f1;font-family: \"微软雅黑\"">'+ (rdata.msg == '' ? '当前日志为空':rdata.msg) +'</pre>'
							+'<div class="bt-form-submit-btn" style="margin-top: 0px;">'
							+'<button type="button" class="layui-btn layui-btn-sm mr10" onclick="bt.crontab.del_crontab_logs('+id+')">'+lan.public.empty+'</button>'
							+'<button type="button" class="layui-btn layui-btn-sm layui-btn-primary" onclick="layer.closeAll()">'+lan.public.close+'</button>'
							+'</div>'
							+'</div>'
				})
				setTimeout(function () {
					var div = document.getElementsByClassName('crontab-log')[0]
					div.scrollTop  = div.scrollHeight;
				},200);
				if(callback) callback(rdata);
			}
		})
	},
	
	// 删除计划任务日志
	del_crontab_logs(id,callback){
		var that = this,loading = bt.load();
		bt.send('del_crontab_logs','crontab/DelLogs',{id:id},function (rdata) {
			loading.close();
			layer.closeAll();
			rdata.time = 2000;
			bt.msg(rdata);
			if(callback) callback(rdata);
		});
	},

	// 获取计划任务列表
	get_crontab_list(status,callback){
		var that = this;
		loading = bt.load();
		bt.send('get_crontab_list','crontab/GetCrontab',{},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		});
	},
	
	// 添加计划任务请求
	add_crontab_send(data,callback){
		var that = this,loading = bt.load('提交数据中...');
		bt.send('add_crontab_send','crontab/AddCrontab',data,function(rdata){
			loading.close();
			bt.msg(rdata);
			console.log(callback)
			if(callback) callback(rdata);
		});
	},
	
	// 获取站点和备份位置信息
	get_data_list(type,callback){
		var that = this,loading= bt.load();
		bt.send('get_data_list','crontab/GetDataList',{type:type},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		});	
	},

	get_crontab_find(id,callback){
		bt.send('get_crond_find','crontab/get_crond_find',{id:id},function(rdata){
			if(callback) callback(rdata);
		})
	}
	
}

// 系统监控
bt.control = {
	// 获取系统监控状态
	get_status:function(callback){
		var loading = bt.load(lan.public.read);
		bt.send('GetControl','config/SetControl',{type:-1},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		},1);
	},

	// 设置系统监控状态
	set_control:function(type,day,callback){
		loadT = bt.load(lan.public.the);
		console.log(type,day)
		bt.send('SetControl','config/SetControl',{type:type,day:day},function(rdata){
			loadT.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		},1);
	},

	clear_control:function(callback){
		bt.confirm({msg:lan.control.close_log_msg,title:lan.control.close_log},function(){
			loadT = bt.load(lan.public.the);
			bt.send('SetControl','config/SetControl',{type:'del'},function(rdata){
				loadT.close();
				bt.msg(rdata);
				if(callback) callback(rdata);
			},1);
		})
	},

	get_data:function(type,start,end,callback){
		action = '';
		switch(type)
		{
			case 'cpu': //cpu和内存一起获取
				action='GetCpuIo';
				break;
			case 'disk':
				action='GetDiskIo';
				break;
			case 'net':
				action='GetNetWorkIo';
				break;
			case 'load':
				action='get_load_average';
				break;
		}
		if(!action) bt.msg(lan.get('lack_param','type'));
		bt.send(action,'ajax/'+action,{start:start,end:end},function(rdata){
			if(callback) callback(rdata,type);
		})
	},

	format_option:function(obj,type){
		option = {
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'cross'
				},
				formatter: obj.formatter
			},
			xAxis: {
				type: 'category',
				boundaryGap: false,
				data: obj.tData,
				axisLine:{
					lineStyle:{
						color:"#666"
					}
				}
			},
			yAxis: {
				type: 'value',
				name: obj.unit,
				boundaryGap: [0, '100%'],
				min:0,
				max: 100,
				splitLine:{
					lineStyle:{
						color:"#ddd"
					}
				},
				axisLine:{
					lineStyle:{
						color:"#666"
					}
				}
			},
			dataZoom: [{
				type: 'inside',
				start: 0,
				end: 100,
				zoomLock:true
			}, {
				start: 0,
				end: 100,
				handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
				handleSize: '80%',
				handleStyle: {
					color: '#fff',
					shadowBlur: 3,
					shadowColor: 'rgba(0, 0, 0, 0.6)',
					shadowOffsetX: 2,
					shadowOffsetY: 2
				}
			}],
			series: []
		};
		
		if(obj.legend) 
		{
			option.legend = {
				data : obj.legend
			};
		}		
		for (var i=0;i<obj.list.length;i++) 
		{
			var item = obj.list[i];
			series = {
				name : item.name,
				type : item.type?item.name:'line',
				smooth : item.smooth ? item.smooth : true,
				symbol : item.symbol ? item.symbol : 'none',
				sampling : item.sampling ? item.sampling : 'average',
				itemStyle : item.itemStyle ? item.itemStyle : { normal:{ color: 'rgb(0, 153, 238)'}},
				data :  item.data						
			}
			option.series.push(series);
		}
		return option;
	}
}


bt.send('get_config','config/get_config',{},function(rdata){
	bt.config = rdata;
})

setTimeout(function(){
	//bt.pub.OnlineEditFile(0,'/www/server/BTPanel/BTPanel/static/js/bt.js')
//	bt.send('dataList','crontab/GetDataList',null,function(rdata){
//						console.log(rdata)
//					});
	//bt.msg('你好');
},1000);



