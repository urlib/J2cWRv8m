<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: announce.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){
	case 'index':

		if($task =='update_setting'){
			form_auth(gpc('formhash','P',''),formhash());

			$setting = array(
			'show_announce_detail' => 0,
			);
			$settings = gpc('setting','P',$setting);

			if(!$error){

				settings_cache($settings);

				$sysmsg[] = __('setting_update_success');
				redirect(urr(ADMINCP,"item=$item"),$sysmsg);

			}else{
				redirect('back',$sysmsg);
			}

		}elseif($task =='update'){
			form_auth(gpc('formhash','P',''),formhash());

			$show_order = gpc('show_order','P',array());
			$annids = gpc('annids','P',array());

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}

			if(!$error){
				for($i =0;$i<count($annids);$i++){
					$db->query_unbuffered("update {$tpf}announces set show_order='".(int)$show_order[$i]."' where annid='".(int)$annids[$i]."'");
				}
				
				redirect(urr(ADMINCP,"item=$item&action=index"),'',0);
			}else{
				redirect('back',$sysmsg);
			}

		}else{
			$q = $db->query("select * from {$tpf}announces order by show_order asc,annid asc");
			$announces = array();
			while($rs = $db->fetch_array($q)){
				$rs['status_text'] = $rs['is_hidden'] ? '<span class="txtblue">'.__('display').'</span>' : __('hidden');
				$rs['short_content'] = str_replace("\r\n",' ',cutstr(preg_replace("/<.+?>/i","",$rs['content']),45));
				$rs['content'] = preg_replace("/<.+?>/i","",str_replace('<br>',LF,$rs['content']));
				$rs['a_modify_announce'] = urr(ADMINCP,"item=$item&menu=extend&action=modify_announce&annid={$rs['annid']}");
				$rs['a_delete_announce'] = urr(ADMINCP,"item=$item&menu=extend&action=delete_announce&annid={$rs['annid']}");
				$rs['a_change_status'] = urr(ADMINCP,"item=$item&menu=extend&action=change_status&annid={$rs['annid']}");
				$rs['expand'] = $rs['is_expand'] ? '<span class="txtblue">'.__('yes').'</span>' : '<span class="txtgray">'.__('no').'</span>';
				$announces[] = $rs;
			}
			$db->free($q);
			unset($rs);
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'add_announce':

		if($task =='add_announce'){
			form_auth(gpc('formhash','P',''),formhash());

			$subject = trim(gpc('subject','P',''));
			$expand = (int)gpc('expand','P',0);
			$content = trim(gpc('content','P',''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(checklength($subject,2,100)){
				$error = true;
				$sysmsg[] = __('subject_error');
			}
			if(checklength($content,2,3000)){
				$error = true;
				$sysmsg[] = __('content_error');
			}else{
				$content = str_replace(LF,'<br>',$content);
			}
			$rs = $db->fetch_one_array("select count(*) as total from {$tpf}announces where subject='$subject'");
			if($rs['total'] >0){
				$error = true;
				$sysmsg[] = __('announce_exists');
			}
			unset($rs);
			if(!$error){
				$ins = array(
				'userid' => $pd_uid,
				'subject' => replace_js($subject),
				'content' => addslashes(replace_js($content)),
				'is_expand' => $expand,
				'in_time' => $timestamp,
				);
				$db->query("insert into {$tpf}announces set ".$db->sql_array($ins).";");
				
				redirect(urr(ADMINCP,"item=$item&action=index"),'',0);
			}else{
				redirect('back',$sysmsg);
			}
		}else{
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'modify_announce':
		$annid = (int)gpc('annid','GP',0);

		if($task =='modify_announce'){
			form_auth(gpc('formhash','P',''),formhash());

			$subject = trim(gpc('subject','P',''));
			$expand = (int)gpc('expand','P',0);
			$content = trim(gpc('content','P',''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(checklength($subject,2,100)){
				$error = true;
				$sysmsg[] = __('subject_error');
			}
			if(checklength($content,2,3000)){
				$error = true;
				$sysmsg[] = __('content_error');
			}else{
				$content = str_replace(LF,'<br>',$content);
			}
			$rs = $db->fetch_one_array("select count(*) as total from {$tpf}announces where subject='$subject'");
			if($rs['total'] >1){
				$error = true;
				$sysmsg[] = __('announce_exists');
			}
			unset($rs);
			if(!$error){
				$ins = array(
				'subject' => replace_js($subject),
				'content' => addslashes(replace_js($content)),
				'is_expand' => $expand,
				'in_time' => $timestamp,
				);
				$db->query("update {$tpf}announces set ".$db->sql_array($ins)." where annid='$annid' limit 1;");
				
				redirect(urr(ADMINCP,"item=$item&action=index"),'',0);
			}else{
				redirect('back',$sysmsg);
			}
		}else{
			$rs = $db->fetch_one_array("select * from {$tpf}announces where annid='$annid'");
			if($rs){
				$subject = $rs['subject'];
				$expand = $rs['is_expand'];
				$content = str_replace('<br>',LF,$rs['content']);
			}
			unset($rs);
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'delete_announce':
		if($settings['online_demo']){
			$error = true;
			$sysmsg[] = __('online_demo_deny');
		}
		if(!$error){
			$annid = (int)gpc('annid','G',0);
			$db->query_unbuffered("delete from {$tpf}announces where annid='$annid' limit 1");
			
			redirect(urr(ADMINCP,"item=$item&action=index"),'',0);
		}else{
			redirect('back',$sysmsg);
		}
		break;

	case 'change_status':
		if($settings['online_demo']){
			$error = true;
			$sysmsg[] = __('online_demo_deny');
		}
		if(!$error){
			$annid = (int)gpc('annid','G',0);
			$rs = $db->fetch_one_array("select is_hidden from {$tpf}announces where annid='$annid'");
			$status = $rs['is_hidden'] ? 0 : 1;
			unset($rs);
			$db->query_unbuffered("update {$tpf}announces set is_hidden='$status' where annid='$annid'");
			
			redirect(urr(ADMINCP,"item=$item&action=index"),'',0);
		}else{
			redirect('back',$sysmsg);
		}
		break;

	default:
		redirect(urr(ADMINCP,"item=$item&action=index"),'',0);
}
?>