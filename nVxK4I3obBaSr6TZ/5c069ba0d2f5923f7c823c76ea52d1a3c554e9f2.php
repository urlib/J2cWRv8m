<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: templates.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){

	case 'active':
		$tpl_id = trim(gpc('tpl_id','G',''));

		$tpl_type = $db->result_first("select tpl_type from {$tpf}templates where tpl_name='$tpl_id'");
		$db->query_unbuffered("update {$tpf}templates set actived=0 where tpl_type='$tpl_type'");
		$db->query_unbuffered("update {$tpf}templates set actived=1 where tpl_name='$tpl_id'");
		tpl_cache();
		$sysmsg[] = __('tpl_active_success');
		redirect(urr(ADMINCP,"item=templates"),$sysmsg);

		break;

	default:
		syn_templates();

		$q = $db->query("select * from {$tpf}templates order by tpl_type desc,actived desc,tpl_name asc");
		while($rs = $db->fetch_array($q)){
			if(check_template($rs['tpl_name'])){
				$templates_arr[] = get_template_info($rs['tpl_name']);
			}
		}
		$db->free($q);
		unset($rs);
		require_once template_echo($item,$admin_tpl_dir,'',1);

}

function syn_templates(){
	global $db,$tpf;
	$dirs = scandir(PHPDISK_ROOT.'templates');
	sort($dirs);

	for($i=0;$i<count($dirs);$i++){
		if(check_template($dirs[$i])){
			$arr[] = $dirs[$i];
		}
	}

	$q = $db->query("select * from {$tpf}templates where actived=1");
	while($rs = $db->fetch_array($q)){
		if(check_template($rs['tpl_name'])){
			$active_templates .= $rs['tpl_name'].',';
		}
	}
	$db->free($q);
	unset($rs);

	if(trim(substr($active_templates,0,-1))){
		$active_arr = explode(',',$active_templates);
	}
	for($i=0;$i<count($arr);$i++){
		$tmp = get_template_info($arr[$i]);
		if(@in_array($arr[$i],$active_arr)){
			$sql_do .= "('".$db->escape($arr[$i])."','1','".$db->escape(trim($tmp['tpl_type']))."'),";
		}else{
			$sql_do .= "('".$db->escape($arr[$i])."','0','".$db->escape(trim($tmp['tpl_type']))."'),";
		}
	}
	$sql_do = substr($sql_do,0,-1);
	$db->query_unbuffered("truncate table {$tpf}templates;");
	$db->query_unbuffered("replace into {$tpf}templates(tpl_name,actived,tpl_type) values $sql_do ;");

	$num = @$db->result_first("select count(*) from {$tpf}templates where tpl_type='admin' and actived=1");
	if(!$num){
		$db->query_unbuffered("update {$tpf}templates set actived=1 where tpl_name='admin'");
	}
	$num = @$db->result_first("select count(*) from {$tpf}templates where tpl_type='user' and actived=1");
	if(!$num){
		$db->query_unbuffered("update {$tpf}templates set actived=1 where tpl_name='default'");
	}
	return true;
}
function get_template_info($tpl_name){
	global $db,$tpf;
	$file = PHPDISK_ROOT."templates/$tpl_name/template_info.php";
	if(file_exists($file)){
		$_data = read_file($file);
		preg_match("/Template Name:(.*)/i",$_data,$tpl_title);
		preg_match("/Template URL:(.*)/i",$_data,$tpl_url);
		preg_match("/Description:(.*)/i",$_data,$tpl_desc);
		preg_match("/Author:(.*)/i",$_data,$tpl_author);
		preg_match("/Author Site:(.*)/i",$_data,$tpl_site);
		preg_match("/Version:(.*)/i",$_data,$tpl_version);
		preg_match("/Template Type:(.*)/i",$_data,$tpl_type);
		preg_match("/PHPDISK Core:(.*)/i",$_data,$phpdisk_core);
	}
	$actived = (int)@$db->result_first("select actived from {$tpf}templates where tpl_name='$tpl_name' limit 1");
	$arr = array(
	'tpl_title' => trim($tpl_title[1]),
	'tpl_url' => trim($tpl_url[1]),
	'tpl_desc' => htmlspecialchars(trim($tpl_desc[1])),
	'tpl_author' => trim($tpl_author[1]),
	'tpl_site' => trim($tpl_site[1]),
	'tpl_version' => trim($tpl_version[1]),
	'tpl_type' => trim(strtolower($tpl_type[1])),
	'tpl_dir' => trim($tpl_name),
	'phpdisk_core' => trim($phpdisk_core[1]),
	'actived' => $actived,
	);
	return $arr;
}
function check_template($tpl_name){
	$dir = PHPDISK_ROOT."templates/{$tpl_name}/";
	if(is_dir($dir) && file_exists($dir.'template_info.php') && $tpl_name !='.' && $tpl_name !='..'){
		$rtn = 1;
	}else{
		$rtn = 0;
	}
	return $rtn;
}

?>