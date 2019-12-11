<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: sitemap.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){
	case 'add_shortcut':
		$title = rawurldecode(trim(gpc('title','G','')));
		$url = base64_decode(trim(gpc('url','G','')));

		$num = $db->result_first("select count(*) from {$tpf}cp_shortcut where url='$url'");
		if($num){
			$error = true;
			$sysmsg[] = __('cp_shortcut_exists');
		}
		if(!$error){
			$ins = array(
			'title' => $title,
			'url' => $url,
			);
			$db->query_unbuffered("insert into {$tpf}cp_shortcut set ".$db->sql_array($ins).";");
			$sysmsg[] = __('add_sitemap_success');
			redirect('back',$sysmsg);
		}else{
			redirect('back',$sysmsg);
		}

		break;
	case 'setting':
		if($task =='setting'){
			form_auth(gpc('formhash','P',''),formhash());

			$ids = gpc('ids','P',array());
			$ids_arr = get_ids_arr($ids,__('please_select_operation_menus'));
			if($ids_arr[0]){
				$error = true;
				$sysmsg[] = $ids_arr[1];
			}else{
				$ids_str = $ids_arr[1];
			}		
			if(!$error){
				$db->query_unbuffered("delete from {$tpf}cp_shortcut where id in ($ids_str)");
				$num = $db->result_first("select count(*) from {$tpf}cp_shortcut");
				if(!$num){
					$db->query_unbuffered("truncate table {$tpf}cp_shortcut;");
				}
				$sysmsg[] = __('del_cp_shortcut_success');
				redirect(urr(ADMINCP,"item=$item&action=$action"),$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}
		}else{
			$q = $db->query("select * from {$tpf}cp_shortcut");
			$cs_menus = array();
			while($rs = $db->fetch_array($q)){
				$cs_menus[] = $rs;
			}
			$db->free($q);
			unset($rs);
			
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;
	default:

		$cp_menus = array(

		'settings' => array(
		'title' => __('menu_site_setting'),
		'sub_title' => __('menu_site_setting'),
		'data' => array(
		array('menu'=>__('menu_base_setting'),'url'=>urr(ADMINCP,"item=settings&action=base")),
		array('menu'=>__('menu_advanced_setting'),'url'=>urr(ADMINCP,"item=settings&action=advanced")),
		array('menu'=>__('menu_other_setting'),'url'=>urr(ADMINCP,"item=settings&action=other"))
		),
		),

		'users' => array(
		'title' => __('menu_user_setting'),
		'sub_title' => __('menu_user_setting'),
		'data' => array(
		array('menu'=>__('menu_add_user'),'url'=>urr(ADMINCP,"item=users&action=add_user")),
		array('menu'=>__('menu_user_group'),'url'=>urr(ADMINCP,"item=groups&action=index")),
		array('menu'=>__('menu_user_manage'),'url'=>urr(ADMINCP,"item=users&action=index")),
		array('menu'=>__('menu_user_active'),'url'=>urr(ADMINCP,"item=users&action=active"))
		),
		),
		'email' => array(
		'sub_title' => __('menu_email'),
		'data' => array(
		array('menu'=>__('menu_email_setting'),'url'=>urr(ADMINCP,"item=email&action=setting")),
		array('menu'=>__('menu_email_test'),'url'=>urr(ADMINCP,"item=email&action=mail_test")),
		),
		),
		'verycode' => array(
		'sub_title' => __('menu_other'),
		'data' => array(
		array('menu'=>__('menu_verycode'),'url'=>urr(ADMINCP,"item=verycode")),
		),
		),

		'files' => array(
		'title' => __('menu_files'),
		'sub_title' => __('menu_files'),
		'data' => array(
		array('menu'=>__('menu_files_list'),'url'=>urr(ADMINCP,"item=files&action=index")),
		array('menu'=>__('menu_tag'),'url'=>urr(ADMINCP,"item=tag")),
		),
		),

		'public' => array(
		'sub_title' => __('menu_public'),
		'data' => array(
		array('menu'=>__('menu_public_setting'),'url'=>urr(ADMINCP,"item=public")),
		array('menu'=>__('menu_public_category'),'url'=>urr(ADMINCP,"item=public&action=category")),
		array('menu'=>__('menu_public_viewfile'),'url'=>urr(ADMINCP,"item=public&action=viewfile")),
		),
		),

		'report' => array(
		'sub_title' => __('menu_report'),
		'data' => array(
		array('menu'=>__('menu_report_setting'),'url'=>urr(ADMINCP,"item=report")),
		array('menu'=>__('menu_report_user'),'url'=>urr(ADMINCP,"item=report&action=user")),
		array('menu'=>__('menu_report_system'),'url'=>urr(ADMINCP,"item=report&action=system")),
		array('menu'=>__('menu_report_file_unlocked'),'url'=>urr(ADMINCP,"item=report&action=file_unlocked")),
		),
		),

		'plugin' => array(
		'title' => __('menu_plugins_manage'),
		'sub_title' => __('menu_plugins_cp'),
		'data' => array(
		array('menu'=>__('menu_plugins_index'),'url'=>urr(ADMINCP,"item=plugins")),
		array('menu'=>__('menu_plugins_cp_setting'),'url'=>urr(ADMINCP,"item=plugins&menu=$menu&action=shortcut")),
		),
		),

		'tpl' => array(
		'title' => __('menu_template_language'),
		'sub_title' => __('menu_template_language'),
		'data' => array(
		array('menu'=>__('menu_lang_manage'),'url'=>urr(ADMINCP,"item=lang")),
		array('menu'=>__('menu_template_manage'),'url'=>urr(ADMINCP,"item=templates")),
		),
		),

		'extend' => array(
		'title' => __('menu_extend_tools'),
		'sub_title' => __('menu_extend'),
		'data' => array(
		array('menu'=>__('menu_adv_manage'),'url'=>urr(ADMINCP,"item=advertisement")),
		array('menu'=>__('menu_link_manage'),'url'=>urr(ADMINCP,"item=link")),
		array('menu'=>__('menu_announce_manage'),'url'=>urr(ADMINCP,"item=announce")),
		array('menu'=>__('menu_navigation_manage'),'url'=>urr(ADMINCP,"item=navigation")),
		array('menu'=>__('menu_credit_manage'),'url'=>urr(ADMINCP,"item=credit")),
		array('menu'=>__('menu_comment_manage'),'url'=>urr(ADMINCP,"item=comment")),
		array('menu'=>__('menu_seo_manage'),'url'=>urr(ADMINCP,"item=seo")),
		array('menu'=>__('menu_union_manage'),'url'=>urr(ADMINCP,"item=union")),
		array('menu'=>__('menu_gallery_manage'),'url'=>urr(ADMINCP,"item=gallery")),
		),
		),
		'datacall' => array(
		'sub_title' => __('menu_datacall_manage'),
		'data' => array(
		array('menu'=>__('menu_datacall_js'),'url'=>urr(ADMINCP,"item=datacall&action=js")),
		array('menu'=>__('menu_datacall_sql'),'url'=>urr(ADMINCP,"item=datacall&action=sql")),
		array('menu'=>__('menu_datacall_arr'),'url'=>urr(ADMINCP,"item=datacall&action=arr")),
		),
		),
		'database' => array(
		'title' => __('menu_system_tools'),
		'sub_title' => __('menu_database_manage'),
		'data' => array(
		array('menu'=>__('menu_database_optimize'),'url'=>urr(ADMINCP,"item=database&action=optimize")),
		array('menu'=>__('menu_database_backup'),'url'=>urr(ADMINCP,"item=database&action=backup")),
		array('menu'=>__('menu_database_restore'),'url'=>urr(ADMINCP,"item=database&action=restore")),
		),
		),
		'tools' => array(
		'sub_title' => __('menu_system_setting'),
		'data' => array(
		array('menu'=>__('menu_search_index'),'url'=>urr(ADMINCP,"item=cache&action=search_index")),
		array('menu'=>__('menu_cache_manage'),'url'=>urr(ADMINCP,"item=cache&action=update")),
		array('menu'=>__('menu_version_check'),'url'=>urr(ADMINCP,"item=version")),
		),
		),
		);
		require_once template_echo($item,$admin_tpl_dir,'',1);
}
?>