<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: gallery.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){
	case 'index':

		if($task =='update_order'){
			form_auth(gpc('formhash','P',''),formhash());
			$show_order = gpc('show_order','P',array());
			$galids = gpc('galids','P',array());

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(!$error){
				for($i =0;$i<count($galids);$i++){
					$db->query_unbuffered("update {$tpf}gallery set show_order='".(int)$show_order[$i]."' where gal_id='".(int)$galids[$i]."'");
				}
				
				redirect(urr(ADMINCP,"item=$item&action=$action"),'',0);
			}else{
				redirect('back',$sysmsg);
			}	
		}elseif($task =='update_setting'){
			form_auth(gpc('formhash','P',''),formhash());
			$setting = array(
				'open_gallery_index' => 0,
				'gallery_type' => 1,
				'gallery_size_width' => 650,
				'gallery_size_height' => 200,
			);	
			$online_demo = $settings['online_demo'];
			$settings = gpc('setting','P',$setting);
				
			if($online_demo){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(!$error){
				
				settings_cache($settings);
				$sysmsg[] = __('setting_update_success');
				redirect(urr(ADMINCP,"item=$item"),$sysmsg);
				
			}else{
				redirect('back',$sysmsg);
			}
			
		}else{
			$q = $db->query("select * from {$tpf}gallery order by show_order asc,gal_id asc");
			$gallerys = array();
			while($rs = $db->fetch_array($q)){
				$rs['a_modify_gal'] = urr(ADMINCP,"item=$item&action=modify_gal&gal_id={$rs['gal_id']}");
				$rs['a_delete_gal'] = urr(ADMINCP,"item=$item&action=delete_gal&gal_id={$rs['gal_id']}");
				$gallerys[] = $rs;
			}
			$db->free($q);
			unset($rs);
			$settings['gallery_type'] = $settings['gallery_type'] ? $settings['gallery_type'] : 1;
			$settings['gallery_size_width'] = $settings['gallery_size_width'] ? (int)$settings['gallery_size_width'] : 650;
			$settings['gallery_size_height'] = $settings['gallery_size_height'] ? (int)$settings['gallery_size_height'] : 200;
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
	break;
	
	case 'add_gal':
		
		if($task =='add_gal'){
			form_auth(gpc('formhash','P',''),formhash());
			$gal_title = trim(gpc('gal_title','P',''));
			$gal_path = trim(gpc('gal_path','P',''));
			$go_url = trim(gpc('go_url','P',''));
			$gal_target = trim(gpc('gal_target','P',''));
			
			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(checklength($gal_title,2,150)){
				$error = true;
				$sysmsg[] = __('gal_title_error');
			}
			if(checklength($gal_path,2,200)){
				$error = true;
				$sysmsg[] = __('gal_path_error');
			}
			if(checklength($go_url,2,200)){
				$error = true;
				$sysmsg[] = __('go_url_error');
			}
			$num = $db->result_first("select count(*) from {$tpf}gallery where gal_path='$gal_path'");
			if($num){
				$error = true;
				$sysmsg[] = __('gal_path_exists');
			}
			if(!$error){
				$ins = array(
					'gal_title' => $gal_title,
					'gal_path' => $gal_path,
					'go_url' => $go_url,
					'gal_target' => $gal_target,
				);
				$db->query("insert into {$tpf}gallery set ".$db->sql_array($ins).";");
				
				redirect(urr(ADMINCP,"item=$item&action=index"),'',0);
			}else{
				redirect('back',$sysmsg);
			}
		}else{
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
	break;
	
	case 'modify_gal':
		$gal_id = (int)gpc('gal_id','GP',0);
		
		if($task =='modify_gal'){
			form_auth(gpc('formhash','P',''),formhash());
			$gal_title = trim(gpc('gal_title','P',''));
			$gal_path = trim(gpc('gal_path','P',''));
			$go_url = trim(gpc('go_url','P',''));
			$gal_target = trim(gpc('gal_target','P',''));
			
			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(checklength($gal_title,2,150)){
				$error = true;
				$sysmsg[] = __('gal_title_error');
			}
			if(checklength($gal_path,2,200)){
				$error = true;
				$sysmsg[] = __('gal_path_error');
			}
			if(checklength($go_url,5,200)){
				$error = true;
				$sysmsg[] = __('go_url_error');
			}
			$num = $db->result_first("select count(*) from {$tpf}gallery where gal_path='$gal_path' and gal_id<>'$gal_id'");
			if($num){
				$error = true;
				$sysmsg[] = __('gal_path_exists');
			}
			if(!$error){
				$ins = array(
					'gal_title' => $gal_title,
					'gal_path' => $gal_path,
					'go_url' => $go_url,
					'gal_target' => $gal_target,
				);
				$db->query("update {$tpf}gallery set ".$db->sql_array($ins)." where gal_id='$gal_id';");
				
				redirect(urr(ADMINCP,"item=$item&action=index"),'',0);
			}else{
				redirect('back',$sysmsg);
			}
		}else{
			$rs = $db->fetch_one_array("select * from {$tpf}gallery where gal_id='$gal_id'");
			if($rs){
				$gal_title = $rs['gal_title'];
				$gal_path = $rs['gal_path'];
				$go_url = $rs['go_url'];
				$gal_target = $rs['gal_target'];
			}
			unset($rs);
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}	
	break;
	
	case 'delete_gal':
		if($settings['online_demo']){
			$error = true;
			$sysmsg[] = __('online_demo_deny');
		}
		if(!$error){
			$gal_id = (int)gpc('gal_id','G',0);
			$db->query_unbuffered("delete from {$tpf}gallery where gal_id='$gal_id' limit 1");
			
			redirect(urr(ADMINCP,"item=$item&action=index"),'',0);
		}else{
			redirect('back',$sysmsg);
		}	
	break;
	
	default:
		redirect(urr(ADMINCP,"item=$item&action=index"),'',0);
}
?>