<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: cache.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){
	case 'search_index':
		if($task =='search_index'){
			form_auth(gpc('formhash','P',''),formhash());
			$searchids = gpc('searchids','P',array(''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			$ids_arr = get_ids_arr($searchids,__('please_select_operation_index'));
			if($ids_arr[0]){
				$error = true;
				$sysmsg[] = $ids_arr[1];
			}else{
				$file_str = $ids_arr[1];
			}
			if(!$error){
				$db->query_unbuffered("delete from {$tpf}search_index where searchid in ($file_str)");
				$sysmsg[] = __('delete_search_cache_success');
				redirect(urr(ADMINCP,"item=$item&action=$action"),$sysmsg);				
			}else{
				redirect('back',$sysmsg);	
			}
		}else{
			$q = $db->query("select * from {$tpf}search_index order by searchid desc");
			$rs = $db->fetch_one_array("select count(*) as total_num from {$tpf}search_index");
			$total_num = $rs['total_num'];
			$start_num = ($pg-1) * $perpage;

			$q = $db->query("select * from {$tpf}search_index order by searchid desc limit $start_num,$perpage");
			while($rs = $db->fetch_array($q)){
				$C['search_list'][] = $rs;
			}
			$db->free($q);
			unset($rs);
			$page_nav = multi($total_num, $perpage, $pg, urr(ADMINCP,"item=$item&action=$action"));
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;
	case 'truncate':
		$db->query_unbuffered("truncate table {$tpf}search_index;");
		$sysmsg[] = __('truncate_search_index_success');
		redirect('back',$sysmsg);
		break;
	case 'update':

		if($task =='update'){
			form_auth(gpc('formhash','P',''),formhash());

			$datas = gpc('datas','P',array());

			if(!count($datas)){
				$error = true;
				$sysmsg[] = __('pls_select_target');
			}
			if(!$error){
				if($datas['tpl'] =='tpl'){

					update_tpl($user_tpl_dir);
					update_tpl($admin_tpl_dir);

					$sysmsg[] = __('tpl_cache_update_success');

				}
				if($datas['cache'] =='cache'){
					$stats['user_folders_count'] = (int)@$db->result_first("select count(*) from {$tpf}folders");

					$stats['user_files_count'] = (int)@$db->result_first("select count(*) from {$tpf}files where is_public=0");

					$stats['users_count'] = (int)@$db->result_first("select count(*) from {$tpf}users ");

					$stats['users_locked_count'] = (int)@$db->result_first("select count(*) from {$tpf}users where is_locked=1");

					$stats['extract_code_count'] = (int)@$db->result_first("select count(*) from {$tpf}extracts");

					$stats['all_files_count'] = (int)@$db->result_first("select count(*) from {$tpf}files");

					$storage_count_tmp = (float)@$db->result_first("select sum(file_size) from {$tpf}files where is_public=0");

					$public_storage_count_tmp = (float)@$db->result_first("select sum(file_size) from {$tpf}files where is_public=1");
					$stats['user_storage_count'] = get_size($storage_count_tmp);
					$stats['public_storage_count'] = get_size($public_storage_count_tmp);
					$stats['total_storage_count'] = get_size($storage_count_tmp+$public_storage_count_tmp);
					$stats['users_open_count'] = $stats['users_count']-$stats['users_locked_count'];
					$stats['stat_time'] = $timestamp;

					stats_cache($stats);
					group_settings_cache();
					stats_cache();
					settings_cache();

					$sysmsg[] = __('data_cache_update_success');
				}
				redirect(urr(ADMINCP,"item=cache&action=$action"),$sysmsg);

			}else{
				redirect('back',$sysmsg);
			}

		}else{
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	default:
		redirect(urr(ADMINCP,"item=cache&action=update"),'',0);
}
function tpl_list($tpl_dir){
	$tpl_arr = array();
	if ($fp = opendir($tpl_dir)) {
		while(($file = readdir($fp)) !== false) {
			if(get_extension($file) == 'html'){
				if(substr($file,0,1) != '.' && $file != 'images'){
					$tpl_arr[] = str_replace('.tpl.html','',$file);
				}
			}
		}
		closedir($fp);
	}
	return $tpl_arr;
}
function update_tpl($tpl_name){
	$tpl_dir = PHPDISK_ROOT.$tpl_name;
	$tpl_arr_t = tpl_list($tpl_dir);
	sort($tpl_arr_t);
	reset($tpl_arr_t);
	for($i=0;$i<count($tpl_arr_t);$i++){
		template_echo($tpl_arr_t[$i],$tpl_name);
	}

}
?>