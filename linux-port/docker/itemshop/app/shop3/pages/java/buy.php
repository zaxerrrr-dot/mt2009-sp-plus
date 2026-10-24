<?php
	$error = $no_space = false;
	$available_bonuses = [];
	
	if($friend!=null)
	{
		$friend_account = $player->getPlayerAccount($friend);
		if($friend_account!=$account_id)
		{
			if($friend=='' || strlen($friend)>32 || !$friend_account)
			{
				$error = true;
				print 1; die();
			}
			if(!$error)
			{
				$from_account = $account_id;
				$to_player = $player->getPlayerID($friend);
				$account_id = $friend_account;
			}
		} else $friend = null;
	}
	
	if($item['available']!=1)
		$error = true;
	
	if($item['type']==2)
	{
		$available_bonuses = $shop->checkSelectionBonus($bonus_selection, $bonus_selected, $item['bonuses_count']);
		
		if(!is_array($available_bonuses))
			$error = true;
	}

	if(!$error && $can_pay && $account->payCoins($item['pay_type'], $final_price))
	{
		if(($item['type']!=3 && $player->CreateItem($item, $account_id, $add_type, $available_bonuses)) || ($item['type']==3 && $account->addBuff($item, $account_id)))
		{
			$shop->addItemHistory($item['id'], $account_id, 1, $item['pay_type'], $final_price, 1, $from_account, 0);
			if($friend!=null)
				$shop->addItemHistory($item['id'], $from_account, 1, $item['pay_type'], $final_price, 1, 0, $to_player);
			
			if($item['pay_type']==1 && $jcoins_back)
				$account->addCoinsByID(2, round($final_price*$jcoins_back/100), $_SESSION['id']);
			
			if($item['limit_all'])
			{
				$shop->updateLimitAll($item['id']);
				if($item['limit_all']==1)
					$shop->deleteItem($item['id']);
			}
		} else if($add_type=='item' && $item['type']!=3 && $player->getNewPosition($item['vnum'], $_SESSION['id'])==-1){
			$shop->addItemHistory($item['id'], $account_id, 0, $item['pay_type'], $final_price, 1, $from_account, 0);
			if($friend!=null)
				$shop->addItemHistory($item['id'], $from_account, 1, $item['pay_type'], $final_price, 1, 0, $to_player);
			
			if($item['pay_type']==1 && $jcoins_back)
				$account->addCoinsByID(2, round($final_price*$jcoins_back/100), $_SESSION['id']);
			
			if($item['limit_all'])
			{
				$shop->updateLimitAll($item['id']);
				if($item['limit_all']==1)
					$shop->deleteItem($item['id']);
			}
			$no_space = true;
		} else $error = true;
	} else $error = true;
	
if($can_pay && !$error) {
?>
<div id="confirmation">
    <div id="itemConfirmation" class="contrast-box">
		<div class="row-fluid clearfix">
            <div class="item-showcase grey-box span4">
                <div id="image" class="picture_wrapper">
					<img id="selectionImageMain" class="image" src="<?php if($item['type']!=3) print $shop_url.'images/'.$shop->getIcon($item['vnum']); else print $shop_url.'images/icons/bonuses/'.$server_item['buff'][$item['vnum']][0].'.png'; ?>" width="242" height="242" />
				</div>
			</div>
            <div class="item-confirmation grey-box clearfix span8">
                <h3><?php print $lang_shop['thanks-for-purchase']; ?></h3>
                <div class="scrollable_container reward mCustomScrollbar">
					<p class="confirmed"><?php print $item_name; ?></p>
					<p><?php if(!$no_space) print $lang_shop['find-in-warehouse']; else print $lang_shop['no-space'].' <a href="'.$shop_url.'user/deposit/">'.$lang_shop['my-objects'].'</a>'; ?></p>
				</div>
                <button class="right btn-default" onclick="javascript:$.fancybox.close();"><?php print $lang_shop['continue-shopping'];?></button>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript">
	$(document).ready(function () {
		cardMargin();
		$('.btn-buy.fancybox, .btn-default.fancybox, .item-thumb.fancybox, .card-heading.fancybox, .btn-price.fancybox').click(function () {
			$('.fancybox-overlay').removeClass('reload');
		});
		$('.fancybox-overlay').addClass('reload');
	});
</script>
<?php } else if(!$can_pay) { ?>

<div id="notEnoughCash" class="contrast-box sys-message">
    <div class="dark-grey-box clearfix">
        <div class="clearfix">
            <div class="item-showcase   span2">
                <div id="image" class="picture_wrapper" style="margin-left: 0; margin-top: 0;">
					<img id="selectionImageMain" class="image" src="<?php print $shop_url.'images/'.$shop->getIcon($item['vnum']); ?>" width="242" height="242" />
				</div>
            </div>
            <div class="money-showcase span5">
                <h2><?php print $lang_shop['not-enough-coins']; ?></h2>
                <div class="currency_status_box">
                    <p><?php print $lang_shop['balance']; ?>:</p>
                    <ul class="currency_status clearfix">
						<li><span><img src="<?php print $shop_url."images/this/coins.png"; ?>" width="16" height="16"/> <?php print number_format($amount_coins, 0, '', '.'); ?></span></li>
						<li><span><img src="<?php print $shop_url."images/this/jcoins.png"; ?>" width="16" height="16"/> <?php print number_format($amount_jcoins, 0, '', '.'); ?></span></li>
					</ul>
				</div>
				<p class="return"><?php print $lang_shop['back']; ?><span> <?php print $item_name; ?> </span>
				<button class="btn-default fancybox right fancybox.ajax" href="<?php print $shop_url."javascript/info/".$item['id']; ?>"><i class="icon-undo2"></i></button>
				</p>
			</div>
		</div>
	</div>
    <div class="alternativ_payment clearfix">
        <div class="alternativ_payment_head">
            <h3><?php print $lang_shop['what-can-i-do'];?></h3>      
			<script type="text/javascript">
				function openPaymentLink()
				{
					location.href=("<?php print $shop_url; ?>user/donate");
				}
			</script>    
			<button class="btn-price premium happyhour" href="javascript:void(0)" onClick="openPaymentLink()" title="">
				<img class="ttip" tooltip-content="<?php print $lang_shop['coins']; ?>" src="<?php print $shop_url."images/this/coins.png"; ?>" /> <?php print $lang_shop['charge-your-account']; ?>
			</button>
			<p><?php print $lang_shop['coins-can-be-purchased']; ?></p>
		</div>
	</div>     
</div>

<script type="text/javascript">
    setDisabledBtn('.btn-buy-box');
    $('.ttip').tipTip(zs.data.ttip);
</script>
<?php } else include 'pages/java/error.php'; ?>