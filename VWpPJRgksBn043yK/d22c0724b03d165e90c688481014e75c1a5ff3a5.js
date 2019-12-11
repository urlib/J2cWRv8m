var crontab = {
    init: function ()
    {
        crontab.get_lib_list("sites", function (lib_data) {
            var arrs = [{ name: '服务器磁盘', title: '服务器磁盘', value: 'localhost' }]
            for (var i = 0; i < lib_data.orderOpt.length; i++) {
                var item = lib_data.orderOpt[i]
                item.title = item.name;
                arrs.push(item);
            }
            crontab.libs = arrs
            crontab.get_list();
        })

        _form_data = crontab.get_form_data();
        _form_data.push(crontab.data.save_btn)

        $(".crontab_body").empty();
        var clicks = []
        for (var i = 0; i < _form_data.length; i++) {
            var html = bt.render_form_line(_form_data[i])
            $(".crontab_body").append(html.html);
            clicks = clicks.concat(html.clicks);
        }
        bt.render_clicks(clicks);
        $(".crontab_body .type").trigger("change");
     
        $('.crontab_body').append("<div class='crontab_help'>" + bt.render_help(['当添加完备份任务，应该手动运行一次，并检查备份包是否完整', '磁盘容量不够、数据库密码错误、网络不稳定等原因，可能导致数据备份不完整']) + "</div>")
    },
    get_list: function (page, search) {
        if (page == undefined) page = 1;
        bt.crontab.get_list(page, search, function (rdata) {
            var _tab = bt.render({
                table: '#cronbody',
                columns: [
                    { field: 'id', type: 'checkbox', width: 30 },
                    {
                        field: 'name', title: "任务名称"
                    },
                    {
                        field: 'status', title: "状态", templet: function (item) {
                            var _status = '<a href="javascript:;" ';
                            if (item.status == '1') {
                                _status += ' onclick="crontab.set_crontab_status(this)" >';
                                _status += '<span style="color:#5CB85C">正常 </span><span style="color:#5CB85C" class="glyphicon glyphicon-play"></span>';
                            }
                            else {
                                _status += ' onclick="crontab.set_crontab_status(this)"';
                                _status += '<span style="color:red">已停止  </span><span style="color:red" class="glyphicon glyphicon-pause"></span>';
                            }
                            return _status;
                        }
                    },
                    {
                        field: 'tType', title: "周期"
                    },
                    {
                        field: 'cycle', title: "执行时机"
                    },
                    {
                        field: 'save', title: "保存数量", templet: function (item) {
                            return (item.save ? item.save + '份' : '-')
                        }
                    },
                    {
                        field: 'backupTo', title: "备份到", templet: function (item) {
                            var optName = '--';
                            if (item.backupTo == "localhost") {
                                if (item.sType == 'site' || item.sType == 'database' || item.sType == 'path') {
                                    optName = '本地磁盘';
                                }                                
                            }
                            else {
                                for (var i = 0; i < crontab.libs.length; i++) {                                 
                                    if (crontab.libs[i].value == item.backupTo) {
                                        optName = crontab.libs[i].name;
                                        break;
                                    }
                                }
                            }
                            return optName;
                        }
                    },
                    {
                        field: 'addtime', title: "添加时间"
                    },
                    {
                        field: 'opt', title: "操作", width: "190px", templet: function (item) {
                            var opt = '<a href="javascript:;" onclick="crontab.start_task_send(this)" class="btlink">执行</a> | <a href="javascript:;" onclick="crontab.edit_crontab_data(this)" class="btlink ">编辑</a> | <a href="javascript:;" onclick="crontab.get_logs_crontab(this)" class="btlink">日志</a>  | <a href="javascript:;" onclick="crontab.del_task_send(this)" class="btlink">删除</a>'
                            return opt;
                        }
                    },
                ],
                data: rdata
            })
        })
    },
    get_edit_obj: function () {
        var robj = $('.edit_crontab');
        if (robj.length > 0) {
            return robj
        }
        else {
            return $(".crontab_body")
        }
    },
    get_lib_list: function (type, callback) {
        bt.send("GetDataList", "crontab/GetDataList", { type: type }, function (rdata) {
            if (callback) callback(rdata)
        })
    },
    start_task_send: function (obj) {
        var data = $(obj).parents('tr').data('item');

        bt.crontab.start_task_send(data, function (rdata) {
            bt.msg(rdata);
        })
    },
    get_logs_crontab: function (obj) {
        var data = $(obj).parents('tr').data('item');

        bt.crontab.get_logs_crontab(data, function (rdata) {
            if (!rdata.status) {
                bt.msg(rdata);
                return;
            };
            layer.open({
                type: 1,
                title: lan.crontab.task_log_title,
                area: ['700px', '490px'],
                shadeClose: false,
                closeBtn: 2,
                content: '<div class="setchmod bt-form  pb70">'
                    + '<pre class="crontab-log" style="overflow: auto; border: 0px none; line-height:23px;padding: 15px; margin: 0px; white-space: pre-wrap; height: 405px; background-color: rgb(51,51,51);color:#f1f1f1;border-radius:0px;font-family: \"微软雅黑\"">' + (rdata.msg == '' ? '当前日志为空' : rdata.msg) + '</pre>'
                    + '<div class="bt-form-submit-btn" style="margin-top: 0px;">'
                    + '<button type="button" class="btn btn-danger btn-sm btn-title clear_logs_crontab" style="margin-right:15px;" >' + lan.public.empty + '</button>'
                    + '<button type="button" class="btn btn-success btn-sm btn-title" onclick="layer.closeAll()">' + lan.public.close + '</button>'
                    + '</div>'
                    + '</div>'
            });
            setTimeout(function () {
                $("#crontab-log").text(rdata.msg);
                var div = document.getElementsByClassName('crontab-log')[0]
                div.scrollTop = div.scrollHeight;

                $(".clear_logs_crontab").click(function () {
                    bt.crontab.del_logs_crontab(data, function (sdata) {
                        layer.closeAll();
                        bt.msg(sdata);
                    })
                })
            }, 200)
        })
    },

    del_task_send: function (obj) {
        var data = $(obj).parents('tr').data('item');
        bt.show_confirm('删除[' + data.name + ']', '您确定要删除该任务吗?', function () {
            bt.crontab.del_task_send(data, function (rdata) {
                layer.closeAll();
                rdata.time = 2000;
                crontab.get_list();
                bt.msg(rdata);
            });
        });
    },
    batch_crontab: function (type, obj, result) {
        if (obj == undefined) {
            obj = {};
            var arr = [];
            result = { count: 0, error_list: [] };
            $('input[type="checkbox"].check:checked').each(function () {
                var _val = $(this).val();
                if (!isNaN(_val)) arr.push($(this).parents('tr').data('item'));
            })

            bt.show_confirm(lan.crontab.del_task_all_title, "<a style='color:red;'>" + lan.get('del_all_task', [arr.length]) + "</a>", function () {
                obj.data = arr;
                bt.closeAll();
                crontab.batch_crontab(type, obj, result);
            });

            return;
        }
        var item = obj.data[0];
        switch (type) {
            case 'del':
                if (obj.data.length < 1) {
                    crontab.get_list();
                    bt.msg({ msg: lan.get('del_all_task_ok', [result.count]), icon: 1, time: 5000 });
                    return;
                }
                bt.crontab.del_task_send(item, function (rdata) {
                    if (rdata.status) {
                        result.count += 1;
                    } else {
                        result.error_list.push({ name: item.item, err_msg: rdata.msg });
                    }
                    obj.data.splice(0, 1)
                    crontab.batch_crontab(type, obj, result);
                })
                break;

        }
    },
    set_crontab_status: function (obj) {
        var data = $(obj).parents('tr').data('item');
        bt.confirm({ title: '提示', msg: data.status ? '计划任务暂停后将无法继续运行，您真的要停用这个计划任务吗？' : '该计划任务已停用，是否要启用这个计划任务？' }, function () {
            bt.crontab.set_crontab_status(data, function (rdata) {
                layer.closeAll();
                crontab.get_list();
                bt.msg(rdata);
            });
        });
    },
    get_form_data: function () {

        var _form_data = [
            {
                title: '任务类型', type: 'select', name: 'sType', items: [
                    { title: 'Shell脚本', value: 'toShell' },
                    { title: '备份网站', value: 'site' },
                    { title: '备份数据库', value: 'database' },
                    { title: '日志切割', value: 'logs' },
                    { title: '备份目录', value: 'path' },
                    { title: '释放内存', value: 'rememory' },
                    { title: '访问URL', value: 'toUrl' },
                ], ps: '<i style="color:red">*&nbsp;&nbsp;</i>任务类型包含以下部分：Shell脚本、备份网站、备份数据库、日志切割、释放内存、访问URL',
                callback: function (obj) {
                    if (obj.val() == "logs") {
                        if (bt.os == "Windows") {               
                            bt.msg({ msg: "Windows暂不支持此功能!", status: false });
                            obj.val("toShell")
                        }
                    }

                    var robj = crontab.get_edit_obj().find(".shell_sbody");
                    robj.children().remove();

                    crontab.get_backto_data(obj.val(), function (form_data) {
                        var nobj = bt.render_form_line(form_data);

                        var _html = $(nobj.html)
                        robj.append(_html.children())
                        bt.render_clicks(nobj.clicks)
                    })
                }
            },
            {
                title: '任务名称', name: 'name'
            },
            {
                title: '执行周期', class: 'run_cycle', items: [
                    {
                        name: 'type', type: 'select', items: [
                            { title: '每天', value: 'day' },
                            { title: 'N天', value: 'day-n' },
                            { title: '每小时', value: 'hour' },
                            { title: 'N小时', value: 'hour-n' },
                            { title: 'N分钟', value: 'minute-n' },
                            { title: '每星期', value: 'week' },
                            { title: '每月', value: 'month' },
                        ]
                        , callback: function (obj) {
                            obj.nextAll().remove();
                            var _sel_data = { items: [crontab.data.week_data, crontab.data.hour_data, crontab.data.minute_data] }
                            switch (obj.val()) {
                                case "hour":
                                    _sel_data = { items: [crontab.data.minute_data] }
                                    break;
                                case "hour-n":
                                    _sel_data = { items: [crontab.data.hour_data, crontab.data.minute_data] }
                                    break;
                                case "day-n":
                                    _sel_data = { items: [crontab.data.day_n_data, crontab.data.hour_data, crontab.data.minute_data] }
                                    break;
                                case "day":
                                    _sel_data = { items: [crontab.data.hour_data, crontab.data.minute_data] }
                                    break;
                                case "month":
                                    _sel_data = { items: [crontab.data.day_data, crontab.data.hour_data, crontab.data.minute_data] }
                                    break;
                                case "minute-n":
                                    _sel_data = { items: [crontab.data.minute_data] }
                                    break;
                                default:
                                    _sel_data = { items: [crontab.data.week_data, crontab.data.hour_data, crontab.data.minute_data] }
                                    break;
                            }
                            var robj = bt.render_form_line(_sel_data);
                            var _html = $(robj.html)
                            obj.parent().append(_html.find(".info-r").children())

                            bt.render_clicks(robj.clicks)
                        }
                    }
                ]
            },
            {
                title: '脚本内容', class: 'shell_sbody', type: 'textarea', name: 'sBody', height: "150px", width: "400px"
            }
        ]
        return _form_data;
    },
    edit_crontab_data: function (obj) {
        var data = $(obj).parents('tr').data('item');

        var _list = crontab.get_form_data(data);
        var _data = crontab.data.save_btn;
        _data.text = "保存编辑";

        _list.push(_data);
        _list.push({ type: 'input', name: 'id', hide: true, value: data.id })
        var _form = {
            title: '编辑计划任务-[' + data.name + ']',
            area: ['800px', '400px'],
            skin: 'edit_crontab',
            list: _list,
            btns: []
        }
        var _bs = bt.render_form(_form, function () {

        })       
        $(".edit_crontab .bt-form-submit-btn").remove()

        setTimeout(function () {          
            //模拟触发事件
            $(".sType" + _bs).attr("disabled", true).val(data.sType).trigger("change")
            $(".type" + _bs).val(data.type).trigger("change")
            $(".name" + _bs).val(data.name)

            //延迟赋值
            setTimeout(function () {      
                //备份
                $(".edit_crontab .sName").attr("disabled", true).val(data.sName)
                $(".edit_crontab .backupTo").val(data.backupTo);
                $(".edit_crontab .save").val(data.save);

                //周期
                $(".edit_crontab .week").val(data.where1);
                $(".edit_crontab .hour").val(data.where_hour);
                $(".edit_crontab .minute").val(data.where_minute);

                $(".edit_crontab .urladdress").val(data.urladdress);
                $(".edit_crontab .sBody").val(data.sBody);

            }, 200)
        }, 200)       
    },
    get_backto_data: function (type,callback)
    {
        crontab.get_edit_obj().find(".name").attr("disabled", false).val("");

        var keys = { path: '备份目录', site: '备份网站', database: '备份数据库', rememory: '提示', logs: '切割网站', toUrl:'URL地址' }
        var title = "脚本内容"
        if (keys[type]) title = keys[type];

        if (type == "logs") type = "site"
        
        if (type == "site" || type == "database") {
            type = type + 's';
            crontab.get_lib_list(type, function (rdata) {
                if (rdata.data.length <= 0) {
                    $('.sType').val('toShell').trigger("change");
                    bt.msg({ status: false, msg: '暂无可用数据，请先添加.' });                    
                    return;
                }               

                crontab[type] = [{ title: '所有', value: 'all' }]
                for (var i = 0; i < rdata.data.length; i++) crontab[type].push({ title: rdata.data[i].name + '[' + rdata.data[i].ps + ']', value: rdata.data[i].name })

                var _sel_data = {
                    title: title, class: 'shell_sbody', items: [
                        {
                            name: 'sName', width: "200px", value: (rdata.data.length > 0 ? rdata.data[0].name : ''), type: 'select', items: crontab[type], callback: function (obj) {
                                crontab.get_edit_obj().find(".name").val(title + "[" + obj.val() + "]")
                            }
                        },
                        { title: '备份到', name: "backupTo", type: "select", items: crontab.libs },
                        { title: '保留最新', width: "50px", name: "save", type: "number", value: 3, unit: "份" }
                    ]
                }
                crontab.get_edit_obj().find(".name").attr("disabled", true).val(title + "[" + rdata.data[0].name + "]");

                callback(_sel_data)
            })
        }
        else {          
            if (type == "rememory") {
                callback({ title: title, class: 'shell_sbody', type: 'span', name: 'smsg', value: "释放PHP、MYSQL、PURE-FTPD、APACHE、NGINX的内存占用,建议在每天半夜执行!"})
            }
            else if (type=="path") {
                var _sel_data = {
                    title: title, class: 'shell_sbody', items: [
                        { name: 'sName', width: "200px", value: bt.get_cookie("sites_path"), event: { css: 'glyphicon-folder-open', callback: function (obj) { bt.select_path(obj); } } },
                        { title: '备份到', name: "backupTo", type: "select", items: crontab.libs },
                        { title: '保留最新', width: "50px", name: "save", type: "number", value: 3, unit: "份" }
                    ]
                }
                callback(_sel_data)
            }
            else if (type == "toUrl") {
                callback({ title: title, class: 'shell_sbody', type: 'input', name: 'urladdress', value:"http://", width: "400px" })
            }
            else {
                callback({ title: title, class: 'shell_sbody', type: 'textarea', name: 'sBody', height: "150px", width: "400px" })
            }
        }     
    },
    libs: [],
    sites: [],
    databases:[],
    data: {
        day_n_data: {
            name: 'where1', type: 'number', width: "50px", unit: '天', value: 3, callback: function (obj) {
                var reg = /^[1-9]\d*$/;
                if (!reg.test(obj.val())) {
                    obj.val(1);
                }
            }
        },
        day_data: {
            name: 'where1', type: 'number', width: "50px", unit: '日', value: 3, callback: function (obj) {
                var reg = /^[1-9]\d*$/;
                if (reg.test(obj.val())) {
                    if (parseInt(obj.val()) > 31) {
                        obj.val(31)
                    }
                }
                else {
                    obj.val(1);
                }
            }
        },
        hour_data: {
            name: 'hour', type: 'number', width: "50px", unit: '小时', value: 1, callback: function (obj) {
                var reg = /^[0-9]\d*$/;
                if (reg.test(obj.val())) {
                    if (parseInt(obj.val()) > 23) {
                        obj.val(23)
                    }
                }
                else {
                    obj.val(1);
                }
            }
        },
        minute_data: {
            name: 'minute', type: 'number', width: "50px", unit: '分钟', value: 30, callback: function (obj) {
                var reg = /^[1-9]\d*$/;
                if (reg.test(obj.val())) {
                    if (parseInt(obj.val()) > 59) {
                        obj.val(59)
                    }
                }
                else {
                    obj.val(1);
                }
            }
        },
        week_data: {
            name: 'where1', type: 'select', items: [
                { title: '周一', value: '1' },
                { title: '周二', value: '2' },
                { title: '周三', value: '3' },
                { title: '周四', value: '4' },
                { title: '周五', value: '5' },
                { title: '周六', value: '6' },
                { title: '周日', value: '7' },
            ]
        },
        save_btn: {
            text: '添加任务', class: 'crontab_add', type: 'button', name: 'btn_save', width: "200px", callback: function (sdata) {
                var loading = bt.load();
                var default_arrs = ["sBody", "sName", "save", ""]
                for (var i = 0; i < default_arrs.length; i++) sdata[default_arrs[i]] = sdata[default_arrs[i]] == undefined ? "" : sdata[default_arrs[i]];
                
                sdata['backupTo'] = sdata['backupTo'] == undefined ? "localhost" : sdata['backupTo'];
                if (sdata.type == 'week') sdata[sdata.type] = sdata.where1;
                if (sdata.type == 'minute-n') sdata['where1'] = sdata['minute'];
                if (sdata.type == 'hour-n') sdata['where1'] = sdata['hour'];

                if (sdata['id'] == undefined) {
                    bt.send("AddCrontab", "crontab/AddCrontab", sdata, function (rdata) {
                        loading.close();
                        layer.closeAll();
                        if (rdata.status) {
                            crontab.get_list();
                        }
                        bt.msg(rdata)
                    })
                }
                else {
                    bt.send("modify_crond", "crontab/modify_crond", sdata, function (rdata) {
                        loading.close();
                        layer.closeAll();
                        if (rdata.status) {
                            crontab.get_list();
                        }
                        bt.msg(rdata)
                    })
                }
            }
        }
    }
}
crontab.init();