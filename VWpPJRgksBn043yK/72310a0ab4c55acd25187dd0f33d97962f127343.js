

var site = {
    get_list: function (page, search, type) {
        if (page == undefined) page = 1;
        if (type == '-1' || type == undefined) {
            type = $('.site_type select').val();
        }
        bt.site.get_list(page, search, type, function (rdata) {
            $('.dataTables_paginate').html(rdata.page);
            bt.plugin.get_firewall_state(function (fdata) {
                var data = rdata.data;
                for (var x = 0; x < data.length; x++) {
                    data[x]['firewall'] = false;
                    data[x]['waf_setup'] = false;
                    if (fdata.status !== false) {
                        data[x]['waf_setup'] = true;
                        for (var i = 0; i < fdata.length; i++) {
                            if (data[x].name == fdata[i].siteName) data[x]['firewall'] = fdata[i].open;
                        }
                    }
                }
                var _tab = bt.render({
                    table: '#webBody',
                    columns: [
                        { field: 'id', type: 'checkbox', width: 30 },
                        {
                            field: 'name', title: '网站名', width: 150, templet: function (item) {
                                return '<a class="btlink webtips" onclick="site.web_edit(this)" href="javascript:;">' + item.name + '</a>';
                            }, sort: function () { site.get_list(); }
                        },

                        {
                            field: 'status', title: '状态', width: 98, templet: function (item) {
                                var _status = '<a href="javascript:;" ';
                                if (item.status == '1' || item.status == '正常' || item.status == '正在运行') {
                                    _status += ' onclick="bt.site.stop(' + item.id + ',\'' + item.name + '\') " >';
                                    _status += '<span style="color:#5CB85C">运行中 </span><span style="color:#5CB85C" class="glyphicon glyphicon-play"></span>';
                                }
                                else {
                                    _status += ' onclick="bt.site.start(' + item.id + ',\'' + item.name + '\')"';
                                    _status += '<span style="color:red">已停止  </span><span style="color:red" class="glyphicon glyphicon-pause"></span>';
                                }
                                return _status;
                            }, sort: function () { site.get_list(); }
                        },
                        {
                            field: 'backup', title: '备份', width: 58, templet: function (item) {
                                var backup = lan.site.backup_no;
                                if (item.backup_count > 0) backup = lan.site.backup_yes;
                                return '<a href="javascript:;" class="btlink" onclick="site.site_detail(' + item.id + ',\'' + item.name + '\')">' + backup + '</a>';
                            }
                        },
                        {
                            field: 'path', title: '根目录', width: '26%', templet: function (item) {
                                var _path = bt.format_path(item.path);
                                return '<a class="btlink" title="打开目录" href="javascript:openPath(\'' + _path + '\');">' + _path + '</a>';
                            }
                        },
                        {
                            field: 'edate', title: '到期时间', width: 86, templet: function (item) {
                                var _endtime = '';
                                if (item.edate) _endtime = item.edate;
                                if (item.endtime) _endtime = item.endtime;
                                _endtime = (_endtime == "0000-00-00") ? lan.site.web_end_time : _endtime
                                return '<a class="btlink setTimes" id="site_endtime_' + item.id + '" >' + _endtime + '</a>';
                            }, sort: function () { site.get_list(); }
                        },
                        {
                            field: 'ps', title: '备注', templet: function (item) {
                                return "<span class='c9 input-edit'  onclick=\"bt.pub.set_data_by_key('sites','ps',this)\">" + item.ps + "</span>";
                            }
                        },
                        bt.os == 'Linux' ? {
                            field: 'id', title: '防火墙', templet: function (item) {
                                var _check = ' onclick="site.no_firewall(this)"';
                                if (item.waf_setup) _check = ' onclick="set_site_obj_state(\'' + item.name + '\',\'open\')"';
                                var _waf = '<input class="btswitch btswitch-ios " ' + _check + ' id="closewaf_' + item.name + '" ' + (item.firewall ? 'checked' : '') + ' type="checkbox">';
                                _waf += '<label class="btswitch-btn bt-waf-firewall" for="closewaf_' + item.name + '" title="' + bt.get_cookie('serverType') + '防火墙开关"></label>';
                                return _waf;
                            }
                        } : '',
                        {
                            field: 'opt', width: 260, title: '操作', align: 'right', templet: function (item) {
                                var opt = '';
                                var _check = ' onclick="site.no_firewall()"';
                                if (item.waf_setup) _check = ' onclick="site_waf_config(\'' + item.name + '\')"';

                                if (bt.os == 'Linux') opt += '<a href="javascript:;" ' + _check + ' class="btlink ">防火墙</a> | ';
                                opt += '<a href="javascript:;" class="btlink" onclick="site.web_edit(this)">设置 </a> | ';
                                opt += '<a href="javascript:;" class="btlink" onclick="site.del_site(' + item.id + ',\'' + item.name + '\')" title="删除站点">删除</a>';
                                return opt;
                            }
                        },
                    ],
                    data: data
                })

                //设置到期时间
                $('a.setTimes').each(function () {
                    var _this = $(this);
                    var _tr = _this.parents('tr');
                    var id = _this.attr('id');
                    laydate.render({
                        elem: '#' + id //指定元素
                        , min: bt.get_date(1)
                        , max: '2099-12-31'
                        , vlue: bt.get_date(365)
                        , type: 'date'
                        , format: 'yyyy-MM-dd'
                        , trigger: 'click'
                        , btns: ['perpetual', 'confirm']
                        , theme: '#20a53a'
                        , done: function (dates) {
                            var item = _tr.data('item');
                            bt.site.set_endtime(item.id, dates, function () { })
                        }
                    });
                })
            })
        });

    },
    get_types: function (callback) {
        bt.site.get_type(function (rdata) {
            var optionList = '';
            for (var i = 0; i < rdata.length; i++) {
                optionList += '<option value="' + rdata[i].id + '">' + rdata[i].name + '</option>'
            }
            if ($('.dataTables_paginate').next().hasClass('site_type')) $('.site_type').remove();
            $('.dataTables_paginate').after('<div class="site_type"><span>站点分类:</span><select class="bt-input-text mr5"  style="width:100px"><option value="-1">全部分类</option>' + optionList + '</select></div>');
            $('.site_type select').change(function () {
                var val = $(this).val();
                site.get_list(0, '', val);
                bt.set_cookie('site_type', val);
            })
            if (callback) callback(rdata);
        });
    },
    no_firewall: function (obj) {
        var typename = bt.get_cookie('serverType');
        layer.confirm(typename + '防火墙暂未开通，<br>请到&quot;<a href="/soft" class="btlink">软件管理>付费插件>' + typename + '防火墙</a>&quot;<br>开通安装使用。', {
            title: typename + '防火墙未开通', icon: 7, closeBtn: 2,
            cancel: function () {
                if (obj) $(obj).prop('checked', false)
            }
        }, function () {
            window.location.href = '/soft';
        }, function () {
            if (obj) $(obj).prop('checked', false)
        })
    },
    site_detail: function (id, siteName, page) {
        if (page == undefined) page = '1';
        var loadT = bt.load(lan.public.the_get);
        bt.pub.get_data('table=backup&search=' + id + '&limit=5&type=0&tojs=site.site_detail&p=' + page, function (frdata) {
            loadT.close();
            var ftpdown = '';
            var body = '';
            var port;
            frdata.page = frdata.page.replace(/'/g, '"').replace(/site.site_detail\(/g, "site.site_detail(" + id + ",'" + siteName + "',");
            if ($('#SiteBackupList').length <= 0) {
                bt.open({
                    type: 1,
                    skin: 'demo-class',
                    area: '700px',
                    title: lan.site.backup_title,
                    closeBtn: 2,
                    shift: 5,
                    shadeClose: false,
                    content: "<div class='divtable pd15 style='padding-bottom: 0'><button id='btn_data_backup' class='btn btn-success btn-sm' type='button' style='margin-bottom:10px'>" + lan.database.backup + "</button><table width='100%' id='SiteBackupList' class='table table-hover'></table><div class='page sitebackup_page'></div></div>"
                });
            }
            setTimeout(function () {
                $('.sitebackup_page').html(frdata.page);
                var _tab = bt.render({
                    table: '#SiteBackupList',
                    columns: [
                        { field: 'name', title: '文件名称' },
                        {
                            field: 'size', title: '文件大小', templet: function (item) {
                                return bt.format_size(item.size);
                            }
                        },
                        { field: 'addtime', title: '备份时间' },
                        {
                            field: 'opt', title: '操作', align: 'right', templet: function (item) {
                                var _opt = '<a class="btlink" href="/download?filename=' + item.filename + '&amp;name=' + item.name + '" target="_blank">下载</a> | ';
                                _opt += '<a class="btlink" herf="javascrpit:;" onclick="bt.site.del_backup(\'' + item.id + '\',\'' + id + '\',\'' + siteName + '\')">删除</a>'
                                return _opt;
                            }
                        },
                    ],
                    data: frdata.data
                });
                $('#btn_data_backup').unbind('click').click(function () {
                    bt.site.backup_data(id, function (rdata) {
                        if (rdata.status) site.site_detail(id, siteName);
                    })
                })
            }, 100)
        });
    },
    add_site: function () {
        bt.site.add_site(function (rdata) {
            if (rdata.siteStatus) {
                site.get_list();
                var html = '';
                var ftpData = '';
                if (rdata.ftpStatus) {
                    var list = [];
                    list.push({ title: lan.site.user, val: rdata.ftpUser });
                    list.push({ title: lan.site.password, val: rdata.ftpPass });
                    var item = {};
                    item.title = lan.site.ftp;
                    item.list = list;
                    ftpData = bt.render_ps(item);
                }
                var sqlData = '';
                if (rdata.databaseStatus) {
                    var list = [];
                    list.push({ title: lan.site.database_name, val: rdata.databaseUser });
                    list.push({ title: lan.site.user, val: rdata.databaseUser });
                    list.push({ title: lan.site.password, val: rdata.databasePass });
                    var item = {};
                    item.title = lan.site.database_txt;
                    item.list = list;
                    sqlData = bt.render_ps(item);
                }
                if (ftpData == '' && sqlData == '') {
                    bt.msg({ msg: lan.site.success_txt, icon: 1 })
                }
                else {
                    bt.open({
                        type: 1,
                        area: '600px',
                        title: lan.site.success_txt,
                        closeBtn: 2,
                        shadeClose: false,
                        content: "<div class='success-msg'><div class='pic'><img src='/static/img/success-pic.png'></div><div class='suc-con'>" + ftpData + sqlData + "</div></div>",
                    });

                    if ($(".success-msg").height() < 150) {
                        $(".success-msg").find("img").css({ "width": "150px", "margin-top": "30px" });
                    }
                }
            }
            else {
                bt.msg(rdata);
            }
        })
    },
    set_default_page: function () {
        bt.open({
            type: 1,
            area: '460px',
            title: lan.site.change_defalut_page,
            closeBtn: 2,
            shift: 0,
            content: '<div class="change-default pd20"><button  class="btn btn-default btn-sm ">' + lan.site.default_doc + '</button><button  class="btn btn-default btn-sm">' + lan.site.err_404 + '</button>	<button  class="btn btn-default btn-sm ">' + lan.site.empty_page + '</button><button  class="btn btn-default btn-sm ">' + lan.site.default_page_stop + '</button></div>'
        });
        setTimeout(function () {
            $('.change-default button').click(function () {
                bt.site.get_default_path($(this).index(), function (path) {
                    bt.pub.on_edit_file(0, path);
                })
            })
        }, 100)
    },
    set_default_site: function () {
        bt.site.get_default_site(function (rdata) {
            var arrs = [{ title: lan.site.default_site_no, value: 'off' }];
            for (var i = 0; i < rdata.sites.length; i++) arrs.push({ title: rdata.sites[i].name, value: rdata.sites[i].name })
            var form = {
                title: lan.site.default_site_yes,
                area: '530px',
                list: [{ title: lan.site.default_site, name: 'defaultSite', width: '300px', value: rdata.defaultSite, type: 'select', items: arrs }],
                btns: [
                    bt.form.btn.close(),
                    bt.form.btn.submit('提交', function (rdata, load) {
                        bt.site.set_default_site(rdata.defaultSite, function (rdata) {
                            load.close();
                            bt.msg(rdata);
                        })
                    })
                ]
            }
            bt.render_form(form);
            $('.line').after($(bt.render_help([lan.site.default_site_help_1, lan.site.default_site_help_2])).addClass('plr20'));
        })
    },
    del_site: function (wid, wname) {
        var thtml = "<div class='options'><label><input type='checkbox' id='delftp' name='ftp'><span>FTP</span></label><label><input type='checkbox' id='deldata' name='data'><span>" + lan.site.database + "</span></label><label><input type='checkbox' id='delpath' name='path'><span>" + lan.site.root_dir + "</span></label></div>";
        bt.show_confirm(lan.site.site_del_title + "[" + wname + "]", lan.site.site_del_info, function () {
            var ftp = '', data = '', path = '';
            var data = { id: wid, webname: wname }
            if ($("#delftp").is(":checked")) data.ftp = 1;
            if ($("#deldata").is(":checked")) data.database = 1;
            if ($("#delpath").is(":checked")) data.path = 1;

            bt.site.del_site(data, function (rdata) {
                if (rdata.status) site.get_list();
                bt.msg(rdata);
            })

        }, thtml);
    },
    batch_site: function (type, obj, result) {
        if (obj == undefined) {
            obj = {};
            var arr = [];
            result = { count: 0, error_list: [] };
            $('input[type="checkbox"].check:checked').each(function () {
                var _val = $(this).val();
                if (!isNaN(_val)) arr.push($(this).parents('tr').data('item'));
            })
            if (type == 'site_type') {
                bt.site.get_type(function (tdata) {
                    var types = [];
                    for (var i = 0; i < tdata.length; i++) types.push({ title: tdata[i].name, value: tdata[i].id })
                    var form = {
                        title: '设置站点分类',
                        area: '530px',
                        list: [{ title: lan.site.default_site, name: 'type_id', width: '300px', type: 'select', items: types }],
                        btns: [
                            bt.form.btn.close(),
                            bt.form.btn.submit('提交', function (rdata, load) {
                                var ids = []
                                for (var x = 0; x < arr.length; x++) ids.push(arr[x].id);
                                bt.site.set_site_type({ id: rdata.type_id, site_array: JSON.stringify(ids) }, function (rrdata) {
                                    if (rrdata.status) {
                                        load.close();
                                        site.get_list();
                                    }
                                    bt.msg(rrdata);
                                })
                            })
                        ]
                    }
                    bt.render_form(form);
                })
                return;
            }
            var thtml = "<div class='options'><label style=\"width:100%;\"><input type='checkbox' id='delpath' name='path'><span>" + lan.site.all_del_info + "</span></label></div>";
            bt.show_confirm(lan.site.all_del_site, "<a style='color:red;'>" + lan.get('del_all_site', [arr.length]) + "</a>", function () {
                if ($("#delpath").is(":checked")) obj.path = '1';
                obj.data = arr;
                bt.closeAll();
                site.batch_site(type, obj, result);
            }, thtml);

            return;
        }
        var item = obj.data[0];
        switch (type) {
            case 'del':
                if (obj.data.length < 1) {
                    site.get_list();
                    bt.msg({ msg: lan.get('del_all_site_ok', [result.count]), icon: 1, time: 5000 });
                    return;
                }
                var data = { id: item.id, webname: item.name, path: obj.path }
                bt.site.del_site(data, function (rdata) {
                    if (rdata.status) {
                        result.count += 1;
                    } else {
                        result.error_list.push({ name: item.item, err_msg: rdata.msg });
                    }
                    obj.data.splice(0, 1)
                    site.batch_site(type, obj, result);
                })
                break;

        }
    },
    set_class_type: function () {
        var _form_data = bt.render_form_line({
            title: '',
            items: [
                { placeholder: '请填写分类名称', name: 'type_name', width: '50%', type: 'text' },
                {
                    name: 'btn_submit', text: '添加', type: 'button', callback: function (sdata) {
                        bt.site.add_type(sdata.type_name, function (ldata) {
                            if (ldata.status) {
                                $('[name="type_name"]').val('');
                                site.get_class_type();
                            }
                            bt.msg(ldata);
                        })
                    }
                }
            ]
        });
        bt.open({
            type: 1,
            area: '350px',
            title: '网站分类管理',
            closeBtn: 2,
            shift: 5,
            shadeClose: true,
            content: "<div class='bt-form edit_site_type'><div class='divtable mtb15' style='overflow:auto'>" + _form_data.html + "<table id='type_table' class='table table-hover' width='100%'></table></div></div>",
            success: function () {
                bt.render_clicks(_form_data.clicks);
                site.get_class_type(function (res) {
                    $('#type_table').on('click', '.del_type', function () {
                        var _this = $(this);
                        var item = _this.parents('tr').data('item');
                        if (item.id == 0) {
                            bt.msg({ icon: 2, msg: '默认分类不可删除/不可编辑!' });
                            return;
                        }
                        bt.confirm({ msg: "是否确定删除分类？", title: '删除分类【' + item.name + '】' }, function () {
                            bt.site.del_type(item.id, function (ret) {
                                if (ret.status) {
                                    site.get_class_type();
                                    bt.set_cookie('site_type', '-1');
                                }
                                bt.msg(ret);
                            })
                        })
                    });
                    $('#type_table').on('click', '.edit_type', function () {
                        var item = $(this).parents('tr').data('item');
                        if (item.id == 0) {
                            bt.msg({ icon: 2, msg: '默认分类不可删除/不可编辑!' });
                            return;
                        }
                        bt.render_form({
                            title: '修改分类管理【' + item.name + '】',
                            area: '350px',
                            list: [{ title: '分类名称', width: '150px', name: 'name', value: item.name }],
                            btns: [
                                { title: '关闭', name: 'close' },
                                {
                                    title: '提交',
                                    name: 'submit',
                                    css: 'btn-success',
                                    callback: function (rdata, load, callback) {
                                        bt.site.edit_type({ id: item.id, name: rdata.name }, function (edata) {
                                            if (edata.status) {
                                                load.close();
                                                site.get_class_type();
                                            }
                                            bt.msg(edata);
                                        })
                                    }
                                }
                            ]
                        });
                    });
                });
            }
        });
    },
    get_class_type: function (callback) {
        site.get_types(function (rdata) {
            bt.render({
                table: '#type_table',
                columns: [
                    { field: 'name', title: '名称' },
                    { field: 'opt', width: '80px', title: '操作', templet: function (item) { return '<a class="btlink edit_type" href="javascript:;">编辑</a> | <a class="btlink del_type" href="javascript:;">删除</a>'; } }
                ],
                data: rdata
            });
            $('.layui-layer-page').css({ 'margin-top': '-' + ($('.layui-layer-page').height() / 2) + 'px', 'top': '50%' });
            if (callback) callback(rdata);
        });
    },
    pool: {
        reload: function (index) {
            if (index == undefined) index = 0
            var _sel = $('#pool_tabs .on');
            if (_sel.length == 0) _sel = $('#pool_tabs span:eq(0)');
            _sel.trigger('click');
        }
    },
    ssl: {
        my_ssl_msg: null,
        my_select_domain_ssl_index: null,
        renew_ssl: function (siteName) {
            data = {}
            if (siteName != undefined) data = { siteName: siteName }            
            var loadT = bt.load("正在一键续订证书.")
            bt.send("renew_lets_ssl", 'ssl/renew_lets_ssl', data , function (rdata) {
                loadT.close();
                if (rdata.status) {
                    if (siteName != undefined) {
                        if (rdata.err_list.length > 0) {
                            bt.msg({ status: false, msg: rdata.err_list[0].msg })
                        }
                        else {
                            site.reload();
                            bt.msg({ status: true, time: 6, msg: '网站【' + siteName + '】续订证书成功.' })
                        }
                    }
                    else {  
                        var ehtml = '', shtml = ''

                        if (rdata.sucess_list.length > 0) {
                            var sucess = {};
                            sucess.title = "成功续签 " + rdata.sucess_list.length + " 张证书";
                            sucess.list = [{ title: "域名列表", val: rdata.sucess_list.join() }];
                            shtml = bt.render_ps(sucess);
                        }

                        if (rdata.err_list.length > 0) {
                            var error = {};
                            error.title = "续签失败 " + rdata.err_list.length + " 张证书";
                            error.list = []
                            for (var i = 0; i < rdata.err_list.length; i++) {
                                error.list.push({ title: rdata.err_list[i]['siteName'], val: rdata.err_list[i]['msg'] })
                            }  
                            ehtml = bt.render_ps(error);
                        }

                        bt.open({
                            type: 1,
                            area: '600px',
                            title: "续签证书成功",
                            closeBtn: 2,
                            shadeClose: false,
                            content: "<div class='success-msg'><div class='pic'><img src='/static/img/success-pic.png'></div><div class='suc-con'>" + shtml + ehtml + "</div></div>",
                        });

                        if ($(".success-msg").height() < 150) {
                            $(".success-msg").find("img").css({ "width": "150px", "margin-top": "30px" });
                        }
                    }
                }
                else {
                    bt.msg(rdata)
                }
            })          
        },
        onekey_ssl: function (partnerOrderId, siteName) {
            bt.site.get_ssl_info(partnerOrderId, siteName, function (rdata) {
                rdata.time = 0;
                bt.msg(rdata);
                if (rdata.status) site.reload(7);
            })
        },
        set_ssl_status: function (action, siteName) {
            bt.site.set_ssl_status(action, siteName, function (rdata) {
                bt.msg(rdata);
                if (rdata.status) {
                    site.reload(7);
                    if (action == 'CloseSSLConf') {
                        layer.msg(lan.site.ssl_close_info, { icon: 1, time: 5000 });
                    }
                }
            })
        },
        verify_domain: function (partnerOrderId, siteName) {
            bt.site.verify_domain(partnerOrderId, siteName, function (vdata) {
                bt.msg(vdata);
                if (vdata.status) {
                    if (vdata.data.stateCode == 'COMPLETED') {
                        site.ssl.onekey_ssl(partnerOrderId, siteName)
                    }
                    else {
                        layer.msg('验证中,请等待CA机构验证,如第一次申请失败，请等待3小时或进入宝塔后台通过DNS方式验证.', { icon: 1, time: 0 });          
                    }
                }
            })
        },
        reload: function (index) {
            if (index == undefined) index = 0
            var _sel = $('#ssl_tabs .on');
            if (_sel.length == 0) _sel = $('#ssl_tabs span:eq(0)');
            _sel.trigger('click');
        }
    },
    edit: {
        set_domains: function (web) {
            var _this = this;
            var loadT = bt.load();
            bt.site.get_domains(web.id, function (rdata) {
                loadT.close();
                var list = [
                    {
                        items: [
                            { name: 'newdomain', width: '340px', type: 'textarea', placeholder: '每行填写一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88' },
                            {
                                name: 'btn_submit_domain', text: '添加', type: 'button', callback: function (sdata) {

                                    if (sdata.newdomain.indexOf("*") >= 0 && bt.get_cookie("serverType") == 'iis') {
                                        bt.msg({ msg: 'IIS不支持泛解析，如需使用，请通过设置默认站点实现。', icon: 2, time: 0 });
                                        return;
                                    }
                                    var arrs = sdata.newdomain.split("\n");
                                    var domins = "";
                                    for (var i = 0; i < arrs.length; i++) domins += arrs[i] + ",";
                                    bt.site.add_domains(web.id, web.name, bt.rtrim(domins, ','), function (ret) {
                                        if (ret.status) site.reload(0)
                                    })
                                }
                            }
                        ]
                    }
                ]
                var _form_data = bt.render_form_line(list[0]);
                $('#webedit-con').html(_form_data.html + "<div class='divtable mtb15' style='height:350px;overflow:auto'><table id='domain_table' class='table table-hover' width='100%'></table></div>");
                bt.render_clicks(_form_data.clicks);
                $('.placeholder').css({ 'left': '15px', 'top': '15px' });
                $('.btn_submit_domain').addClass('pull-right').css("margin", "30px 35px 0 0")
                $(".placeholder").click(function () {
                    $(this).hide();
                    $('.newdomain').focus();
                })
                $('.domains').focus(function () { $(".placeholder").hide(); });
                $('.domains').blur(function () {
                    if ($(this).val().length == 0) $(".placeholder").show();
                });
                bt.render({
                    table: '#domain_table',
                    columns: [
                        { field: 'name', title: '域名', templet: function (item) { return "<a title='" + lan.site.click_access + "' target='_blank' href='http://" + item.name + ":" + item.port + "' class='btlinkbed'>" + item.name + "</a>" } },
                        { field: 'port', width: '70px', title: '端口' },
                        { field: 'opt', width: '50px', title: '操作', templet: function (item) { return '<a class="table-btn-del domain_del" href="javascript:;"><span class="glyphicon glyphicon-trash"></span></a>'; } }
                    ],
                    data: rdata
                })
                setTimeout(function () {
                    $('.domain_del').click(function () {
                        if ($(this).parents('tbody').find('tr').length == 1) {
                            bt.msg({ msg: lan.site.domain_last_cannot, icon: 2 });
                            return;
                        }
                        var item = $(this).parents('tr').data('item');
                        bt.confirm({ msg: lan.site.domain_del_confirm }, function () {
                            bt.site.del_domain(web.id, web.name, item.name, item.port, function (ret) {
                                if (ret.status) site.reload(0)
                            })
                        })
                    })
                }, 100)
            })
        },
        set_dirbind: function (web) {
            var _this = this;
            bt.site.get_dirbind(web.id, function (rdata) {
                var dirs = [];
                for (var n = 0; n < rdata.dirs.length; n++) dirs.push({ title: rdata.dirs[n], value: rdata.dirs[n] });
                var data = {
                    title: '', items: [
                        { title: '域名', width: '140px', name: 'domain' },
                        { title: '子目录', name: 'dirName', type: 'select', items: dirs },
                        {
                            text: '添加', type: 'button', name: 'btn_add_subdir', callback: function (sdata) {
                                if (!sdata.domain || !sdata.dirName) {
                                    layer.msg(lan.site.d_s_empty, { icon: 2 });
                                    return;
                                }
                                if (sdata.domain.indexOf("*") >= 0 && bt.get_cookie("serverType") == 'iis') {
                                    bt.msg({ msg: 'IIS不支持泛解析，如需使用，请通过设置默认站点实现。', icon: 2, time: 0 });
                                    return;
                                }
                                bt.site.add_dirbind(web.id, sdata.domain, sdata.dirName, function (ret) {
                                    if (ret.status) site.reload(1)
                                    bt.msg(ret);
                                })
                            }
                        }
                    ]
                }
                var _form_data = bt.render_form_line(data);
                $('#webedit-con').html(_form_data.html + '<div class="divtable mtb15" style="height:450px;overflow:auto"><table id="sub_dir_table" class="table table-hover" width="100%" style="margin-bottom:0"></table></div>');
                bt.render_clicks(_form_data.clicks);
                bt.render({
                    table: '#sub_dir_table',
                    columns: [
                        { field: 'domain', title: '域名' },
                        { field: 'port', width: '70px', title: '端口' },
                        { field: 'path', width: '100px', title: '子目录' },
                        {
                            field: 'opt', width: '100px', align: 'right', title: '操作', templet: function (item) {
                                return '<a class="btlink rewrite" href="javascript:;">伪静态</a> | <a class="btlink del" href="javascript:;">删除</a>';
                            }
                        }
                    ],
                    data: rdata.binding
                })
                setTimeout(function () {
                    $('#sub_dir_table td a').click(function () {
                        var item = $(this).parents('tr').data('item');
                        if ($(this).hasClass('del')) {
                            bt.confirm({ msg: lan.site.s_bin_del }, function () {
                                bt.site.del_dirbind(item.id, function (ret) {
                                    if (ret.status) site.reload(1)
                                })
                            })
                        } else {
                            bt.site.get_dir_rewrite({ id: item.id }, function (ret) {
                                if (!ret.status) {
                                    var confirmObj = layer.confirm(lan.site.url_rewrite_alter, { icon: 3, closeBtn: 2 }, function () {
                                        bt.site.get_dir_rewrite({ id: item.id, add: 1 }, function (ret) {
                                            layer.close(confirmObj);
                                            show_dir_rewrite(ret);
                                        });
                                    });
                                    return;
                                }
                                show_dir_rewrite(ret);

                                function show_dir_rewrite(ret) {
                                    var arrs = [];
                                    for (var i = 0; i < ret.rlist.length; i++) arrs.push({ title: ret.rlist[i], value: ret.rlist[i] });
                                    var datas = [{
                                        name: 'dir_rewrite', type: 'select', width: '130px', items: arrs, callback: function (obj) {
                                            var spath = setup_path + '/panel/rewrite/' + bt.get_cookie('serverType') + '/' + obj.val() + '.conf';
                                            bt.files.get_file_body(spath, function (sdata) {
                                                $('.dir_config').text(sdata.data);
                                            })
                                        }
                                    },
                                    { items: [{ name: 'dir_config', type: 'textarea', value: ret.data, width: '470px', height: '260px' }] },
                                    {
                                        items: [{
                                            name: 'btn_save', text: '保存', type: 'button', callback: function (ldata) {
                                                if (bt.os == "Linux") {
                                                    bt.files.set_file_body(ret.filename, ldata.dir_config, 'utf-8', function (sdata) {
                                                        if (sdata.status) load_form.close();
                                                        bt.msg(sdata);
                                                    })
                                                }
                                                else {
                                                    var loading = bt.load();
                                                    bt.site.set_site_rewrite(item.domain + '_' + item.path, ldata.dir_config, function (sdata) {
                                                        loading.close();
                                                        if (sdata.status) load_form.close();
                                                        bt.msg(sdata);
                                                    })
                                                }
                                            }
                                        }]
                                    }]
                                    var load_form = bt.open({
                                        type: 1,
                                        area: '510px',
                                        title: lan.site.config_url,
                                        closeBtn: 2,
                                        shift: 5,
                                        skin: 'bt-w-con',
                                        shadeClose: true,
                                        content: "<div class='bt-form webedit-dir-box dir-rewrite-man-con'></div>"
                                    });

                                    setTimeout(function () {
                                        var _html = $(".webedit-dir-box")
                                        var clicks = [];
                                        for (var i = 0; i < datas.length; i++) {
                                            var _form_data = bt.render_form_line(datas[i]);
                                            _html.append(_form_data.html);
                                            var _other = (bt.os == 'Linux' && i == 0) ? '<span>规则转换工具：<a href="https://www.bt.cn/Tools" target="_blank" style="color:#20a53a">Apache转Nginx</a></span>' : '';
                                            _html.find('.info-r').append(_other)
                                            clicks = clicks.concat(_form_data.clicks);
                                        }
                                        _html.append(bt.render_help(['请选择您的应用，若设置伪静态后，网站无法正常访问，请尝试设置回default', '您可以对伪静态规则进行修改，修改完后保存即可。']));
                                        bt.render_clicks(clicks);
                                    }, 100)
                                }
                            })
                        }
                    })
                }, 100)
            })
        },
        set_dirpath: function (web) {
            var loading = bt.load();
            bt.site.get_site_path(web.id, function (path) {             
                bt.site.get_dir_userini(web.id, path, function (rdata) {
                    loading.close();
                    if (rdata.status == false) {
                        bt.msg(rdata)
                        return;
                    }
                    var dirs = [];
                    for (var n = 0; n < rdata.runPath.dirs.length; n++) dirs.push({ title: rdata.runPath.dirs[n], value: rdata.runPath.dirs[n] });
                    var datas = [
                        {
                            title: '', items: [
                                {
                                    name: 'userini', type: 'checkbox', text: '防跨站攻击(open_basedir)', value: rdata.userini, callback: function (sdata) {
                                        bt.site.set_dir_userini(path, function (ret) {
                                            if (ret.status) site.reload(2)
                                        })
                                    }
                                },
                                {
                                    name: 'logs', type: 'checkbox', text: '写访问日志', value: rdata.logs, callback: function (sdata) {
                                        bt.site.set_logs_status(web.id, function (ret) {
                                            if (ret.status) site.reload(2)
                                        })
                                    }
                                }
                            ]
                        },
                        {
                            name: 'config_lock', type: 'checkbox', text: '锁定配置文件(仅IIS有效)', value: rdata.locking, callback: function (sdata) {
                                bt.site.set_config_locking(web.name, function (ret) {
                                    if (ret.status) site.reload()
                                    bt.msg(ret)
                                })
                            }
                        },
                        {
                            title: '', items: [
                                { name: 'path', title: '网站目录', width: '50%', value: path, event: { css: 'glyphicon-folder-open', callback: function (obj) { bt.select_path(obj); } } },
                                {
                                    name: 'btn_site_path', type: 'button', text: '保存', callback: function (pdata) {
                                        bt.site.set_site_path(web.id, pdata.path, function (ret) {
                                            if (ret.status == false) {
                                                bt.msg(ret);
                                                return;
                                            }
                                            if (ret.status) site.reload()
                                        })
                                    }
                                }
                            ]
                        },
                        {
                            title: '', items: [
                                { title: '运行目录', width: '50%', value: rdata.runPath.runPath, name: 'dirName', type: 'select', items: dirs },
                                {
                                    name: 'btn_run_path', type: 'button', text: '保存', callback: function (pdata) {
                                        bt.site.set_site_runpath(web.id, pdata.dirName, function (ret) {
                                            if (ret.status) site.reload()
                                        })
                                    }
                                }
                            ]
                        }
                    ]
                    var _html = $("<div class='webedit-box soft-man-con'></div>")
                    var clicks = [];
                    for (var i = 0; i < datas.length; i++) {
                        var _form_data = bt.render_form_line(datas[i]);
                        _html.append($(_form_data.html).addClass('line mtb10'));
                        clicks = clicks.concat(_form_data.clicks);
                    }
                    _html.find('input[type="checkbox"]').parent().addClass('label-input-group ptb10');
                    _html.find('button[name="btn_run_path"]').addClass('ml45');
                    _html.find('button[name="btn_site_path"]').addClass('ml33');
                    _html.append(bt.render_help(['部分程序需要指定二级目录作为运行目录，如ThinkPHP5，Laravel', '选择您的运行目录，点保存即可','wordpress安装/修改模块导致网站500错误 <a style="color:#20a53a;" href="https://www.bt.cn/bbs/thread-33097-1-1.html" target="_blank">参考此贴</a>','锁定配置将保护您的站点配置文件不被替换/修改等操作 <font style="color:red">(PS:可通过面板修改配置并校验格式正确性)</font>']));
                    if (bt.os == 'Linux') _html.append('<div class="user_pw_tit" style="margin-top: 2px;padding-top: 11px;"><span class="tit">密码访问</span><span class="btswitch-p"><input class="btswitch btswitch-ios" id="pathSafe" type="checkbox"><label class="btswitch-btn phpmyadmin-btn" for="pathSafe" ></label></span></div><div class="user_pw" style="margin-top: 10px; display: block;"></div>')

                    $('#webedit-con').append(_html);
                    bt.render_clicks(clicks);
                    $('#pathSafe').click(function () {
                        var val = $(this).prop('checked');
                        var _div = $('.user_pw')
                        if (val) {
                            var dpwds = [
                                { title: '授权账号', width: '200px', name: 'username_get', placeholder: '不修改请留空' },
                                { title: '访问密码', width: '200px', type: 'password', name: 'password_get_1', placeholder: '不修改请留空' },
                                { title: '重复密码', width: '200px', type: 'password', name: 'password_get_2', placeholder: '不修改请留空' },
                                {
                                    name: 'btn_password_get', text: '保存', type: 'button', callback: function (rpwd) {
                                        if (rpwd.password_get_1 != rpwd.password_get_2) {
                                            layer.msg(lan.bt.pass_err_re, { icon: 2 });
                                            return;
                                        }
                                        bt.site.set_site_pwd(web.id, rpwd.username_get, rpwd.password_get_1, function (ret) {
                                            if (ret.status) site.reload(2)
                                        })
                                    }
                                }
                            ]
                            for (var i = 0; i < dpwds.length; i++) {
                                var _from_pwd = bt.render_form_line(dpwds[i]);
                                _div.append("<div class='line'>" + _from_pwd.html + "</div>");
                                bt.render_clicks(_from_pwd.clicks);
                            }
                        } else {
                            bt.site.close_site_pwd(web.id, function (rdata) {
                                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
                                _div.html('');
                            })
                        }
                    })
                    if (rdata.pass) $('#pathSafe').trigger('click');
                })
            })
        },
        set_apppool: function (web, index) {
            if (index == undefined) index = 0;
            var loadT = bt.load();
            bt.site.get_net_version_byaspp(web.name, function (ndata) {
                loadT.close();
                if (ndata.status === false) {
                    bt.msg(ndata);
                    return;
                }     
           
                bt.site.get_iis_net_versions(function (ldata) {
                    if (ldata.status === false) {
                        bt.msg(ldata);
                        return;
                    }

                    $('#webedit-con').html("<div id='pool_tabs'></div><div class=\"tab-con\" style=\"padding:20px 0px;\"></div>");

                    var _tabs = [
                        {
                            title: '基础设置', callback: function (robj) {
                                var nets = [];
                                for (var i = 0; i < ldata.length; i++)  nets.push({ title: ldata[i], value: ldata[i] })

                                var shtml = '<p  style="margin-left:30px;" class="status">当前状态：<span>开启</span><span style="color: #20a53a; margin-left: 3px;" class="glyphicon glyphicon glyphicon-play"></span>'
                                var opttxt = '停止'
                                if (ndata.status != 'Started') {
                                    shtml = '<p class="status">当前状态：<span>关闭</span><span style="color: red; margin-left: 3px;" class="glyphicon glyphicon-pause"></span>'
                                    opttxt = '启动'
                                }
                                shtml += '<span class="app_status" style="margin-left:20px;"><button class="btn btn-default btn-sm">' + opttxt + '</button> <button class="btn btn-default btn-sm">重启</button></span></p>'

                                var _html = $('<div class="webedit-box soft-man-con"> ' + shtml + ' </div>')
                                
                                var datas = [
                                    { title: '托管管道模式', name: 'model', type: 'select', value: ndata.type, items: [{ title: '集成', value: 'Integrated' }, { title: '经典', value: 'Classic' }] },
                                    { title: '.NET 版本', name: 'net_version', type: 'select', value: ndata.version, items: nets },
                                    { title: '32位应用程序', name: 'enable32BitAppOnWin64', type: 'select', value: ndata.enable32BitAppOnWin64, ps: 'x64系统下仍加载x86应用程序池，默认开启', items: [{ title: '启用', value: 'true' }, { title: '停用', value: 'false' }] },
                                    { title: '队列长度', name: 'queueLength', width: "130px", type: 'number', value: ndata.queueLength, ps: '默认1000，超过此长度将响应503' },
                                    {
                                        title: '  ', name: 'btn_set_app', text: '保存', type: 'button', callback: function (ldata) {
                                            ldata['name'] = web.name;
                                            bt.site.set_iis_apppool(ldata, function (ret) {
                                                if (ret.status) site.edit.set_apppool(web,0)
                                            })
                                        }
                                    }
                                ]
                                robj.append(_html);
                                for (var i = 0; i < datas.length; i++) {
                                    bt.render_form_line(datas[i], '', robj);                                    
                                }
                                robj.append(bt.render_help(['IIS性能调整与异常排除<a href="https://www.bt.cn/bbs/thread-33111-1-1.html" target="_blank" class="btlink"> 使用帮助</a>']))

                                $(".app_status button").click(function () {
                                    var _index = $(this).index();
                                    var opt = "start";
                                    if (ndata.status == 'Started') opt = "stop";
                                    if (_index == 1) opt = "restart";
                                    var msg = lan.bt[opt];
                                    bt.confirm({ msg: "是否确定" + msg + "程序池[" + web.name + "]？", title: '提示' }, function () {
                                        bt.site.set_apppool_status(web.name, opt, function (ret) {
                                            if (ret.status) {
                                                site.get_class_type();
                                                site.edit.set_apppool(web, 0)
                                            }  
                                            bt.msg(ret);
                                        })
                                    })
                                })               
                            }
                        },
                        {
                            title: '回收设置', callback: function (robj) {
                                var periodicRestart = ndata.periodicRestart;
                                var re_data = [
                                    { title: '内存限制', name: 'privateMemory', width: "120px", type: 'number', value: periodicRestart.privateMemory, unit: 'KB' },
                                    { title: '请求限制', name: 'requests', width: "120px", type: 'number', value: periodicRestart.requests },
                                    { title: '固定回收时间', name: 'time', width: "180px", type: 'number', value: periodicRestart.time, unit: '秒' },
                                    {
                                        title: ' ', items: [
                                           {
                                                title: '  ', name: 'btn_site_app_recycling', text: '应用本站', type: 'button', callback: function (ldata) {
                                                    ldata['is_global'] = 0;
                                                    site.edit.set_site_app_recycling(web,ldata)
                                                }
                                            },
                                            {
                                                title: '  ', name: 'btn_all_app_recycling', text: '应用所有', type: 'button', callback: function (ldata) {
                                                    ldata['is_global'] = 0;                                          
                                                    site.edit.set_site_app_recycling(web,ldata)
                                                }
                                            },
                                        ]
                                    }
                                ]
                                for (var i = 0; i < re_data.length; i++) {
                                    bt.render_form_line(re_data[i], '', robj)
                                }
                                $(".btn_all_app_recycling").removeClass('btn-success').addClass('btn-danger');

                                robj.append('<div style="border-bottom:#ccc 1px solid;margin-bottom:10px;padding-bottom:10px;margin-top: 20px;"> <input id="recycling_time" class="bt-input-text recycling_time" style="width:280px"  type="text" value=""  placeholder="每天定时回收程序池,格式：12:00"><button class="btn btn_add_recycling btn-success btn-sm va0 mlr15" >添加</button></div><div class="divtable" style="max-height:150px;overflow:auto;border:#ddd 1px solid"><table id="pool_recycling_list" class="table table-hover" style="border:none;"></table></div>');

                                var schedule_list = []
                                for (var i = 0; i < periodicRestart.schedule.length; i++)  schedule_list.push({ time_start: periodicRestart.schedule[i]})
                                
                                bt.render({
                                    table: '#pool_recycling_list',
                                    columns: [
                                        { field: 'time_start',title: '时间（24小时制）' },
                                        {
                                            field: 'opt', width: '70px', title: '操作', templet: function (item) {
                                                return '<a class="btlink pool_recycling_del">删除</a>'
                                            }
                                        }
                                    ],
                                    data: schedule_list
                                });

                                robj.append(bt.render_help(['内存限制：超过内存限制自动回收，0表示不限制', '请求限制：超过请求限制自动回收,0表示不限制', '固定回收时间：固定回收，默认1740分钟', '定时回收：表示每天固定时间回收程序池，建议设置在半夜。','IIS性能调整与异常排除<a href="https://www.bt.cn/bbs/thread-33111-1-1.html" target="_blank" class="btlink"> 使用帮助</a>']))

          
                                $(".pool_recycling_del").click(function () {
                                    var item = $(this).parents('tr').data('item')
                                    site.edit.set_site_recycling_bytime(web, item.time_start, "0");
                                })

                                $(".btn_add_recycling").click(function () {                                    
                                    site.edit.set_site_recycling_bytime(web, $(".recycling_time").val() + ':00', "1");
                                })

                                //时间选择器
                                laydate.render({
                                    elem: '#recycling_time',
                                    type: 'time',
                                    trigger: 'click',
                                    format:'HH:MM'
                                });       
                            }
                        },                       
                        {
                            title: '故障防护', callback: function (robj) {
                                var failure = ndata.failure;
                                var failure_data = [
                                    { title: '状态', name: 'rapidFailProtection', width: "120px", type: 'select', value: failure.rapidFailProtection, items: [{ title: '开启', value: 'true' }, { title: '关闭', value: 'false' }] },
                                    { title: '故障间隔', name: 'rapidFailProtectionInterval', width: "120px", type: 'number', value: failure.rapidFailProtectionInterval, unit: '分钟' },
                                    { title: '最大故障次数', name: 'rapidFailProtectionMaxCrashes', width: "120px", type: 'number', value: failure.rapidFailProtectionMaxCrashes, unit: '次' },
                                    { title: '故障处理方式', name: 'failure_type', width: "150px", type: 'select', value: failure.failure_type, items: [{ title: '不处理', value: 'false' }, { title: '重启当前程序池', value: 'start_pool' }, { title: '重启IIS', value: 'restart_iis' }] },
                                    {
                                        title: ' ', items: [
                                            {
                                                title: '  ', name: 'btn_site_app_failure', text: '应用本站', type: 'button', callback: function (ldata) {
                                                    ldata['is_global'] = 0;

                                                    site.edit.set_site_app_failure(web, ldata)
                                                }
                                            },
                                            {
                                                title: '  ', name: 'btn_all_app_failure', text: '应用所有', type: 'button', callback: function (ldata) {
                                                    ldata['is_global'] = 1;
                                                    site.edit.set_site_app_failure(web, ldata)
                                                }
                                            },
                                        ]
                                    }
                                ]
                                for (var i = 0; i < failure_data.length; i++) {
                                    bt.render_form_line(failure_data[i], '', robj)
                                }
                                $(".btn_all_app_failure").removeClass('btn-success').addClass('btn-danger');

                                robj.append(bt.render_help(['【故障间隔】内发送了【最大故障次数】错误则停止程序池，整站响应503错误', '故障处理方式：当应用程序池被异常关闭后触发的处理方式.','IIS性能调整与异常排除<a href="https://www.bt.cn/bbs/thread-33111-1-1.html" target="_blank" class="btlink"> 使用帮助</a>']))
                            }
                        },
                        {
                            title: '工作进程', callback: function (robj) {
                                var process = ndata.processModel;
                                var re_data = [
                                    { title: '最大工作进程', name: 'maxProcesses', width: "180px", type: 'number', value: process.maxProcesses },
                                    { title: '启动超时', name: 'startupTimeLimit', width: "180px", type: 'number', value: process.startupTimeLimit, unit: ' 秒' },
                                    { title: '请求超时', name: 'shutdownTimeLimit', width: "180px", type: 'number', value: process.shutdownTimeLimit, unit: ' 秒' },
                                    { title: '闲置超时', name: 'idleTimeout', width: "180px", type: 'number', value: process.idleTimeout, unit: ' 秒' },                                 
                                    {
                                        title: ' ', items: [
                                            {
                                                title: '  ', name: 'btn_site_app_process', text: '保存', type: 'button', callback: function (ldata) {
                                                    site.edit.set_site_app_process(web, ldata)
                                                }
                                            }
                                        ]
                                    }
                                ]

                                for (var i = 0; i < re_data.length; i++) {
                                    bt.render_form_line(re_data[i], '', robj)
                                }
                                robj.append(bt.render_help(['启动超时：启动程序池超时时间', '请求超时：完成处理请求超时时间', '闲置超时：超过此时间未收到请求，此进程将进入闲置状态', '最大工作进程：应用池启动进程数,增加进程数可有效缓解进程池压力(<span style="color:red">注意：每增加一个进程将会增加200M内存占用，并且可能会造成用户登录状态丢失，谨慎使用。</span>)', 'IIS性能调整与异常排除<a href="https://www.bt.cn/bbs/thread-33111-1-1.html" target="_blank" class="btlink"> 使用帮助</a>']))
                            }
                        },
                        {
                            title: '活动进程', callback: function (robj) {

                                var loading = bt.load();
                                bt.send('get_iis_process_list', 'site/get_iis_process_list', { siteName: web.name }, function (rdata) {
                                    loading.close();

                                    if (rdata.status === false) {
                                        bt.msg(rdata);
                                        return;
                                    }
                                    var _total_html = ' <table class="table table-hover table-bordered" style="width: 490px;margin-bottom:10px;background-color:#fafafa">\
					                        <tbody> <tr><th style="width:80px">总连接数：</th><td>' + rdata.total_request + '</td><th style="width:80px">总内存：</th><td>' + rdata.total_memory + ' KB</td><th style="width:80px">总CPU：</th><td>' + rdata.total_cpu + ' %</td></tr></tbody>\
					                    </table>'
                                    var con = "<div class='divtable style='padding-bottom: 0'><table width='100%' id='tab_iis_status' class='table table-hover'></table></div>";
                                    robj.html(_total_html + con);

                                    var _tab = bt.render({
                                        table: '#tab_iis_status',
                                        columns: [
                                            { field: 'name', title: '网站名', width: "100px" },
                                            { field: 'pid', title: '进程ID', width: "100px" },
                                            { field: 'cpu', title: 'CPU', width: "100px" },
                                            { field: 'memory', title: '内存(KB)', width: "100px" },
                                            { field: 'request', title: '活动连接数', width: "100px" },
                                            {
                                                field: 'opt', title: '操作', width: "100px", templet: function (item) {
                                                    return '<a class="btlink get_request_info">查看</a>'
                                                }
                                            }
                                        ],
                                        data: rdata.apps
                                    })
                                    $(".get_request_info").click(function () {
                                        var _item = $(this).parents('tr').data('item')

                                        bt.soft.web.get_iis_request_list(_item.pid, function (res) {
                                            if ($("#iis_request_list").length <= 0) {
                                                bt.open({
                                                    type: 1,
                                                    title: "[" + _item.name + "]活动进程",
                                                    area: ['500px', '500px'],
                                                    closeBtn: 2,
                                                    shadeClose: false,
                                                    content: '<div class="pd15 div_cn_form"><div style="border-bottom:#ccc 1px solid;margin-bottom:10px;padding-bottom:10px"></div><div class="divtable" style="max-height:300px;overflow:auto;border:#ddd 1px solid"><table id="iis_request_list" class="table table-hover gztr" style="border:none;"></table></div></div>',
                                                    success: function () {
                                                        init_request_data_list(res);
                                                    }
                                                })
                                            }
                                            else {
                                                init_request_data_list(res)
                                            }

                                            function init_request_data_list(res) {
                                                var _tab = bt.render({
                                                    table: '#iis_request_list',
                                                    columns: [
                                                        { field: 'method', title: '类型', width: "100px" },
                                                        { field: 'url', title: 'URL', width: "100px" },
                                                        { field: 'time', title: '耗时', width: "100px" },
                                                        { field: 'client', title: '客户端', width: "100px" },
                                                        { field: 'module', title: '处理模块', width: "100px" },

                                                    ],
                                                    data: res
                                                })
                                            }
                                        })
                                    })
                                })

                                
                            }
                        }
                    ]
                    bt.render_tab('pool_tabs', _tabs);
                    $('#pool_tabs span:eq(' + index +')').trigger('click');  
                })
            })           
        },
        set_site_app_process: function (web, ldata) {
            ldata['siteName'] = web.name
            var loading = bt.load();
            bt.send('set_site_app_process', 'site/set_site_app_process', ldata, function (rRet) {
                loading.close();
                if (rRet.status) {
                    site.edit.set_apppool(web, 3)
                }
                bt.msg(rRet);
            })
        },
        set_site_recycling_bytime: function (web, recycling_time, stype) {

            var loading = bt.load();
            bt.send('set_site_recycling_bytime', 'site/set_site_recycling_bytime', { siteName: web.name, recycling_time: recycling_time, stype: stype }, function (rRet) {
                loading.close();
                if (rRet.status) {
                    site.edit.set_apppool(web, 1)
                }
                bt.msg(rRet);
            })
        },
        set_site_app_recycling: function (web,ldata) {
            ldata['siteName'] = web.name
            var loading = bt.load();
            bt.send('set_iis_app_recycling', 'site/set_iis_app_recycling', ldata, function (rRet) {
                loading.close();
                if (rRet.status) {
                    site.edit.set_apppool(web, 1)
                }
                bt.msg(rRet);
            })
        },
        set_site_app_failure: function (web, ldata) {
            ldata['siteName'] = web.name
            var loading = bt.load();
            bt.send('set_iis_app_failure', 'site/set_iis_app_failure', ldata, function (rRet) {
                loading.close();
                if (rRet.status) {
                    site.edit.set_apppool(web, 2)
                }
                bt.msg(rRet);
            })
        },
        set_error_page: function (web) {
            bt.site.get_site_error_pages(web.name, function (rdata) {
                if (rdata.status === false) {
                    bt.msg(rdata);
                    return;
                }
                var _from_data = {                    
                    items: [
                        { title: '响应错误模式：',width:'330px', name: 'error_model', type: 'select', value: rdata.error_model, items: [{ title: '自定义错误页', value: 'Custom' }, { title: '详细错误页', value: 'Detailed' }, { title: '本地请求的详细错误页和远程请求的自定义错误页', value: 'DetailedLocalOnly' }] },
                        {
                            name: 'btn_set_error_model', text: '切换', type: 'button', callback: function (ldata) {
                                ldata['name'] = web.name;
                                bt.site.set_site_error_model(ldata, function (ret) {
                                    if (ret.status) {
                                        site.reload()
                                    }                                   
                                    bt.msg(ret);
                                })
                            }
                        }
                    ]
                }
                bt.render_form_line(_from_data, '', $("#webedit-con").empty());

                $('#webedit-con').append("<div class='divtable mtb15' style='height:380px;overflow:auto'><table id='error_page_table' class='table table-hover' width='100%'></table></div>");
                bt.render({
                    table: '#error_page_table',
                    columns: [
                        {
                            field: 'statusCode',width:'55px', title: '错误码', templet: function (item) {
                                return item.statusCode
                            }
                        },
                        {
                            field: 'responseMode', width: '60px', title: '类型', templet: function (item) {
                                switch (item.responseMode) {
                                    case 'File':
                                        return "文件";
                                    case "ExecuteURL":
                                        return "根目录";
                                        break;
                                    case "Redirect":
                                        return "重定向";
                                        break;
                                }
                            }
                        },
                        {
                            field: 'path', title: '路径', templet: function (item) {
                                
                                if (item.prefixLanguageFilePath != "") {
                                    var path = item.prefixLanguageFilePath + '\\' + item.path;
                                    return path;
                                }
                                else {
                                    return item.path;
                                }                                
                            }
                        },                       
                        {
                            field: 'opt', width: '80px', title: '操作', templet: function (item) {
                                return '<a class="btlink edit_error_page" href="javascript:;">编辑</a> | <a class="btlink re_error_page" href="javascript:;">还原</a>';
                            }
                        }
                    ],
                    data: rdata.list
                })
                $(".re_error_page").click(function () {
                    var item = $(this).parents('tr').data('item')
                    bt.confirm({ msg: "是否确定还原错误码[" + item.statusCode + "]显示页？", title: '提示' }, function () {
                        bt.site.re_error_page_bycode(web.name, item.statusCode, function (ret) {
                            if (ret.status) {
                                site.reload()
                            }
                            bt.msg(ret);
                        })
                    }) 
                })

                $(".edit_error_page").click(function () {
                    var item = $(this).parents('tr').data('item')
                    bt.render_form({
                        title: "编辑【" + item.statusCode + "】错误页",
                        area: '530px',
                        list: [
                            { title: '错误码', name: 'code', value: item.statusCode, disabled: true },
                            { title: '类型', name: 'responseMode', type: 'select', value: item.responseMode, items: [{ title: '根目录', value: 'ExecuteURL' }, { title: '重定向', value: 'Redirect' }] },
                            { title: '地址', name: 'path', value: item.path }
                        ],
                        btns: [
                            { title: '关闭', name: 'close' },
                            {
                                title: '提交', name: 'submit', css: 'btn-success', callback: function (rdata, load, callback) {
                                    if (rdata.responseMode == 'Redirect') {
                                        if (!bt.check_url(rdata.path)) {
                                            bt.msg({ icon: 2, msg: '地址格式不正确,格式为：https://www.bt.cn' });
                                            return;
                                        }
                                    }
                                    else {
                                        var reg = /^\/.+/;
                                        if (!reg.test(rdata.path)) {
                                            bt.msg({ icon: 2, msg: '地址格式不正确,格式为：/404.html' });
                                            return;
                                        }
                                    }
                                    bt.confirm({ msg: "您确定修改" + item.statusCode + "错误页吗？", title: "编辑" }, function () {
                                        var loading = bt.load();
                                        rdata['name'] = web.name;
                                        bt.send('set_error_page_bycode', 'site/set_error_page_bycode', rdata, function (rRet) {
                                            loading.close();
                                            if (rRet.status) {
                                                load.close();	
                                                site.reload()
                                            }
                                            bt.msg(rRet);
                                        })
                                    })
                                }
                            }
                        ]
                    })
                })
                $('#webedit-con').append(bt.render_help(['重定向：302重定向到指定url(如：https://www.bt.cn)', '根目录：访问到网站根目录指定文件(如：/404.html)','IIS出现500错误处理方案 <a href="https://www.bt.cn/bbs/thread-33102-1-1.html" target="_blank" class="btlink"> 使用帮助</a>']));
            })
        },
        set_dirguard: function (web) {
            String.prototype.myReplace = function (f, e) {//吧f替换成e
                var reg = new RegExp(f, "g"); //创建正则RegExp对象
                return this.replace(reg, e);
            }
            bt.site.get_dir_auth(web.id, function (res) {
                if (res.status == false) {
                    bt.msg(res)                    
                    return;
                }
                var datas = {
                    items: [{ name: 'add_dir_guard', text: '添加目录保护', type: 'button', callback: function (data) { site.edit.template_Dir(web.id, true) } }]
                }
                var form_line = bt.render_form_line(datas);
                $('#webedit-con').append(form_line.html);
                bt.render_clicks(form_line.clicks);
                $('#webedit-con').addClass('divtable').append('<table id="dir_guard" class="table table-hover"></table>');
                setTimeout(function () {
                    var data = [];
                    var _tab = bt.render({
                        table: '#dir_guard',
                        columns: [
                            {
                                field: 'name', title: '名称', template: function (item) {
                                    return '<span style="width:60px;" title="' + item.name + '">' + item.name + '</span>'
                                }
                            },
                            {
                                field: 'site_dir', title: '保护的目录', template: function (item) {
                                    return '<span style="width:60px;" title="' + item.site_dir + '">' + item.site_dir + '</span>'
                                }
                            },
                            {
                                field: 'dname', title: '操作', align: 'right', templet: function (item) {
                                    var dirName = item.name
                                    item = JSON.stringify(item).myReplace('"', '\'');
                                    var conter = '<a class="btlink" onclick="site.edit.template_Dir(\'' + web.id + '\',false,' + item + ')" href="javascript:;">编辑</a> ' +
                                        '| <a class="btlink" onclick="bt.site.delete_dir_guard(\'' + web.id + '\',\'' + dirName + '\',function(rdata){if(rdata.status)site.reload()})" href="javascript:;">删除</a>';
                                    return conter
                                }
                            }
                        ],
                        data: res
                    })

                })
            });
        },

        limit_network: function (web) {
            var loadT =  bt.load();
            bt.site.get_limitnet(web.id, function (rdata) {
                loadT.close();
                if (rdata.status === false) {
                    bt.msg(rdata);
                    return;
                }
                var limits = [
                    { title: '论坛/博客', value: 1, items: { perserver: 300, perip: 25, limit_rate: 512 } },
                    { title: '图片站', value: 2, items: { perserver: 200, perip: 10, limit_rate: 1024 } },
                    { title: '下载站', value: 3, items: { perserver: 50, perip: 3, limit_rate: 2048 } },
                    { title: '商城', value: 4, items: { perserver: 500, perip: 10, limit_rate: 2048 } },
                    { title: '门户', value: 5, items: { perserver: 400, perip: 15, limit_rate: 1024 } },
                    { title: '企业', value: 6, items: { perserver: 60, perip: 10, limit_rate: 512 } },
                    { title: '视频', value: 7, items: { perserver: 150, perip: 4, limit_rate: 1024 } }
                ]
                var datas = [
                    {
                        items: [{
                            name: 'status', type: 'checkbox', value: rdata.perserver != 0 ? true : false, text: '启用流量控制', callback: function (ldata) {
                                if (ldata.status) {
                                    bt.site.set_limitnet(web.id, ldata, function (ret) {
                                        if (ret.status) site.reload(3)
                                    })
                                } else {
                                    bt.site.close_limitnet(web.id, function (ret) {
                                        if (ret.status) site.reload(3)
                                    })
                                }
                            }
                        }]
                    },
                    {
                        items: [{
                            title: '限制方案  ', width: '160px', name: 'limit', type: 'select', items: limits, callback: function (obj) {
                                var data = limits.filter(function (p) { return p.value === parseInt(obj.val()); })[0]
                                for (var key in data.items) $('input[name="' + key + '"]').val(data.items[key]);
                            }
                        }]
                    },
                    { items: [{ title: '并发限制   ', type: 'number', width: '200px', value: rdata.perserver, name: 'perserver' }] },
                    { hide: bt.os == 'Linux' ? false : true, items: [{ title: '单IP限制   ', type: 'number', width: '200px', value: rdata.perip, name: 'perip' }] },
                    { hide: bt.os == 'Linux' ? true : false, items: [{ title: '超时时间   ', type: 'number', width: '200px', value: rdata.timeout ? rdata.timeout : 120, name: 'timeout' }] },
                    { items: [{ title: '流量限制   ', type: 'number', width: '200px', value: rdata.limit_rate, name: 'limit_rate' }] },
                    {
                        name: 'btn_limit_get', text: '保存', type: 'button', callback: function (ldata) {
                            bt.site.set_limitnet(web.id, ldata, function (ret) {
                                if (ret.status) site.reload(3)
                            })
                        }
                    }
                ]
                var _html = $("<div class='webedit-box soft-man-con'></div>")
                var clicks = [];
                for (var i = 0; i < datas.length; i++) {
                    var _form_data = bt.render_form_line(datas[i]);
                    _html.append(_form_data.html);
                    clicks = clicks.concat(_form_data.clicks);
                }
                _html.find('input[type="checkbox"]').parent().addClass('label-input-group ptb10');
                _html.append(bt.render_help(['限制当前站点最大并发数', '限制单个IP访问最大并发数', '限制每个请求的流量上限（单位：KB）']));
                $('#webedit-con').append(_html);
                bt.render_clicks(clicks);
                if (rdata.perserver == 0) $("select[name='limit']").trigger("change")
            })
        },
        get_rewrite_list: function (web) {
            var filename = '/www/server/panel/vhost/rewrite/' + web.name + '.conf';
            if (bt.get_cookie('serverType') == 'apache') filename = web.path + '/.htaccess';
            bt.site.get_rewrite_list(web.name, function (rdata) {
                var arrs = [];
                for (var i = 0; i < rdata.rewrite.length; i++) arrs.push({ title: rdata.rewrite[i], value: rdata.rewrite[i] });

                var datas = [{
                    name: 'rewrite', type: 'select', width: '130px', items: arrs, callback: function (obj) {
                        var spath = filename;
                        if (bt.os != 'Linux' && obj.val() == lan.site.rewritename) {
                            var loadT = bt.load()
                            bt.site.get_site_rewrite(web.name, function (ret) {
                                if (ret.status === false) {
                                    bt.msg(ret);
                                    return;
                                }
                                loadT.close()
                                editor.setValue(ret.data);
                            })
                        }
                        else {
                            if (obj.val() != lan.site.rewritename) spath = setup_path + '/panel/rewrite/' + bt.get_cookie('serverType') + '/' + obj.val() + '.conf';
                            bt.files.get_file_body(spath, function (ret) {
                                editor.setValue(ret.data);
                            })
                        }
                    }
                },
                { items: [{ name: 'config', type: 'textarea', value: rdata.data, widht: '340px', height: '200px' }] },
                {
                    items: [{
                        name: 'btn_save', text: '保存', type: 'button', callback: function (ldata) {
                            if (bt.os == "Linux") {
                                bt.files.set_file_body(filename, editor.getValue(), 'utf-8', function (ret) {
                                    if (ret.status) site.reload(4)
                                    bt.msg(ret);
                                })
                            }
                            else {
                                var loading = bt.load();
                                bt.site.set_site_rewrite(web.name, editor.getValue(), function (ret) {
                                    loading.close()
                                    if (ret.status) site.reload()
                                    bt.msg(ret);
                                })
                            }
                        }
                    },
                    {
                        name: 'btn_save_to', text: '另存为模板', type: 'button', callback: function (ldata) {
                            var temps = {
                                title: lan.site.save_rewrite_temp,
                                area: '330px',
                                list: [
                                    { title: '模板名称', placeholder: '模板名称', width: '160px', name: 'tempname' }
                                ],
                                btns: [
                                    { title: '关闭', name: 'close' },
                                    {
                                        title: '提交', name: 'submit', css: 'btn-success', callback: function (rdata, load, callback) {
                                            bt.site.set_rewrite_tel(rdata.tempname, editor.getValue(), function (rRet) {
                                                if (rRet.status) {
                                                    load.close();
                                                    site.reload(4)
                                                }
                                                bt.msg(rRet);
                                            })
                                        }
                                    }
                                ]
                            }
                            bt.render_form(temps);
                        }
                    }]
                }
                ]
                var _html = $("<div class='webedit-box soft-man-con'></div>")
                var clicks = [];
                for (var i = 0; i < datas.length; i++) {
                    var _form_data = bt.render_form_line(datas[i]);
                    _html.append(_form_data.html);
                    var _other = (bt.os == 'Linux' && i == 0) ? '<span>规则转换工具：<a href="https://www.bt.cn/Tools" target="_blank" style="color:#20a53a">Apache转Nginx</a></span>' : '';
                    _html.find('.info-r').append(_other)
                    clicks = clicks.concat(_form_data.clicks);
                }
                _html.append(bt.render_help(['请选择您的应用，若设置伪静态后，网站无法正常访问，请尝试设置回default', '您可以对伪静态规则进行修改，修改完后保存即可。']));
                $('#webedit-con').append(_html);
                bt.render_clicks(clicks);

                $('textarea.config').attr('id', 'config_rewrite');
                var editor = CodeMirror.fromTextArea(document.getElementById("config_rewrite"), {
                    extraKeys: { "Ctrl-Space": "autocomplete" },
                    lineNumbers: true,
                    matchBrackets: true,
                });
                $(".CodeMirror-scroll").css({ "height": "340px", "margin": 0, "padding": 0 });
                $('select.rewrite').trigger('change')

            })
        },
        set_default_index: function (web) {
            var loadT = bt.load();
            bt.site.get_index(web.id, function (rdata) {
                loadT.close();
                if (rdata.status === false) {
                    bt.msg(rdata);
                    return;
                }
                rdata = rdata.replace(new RegExp(/(,)/g), "\n");
                var data = {
                    items: [
                        { name: 'Dindex', height: '230px', width: '50%', type: 'textarea', value: rdata },
                        {
                            name: 'btn_submit', text: '保存', type: 'button', callback: function (ddata) {
                                var Dindex = ddata.Dindex.replace(new RegExp(/(\n)/g), ",");
                                bt.site.set_index(web.id, Dindex, function (ret) {
                                    if (ret.status) site.reload(5)
                                })
                            }
                        }
                    ]
                }
                var _form_data = bt.render_form_line(data);
                var _html = $(_form_data.html)
                _html.append(bt.render_help([lan.site.default_doc_help]))
                $('#webedit-con').append(_html);
                $('.btn_submit').addClass('pull-right').css("margin", "90px 100px 0 0")
                bt.render_clicks(_form_data.clicks);
            })
        },
        set_config: function (web) {
            var loadT = bt.load();
            bt.site.get_site_config(web.name, function (rdata) {
                loadT.close();
                if (rdata.status == false) {
                    bt.msg(rdata);
                    return;
                }
                var datas = [
                    { items: [{ name: 'site_config', type: 'textarea', value: rdata.data, widht: '340px', height: '200px' }] },
                    {
                        items: [
                            {
                                name: 'btn_config_submit', text: '保存', type: 'button', callback: function (ddata) {

                                    bt.confirm({ msg: "修改默认配置可能会导致网站500错误，如不了解配置文件格式请勿随意修改，是否继续修改？", title: '警告' }, function () {
                                        bt.site.set_site_config(web.name, editor.getValue(), rdata.encoding, function (ret) {
                                            if (ret.status) site.reload(6)
                                            bt.msg(ret);
                                        })
                                    })
                                }
                            },
                            {
                                name: 'btn_re_config_submit', text: '恢复默认配置', type: 'button', callback: function (ddata) {

                                    bt.confirm({ msg: "网站配置将会恢复到初始状态，是否继续修改？", title: '提示' }, function () {
                                        bt.site.set_re_site_config(web.name, function (ret) {
                                            if (ret.status) site.reload(6)
                                            bt.msg(ret);
                                        })
                                    })
                                }
                            }
                        ]
                    }
                ]
                var robj = $('#webedit-con');
                for (var i = 0; i < datas.length; i++) {
                    var _form_data = bt.render_form_line(datas[i]);
                    robj.append(_form_data.html);
                    bt.render_clicks(_form_data.clicks);
                }
                var helps = [lan.site.web_config_help]
                if (bt.get_cookie('serverType') == 'iis') {
                    helps.push('<span style="color:red">如您的部分操作不生效，请尝试将配置文件恢复到默认配置(如php版本，重定向等)</span>');
                    helps.push('IIS配置文件格式说明 <a href="https://www.bt.cn/bbs/thread-33097-1-1.html" target="_blank" class="btlink"> 使用帮助</a>')
                }
                robj.append(bt.render_help(helps));
                $('textarea.site_config').attr('id', 'configBody');
                var editor = CodeMirror.fromTextArea(document.getElementById("configBody"), {
                    extraKeys: { "Ctrl-Space": "autocomplete" },
                    lineNumbers: true,
                    matchBrackets: true,
                });
                $(".CodeMirror-scroll").css({ "height": "400px", "margin": 0, "padding": 0 });
            })
        },
        set_ssl: function (web) {
            $('#webedit-con').html("<div id='ssl_tabs'></div><div class=\"tab-con\" style=\"padding:20px 0px;\"></div>");
            bt.site.get_site_ssl(web.name, function (rdata) {
                var _tabs = [
                    {
                        title: '宝塔SSL', on: true, callback: function (robj) {
                            bt.pub.get_user_info(function (udata) {
                                if (udata.status) {
                                    bt.site.get_domains(web.id, function (ddata) {
                                        
                                        //IIS特殊处理                                       
                                        var domains = [];
                                        for (var i = 0; i < ddata.length; i++) {
                                            if (ddata[i].name.indexOf('*') == -1) domains.push({ title: ddata[i].name, value: ddata[i].name });
                                        }
                                        var arrs1 = [
                                            { title: '域名', width: '200px', name: 'domains', type: 'select', items: domains },
                                            {
                                                title: ' ', name: 'btsslApply', text: '申请', type: 'button', callback: function (sdata) {
                                                    if (sdata.domains.indexOf('www.') != -1) {
                                                        var rootDomain = sdata.domains.split(/www\./)[1];
                                                        if (!$.inArray(domains, rootDomain)) {
                                                            layer.msg('您为域名[' + sdata.domains + ']申请证书，但程序检测到您没有将其根域名[' + rootDomain + ']绑定并解析到站点，这会导致证书签发失败!', { icon: 2, time: 5000 });
                                                            return;
                                                        }
                                                    }
                                                    bt.confirm({ msg: "申请SSL请确保当前域名已经解析生效，并未开启301/反向代理/CDN等功能，否则将导致验证失败并且需要等待3小时后或者手动去官网改为DNS验证进行申请，确定继续吗？", title: '提示' }, function () {
                                                        bt.site.get_dv_ssl(sdata.domains, web.path, function (tdata) {
                                                            bt.msg(tdata);
                                                            if (tdata.status) site.ssl.verify_domain(tdata.data.partnerOrderId, web.name);
                                                        })
                                                    })
                                                }
                                            }
                                        ]
                                        for (var i = 0; i < arrs1.length; i++) {
                                            var _form_data = bt.render_form_line(arrs1[i]);
                                            robj.append(_form_data.html);
                                            bt.render_clicks(_form_data.clicks);
                                        }
                                        robj.append("<div id='ssl_order_list' class=\"divtable mtb15 table-fixed-box\" style=\"max-height:200px;overflow-y: auto;\"><table id='bt_order_list' class='table table-hover'><thead><tr><th>域名</th><th>到期时间</th><th>状态</th><th>操作</th></tr></thead><tbody><tr><td colspan='4' style='text-align:center'><img style='height: 18px;margin-right:10px' src='/static/layer/skin/default/loading-2.gif'>正在获取订单,请稍后...</td></tr></tbody></table></div>");

                                        var helps = [
                                            '申请之前，请确保域名已解析，如未解析会导致审核失败(包括根域名)',
                                            '宝塔SSL申请的是免费版TrustAsia DV SSL CA - G5证书，仅支持单个域名申请',
                                            '有效期1年，不支持续签，到期后需要重新申请',
                                            '建议使用二级域名为www的域名申请证书,此时系统会默认赠送顶级域名为可选名称',
                                            '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点',
                                            '99%的用户都可以轻易自助部署，如果您不懂，<a class="btlink" href="https://www.bt.cn/yunwei" target="_blank">宝塔提供证书部署服务50元一次</a>',
                                            '宝塔SSL申请注意事项及教程 <a href="https://www.bt.cn/bbs/thread-33113-1-1.html" target="_blank" class="btlink"> 使用帮助</a>'
                                        ]
                                        if (bt.get_cookie('serverType') == 'iis') {
                                            helps.push('<span style="color:red">IIS8.5以下版本，一台服务器只能存在一个SSL，多次部署会替换之前的SSL</span>')
                                        }
                                        robj.append(bt.render_help(helps));
                                        bt.site.get_order_list(web.name, function (odata) {

                                            if (odata.status === false) {
                                                $("#bt_order_list tr:eq(1) td").text(odata.msg)
                                                return;
                                            }
                                            $("#ssl_order_list").html("<table id='bt_order_list' class='table table-hover'></table>");
                                            bt.render({
                                                table: '#bt_order_list',
                                                columns: [
                                                    { field: 'commonName', title: '域名' },
                                                    {
                                                        field: 'endtime', width: '70px', title: '到期时间', templet: function (item) {
                                                            return bt.format_data(item.endtime, 'yyyy/MM/dd');
                                                        }
                                                    },
                                                    { field: 'stateName', width: '100px', title: '状态' },
                                                    {
                                                        field: 'opt', align: 'right', width: '100px', title: '操作', templet: function (item) {
                                                             
                                                            var opt = '<a class="btlink" onclick="site.ssl.onekey_ssl(\'' + item.partnerOrderId + '\',\'' + web.name + '\')" href="javascript:;">部署</a>'
                                                            if (item.stateCode == 'WF_DOMAIN_APPROVAL') {
                                                                opt = '<a class="btlink" onclick="site.ssl.verify_domain(\'' + item.partnerOrderId + '\',\'' + web.name + '\')" href="javascript:;">验证域名</a>';
                                                            }
                                                            else {
                                                                if (item.setup) opt = '已部署 | <a class="btlink" href="javascript:site.ssl.set_ssl_status(\'CloseSSLConf\',\'' + web.name + '\')">关闭</a>'
                                                            }
                                                            return opt;
                                                        }
                                                    }
                                                ],
                                                data: odata.data
                                            })
                                            bt.fixed_table('bt_order_list');

                                        })
                                                                             
                                    })
                                }
                                else {
                                    robj.append('<div class="alert alert-warning" style="padding:10px">未绑定宝塔账号，请注册绑定，绑定宝塔账号(非论坛账号)可实现一键部署SSL</div>');

                                    var datas = [
                                        { title: '宝塔账号', name: 'bt_username', value: rdata.email, width: '260px', placeholder: '请输入手机号码' },
                                        { title: '密码', type: 'password', name: 'bt_password', value: rdata.email, width: '260px' },
                                        {
                                            title: ' ', items: [
                                                {
                                                    text: '登录', name: 'btn_ssl_login', type: 'button', callback: function (sdata) {
                                                        bt.pub.login_btname(sdata.bt_username, sdata.bt_password, function (ret) {
                                                            if (ret.status) site.reload(7);
                                                        })
                                                    }
                                                },
                                                {
                                                    text: '注册宝塔账号', name: 'bt_register', type: 'button', callback: function (sdata) {
                                                        window.open('https://www.bt.cn/register.html')
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                    for (var i = 0; i < datas.length; i++) {
                                        var _form_data = bt.render_form_line(datas[i]);
                                        robj.append(_form_data.html);
                                        bt.render_clicks(_form_data.clicks);
                                    }
                                    robj.append(bt.render_help(['宝塔SSL证书为亚洲诚信证书，需要实名认证才能申请使用', '已有宝塔账号请登录绑定', '宝塔SSL申请的是TrustAsia DV SSL CA - G5 原价：1900元/1年，宝塔用户免费！', '一年满期后免费颁发']));
                                }
                            })

                        }
                    },
                    {
                        title: "Let's Encrypt", callback: function (robj) {
                            if (rdata.status && rdata.type == 1) {
                                var cert_info = '';
                                if (rdata.cert_data) {
                                    cert_info = '<div style="margin-bottom: 10px;" class="alert alert-success">\
                                        <p style="margin-bottom: 9px;"><span style="width: 307px;display: inline-block;"><b>已部署成功：</b>将在距离到期时间1个月内尝试自动续签</span>\
                                        <span style="margin-left: 20px;display: inline-block;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;max-width: 135px;width: 135px;">\
                                        <b>证书品牌：</b>'+ rdata.cert_data.issuer + '</span></p>\
                                        <span style="display:inline-block;max-width: 307px;overflow:hidden;text-overflow:ellipsis;vertical-align:-3px;white-space: nowrap;width: 307px;"><b>认证域名：</b> ' + rdata.cert_data.dns.join('、') + '</span>\
                                        <span style="margin-left: 20px;"><b>到期时间：</b> ' + rdata.cert_data.notAfter + '</span></div>'
                                }
                                robj.append('<div>' + cert_info + '<div><span>密钥(KEY)</span><span style="padding-left:194px">证书(PEM格式)</span></div></div>');
                                var datas = [
                                    {
                                        items: [
                                            { name: 'key', width: '45%', height: '220px', type: 'textarea', value: rdata.key },
                                            { name: 'csr', width: '45%', height: '220px', type: 'textarea', value: rdata.csr }
                                        ]
                                    },
                                    {
                                        items: [
                                            {
                                                text: '关闭SSL', name: 'btn_ssl_close', hide: rdata.status == false, type: 'button', callback: function (sdata) {
                                                    site.ssl.set_ssl_status('CloseSSLConf', web.name);
                                                }
                                            },
                                            {
                                                text: '续签当前网站', name: 'btn_ssl_renew', hide: rdata.status == false, type: 'button', callback: function (sdata) {
                                                    site.ssl.renew_ssl(web.name);
                                                }
                                            },
                                            {
                                                text: '一键续签全部', name: 'btn_ssl_renew_all', hide: rdata.status == false, type: 'button', callback: function (sdata) {
                                                    site.ssl.renew_ssl();
                                                }
                                            }
                                        ]
                                    }
                                ]
                                for (var i = 0; i < datas.length; i++) {
                                    var _form_data = bt.render_form_line(datas[i]);
                                    robj.append(_form_data.html);
                                    bt.render_clicks(_form_data.clicks);
                                }
                                robj.find('textarea').css('background-color', '#f6f6f6').attr('readonly', true);
                                var helps = [
                                    '申请之前，请确保域名已解析，如未解析会导致审核失败(包括根域名)',
                                    '宝塔SSL申请的是免费版TrustAsia DV SSL CA - G5证书，仅支持单个域名申请',
                                    '有效期1年，不支持续签，到期后需要重新申请',
                                    '建议使用二级域名为www的域名申请证书,此时系统会默认赠送顶级域名为可选名称',
                                    '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点'                                  
                                ]
                                robj.append(bt.render_help(['已为您自动生成Let\'s Encrypt免费证书；', '如需使用其他SSL,请切换其他证书后粘贴您的KEY以及PEM内容，然后保存即可。']));
                                return;
                            }
                            bt.site.get_site_domains(web.id, function (ddata) {
                                var helps = [[
                                    '申请之前，请确保域名已解析，如未解析会导致审核失败',
                                    'Let\'s Encrypt免费证书，有效期3个月，支持多域名。默认会自动续签',
                                    '若您的站点使用了CDN或301重定向会导致续签失败',
                                    '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点',
                                    'Let\'s Encrypt证书使用教程 <a href="https://www.bt.cn/bbs/thread-33097-1-1.html" target="_blank" class="btlink"> 使用帮助</a>'
                                ], [
                                    '自动组合泛域名：根据选择域名自动解析泛域名并申请泛域名SSL证书',
                                    '在DNS验证中，我们提供了3个自动化DNS-API，并提供了手动模式',
                                    '使用DNS接口申请证书可自动续期，手动模式下证书到期后手需重新申请',
                                    '使用【宝塔DNS云解析】接口前您需要确认当前要申请SSL证书的域名DNS为【云解析】',
                                    '使用【DnsPod/阿里云DNS】接口前您需要先在弹出的窗口中设置对应接口的API',
                                    'Let\'s Encrypt证书使用教程 <a href="https://www.bt.cn/bbs/thread-33097-1-1.html" target="_blank" class="btlink"> 使用帮助</a>'
                                ]]
                                var datas = [
                                    {
                                        title: '验证方式', items: [
                                            {
                                                name: 'check_file', text: '文件验证', type: 'radio', callback: function (obj) {
                                                    $('.checks_line').remove()
                                                    $(obj).siblings().removeAttr('checked');

                                                    $('.help-info-text').html($(bt.render_help(helps[0])));
                                                    var _form_data = bt.render_form_line({ title: ' ', class: 'checks_line label-input-group', items: [{ name: 'force', type: 'checkbox', value: true, text: '提前校验域名(提前发现问题,减少失败率)' }] });
                                                    $(obj).parents('.line').append(_form_data.html);

                                                    $('#ymlist li input[type="checkbox"]').each(function () {
                                                        if ($(this).val().indexOf('*') >= 0) {
                                                            $(this).parents('li').hide();
                                                        }
                                                    })
                                                }
                                            },
                                            {
                                                name: 'check_dns', text: 'DNS验证', type: 'radio', callback: function (obj) {
                                                    $('.checks_line').remove();
                                                    $(obj).siblings().removeAttr('checked');
                                                    $('.help-info-text').html($(bt.render_help(helps[1])));
                                                    $('#ymlist li').show();

                                                    var arrs_list = [], arr_obj = {};
                                                    bt.site.get_dns_api(function (api) {
                                                        for (var x = 0; x < api.length; x++) {
                                                            arrs_list.push({ title: api[x].title, value: api[x].name });
                                                            arr_obj[api[x].name] = api[x];
                                                        }
                                                        var data = [{
                                                            title: '选择DNS接口', class: 'checks_line', items: [
                                                                {
                                                                    name: 'dns_select', width: '120px', type: 'select', items: arrs_list, callback: function (obj) {
                                                                        var _val = obj.val();
                                                                        $('.set_dns_config').remove();
                                                                        var _val_obj = arr_obj[_val];
                                                                        var _form = {
                                                                            title: '',
                                                                            area: '530px',
                                                                            list: [],
                                                                            btns: [{ title: '关闭', name: 'close' }]
                                                                        };

                                                                        var helps = [];
                                                                        if (_val_obj.data !== false) {
                                                                            _form.title = '设置【' + _val_obj.title + '】接口';
                                                                            helps.push(_val_obj.help);
                                                                            var is_hide = true;
                                                                            for (var i = 0; i < _val_obj.data.length; i++) {
                                                                                _form.list.push({ title: _val_obj.data[i].name, name: _val_obj.data[i].key, value: _val_obj.data[i].value })
                                                                                if (!_val_obj.data[i].value) is_hide = false;
                                                                            }
                                                                            _form.btns.push({
                                                                                title: '保存', css: 'btn-success', name: 'btn_submit_save', callback: function (ldata, load) {
                                                                                    bt.site.set_dns_api({ pdata: JSON.stringify(ldata) }, function (ret) {
                                                                                        if (ret.status) {
                                                                                            load.close();
                                                                                            robj.find('input[type="radio"]:eq(0)').trigger('click')
                                                                                            robj.find('input[type="radio"]:eq(1)').trigger('click')
                                                                                        }
                                                                                        bt.msg(ret);
                                                                                    })
                                                                                }
                                                                            })
                                                                            if (is_hide) {
                                                                                obj.after('<button class="btn btn-default btn-sm mr5 set_dns_config">设置</button>');
                                                                                $('.set_dns_config').click(function () {
                                                                                    var _bs = bt.render_form(_form);
                                                                                    $('div[data-id="form' + _bs + '"]').append(bt.render_help(helps));
                                                                                })
                                                                            } else {
                                                                                var _bs = bt.render_form(_form);
                                                                                $('div[data-id="form' + _bs + '"]').append(bt.render_help(helps));
                                                                            }
                                                                        }
                                                                    }
                                                                },
                                                                {
                                                                    title: '等待 ', name: 'dnssleep', width: '60px', type: 'number', value: 10, unit: '秒', callback: function (obj) {
                                                                        if (obj.val() < 10) obj.val(10);
                                                                        if (obj.val() > 120) obj.val(120);
                                                                    }
                                                                }
                                                            ]
                                                        }, 
                                                            {
                                                                title: ' ', class: 'checks_line label-input-group', items:
                                                                [
                                                                    { css: 'label-input-group ptb10', text: '自动组合泛域名', name: 'app_root', type: 'checkbox' }
                                                                ]
                                                            }
                                                        ]
                                                        for (var i = 0; i < data.length; i++) {
                                                            var _form_data = bt.render_form_line(data[i]);
                                                            $(obj).parents('.line').append(_form_data.html)
                                                            bt.render_clicks(_form_data.clicks);
                                                        }
                                                    })
                                                }
                                            },
                                        ]
                                    },
                                    { title: '管理员邮箱', name: 'admin_email', value: rdata.email, width: '260px' }
                                ]
                                for (var i = 0; i < datas.length; i++) {
                                    var _form_data = bt.render_form_line(datas[i]);
                                    robj.append(_form_data.html);
                                    bt.render_clicks(_form_data.clicks);
                                }
                                var _ul = $('<ul id="ymlist" class="domain-ul-list"></ul>');
                                for (var i = 0; i < ddata.domains.length; i++) {
                                    if (ddata.domains[i].binding === true) continue
                                    _ul.append('<li style="cursor: pointer;"><input class="checkbox-text" type="checkbox" value="' + ddata.domains[i].name + '">' + ddata.domains[i].name + '</li>');
                                }
                                var _line = $("<div class='line mtb10'></div>");
                                _line.append('<span class="tname text-center">域名</span>');
                                _line.append(_ul);
                                robj.append(_line);
                                robj.find('input[type="radio"]').parent().addClass('label-input-group ptb10');
                                $("#ymlist li input").click(function (e) {
                                    e.stopPropagation();
                                })
                                $("#ymlist li").click(function () {

                                    var o = $(this).find("input");
                                    if (o.prop("checked")) {
                                        o.prop("checked", false)
                                    }
                                    else {
                                        o.prop("checked", true);
                                    }
                                })
                                var _btn_data = bt.render_form_line({
                                    title: ' ', text: '申请', name: 'letsApply', type: 'button', callback: function (ldata) {
                                        ldata['domains'] = [];
                                        $('#ymlist input[type="checkbox"]:checked').each(function () {
                                            ldata['domains'].push($(this).val())
                                        })
                                        var ddata = {
                                            siteName: web.name,
                                            email: ldata.admin_email,
                                            updateOf: 1,
                                            domains: JSON.stringify(ldata['domains'])
                                        }
                                        if (ldata.check_file) {
                                            ddata['force'] = ldata.force;
                                            site.create_let(ddata, function (res) {
                                                if (res.status) {
                                                    site.reload()
                                                }
                                            });
                                        }
                                        else {
                                            ddata['dnsapi'] = ldata.dns_select;
                                            ddata['dnssleep'] = ldata.dnssleep;
                                            ddata['app_root'] = ldata.app_root ? 1 : 0;
                                            site.create_let(ddata, function (ret) {
                                                if (ldata.dns_select == 'dns') {
                                                    if (ret.key) {
                                                        site.reload()
                                                        return;
                                                    }
                                                    if (!ret.status) {
                                                        bt.msg(ret)
                                                        return;
                                                    }
                                                    var b_load = bt.open({
                                                        type: 1,
                                                        area: '700px',
                                                        title: '手动解析TXT记录',
                                                        closeBtn: 2,
                                                        shift: 5,
                                                        shadeClose: false,
                                                        content: "<div class='divtable pd15 div_txt_jx'><p class='mb15' >请按以下列表做TXT解析:</p><table id='dns_txt_jx' class='table table-hover'></table><div class='text-right mt10'><button class='btn btn-success btn-sm btn_check_txt' >验证</button></div></div>",
                                                        success: function () {
                                                            bt.render({
                                                                table: '#dns_txt_jx',
                                                                columns: [
                                                                    { field: 'acme_name', width: '220px', title: '解析域名' },
                                                                    { field: 'domain_dns_value', title: 'TXT记录值' },
                                                                ],
                                                                data: ret.dns_names
                                                            })
                                                            if (ret.dns_names.length == 0) ret.dns_names.append('_acme-challenge.bt.cn')
                                                            $('.div_txt_jx').append(bt.render_help(['解析域名需要一定时间来生效,完成所以上所有解析操作后,请等待1分钟后再点击验证按钮', '可通过CMD命令来手动验证域名解析是否生效: nslookup -q=txt ' + ret.dns_names[0].acme_name, '若您使用的是宝塔云解析插件,阿里云DNS,DnsPod作为DNS,可使用DNS接口自动解析']));

                                                            $('.btn_check_txt').click(function () {
                                                                ddata['renew'] = 'True'
                                                                site.create_let(ddata, function (ldata) {
                                                                    if (ldata.status) {
                                                                        b_load.close();
                                                                        site.reload()
                                                                    }
                                                                });
                                                            })
                                                        }
                                                    });                                           
                                                }
                                                else {
                                                    site.reload()
                                                    bt.msg(ret);
                                                }
                                            })
                                        }
                                    }
                                });
                                robj.append(_btn_data.html);
                                bt.render_clicks(_btn_data.clicks);

                                robj.append(bt.render_help(helps[0]));
                                robj.find('input[type="radio"]:eq(0)').trigger('click')
                            })
                        }
                    },
                    {
                        title: "其他证书", callback: function (robj) {
                            var cert_info = '';
                            if (rdata.cert_data) {
                                cert_info = '<div style="margin-bottom: 10px;" class="alert alert-success">\
                                        <p style="margin-bottom: 9px;"><span style="width: 306px;display: inline-block;">'+ (rdata.status ? '<b>已部署成功：</b>请在证书到期之前更换新的证书' : '<b style="color:red;">当前未部署：</b>请点击【保存】按钮完成此证书的部署') + '</span>\
                                        <span style="margin-left: 20px;display: inline-block;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;max-width: 138px;width: 140px;">\
                                        <b>证书品牌：</b>'+ rdata.cert_data.issuer + '</span></p>\
                                        <span style="display:inline-block;max-width: 306px;overflow:hidden;text-overflow:ellipsis;vertical-align:-3px;white-space: nowrap;width: 357px;"><b>认证域名：</b> ' + rdata.cert_data.dns.join('、') + '</span>\
                                        <span style="margin-left: 20px;"><b>到期时间：</b> ' + rdata.cert_data.notAfter + '</span></div>'
                            }
                            var datas = []    
                            var helps = []
                            if (bt.get_cookie('serverType') == 'iis') {
                                robj.append("<div>" + cert_info +"</div>")
                                robj.append('<button class="btn btn-success btn-sm" onclick="site.upload_pfx(\'' + web.id + '\',\'' + web.name + '\')" style="margin-top:10px">导入证书</button>')
                                robj.append("<div class=\"divtable mtb15 table-fixed-box\" style=\"max-height:200px;overflow-y: auto;\"><table id='bt_ssl_list' class='table table-hover'></table></div>")
                                bt.render({
                                    table: '#bt_ssl_list',
                                    columns: [
                                        { field: 'name', title: '证书列表' },
                                        {
                                            field: 'opt', align: 'right', width: '100px', title: '操作', templet: function (item) {
                                                var opt = '<a class="btlink set-ssl" href="javascript:;">部署</a> | <a class="btlink del-ssl" href="javascript:;">删除</a>'
                                                if (item.setup) {
                                                    opt = '已部署 | <a class="btlink" onclick="site.ssl.set_ssl_status(\'CloseSSLConf\',\'' + web.name + '\')" >关闭</a>';
                                                }
                                                return opt;
                                            }
                                        }
                                    ],
                                    data: rdata.data
                                })
                                bt.fixed_table('bt_ssl_list');
                                $('a.set-ssl').click(function () {
                                    var _this = $(this);
                                    var item = $(this).parents('tr').data('item')
                                   
                                    bt.site.set_ssl(web.name, { cerName: item.name, password: item.password }, function (ret) {
                                        if (ret.status) site.reload(7);
                                        if (ret.msg.indexOf('password') >= 0) {
                                            var index = layer.open({
                                                type: 1,
                                                skin: 'demo-class',
                                                area: '350px',
                                                title: '填写证书密码',
                                                closeBtn: 2,
                                                shift: 5,
                                                shadeClose: false,
                                                content: "<div class='bt-form pd20 pb70' >\
							                        <div class='line'>\
							                        <span class='tname'>证书密码:</span><div class='info-r '><input  type='text' value='bt.cn' class='bt-input-text new_password' /></div>\
							                        </div>\
							                        <ul class='help-info-text c7'>\
								                        <li>在此处填写pfx证书密码!</li>\
								                        <li>宝塔证书默认密码bt.cn,其他证书咨询证书提供商!</li>\
							                        </ul>\
					                                <div class='bt-form-submit-btn'>\
								                        <button type='button' class='btn btn-danger btn-sm btn-title' onclick='layer.closeAll()'>取消</button>\
						                                <button type='button' class='btn btn-success btn-sm btn-title btnOtherSSL' >提交</button>\
					                                </div>\
					                                </div>"
                                            });
                                            setTimeout(function () {
                                                $(".btnOtherSSL").click(function () {
                                                    item.password = $(".new_password").val();
                                                    _this.parents('tr').data('item', item)
                                                    _this.trigger('click');
                                                    layer.close(index);
                                                })
                                            }, 100)

                                        }
                                    })
                                })
                                $('a.del-ssl').click(function () {
                                    var _item = $(this).parents('tr').data('item');
                                    bt.confirm({ msg: "是否确定删除" + _item.name+"？", title: '提示' }, function () {
                                        var loading = bt.load()
                                        bt.send("del_iis_other_ssl", 'site/del_iis_other_ssl', { filename: _item.name }, function (rdata) {
                                            loading.close();
                                            if (rdata.status) {
                                                site.reload();
                                            }
                                            bt.msg(rdata);
                                        })
                                    })
                                })
                                helps = ['IIS证书格式为.pfx文件', '宝塔证书密码为bt.cn,其他证书密码在证书目录password文件', '手动导入Let\'s Encrypt证书一律不支持续签功能']
                            }
                            else {

                                helps = [
                                    '粘贴您的*.key以及*.pem内容，然后保存即可<a href="http://www.bt.cn/bbs/thread-704-1-1.html" class="btlink" target="_blank">[帮助]</a>。',
                                    '如果浏览器提示证书链不完整,请检查是否正确拼接PEM证书',
                                    'PEM格式证书 = 域名证书.crt + 根证书(root_bundle).crt',
                                    '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点',
                                ]

                                robj.append('<div>' + cert_info+'<div><span>密钥(KEY)</span><span style="padding-left:194px">证书(PEM格式)</span></div></div>');
                                datas = [
                                    {
                                        items: [
                                            { name: 'key', width: '45%', height: '220px', type: 'textarea', value: rdata.key },
                                            { name: 'csr', width: '45%', height: '220px', type: 'textarea', value: rdata.csr }
                                        ]
                                    },
                                    {
                                        items: [
                                            {
                                                text: '保存', name: 'btn_ssl_save', type: 'button', callback: function (sdata) {
                                                    bt.site.set_ssl(web.name, sdata, function (ret) {
                                                        if (ret.status) site.reload(7);
                                                        bt.msg(ret);
                                                    })
                                                }
                                            },
                                            {
                                                text: '关闭SSL', name: 'btn_ssl_close', hide: rdata.status == false, type: 'button', callback: function (sdata) {
                                                    site.ssl.set_ssl_status('CloseSSLConf', web.name);
                                                }
                                            }
                                        ]
                                    }
                                ]
                                for (var i = 0; i < datas.length; i++) {
                                    var _form_data = bt.render_form_line(datas[i]);
                                    robj.append(_form_data.html);
                                    bt.render_clicks(_form_data.clicks);
                                }
                            }                            
                            robj.append(bt.render_help(helps));

                        }
                    },
                    {
                        title: "关闭", callback: function (robj) {
                            if (rdata.type == -1) {
                                robj.html("<div class='mtb15' style='line-height:30px'>" + lan.site.ssl_help_1 + "</div>");
                                return;
                            };
                            var txt = '';
                            switch (rdata.type) {
                                case 1:
                                    txt = "Let's Encrypt";
                                    break;
                                case 0:
                                    txt = '其他证书';
                                    break;
                                case 2:
                                    txt = lan.site.bt_ssl;
                                    break;
                            }
                            $(".tab-con").html("<div class='line mtb15'>" + lan.get('ssl_enable', [txt]) + "</div><div class='line mtb15'><button class='btn btn-success btn-sm' onclick=\"site.ssl.set_ssl_status('CloseSSLConf','" + web.name + "')\">" + lan.site.ssl_close + "</button></div>");

                        }
                    },
                    {
                        title: "证书夹", callback: function (robj) {
                            robj.html("<div class='divtable'><table id='cer_list_table' class='table table-hover'></table></div>");
                            bt.site.get_cer_list(function (rdata) {
                                bt.render({
                                    table: '#cer_list_table',
                                    columns: [
                                        {
                                            field: 'subject', title: '域名', templet: function (item) {
                                                return item.dns.join('<br>')
                                            }
                                        },
                                        { field: 'notAfter', width: '83px', title: '到期时间' },
                                        { field: 'issuer', width: '150px', title: '品牌' },
                                        {
                                            field: 'opt', width: '75px', align: 'right', title: '操作', templet: function (item) {
                                                var server_type = bt.get_cookie("serverType")
                                                var opt = ''
                                                console.log(item.type, server_type)
                                                if ((item.type == 'pfx' && server_type == 'iis') || (item.type == 'pem' && server_type != 'iis')) {
                                                    opt += '<a class="btlink" onclick="bt.site.set_cert_ssl(\'' + item.subject + '\',\'' + web.name + '\',function(rdata){if(rdata.status){site.ssl.reload(2);}})" href="javascript:;">部署</a> |'
                                                }                                                
                                                                                             
                                                opt += '<a class="btlink" onclick="bt.site.remove_cert_ssl(\'' + item.subject + '\',function(rdata){if(rdata.status){site.ssl.reload(4);}})" href="javascript:;">删除</a>'
                                                return opt;
                                            }
                                        }
                                    ],
                                    data: rdata
                                })

                                robj.append(bt.render_help(['证书夹部署Let\'s Encrypt不具备自动续签功能']));
                            })
                        }
                    },
                    {
                        title: "IIS证书", callback: function (robj) {
                            var loading = bt.load()
                            robj.append("<div id='ssl_domain_list_panel' class=\"divtable mtb15 table-fixed-box\" style=\"max-height:500px;overflow-y: auto;\"><table id='ssl_domain_list' class='table table-hover'></table></div>")
                            bt.send("get_iis_ssl_bydomain", "site/get_iis_ssl_bydomain", { siteName: web.name }, function (res) {
                                loading.close();
                                if (res.status == false) {
                                    bt.msg(res)
                                    return
                                }
                                var _tab = bt.render({
                                    table: '#ssl_domain_list',
                                    columns: [                                     
                                        { field: 'name', title: '网站域名' },
                                        {
                                            field: 'subject', title: '证书域名', templet: function (item) {
                                                if (item.status) {
                                                    return item.cert.dns.join('<br>')
                                                }
                                                return '--'
                                            }
                                        },
                                        {
                                            field: 'notAfter', width: '83px', title: '到期时间', templet: function (item) {
                                                if (item.status) {
                                                    return item.cert.notAfter
                                                }
                                                return '--'
                                            }
                                        },                                     
                                        {
                                            field: 'status', width: '150px', title: '部署状态', templet: function (item) {
                                                var msg = "";
                                                if (item.status == true) {
                                                    msg = "<span>已部署";                                                   
                                                    if ($.inArray(item.name,item.cert.dns) < 0) {
                                                        msg += ' <span style="color:red">[证书不匹配]</span>';
                                                    }                                   
                                                    msg += "</span>";
                                                }
                                                else {
                                                    msg = "<span>未部署</span>";
                                                }
                                                return msg;
                                            }
                                        },
                                        {
                                            field: 'name',align:"right", title: '操作', width: 60, templet: function (item) {
                                                return '<a class="btlink" href="javascript:;" onclick="site.edit.set_iis_domain_ssl(\''+web.name+'\',this)">部署</a> ';
                                            }
                                        }
                                    ],
                                    data: res
                                })
                                robj.append(bt.render_help(['IIS默认一个网站部署一个证书，如果需要给每个域名部署证书，请阅读 <a href="https://www.bt.cn/bbs/thread-35492-1-1.html" class="btlink" target="_blank">[帮助]</a>。','证书不匹配：表示证书域名列表不包括此域名，需要自行设置有效的域名']));
                            })
                        }
                    }
                ]
                bt.render_tab('ssl_tabs', _tabs);

                $('#ssl_tabs').append('<div class="ss-text pull-right mr30" style="position: relative;top:-4px"><em>强制HTTPS</em><div class="ssh-item"><input class="btswitch btswitch-ios" id="toHttps" type="checkbox"><label class="btswitch-btn" for="toHttps"></label></div></div>');
                $("#toHttps").attr('checked', rdata.httpTohttps);
                $('#toHttps').click(function (sdata) {
                    var isHttps = $("#toHttps").attr('checked');
                    if (isHttps) {
                        layer.confirm('关闭强制HTTPS后需要清空浏览器缓存才能看到效果,继续吗?', { icon: 3, title: "关闭强制HTTPS" }, function () {
                            bt.site.close_http_to_https(web.name, function () { site.reload(7); })
                        });
                    }
                    else {
                        if (rdata.status == false) {
                            bt.msg({ status: false, msg: '请先部署SSL证书，否则无法强制跳转HTTPS.' })
                            return;
                        }
                        bt.site.set_http_to_https(web.name, function (res) {
                            if (res.status) {
                                site.reload();
                            }
                            else {
                                $("#toHttps").attr('checked', rdata.httpTohttps);
                            }
                            bt.msg(res);
                        })
                    }
                })
                switch (rdata.type) {
                    case 1:
                        $('#ssl_tabs span:eq(1)').trigger('click');
                        break;
                    case 0:
                        $('#ssl_tabs span:eq(2)').trigger('click');
                        break;
                    default:
                        $('#ssl_tabs span:eq(0)').trigger('click');
                        break;
                }

            })
        },
        set_iis_domain_ssl: function (siteName, obj) {

            var loading = bt.load()
            bt.send("get_iis_ssl_file_list", "site/get_iis_ssl_file_list", { siteName: siteName }, function (res) {
                loading.close();
                if (res.status == false) {
                    bt.msg(res)
                    return
                }
                var _domain = $(obj).parents('tr').data('item');
                site.ssl.my_select_domain_ssl_index = layer.open({
                    type: 1,
                    area: ['550px', '550px'],
                    title: '部署域名【' + _domain.name + '】SSL证书',
                    closeBtn: 2,
                    shift: 0,
                    content: "<div class=\"divtable pd20 mtb15 table-fixed-box\" style=\"max-height:500px;overflow-y: auto;\"><table id='ssl_select_list' class='table table-hover'></table></div>",
                    success : function () {                        
                        var _tab = bt.render({
                            table: '#ssl_select_list',
                            columns: [                                                              
                                {
                                    field: 'subject', title: '证书域名', templet: function (item) {
                                        return item.dns.join('<br>')
                                    }
                                },
                                { field: 'notAfter', width: '83px', title: '到期时间'},  
                                { field: 'issuer', width: '130px', title: '品牌' },  
                                {
                                    field: 'name', align: "right", title: '操作', width: 60, templet: function (item) {
                                        return '<a class="btlink" href="javascript:;" onclick="site.edit.set_domain_iis_byfile(\'' + _domain.name + '\',\'' + item.path + '\')" >选择</a> ';
                                    }
                                }
                            ],
                            data: res
                        })

                    }
                })
            })
        },
        set_domain_iis_byfile: function (domain, path,password) {
            var loading = bt.load("正在部署【" + domain + "】证书...");
            bt.send("set_domain_iis_byfile", "site/set_domain_iis_byfile", { domain: domain, path: path, password: password }, function (res) {
                loading.close();
               
                if (res.msg.indexOf('password') >= 0) {
                    var index = layer.open({
                        type: 1,
                        skin: 'demo-class',
                        area: '350px',
                        title: '填写证书密码',
                        closeBtn: 2,
                        shift: 5,
                        shadeClose: false,
                        content: "<div class='bt-form pd20 pb70' >\
							        <div class='line'>\
							        <span class='tname'>证书密码:</span><div class='info-r '><input  type='text' value='bt.cn' class='bt-input-text new_password' /></div>\
							        </div>\
							        <ul class='help-info-text c7'>\
								        <li>在此处填写pfx证书密码!</li>\
								        <li>宝塔证书默认密码bt.cn,其他证书咨询证书提供商!</li>\
							        </ul>\
					                <div class='bt-form-submit-btn'>\
								        <button type='button' class='btn btn-danger btn-sm btn-title' onclick='layer.closeAll()'>取消</button>\
						                <button type='button' class='btn btn-success btn-sm btn-title btnOtherSSL' >提交</button>\
					                </div>\
					                </div>",
                        success: function () {
                            $(".btnOtherSSL").click(function () {                              
                                site.edit.set_domain_iis_byfile(domain, path, $(".new_password").val())
                                layer.close(index);
                            })
                        }
                        
                    });
                }
                else {
                    if (res.status) {
                        if (site.ssl.my_select_domain_ssl_index) {
                            layer.close(site.ssl.my_select_domain_ssl_index); 
                        }                        
                        site.ssl.reload()
                    }
                    bt.msg(res);
                }                
            })
        },
        set_php_version: function (web) {
            var loadT = bt.load();
            bt.site.get_site_phpversion(web.name, function (sdata) {
                if (sdata.status === false) {
                    bt.msg(sdata);
                    return;
                }
                bt.site.get_all_phpversion(function (vdata) {
                    loadT.close();
                    var versions = [];
                    for (var j = vdata.length - 1; j >= 0; j--) {
                        var o = vdata[j];
                        o.value = o.version;
                        o.title = o.name;
                        versions.push(o);
                    }
                    var data = {
                        items: [
                            { title: 'PHP版本', name: 'versions', value: sdata.phpversion, type: 'select', items: versions },
                            {
                                text: '切换', name: 'btn_change_phpversion', type: 'button', callback: function (pdata) {
                                    bt.site.set_phpversion(web.name, pdata.versions, function (ret) {
                                        if (ret.status) site.reload(8)
                                        bt.msg(ret);
                                    })
                                }
                            }
                        ]
                    }
                    var _form_data = bt.render_form_line(data);
                    var _html = $(_form_data.html);
                    _html.append(bt.render_help(['请根据您的程序需求选择版本', '若非必要,请尽量不要使用PHP5.2,这会降低您的服务器安全性；', 'PHP7不支持mysql扩展，默认安装mysqli以及mysql-pdo。']));
                    $('#webedit-con').append(_html);
                    bt.render_clicks(_form_data.clicks);
                })
            })
        },
        templet_301: function (web, obj) {
            var is_create = false
            if (obj === false) {
                is_create = true
                obj = {
                    redirectname: (new Date()).valueOf(),
                    tourl: 'http://',
                    redirectdomain: [],
                    redirectpath: '',
                    redirecttype: '',  
                    domainorpath: 'domain',
                    type: 1,
                    holdpath : 1
                }
            }
            var helps = [
                '重定向类型：表示访问选择的“域名”或输入的“路径”时将会重定向到指定URL',
                '目标URL：可以填写你需要重定向到的站点，目标URL必须为可正常访问的URL，否则将返回错误',
                '重定向方式：使用301表示永久重定向，使用302表示临时重定向',
                '保留URI参数：表示重定向后访问的URL是否带有子路径或参数如设置访问http://b.com 重定向到http://a.com',
                '保留URI参数： http://b.com/1.html ---> http://a.com/1.html',
                '不保留URI参数：http://b.com/1.html ---> http://a.com'
            ];
            bt.site.get_domains(web.id, function (rdata) {
                var domains = [];

                for (var i = 0; i < rdata.length; i++) {
                    var val = rdata[i].name;
                    if (rdata[i].port != 80) val += ':' + rdata[i].port;
                    domains.push({ title: val, value: val });
                }

                var form_data = {
                    title: is_create ? '创建重定向' : '修改重定向[' + obj.redirectname + ']',
                    area: '650px',
                    skin: 'site-301-form',
                    list: [
                        {
                            class: 'btswitch-line ',
                            items: [
                                { title: '开启重定向  ', name: 'type', value: obj.type == 1 ? true : false, type: 'btswitch' },
                                { title: '保留URI参数  ', name: 'holdpath', value: obj.holdpath == 1 ? true : false, type: 'btswitch' }
                            ]
                        },
                        { title: '重定向名称  ', value: obj.redirectname, name: 'redirectname', width: '300px', hide: true },
                        {
                            items: [
                                {
                                    title: '重定向类型  ', name: 'domainorpath', value: obj.domainorpath, type: 'select', items: [
                                        { title: '域名', value: 'domain' },
                                        { title: '路径', value: 'path' },
                                    ], callback: function (sobj) {
                                        var subid = sobj.attr('name') + '_subid';
                                        $('#' + subid).remove();
                                        if (sobj.val() == 'domain') {
                                            var item = {
                                                items: [
                                                    { title: '重定向域名 ', name: 'redirectdomain', width: '173px', type: 'select', class: 'selectpicker', items: domains },
                                                    { title: '目标URL  ', name: 'tourl', value: obj.tourl, width: '173px' },
                                                ]
                                            }
                                            var _tr = bt.render_form_line(item)
                                            sobj.parents('div.line').append('<div class="line" id=' + subid + '>' + _tr.html + '</div>');

                                            site.edit.render_sel('redirectdomain')  
                                        }
                                        else {
                                            var item = {
                                                items: [
                                                    { title: '重定向路径  ', name: 'redirectpath', value: obj.redirectpath, width: '173px' },
                                                    { title: '目标URL  ', name: 'tourl', value: obj.tourl, width: '173px' },
                                                ]
                                            }
                                            var _tr = bt.render_form_line(item)
                                            sobj.parents('div.line').append('<div class="line" id=' + subid + '>' + _tr.html + '</div>');
                                        }
                                    }
                                },
                                {
                                    title: '重定向方式 ', name: 'redirecttype', value: obj.redirecttype, type: 'select', items: [
                                        { title: '301', value: '301' },
                                        { title: '302', value: '302' },
                                    ]
                                }
                            ]
                        }
                    ],
                    btns: [
                        bt.form.btn.close(),
                        bt.form.btn.submit('提交', function (rdata, load) {
                            if (!rdata.hasOwnProperty("redirectpath")) {
                                rdata['redirectpath'] = ''
                            }
                            rdata.type = rdata.type ? 1 : 0;
                            rdata.holdpath = rdata.holdpath ? 1 : 0;
            
                            rdata['sitename'] = web.name;
                            rdata['redirectdomain'] = JSON.stringify($('.selectpicker').val() || []);
                            if (is_create) {
                                bt.site.create_redirect(rdata, function (rdata) {
                                    if (rdata.status) {
                                        load.close();
                                        site.reload();
                                    }
                                    bt.msg(rdata);
                                });
                            }
                            else {
                                bt.site.modify_redirect(rdata, function (rdata) {
                                    if (rdata.status) {
                                        load.close();
                                        site.reload();
                                    }
                                    bt.msg(rdata);
                                });
                            }                         
                        })
                    ]
                }
                bt.render_form(form_data);
                $('.' + form_data.skin + ' .bt-form').append(bt.render_help(helps));
                setTimeout(function () {
                    $("select[name='domainorpath']").trigger("change")

                }, 100)


            });
        },
        edit_redirect: function (obj,name) {
            var item = $(obj).parents('tr').data('item');
            if (item[name]) {
                item[name] = 0;
            } else {
                item[name] = 1
            }
            item['redirectdomain'] = JSON.stringify(item['redirectdomain'] || []);

            bt.site.modify_redirect(item, function (rdata) {
                if (rdata.status) {
                    site.reload();
                }
                bt.msg(rdata);
            });
        },
        template_Dir: function (id, type, obj) {
            if (type) {
                obj = { "name": "", "sitedir": "", "username": "", "password": "" };
            } else {
                obj = { "name": obj.name, "sitedir": obj.site_dir, "username": obj.username, "password": obj.password };
            }
            var form_directory = bt.open({
                type: 1,
                skin: 'demo-class',
                area: '550px',
                title: type ? '添加目录保护' : '修改目录目录',
                closeBtn: 2,
                shift: 5,
                shadeClose: false,
                content: "<form id='form_dir' class='divtable pd15' style='padding: 40px 0 90px 60px'>" +
                    "<div class='line'>" +
                    "<span class='tname'>名称</span>" +
                    "<div class='info-r ml0'><input name='dir_name' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.name + "'>" +
                    "</div></div>" +
                    "<div class='line'>" +
                    "<span class='tname'>保护的目录</span>" +
                    "<div class='info-r ml0'><input name='dir_sitedir' placeholder='输入需要保护的目录，如：/text/' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.sitedir + "'>" +
                    "</div></div>" +
                    "<div class='line'>" +
                    "<span class='tname'>用户名</span>" +
                    "<div class='info-r ml0'><input name='dir_username' AUTOCOMPLETE='off' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.username + "'>" +
                    "</div></div>" +
                    "<div class='line'>" +
                    "<span class='tname'>密码</span>" +
                    "<div class='info-r ml0'><input name='dir_password' AUTOCOMPLETE='off' class='bt-input-text mr10' type='password' style='width:270px' value='" + obj.password + "'>" +
                    "</div></div>" +
                    "<ul class='help-info-text c7 plr20'>" +
                    "<li>目录设置保护后，访问时需要输入账号密码才能访问</li>" +
                    "<li>例如我设置了保护目录 /test/ ,那我访问 http://aaa.com/test/ 是就要输入账号密码才能访问</li>" +
                    "</ul>" +
                    "<div class='bt-form-submit-btn'><button type='button' class='btn btn-sm btn-danger btn-colse-guard'>关闭</button><button type='button' class='btn btn-sm btn-success btn-submit-guard'>" + (type ? '提交' : '保存') + "</button></div></form>"
            });
            $('.btn-colse-guard').click(function () {
                form_directory.close();
            });
            $('.btn-submit-guard').click(function () {
                var guardData = {};
                guardData['id'] = id;
                guardData['name'] = $('input[name="dir_name"]').val();
                guardData['site_dir'] = $('input[name="dir_sitedir"]').val();
                guardData['username'] = $('input[name="dir_username"]').val();
                guardData['password'] = $('input[name="dir_password"]').val();
                if (type) {
                    bt.site.create_dir_guard(guardData, function (rdata) {
                        if (rdata.status) {
                            form_directory.close();
                            site.reload()
                        }
                        bt.msg(rdata);
                    });
                } else {
                    bt.site.edit_dir_account(guardData, function (rdata) {
                        if (rdata.status) {
                            form_directory.close();
                            site.reload()
                        }
                        bt.msg(rdata);
                    });
                }
            });
            setTimeout(function () {
                if (!type) {
                    $('input[name="dir_name"]').attr('disabled', 'disabled');
                    $('input[name="dir_sitedir"]').attr('disabled', 'disabled');
                }
            }, 500)

        },
        set_301: function (web) {
            bt.site.get_redirect_list(web.name, function (rdata) {
                if (rdata.status === false) {
                    bt.msg(rdata);
                    return
                }
                var datas = {
                    items: [{ name: 'add_proxy', text: '添加重定向', type: 'button', callback: function (data) { site.edit.templet_301(web, false) } }]
                }
                var form_line = bt.render_form_line(datas);
                $('#webedit-con').append(form_line.html);
                bt.render_clicks(form_line.clicks);
                $('#webedit-con').addClass('divtable').append('<table id="proxy_list" class="table table-hover"></table>');
                setTimeout(function () {
                    var _tab = bt.render({
                        table: '#proxy_list',
                        columns: [                           
                            {
                                field: '', title: '重定向类型', templet: function (item) {
                                    var conter = '';
                                    if (item.domainorpath == 'path') {
                                        conter = item.redirectpath;
                                    } else {
                                        conter = item.redirectdomain ? item.redirectdomain.join('、') : '空'
                                    }
                                    return '<span style="width:100px;" title="' + conter + '">' + conter + '</span>';
                                }
                            },
                            { field: 'redirecttype', title: '重定向方式' },
                            {
                                field: 'holdpath', index: true, title: '保留路径', templet: function (item) {
                                    return '<a href="javascript:;" onclick="site.edit.edit_redirect(this,\'holdpath\')" class="btlink set_path_state" style="display:" data-stuats="' + (item.holdpath == 1 ? 0 : 1) + '">' + (item.holdpath == 1 ? '<span style="color:#20a53a;" class="set_path_state">开启</span>' : '<span style="color:red;" class="set_path_state">关闭</span>') + '</a>';
                                }
                            },
                            {
                                field: 'type', title: '状态', index: true, templet: function (item) {
                                    return '<a href="javascript:;" onclick="site.edit.edit_redirect(this,\'type\')" class="btlink set_type_state" style="display:" data-stuats="' + (item.type == 1 ? 0 : 1) + '">' + (item.type == 1 ? '<span style="color:#20a53a;">运行中</span><span style="color:#5CB85C" class="glyphicon glyphicon-play"></span>' : '<span style="color:red;">已暂停</span><span style="color:red" class="glyphicon glyphicon-pause"></span>') + '</a>'
                                }
                            },
                            {
                                field: '', title: '操作', align: 'right', index: true, templet: function (item) {
                                    var redirectname = item.redirectname;
                                    var sitename = item.sitename;
                                    var open_file = '';
                                    if (bt.get_cookie("serverType") != 'iis') {
                                        open_file = '<a class="btlink open_config_file" href="javascript:;">配置文件</a> | '
                                    }
                                    var conter = open_file + ' <a class="btlink edit_redirect"  href="javascript:;">编辑</a> | <a class="btlink" onclick="bt.site.remove_redirect(\'' + sitename + '\',\'' + redirectname + '\',function(rdata){if(rdata.status)site.reload(10)})" href="javascript:;">删除</a>';
                                    return conter
                                }
                            }
                        ],
                        data: rdata
                    });

                    $('.edit_redirect').click(function () {
                        var item = $(this).parents('tr').data('item');
                        site.edit.templet_301(web, item);
                    });
                    $('.open_config_file').click(function () {
                        var item = $(this).parents('tr').data('item');

                        var sitename = web.name;
                        var redirectname = item.redirectname;
                        var redirect_config = '';
                        bt.site.get_redirect_config({
                            sitename: sitename,
                            redirectname: redirectname,
                            webserver: bt.get_cookie('serverType')
                        }, function (rdata) {
                            if (typeof rdata == 'object' && rdata.constructor == Array) {
                                if (!rdata[0].status) bt.msg(rdata)
                            } else {
                                if (rdata.status == false) bt.msg(rdata)
                            }
                            var datas = [
                                { items: [{ name: 'redirect_configs', type: 'textarea', value: rdata[0].data, widht: '340px', height: '200px' }] },
                                {
                                    name: 'btn_config_submit', text: '保存', type: 'button', callback: function (ddata) {
                                        bt.site.save_redirect_config({ path: rdata[1], data: editor.getValue(), encoding: rdata[0].encoding }, function (ret) {
                                            if (ret.status) {
                                                site.reload(11);
                                                redirect_config.close();
                                            }
                                            bt.msg(ret);
                                        })
                                    }
                                }
                            ]
                            redirect_config = bt.open({
                                type: 1,
                                area: ['550px', '550px'],
                                title: '编辑配置文件[' + redirectname + ']',
                                closeBtn: 2,
                                shift: 0,
                                content: "<div class='bt-form'><div id='redirect_config_con' class='pd15'></div></div>"
                            })
                            var robj = $('#redirect_config_con');
                            for (var i = 0; i < datas.length; i++) {
                                var _form_data = bt.render_form_line(datas[i]);
                                robj.append(_form_data.html);
                                bt.render_clicks(_form_data.clicks);
                            }
                            robj.append(bt.render_help(['此处为重定向的配置文件，若您不了解配置规则,请勿随意修改。']));
                            $('textarea.redirect_configs').attr('id', 'configBody');
                            var editor = CodeMirror.fromTextArea(document.getElementById("configBody"), {
                                extraKeys: { "Ctrl-Space": "autocomplete" },
                                lineNumbers: true,
                                matchBrackets: true
                            });
                            $(".CodeMirror-scroll").css({ "height": "350px", "margin": 0, "padding": 0 });
                            setTimeout(function () {
                                editor.refresh();
                            }, 250);
                        });
                    });
                }, 100);
            });
        },
        render_sel: function (name) {
            var _domain_sel = $("select[name='" + name + "']");
            _domain_sel.attr('data-actions-box', true);
            _domain_sel.attr('multiple', true);
            _domain_sel.attr('data-live-search', false);
            _domain_sel.addClass('selectpicker show-tick form-control');

            _domain_sel.selectpicker({
                'noneSelectedText': '请选择站点...',
                'selectAllText': '全选',
                'deselectAllText': '取消全选'
            });
            _domain_sel.parents('.bootstrap-select').attr('style', 'float: inherit!important')

        },
        templet_proxy: function (web, obj) {
            var is_create = false
            if (obj === false) {
                is_create = true
                obj = {
                    proxyname: (new Date()).valueOf(),
                    tourl: 'http://',
                    proxydomains:[],
                    to_domian: '$host',       
                    open: 1,
                    cache_open: 1,
                    path_open: 0,
                    root_path:'/',
                }
            }
            if (!obj.hasOwnProperty("sub1")) {
                obj['sub1'] = '';
                obj['sub2'] = '';
            }
            var helps = [
                '代理目录：访问这个目录时将会把目标URL的内容返回并显示(需要开启高级功能)',
                '目标URL：可以填写你需要代理的站点，目标URL必须为可正常访问的URL，否则将返回错误',
                '发送域名：将域名添加到请求头传递到代理服务器，默认为目标URL域名，若设置不当可能导致无法正常运行',
                '内容替换：只能在使用nginx时提供，多个内容用逗号分开，如sub1,sub2替换为str1,str2',
            ];
            bt.site.get_domains(web.id, function (rdata) {
                var domains = [];

               

                for (var i = 0; i < rdata.length; i++) {
                    var val = rdata[i].name;
                    if (rdata[i].port != 80) val += ':' + rdata[i].port;
                    domains.push({ title: val, value: val });
                }

                var form_data = {
                    title: is_create ? '创建反向代理' : '修改反向代理[' + obj.proxyname + ']',
                    area: '650px',
                    skin: 'site-proxy-form',
                    list: [
                        {
                            class: 'btswitch-line ',
                            items: [
                                { title: '开启代理  ', name: 'open', value: obj.open == 1 ? true : false, type: 'btswitch' },
                                { title: '开启缓存  ', name: 'cache_open', hide: bt.get_cookie('serverType') == 'iis' ? false : true, value: obj.cache_open == 1 ? true : false, type: 'btswitch' },
                                {
                                    title: '高级功能  ', name: 'path_open', value: obj.path_open == 1 ? true : false, type: 'btswitch'
                                }
                            ]
                        },
                        { items: [{ title: '代理名称   ', disabled: is_create ? false : true, width: '200px', value: obj.proxyname, name: 'proxyname' }] },     
                        { class: 'root_path-line', items: [{ title: '代理路径   ', width: '200px', value: obj.root_path, name: 'root_path' }] },     
                        { items: [{ title: '请求域名   ', hide: bt.get_cookie('serverType') == 'iis' ? false : true,name: 'proxydomains', type: 'select', class: 'selectpicker', items: domains }] },
                        {
                            items: [
                                {
                                    title: '目标URL   ', name: 'tourl', value: obj.tourl, width: '200px', callback: function (robj) {
                                      
                                        var val = $(robj).val(), ip_reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
                                        val = val.replace(/^http[s]?:\/\//, '');
                                        val = val.replace(/:([0-9]*)$/, '');
                                        if (ip_reg.test(val) || bt.get_cookie('serverType') == 'iis') {
                                            $("input[name='to_domian']").val('$host');
                                        } else {
                                            $("input[name='to_domian']").val(val);
                                        }
                                    }
                                },
                                { title: '发送域名   ', name: 'to_domian', value: obj.to_domian, width: '200px' },
                            ]
                        },
                        {
                            hide : bt.get_cookie('serverType') == 'nginx' ? false : true,
                            items: [
                                { title: '替换内容   ', name: 'sub1', value: obj.sub1, width: '200px' },
                                { title: '&nbsp;&nbsp;&nbsp;替换为   ', name: 'sub2', value: obj.sub2, width: '200px' },                               
                            ]
                        }
                    ],
                    btns: [
                        bt.form.btn.close(),
                        bt.form.btn.submit('提交', function (rdata, load) {

                            if (rdata.sub1.split(',').length != rdata.sub2.split(',').length) {
                                bt.msg({ status: false,msg:'替换内容个数必须与替换后个数量相等.'});
                                return;
                            }

                            rdata.open = rdata.open ? 1 : 0;
                            rdata.cache_open = obj['cache_open']
                            rdata.path_open = rdata.path_open ? 1 : 0;
                            rdata['sitename'] = web.name;
                            rdata['proxydomains'] = JSON.stringify($('.selectpicker').val() || []);

                            if (is_create) {
                                bt.site.create_proxy(rdata, function (rdata) {
                                    if (rdata.status) {
                                        load.close();
                                        site.reload();
                                    }
                                    bt.msg(rdata);
                                });
                            }
                            else {
                                bt.site.modify_proxy(rdata, function (rdata) {
                                    if (rdata.status) {
                                        load.close();
                                        site.reload();
                                    }
                                    bt.msg(rdata);
                                });
                            }
                        })
                    ],
                    sucess: function () {
                     
                    }
                }
                bt.render_form(form_data);
           
                $('.' + form_data.skin + ' .bt-form').append(bt.render_help(helps));
                site.edit.render_sel('proxydomains')  

                $("#path_open").change(function () {
                    var robj = $('.root_path-line');
                    if ($(this).prop('checked')) {
                        robj.show();
                    } else {
                        robj.hide();
                    }                    
                })     

                $("#path_open").trigger("change")
            });
        },
        edit_proxy : function (obj, name) {
            var item = $(obj).parents('tr').data('item');
            if (item[name]) {
                item[name] = 0;
            } else {
                item[name] = 1
            }
            item['proxydomains'] = JSON.stringify(item['proxydomains'] || []);

            bt.site.modify_proxy(item, function (rdata) {
                if (rdata.status) {
                    site.reload();
                }
                bt.msg(rdata);
            });
        },
        set_proxy: function (web) {
            bt.site.get_proxy_list(web.name, function (rdata) {
                if (rdata.status === false) {
                    rdata.time = 0
                    bt.msg(rdata);
                    return;
                }
                var robj = $('#webedit-con');
                var datas = {
                    items: [{ name: 'add_proxy', text: '添加反向代理', type: 'button', callback: function (data) { site.edit.templet_proxy(web, false) } }]
                }
                var form_line = bt.render_form_line(datas);
                $('#webedit-con').append(form_line.html);
                bt.render_clicks(form_line.clicks);
                $('#webedit-con').addClass('divtable').append('<table id="proxy_list" class="table table-hover"></table>');
                setTimeout(function () {
                    var _tab = bt.render({
                        table: '#proxy_list',
                        columns: [
                            {
                                field: 'proxyname', title: '名称', templet: function (item) {
                                    return '<span style="width:70px;" title="' + item.proxyname + '">' + item.proxyname + '</span>';
                                }
                            },
                            { field: 'root_path', title: '目录' },
                            {
                                field: 'tourl', title: '目标url', templet: function (item) {
                                    return '<span style="width:70px;" title="' + item.tourl + '">' + item.tourl + '</span>';
                                }
                            },
                            {
                                field: 'open', title: '状态', index: true, templet: function (item) {
                                    return '<a href="javascript:;" onclick="site.edit.edit_proxy(this,\'open\')" class="btlink set_type_state" style="display:" data-stuats="' + (item.open == 1 ? 0 : 1) + '">' + (item.open == 1 ? '<span style="color:#20a53a;">运行中</span><span style="color:#5CB85C" class="glyphicon glyphicon-play"></span>' : '<span style="color:red;">已暂停</span><span style="color:red" class="glyphicon glyphicon-pause"></span>') + '</a>'
                                }
                            },
                            {
                                field: 'cache_open', title: '缓存', index: true, templet: function (item) {
                                    return '<a href="javascript:;" onclick="site.edit.edit_proxy(this,\'cache_open\')" class="btlink set_type_state" style="display:" data-stuats="' + (item.cache_open == 1 ? 0 : 1) + '">' + (item.cache_open == 1 ? '<span style="color:#20a53a;">开启</span><span style="color:#5CB85C" class="glyphicon glyphicon-play"></span>' : '<span style="color:red;">关闭</span><span style="color:red" class="glyphicon glyphicon-pause"></span>') + '</a>'
                                }
                            },
                            {
                                field: '', title: '操作',width:'150px', align: 'right', index: true, templet: function (item) {
                                    var redirectname = item.redirectname;
                                    var sitename = item.sitename;
                                    var open_file = '';
                                    if (bt.get_cookie("serverType") != 'iis') {
                                        open_file = '<a class="btlink open_config_file" href="javascript:;">配置文件</a> | '
                                    }
                                    var conter = open_file + ' <a class="btlink edit_proxy"  href="javascript:;">编辑</a> | <a class="btlink" onclick="bt.site.remove_proxy(\'' + sitename + '\',\'' + item.proxyname + '\',function(rdata){if(rdata.status)site.reload()})" href="javascript:;">删除</a>';
                                    return conter
                                }
                            }
                        ],
                        data: rdata
                    });
                    $('.open_config_file').click(function () {
                        var item = $(this).parents('tr').data('item');
                        var sitename = web.name;
                        var proxyname = item.proxyname;
     
                        var proxy_config = '';
                        bt.site.get_proxy_config({
                            sitename: sitename,
                            proxyname: proxyname,
                            webserver: bt.get_cookie('serverType')
                        }, function (rdata) {
                            if (typeof rdata == 'object' && rdata.constructor == Array) {
                                if (!rdata[0].status) bt.msg(rdata)
                            } else {
                                if (rdata.status == false) bt.msg(rdata)
                            }
                            var datas = [
                                { items: [{ name: 'proxy_configs', type: 'textarea', value: rdata[0].data, widht: '340px', height: '200px' }] },
                                {
                                    name: 'btn_config_submit', text: '保存', type: 'button', callback: function (ddata) {
                                        bt.site.save_proxy_config({ path: rdata[1], data: editor.getValue(), encoding: rdata[0].encoding }, function (ret) {
                                            if (ret.status) {
                                                site.reload(12);
                                                proxy_config.close();
                                            }
                                            bt.msg(ret);
                                        })
                                    }
                                }
                            ]
                            proxy_config = bt.open({
                                type: 1,
                                area: ['550px', '550px'],
                                title: '编辑配置文件[' + proxyname + ']',
                                closeBtn: 2,
                                shift: 0,
                                content: "<div class='bt-form'><div id='proxy_config_con' class='pd15'></div></div>"
                            })
                            var robj = $('#proxy_config_con');
                            for (var i = 0; i < datas.length; i++) {
                                var _form_data = bt.render_form_line(datas[i]);
                                robj.append(_form_data.html);
                                bt.render_clicks(_form_data.clicks);
                            }
                            robj.append(bt.render_help(['此处为该负载均衡的配置文件，若您不了解配置规则,请勿随意修改。']));
                            $('textarea.proxy_configs').attr('id', 'configBody');
                            var editor = CodeMirror.fromTextArea(document.getElementById("configBody"), {
                                extraKeys: { "Ctrl-Space": "autocomplete" },
                                lineNumbers: true,
                                matchBrackets: true
                            });
                            $(".CodeMirror-scroll").css({ "height": "350px", "margin": 0, "padding": 0 });
                            setTimeout(function () {
                                editor.refresh();
                            }, 250);
                        });
                    });
                    $('.edit_proxy').click(function () {
                        var item = $(this).parents('tr').data('item');
                        site.edit.templet_proxy(web, item);
                    });
                })
            })
        },
        set_security: function (web) {
            var loadT = bt.load();
            bt.site.get_site_security(web.id, web.name, function (rdata) {
                loadT.close();
                if (rdata.status === false) {
                    bt.msg(rdata);
                    return;
                }
                var robj = $('#webedit-con');
                var datas = [
                    { title: 'URL后缀', name: 'sec_fix', value: rdata.fix, disabled: rdata.status, width: '360px' },
                    { title: '许可域名', name: 'sec_domains', value: rdata.domains, disabled: rdata.status, width: '360px' },

                    {
                        title: ' ', class: 'label-input-group', items: [
                            {
                                text: '启用防盗链', name: 'status', value: rdata.status, type: 'checkbox', callback: function (sdata) {
                                    bt.site.set_site_security(web.id, web.name, sdata.sec_fix, sdata.sec_domains, sdata.status, function (ret) {
                                        if (ret.status) site.reload(12)
                                        bt.msg(ret);
                                    })
                                }
                            }
                        ]
                    }
                ]
                for (var i = 0; i < datas.length; i++) {
                    var _form_data = bt.render_form_line(datas[i]);
                    robj.append(_form_data.html);
                    bt.render_clicks(_form_data.clicks);
                }
                var helps = ['默认允许资源被直接访问,即不限制HTTP_REFERER为空的请求', '多个URL后缀与域名请使用逗号(,)隔开,如: png,jpeg,zip,js', '当触发防盗链时,将直接返回404状态']
                robj.append(bt.render_help(helps));
            })
        },
        set_tomact: function (web) {
            bt.site.get_site_phpversion(web.name, function (rdata) {
                var robj = $('#webedit-con');
                if (!rdata.tomcatversion) {
                    robj.html('<font>' + lan.site.tomcat_err_msg1 + '</font>');
                    layer.msg(lan.site.tomcat_err_msg, { icon: 2 });
                    return;
                }
                var data = {
                    class: 'label-input-group', items: [{
                        text: lan.site.enable_tomcat, name: 'tomcat', value: rdata.tomcat == -1 ? false : true, type: 'checkbox', callback: function (sdata) {
                            bt.site.set_tomcat(web.name, function (ret) {
                                if (ret.status) site.reload(9)
                                bt.msg(ret);
                            })
                        }
                    }]
                }
                var _form_data = bt.render_form_line(data);
                robj.append(_form_data.html);
                bt.render_clicks(_form_data.clicks);
                var helps = [lan.site.tomcat_help1 + ' ' + rdata.tomcatversion + ',' + lan.site.tomcat_help2, lan.site.tomcat_help3, lan.site.tomcat_help4, lan.site.tomcat_help5]
                robj.append(bt.render_help(helps));
            })
        },
        get_site_logs: function (web) {
            bt.site.get_site_logs(web.name, function (rdata) {
                var robj = $('#webedit-con'), _logs = '';
                if (rdata.path != '' && rdata.path != undefined) {
                    _logs += '<div style="margin-bottom: 5px; position: relative; height:30px;line-height:30px;">日志路径：<a class="btlink" title="打开目录" href="javascript:openPath(\'' + rdata.path + '\');">' + rdata.path + '</a>'
                    if (bt.get_cookie('serverType') == 'iis') {
                        _logs += '<button style="position: absolute;right:0" onclick="site.edit.check_log_time()" class ="btn btn-success btn-sm btn-title">校对IIS日志时间</button>'
                    }
                    _logs += "</div>"
                    robj.append(_logs)
                }                
                var logs = { class: 'bt-logs', items: [{ name: 'site_logs', height: '530px', value: rdata.msg, width: '100%', type: 'textarea' }] }
                var _form_data = bt.render_form_line(logs);
                robj.append(_form_data.html);
                bt.render_clicks(_form_data.clicks);
                $('textarea[name="site_logs"]').attr('readonly', true);
            })
        },
        check_log_time: function () {
            bt.confirm({ msg: "是否立即校对IIS日志时间，校对后日志统一使用北京时间记录？", title: '提示' }, function () {
                var loading = bt.load()
                bt.send("check_log_time", 'site/check_log_time', {  }, function (rdata) {
                    loading.close();
                    if (rdata.status) {
                        site.reload();
                    }
                    bt.msg(rdata);
                })
            })
        }
    },
    create_let: function (ddata, callback) {
        bt.site.create_let(ddata, function (ret) {
            if (ret.status) {
                if (callback) {
                    callback(ret);
                }
                else {
                    site.ssl.reload(1);
                    bt.msg(ret);
                    return;
                }
            } else {
                if (!ret.out) {
                    bt.msg(ret);
                    return;
                }
                var data = "<p>" + ret.msg + "</p><hr />"
                if (ret.err[0].length > 10) data += '<p style="color:red;">' + ret.err[0].replace(/\n/g, '<br>') + '</p>';
                if (ret.err[1].length > 10) data += '<p style="color:red;">' + ret.err[1].replace(/\n/g, '<br>') + '</p>';

                layer.msg(data, { icon: 2, area: '500px', time: 0, shade: 0.3, shadeClose: true });
            }
        })
    },
    upload_pfx: function ()
    {
        var path = setup_path + "/temp/ssl/";
        bt_upload_file.open(path, ".pfx", ' <span style="color:red;">请上传pfx文件</span>', function (path) {
            site.reload();
        });
        return;

        var path = setup_path + "/temp/ssl/";
        var index = layer.open({
            type: 1,
            closeBtn: 2,
            title: '上传IIS证书文件 --- <span style="color:red;">请上传pfx文件</span>',
            area: ['500px', '500px'],
            shadeClose: false,
            content: '<div class="fileUploadDiv">\
                            <input type="hidden" id="input-val" value="' + path + '" />\
				            <input type="file" id="file_input" multiple="true" autocomplete="off" />\
				            <button type="button"  id="opt" autocomplete="off">添加文件</button>\
				            <button type="button" id="up" autocomplete="off" >开始上传</button>\
				            <span id="totalProgress" style="position: absolute;top: 7px;right: 147px;"></span>\
                            <input type="hidden" id ="fileCodeing" value ="utf-8" />\
				            <button type="button" id="filesClose" autocomplete="off">关闭</button>\
				            <ul id="up_box"></ul>\
                        </div>'
        });
        $("#filesClose").click(function () {
            layer.close(index);
            site.reload();
            setTimeout(site.ssl.reload(),200)
        });
        UploadStart(false);
    },
    reload: function (index) {
        if (index == undefined) index = 0 
       
        var _sel = $('.site-menu p.bgw');
        if (_sel.length == 0)  _sel = $('.site-menu p:eq(0)');           
        _sel.trigger('click');
    },
    //拆分多个配置
    set_iis_multiple: function (siteName) {
     
        bt.confirm({ msg: "是否确定执行自动解析？", title: '提示' }, function () {
               var loading = bt.load()
            bt.send("set_iis_multiple", 'site/set_iis_multiple', { siteName: siteName }, function (rdata) {
                loading.close();
                if (rdata.status) {
                    site.reload();
                }
                bt.msg(rdata);
            })
        })
       
    },
    plugin_firewall: function () {
        var typename = bt.get_cookie('serverType');
        var name = 'btwaf_httpd';
        if (typename == "nginx") name = 'btwaf'

        bt.plugin.get_plugin_byhtml(name, function (rhtml) {
            if (rhtml.status === false) return;

            var list = rhtml.split('<script type="javascript/text">');
            if (list.length > 1) {
                rcode = rhtml.split('<script type="javascript/text">')[1].replace("<\/script>", "");
            }
            else {
                list = rhtml.split('<script type="text/javascript">');
                rcode = rhtml.split('<script type="text/javascript">')[1].replace("<\/script>", "");
            }
            rcss = rhtml.split('<style>')[1].split('</style>')[0];
            $("body").append('<div style="display:none"><style>' + rcss + '</style><script type="javascript/text">' + rcode + '<\/script></div>');
            setTimeout(function () {
                if (!!(window.attachEvent && !window.opera)) {
                    execScript(rcode);
                } else {
                    window.eval(rcode);
                }
            }, 200)
        })
    },
    web_edit: function (obj) {
        var _this = this;
        var item = $(obj).parents('tr').data('item');
        bt.open({
            type: 1,
            area: ['700px', '700px'],
            title: lan.site.website_change + '[' + item.name + ']  --  ' + lan.site.addtime + '[' + item.addtime + ']',
            closeBtn: 2,
            shift: 0,
            content: "<div class='bt-form'><div class='bt-w-menu site-menu pull-left' style='height: 100%;'></div><div id='webedit-con' class='bt-w-con webedit-con pd15'></div></div>"
        })
        setTimeout(function () {
            var menus = [
                { title: '域名管理', callback: site.edit.set_domains },
                { title: '子目录绑定', callback: site.edit.set_dirbind },
                { title: '网站目录', callback: site.edit.set_dirpath },
                { title: '目录保护', callback: site.edit.set_dirguard },
                { title: '应用程序池',os : 'Windows', callback: site.edit.set_apppool },
                { title: '错误页', os: 'Windows', callback: site.edit.set_error_page },
                { title: '流量限制', callback: site.edit.limit_network },
                { title: '伪静态', callback: site.edit.get_rewrite_list },
                { title: '默认文档', callback: site.edit.set_default_index },
                { title: '配置文件', callback: site.edit.set_config },
                { title: 'SSL', callback: site.edit.set_ssl },
                { title: 'PHP版本', callback: site.edit.set_php_version },
                { title: 'Tomact',os:'Linux',callback: site.edit.set_tomact },
                { title: '重定向', callback: site.edit.set_301 },                
                { title: '反向代理', callback: site.edit.set_proxy },
                { title: '防盗链', callback: site.edit.set_security },
                { title: '响应日志', callback: site.edit.get_site_logs }
            ]
            for (var i = 0; i < menus.length; i++) {
                var men = menus[i];
                if (men.os == undefined || men.os == bt.os) {
                    var _p = $('<p>' + men.title + '</p>');
                    _p.data('callback', men.callback);
                    $('.site-menu').append(_p);
                }        
            }
            $('.site-menu p').click(function () {
                $('#webedit-con').html('');
                $(this).addClass('bgw').siblings().removeClass('bgw');
                var callback = $(this).data('callback')
                if (callback) callback(item);
            })
            site.reload(0);
        }, 100)
    }
}
site.get_types();