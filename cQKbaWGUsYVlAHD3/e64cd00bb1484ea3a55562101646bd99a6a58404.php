<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: search.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/
include "includes/commons.inc.php";

$in_front = true;

$title = __('search_title');
include PHPDISK_ROOT."./includes/header.inc.php";

switch($action){
	case 'search':
		$n = trim(gpc('n','G',''));
		$u = trim(gpc('u','G',''));
		$s = trim(gpc('s','G',''));
		$t = trim(gpc('t','G',''));
		$o_arr = array('asc','desc');
		if($n){
			$sql_order = in_array($n,$o_arr) ? " file_name $n" : " file_name asc";
		}elseif($u){
			$sql_order = in_array($u,$o_arr) ? " username $u" : " username asc";
		}elseif($s){
			$sql_order = in_array($s,$o_arr) ? " file_size $s" : " file_size asc";
		}elseif($t){
			$sql_order = in_array($t,$o_arr) ? " file_time $t" : " file_time asc";
		}else{
			$sql_order = " file_id desc";
		}

		$word = trim(gpc('word','G',''));
		$scope = trim(gpc('scope','G',''));
		$word_str = $word = str_replace('　',' ',replace_inject_str($word));
$str = '';
		if(strpos($word_str,'.') ===true){
			$arr = explode('.',$word_str);
		}else{
			$arr = explode(' ',$word_str);
		}
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
		$insert_index = false;

		switch($scope){
			case 'mydisk':
				$sql_do = " {$tpf}files fl,{$tpf}users u where fl.userid=u.userid and is_public=0 and fl.userid='$pd_uid' and in_recycle=0 and {$sql_keyword}";
				$sql_do2 = "{$tpf}search_index where scope='$scope' and word='$word' and userid='$pd_uid'";
				$rs = $db->fetch_one_array("select * from {$sql_do2}");
				if($rs['search_time']){
					if($timestamp-$rs['search_time']<3600){
						$sql_do = "{$tpf}files fl,{$tpf}users u where fl.userid=u.userid and file_id in ({$rs['file_ids']})";
						$db->query_unbuffered("update {$tpf}search_index set total_count=total_count+1 where searchid='{$rs['searchid']}'");
					}else{
						$db->query_unbuffered("update {$tpf}search_index set search_time='$timestamp',total_count=total_count+1 where searchid='{$rs['searchid']}'");
					}
				}else{
					$insert_index = true;
				}
				break;
			case 'public':
				$sql_do = " {$tpf}files fl,{$tpf}users u where fl.userid=u.userid and is_public=1 and in_recycle=0 and is_checked=1 and {$sql_keyword}";
				$sql_do2 = "{$tpf}search_index where scope='$scope' and word='$word' and userid='$pd_uid'";
				$rs = $db->fetch_one_array("select * from {$sql_do2}");
				if($rs['search_time']){
					if($timestamp-$rs['search_time']<3600*12){
						$sql_do = "{$tpf}files fl,{$tpf}users u where fl.userid=u.userid and file_id in ({$rs['file_ids']})";
						$db->query_unbuffered("update {$tpf}search_index set total_count=total_count+1 where searchid='{$rs['searchid']}'");
					}else{
						$db->query_unbuffered("update {$tpf}search_index set search_time='$timestamp',total_count=total_count+1 where searchid='{$rs['searchid']}'");
					}
				}else{
					$insert_index = true;
				}

				break;
			case 'all':
			default:
				$sql_s = $pd_uid ? " and (u.userid='$pd_uid' or in_share=1 or is_public=1)" : " and (in_share=1 or is_public=1)";
				$sql_do = " {$tpf}files fl,{$tpf}users u where fl.userid=u.userid and in_recycle=0 and is_checked=1 {$sql_s} and {$sql_keyword}";
				$sql_do2 = "{$tpf}search_index where scope='$scope' and word='$word' and userid='$pd_uid'";
				$rs = $db->fetch_one_array("select * from {$sql_do2}");
				if($rs['search_time']){
					if($timestamp-$rs['search_time']<3600*12){
						$sql_do = "{$tpf}files fl,{$tpf}users u where fl.userid=u.userid and file_id in ({$rs['file_ids']})";
						$db->query_unbuffered("update {$tpf}search_index set total_count=total_count+1 where searchid='{$rs['searchid']}'");
					}else{
						$db->query_unbuffered("update {$tpf}search_index set search_time='$timestamp',total_count=total_count+1 where searchid='{$rs['searchid']}'");
					}
				}else{
					$insert_index = true;
				}
				break;
		}
		$perpage = 20;
		$rs = $db->fetch_one_array("select count(*) as total_num from {$sql_do}");
		$total_num = $rs['total_num'];
		$start_num = ($pg-1) * $perpage;
		
		function s_result(){
			global $db,$tpf,$sql_do,$sql_order,$perpage,$start_num;
			$q = $db->query("select file_id,file_key,file_name,file_extension,file_size,file_time,server_oid,file_store_path,file_real_name,is_image,u.username from {$sql_do} order by {$sql_order} limit $start_num,$perpage");
			$files_array = array();
			while($rs = $db->fetch_array($q)){
				$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
				$rs['file_thumb'] = get_file_thumb($rs);
				$rs['file_name_all'] = $rs['file_name'].$tmp_ext;
				$rs['file_name'] = cutstr($rs['file_name'].$tmp_ext,35);
				$rs['file_size'] = get_size($rs['file_size']);
				$rs['file_time'] = custom_time("Y-m-d",$rs['file_time']);
				$rs['a_downfile'] = urr("downfile","file_id={$rs['file_id']}&file_key={$rs['file_key']}");
				$rs['a_viewfile'] = urr("viewfile","file_id={$rs['file_id']}");
				$rs['a_space'] = urr("space","username=".rawurlencode($rs['username']));
				$file_ids .= $rs['file_id'].',';
				$files_array[] = $rs;
			}
			$db->free($q);
			unset($rs);
			return $files_array;
		}

		$files_array = s_result();
		$file_ids = substr($file_ids,0,-1);
		if($insert_index && $file_ids){
			$ins = array(
			'userid' => $pd_uid,
			'scope' => $scope,
			'word' => $word,
			'search_time' => $timestamp,
			'total_count' => 1,
			'file_ids' => $file_ids,
			'ip' => $onlineip,
			);
			$db->query("insert into {$tpf}search_index set ".$db->sql_array($ins).";");
		}
		$n_t = ($n=='asc') ? 'desc' : 'asc';
		$u_t = ($u=='asc') ? 'desc' : 'asc';
		$s_t = ($s=='asc') ? 'desc' : 'asc';
		$t_t = ($t=='asc') ? 'desc' : 'asc';
		$n_order = $n ? $L['o_'.$n_t] : '';
		$u_order = $u ? $L['o_'.$u_t] : '';
		$s_order = $s ? $L['o_'.$s_t] : '';
		$t_order = $t ? $L['o_'.$t_t] : '';
		$n_url = urr("search","action=search&word=".rawurlencode($word)."&scope=$scope&n=$n_t");
		$u_url = urr("search","action=search&word=".rawurlencode($word)."&scope=$scope&u=$u_t");
		$s_url = urr("search","action=search&word=".rawurlencode($word)."&scope=$scope&s=$s_t");
		$t_url = urr("search","action=search&word=".rawurlencode($word)."&scope=$scope&t=$t_t");
		$arr = explode('&',$_SERVER['QUERY_STRING']);
		$page_nav = multi($total_num, $perpage, $pg, urr("search","action=search&word=".rawurlencode($word)."&scope=$scope&{$arr[3]}"));

		require_once template_echo('pd_search',$user_tpl_dir);

		break;

	default:
		require_once template_echo('pd_search',$user_tpl_dir);
}

include PHPDISK_ROOT."./includes/footer.inc.php";

?>
