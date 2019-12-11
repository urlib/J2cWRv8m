<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: extract.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

include "includes/commons.inc.php";

$in_front = true;

$title = __('extract_file').' - '.$settings['site_title'];
include PHPDISK_ROOT."./includes/header.inc.php";

switch($action){
	case 'file_extract':
		form_auth(gpc('formhash','P',''),formhash());

		$extract_code = trim(gpc('extract_code','P',''));

		if(strlen($extract_code)==8){
			$rs = $db->fetch_one_array("select * from {$tpf}files where file_key='$extract_code'");
			if($rs){
				$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
				$rs['file_thumb'] = get_file_thumb($rs);
				$rs['file_name_all'] = $rs['file_name'].$tmp_ext;
				$rs['file_name'] = cutstr($rs['file_name'].$tmp_ext,35);
				$rs['file_size'] = get_size($rs['file_size']);
				$rs['file_time'] = custom_time("Y-m-d",$rs['file_time']);
				$rs['a_viewfile'] = 'viewfile.php?file_id='.$rs['file_id'].'&code='.md5($rs['file_key']);
				$files_array[] = $rs;
			}else{
				$sysmsg[] = __('extract_code_not_found');
			}
			unset($rs);
		}else{
			$rs2 = $db->fetch_one_array("select * from {$tpf}extracts where extract_code='$extract_code'");
			if($rs2){
				if($rs2['extract_locked']){
					$error = true;
					$sysmsg[] = __('extract_code_locked');
				}else{
					$db->query("update {$tpf}extracts set extract_count=extract_count+1 where extract_id='".$rs2['extract_id']."'");
					if($rs2['extract_type']==1){
						if($timestamp > $rs2['extract_time']){
							$error = true;
							$sysmsg[] = __('extract_exceed_time_limit');
						}
					}else{
						if($rs2['extract_total'] && ($rs2['extract_count'] > $rs2['extract_total'])){
							$error = true;
							$sysmsg[] = __('extract_exceed_count_limit');
						}
					}
				}
				if(!$error){
					function extract_file($ids){
						global $db,$tpf;
						$q = $db->query("select file_id,file_key,file_name,file_extension,file_size,file_time,server_oid,file_store_path,file_real_name,is_image,store_old from {$tpf}files where file_id in ($ids) order by file_id desc");
						$files_array = array();
						while($rs = $db->fetch_array($q)){
							$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
							$rs['file_thumb'] = get_file_thumb($rs);
							$rs['file_name_all'] = $rs['file_name'].$tmp_ext;
							$rs['file_name'] = cutstr($rs['file_name'].$tmp_ext,35);
							$rs['file_size'] = get_size($rs['file_size']);
							$rs['file_time'] = custom_time("Y-m-d",$rs['file_time']);
							$rs['a_viewfile'] = 'viewfile.php?file_id='.$rs['file_id'].'&code='.md5($rs['file_key']);
							$files_array[] = $rs;
						}
						$db->free($q);
						unset($rs);
						return $files_array;
					}
					$files_array = extract_file($rs2['extract_file_ids']);
				}
				unset($rs);
			}else{
				$sysmsg[] = __('extract_code_not_found');
			}
			unset($rs2);
		}

		require_once template_echo('pd_extract',$user_tpl_dir);

		break;

	default:
		require_once template_echo('pd_extract',$user_tpl_dir);
}
include PHPDISK_ROOT."./includes/footer.inc.php";

?>