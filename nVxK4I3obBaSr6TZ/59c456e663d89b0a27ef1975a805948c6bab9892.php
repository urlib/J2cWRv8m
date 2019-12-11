<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: groups.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){
	case 'group_create':

		if($task =='group_create'){
			form_auth(gpc('formhash','P',''),formhash());

			$group_name = trim(gpc('group_name','P',''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(checklength($group_name,2,100)){
				$error = true;
				$sysmsg[] = __('group_name_error');
			}
			$rs = $db->fetch_one_array("select count(*) as total from {$tpf}groups where group_name='$group_name'");
			if($rs['total'] >0){
				$error = true;
				$sysmsg[] = __('group_name_exists');
			}
			unset($rs);
			if(!$error){
				$rs = $db->fetch_one_array("select gid from {$tpf}groups order by gid desc limit 1");
				$next_gid = $rs['gid'] ? (int)$rs['gid']+1 : 5;
				$ins = array(
				'gid' => $next_gid,
				'group_type' => 0,
				'group_name' => $group_name,
				);
				$db->query("insert into {$tpf}groups set ".$db->sql_array($ins).";");
				redirect(urr(ADMINCP,"item=groups&action=index"),'',0);

			}else{
				redirect('back',$sysmsg);
			}
		}else{
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'group_setting':
		$gid = (int)gpc('gid','GP',0);

		if($task =='group_setting'){
			form_auth(gpc('formhash','P',''),formhash());

			$max_flow_down = trim(gpc('max_flow_down','P',''));
			$max_flow_view = trim(gpc('max_flow_view','P',''));
			$max_storage = strtoupper(trim(gpc('max_storage','P','')));
			$max_filesize = trim(gpc('max_filesize','P',''));
			$group_file_types = trim(gpc('group_file_types','P',''));
			$max_folders = (int)gpc('max_folders','P',0);
			$max_files = (int)gpc('max_files','P',0);
			$can_share = (int)gpc('can_share','P',0);
			$secs_loading = (int)gpc('secs_loading','P',0);
			$server_ids = gpc('server_ids','P',array());

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			for($i=0;$i<count($server_ids);$i++){
				$server_str .= $server_ids[$i].',';
			}
			$server_str = $server_str ? substr($server_str,0,-1) : 0;
			if(!$error){
				$ins = array(
				'max_flow_down' => $max_flow_down,
				'max_flow_view' => $max_flow_view,
				'max_storage' => $max_storage,
				'max_filesize' => $max_filesize,
				'group_file_types' => $group_file_types,
				'max_folders' => $max_folders,
				'max_files' => $max_files,
				'can_share' => $can_share,
				'secs_loading' => $secs_loading,
				'server_ids' => $server_str,
				);
				$db->query("update {$tpf}groups set ".$db->sql_array($ins)." where gid='$gid';");
				group_settings_cache();

				if(!$can_share){
					$db->query_unbuffered("update {$tpf}files set in_share=0 where userid in (select userid from {$tpf}users where gid='$gid')");
				}

				$sysmsg[] = __('group_setting_success');
				redirect(urr(ADMINCP,"item=groups&action=index"),$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}
		}else{
			$group_set = $db->fetch_one_array("select * from {$tpf}groups where gid='$gid'");
			if(display_plugin('multi_server','open_multi_server_plugin',$settings['open_multi_server'],0)){
				$q = $db->query("select * from {$tpf}servers where server_closed=0 order by server_id");
				$server_arr = array();
				while($rs = $db->fetch_array($q)){
					$server_arr[] = $rs;
				}
				$db->free($q);
				unset($rs);
			}else{
				$server_arr[0]['server_id'] = 1;
				$server_arr[0]['server_name'] = 'Local Server';
			}
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'group_modify':
		$gid = (int)gpc('gid','GP',0);

		if($task =='group_modify'){
			form_auth(gpc('formhash','P',''),formhash());

			$group_name = trim(gpc('group_name','P',''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(checklength($group_name,2,100)){
				$error = true;
				$sysmsg[] = __('group_name_error');
			}
			$rs = $db->fetch_one_array("select count(*) as total from {$tpf}groups where group_name='$group_name' and gid<>'$gid'");
			if($rs['total'] >0){
				$error = true;
				$sysmsg[] = __('group_name_exists');
			}
			unset($rs);

			if(!$error){
				$db->query("update {$tpf}groups set group_name='$group_name' where gid='$gid'");
				group_settings_cache();
				redirect(urr(ADMINCP,"item=groups&action=index"),'',0);
			}else{
				redirect('back',$sysmsg);
			}

		}else{
			$rs = $db->fetch_one_array("select gid,group_name from {$tpf}groups where gid='$gid'");
			if($rs){
				$group_name = $rs['group_name'];
			}
			unset($rs);
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'group_delete':
		if($settings['online_demo']){
			$error = true;
			$sysmsg[] = __('online_demo_deny');
		}
		if(!$error){
			$gid = (int)gpc('gid','G',0);
			$rs = $db->fetch_one_array("select count(*) as total from {$tpf}groups where gid='$gid' and group_type<>1");

			if($rs['total'] >0){
				$db->query("update {$tpf}users set gid=4 where gid='$gid'");
				$db->query("delete from {$tpf}groups where gid='$gid' and group_type<>1");
				$sysmsg[] = __('group_delete_success');
			}
			unset($rs);
			group_settings_cache();
			redirect(urr(ADMINCP,"item=groups&action=index"),$sysmsg);
		}else{
			redirect('back',$sysmsg);
		}
		break;

	case 'index':
		$q = $db->query("select gid,group_name,group_type,server_ids from {$tpf}groups order by gid asc");
		$groups = array();
		while($rs = $db->fetch_array($q)){
			$rs['user_count'] = (int)@$db->result_first("select count(*) as user_count from {$tpf}users where gid='".$rs['gid']."'");
			if(display_plugin('multi_server','open_multi_server_plugin',$settings['open_multi_server'],0)){
				if(strpos($rs['server_ids'],',')){
					$group_server = __('random_server');
				}else{
					$group_server = @$db->result_first("select server_name from {$tpf}servers where server_id='{$rs['server_ids']}'");
				}
			}
			$rs['group_server'] = $group_server ? trim($group_server) : 'Local Server';
			$rs['group_type_txt'] = $rs['group_type'] ? __('group_type_inner') : __('group_type_custom');
			$rs['is_admin'] = ($rs['gid']==1) ? 1 : 0;
			$rs['a_view'] = urr(ADMINCP,"item=users&menu=user&action=index&gid={$rs['gid']}");
			$rs['a_group_setting'] = urr(ADMINCP,"item=groups&menu=user&action=group_setting&gid={$rs['gid']}");
			$rs['a_group_modify'] = urr(ADMINCP,"item=groups&menu=user&action=group_modify&gid={$rs['gid']}");
			$rs['a_group_delete'] = urr(ADMINCP,"item=groups&menu=user&action=group_delete&gid={$rs['gid']}");
			$groups[] = $rs;
		}
		$db->free($q);
		unset($rs);
		require_once template_echo($item,$admin_tpl_dir,'',1);
		break;

	default:
		redirect(urr(ADMINCP,"item=groups&action=index"),'',0);
}
?>