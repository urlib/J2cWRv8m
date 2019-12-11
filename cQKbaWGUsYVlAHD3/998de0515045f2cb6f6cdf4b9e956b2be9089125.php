<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: mydisk.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

include "includes/commons.inc.php";

phpdisk_core::user_login();

define('IN_MYDISK' ,true);

// fix firefox
if($item =='upload'){
	$uid = (int)gpc('uid','GP',0);
	$pd_is_activated = @$db->result_first("select is_activated from {$tpf}users where userid='$uid'");
}
/*if($settings['user_active'] && $pd_is_activated<>1){
	echo '<script>alert("'.__('account_not_actived').'");document.location="./";</script>';
	exit;
}*/
$menu = trim(gpc('menu','G',''));
$menu = $menu ? $menu : 'file';
$item = $item ? $item : 'files';

if($menu =='file'){

	// root my folders
	$arr = my_folder_root();
	$tmp = $arr[file_count] ? __('all_file')."{$arr[file_count]} , ".__('folder_size').get_size($arr[folder_size]) : '';
	$folder_list = "tr.add(0,-1,'".__('mydisk_cp_manage')."','".urr("mydisk","item=files&action=index")."','{$tmp}');".LF;
	// my other folders
	$arr = my_folder_menu();
	foreach($arr as $v){
		$folder_list .= "tr.add({$v['folder_id']},{$v['parent_id']},'{$v['folder_name']}','".urr("mydisk","item=files&action=index&folder_id={$v['folder_id']}")."','{$v[count]}');".LF;
	}

}elseif($menu =='folder'){
	$tmp = (int)@$db->result_first("select sum(file_size) from {$tpf}files where in_recycle=0 and userid='$pd_uid'");
	$total_space = get_size($tmp);
	$file_count = (int)@$db->result_first("select count(*) from {$tpf}files where in_recycle=0 and userid='$pd_uid'");
	$folder_count = (int)@$db->result_first("select count(*) from {$tpf}folders where in_recycle=0 and userid='$pd_uid'");

}elseif($menu =='public'){

	$arr = public_menu_list();
	$public_folder_tree = "tr.add(0,-1,'".__('public_file_manage')."','###');".LF;
	foreach($arr as $v){
		$public_folder_tree .= "tr.add({$v['cate_id']},{$v['pid']},'{$v['cate_name']}','".urr("mydisk","item=public&menu=public&action=index&pid={$v['pid']}&id={$v['cate_id']}")."','".$v[num]."');".LF;
	}

	$my_file_store = @$db->result_first("select sum(file_size) from {$tpf}files where is_public=1 and cate_id>0 and userid='$pd_uid'");

	$file_count = @$db->result_first("select count(*) from {$tpf}files where is_public=1 and cate_id>0 and userid='$pd_uid'");
	$total_space = get_size($my_file_store);

}elseif($menu =='recycle'){
	$tmp = (int)@$db->result_first("select sum(file_size) from {$tpf}files where in_recycle=1 and userid='$pd_uid'");
	$total_space = get_size($tmp);
	$file_count = (int)@$db->result_first("select count(*) from {$tpf}files where in_recycle=1 and userid='$pd_uid'");
	$folder_count = (int)@$db->result_first("select count(*) from {$tpf}folders where in_recycle=1 and userid='$pd_uid'");

}elseif($menu == 'profile'){
	$num = @$db->result_first("select count(*) as total from {$tpf}messages where touserid='$pd_uid' and is_new=1");
	$new_msg = $num ? '<span class="txtred" title="'.__('new_msg').'">('.$num.')</span>' : '';
}

if($item =='folders' && $action !='index'){
	$inner_box = true;
}
if($item == 'upload'){
	$inner_box = true;
}
if($item == 'files' && in_array($action,array('file_modify','file_delete','view_extract_file','unshare_file','short_url'))){
	$inner_box = true;
}
if($item =='share'){
	$inner_box = true;
}
if($item =='recycle' && in_array($action,array('show_files','folder_delete_complete','file_delete_complete','folder_restore','file_restore'))){
	$inner_box = true;
}
if($item =='public' && in_array($action, array('file_modify','file_delete'))){
	$inner_box = true;
}
if($item =='message' && in_array($action,array('sendmsg','view','reply'))){
	$inner_box = true;
}
if($item =='buddy' && in_array($action,array('addbuddy','delbuddy','s_addbuddy'))){
	$inner_box = true;
}
if($inner_box){
	require_once template_echo('my_header',$user_tpl_dir);
	require_once PHPDISK_ROOT."modules/".$item.".inc.php";
	require_once template_echo('my_footer',$user_tpl_dir);
}else{
	require_once template_echo('my_header',$user_tpl_dir);

	$items = array('files','folders','upload','profile','main','recycle','share','stats','public','message','buddy','disk');
	if(in_array($item,$items)){
		$action_module = PHPDISK_ROOT.'modules/'.$item.'.inc.php';
	}else{
		echo "Error operation, system halt!";
	}
	$site_stat = $settings['site_stat'] ? '&nbsp;'.stripslashes(base64_decode($settings['site_stat'])) : '';
	$debug_info = $settings['debug_info'] ? '' : 'none';

	$pageinfo = page_end_time();

	require_once template_echo("mydisk",$user_tpl_dir);
	require_once template_echo('my_footer',$user_tpl_dir);
}

include PHPDISK_ROOT."./includes/footer.inc.php";

?>


