<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: users.inc.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

if(!defined('IN_PHPDISK') || !defined('IN_ADMINCP')) {
	exit('[PHPDisk] Access Denied');
}

switch($action){

	case 'index':

		if($task =='move'){
			form_auth(gpc('formhash','P',''),formhash());

			$userids = gpc('userids','P',array(''));
			$dest_gid = (int)gpc('dest_gid','P','');

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(!$dest_gid){
				$error = true;
				$sysmsg[] = __('please_select_dest_gid');
			}

			$ids_arr = get_ids_arr($userids,__('please_select_move_users'),1);
			if($ids_arr[0]){
				$error = true;
				$sysmsg[] = $ids_arr[1];
			}else{
				$user_str = $ids_arr[1];
			}

			if(!$error){
				$db->query_unbuffered("update {$tpf}users set gid='$dest_gid' where userid in ($user_str)");
				$sysmsg[] = __('move_user_success');
				redirect(urr(ADMINCP,"item=users&action=index"),$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}
		}else{
			$perpage = 50;
			$gid = (int)gpc('gid','G',0);
			$orderby = gpc('orderby','G','');
			$sql_str = "";
			switch($orderby){
				case 'time_desc':
					$sql_orderby = " order by reg_time desc";
					break;
				case 'time_asc':
					$sql_orderby = " order by reg_time asc";
					break;
				case 'is_locked':
					$sql_orderby = $sql_str = " and u.is_locked=1";
					break;
				default:
					$sql_orderby = "";
			}
			$sql_ext = $gid ? " and u.gid='$gid'" : "";
			$sql_do = " {$tpf}users u,{$tpf}groups g where u.gid=g.gid {$sql_ext}";

			$rs = $db->fetch_one_array("select count(*) as total_num from {$sql_do} {$sql_str}");
			$total_num = $rs['total_num'];
			$start_num = ($pg-1) * $perpage;

			$q = $db->query("select userid,username,email,reg_time,is_locked,group_name,credit,g.gid from {$sql_do} {$sql_orderby} limit $start_num ,$perpage");
			$users = array();
			while($rs = $db->fetch_array($q)){
				$rs['is_admin'] = ($rs['gid']==1) ? 1 : 0;
				$rs['reg_time'] = date("Y-m-d H:i:s",$rs['reg_time']);
				$rs['status_text'] = $rs['is_locked'] ? '<span class="txtred">'.__('user_open').'</span>' : __('user_locked');
				$rs['a_user_edit'] = urr(ADMINCP,"item=users&menu=$menu&action=user_edit&uid={$rs['userid']}");
				$rs['a_user_lock'] = urr(ADMINCP,"item=users&menu=$menu&action=user_lock&uid={$rs['userid']}");
				$rs['a_user_delete'] = urr(ADMINCP,"item=users&menu=$menu&action=user_delete&uid={$rs['userid']}");
				$rs['a_user_viewfile'] = urr(ADMINCP,"item=files&menu=file&action=index&view=user&uid={$rs['userid']}");
				$rs['credit'] = $rs['credit'] ? "({$rs['credit']})" : "";
				$users[] = $rs;
			}
			$db->free($q);
			unset($rs);

			$q = $db->query("select gid,group_name,group_type from {$tpf}groups order by gid asc");
			$groups = array();
			while($rs = $db->fetch_array($q)){
				$rs['txtcolor'] = $rs['group_type'] ? 'txtblue' : '';
				$groups[] = $rs;
			}
			$db->free($q);
			unset($rs);

			$q = $db->query("select gid,group_name,group_type from {$tpf}groups where gid<>1 order by gid asc");
			$mini_groups = array();
			while($rs = $db->fetch_array($q)){
				$rs['txtcolor'] = $rs['group_type'] ? 'txtblue' : '';
				$mini_groups[] = $rs;
			}
			$db->free($q);
			unset($rs);

			$page_nav = multi($total_num, $perpage, $pg, urr(ADMINCP,"item=users&action=index&gid=$gid"));

			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'search':
		$perpage = 50;
		$word = trim(gpc('word','G',''));
		$word_str = str_replace('　',' ',replace_inject_str($word));
		$arr = explode(' ',$word_str);
		if(count($arr)>1){
			for($i=0;$i<count($arr);$i++){
				if(trim($arr[$i]) <> ''){
					$str .= " u.username like '%{$arr[$i]}%' and";
				}
			}
			$str = substr($str,0,-3);
			$sql_keyword = " and (".$str.")";

		}else{
			$sql_keyword = " and u.username like '%{$word_str}%'";
		}
		$sql_do = " {$tpf}users u,{$tpf}groups g where u.gid=g.gid {$sql_keyword}";

		$rs = $db->fetch_one_array("select count(*) as total_num from {$sql_do}");
		$total_num = $rs['total_num'];
		$start_num = ($pg-1) * $perpage;

		$q = $db->query("select userid,username,email,reg_time,is_locked,credit,g.gid,g.group_type,g.group_name from {$sql_do} limit $start_num,$perpage");
		$users = array();
		while($rs = $db->fetch_array($q)){
			$rs['reg_time'] = date("Y-m-d H:i:s",$rs['reg_time']);
			$rs['is_admin'] = ($rs['gid']==1) ? 1 : 0;
			$rs['status_text'] = $rs['is_locked'] ? '<span class="txtred">'.__('user_open').'</span>' : __('user_locked');
			$rs['a_user_edit'] = urr(ADMINCP,"item=users&action=user_edit&uid={$rs['userid']}");
			$rs['a_user_lock'] = urr(ADMINCP,"item=users&action=user_lock&uid={$rs['userid']}");
			$rs['a_user_delete'] = urr(ADMINCP,"item=users&action=user_delete&uid={$rs['userid']}");
			$rs['a_user_viewfile'] = urr(ADMINCP,"item=files&action=index&view=user&uid={$rs['userid']}");
			$rs['credit'] = $rs['credit'] ? "({$rs['credit']})" : "";
			$users[] = $rs;
		}
		$db->free($q);
		unset($rs);

		$q = $db->query("select gid,group_name,group_type from {$tpf}groups order by gid asc");
		$groups = array();
		while($rs = $db->fetch_array($q)){
			$rs['txtcolor'] = $rs['group_type'] ? 'txtblue' : '';
			$groups[] = $rs;
		}
		$db->free($q);
		unset($rs);

		$q = $db->query("select gid,group_name,group_type from {$tpf}groups where gid<>1 order by gid asc");
		$mini_groups = array();
		while($rs = $db->fetch_array($q)){
			$rs['txtcolor'] = $rs['group_type'] ? 'txtblue' : '';
			$mini_groups[] = $rs;
		}
		$db->free($q);
		unset($rs);

		$page_nav = multi($total_num, $perpage, $pg, urr(ADMINCP,"item=users&action=search&word=".rawurlencode($word).""));

		require_once template_echo($item,$admin_tpl_dir,'',1);
		break;

	case 'user_lock':
		if($settings['online_demo']){
			$error = true;
			$sysmsg[] = __('online_demo_deny');
		}
		if(!$error){
			$uid = (int)gpc('uid','G',0);
			$rs = $db->fetch_one_array("select is_locked from {$tpf}users where userid='$uid'");
			$is_locked = $rs['is_locked'] ? 0 : 1;
			unset($rs);
			$db->query_unbuffered("update {$tpf}users set is_locked='$is_locked' where userid='$uid' limit 1");
			redirect($_SERVER['HTTP_REFERER'],'',0);
		}else{
			redirect('back',$sysmsg);
		}
		break;

	case 'user_delete':
		if($settings['online_demo']){
			$error = true;
			$sysmsg[] = __('online_demo_deny');
		}
		if(!$error){
			$uid = (int)gpc('uid','G',0);
			delete_phpdisk_file("select * from {$tpf}files where userid='$uid'");

			$db->query_unbuffered("delete from {$tpf}folders where userid='$uid'");
			$db->query_unbuffered("delete from {$tpf}extracts where userid='$uid'");
			$db->query_unbuffered("delete from {$tpf}users where userid='$uid'");
			$db->query_unbuffered("delete from {$tpf}files where userid='$uid'");
			$db->query_unbuffered("delete from {$tpf}buddys where userid='$uid' or touserid='$uid'");
			$db->query_unbuffered("delete from {$tpf}messages where userid='$uid' or touserid='$uid'");
			if(display_plugin('api','open_uc_plugin',$settings['connect_uc'],0)){
				$username = @$db->result_first("select username from {$tpf}users where userid='$uid' limit 1");
				if($settings['connect_uc_type']=='phpwind'){
					$arr = uc_user_get($username,1);
					uc_user_delete($arr['uid']);
				}else{
					$result = uc_user_delete($username);
					if(!$result){
						$sysmsg[] = "UC:".__('delete_user_error');
					}
				}
			}
			$sysmsg[] = __('delete_user_success');
			redirect(urr(ADMINCP,"item=users&action=index"),$sysmsg);
		}else{
			redirect('back',$sysmsg);
		}
		break;

	case 'add_user':

		if($task =='add_user'){
			form_auth(gpc('formhash','P',''),formhash());

			$username = trim(gpc('username','P',''));
			$password = trim(gpc('password','P',''));
			$confirm_password = trim(gpc('confirm_password','P',''));
			$email = trim(gpc('email','P',''));
			$gid = (int)gpc('gid','P','');
			$is_locked = (int)gpc('is_locked','P','');
			$is_activated = (int)gpc('is_activated','P',0);
			$credit = (int)gpc('credit','P','');
			$wealth = (float)gpc('wealth','P','');
			$rank = (int)gpc('rank','P','');
			$exp = (int)gpc('exp','P','');
			$user_store_space = (int)gpc('user_store_space','P','');
			$user_file_types = trim(gpc('user_file_types','P',''));
			$down_flow_count = (int)gpc('down_flow_count','P','');
			$view_flow_count = (int)gpc('view_flow_count','P','');

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if(checklength($username,2,60)){
				$error = true;
				$sysmsg[] = __('username_error');
			}elseif(is_bad_chars($username)){
				$error = true;
				$sysmsg[] = __('username_has_bad_chars');
			}else{
				$rs = $db->fetch_one_array("select username from {$tpf}users where username='$username' limit 1");
				if($rs){
					if(strcasecmp($username,$rs['username']) ==0){
						$error = true;
						$sysmsg[] = __('username_already_exists');
					}
				}
				unset($rs);
			}
			if(display_plugin('api','open_uc_plugin',$settings['connect_uc'],0)){
				if($settings['connect_uc_type']=='phpwind'){
					$checkuser = uc_check_username($username);
					if($checkuser<>1){
						$error = true;
						$sysmsg[] = 'UC:'.__('username_already_exists');
					}
				}else{
					$ucresult = uc_user_checkname($username);
					if($ucresult < 0) {
						$error = true;
						$sysmsg[] = 'UC:'.__('username_already_exists');
					}
				}
			}
			if(checklength($password,6,20)){
				$error = true;
				$sysmsg[] = __('password_error');
			}else{
				if($password == $confirm_password){
					$md5_pwd = md5($password);
				}else{
					$error = true;
					$sysmsg[] = __('confirm_password_invalid');
				}
			}
			if(!checkemail($email)){
				$error = true;
				$sysmsg[] = __('invalid_email');
			}else{
				$rs = $db->fetch_one_array("select email from {$tpf}users where email='$email' limit 1");
				if($rs){
					if(strcasecmp($email,$rs['email']) ==0){
						$error = true;
						$sysmsg[] = __('email_already_exists');
					}
					unset($rs);
				}
			}
			if(display_plugin('api','open_uc_plugin',$settings['connect_uc'],0)){
				if($settings['connect_uc_type']=='phpwind'){
					$ucresult = uc_check_email($email);
					if($ucresult <>1){
						$error = true;
						$sysmsg[] = 'UC:'.__('email_already_exists');
					}
				}else{
					$ucresult = uc_user_checkemail($email);
					if($ucresult < 0) {
						$error = true;
						$sysmsg[] = 'UC:'.__('email_already_exists');
					}
				}
			}

			if(!$error && display_plugin('api','open_uc_plugin',$settings['connect_uc'],0)){
				$uid = uc_user_register($username , $password , $email);
				if($uid <= 0){
					$error = true;
					$sysmsg[] = 'UC: '.__('add_user_error');
				}
			}

			if(!$error){
				$ins = array(
				'username' => $username,
				'password' => $md5_pwd,
				'email' => $email,
				'gid' => $gid,
				'is_activated' => $is_activated,
				'credit' => $credit,
				'wealth' => $wealth,
				'rank' => $rank,
				'exp' => $exp,
				'is_locked' => $is_locked,
				'user_store_space' => $user_store_space,
				'user_file_types' => $user_file_types,
				'down_flow_count' => $down_flow_count,
				'view_flow_count' => $view_flow_count,
				'reg_time' => $timestamp,
				'reg_ip' => $onlineip,
				);

				$db->query("insert into {$tpf}users set ".$db->sql_array($ins).";");
				$rs = $db->fetch_one_array("select count(*) as total from {$tpf}users ");
				if($rs['total']){
					$stats['users_count'] = (int)$rs['total'];
					stats_cache($stats);
				}
				unset($rs);
				$sysmsg[] = __('add_user_success');
				redirect(urr(ADMINCP,"item=users&action=index"),$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}

		}else{
			$q = $db->query("select gid,group_name,group_type from {$tpf}groups order by gid asc");
			$groups = array();
			while($rs = $db->fetch_array($q)){
				$rs['txtcolor'] = $rs['group_type'] ? 'txtblue' : '';
				$groups[] = $rs;
			}
			$db->free($q);
			unset($rs);
			$default_gid = 4;
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;

	case 'user_edit':
		$uid = (int)gpc('uid','GP',0);

		if($task =='user_edit'){
			form_auth(gpc('formhash','P',''),formhash());

			$password = trim(gpc('password','P',''));
			$email = trim(gpc('email','P',''));
			$is_locked = (int)gpc('is_locked','P',0);
			$is_activated = (int)gpc('is_activated','P',0);
			$gid = (int)gpc('gid','P',0);
			$credit = (int)gpc('credit','P','');
			$wealth = (float)gpc('wealth','P','');
			$rank = (int)gpc('rank','P','');
			$exp = (int)gpc('exp','P','');
			$user_file_types = trim(gpc('user_file_types','P',''));
			$user_store_space = str_replace('，',',',trim(gpc('user_store_space','P','')));
			$down_flow_count = (int)gpc('down_flow_count','P','');
			$view_flow_count = (int)gpc('view_flow_count','P','');

			if($settings['online_demo']){
				$error = true;
				$sysmsg[] = __('online_demo_deny');
			}
			if($password){
				if(checklength($password,6,20)){
					$error = true;
					$sysmsg[] = __('invalid_password');
				}else{
					$md5_pwd = md5($password);
				}
			}else{
				$rs = $db->fetch_one_array("select password from {$tpf}users where userid='$uid'");
				$md5_pwd = $rs['password'];
			}
			if($gid>1){
				$rs = $db->fetch_one_array("select count(*) as total from {$tpf}users where gid=1 and userid<>'$uid'");
				if(!$rs['total']){
					$error = true;
					$sysmsg[] = __('only_one_admin');
				}
				unset($rs);
			}
			if(!checkemail($email)){
				$error = true;
				$sysmsg[] = __('invalid_email');
			}else{
				$rs = $db->fetch_one_array("select email from {$tpf}users where email='$email' and userid<>'$uid'");
				if($rs){
					if(strcasecmp($email,$rs['email']) ==0){
						$error = true;
						$sysmsg[] = __('email_already_exists');
					}
					unset($rs);
				}
			}
			$user_store_space = $user_store_space ? $user_store_space : 0;
			if($user_file_types && substr($user_file_types,strlen($user_file_types)-1,1) ==','){
				$user_file_types = substr($user_file_types,0,-1);
			}
			if(display_plugin('api','open_uc_plugin',$settings['connect_uc'],0)){
				$old_pwd = $db->result_first("select password from {$tpf}users where userid='$uid'");
				if($settings['connect_uc_type']=='phpwind'){
					uc_user_edit($pd_uid, $pd_username, $pd_username, $password, $email);
				}else{
					$ucresult = uc_user_edit($username, $old_pwd, $password,$email,1);
					if($ucresult < 0) {
						$error = true;
						$sysmsg[] = 'UC:'.__('update_password_error');
					}
				}
			}

			if(!$error){
				$ins = array(
				'password' => $md5_pwd,
				'email' => $email,
				'is_locked' => $is_locked,
				'gid' => $gid,
				'is_activated' => $is_activated,
				'credit' => $credit,
				'wealth' => $wealth,
				'rank' => $rank,
				'exp' => $exp,
				'user_file_types' => $user_file_types,
				'user_store_space' => $user_store_space,
				'down_flow_count' => $down_flow_count,
				'view_flow_count' => $view_flow_count,
				);
				$db->query_unbuffered("update {$tpf}users set ".$db->sql_array($ins)." where userid='$uid';");
				$sysmsg[] = __('user_edit_success');
				redirect(urr(ADMINCP,"item=users&action=index"),$sysmsg);

			}else{
				redirect('back',$sysmsg);
			}

		}else{
			$q = $db->query("select gid,group_name,group_type from {$tpf}groups order by gid asc");
			$groups = array();
			while($rs = $db->fetch_array($q)){
				$rs['txtcolor'] = $rs['group_type'] ? 'txtblue' : '';
				$groups[] = $rs;
			}
			$db->free($q);
			unset($rs);

			$user = $db->fetch_one_array("select * from {$tpf}users where userid='$uid' limit 1");
			if($user){
				$user['user_store_space'] = $user['user_store_space'] ? $user['user_store_space'] : 0;
				require_once template_echo($item,$admin_tpl_dir,'',1);
			}else{
				exit('Error Operation!');
			}
		}
		break;
	case 'active':
		if($task =='update'){
			form_auth(gpc('formhash','P',''),formhash());

			$setting = array(
			'user_active' => 0,
			);
			$user_active_curr = (int)gpc('user_active_curr','P',0);
			
			if($user_active_curr ==2){
				$db->query_unbuffered("update {$tpf}users set is_activated=1");
			}elseif($user_active_curr ==3){
				$db->query_unbuffered("update {$tpf}users set is_activated=0");
			}
			
			$open_email = $settings['open_email'];
			$settings = gpc('setting','P',$setting);

			if($settings['user_active']==1 && !$open_email){
				$error = true;
				$sysmsg[] = __('user_active_email');
			}

			if(!$error){
				settings_cache($settings);
				$sysmsg[] = __('user_active_success');
				redirect('back',$sysmsg);
			}else{
				redirect('back',$sysmsg);
			}
		}else{
			require_once template_echo($item,$admin_tpl_dir,'',1);
		}
		break;
	case 'adminlogout':
		$db->query_unbuffered("update {$tpf}adminsession set hashcode='' where userid='$pd_uid'");
		$sysmsg[] = __('system_logout_success');
		redirect('javascript:self.parent.close();',$sysmsg);
		break;

	default:
		redirect(urr(ADMINCP,"item=users&action=index"),'',0);
}

?>