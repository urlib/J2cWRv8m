<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: public.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

include "includes/commons.inc.php";

$in_front = true;

$cate_id = (int)gpc('cate_id','G',0);
$pid = (int)gpc('pid','G',0);
$n = trim(gpc('n','G',''));
$u = trim(gpc('u','G',''));
$s = trim(gpc('s','G',''));
$t = trim(gpc('t','G',''));
$cate_name = @$db->result_first("select cate_name from {$tpf}categories where cate_id='$cate_id'");
$cate_name = $cate_name ? $cate_name.' - ' : '';
$title = $cate_name.__('public_file');
include PHPDISK_ROOT."./includes/header.inc.php";

$public_folder_tree = public_menu_cache(1);

if($cate_id){
	$o_arr = array('asc','desc');
	if($n){
		$sql_order = in_array($n,$o_arr) ? " file_name $n" : " file_name asc";
	}elseif($u){
		$sql_order = in_array($u,$o_arr) ? " username $u" : " username asc";
	}elseif($s){
		$sql_order = in_array($s,$o_arr) ? " file_size $s" : " file_size asc";
	}elseif($t){
		$sql_order = in_array($t,$o_arr) ? " file_time $t" : " file_time asc";
	}else{
		$sql_order = " file_id desc";
	}
	$perpage = 20;
	$cate_sql = $pid ? " fl.subcate_id='$cate_id' and " : " fl.cate_id='$cate_id' and ";
	$sql_do = "{$tpf}files fl,{$tpf}users u where {$cate_sql} is_public=1 and in_recycle=0 and cate_id>0 and fl.userid>0 and fl.userid=u.userid";

	$rs = $db->fetch_one_array("select count(*) as total_num from {$sql_do}");
	$total_num = $rs['total_num'];
	$start_num = ($pg-1) * $perpage;
	function get_public_file($cate_id){
		global $db,$tpf,$sql_do,$sql_order,$start_num,$perpage;
		$q = $db->query("select fl.*,u.username from {$sql_do} order by {$sql_order} limit $start_num, $perpage");
		$files_array = array();
		while($rs = $db->fetch_array($q)){
			$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
			$rs['file_name_all'] = $rs['file_name'].$tmp_ext;
			$rs['file_name'] = cutstr($rs['file_name'].$tmp_ext,35);
			$rs['file_size'] = get_size($rs['file_size']);
			$rs['file_time'] = custom_time("Y-m-d",$rs['file_time']);
			$rs['a_space'] = urr("space","username=".rawurlencode($rs['username']));
			$rs['a_viewfile'] = urr("viewfile","file_id={$rs['file_id']}&file_key={$rs['file_key']}");
			$rs['file_thumb'] = get_file_thumb($rs);
			$files_array[] = $rs;
		}
		$db->free($q);
		unset($rs);
		return $files_array;
	}
	$files_array = get_public_file($cate_id);
	$n_t = ($n=='asc') ? 'desc' : 'asc';
	$u_t = ($u=='asc') ? 'desc' : 'asc';
	$s_t = ($s=='asc') ? 'desc' : 'asc';
	$t_t = ($t=='asc') ? 'desc' : 'asc';
	$n_order = $n ? $L['o_'.$n_t] : '';
	$u_order = $u ? $L['o_'.$u_t] : '';
	$s_order = $s ? $L['o_'.$s_t] : '';
	$t_order = $t ? $L['o_'.$t_t] : '';
	$n_url = urr("public","pid=$pid&cate_id=$cate_id&n=$n_t");
	$u_url = urr("public","pid=$pid&cate_id=$cate_id&u=$u_t");
	$s_url = urr("public","pid=$pid&cate_id=$cate_id&s=$s_t");
	$t_url = urr("public","pid=$pid&cate_id=$cate_id&t=$t_t");
	$arr = explode('&',$_SERVER['QUERY_STRING']);
	$page_nav = multi($total_num, $perpage, $pg, "public.php?pid=$pid&cate_id=$cate_id&{$arr[2]}");

}else{
	function get_cate(){
		global $db,$tpf;
		$q = $db->query("select cate_id from {$tpf}categories where pid=0 and is_hidden=0 order by show_order asc,cate_id asc");
		while($rs = $db->fetch_array($q)){
			$cate_arr[] = $rs['cate_id'];
		}
		unset($rs);
		return $cate_arr;
	}
	$cate_arr = get_cate();
	for($i=0;$i<count($cate_arr);$i++){
		$arr_file[$cate_arr[$i]] = get_cate_file($cate_arr[$i]);
		//$arr_file[$cate_arr[$i]] = super_cache::get('get_cate_file|'.$cate_arr[$i]);
		$public_file_title[$cate_arr[$i]] = get_cate_title($cate_arr[$i]);
	}
}

$public_files_count = @$db->result_first("select count(*) from {$tpf}files where is_public=1 and is_checked=1 and cate_id>0 and userid>0");
$stat['public_files_count'] = $public_files_count;
$stat['stat_time'] = $timestamp;
stats_cache($stat);

$total_file_store = $stats['public_storage_count'];
require_once template_echo('pd_public',$user_tpl_dir);

function get_cate_file($cate_id){
	global $db,$tpf;
	$q = $db->query("select file_id,file_key,file_name,file_extension,file_time from {$tpf}files fl,{$tpf}categories c where c.pid=0 and is_public=1 and in_recycle=0 and fl.cate_id='$cate_id' and fl.cate_id=c.cate_id order by file_id desc limit 10");
	$arr = array();
	while($rs = $db->fetch_array($q)){
		$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
		$rs['file_name'] = cutstr($rs['file_name'].$tmp_ext,25);
		$rs['a_viewfile'] = urr("viewfile","file_id={$rs['file_id']}");
		$rs['file_time'] = is_today($rs['file_time']) ? '<span class="txtred" style="float:right">'.date('m/d',$rs['file_time']).'</span>' : '<span class="txtgray" style="float:right">'.date('m/d',$rs['file_time']).'</span>';
		$arr[] = $rs;
	}
	$db->free($q);
	unset($rs);
	return $arr;
}
function get_cate_title($cate_id){
	global $db,$tpf;
	return $db->result_first("select cate_name from {$tpf}categories where cate_id='$cate_id'");
}
include PHPDISK_ROOT."./includes/footer.inc.php";

?>
