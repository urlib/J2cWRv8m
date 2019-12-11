<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: lang.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){

	case 'active':
		$lang_name = trim(gpc('lang_name','G',''));

		$lang_package = PHPDISK_ROOT.'./languages/'.$lang_name.'/LC_MESSAGES/phpdisk.po';

		if(!file_exists($lang_package)){
			$sysmsg[] = __('lang_not_exists');

		}else{
			$db->query_unbuffered("update {$tpf}langs set actived=0;");
			$db->query_unbuffered("update {$tpf}langs set actived=1 where lang_name='$lang_name'");
			lang_cache();
			$sysmsg[] = __('lang_active_success');
		}
		redirect(urr(ADMINCP,"item=lang"),$sysmsg);

		break;

	default:
		if($task =='update'){
			form_auth(gpc('formhash','P',''),formhash());

			$setting = array(
			'open_switch_langs' => 0,
			);
			$settings = gpc('setting','P',$setting);
			if(!$error){

				settings_cache($settings);
				lang_cache();
				$sysmsg[] = __('lang_update_success');
				redirect(urr(ADMINCP,"item=lang"),$sysmsg);

			}else{
				redirect('back',$sysmsg);
			}
		}else{
			syn_languages();

			$q = $db->query("select * from {$tpf}langs order by actived desc,lang_name asc");
			while($rs = $db->fetch_array($q)){
				if(check_lang($rs['lang_name'])){
					$languages_arr[] = get_lang_info($rs['lang_name']);
				}
			}
			$db->free($q);
			unset($rs);
			require_once template_echo('lang',$admin_tpl_dir,'',1);
		}
}
function syn_languages(){
	global $db,$tpf;
	$dirs = scandir(PHPDISK_ROOT.'./languages');
	sort($dirs);
	for($i=0;$i<count($dirs);$i++){
		if(check_lang($dirs[$i])){
			$arr[] = $dirs[$i];
		}
	}
	$q = $db->query("select * from {$tpf}langs where actived=1");
	while($rs = $db->fetch_array($q)){
		if(check_lang($rs['lang_name'])){
			$active_languages .= $rs['lang_name'].',';
		}
	}
	$db->free($q);
	unset($rs);

	if(trim(substr($active_languages,0,-1))){
		$active_arr = explode(',',$active_languages);
	}
	for($i=0;$i<count($arr);$i++){
		if(@in_array($arr[$i],$active_arr)){
			$sql_do .= "('".$db->escape($arr[$i])."','1'),";
		}else{
			$sql_do .= "('".$db->escape($arr[$i])."','0'),";
		}
	}
	$sql_do = substr($sql_do,0,-1);
	$db->query_unbuffered("truncate table {$tpf}langs;");
	$db->query_unbuffered("replace into {$tpf}langs(lang_name,actived) values $sql_do ;");

	$num = @$db->result_first("select count(*) from {$tpf}langs where actived=1");
	if(!$num){
		$db->query_unbuffered("update {$tpf}langs set actived=1 where lang_name='zh_cn'");
	}
	return true;
}
function get_lang_info($lang_name){
	global $db,$tpf;
	$file = PHPDISK_ROOT."languages/$lang_name/lang_info.php";
	if(file_exists($file)){
		$_data = read_file($file);
		preg_match("/Language Name:(.*)/i",$_data,$lang_title);
		preg_match("/Language URL:(.*)/i",$_data,$lang_url);
		preg_match("/Description:(.*)/i",$_data,$lang_desc);
		preg_match("/Author:(.*)/i",$_data,$lang_author);
		preg_match("/Author Site:(.*)/i",$_data,$lang_site);
		preg_match("/Version:(.*)/i",$_data,$lang_version);
		preg_match("/PHPDISK Core:(.*)/i",$_data,$phpdisk_core);
	}
	$actived = (int)@$db->result_first("select actived from {$tpf}langs where lang_name='$lang_name' limit 1");
	$arr = array(
	'lang_title' => trim($lang_title[1]),
	'lang_url' => trim($lang_url[1]),
	'lang_desc' => htmlspecialchars(trim($lang_desc[1])),
	'lang_author' => trim($lang_author[1]),
	'lang_site' => trim($lang_site[1]),
	'lang_version' => trim($lang_version[1]),
	'lang_dir' => trim($lang_name),
	'phpdisk_core' => trim($phpdisk_core[1]),
	'actived' => $actived,
	);
	return $arr;
}
function check_lang($lang_name){
	$dir = PHPDISK_ROOT."languages/{$lang_name}/";
	if(file_exists($dir.'./lang_info.php') && $lang_name !='.' && $lang_name !='..'){
		$rtn = 1;
	}else{
		$rtn = 0;
	}
	return $rtn;
}

?>