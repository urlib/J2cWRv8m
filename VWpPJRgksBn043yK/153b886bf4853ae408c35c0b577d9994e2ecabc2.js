var bt = {
	/**
	 * 获取随机字符串
	 * @param {len} 长度
	 */
	RandomStrPwd:function(len) {
		len = len || 32;
		var c = "AaBbCcDdEeFfGHhiJjKkLMmNnPpRSrTsWtXwYxZyz2345678";
		var a = c.length;
		var d = "";
		for(i = 0; i < len; i++) {
			d += c.charAt(Math.floor(Math.random() * a))
		}
		return d
	}
	
	/**
	 * 刷新页面
	 */
	ReFresh:function () {
		window.location.reload()
	}
	
	GetBakPost:function (b) {
		$(".baktext").hide().prev().show();
		var c = $(".baktext").attr("data-id");
		var a = $(".baktext").val();
		if(a == "") {
			a = "空"
		}
		self.setWebPs(b, c, a);
		$("a[data-id='" + c + "']").html(a);
		$(".baktext").remove()
	}

	SetWebPs:function (b, e, a) {
		var d = layer.load({
			shade: true,
			shadeClose: false
		});
		var c = "ps=" + a;
		$.post("/data?action=setPs", "table=" + b + "&id=" + e + "&" + c, function(f) {
			if(f == true) {
				if(b == "sites") {
					site.getWeb(1)
				} else {
					if(b == "ftps") {
						ftp.getFtp(1)
					} else {
						database.getData(1)
					}
				}
				layer.closeAll();
				layer.msg("修改成功", {
					icon: 1
				})
			} else {
				layer.msg("失败，没有权限", {
					icon: 2
				});
				layer.closeAll()
			}
		})
}
	
	
}
