<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: announce.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

include "includes/commons.inc.php";

$inner_box = true;
$aid = (int)gpc('aid','G',0);
include PHPDISK_ROOT.'includes/header.inc.php';

$arr = get_announce($aid);
$content = $arr[0];

require_once template_echo('pd_announce',$user_tpl_dir);

include PHPDISK_ROOT.'includes/footer.inc.php';

function get_announce($aid){
	global $db,$tpf;
	if(!$aid){
		die("$aid Error!");
	}else{
		$content = $db->result_first("select content from {$tpf}announces where annid='$aid'");
	}
	return array($content);
}

?>