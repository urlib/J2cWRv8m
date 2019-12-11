<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: viewfile.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

include "includes/commons.inc.php";

$in_front = true;

$file_id = (int)gpc('file_id','GP',0);
$code = trim(gpc('code','G',''));

$rs = @$db->fetch_one_array("select * from {$tpf}files where file_id='$file_id'");
if($rs){
	$file_time = $rs[file_time];
}
unset($rs);

$file = file_data($file_id);

function file_data($file_id){
	global $db,$tpf,$settings,$file_time,$code;
	$file = $db->fetch_one_array("select * from {$tpf}files where file_id='$file_id'");
	if(!$file){
		$file['is_del'] = 1;
		$file['file_name'] = __('visited_tips');
	}else{
		$file['is_del'] = 0;
		$file_key = trim($file['file_key']);
		$file['in_extract'] = ($code==md5($file_key)) ? 1 : 0;

		$file['username'] = @$db->result_first("select username from {$tpf}users where userid='{$file['userid']}' limit 1");
		$tmp_ext = $file['file_extension'] ? '.'.$file['file_extension'] : "";
		$file_extension = $file['file_extension'];
		$file_ext = get_real_ext($file_extension);
		$store_old = $file['store_old'];
		if(display_plugin('multi_server','open_multi_server_plugin',$settings['open_multi_server'],0) && $file['server_oid'] >1){
			$rs2 = $db->fetch_one_array("select * from {$tpf}servers where server_oid='{$file['server_oid']}' limit 1");
			if($rs2){
				$file['file_thumb'] = $rs2['server_host'].$rs2['server_store_path'].'/'.$file['file_store_path'].'/'.$file['file_real_name'].'_thumb.'.$file_extension;
			}
			unset($rs2);
		}else{
			$file['file_thumb'] = $settings['file_path'].'/'.$file['file_store_path'].'/'.$file['file_real_name'].'_thumb.'.$file['file_extension'];
		}
		$file_description = $file['file_description'];
		$file['file_description'] = nl2br($file['file_description']);
		$file['a_space'] = urr("space","username=".rawurlencode($file['username']));
		$file['file_name'] = $file['file_name'].$tmp_ext;
		$file['file_size'] = get_size($file['file_size']);
		$file['file_time'] = date("Y-m-d",$file['file_time']);
		$file['credit_down'] = $file['file_credit'] ? (int)$file['file_credit'] : (int)$settings['credit_down'];
		$file['username'] = $file['username'] ? '<a href="'.$file['a_space'].'">'.$file['username'].'</a>' : __('visitor');

		$file['tags'] = get_file_tags($file_id);

		if($settings['open_file_url']){
			$file['file_view_url'] = $settings['phpdisk_url'].urr("viewfile","file_id={$file['file_id']}&file_key={$file['file_key']}");
			$file['file_html_url'] = '<a href='.$settings['phpdisk_url'].urr("viewfile","file_id={$file['file_id']}&file_key={$file['file_key']}").' target=_blank>'.$file['file_name'].'</a>';
			$file['file_ubb_url'] = '[url='.$settings['phpdisk_url'].urr("viewfile","file_id={$file['file_id']}&file_key={$file['file_key']}").']'.$file['file_name'].'[/url]';
		}

		if($file[yun_fid]){
			$file['url'] = $file['a_downfile'] = 'http://d.yun.phpdisk.com/down-'.$file[yun_fid];
		}else{
			if($file['server_oid']>1){
				$rs = $db->fetch_one_array("select server_host,server_store_path from {$tpf}servers where server_oid='{$file['server_oid']}'");
				if($rs){
					if(display_plugin('multi_server','open_multi_server_plugin',$settings['open_multi_server'],0)){
						$file['a_downfile'] = $rs['server_host'].urr("downfile","file_id={$file['file_id']}&file_key={$file['file_key']}");
						$file['a_viewfile'] = $rs['server_host']."downfile.php?action=view&file_id={$file['file_id']}&file_key={$file['file_key']}&uid=$pd_uid";
					}else{
						$file['a_downfile'] = urr("downfile","file_id={$file['file_id']}&file_key={$file['file_key']}");
					}
					$file['url'] = $rs['server_host']."downfile.php?action=by_tools&file_id={$file['file_id']}&file_key={$file['file_key']}&uid=$pd_uid";
				}
				unset($rs);
			}else{
				$file['a_downfile'] = urr("downfile","file_id={$file['file_id']}&file_key={$file['file_key']}");
				$file['url'] = $settings['phpdisk_url'].urr("downfile","action=by_tools&file_id={$file['file_id']}&file_key={$file['file_key']}");
			}
		}
		$file['flashget_url'] = flashget_encode($file['url'],$settings['flashget_uid']);
		$file['thunder_url'] = thunder_encode($file['url']);

		if($settings['open_vote']){
			$all_count = $file['good_count']+$file['bad_count'];
			$file['good_rate'] = $file['good_count'] ? round($file['good_count']/$all_count,3)*100 : 0;
			$file['bad_rate'] = $file['bad_count'] ? round($file['bad_count']/$all_count,3)*100 : 0;
		}
		if(!$file[yun_fid]){
			if(display_plugin('multi_server','open_multi_server_plugin',$settings['open_multi_server'],0) && $file['server_oid'] >1){
				$rs2 = $db->fetch_one_array("select * from {$tpf}servers where server_oid='{$file['server_oid']}' limit 1");
				if($rs2){
					if(can_true_link($file_extension)){
						$str = $rs2['server_host'].$rs2['server_store_path'].'/'.$file['file_store_path'].'/'.$file['file_real_name'];
						$file_url = $file['store_old'] ? $str : $str.$file_ext;
						$file['a_viewfile'] = $file['a_downfile'] = $file['file_view_url'] = $file_url;
						$file['file_html_url'] = '<a href='.$file_url.' target=_blank>'.$file['file_name'].'</a>';
						$file['file_ubb_url'] = '[url='.$file_url.']'.$file['file_name'].'[/url]';
					}else{
						$file['a_viewfile'] = $rs2['server_host'].urr("downfile","action=view&file_id={$file['file_id']}&file_key={$file['file_key']}");
						$file['file_view_url'] = $settings['phpdisk_url'].urr("viewfile","file_id={$file['file_id']}&file_key={$file['file_key']}");
						$file['file_html_url'] = '<a href='.$settings['phpdisk_url'].urr("viewfile","file_id={$file['file_id']}&file_key={$file['file_key']}").' target=_blank>'.$file['file_name'].'</a>';
						$file['file_ubb_url'] = '[url='.$settings['phpdisk_url'].urr("viewfile","file_id={$file['file_id']}&file_key={$file['file_key']}").']'.$file['file_name'].'[/url]';
					}
					$file['preview_link'] = $rs2['server_host'].$rs2['server_store_path'].'/'.$file['file_store_path'].'/'.$file['file_real_name'].$file_ext;
				}
				unset($rs2);
			}else{
				if(can_true_link($file_extension)){
					$str = $settings['phpdisk_url'].$settings['file_path'].'/'.$file['file_store_path'].'/'.$file['file_real_name'];
					$file_url = $file['store_old'] ? $str : $str.$file_ext;
					$file['a_viewfile'] = $file['a_downfile'] = $file['file_view_url'] = $file_url;
					$file['file_html_url'] = '<a href='.$file_url.' target=_blank>'.$file['file_name'].'</a>';
					$file['file_ubb_url'] = '[url='.$file_url.']'.$file['file_name'].'[/url]';
				}else{
					$file['a_viewfile'] = urr("downfile","action=view&file_id={$file['file_id']}&file_key={$file['file_key']}");
					$file['file_view_url'] = $settings['phpdisk_url'].urr("viewfile","file_id={$file['file_id']}&file_key={$file['file_key']}");
					$file['file_html_url'] = '<a href='.$settings['phpdisk_url'].urr("viewfile","file_id={$file['file_id']}&file_key={$file['file_key']}").' target=_blank>'.$file['file_name'].'</a>';
					$file['file_ubb_url'] = '[url='.$settings['phpdisk_url'].urr("viewfile","file_id={$file['file_id']}&file_key={$file['file_key']}").']'.$file['file_name'].'[/url]';
				}
				$file['preview_link'] = $settings['phpdisk_url'].$settings['file_path'].'/'.$file['file_store_path'].'/'.$file['file_real_name'].$file_ext;
			}
		}
		return $file;
	}
}

