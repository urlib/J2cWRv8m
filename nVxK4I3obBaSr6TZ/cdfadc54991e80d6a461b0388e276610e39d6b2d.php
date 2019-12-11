<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: main.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){
	default:

		main_stats();

		$datacall_secure = file_exists(PHPDISK_ROOT.'api/datacall.php') ? true : false;
		$install_dir_exists = is_dir(PHPDISK_ROOT.'install/') ? true : false;
		
		$iconv_support = function_exists('iconv') ? '<span class="txtblue">'.__('yes').'</span>' : '<span class="txtred">'.__('no').'</span>';
		$mbstring_support = function_exists('mb_convert_encoding') ? '<span class="txtblue">'.__('yes').'</span>' : '<span class="txtred">'.__('no').'</span>';
		$post_max_size = ini_get('post_max_size');
		$file_max_size = ini_get('upload_max_filesize');
		$mysql_info = mysql_get_client_info();
		$gd_support = function_exists('gd_info') ? '<span class="txtblue">'.__('yes').'</span>' : '<span class="txtred">'.__('no').'</span>';
		$gd_info_arr = gd_info();
		$gd_info = $gd_info_arr['GD Version'];
		$charset_info = strtoupper($charset);

		$update_url = "<a href=".urr(ADMINCP,"item=version").">".__('update_now')."</a>";
		$update_log = PHPDISK_ROOT.'system/update.log.php';

		if($settings['open_autoupdate']){
			if(file_exists($update_file) && ($timestamp - filemtime($update_file)) < 86400*7){
				$alert = 0;
			}else{
				$alert = 1;
				$str = "<?php".LF;
				$str .= "\texit;".LF;
				$str .= "// This is PHPDISK auto-generated file. Do NOT modify me.".LF;
				$str .= "// Cache Time: ".date("Y-m-d H:i:s").LF.LF;
				$str .= "?>".LF;
				$str .= PHPDISK_VERSION.'|'.PHPDISK_RELEASE.LF;
				write_file($update_log,$str);
			}
		}else{
			$alert = 0;
		}
		$newsdown = PHPDISK_ROOT.'system/newsdown.log.php';
		if(!file_exists($newsdown) || ($timestamp - filemtime($newsdown)) > 86400*3){
			$arr = get_web_link('http://www.phpdisk.com/');
		}else{
			$get_official_news = false;
			$show_news_frame = 'none';
		}
		if($arr['http_code'] == 200){
			$get_official_news = true;
			$show_news_frame = '';
			@unlink($newsdown);
		}elseif($arr['http_code'] ==0){
			$str = "<?php".LF;
			$str .= "\texit;".LF;
			$str .= "// This is PHPDISK auto-generated file. Do NOT modify me.".LF;
			$str .= "// Cache Time: ".date("Y-m-d H:i:s").LF.LF;
			$str .= "// phpdisk official site ...".LF;
			$str .= "?>".LF;
			write_file($newsdown,$str);
		}

		require_once template_echo('main',$admin_tpl_dir,'',1);
}
function get_web_link($url){
	if(function_exists('curl_init')){
		$options = array(
		CURLOPT_RETURNTRANSFER => true,
		CURLOPT_HEADER         => false,
		CURLOPT_ENCODING       => "",
		CURLOPT_USERAGENT      => "spider",
		CURLOPT_AUTOREFERER    => true,
		CURLOPT_CONNECTTIMEOUT => 120,
		CURLOPT_TIMEOUT        => 2,
		CURLOPT_MAXREDIRS      => 10,
		CURLOPT_NOBODY => 1,
		);
		$ch = curl_init($url);
		curl_setopt_array($ch, $options);
		$content = curl_exec($ch);
		$err = curl_errno($ch);
		$errmsg = curl_error($ch);
		$header = curl_getinfo($ch);
		curl_close($ch);

		$header['errno'] = $err;
		$header['errmsg'] = $errmsg;
		$header['content'] = $content;

		return $header;
	}
}
?>