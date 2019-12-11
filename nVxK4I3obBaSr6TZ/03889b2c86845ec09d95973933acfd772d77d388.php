<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: verycode.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){
	
	default:
		
		if($task =='update'){
			form_auth(gpc('formhash','P',''),formhash());
			$setting = array(
				'register_verycode' => 0,
				'login_verycode' => 0,
				'forget_verycode' => 0,
				'verycode_type' => 0,
				'active_verycode' => 0,
			);
			$settings = gpc('setting','P',$setting);

			$settings['register_verycode'] = (int)$settings['register_verycode'];
			$settings['login_verycode'] = (int)$settings['login_verycode'];
			$settings['forget_verycode'] = (int)$settings['forget_verycode'];
			$settings['active_verycode'] = (int)$settings['active_verycode'];
			
			settings_cache($settings);
			
			$sysmsg[] = __('verycode_update_success');
			
			redirect($_SERVER['HTTP_REFERER'],$sysmsg);
		}else{	
			$settings['verycode_type'] = $settings['verycode_type'] ? (int)$settings['verycode_type'] : 1;
			$setting = $settings;
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
}
?>