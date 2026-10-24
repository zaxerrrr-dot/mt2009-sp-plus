<?php
	// MT2009_PLUS_ITEMSHOP_V3_V3: a purchase of a line of the IN-GAME shop, by the rules of CItemShopManager::BuyItem
	// (game/src/itemshop_manager.cpp): 1..10 at once (more is refused), more than one only of what stacks (not
	// ANTIFLAG_STACK), the level floor of the character, a running promotion's price, a flash offer only while it runs
	// and has stock (player.itemshop_time_auction) within its limit per account, a VIP effect (Pierscien
	// Doswiadczenia ...) is premium time on the account (account.*_expire, as AddVIP) and refused while the premium
	// account runs; the goods are count x quantity pieces in stacks of the item's size, to the ItemShop storage
	// (player.item_award, mall=1); a Smocze Monety purchase gives the price back as Smocze Znaki (a Kupon SM: the price
	// less its value); logged as the game logs it (log.itemshop). Paid in one guarded UPDATE first; whatever cannot be
	// written gives the money back.
	require_once 'include/functions/tile.php';
	$error = $no_space = false;
	$error_text = '';
	$available_bonuses = [];
	$qty = (int)$buy_qty;
	$unit_price = $final_price;
	$delivered = 0;
	$marks_given = 0;

	if($qty < 1 || $qty > 10)
		$error_text = sprintf($lang_shop['mt-buy-max'], 10);
	else if(empty($item['stackable']))
		$qty = 1;	// the game buys one of what does not stack, whatever was asked
	$final_price = $unit_price * $qty;

	if($error_text=='')
	{
		$block = mt2009_buy_block($item, $unit_price, $qty);
		if($block!='')
		{
			$balance = $item['pay_type']==2 ? $amount_jcoins : $amount_coins;
			if($final_price > $balance && $block == ($item['pay_type']==2 ? $lang_shop['mt-not-enough-marks'] : $lang_shop['not-enough-coins']))
				$can_pay = false;
			else
				$error_text = $block;
		}
	}
	$pieces = (int)$item['count'] * $qty;

	// a flash offer: stock left and the account's limit (pieces since the offer's start)
	if($error_text=='' && $can_pay && !empty($item['auction']))
	{
		if((int)$item['auction_max'] > 0 && (int)$item['auction_bought'] >= (int)$item['auction_max'])
			$error_text = $lang_shop['mt-auction-sold-out'];
		else if((int)$item['auction_account_limit'] > 0)
		{
			$sth = $shop_db->pdo->prepare("SELECT COALESCE(SUM(quantity), 0) FROM history WHERE account = ? AND item = ? AND type = 1 AND date >= ?");
			$sth->execute([(int)$_SESSION['id'], (int)$item['id'], $item['auction_start']]);
			$mine = (int)$sth->fetchColumn() * (int)$item['count'];
			if($mine >= (int)$item['auction_account_limit'])
				$error_text = sprintf($lang_shop['mt-auction-limit'], (int)$item['auction_account_limit']);
			else if($mine + $pieces > (int)$item['auction_account_limit'])
				$error_text = $lang_shop['mt-auction-would-exceed'];
		}
	}

	$money_before = $item['pay_type']==2 ? $amount_jcoins : $amount_coins;
	if($error_text=='' && $can_pay)
	{
		if(!$account->payCoins($item['pay_type'], $final_price))
			$can_pay = false;
		else
		{
			$ok = false;
			if(!empty($item['vip']))
			{
				// CItemShopManager::AddVIP: value0 = which premium, value1 = hours, added to what is left
				$columns = ['silver_expire', 'gold_expire', 'safebox_expire', 'autoloot_expire', 'fish_mind_expire',
					'marriage_fast_expire', 'money_drop_rate_expire', 'shop_expire', 'premium_expire'];
				$type = (int)$item['vip_type'];
				$hours = (int)$item['vip_hours'];
				if(isset($columns[$type]) && $hours > 0)
				{
					$col = $columns[$type];
					$sth = $account_db->pdo->prepare("UPDATE account SET `$col` = CASE WHEN `$col` <= NOW() THEN DATE_ADD(NOW(), INTERVAL $hours HOUR) ELSE DATE_ADD(`$col`, INTERVAL $hours HOUR) END WHERE id = ?");
					$ok = $sth->execute([(int)$_SESSION['id']]) && $sth->rowCount()==1;
				}
			}
			else
			{
				// count x quantity in stacks of the item's size (BuyItem), one storage row each
				$stack = max(1, (int)$item['max_stack']);
				$chunks = [];
				for($left = $pieces; $left > 0; $left -= $stack)
					$chunks[] = min($stack, $left);
				$player_db->pdo->beginTransaction();
				$ok = true;
				foreach($chunks as $n)
				{
					$piece = $item;
					$piece['count'] = $n;
					if(!$player->CreateItem($piece, $account_id, 'item_award', $available_bonuses))
					{
						$ok = false;
						break;
					}
					$delivered += $n;
				}
				if($ok)
					$player_db->pdo->commit();
				else
				{
					$player_db->pdo->rollBack();
					$delivered = 0;
				}
			}
			if(!$ok)
			{
				// paid but nothing written - back
				$account->addCoinsByID($item['pay_type'], $final_price, $_SESSION['id']);
				$error = true;
			}
			else
			{
				if($item['pay_type']==1)
				{
					// 100 % back as Smocze Znaki; a Kupon SM (80014-80019) the price less its value (BuyItem)
					$marks_given = $final_price;
					if($item['vnum'] >= 80014 && $item['vnum'] <= 80019)
						$marks_given = max(0, $final_price - (int)$item['value0']);
					if($marks_given > 0)
						$account->addCoinsByID(2, $marks_given, $_SESSION['id']);
				}
				if(!empty($item['auction']))
					$player_db->pdo->prepare("UPDATE itemshop_time_auction SET buy_count = buy_count + ? WHERE item_index = ?")->execute([$pieces, (int)$item['id']]);
				$shop_db->pdo->prepare("INSERT INTO history (account, item, taken, pay_type, coins, type, from_account, to_player, quantity) VALUES (?, ?, 1, ?, ?, 1, 0, 0, ?)")
					->execute([(int)$_SESSION['id'], (int)$item['id'], (int)$item['pay_type'], (int)$final_price, $qty]);
				$player_db->pdo->prepare("INSERT INTO log.itemshop (pid, aid, item_index, vnum, quantity, price, currency, item_id, time, money_before) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NOW(), ?)")
					->execute([$shop_char ? (int)$shop_char['id'] : 0, (int)$_SESSION['id'], (int)$item['id'], (int)$item['vnum'], $qty, (int)$final_price, (int)$item['pay_type'], (int)$money_before]);
			}
		}
	}
	if($error_text!='')
		$error = true;

