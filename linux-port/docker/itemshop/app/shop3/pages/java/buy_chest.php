<?php
	// MT2009_PLUS_ITEMSHOP_V3_V6: buying a costume set chest (the owner's round 3) - rolled here, at the purchase, as the
	// big servers' shop does: each of the 1..10 chests one roll of its results (itemshop3.chest_drops, chances in parts
	// per million, tools/itemshop3/gen_global_catalog.py), every item of the result in the ItemShop storage
	// (player.item_award, as any purchase - Player::CreateItem, the line's duration in socket0), the costume / hair /
	// skin the one the buying character can wear (sex, class), and the result window lists what was won.
	// One transaction on one connection (the account's coins, the storage rows, the rolls' log, the shop's history, the
	// game's itemshop log): all of it or nothing. The item window's token (header.php, info.php) makes a purchase once -
	// a second request with it (a double click, a reload) is not paid again and shows the first one's result.
	require_once 'include/functions/tile.php';
	$qty = (int)$buy_qty;
	$unit_price = $final_price;
	$error_text = '';
	$result = null;
	$token = isset($_GET['t']) ? strtolower(preg_replace('/[^a-fA-F0-9]/', '', (string)$_GET['t'])) : '';
	$pdo = $player_db->pdo;
	$account_id = (int)$_SESSION['id'];

	// the token's earlier purchase: its result again, nothing paid
	$stored = function($token) use ($pdo, $account_id) {
		if(strlen($token) != 32)
			return null;
		$sth = $pdo->prepare("SELECT result FROM itemshop3.purchase_tokens WHERE token = ? AND account = ?");
		$sth->execute([$token, $account_id]);
		$row = $sth->fetchColumn();
		$res = $row ? json_decode($row, true) : null;
		return is_array($res) ? $res : null;
	};

	$result = $stored($token);
	if($result === null)
	{
		$chest = $shop->getChest((int)$item['chest']);
		$drops = $chest ? $shop->getChestDrops((int)$chest['id']) : [];
		if(strlen($token) != 32 || !isset($_SESSION['mt_buy_tokens'][$token]) || (int)$_SESSION['mt_buy_tokens'][$token] != (int)$item['id'])
			$error_text = $lang_shop['mt-buy-token'];
		else if($qty < 1 || $qty > 10)
			$error_text = sprintf($lang_shop['mt-buy-max'], 10);
		else if(!$chest || !count($drops) || array_sum(array_column($drops, 'ppm')) != 1000000)
			$error_text = $lang_shop['mt-not-available'];
		else
		{
			$block = mt2009_buy_block($item, $unit_price, $qty);
			if($block != '')
			{
				if($unit_price * $qty > $amount_coins && $block == $lang_shop['not-enough-coins'])
					$can_pay = false;
				else
					$error_text = $block;
			}
		}
	}

	if($result === null && $error_text == '' && $can_pay)
	{
		$wear = $shop_char ? Shop::wearNames($shop_char['job']) : [];
		$total = $unit_price * $qty;
		$column = Account::currencyColumn((int)$item['pay_type']);
		$login = $account->getAccountData('login', $account_id);
		$money_before = (int)$item['pay_type'] == 2 ? $amount_jcoins : $amount_coins;
		$rolls = [];
		$failed = false;
		try
		{
			$pdo->beginTransaction();
			$sth = $pdo->prepare("INSERT INTO itemshop3.purchase_tokens (token, account, line, qty) VALUES (?, ?, ?, ?)");
			if(!$sth->execute([$token, $account_id, (int)$item['id'], $qty]))
				throw new Exception('token');	// used meanwhile (a second request in parallel) - its result below
			$sth = $pdo->prepare("UPDATE account.account SET `$column` = `$column` - ? WHERE id = ? AND `$column` >= ?");
			$sth->execute([$total, $account_id, $total]);
			if($sth->rowCount() != 1)
			{
				$pdo->rollBack();
				$can_pay = false;
			}
			else
			{
				for($n = 1; $n <= $qty; $n++)
				{
					// one roll: 1..1 000 000 against the results' chances in their order
					$rnd = random_int(1, 1000000);
					$acc = 0;
					$drop = null;
					foreach($drops as $d)
					{
						$acc += (int)$d['ppm'];
						if($rnd <= $acc)
						{
							$drop = $d;
							break;
						}
					}
					if(!$drop)
						$drop = end($drops);
					$won = [];
					$award_ids = [];
					foreach($drop['items'] as $alts)
					{
						// the alternative the character can wear (a man's costume for a man, the sword skin for a warrior)
						$fit = array_values(array_filter($alts, function($a) use ($wear) {
							foreach($wear as $col)
								if(!empty($a[$col]))
									return false;
							return true;
						}));
						$pool = count($fit) ? $fit : $alts;
						$pick = $pool[random_int(0, count($pool) - 1)];
						$piece = ['id' => 0, 'type' => 1, 'vnum' => (int)$pick['vnum'], 'count' => max(1, (int)$pick['count']), 'time' => (int)$pick['minutes'],
							'polymorph' => 0, 'socket0' => 0, 'socket1' => 0, 'socket2' => 0, 'socket3' => 0, 'socket4' => 0, 'socket5' => 0];
						for($a = 0; $a <= 6; $a++)
							$piece['attrtype'.$a] = $piece['attrvalue'.$a] = 0;
						$proto = $shop->getItem($piece['vnum']);
						if($piece['time'] <= 0 && $proto)
							$piece['time'] = $player->getItemProtoDuration($proto);
						if(!$player->CreateItem($piece, $account_id, 'item_award'))
							throw new Exception('award');
						$award_ids[] = (int)$pdo->lastInsertId();
						$won[] = ['vnum' => $piece['vnum'], 'name' => $pick['name'], 'count' => $piece['count'], 'minutes' => (int)$pick['minutes']];
					}
					$sth = $pdo->prepare("INSERT INTO itemshop3.chest_rolls (token, account, pid, line, chest_id, roll_no, drop_no, ppm, rnd, label, vnums, award_ids, price, pay_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
					if(!$sth->execute([$token, $account_id, $shop_char ? (int)$shop_char['id'] : 0, (int)$item['id'], (int)$chest['id'], $n, (int)$drop['drop_no'], (int)$drop['ppm'], $rnd,
						mb_substr($drop['label'], 0, 160), implode(',', array_column($won, 'vnum')), implode(',', $award_ids), $unit_price, (int)$item['pay_type']]))
						throw new Exception('roll');
					$rolls[] = ['label' => $drop['label'], 'kind' => $drop['kind'], 'ppm' => (int)$drop['ppm'], 'items' => $won];
				}
				// 100 % of a Smocze Monety price back as Smocze Znaki (the owner's rule, as every purchase here)
				$marks = (int)$item['pay_type'] == 1 ? $total : 0;
				if($marks > 0 && !$pdo->prepare("UPDATE account.account SET cash_mark = cash_mark + ? WHERE id = ?")->execute([$marks, $account_id]))
					throw new Exception('marks');
				if(!$pdo->prepare("INSERT INTO itemshop3.history (account, item, taken, pay_type, coins, type, from_account, to_player, quantity) VALUES (?, ?, 1, ?, ?, 1, 0, 0, ?)")
					->execute([$account_id, (int)$item['id'], (int)$item['pay_type'], $total, $qty]))
					throw new Exception('history');
				if(!$pdo->prepare("INSERT INTO log.itemshop (pid, aid, item_index, vnum, quantity, price, currency, item_id, time, money_before) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NOW(), ?)")
					->execute([$shop_char ? (int)$shop_char['id'] : 0, $account_id, (int)$item['id'], 0, $qty, $total, (int)$item['pay_type'], $money_before]))
					throw new Exception('log');
				$result = ['qty' => $qty, 'price' => $total, 'marks' => $marks, 'rolls' => $rolls];
				if(!$pdo->prepare("UPDATE itemshop3.purchase_tokens SET result = ? WHERE token = ?")->execute([json_encode($result, JSON_UNESCAPED_UNICODE), $token]))
					throw new Exception('result');
				$pdo->commit();
				unset($_SESSION['mt_buy_tokens'][$token]);
			}
		}
		catch(Exception $e)
		{
			if($pdo->inTransaction())
				$pdo->rollBack();
			$result = $stored($token);	// a parallel request with this token bought it - show that one
			if($result === null)
				$error_text = $lang_shop['mt-chest-failed'];
		}
	}

	if($result !== null)
	{
?>
<div id="confirmation" class="mt-chest-confirmation">
    <div id="itemConfirmation" class="contrast-box">
		<div class="row-fluid clearfix">
            <div class="item-showcase grey-box span4">
                <div id="image" class="picture_wrapper">
					<span class="mt-picture"><img id="selectionImageMain" class="image mt-icon mt-chest-big" src="<?php print mt2009_item_image($item, true); ?>" alt=""></span>
				</div>
			</div>
            <div class="item-confirmation grey-box clearfix span8">
                <h3><?php print $lang_shop['thanks-for-purchase']; ?></h3>
                <div class="scrollable_container reward mt-chest-reward">
					<p class="confirmed"><?php if((int)$result['qty'] > 1) print (int)$result['qty'].' x '; print htmlspecialchars($item_name); ?></p>
					<p class="mt-chest-won-title"><?php print sprintf($lang_shop['mt-chest-won'], count($result['rolls'])); ?></p>
					<ol class="mt-chest-won">
					<?php foreach($result['rolls'] as $roll) { ?>
						<li class="mt-chest-roll<?php if($roll['kind'] != 'common') print ' mt-chest-rare'; ?>">
						<?php foreach($roll['items'] as $won) { ?>
							<span class="mt-chest-item"><img src="<?php print mt2009_item_image(['vnum' => $won['vnum'], 'type' => 1]); ?>" alt="" onerror="this.onerror=null;this.src='<?php print $shop_url; ?>images/this/noicon.png';">
							<?php print htmlspecialchars(((int)$won['count'] > 1 ? (int)$won['count'].'x ' : '').$won['name']); ?><?php if((int)$won['minutes'] > 0) print ' <em>('.htmlspecialchars(strip_tags($shop->secondsToTime((int)$won['minutes'] * 60, $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes']))).')</em>'; ?></span>
						<?php } ?>
						</li>
					<?php } ?>
					</ol>
					<?php if((int)$result['marks'] > 0) { ?>
					<p class="bill_mileage text-success"><span class="block-price"><img src="<?php print $shop_url; ?>images/this/jcoins.png" alt=""> <span class="end-price"><?php print number_format((int)$result['marks'], 0, '', '.'); ?></span></span> <?php print $lang_shop['mt-marks-got']; ?></p>
					<?php } ?>
					<p><?php print $lang_shop['find-in-warehouse']; ?></p>
				</div>
                <button class="right btn-default" onclick="javascript:$.fancybox.close(true);"><?php print $lang_shop['continue-shopping'];?></button>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript">
	// MT2009_PLUS_ITEMSHOP_V3_V7: the new balances in the header at once - no page reload when the window closes (the
	// package marked the overlay "reload": closing it reloaded the whole shop, and a click on another item meanwhile was
	// lost to that reload - the owner had to click twice)
	$(document).ready(function () {
		cardMargin();
		$('.fancybox-overlay').removeClass('reload');
		if (typeof mt2009SetBalances == 'function')
			mt2009SetBalances(<?php print (int)$account->getCoins(1, $_SESSION['id']); ?>, <?php print (int)$account->getCoins(2, $_SESSION['id']); ?>);
	});
</script>
<?php
	}
	else if(!$can_pay)
	{
		// not enough Smocze Monety: buy.php's window
		$mt_chest_fallback = true;
		include 'pages/java/buy.php';
	}
	else
	{
?>
<div id="error" class="contrast-box">
	<div class="dark-grey-box">
		<h2><i class="icon-info left"></i><?php print htmlspecialchars($item_name); ?></h2>
		<p class="mt-buy-refused"><?php print htmlspecialchars($error_text); ?></p>
		<div class="btn_wrapper"><button class="btn-default fancybox fancybox.ajax" href="<?php print $shop_url."javascript/info/".$item['id']; ?>"><i class="icon-undo2"></i></button></div>
	</div>
</div>
<?php } ?>
