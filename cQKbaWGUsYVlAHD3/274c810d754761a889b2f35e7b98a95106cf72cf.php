<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: downfile.php 29 2014-02-10 01:43:18Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

include "includes/commons.inc.php";

@set_time_limit(0);
@ignore_user_abort(true);
@set_magic_quotes_runtime(0);
@session_write_close(); 
$file_id = (int)gpc('file_id','G',0);

$rs = $db->fetch_one_array("select * from {$tpf}files where file_id='$file_id'");
if($rs){

	if($settings['login_down_file'] && !$pd_uid && $rs['userid']){
		alert(__('file_login_down'),urr("account","action=login"));
	}
	if(!$rs['is_checked'] && $pd_gid<>1){
		alert(__('file_checking'),$_SERVER['HTTP_REFERER']);
	}
	if(!$rs['in_share'] && ($pd_uid != $rs['userid'])){
		alert(__('not_share_msg'),$_SERVER['HTTP_REFERER']);
	}

	$file_id = $rs['file_id'];
	$userid = $rs['userid'];
	$file_real_name = $rs['file_real_name'];
	$file_name_short = $rs['file_name'];
	$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
	$file_name = $rs['file_name'].$tmp_ext;
	$file_credit = (int)$rs['file_credit'];

	$file_extension = $rs['file_extension'];
	$file_ext = get_real_ext($file_extension);
	$file_mime = $rs['file_mime'];
	$file_size = $rs['file_size'];
	$thumb_size = $rs['thumb_size'];
	$file_store_path = $rs['file_store_path'];
	$is_locked = $rs['is_locked'];
	$store_old = $rs['store_old'];
	if(is_utf8()){
		$file_real_name = convert_str('utf-8','gbk',$file_real_name);
	}
	$file_location = $settings['file_path'].'/'.$file_store_path.'/'.$file_real_name.$file_ext;

	if(!file_exists(PHPDISK_ROOT.$file_location)){
		$file_not_found = 1;
	}
}
if($file_not_found){
	alert(__('file_not_found'),$_SERVER['HTTP_REFERER']);
}
if($is_locked){
	alert(__('file_locked'),$_SERVER['HTTP_REFERER']);
}

$filter_arr = explode(',',$settings['filter_extension']);

if(is_utf8()){
	$file_name = convert_str('utf-8','gbk',$file_name);
}

$file_name = str_replace("+", "%20",$file_name);
ob_end_clean();
$ua = $_SERVER["HTTP_USER_AGENT"];
if($action == 'view'){
		header('Content-disposition: inline;filename="'.$file_name.'"');
}else{
		header('Content-disposition: attachment;filename="'.$file_name.'"');
}
header('Content-type: application/octet-stream');
header('Content-Encoding: none');
header('Content-Transfer-Encoding: binary');
header('Content-length: '.$file_size);
@readfile($file_location);
//include PHPDISK_ROOT."./includes/footer.inc.php";

function alert($msg,$url){
	echo "<script>alert('$msg');document.location='$url';</script>";
	exit;
}
?>

