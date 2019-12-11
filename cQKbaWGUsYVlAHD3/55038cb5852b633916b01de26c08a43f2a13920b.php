<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: pw_api.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

include 'includes/commons.inc.php';

require_once(PD_PLUGINS_DIR.'api/pw_api/security.php');

require_once(PD_PLUGINS_DIR.'api/pw_api/pw_common.php');

require_once(PD_PLUGINS_DIR.'api/pw_api/class_base.php');

$api = new api_client();

$response = $api->run($_POST + $_GET);

if ($response) {
	echo $api->dataFormat($response);
}

?>