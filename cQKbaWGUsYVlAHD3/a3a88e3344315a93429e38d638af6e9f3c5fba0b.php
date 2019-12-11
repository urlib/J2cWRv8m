<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: ajax.php 35 2014-07-07 02:54:55Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

include "includes/commons.inc.php";

switch($action){
	case 'digg':
		$file_id = (int)gpc('file_id','G',0);
		$dig_type = (int)gpc('dig_type','G',0);
		$digg_cookie = gpc("phpdisk_digg_{$file_id}",'C','');
		if(!$digg_cookie){
			$rs = $db->fetch_one_array("select good_count,bad_count,userid from {$tpf}files where file_id='$file_id' limit 1");
			if($rs){
				$good_count = (int)$rs['good_count']+1;
				$bad_count = (int)$rs['bad_count']+1;
				$userid = (int)$rs['userid'];
			}
			unset($rs);
			if($dig_type ==1){
				$db->query_unbuffered("update {$tpf}files set good_count=good_count+1 where file_id='$file_id'");
			}elseif($dig_type ==2){
				$db->query_unbuffered("update {$tpf}files set bad_count=bad_count+1 where file_id='$file_id'");
			}
			pd_setcookie("phpdisk_digg_{$file_id}", $file_id, $timestamp+3600);
			echo "var re=new Array();re[0]=".$file_id.";re[1]=".$dig_type.";re[2]=\"success\";re[3]=\"".__('vote_success')."\";";
		}else{
			echo "var re=new Array();re[0]=".$file_id.";re[1]=".$dig_type.";re[2]=\"fail\";re[3]=\"".__('cannot_same_vote')."\";";
		}
		break;
	case 'down_process':
		$temp_ip = base64_decode(gpc('down_ip','C',''));
		$file_id = (int)gpc('file_id','G',0);
		$userid = $db->result_first("select userid from {$tpf}files where file_id='$file_id'");
		$exp_down = (int)$settings['exp_down'];
		$db->query_unbuffered("update {$tpf}users set exp=exp+$exp_down where userid='$pd_uid'");

		$exp_down_my = (int)$settings['exp_down_my'];
		$db->query_unbuffered("update {$tpf}users set exp=exp+$exp_down_my where userid='$userid'");

		if($settings['credit_open'] && $pd_uid!=$userid){
			$credit = $settings['credit_open'] ? (int)$settings['credit_down'] : 0;
			$credit_my = $settings['credit_open'] ? (int)$settings['credit_down_my'] : 0;
			$pd_credit = (int)$db->result_first("select credit from {$tpf}users where userid='$pd_uid' limit 1");
			if($pd_credit && $pd_credit>=$credit){
				$db->query_unbuffered("update {$tpf}users set credit=credit-{$credit} where userid='$pd_uid'");
			}
			$db->query_unbuffered("update {$tpf}users set credit=credit+{$credit_my} where userid='$userid'");
			unset($rs);
		}

		if(display_plugin('filelog','open_filelog_plugin',($settings['open_filelog'] && $settings['open_down_filelog']),0)){
			$username = @$db->result_first("select username from {$tpf}users where userid='$userid' limit 1");
			$down_username = @$db->result_first("select username from {$tpf}users where userid='$pd_uid' limit 1");
			$down_username = $down_username ? $down_username : '-';
			$log_format = $file_name.'|'.get_size($file_size).'|'.__('download').'|'.$username.'|'.$down_username.'|'.date("Y-m-d H:i:s").'|'.$onlineip;
			all_file_logs($log_format);
			my_file_down_logs($log_format,$userid);
		}
		if($temp_ip!=get_ip()){
			pd_setcookie('down_ip',base64_encode(get_ip()),86400);
			$db->query_unbuffered("update {$tpf}files set file_downs=file_downs+1,file_last_view='$timestamp' where file_id='$file_id'");
		}
		echo 'true';
		break;
	case 'uploadCloud':
		$folder_id = (int)gpc('folder_id','P',0);
		$folder_id = $folder_id ? $folder_id : -1;
		$data = trim(gpc('data','P',''));

		$is_checked = $is_public ? ($settings['check_public_file'] ? 0 :1) : 1;
		if($settings['all_file_share']){
			$in_share = 1;
		}else{
			$in_share = (int)@$db->result_first("select in_share from {$tpf}folders where userid='$pd_uid' and folder_id='$folder_id'");
		}
		if($data){
			$file_key = random(8);
			if(strpos($data,',')!==false){
				$add_sql = $msg = '';
				$arr = explode(',',$data);
				for($i=0;$i<count($arr)-1;$i++){
					$file = unserialize(base64_decode($arr[$i]));
					$file[file_id] = (int)$file[file_id];
					$file[file_size] = (int)$file[file_size];
					$file[file_description] = $db->escape(trim($file[file_description]));
					$file[file_extension] = $db->escape(trim($file[file_extension]));
					$file[file_name] = $db->escape(trim($file[file_name]));
					$report_status =0;
					$report_arr = explode(',',$settings['report_word']);
					if(count($report_arr)){
						foreach($report_arr as $value){
							if (strpos($file['file_name'],$value) !== false){
								$report_status = 2;
							}
						}
					}
					$num = @$db->result_first("select count(*) from {$tpf}files where yun_fid='{$file[file_id]}' and userid='$pd_uid'");
					if($num && $file[file_id]){
						$tmp_ext = $file[file_extension] ? '.'.$file[file_extension] : '';
						$msg .=	$file[file_name].$tmp_ext.',';
					}else{
						$add_sql .= "({$file[file_id]},'{$file[file_name]}','$file_key','{$file[file_extension]}','application/octet-stream','{$file[file_description]}','{$file[file_size]}','$timestamp','$is_checked','$in_share','$report_status','$pd_uid','$folder_id','$onlineip'),";
					}
				}
				if($add_sql){
					$add_sql = is_utf8() ? $add_sql : convert_str('utf-8','gbk',$add_sql);
					$add_sql = substr($add_sql,0,-1);
					$db->query_unbuffered("insert into {$tpf}files(yun_fid,file_name,file_key,file_extension,file_mime,file_description,file_size,file_time,is_checked,in_share,report_status,userid,folder_id,ip) values $add_sql ;");
				}
			}else{
				$file = unserialize(base64_decode($data));
				/*foreach($file as $k=>$v){
				$file[$k] = $db->escape($file[$v]);
				}*/
				$file[file_id] = (int)$file[file_id];
				$file[file_size] = (int)$file[file_size];
				$file[file_description] = $db->escape(trim($file[file_description]));
				$file[file_extension] = $db->escape(trim($file[file_extension]));
				$file[file_name] = $db->escape(trim($file[file_name]));
				$num = @$db->result_first("select count(*) from {$tpf}files where yun_fid='{$file[file_id]}' and userid='$pd_uid'");
				if($num && $file[file_id]){
					$tmp_ext = $file[file_extension] ? '.'.$file[file_extension] : '';
					$msg = $file[file_name].$tmp_ext;
				}else{
					$report_status =0;
					$report_arr = explode(',',$settings['report_word']);
					if(count($report_arr)){
						foreach($report_arr as $value){
							if (strpos($file['file_name'],$value) !== false){
								$report_status = 2;
							}
						}
					}
					$ins = array(
					'yun_fid' => $file[file_id],
					'file_name' => $file[file_name],
					'file_key' => $file_key,
					'file_extension' => $file[file_extension],
					'file_mime' => 'application/octet-stream',
					'file_description' => $file[file_description],
					'file_size' => $file['file_size'],
					'file_time' => $timestamp,
					'is_checked' => $is_checked,
					'in_share' => $in_share,
					'report_status' => $report_status,
					'userid' => $pd_uid,
					'folder_id' => $folder_id ? $folder_id : -1,
					'ip' => $onlineip,
					);
					$sql = "insert into {$tpf}files set ".$db->sql_array($ins).";";
					$db->query_unbuffered(is_utf8() ? $sql : iconv('utf-8','gbk',$sql));
				}
			}
			$msg = $msg ? '文件已存在：'.substr($msg,0,-1).',不能重复添加' : '';
			echo 'true|'.$msg;
		}else{
			echo 'false';
		}
		break;
	case 'ajax_file':
		$folder_id = (int)gpc('folder_id','P',0);
		$folder_id = $folder_id ? $folder_id : -1;

		$perpage = 30;
		$pg=1;
		$sql_do = " {$tpf}files where folder_id='$folder_id' and userid='$pd_uid' and in_recycle=0 and is_public=0";
		$rs = $db->fetch_one_array("select count(*) as total_num from {$sql_do}");
		$total_num = $rs['total_num'];
		$start_num = ($pg-1) * $perpage;

		$q = $db->query("select * from $sql_do order by file_id desc limit 30");
		$files_array = array();
		while($rs = $db->fetch_array($q)){
			$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
			$rs['file_thumb'] = get_file_thumb($rs);

			$rs['file_name_all'] = $rs['file_name'].$tmp_ext;
			$rs['file_name'] = ($action =='detail') ? cutstr($rs['file_name'].$tmp_ext,15) : cutstr($rs['file_name'].$tmp_ext,35);
			$rs['folder_icon'] = $rs['in_share'] ? 'share_folder' : 'folder';
			$rs['file_size'] = get_size($rs['file_size']);
			$rs['file_description'] = cutstr($rs['file_description'],80);
			$rs['file_time'] = custom_time("Y-m-d",$rs['file_time']);
			$rs['a_downfile'] = urr("downfile","file_id={$rs['file_id']}&file_key={$rs['file_key']}");
			$rs['a_viewfile'] = urr("viewfile","file_id={$rs['file_id']}");
			$rs['a_file_modify'] = urr("mydisk","item=files&action=file_modify&file_id={$rs['file_id']}");
			$rs['a_file_delete'] = urr("mydisk","item=files&action=file_delete&file_id={$rs['file_id']}");
			$rs['a_file_unshare'] = urr("mydisk","item=files&action=unshare_file&file_id={$rs['file_id']}");
			$rs['a_file_short_url'] = urr("mydisk","item=files&action=short_url&file_id={$rs['file_id']}");
			$rs['out_file_short_url'] = 'http://phpdisk.com/'.$rs['file_short_url'];
			$rs['file_out_link'] = $settings['phpdisk_url'].urr("viewfile","file_id={$rs['file_id']}");
			$files_array[] = $rs;
		}
		$db->free($q);
		unset($rs);
		if(count($files_array)){
			$str = '';
			foreach($files_array as $k => $v){
				$color = ($k%2 ==0) ? 'color1' :'color4';
				$str .= '<tr class="'.$color.'">';
				$str .= '	<td><input type="checkbox" name="file_ids[]" id="file_ids" value="'.$v['file_id'].'" />&nbsp;<a href="'.$v['a_downfile'].'" title="'.__('total_space').__('download').'">'.file_icon($v['file_extension']).'</a>&nbsp;';
				if($v['is_image']){
					$str .= '		<a href="'.$v['a_viewfile'].'" id="p_'.$k.'" target="_blank">'.$v['file_name'].'</a>';
					$str .= '	<span class="txtgray">'.$v['file_description'].'</span><br />';
					$str .= '<div id="c_'.$k.'" class="menu_thumb"><img src="'.$v['file_thumb'].'" /></div>';
					$str .= '<script type="text/javascript">on_menu(\'p_'.$k.'\',\'c_'.$k.'\',\'x\',\'\',\'\');</script>';
				}else{
					$str .= '		<a href="'.$v['a_viewfile'].'" target="_blank">'.$v['file_name'].'</a>';
					$str .= '	<span class="txtgray">'.$v['file_description'].'</span>';
				}
				$str .= '	</td>';
				$str .= '	<td align="center">'.$v['file_size'].'</td>';
				$str .= '	<td align="center"  class="txtgray">'.$v['file_time'].'</td>';
				$str .= '	<td align="right">';
				if($v['in_share']){
					$str .= '	<a href="javascript:;" onclick="abox(\''.$v['a_file_unshare'].'\',\''.__('file_unshare').'\',400,200);" title="'.__('file_unshare').'"><img src="images/share_file.gif" border="0" align="absmiddle" /></a>';
				}
				if($settings['open_file_outlink']){
					$str .= '	<a href="javascript:void(0);" id="pl_'.$k.'" title="'.__('out_link').'"><img src="images/ico_link.gif" border="0" align="absmiddle" /></a>';
					$str .= '	<div id="cl_'.$k.'" class="menu_thumb"><input type="text" size="30" id="file_out_link_'.$k.'" value="'.$v['file_out_link'].'" readonly title="'.__('out_link').'" /><input type="button" value="'.__('copy').'" class="btn" onclick="getId(\'file_out_link_'.$k.'\').select();copy_text(\'file_out_link_'.$k.'\');" /></div>';
					$str .= '<script type="text/javascript">on_menu(\'pl_'.$k.'\',\'cl_'.$k.'\',\'-x\',\'\',\'\');</script>';
				}
				if($settings['open_file_extract_code']){
					$str .= '	<a href="###" id="pe_'.$k.'" title="'.__('extract_code').'"><img src="images/ico_code.gif" border="0" align="absmiddle" /></a>';
					$str .= '	<div id="ce_'.$k.'" class="menu_thumb"><input type="text" size="8" value="'.$v['file_key'].'" id="file_key_'.$k.'" readonly title="'.__('extract_code').'" /><input type="button" value="'.__('copy').'" class="btn" onclick="getId(\'file_key_'.$k.'\').select();copy_text(\'file_key_'.$k.'\');" /></div>';
					$str .= '<script type="text/javascript">on_menu(\'pe_'.$k.'\',\'ce_'.$k.'\',\'-x\',\'\',\'\');</script>';
				}
				$str .= '	<a href="javascript:;" onclick="abox(\''.$v['a_file_modify'].'\',\''.__('file_modify').'\',400,280);" title="'.__('modify').'"><img src="images/edit_icon.gif" border="0" align="absmiddle" /></a>';
				$str .= '	<a href="javascript:;" onclick="abox(\''.$v['a_file_delete'].'\',\''.__('file_delete').'\',400,200);" title="'.__('delete').'"><img src="images/recycle_icon.gif" border="0" align="absmiddle" /></a>';
				$str .= '	</td>';
				$str .= '</tr>';
			}
			$page_nav = multi($total_num, $perpage, $pg, urr("mydisk","item=files&action=index&folder_node=$folder_node&folder_id=$folder_id"));
			if($page_nav){
				$str .= '<tr>';
				$str .= '	<td colspan="6">'.$page_nav.'</td>';
				$str .= '</tr>';
			}
			$option_folder_4 = get_option_folders(4);
			$pub_menu_option = get_option_public_folder();
			if(count($files_array)){
				$str .= '<tr>';
				$str .= '	<td colspan="6" class="td_line"><a href="javascript:void(0);" onclick="reverse_ids(document.file_form.file_ids);">'.__('select_all').'</a>&nbsp;&nbsp;<a href="javascript:void(0);" onclick="cancel_ids(document.file_form.file_ids);">'.__('select_cancel').'</a>&nbsp;&nbsp;';
				$str .= '	<span id="dest_folder">';
				$str .= '	<select name="dest_folder" style="width:120px">';
				$str .= '	<option value="-1" class="txtgreen">'.__('please_select').'</option>';
				$str .=	$option_folder_4;
				$str .= '	</select>&nbsp;';
				$str .= '	</span>';
				$str .= '	<span id="public_cate" style="display:none">';
				$str .= '	<select name="public_cate" style="width:120px">';
				$str .= '	<option value="-1" class="txtgreen">'.__('please_select').'</option>';
				$str .=	$pub_menu_option;
				$str .= '	</select>&nbsp;';
				$str .= '	</span>';
				$str .= '	<input type="radio" id="to_folder" name="task" value="to_folder" checked="checked" onclick="chk_folder();"/><label for="to_folder">'.__('my_folder').'</label>&nbsp;';
				$str .= '	<input type="radio" id="to_public" name="task" value="to_public" onclick="chk_public();"/><label for="to_public">'.__('to_public').'</label>&nbsp;';
				$str .= '	<input type="radio" id="to_extract" name="task" value="to_extract"/><label for="to_extract">'.__('make_extract_code').'</label>&nbsp;';
				$str .= '	<input type="radio" id="is_link_code" name="task" value="is_link_code"/><label for="is_link_code">'.__('is_link_code').'</label>&nbsp;';
				$str .= '	<input type="radio" id="to_share" name="task" value="to_share"/><label for="to_share">'.__('to_share').'</label>&nbsp;';
				$str .= '	<input type="radio" id="file_delete" name="task" value="file_delete"/><label for="file_delete"><span class="txtred">'.__('move_to_recycle').'</span></label>&nbsp;';
				$str .= '	<input type="submit" class="btn" value="'.__('btn_submit').'" onclick="return confirm(\''.__('confirm_op').'\');" />';
				$str .= '	</td>';
				$str .= '</tr>';
			}
		}
		echo $str;
		break;
}

include PHPDISK_ROOT."./includes/footer.inc.php";

?>