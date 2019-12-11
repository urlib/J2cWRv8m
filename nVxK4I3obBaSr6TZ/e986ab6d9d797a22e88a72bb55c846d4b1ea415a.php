<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: settings.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){
	case 'base':

		if($task =='base'){
			form_auth(gpc('formhash','P',''),formhash());

			$setting = array(
			'site_title' => '',
			'miibeian' => '',
			'contact_us' => '',
			'site_stat' => '',
			'phpdisk_url' => '',
			'encrypt_key' => '',
			'allow_access' => '1',
			'close_access_reason' => '',
			'allow_register' => '1',
			'close_register_reason' => '',
			);
			$online_demo = $settings['online_demo'];
			$settings = gpc('setting','P',$setting);
			$settings['filter_extension'] = 'asp,asa,aspx,ascx,dtd,xsd,xsl,xslt,as,wml,java,vtm,vtml,jst,asr,php,php3,php4,php5,vb,vbs,jsf,jsp,pl,cgi,js,html,htm,xhtml,xml,css,shtm,cfm,cfml,shtml,bat,sh';
			$settings['site_stat'] = base64_encode($settings['site_stat']);

			if($online_demo){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(checklength($settings['site_title'],2,100)){
				$error = true;
				$sysmsg[] = __('site_title_error');
			}
			if(substr($settings['phpdisk_url'],0,7) !='http://' && substr($settings['phpdisk_url'],0,8) !='https://'){
				$error = true;
				$sysmsg[] = __('phpdisk_url_error');
			}else{
				$settings['phpdisk_url'] = substr($settings['phpdisk_url'],-1) =='/' ? $settings['phpdisk_url'] : $settings['phpdisk_url'].'/';
			}
			if(checklength($settings['encrypt_key'],8,20) || preg_match("/[^a-z0-9]/i",$settings['encrypt_key'])){
				$error = true;
				$sysmsg[] = __('encrypt_key_error');
			}
			if(!checkemail($settings['contact_us'])){
				$error = true;
				$sysmsg[] = __('contact_us_error');
			}
			if(!$settings['allow_access']){
				if(checklength($settings['close_access_reason'],2,200)){
					$error = true;
					$sysmsg[] = __('close_access_reason_error');
				}
			}
			if(!$settings['allow_register']){
				if(checklength($settings['close_register_reason'],2,200)){
					$error = true;
					$sysmsg[] = __('close_register_reason_error');
				}
			}
			$settings['perpage'] = !is_numeric($settings['perpage']) ? 20 : (int)$settings['perpage'];

			if(!$error){

				settings_cache($settings);

				$sysmsg[] = __('base_settings_update_success');
				redirect(urr(ADMINCP,"item=settings&action=$action"),$sysmsg);

			}else{
				redirect('back',$sysmsg);
			}

		}else{
			$setting = $settings;
			$setting['site_stat'] = stripslashes(base64_decode($setting['site_stat']));
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'advanced':
		if($task =='advanced'){
			form_auth(gpc('formhash','P',''),formhash());

			$setting = array(
			'file_path' => '',
			'secs_loading' => 0,
			'login_down_file' => 0,
			'true_link' => 0,
			'true_link_extension' => '',
			'open_demo_login' => 0,
			'open_plugins_cp' => 0,
			'gzipcompress' => 0,
			'max_file_size' => '',
			'perpage' => 0,
			'open_file_preview' => 0,
			'open_file_extract_code' => 0,
			'open_file_outlink' => 0,
			'downfile_directly' => 0,
			'show_relative_file' => 0,
			'show_stat_index' => 0,
			'invite_register_encode' => 0,
			'show_hot_file_right' => 0,
			'create_default_folder' => '',	
			'cache_time' => 0,
			'all_file_share' => 0,
			'share_tool' => '',		
			'local_store' => 0,		
			'yun_store' => 0,		
			);
			$online_demo = $settings['online_demo'];
			$settings = gpc('setting','P',$setting);
			$settings['filter_extension'] = 'asp,asa,aspx,ascx,dtd,xsd,xsl,xslt,as,wml,java,vtm,vtml,jst,asr,php,php3,php4,php5,vb,vbs,jsf,jsp,pl,cgi,js,html,htm,xhtml,xml,css,shtm,cfm,cfml,shtml,bat,sh';
			$settings['true_link_extension'] = str_replace(array("\r","\n",'，'),array('','',','),$settings['true_link_extension']);
			$settings['share_tool'] = base64_encode($settings['share_tool']);
			
			if($online_demo){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			$bad_dirs = array('admin','docs','images','includes','install','languages','modules','system','templates','tools');
			if(in_array($settings['file_path'],$bad_dirs)){
				$error = true;
				$sysmsg[] = '"'.$settings['file_path'].'"'.__('system_reserve_folder');
			}
			if(checklength($settings['file_path'],2,20)){
				$error = true;
				$sysmsg[] = __('file_path_error');
			}
			if($settings['hide_local_store'] && $settings['hide_yun_store']==1){
				$error = true;
				$sysmsg[] = '您至少需要选择一种网盘上传接口';
			}
			if($settings['hide_yun_store']==2 && $settings[yun_site_key]==''){
				$error = true;
				$sysmsg[] = '使用网盘云站长版时，需要填写站长版密钥';
			}
			if(!is_numeric($settings['show_hot_file_right'])){
				$error = true;
				$sysmsg[] = __('show_hot_file_right_error');
			}else{
				$settings['show_hot_file_right'] = (int)$settings['show_hot_file_right'];
			}
			if(!$error){

				settings_cache($settings);

				$sysmsg[] = __('advanced_settings_update_success');
				redirect(urr(ADMINCP,"item=settings&action=$action"),$sysmsg);

			}else{
				redirect('back',$sysmsg);
			}

		}else{
			$upload_max = get_byte_value(ini_get('upload_max_filesize'));
			$post_max = get_byte_value(ini_get('post_max_size'));
			$settings_max = $settings['max_file_size'] ? get_byte_value($settings['max_file_size']) : 0;
			$max_php_file_size = min($upload_max, $post_max);
			$max_file_size_byte = ($settings_max && $settings_max <= $max_php_file_size) ? $settings_max : $max_php_file_size;
			$max_user_file_size = get_size($max_file_size_byte,'B',0);
			$settings['secs_loading'] = $settings['secs_loading'] ? (int)$settings['secs_loading'] : 0;
			$file_real_path = PHPDISK_ROOT.$settings['file_path'].'/';
			if(!is_dir($file_real_path)){
				$file_path_tips = __('file_path_not_exists');
			}
			$settings['open_link_domain'] = str_replace('|',LF,$settings['open_link_domain']);
			$settings['share_tool'] = stripslashes(base64_decode($settings['share_tool']));
			$settings['cache_time'] = isset($settings['cache_time']) ? $settings['cache_time'] : 1;
			$setting = $settings;
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;
	case 'share':
		$db->query_unbuffered("update {$tpf}files set in_share=1");
		$sysmsg[] = __('share_all_file_success');
		redirect('back',$sysmsg);
		break;
}
?>