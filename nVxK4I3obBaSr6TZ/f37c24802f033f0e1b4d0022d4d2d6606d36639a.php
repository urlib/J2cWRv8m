<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: version.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}
@set_time_limit(120);

$autoupdate_configs_name = 'phpdisk_autoupdate_configs_'.$db_charset;
$default_path = 'http://www.phpdisk.com/autoupdate/file_edition/';
$auto_update_path = isset($auth['com_autoupdate_path']) ? trim($auth['com_autoupdate_path']) : $default_path;

if(file_exists(PHPDISK_ROOT.$autoupdate_configs_name.'.php')){
	require_once PHPDISK_ROOT.$autoupdate_configs_name.'.php';
}

$charset_info = strtoupper($charset);

switch($action){
	case 'step1':
		$file_src = $auto_update_path.$autoupdate_configs_name.'.zip';
		$file_dest = PHPDISK_ROOT.$autoupdate_configs_name.'.zip';
		if(@fopen($file_src,'r')){
			download_file($file_src,$file_dest);
			$msg = __('check_configs');
			gonext(urr(ADMINCP,"item=$item&action=step2"));
		}else{
			$msg = __('configs_download_error');
		}
		require_once template_echo($item,$admin_tpl_dir,'',1);
		break;
	case 'step2':
		$zip = new cls_zip;
		$zip->unzip(PHPDISK_ROOT.$autoupdate_configs_name.'.zip','.');
		$msg = __('download_update_configs');
		gonext(urr(ADMINCP,"item=$item&action=step3"));
		require_once template_echo($item,$admin_tpl_dir,'',1);
		break;
	case 'step3':
		$phpdisk_package_url = trim($pau['phpdisk_package_'.PHPDISK_RELEASE.'_'.$pau['last_version'].'_'.$db_charset]);
		if(fopen($phpdisk_package_url,'rb')){
			$file_dest = PHPDISK_ROOT.'phpdisk_package_'.$db_charset.'.zip';
			download_file($phpdisk_package_url,$file_dest);
			$msg = __('download_new_version');
			gonext(urr(ADMINCP,"item=$item&action=step4"));
		}else{
			$msg = __('phpdisk_no_package');
			clean_env();
		}
		require_once template_echo($item,$admin_tpl_dir,'',1);
		break;
	case 'step4':
		if(file_exists(PHPDISK_ROOT.'phpdisk_package_'.$db_charset.'.zip')){
			$md5_hash = strtolower(md5(read_file(PHPDISK_ROOT.'phpdisk_package_'.$db_charset.'.zip')));
		}
		if($pau['package_verify_'.PHPDISK_RELEASE.'_'.$pau['last_version'].'_'.$db_charset] != $md5_hash){
			$msg = __('package_verify_error');
		}else{
			$msg = __('package_verify_success');
			gonext(urr(ADMINCP,"item=$item&action=step5"));
		}
		require_once template_echo($item,$admin_tpl_dir,'',1);
		break;
	case 'step5':
		$msg = __('update_db_sql');
		if($pau['update_sqls'] && $pau['update_db']){
			$arr_p = explode(';',$pau['update_sqls']);
			for($i=0;$i<count($arr_p)-1;$i++){
				$db->query($arr_p[$i]);
				$msg .= "SQL Query: {$arr_p[$i]} ...... <span class=\"txtblue\">OK</span>.<br>";
			}
		}
		gonext(urr(ADMINCP,"item=$item&action=step6"));
		require_once template_echo($item,$admin_tpl_dir,'',1);
		break;
	case 'step6':
		$zip = new cls_zip;
		$zip->unzip(PHPDISK_ROOT.'phpdisk_package_'.$db_charset.'.zip','.');
		$msg = __('update_new_version_script');
		gonext(urr(ADMINCP,"item=$item&action=step7"));
		require_once template_echo($item,$admin_tpl_dir,'',1);
		break;
	case 'step7':
		clean_env();
		$msg = __('update_success');
		require_once template_echo($item,$admin_tpl_dir,'',1);
		break;

	default:
		$update_url = "<a href=".urr(ADMINCP,"item=version&action=step1")." onclick=return confirm('".__('confirm_update')."');>".__('update_now')."</a>";
		$update_log = PHPDISK_ROOT."./system/update.log.php";

		$str = "<?php".LF;
		$str .= "\texit;".LF;
		$str .= "// This is PHPDISK auto-generated file. Do NOT modify me.".LF;
		$str .= "// Cache Time: ".date("Y-m-d H:i:s").LF.LF;
		$str .= "?>".LF;
		$str .= PHPDISK_VERSION.'|'.PHPDISK_RELEASE.LF;
		write_file($update_log,$str);
		require_once template_echo($item,$admin_tpl_dir,'',1);
}
function download_file($file_src,$file_dest){
	$handle = fopen($file_src, "rb");
	$contents = "";
	do {
		$data = fread($handle, 1024);
		if (strlen($data) == 0) {
			break;
		}
		$contents .= $data;
	} while(true);
	@fclose ($handle);
	write_file($file_dest,$contents);
}
function clean_env(){
	global $autoupdate_configs_name,$pau,$db_charset;
	if($pau['clean_old_file']){
		if($pau['old_files']){
			$arr = explode(';',$pau['old_files']);
			for($i=0;$i<count($arr)-1;$i++){
				@unlink(PHPDISK_ROOT.$arr[$i]);
			}
		}
		if($pau['old_dirs']){
			$arr = explode(';',$pau['old_dirs']);
			for($i=0;$i<count($arr)-1;$i++){
				@rmdir(PHPDISK_ROOT.$arr[$i]);
			}
		}
	}
	@unlink(PHPDISK_ROOT.'phpdisk_autoupdate_configs_'.$db_charset.'.php');
	@unlink(PHPDISK_ROOT.$autoupdate_configs_name.'.zip');
	@unlink(PHPDISK_ROOT.'phpdisk_package_'.$db_charset.'.zip');
}
function gonext($url,$timeout=1500){
	echo "<script>\r\n";
	echo "<!--\r\n";
	echo "function redirect() {\r\n";
	echo "	window.location.replace('$url');\r\n";
	echo "}\r\n";
	echo "setTimeout('redirect();', $timeout);\r\n";
	echo "-->\r\n";
	echo "</script>\r\n";
}

?>