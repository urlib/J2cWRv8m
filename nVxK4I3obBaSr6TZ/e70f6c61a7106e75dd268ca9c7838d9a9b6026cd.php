<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: seo.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){

	default:

		if($task =='update_setting'){
			form_auth(gpc('formhash','P',''),formhash());

			$setting = array(
			'open_seo' => 0,
			'meta_keywords' => '',
			'meta_description' => '',
			'open_rewrite' => 0,
			);
			$settings = gpc('setting','P',$setting);

			if(!$error){

				settings_cache($settings);

				$sysmsg[] = __('seo_update_success');
				redirect(urr(ADMINCP,"item=$item"),$sysmsg);

			}else{
				redirect('back',$sysmsg);
			}

		}else{			
			$setting = $settings;
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
}
?>