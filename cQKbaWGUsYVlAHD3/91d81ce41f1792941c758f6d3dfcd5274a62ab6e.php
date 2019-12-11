<?php 
/**
#	Project: PHPDISK File Storage Solution
#	This is NOT a freeware, use is subject to license terms.
#
#	Site: http://www.phpdisk.com
#
#	$Id: payment.php 25 2014-01-10 03:13:43Z along $
#
#	Copyright (C) 2008-2014 PHPDisk Team. All Rights Reserved.
#
*/

include "includes/commons.inc.php";

$in_front = true;

if(!display_plugin('payment','open_payment_plugin',$settings['open_payment'],0)){
	exit('ERROR: payment '.__('plugin_not_install'));
}

$title = __('pay_online');
include PHPDISK_ROOT."./includes/header.inc.php";

switch($action){
	case 'alipay':
		require_once PD_PLUGINS_DIR."payment/alipay/alipay_config.php";
		require_once PD_PLUGINS_DIR."payment/alipay/class/alipay_notify.php";

		$alipay = new alipay_notify($partner,$key,$sign_type,$_input_charset,$transport);
		$verify_result = $alipay->return_verify();

		$out_trade_no = trim(gpc('out_trade_no','G',''));
		$total_fee = (float)gpc('total_fee','G','');
		$trade_status = gpc('trade_status','G','');
		$auto_convert = (int)gpc('auto_convert','G',0);

		$rs = $db->fetch_one_array("select order_id,pay_status from {$tpf}orders where order_number='$out_trade_no' and pay_method='$action' and userid='$pd_uid'");
		if($rs){
			$order_id = (int)$rs['order_id'];
			$pay_done = $rs['pay_status']=='success' ? 1 : 0;
		}
		unset($rs);
		if($verify_result && ($trade_status == 'TRADE_FINISHED' || $trade_status == 'TRADE_SUCCESS')) {
			if(!$pay_done){
				if($auto_convert){
					$credit = $settings['credit_convert'] * $total_fee;
					$db->query_unbuffered("update {$tpf}users set credit=credit+$credit where userid='$pd_uid' limit 1");
				}else{
					$db->query_unbuffered("update {$tpf}users set wealth=wealth+$total_fee where userid='$pd_uid' limit 1");
				}
				$db->query_unbuffered("update {$tpf}orders set pay_status='success' where order_id='$order_id'");
			}
			$s_title = __('pay_success');
			$msg = __('your_order').': '.$out_trade_no.','.__('pay_success');

		}else {
			$db->query_unbuffered("update {$tpf}orders set pay_status='fail' where order_id='$order_id'");

			$s_title = __('pay_fail');
			$msg = __('your_order').': '.$out_trade_no.','.__('pay_fail');

		}
		require_once template_echo('pd_payment',$user_tpl_dir);
		break;

	case 'tenpay':
		include_once PD_PLUGINS_DIR."payment/tenpay/PayResponseHandler.class.php";

		$key = $settings['ten_key'];
		$resHandler = new PayResponseHandler();
		$resHandler->setKey($key);
		$auto_convert = (int)gpc('auto_convert','G',0);

		if($resHandler->isTenpaySign()) {
			$transaction_id = $resHandler->getParameter("transaction_id");
			$total_fee = $resHandler->getParameter("total_fee");
			$total_fee = round($total_fee/100,2);
			$pay_result = $resHandler->getParameter("pay_result");

			$rs = $db->fetch_one_array("select order_id,pay_status from {$tpf}orders from {$tpf}orders where order_number='$transaction_id' and pay_method='$action' and userid='$pd_uid'");
			if($rs){
				$order_id = (int)$rs['order_id'];
				$pay_done = $rs['pay_status']=='success' ? 1 : 0;
			}
			unset($rs);
			if( "0" == $pay_result ) {
				if(!$pay_done){
					if($auto_convert){
						$credit = $settings['credit_convert'] * $total_fee;
						$db->query_unbuffered("update {$tpf}users set credit=credit+$credit where userid='$pd_uid' limit 1");
					}else{
						$db->query_unbuffered("update {$tpf}users set wealth=wealth+$total_fee where userid='$pd_uid' limit 1");
					}
					$db->query_unbuffered("update {$tpf}orders set pay_status='success' where order_id='$order_id'");
				}
				$s_title = __('pay_success');
				$msg = __('your_order').': '.$transaction_id.','.__('pay_success');
			} else {
				$db->query_unbuffered("update {$tpf}orders set pay_status='fail' where order_id='$order_id'");
				$s_title = __('pay_fail');
				$msg = __('your_order').': '.$transaction_id.','.__('pay_fail');
			}
		} else {
			$msg = '<span class="txtred">'.__('sign_pay_error').'</span>';
		}
		require_once template_echo('pd_payment',$user_tpl_dir);
		break;

	case 'chinabank':
		$key = $settings['chinabank_key'];	//登陆后在上面的导航栏里可能找到“B2C”，在二级导航栏里有“MD5密钥设置”

		$v_oid     =trim($_POST['v_oid']);       // 商户发送的v_oid定单编号
		$v_pmode   =trim($_POST['v_pmode']);    // 支付方式（字符串）
		$v_pstatus =trim($_POST['v_pstatus']);   //  支付状态 ：20（支付成功）；30（支付失败）
		$v_pstring =trim($_POST['v_pstring']);   // 支付结果信息 ： 支付完成（当v_pstatus=20时）；失败原因（当v_pstatus=30时,字符串）；
		$v_amount  =trim($_POST['v_amount']);     // 订单实际支付金额
		$v_moneytype =trim($_POST['v_moneytype']); //订单实际支付币种
		$remark1   =trim($_POST['remark1']);      //备注字段1
		$remark2   =trim($_POST['remark2']);     //备注字段2
		$v_md5str  =trim($_POST['v_md5str']);   //拼凑后的MD5校验值
		$auto_convert = (int)gpc('auto_convert','G',0);

		$md5string=strtoupper(md5($v_oid.$v_pstatus.$v_amount.$v_moneytype.$key));

		if ($v_md5str==$md5string){
			$rs = $db->fetch_one_array("select order_id,pay_status from {$tpf}orders where order_number='$v_oid' and pay_method='$action' and userid='$pd_uid'");
			if($rs){
				$order_id = (int)$rs['order_id'];
				$pay_done = $rs['pay_status']=='success' ? 1 : 0;
			}
			unset($rs);
			if($v_pstatus=="20"){
				if(!$pay_done){
					if($auto_convert){
						$credit = $settings['credit_convert'] * $v_amount;
						$db->query_unbuffered("update {$tpf}users set credit=credit+$credit where userid='$pd_uid' limit 1");
					}else{
						$db->query_unbuffered("update {$tpf}users set wealth=wealth+$v_amount where userid='$pd_uid' limit 1");
					}
					$db->query_unbuffered("update {$tpf}orders set pay_status='success' where order_id='$order_id'");
				}
				$s_title = __('pay_success');
				$msg = __('your_order').': '.$v_oid.','.__('pay_success');
			}else{
				$db->query_unbuffered("update {$tpf}orders set pay_status='fail' where order_id='$order_id'");

				$s_title = __('pay_fail');
				$msg = __('your_order').': '.$v_oid.','.__('pay_fail');
			}
		}else{
			echo __('sign_pay_error');
		}
		require_once template_echo('pd_payment',$user_tpl_dir);
		break;

	case 'yeepay':
		include_once PD_PLUGINS_DIR.'payment/yeepay/yeepayCommon.php';

		$return = getCallBackValue($r0_Cmd,$r1_Code,$r2_TrxId,$r3_Amt,$r4_Cur,$r5_Pid,$r6_Order,$r7_Uid,$r8_MP,$r9_BType,$hmac);

		$bRet = CheckHmac($r0_Cmd,$r1_Code,$r2_TrxId,$r3_Amt,$r4_Cur,$r5_Pid,$r6_Order,$r7_Uid,$r8_MP,$r9_BType,$hmac);
		$auto_convert = (int)gpc('auto_convert','G',0);

		$rs = $db->fetch_one_array("select order_id,pay_status from {$tpf}orders where order_number='$r6_Order' and pay_method='$action' and userid='$pd_uid'");
		if($rs){
			$order_id = (int)$rs['order_id'];
			$pay_done = $rs['pay_status']=='success' ? 1 : 0;
		}
		unset($rs);
		if($bRet){
			if($r1_Code=="1"){

				if($r9_BType=="1"){
					echo "交易成功";
					echo  "<br />在线支付页面返回";
				}elseif($r9_BType=="2"){

					if(!$pay_done){
						if($auto_convert){
							$credit = $settings['credit_convert'] * $r3_Amt;
							$db->query_unbuffered("update {$tpf}users set credit=credit+$credit where userid='$pd_uid' limit 1");
						}else{
							$db->query_unbuffered("update {$tpf}users set wealth=wealth+$r3_Amt where userid='$pd_uid' limit 1");
						}
						$db->query_unbuffered("update {$tpf}orders set pay_status='success' where order_id='$order_id'");
					}
					$s_title = __('pay_success');
					$msg = __('your_order').': '.$r6_Order.','.__('pay_success');

				}else{
					$db->query_unbuffered("update {$tpf}orders set pay_status='fail' where order_id='$order_id'");

					$s_title = __('pay_fail');
					$msg = __('your_order').': '.$r6_Order.','.__('pay_fail');

				}
			}

		}else{
			echo __('sign_pay_error');
		}
		require_once template_echo('pd_payment',$user_tpl_dir);
		break;

	default:
		redirect('./','');
}
include PHPDISK_ROOT."./includes/footer.inc.php";

?>