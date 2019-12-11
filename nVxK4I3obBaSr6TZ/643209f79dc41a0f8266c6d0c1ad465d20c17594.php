<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: credit.inc.php 25 2014-01-10 03:13:43Z along $
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
			'open_credit_convert' => 0,
			'credit_convert' => 0,
			'credit_open' => 0,
			'credit_reg' => 0,
			'credit_invite' => 0,
			'credit_login' => 0,
			'credit_msg' => 0,
			'credit_upload' => 0,
			'credit_down' => 0,
			'credit_down_my' => 0,
			'wealth_reg' => 0,
			'wealth_invite' => 0,
			'wealth_login' => 0,
			'wealth_msg' => 0,
			'wealth_upload' => 0,
			'wealth_down' => 0,
			'wealth_down_my' => 0,
			'exp_reg' => 0,
			'exp_invite' => 0,
			'exp_login' => 0,
			'exp_msg' => 0,
			'exp_upload' => 0,
			'exp_down' => 0,
			'exp_down_my' => 0,
			'credit_union' => '积分',
			'wealth_union' => '金钱',
			'exp_union' => '经验',
			'exp_const' => 50,
			);
			$settings = gpc('setting','P',$setting);

			if(trim($settings['credit_union']) ==''){
				$error = true;
				$sysmsg[] = __('cu_error');
			}
			if(trim($settings['wealth_union']) ==''){
				$error = true;
				$sysmsg[] = __('wu_error');
			}
			if(trim($settings['exp_union']) ==''){
				$error = true;
				$sysmsg[] = __('eu_error');
			}
			if(!is_numeric($settings['exp_const'])){
				$error = true;
				$sysmsg[] = __('cu_error');
			}else{
				$settings['exp_const'] = (int)$settings['exp_const'];
			}
			if(!$error){
				settings_cache($settings);

				$sysmsg[] = __('credit_update_success');
				redirect(urr(ADMINCP,"item=$item"),$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}

		}else{
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
}
?>