if($settings['open_report']){
	$rs = $db->fetch_one_array("select count(*) as total from {$tpf}reports where userid='$pd_uid' and file_id='$file_id'");
	$has_report = $rs['total'] ? 1 : 0;
	$a_report_file = urr("viewfile","action=report&file_id=$file_id&file_key=$file_key");
	if(!$pd_uid){
		$login_txt = __('please_login');
		$disabled = 'disabled';
	}
}

$relate_file = get_relate_file("select file_id,file_key,file_name,file_extension,file_size,file_time from {$tpf}files where ((is_public=1 and is_checked=1) or in_share=1) and in_recycle=0 and userid='{$file['userid']}' and file_id<>'$file_id' order by file_id desc limit 10");
$you_like_file = get_relate_file("select file_id,file_key,file_name,file_extension,file_size,file_time from {$tpf}files where ((is_public=1 and is_checked=1) or in_share=1) and in_recycle=0 and file_id<>'$file_id' order by rand() limit 10");

if($settings['show_relative_file']){
	$C[relate_file] = get_relate_file("select file_id,file_key,file_name,file_extension,file_size,file_time from {$tpf}files where ((is_public=1 and is_checked=1) or in_share=1) and in_recycle=0 and file_extension='".$db->escape($file[file_extension])."' and file_id<>'$file_id' order by file_id desc limit 15");
}
function get_relate_file($sql){
	global $db,$tpf;
	$q = $db->query($sql);
	$relate_file = array();
	while($rs = $db->fetch_array($q)){
		$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
		$rs['file_name_all'] = $rs['file_name'].$tmp_ext;
		$rs['file_name'] = cutstr($rs['file_name'].$tmp_ext,30);
		$rs['file_size'] = get_size($rs['file_size']);
		$rs['file_time'] = date("m/d",$rs['file_time']);
		$rs['a_viewfile'] = urr("viewfile","file_id={$rs['file_id']}");
		$relate_file[] = $rs;
	}
	$db->free($q);
	unset($rs);
	return $relate_file;
}
if($settings['open_comment']){
	function file_last_comment($file_id){
		global $db,$tpf;
		$q = $db->query("select c.*,u.username from {$tpf}comments c,{$tpf}users u where file_id='$file_id' and is_checked=1 and c.userid=u.userid order by cmt_id desc limit 5");
		$cmts = array();
		while($rs = $db->fetch_array($q)){
			$rs['content'] = str_replace("\r\n","<br>",$rs['content']);
			$rs['in_time'] = custom_time("Y-m-d H:i:s",$rs['in_time']);
			$rs['a_space'] = urr("space","username=".rawurlencode($rs['username']));
			$cmts[] = $rs;
		}
		$db->free($q);
		unset($rs);
		return $cmts;
	}
	$cmts = file_last_comment($file_id);
	$a_comment = urr("comment","file_id=$file_id");
}

