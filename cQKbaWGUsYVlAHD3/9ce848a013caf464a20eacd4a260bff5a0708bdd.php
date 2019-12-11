<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: space.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

include "includes/commons.inc.php";

$in_front = true;

$username = trim(gpc('username','G',''));
$rs = $db->fetch_one_array("select username,userid from {$tpf}users where username='$username'");
$title = $rs['username'].' '.__('space_title').' - '.$settings['site_title'];
$space_title = $rs['username'].' '.__('space_title');
$userid = $rs['userid'];
if(!$userid){
	aheader('./');
}
include PHPDISK_ROOT."./includes/header.inc.php";

$perpage = 20;
$sql_do = "{$tpf}files where userid='$userid' and in_share=1 and in_recycle=0";

$rs = $db->fetch_one_array("select count(*) as total_num from {$sql_do}");
$total_num = $rs['total_num'];
$start_num = ($pg-1) * $perpage;

$q = $db->query("select * from {$sql_do} order by file_id desc limit $start_num,$perpage");
$files_array = array();
while($rs = $db->fetch_array($q)){
	$tmp_ext = $rs['file_extension'] ? '.'.$rs['file_extension'] : "";
	$rs['file_thumb'] = get_file_thumb($rs);
	$rs['file_name_all'] = $rs['file_name'].$tmp_ext;
	$rs['file_name'] = cutstr($rs['file_name'].$tmp_ext,25);
	$rs['file_size'] = get_size($rs['file_size']);
	$rs['file_time'] = custom_time("Y-m-d",$rs['file_time']);
	$rs['a_viewfile'] = urr("viewfile","file_id={$rs['file_id']}");
	$files_array[] = $rs;
}
$db->free($q);
unset($rs);

$page_nav = multi($total_num, $perpage, $pg, "space.php?username=".rawurlencode($username));


require_once template_echo('pd_space',$user_tpl_dir);

include PHPDISK_ROOT."./includes/footer.inc.php";
?>
