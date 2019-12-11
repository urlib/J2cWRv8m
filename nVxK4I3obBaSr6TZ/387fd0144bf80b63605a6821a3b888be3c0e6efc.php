<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: files.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){
	case 'index':

		$view = trim(gpc('view','GP',''));
		$uid = (int)gpc('uid','GP',0);

		if($task =='check_public'){
			form_auth(gpc('formhash','P',''),formhash());

			$file_ids = gpc('file_ids','P',array(''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			$ids_arr = get_ids_arr($file_ids,__('please_select_check_files'));
			if($ids_arr[0]){
				$error = true;
				$sysmsg[] = $ids_arr[1];
			}else{
				$file_str = $ids_arr[1];
			}
			if(!$error){
				$db->query_unbuffered("update {$tpf}files set is_checked=1 where file_id in ($file_str)");
				$sysmsg[] = __('check_public_success');
				redirect(urr(ADMINCP,"item=files&action=index&view=checked_file"),$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}

		}elseif($task =='file_to_locked'){
			form_auth(gpc('formhash','P',''),formhash());

			$file_ids = gpc('file_ids','P',array(''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			$ids_arr = get_ids_arr($file_ids,__('please_select_check_files'));
			if($ids_arr[0]){
				$error = true;
				$sysmsg[] = $ids_arr[1];
			}else{
				$file_str = $ids_arr[1];
			}
			if(!$error){
				$db->query_unbuffered("update {$tpf}files set is_locked=1 where file_id in ($file_str)");
				$sysmsg[] = __('file_to_locked_success');
				redirect($_SERVER['HTTP_REFERER'],$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}

		}elseif($task == 'file_to_unlocked'){
			form_auth(gpc('formhash','P',''),formhash());

			$file_ids = gpc('file_ids','P',array(''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			$ids_arr = get_ids_arr($file_ids,__('please_select_check_files'));
			if($ids_arr[0]){
				$error = true;
				$sysmsg[] = $ids_arr[1];
			}else{
				$file_str = $ids_arr[1];
			}
			if(!$error){
				$db->query_unbuffered("update {$tpf}files set is_locked=0 where file_id in ($file_str)");
				$sysmsg[] = __('file_to_unlocked_success');
				redirect($_SERVER['HTTP_REFERER'],$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}

		}elseif($task =='delete_file_complete'){
			form_auth(gpc('formhash','P',''),formhash());

			$file_ids = gpc('file_ids','P',array(''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			$ids_arr = get_ids_arr($file_ids,__('please_select_delete_files'));
			if($ids_arr[0]){
				$error = true;
				$sysmsg[] = $ids_arr[1];
			}else{
				$file_str = $ids_arr[1];
			}
			if(!$error){
				delete_phpdisk_file("select * from {$tpf}files where file_id in($file_str)");
				$db->query_unbuffered("delete from {$tpf}files where file_id in ($file_str)");
				$sysmsg[] = __('file_delete_success');
				redirect($_SERVER['HTTP_REFERER'],$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}

		}else{
			$sql_ext = '';
			switch($view){
				case 'mydisk_recycle':
					$sql_ext = " where in_recycle=1 and is_public=0";
					break;
				case 'user':
					$sql_ext = " where f.userid='$uid'";
					break;
				default:
					$sql_ext = " where is_public=0 and in_recycle=0 and is_public=0";
			}
			$rs = $db->fetch_one_array("select count(*) as total_num from {$tpf}files f {$sql_ext}");
			$total_num = $rs['total_num'];
			$start_num = ($pg-1) * $perpage;

			$q = $db->query("select f.*,u.username from {$tpf}files f,{$tpf}users u {$sql_ext} and f.userid=u.userid order by file_id desc limit $start_num,$perpage");
			$files_array = array();
			while($rs = $db->fetch_array($q)){
				$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
				$rs['file_thumb'] = get_file_thumb($rs);
				$rs['file_name_all'] = $rs['file_name'].$tmp_ext;
				$rs['file_name'] = cutstr($rs['file_name'].$tmp_ext,35);
				$rs['a_user_view'] = urr(ADMINCP,"item=files&action=$action&view=user&uid=".$rs['userid']);
				$rs['file_size'] = get_size($rs['file_size']);
				$rs['file_time'] = date("Y-m-d H:i:s",$rs['file_time']);
				$rs['a_downfile'] = urr("downfile","file_id={$rs['file_id']}&file_key={$rs['file_key']}");
				$rs['a_viewfile'] = urr("viewfile","file_id={$rs['file_id']}");
				$rs['a_recycle_delete'] = urr(ADMINCP,"item=files&action=recycle_delete&file_id={$rs['file_id']}");
				$rs['status_txt'] = $rs['is_locked'] ? "<span class=\"txtred\">".__('locked_status')."</span>" : "<span class=\"txtblue\">".__('common_status')."</span>";
				$rs[in_yun] = $rs[yun_fid] ? 'class="txtblue"' : '';
				$files_array[] = $rs;
			}
			$db->free($q);
			unset($rs);
			$page_nav = multi($total_num, $perpage, $pg, urr(ADMINCP,"item=$item&action=$action&view=$view&uid=$uid"));

			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'search':
		if($task =='check_public'){
			form_auth(gpc('formhash','P',''),formhash());

			$file_ids = gpc('file_ids','P',array(''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			$ids_arr = get_ids_arr($file_ids,__('please_select_check_files'));
			if($ids_arr[0]){
				$error = true;
				$sysmsg[] = $ids_arr[1];
			}else{
				$file_str = $ids_arr[1];
			}
			if(!$error){
				$db->query_unbuffered("update {$tpf}files set is_checked=1 where file_id in ($file_str)");

				$sysmsg[] = __('check_public_success');
				redirect(urr(ADMINCP,"item=files&action=index&view=checked_file"),$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}

		}elseif($task =='file_to_locked'){
			form_auth(gpc('formhash','P',''),formhash());

			$file_ids = gpc('file_ids','P',array(''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			$ids_arr = get_ids_arr($file_ids,__('please_select_check_files'));
			if($ids_arr[0]){
				$error = true;
				$sysmsg[] = $ids_arr[1];
			}else{
				$file_str = $ids_arr[1];
			}
			if(!$error){
				$db->query_unbuffered("update {$tpf}files set is_locked=1 where file_id in ($file_str)");
				$sysmsg[] = __('file_to_locked_success');
				redirect($_SERVER['HTTP_REFERER'],$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}

		}elseif($task == 'file_to_unlocked'){
			form_auth(gpc('formhash','P',''),formhash());

			$file_ids = gpc('file_ids','P',array(''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			$ids_arr = get_ids_arr($file_ids,__('please_select_check_files'));
			if($ids_arr[0]){
				$error = true;
				$sysmsg[] = $ids_arr[1];
			}else{
				$file_str = $ids_arr[1];
			}
			if(!$error){
				$db->query_unbuffered("update {$tpf}files set is_locked=0 where file_id in ($file_str)");
				$sysmsg[] = __('file_to_unlocked_success');
				redirect($_SERVER['HTTP_REFERER'],$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}

		}elseif($task =='delete_file_complete'){
			form_auth(gpc('formhash','P',''),formhash());

			$file_ids = gpc('file_ids','P',array(''));

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			$ids_arr = get_ids_arr($file_ids,__('please_select_delete_files'));
			if($ids_arr[0]){
				$error = true;
				$sysmsg[] = $ids_arr[1];
			}else{
				$file_str = $ids_arr[1];
			}
			if(!$error){
				delete_phpdisk_file("select * from {$tpf}files where file_id in($file_str)");
				$db->query_unbuffered("delete from {$tpf}files where file_id in ($file_str)");
				$sysmsg[] = __('file_delete_success');
				redirect($_SERVER['HTTP_REFERER'],$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}
		}else{
			$word = trim(gpc('word','G',''));
			$word_str = str_replace('　',' ',replace_inject_str($word));
			$arr = explode(' ',$word_str);
      $str = '';
			if(count($arr)>1){
				for($i=0;$i<count($arr);$i++){
					if(trim($arr[$i]) <> ''){
						$str .= " (file_name like '%{$arr[$i]}%' or file_extension like '%{$arr[$i]}%') and";
					}
				}
				$str = substr($str,0,-3);
				$sql_keyword = " (".$str.")";

			}else{
				$sql_keyword = " (file_name like '%{$word_str}%' or file_extension like '%{$word_str}%')";
			}
			$sql_do = " {$tpf}files fl,{$tpf}users u where fl.userid=u.userid and {$sql_keyword}";

			$rs = $db->fetch_one_array("select count(*) as total_num from {$sql_do}");
			$total_num = $rs['total_num'];
			$start_num = ($pg-1) * $perpage;

			$q = $db->query("select fl.*,u.username from {$sql_do} order by file_id desc limit $start_num,$perpage");
			$files_array = array();
			while($rs = $db->fetch_array($q)){
				$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
				$rs['file_name_all'] = $rs['file_name'].$tmp_ext;
				$rs['file_name'] = str_replace($word,'<span class="txtred">'.$word.'</span>',cutstr($rs['file_name'].$tmp_ext,35));
				$rs['a_user_view'] = urr(ADMINCP,"item=files&action=index&view=user&uid=".$rs['userid']);
				$rs['file_size'] = get_size($rs['file_size']);
				$rs['file_time'] = custom_time("Y-m-d",$rs['file_time']);
				$rs['a_downfile'] = urr("downfile","file_id={$rs['file_id']}&file_key={$rs['file_key']}");
				$rs['a_viewfile'] = urr("viewfile","file_id={$rs['file_id']}");
				$rs['a_recycle_delete'] = urr(ADMINCP,"item=files&action=recycle_delete&file_id={$rs['file_id']}");
				$rs['status_txt'] = $rs['is_locked'] ? "<span class=\"txtred\">".__('locked_status')."</span>" : "<span class=\"txtblue\">".__('common_status')."</span>";
				$rs[in_yun] = $rs[yun_fid] ? 'class="txtblue"' : '';
				$files_array[] = $rs;
			}
			$db->free($q);
			unset($rs);
			$page_nav = multi($total_num, $perpage, $pg, urr(ADMINCP,"item=$item&action=search&word=".rawurlencode($word).""));

			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'recycle_delete':
		if($settings['online_demo']){
			$error = true;
			$sysmsg[] = __('online_demo_deny');
		}
		if(!$error){
			$file_id = (int)gpc('file_id','G',0);
			delete_phpdisk_file("select * from {$tpf}files where file_id='$file_id'");
			$db->query_unbuffered("delete from {$tpf}files where file_id='$file_id'");
			$sysmsg[] = __('file_delete_success');
			redirect(urr(ADMINCP,"item=files&action=index&view=public_recycle"),$sysmsg);
		}else{
			redirect('back',$sysmsg);
		}
		break;

}

?>