if($can_pay && !$error) {
?>
<div id="confirmation">
    <div id="itemConfirmation" class="contrast-box">
		<div class="row-fluid clearfix">
            <div class="item-showcase grey-box span4">
                <div id="image" class="picture_wrapper">
					<span class="mt-picture"><img id="selectionImageMain" class="image mt-icon" src="<?php print mt2009_item_image($item); ?>" alt=""></span>
				</div>
			</div>
            <div class="item-confirmation grey-box clearfix span8">
                <h3><?php print $lang_shop['thanks-for-purchase']; ?></h3>
                <div class="scrollable_container reward mCustomScrollbar">
					<p class="confirmed"><?php if($qty > 1) print $qty.' x '; print htmlspecialchars($item_name); if(empty($item['vip']) && $pieces > 1) print ' ('.$pieces.' '.$lang_shop['mt-pieces'].')'; ?></p>
					<?php if($marks_given > 0) { ?>
					<p class="bill_mileage text-success"><span class="block-price"><img src="<?php print $shop_url; ?>images/this/jcoins.png" alt=""> <span class="end-price"><?php print number_format($marks_given, 0, '', '.'); ?></span></span> <?php print $lang_shop['mt-marks-got']; ?></p>
					<?php } ?>
					<p><?php print !empty($item['vip']) ? $lang_shop['mt-vip-bought'] : $lang_shop['find-in-warehouse']; ?></p>
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
					<span class="mt-picture"><img id="selectionImageMain" class="image mt-icon" src="<?php print mt2009_item_image($item); ?>" alt=""></span>
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
					window.open("<?php print $topup_url; ?>", "_blank");	// MT2009_PLUS_ITEMSHOP_V3_V2
				}
			</script>    
			<button class="btn-price premium happyhour" href="javascript:void(0)" onClick="openPaymentLink()" title="">
				<img class="ttip" tooltip-content="<?php print $lang_shop['coins']; ?>" src="<?php print $shop_url."images/this/coins.png"; ?>" /> <?php print $lang_shop['mt-topup']; ?>
			</button>
			<p><?php print $lang_shop['coins-can-be-purchased']; ?></p>
		</div>
	</div>     
</div>

<script type="text/javascript">
    setDisabledBtn('.btn-buy-box');
    $('.ttip').tipTip(zs.data.ttip);
</script>
<?php } else if($error_text!='') { ?>
<div id="error" class="contrast-box">
	<div class="dark-grey-box">
		<h2><i class="icon-info left"></i><?php print htmlspecialchars($item_name); ?></h2>
		<p class="mt-buy-refused"><?php print htmlspecialchars($error_text); ?></p>
		<div class="btn_wrapper"><button class="btn-default fancybox fancybox.ajax" href="<?php print $shop_url."javascript/info/".$item['id']; ?>"><i class="icon-undo2"></i></button></div>
	</div>
</div>
<?php } else include 'pages/java/error.php'; ?>