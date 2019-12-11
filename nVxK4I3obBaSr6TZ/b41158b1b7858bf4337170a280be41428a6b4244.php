<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: public.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){
	case 'add_cate':

		if($task =='add_cate'){
			form_auth(gpc('formhash','P',''),formhash());

			$cate_name = trim(gpc('cate_name','P',''));
			$pid = (int)gpc('pid','P',0);
			$is_hidden = (int)gpc('is_hidden','P',0);

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(checklength($cate_name,1,60)){
				$error = true;
				$sysmsg[] = __('cate_name_error');
			}
			$rs = $db->fetch_one_array("select count(*) as total from {$tpf}categories where cate_name='$cate_name'");
			if($rs['total']){
				$error = true;
				$sysmsg[] = __('cate_name_exists');
			}
			if(!$error){
				$ins = array(
				'cate_name' => $cate_name,
				'pid' => $pid,
				'is_hidden' => $is_hidden,
				);
				$db->query("insert into {$tpf}categories set ".$db->sql_array($ins).";");
				$sysmsg[] = __('cate_add_success');
				redirect(urr(ADMINCP,"item=$item&action=category"),$sysmsg);

			}else{
				redirect('back',$sysmsg);
			}
		}else{
			$q = $db->query("select * from {$tpf}categories where pid=0 order by show_order asc,cate_id asc");
			$cate_arr = array();
			while($rs = $db->fetch_array($q)){
				$cate_arr[] = $rs;
			}
			$db->free($q);
			unset($rs);
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'modify_cate':
		$cate_id = (int)gpc('cate_id','GP',0);

		if($task =='modify_cate'){
			form_auth(gpc('formhash','P',''),formhash());

			$cate_name = trim(gpc('cate_name','P',''));
			$pid = (int)gpc('pid','P',0);
			$is_hidden = (int)gpc('is_hidden','P',0);

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(checklength($cate_name,1,60)){
				$error = true;
				$sysmsg[] = __('cate_name_error');
			}
			$rs = $db->fetch_one_array("select count(*) as total from {$tpf}categories where cate_name='$cate_name' and cate_id<>'$cate_id'");
			if($rs['total']){
				$error = true;
				$sysmsg[] = __('cate_name_exists');
			}
			if(!$error){
				$ins = array(
				'cate_name' => $cate_name,
				'pid' => $pid,
				'is_hidden' => $is_hidden,
				);
				$db->query_unbuffered("update {$tpf}categories set ".$db->sql_array($ins)." where cate_id='$cate_id' and cate_id<>'$pid';");
				if($pid){
					$db->query_unbuffered("update {$tpf}files set subcate_id='$cate_id',cate_id='$pid' where cate_id='$cate_id'");
				}else{
					$db->query_unbuffered("update {$tpf}files set subcate_id='0',cate_id='$cate_id' where subcate_id='$cate_id'");
				}
				$sysmsg[] = __('cate_modify_success');
				redirect(urr(ADMINCP,"item=$item&action=category"),$sysmsg);

			}else{
				redirect('back',$sysmsg);
			}
		}else{
			$q = $db->query("select * from {$tpf}categories where pid=0 order by show_order asc,cate_id asc");
			$cate_arr = array();
			while($rs = $db->fetch_array($q)){
				$cate_arr[] = $rs;
			}
			$db->free($q);
			unset($rs);

			$rs = $db->fetch_one_array("select * from {$tpf}categories where cate_id='$cate_id'");
			if($rs){
				$cate_name = $rs['cate_name'];
				$pid = $rs['pid'];
				$is_hidden = $rs['is_hidden'];
			}
			unset($rs);
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'category':

		if($task =='update'){
			form_auth(gpc('formhash','P',''),formhash());

			$show_order = gpc('show_order','P',array());
			$cate_ids = gpc('cate_ids','P',array());
			$cate_names = gpc('cate_names','P',array());

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(!$error){
				for($i =0;$i<count($cate_ids);$i++){
					$title = trim(replace_js($cate_names[$i]));
					if($title){
						$db->query_unbuffered("update {$tpf}categories set show_order='".(int)$show_order[$i]."',cate_name='$title' where cate_id='".(int)$cate_ids[$i]."'");
					}
				}
				redirect(urr(ADMINCP,"item=$item&action=category"),'',0);
			}else{
				redirect('back',$sysmsg);
			}

		}else{
			$q = $db->query("select * from {$tpf}categories order by show_order asc, cate_id asc");
			$cates = array();
			while($rs = $db->fetch_array($q)){
				$cates[] = $rs;
			}
			$db->free($q);
			unset($rs);

			for($i = 0; $i < count($cates); $i++){
				if($cates[$i]['pid']==0){
					$total = @$db->result_first("select count(*) from {$tpf}files where (cate_id='{$cates[$i]['cate_id']}' or subcate_id='{$cates[$i]['cate_id']}') and cate_id>0 and is_public=1 and is_public=1 and userid>0");
					$a_modify = urr(ADMINCP,"item=$item&menu=file&action=modify_cate&cate_id={$cates[$i]['cate_id']}");
					$a_cate_href = urr("public","pid={$cates[$i]['pid']}&cate_id={$cates[$i]['cate_id']}");
					$a_del_cate = urr(ADMINCP,"item=$item&menu=file&action=del_cate&cate_id={$cates[$i]['cate_id']}");
					$is_hidden = $cates[$i]['is_hidden'] ? '<span class="txtgray">('.__('is_hidden').')</span>' : '';

					$cate_list .= '<tr>';
					$cate_list .= '	<td>';
					$cate_list .= '	<input type="text" name="show_order[]" value="'.$cates[$i]['show_order'].'" style="width:20px; text-align:center" maxlength="2" />';
					$cate_list .= '	<input type="hidden" name="cate_ids[]" value="'.$cates[$i]['cate_id'].'" />';
					$cate_list .= '	<input type="text" name="cate_names[]" value="'.$cates[$i]['cate_name'].'" />&nbsp;'.$is_hidden.'</td>';
					$cate_list .= '	<td align="center">';
					$cate_list .= '	<a href="'.$a_cate_href.'" target="_blank">'.$total.'</a>';
					$cate_list .= '	</td>';
					$cate_list .= '	<td align="right">';
					$cate_list .= '	<a href="'.$a_modify.'">'.__('modify').'</a>&nbsp;';
					$cate_list .= '	<a href="'.$a_del_cate.'" onclick="return confirm(\''.__('del_category_confirm').'\');">'.__('delete').'</a></td>';
					$cate_list .= '</tr>';

					for($j = 0; $j < count($cates); $j++){
						if($cates[$j]['pid']>0 && $cates[$j]['pid'] == $cates[$i]['cate_id']){
							$total = @$db->result_first("select count(*) from {$tpf}files where (cate_id='{$cates[$j]['cate_id']}' or subcate_id='{$cates[$j]['cate_id']}') and cate_id>0 and is_public=1 and is_public=1 and userid>0");
							$a_modify = urr(ADMINCP,"item=$item&menu=file&action=modify_cate&cate_id={$cates[$j]['cate_id']}");
							$a_cate_href = urr("public","pid={$cates[$j]['pid']}&cate_id={$cates[$j]['cate_id']}");
							$a_del_cate = urr(ADMINCP,"item=$item&menu=file&action=del_cate&cate_id={$cates[$j]['cate_id']}");
							$is_hidden = $cates[$j]['is_hidden'] ? '<span class="txtgray">('.__('is_hidden').')</span>' : '';

							$cate_list .= '<tr>';
							$cate_list .= '	<td>';
							$cate_list .= '	&nbsp;&nbsp;&nbsp;&nbsp;<input type="text" name="show_order[]" value="'.$cates[$j]['show_order'].'" style="width:20px; text-align:center" maxlength="2" />';
							$cate_list .= '	<input type="hidden" name="cate_ids[]" value="'.$cates[$j]['cate_id'].'" />';
							$cate_list .= '	<input type="text" name="cate_names[]" value="'.$cates[$j]['cate_name'].'" />'.$is_hidden.'</td>';
							$cate_list .= '	<td align="center">';
							$cate_list .= '	<a href="'.$a_cate_href.'" target="_blank">'.$total.'</a>';
							$cate_list .= '	</td>';
							$cate_list .= '	<td align="right">';
							$cate_list .= '	<a href="'.$a_modify.'">'.__('modify').'</a>&nbsp;';
							$cate_list .= '	<a href="'.$a_del_cate.'" onclick="return confirm(\''.__('del_category_confirm').'\');">'.__('delete').'</a></td>';
							$cate_list .= '</tr>';

						}
					}
				}
			}
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}

		break;

	case 'del_cate':
		if($settings['online_demo']){
			$error = true;
			$sysmsg[] = __('online_demo_deny');
		}
		if(!$error){
			$cate_id = (int)gpc('cate_id','G',0);
			if($cate_id){
				$db->query_unbuffered("delete from {$tpf}files where cate_id='$cate_id' and is_public=1");
				$db->query_unbuffered("delete from {$tpf}categories where cate_id='$cate_id'");
			}
			$sysmsg[] = __('del_cate_success');
			redirect(urr(ADMINCP,"item=$item&action=category"),$sysmsg);
		}else{
			redirect('back',$sysmsg);
		}
		break;

	case 'viewfile':
		$view = trim(gpc('view','GP',''));
		if($task){
			$file_ids = gpc('file_ids','P',array());

			$ids_arr = get_ids_arr($file_ids,__('please_select_operation_files'));
			if($ids_arr[0]){
				$error = true;
				$sysmsg[] = $ids_arr[1];
			}else{
				$file_str = $ids_arr[1];
			}
		}
		if($task == 'check_file'){
			form_auth(gpc('formhash','P',''),formhash());

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(!$error){
				$db->query_unbuffered("update {$tpf}files set is_checked=1 where is_public=1 and file_id in ($file_str)");
				$sysmsg[] = __('check_file_success');
				redirect($_SERVER['HTTP_REFERER'],$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}
		}elseif($task == 'delete'){
			form_auth(gpc('formhash','P',''),formhash());

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(!$error){
				delete_phpdisk_file("select * from {$tpf}files where is_public=1 and file_id in ($file_str)");
				$db->query_unbuffered("delete from {$tpf}files where is_public=1 and file_id in ($file_str)");

				$sysmsg[] = __('delete_file_success');
				redirect($_SERVER['HTTP_REFERER'],$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}
		}else{
			$sql_ext = "";
			switch($view){
				case 'temp_file':
					$sql_ext = " where is_public=1 and cate_id=0 ";
					break;
				default:
					$sql_ext = " where is_public=1 and cate_id>0";
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
				$rs['a_space'] = urr("space","username=".rawurlencode($rs['username']));
				$rs['file_size'] = get_size($rs['file_size']);
				$rs['file_time'] = date("Y-m-d H:i:s",$rs['file_time']);
				$rs['a_downfile'] = urr("downfile","file_id={$rs['file_id']}&file_key={$rs['file_key']}");
				$rs['a_viewfile'] = urr("viewfile","file_id={$rs['file_id']}");
				$rs['a_recycle_delete'] = urr(ADMINCP,"item=files&menu=file&action=recycle_delete&file_id={$rs['file_id']}");
				$rs['status_txt'] = $rs['is_checked'] ? '<span class="txtblue">'.__('checked').'</span>' : '<span class="txtred">'.__('unchecked').'</span>';
				$rs[in_yun] = $rs[yun_fid] ? 'class="txtblue"' : '';
				$files_array[] = $rs;
			}
			$db->free($q);
			unset($rs);
			$page_nav = multi($total_num, $perpage, $pg, urr(ADMINCP,"item=$item&menu=file&action=$action&view=$view"));
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	default:

		if($task == 'update'){
			form_auth(gpc('formhash','P',''),formhash());

			$setting = array(
			'check_public_file' => 0,
			'file_to_public_checked' => 0,		
			'show_index' => 0,
			'show_public' => 0,
			);
			$settings = gpc('setting','P',$setting);

			if(!$error){

				settings_cache($settings);

				$sysmsg[] = __('public_update_success');
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