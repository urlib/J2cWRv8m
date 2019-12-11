<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: index.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/
include "includes/commons.inc.php";

$in_front = true;

$title = $settings['site_title'];
include PHPDISK_ROOT."./includes/header.inc.php";

if($pd_uid){
	$mystats = my_stats($pd_uid);
	$myinfo = get_mydisk_info($pd_uid);
}
$last = index_last();
$C[announce_arr] = get_announce_list();
$C[gallery_arr] = get_index_galley();

$C[last_file] = get_last_file();
$C[hot_file] = get_hot_file();

$C[links_arr] = get_friend_link();
main_stats();
$last_users = get_last_user_list();

require_once template_echo('phpdisk',$user_tpl_dir);

include PHPDISK_ROOT."./includes/footer.inc.php";

function get_announce_list(){
	global $db,$tpf;
	$q = $db->query("select subject,annid,in_time from {$tpf}announces where is_hidden=0 order by show_order asc,annid desc");
	$anns = array();
	while($rs = $db->fetch_array($q)){
		$rs['subject'] = htmlspecialchars_decode($rs['subject']);
		$rs[href] = urr("announce","aid=".$rs[annid]);
		$rs[in_time] = date("Y-m-d",$rs['in_time']);
		$anns[] = $rs;
	}
	$db->free($q);
	unset($rs);
	return $anns;
}
function get_friend_link(){
	global $db,$tpf;
	$q = $db->query("select * from {$tpf}links where is_hidden=0 order by logo desc,show_order asc,linkid desc");
	$arr = array();
	while($rs = $db->fetch_array($q)){
		$rs['has_logo'] = $rs['logo'] ? 1 : 0;
		$arr[] = $rs;
	}
	$db->free($q);
	unset($rs);
	return $arr;
}

function get_index_galley(){
	global $db,$tpf,$settings;
	$settings['gallery_type'] = $settings['gallery_type'] ? $settings['gallery_type'] : 1;
	$q = $db->query("select * from {$tpf}gallery order by show_order asc, gal_id asc");
	$arr = array();
	while($rs = $db->fetch_array($q)){
		$arr[] = $rs;
	}
	$db->free($q);
	unset($rs);
	return $arr;
}
function index_last(){
	global $db,$tpf;
	$username = @$db->result_first("select username from {$tpf}users order by userid desc limit 1");
	$arr['username'] = $username;
	$arr['a_last_user'] = urr("space","username=".rawurlencode($username));
	return $arr;
}
function my_stats($pd_uid){
	global $db,$tpf;
	$stats['total_folders'] = (int)@$db->result_first("select count(*) from {$tpf}folders where userid='$pd_uid' and in_recycle=0");
	$stats['total_share_files'] = @$db->result_first("select count(*) from {$tpf}files where userid='$pd_uid' and in_share=1 and in_recycle=0");
	$stats['total_files'] = (int)@$db->result_first("select count(*) from {$tpf}files where userid='$pd_uid' and in_recycle=0");
	$stats['file_size_total'] = get_size(@$db->result_first("select sum(file_size) from {$tpf}files where userid='$pd_uid' and in_recycle=0"));
	$stats['last_login_ip'] = @$db->result_first("select last_login_ip from {$tpf}users where userid='$pd_uid'");
	return $stats;
}
function get_hot_tags(){
	global $db,$tpf;
	$q = $db->query("select * from {$tpf}tags where is_hidden=0 and tag_count>0 order by tag_count desc,tag_id desc limit 30");
	$hot_tags = array();
	while($rs = $db->fetch_array($q)){
		$rs['a_view_tag'] = urr("tag","tag=".rawurlencode($rs['tag_name'])."");
		$rs['tag_count'] = $rs['tag_count'] ? "({$rs['tag_count']})" : '';
		$hot_tags[] = $rs;
	}
	$db->free($q);
	unset($rs);
	return $hot_tags;
}
function get_last_user_list($num=10){
	global $db,$tpf;
	$q = $db->query("select username,reg_time from {$tpf}users order by userid desc limit $num");
	$last_users = array();
	while ($rs = $db->fetch_array($q)) {
		$rs[a_space] = urr("space","username=".rawurlencode($rs[username]));
		$rs[reg_time] = custom_time('m/d',$rs[reg_time]);
		$last_users[] = $rs;	
	}
	$db->free($q);
	unset($rs);
	return $last_users;
}
function get_last_file(){
	global $db,$tpf;
	$q = $db->query("select file_id,file_key,file_name,file_extension,file_time from {$tpf}files where (is_public=1 or in_share=1) and in_recycle=0 and report_status=0 and userid>0 order by file_id desc limit 10");
	$last_file = array();
	while($rs = $db->fetch_array($q)){
		$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
		$rs['file_name'] = cutstr($rs['file_name'].$tmp_ext,30);
		$rs['a_viewfile'] = urr("viewfile","file_id={$rs['file_id']}");
		$rs['file_time'] = is_today($rs['file_time']) ? '<span class="txtred" style="float:right">'.date('m/d',$rs['file_time']).'</span>' : '<span class="txtgray" style="float:right">'.date('m/d',$rs['file_time']).'</span>';
		$rs['file_icon'] = file_icon($rs['file_extension']);
		$last_file[] = $rs;
	}
	$db->free($q);
	unset($rs);
	return $last_file;
}
function get_hot_file(){
	global $db,$tpf;
	$q = $db->query("select file_id,file_key,file_name,file_extension,file_time from {$tpf}files where (is_public=1 or in_share=1) and in_recycle=0 and report_status=0 and userid>0 order by file_views desc limit 10");
	$hot_file = array();
	while($rs = $db->fetch_array($q)){
		$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
		$rs['file_name'] = cutstr($rs['file_name'].$tmp_ext,30);
		$rs['a_viewfile'] = urr("viewfile","file_id={$rs['file_id']}");
		$rs['file_time'] = is_today($rs['file_time']) ? '<span class="txtred" style="float:right">'.date('m/d',$rs['file_time']).'</span>' : '<span class="txtgray" style="float:right">'.date('m/d',$rs['file_time']).'</span>';
		$rs['file_icon'] = file_icon($rs['file_extension']);
		$hot_file[] = $rs;
	}
	$db->free($q);
	unset($rs);
	return $hot_file;
}

?>