$title = $file['file_name'].' - '.$settings['site_title'];

if($settings['open_seo'] && $settings['open_tag']){
	function file2tag($file_id){
		global $db,$tpf;
		$q = $db->query("select tag_name from {$tpf}file2tag where file_id='$file_id'");
		$arr = array();
		while($rs = $db->fetch_array($q)){
			$arr[] = $rs;
		}
		$db->free($q);
		unset($rs);
		return $arr;
	}
	$arr = file2tag($file_id);
	$file_tags = '';
	if(count($arr)){
		foreach($arr as $v){
			$file_tags .= $v['tag_name'].',';
		}
	}
	$file_keywords = $file_tags.$file['file_name'].',';
	$file_description = $file['file_name'].','.str_replace("\r\n",'',preg_replace("/<.+?>/i","",$file_description));
}

$loading_secs = 0;
if($pd_uid && $pd_gid){
	if($settings['secs_for_user']){
		$group_set = $group_settings[$pd_gid];
		$loading_secs = min((int)$group_set['secs_loading'],(int)$settings['global_secs_loading']);
	}else{
		$loading_secs = 0;
	}
}else{
	$loading_secs = (int)$settings['global_secs_loading'];
}

include PHPDISK_ROOT."./includes/header.inc.php";

switch($action){
	case 'report':
		form_auth(gpc('formhash','P',''),formhash());

		$content = trim(gpc('content','P',''));
		$file_id = (int)gpc('file_id','P',0);
		$file_key = gpc('file_key','P',0);

		if(checklength($content,2,250)){
			$error = true;
			$sysmsg[] = __('report_content_error');
		}
		$rs = $db->fetch_one_array("select count(*) as total from {$tpf}reports where file_id='".$file_id."' and userid='$pd_uid'");
		if($rs['total']){
			$error = true;
			$sysmsg[] = __('report_already_exists');
		}
		unset($rs);
		if(!$error){
			$ins = array(
			'userid' => $pd_uid,
			'file_id' => $file_id,
			'file_key' => $file_key,
			'content' => replace_js($content),
			'in_time' => $timestamp,
			'ip' => $onlineip,
			'is_new' => 1,
			);
			$db->query("insert into {$tpf}reports set ".$db->sql_array($ins).";");
			$db->query_unbuffered("update {$tpf}files set report_status=1 where file_id='$file_id'");
			$sysmsg[] = __('report_success');
			redirect(urr("viewfile","file_id=$file_id&file_key=$file_key"),$sysmsg,5000);
		}else{
			redirect('back',$sysmsg);
		}

		break;

	case 'comment':
		form_auth(gpc('formhash','P',''),formhash());

		$content = trim(gpc('content','P',''));
		$file_id = (int)gpc('file_id','P',0);
		$file_key = gpc('file_key','P',0);

		if(checklength($content,2,600)){
			$error = true;
			$sysmsg[] = __('cmt_content_error');
		}
		if(!$error){
			$ins = array(
			'userid' => $pd_uid,
			'file_id' => $file_id,
			'file_key' => $file_key,
			'content' => replace_js($content),
			'in_time' => $timestamp,
			'ip' => $onlineip,
			'is_checked' => $settings['check_comment'] ? 0 : 1,
			);
			$db->query("insert into {$tpf}comments set ".$db->sql_array($ins).";");
			$sysmsg[] = __('cmt_success');
			redirect(urr("viewfile","file_id=$file_id&file_key=$file_key"),$sysmsg,5000);
		}else{
			redirect('back',$sysmsg);
		}
		break;
}

require_once template_echo('pd_viewfile',$user_tpl_dir);

$db->query_unbuffered("update {$tpf}files set file_views=file_views+1 where file_id='$file_id'");

include PHPDISK_ROOT."./includes/footer.inc.php";

function get_file_tags($file_id){
	global $db,$tpf;
	$str = '';
	$q = $db->query("select * from {$tpf}file2tag where file_id='$file_id'");
	while($rs = $db->fetch_array($q)){
		$str .= '<a href="'.urr("tag","tag=".urlencode($rs[tag_name])).'">'.$rs[tag_name].'</a> ';
	}
	$db->free($q);
	unset($rs);
	return $str;
}

?>