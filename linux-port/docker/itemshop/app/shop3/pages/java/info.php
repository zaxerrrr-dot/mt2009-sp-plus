<?php
	// MT2009_PLUS_ITEMSHOP_V3_V2: the item's window as the big servers' shop has it (the owner's saved page,
	// 23.10.2026): name and price on top with the Smocze Znaki you get back, the path, the picture, the tabs
	// ("Informacje" - the description, the costume set with its bonuses; "Zawartość" for a package), and the
	// purchase box below: for whom, how many (stackable items), the price now, "Kup", how the price is made.
	require_once 'include/functions/tile.php';
	$icon_src = mt2009_item_image($item);
	$marks_back = ($item['pay_type']==1 && $jcoins_back) ? (int)round($final_price*$jcoins_back/100) : 0;
	$stackable = !empty($item['stackable']) && $item['type']==1;
	$amounts = $stackable ? [1, 5, 10] : [1];
	$buy_link = $shop_url.'javascript/buy/'.$item['id'].'/';
	$char_label = $shop_char ? $shop_char['name'] : $account->getAccountData('login', $_SESSION['id']);
	$balance = $item['pay_type']==2 ? $amount_jcoins : $amount_coins;

	// The description: the catalogue's text (or the item's), then what the item is.
	$info_lines = [];
	$text = $item['description']!='' ? $item['description'] : $description;
	$text = trim(str_replace(["<p>", "</p>"], ["", "<br>"], (string)$text));
	if($text!='')
		$info_lines[] = '•	'.strip_tags($text, '<br><b><strong><a>');
	if($item['count']>1)
		$info_lines[] = '•	'.$lang_shop['mt-count'].': '.$item['count'];
	if($item['limit_account']>0)
		$info_lines[] = '•	'.$lang_shop['purchase_limit'].': '.max(0, $item['limit_account']-$count_account);
	if($item['expire']!=null && isset($time_left) && $time_left>0)
		$info_lines[] = '•	'.$lang_shop['offer-expires'].' '.$shop->secondsToTime($time_left, $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes']);
	if($shop->getItem($item['vnum'], 'limit_type0')=='LEVEL')
		$info_lines[] = '•	'.$lang_shop['required-level'].' '.max(1, (int)$shop->getItem($item['vnum'], 'limit_value0'));
	if($item['type']==3 && isset($account_bonuses[$item['vnum']]))
		$info_lines[] = '•	'.$account_bonuses[$item['vnum']];
	if($item['book_type']=='RANDOM_ALL_CHARS')
		$info_lines[] = '•	'.$lang_shop['get-random-skill'];
	else if($item['book_type']!='FIX')
		$info_lines[] = '•	'.$lang_shop['get-random-skill-for'].' '.$shop->getLocaleGameByType($item['book_type']);
	if($item['time']>0)
		$info_lines[] = '•	'.$lang_shop['duration'].': '.$shop->secondsToTime($item['time']*60, $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes']);
	else if($item_proto && $item_proto['item_type']=='ITEM_COSTUME')
		$info_lines[] = '•	'.$lang_shop['duration'].': '.$lang_shop['permanent'];
	foreach(array_merge($addon, $bonuses) as $bonus)
		if(isset($bonuses_name[$bonus[0]]))
			$info_lines[] = '•	'.sprintf($bonuses_name[$bonus[0]], $bonus[1]);

	// The costume sets this item is a part of (tools/zestawy/gen_zestawy.py): the parts and the bonuses per grade.
	$sets = $shop->getCostumeSets($item['vnum']);
	$set_names = [];
	if(count($sets))
	{
		$set_vnums = [];
		foreach($sets as $set)
			foreach($set['parts'] as $part)
				$set_vnums = array_merge($set_vnums, $part['vnums']);
		$set_names = $shop->getMultipleNames(array_values(array_unique($set_vnums)));
	}

	$bundle = $shop->getBundleItems($item['id']);
	$bundle_names = count($bundle) ? $shop->getMultipleNames(array_column($bundle, 'vnum')) : [];
?>
<div id="item-fancybox" class="scrollable_container_fancy">
<div id="itemDetails" class="contrast-box row-fluid">
	<div class="span12">
		<div class="meta-infos clearfix">
			<h2 id="name" class="left">
				<span id="selectionNameMain"><?php print htmlspecialchars($item_name); ?></span>
			</h2>
			<div id="detail-header-price" class="meta-prop">
				<div class="price">
					<?php if($final_price>0) { ?>
					<span class="price-label"><?php print $lang_shop['price_object']; ?>:</span>
					<span class="amount js_currency" data-currency="<?php print (int)$item['pay_type']; ?>" style="display: inline;">
						<span class="block-price">
							<img class="ttip" src="<?php print $shop_url.'images/this/'.($item['pay_type']==2 ? 'jcoins.png' : 'coins.png'); ?>" alt="" tooltip-content="<?php print $item['pay_type']==2 ? $lang_shop['jcoins'] : $lang_shop['coins']; ?>">
							<span class="end-price old-price"><?php print number_format($final_price, 0, '', '.'); ?></span>
						</span>
					</span>
					<?php } else { ?>
					<span class="free-label"><?php print $lang_shop['free']; ?></span>
					<?php } ?>
				</div>
				<?php if($marks_back) { ?>
				<p class="bill_mileage text-success">
					<span class="block-price"><img class="ttip" src="<?php print $shop_url; ?>images/this/jcoins.png" alt="" tooltip-content="<?php print $lang_shop['jcoins']; ?>"> <span class="end-price mt-marks-one"><?php print number_format($marks_back, 0, '', '.'); ?></span></span> <?php print $lang_shop['mt-marks-back']; ?>
				</p>
				<?php } ?>
			</div>
			<div class="breadcrumb">
				<span><a href="<?php print $shop_url; ?>"><?php print $lang_shop['mt-home']; ?></a>&rsaquo;</span>
				<span><a href="<?php print $shop_url.'items/'; ?>"><?php print $lang_shop['all_objects']; ?></a>&rsaquo;</span>
				<?php if(isset($categoriesbyid[$item['category']]['name'])) { ?>
				<span><a href="<?php print $shop_url.'items/'.$item['category'].'/'; ?>"><?php print $categoriesbyid[$item['category']]['name']; ?></a>&rsaquo;</span>
				<?php } ?>
				<span class="active"><?php print htmlspecialchars($item_name); ?></span>
			</div>
		</div>
		<div id="pictureShowcase">
			<div class="item-info clearfix">
				<div class="item-showcase grey-box span4">
					<div id="image" class="picture_wrapper">
						<img id="selectionImageMain" class="image mt-icon" src="<?php print $icon_src; ?>" alt="<?php print htmlspecialchars($item_name); ?>" onerror="this.onerror=null;this.src='<?php print $shop_url; ?>images/this/noicon.png';">
					</div>
				</div>
				<div class="tabbable item-description span8">
					<ul class="nav nav-tabs">
						<li class="active"><a href="#info" data-toggle="tab"><?php print $lang_shop['info']; ?></a></li>
						<?php if(count($bundle)) { ?>
						<li><a href="#contents" data-toggle="tab"><?php print $lang_shop['mt-contents']; ?></a></li>
						<?php } ?>
					</ul>
					<div class="tab-content">
						<div class="tab-pane scrollable_container_fancy grey-box active" id="info">
							<p id="selectionShortMain"><?php print implode('<br>', $info_lines); ?></p>
							<?php foreach($sets as $set) { ?>
							<div class="mt-set">
								<p class="mt-set-name"><strong><?php print $lang_shop['mt-set-title']; ?>: <?php print htmlspecialchars($set['name']); ?></strong></p>
								<?php if($set['id'] >= 100) { ?><p><?php print $lang_shop['mt-set-legacy']; ?></p><?php } ?>
								<p><?php print $lang_shop['mt-set-parts']; ?><br>
								<?php foreach($set['parts'] as $part) {
									$variants = [];
									foreach($part['vnums'] as $v)
									{
										$n = isset($set_names[$v]) ? $set_names[$v] : (string)$v;
										$n = htmlspecialchars($n);
										if($v == $item['vnum'])
											$n = '<strong>'.$n.'</strong>';
										if(!in_array($n, $variants))
											$variants[] = $n;
									}
									print '•	'.htmlspecialchars($part['label']).': '.implode(', ', $variants).'<br>';
								} ?>
								</p>
								<p><?php print $lang_shop['mt-set-bonus']; ?> (<?php print count($set['parts']); ?> <?php print $lang_shop['mt-set-parts-count']; ?>):<br>
								<?php foreach($set['grades'] as $grade => $lines) { ?>
									<span class="mt-set-grade"><?php print sprintf($lang_shop['mt-set-grade'], $grade); ?>:</span> <?php print htmlspecialchars(implode(', ', $lines)); ?><br>
								<?php } ?>
								</p>
								<?php if(count($set['grades']) > 1) { ?><p class="mt-set-note"><?php print $lang_shop['mt-set-note']; ?></p><?php } ?>
							</div>
							<?php } ?>
						</div>
						<?php if(count($bundle)) { ?>
						<div class="tab-pane scrollable_container_fancy grey-box" id="contents">
							<table class="table mt-contents">
								<thead><tr><th><?php print $lang_shop['mt-name']; ?></th><th><?php print $lang_shop['mt-amount']; ?></th></tr></thead>
								<tbody>
								<?php foreach($bundle as $b) { ?>
									<tr><td><?php print htmlspecialchars(isset($bundle_names[$b['vnum']]) ? $bundle_names[$b['vnum']] : $b['vnum']); ?></td><td><?php print (int)$b['count']; ?></td></tr>
								<?php } ?>
								</tbody>
							</table>
						</div>
						<?php } ?>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
<div id="itemBuy" class="contrast-box variants">
	<div class="grey-box clearfix">
		<div class="dark-grey-box clearfix">
			<div class="contrast-box 1">
				<form class="clearfix" onsubmit="return false;">
					<label class="js_currency" data-currency="<?php print (int)$item['pay_type']; ?>" style="display: block;">
						<span class="unitCount">1</span> <?php print $lang_shop['mt-pieces-buy']; ?>
					</label>
					<span class="one_char current_purchase_char"> <?php print htmlspecialchars($char_label); ?></span>
				</form>
				<?php if(count($amounts) > 1 && $item['available']==1 && $can_pay) { ?>
				<div class="amount clearfix js_currency" data-currency="<?php print (int)$item['pay_type']; ?>" style="display: block;">
					<label><?php print $lang_shop['mt-choose-amount']; ?></label>
					<ul id="js_button_container" class="clearfix">
						<?php foreach($amounts as $n) { ?>
						<li><button type="button" class="btn-discount btn-default<?php if($n==1) print ' btn-active'; ?>" data-variant="<?php print $n; ?>" value="<?php print $n; ?>"><?php print $n; ?></button></li>
						<?php } ?>
					</ul>
				</div>
				<?php } ?>
				<div class="arrow"></div>
			</div>
			<div id="buy">
				<?php if($item['available']==1) { ?>
				<form action="" method="get" onsubmit="return false;">
					<p><?php print $lang_shop['mt-now-for']; ?></p>
					<p class="bill_price block-price"><img class="ttip" src="<?php print $shop_url.'images/this/'.($item['pay_type']==2 ? 'jcoins.png' : 'coins.png'); ?>" alt=""> <span class="end-price mt-total"><?php print number_format($final_price, 0, '', '.'); ?></span></p>
					<div class="buy-btn-box clearfix">
						<div class="btn-group">
							<?php if($can_pay) { ?>
							<button type="button" class="btn-price" name="changer" style="display: inline-block;"><?php print $lang_shop['buy']; ?></button>
							<button id="purchaseLink1" class="js_currency fancybox fancybox.ajax btn-buy" data-currency="<?php print (int)$item['pay_type']; ?>" href="<?php print $buy_link.'?q=1'; ?>" style="display: none;"><?php print $lang_shop['buy-now']; ?></button>
							<?php } else { ?>
							<button class="btn-disabled ttip" style="display: inline-block;" href="javascript:void(0);" tooltip-content="<?php print $item['pay_type']==2 ? $lang_shop['mt-not-enough-marks'] : $lang_shop['not-enough-coins']; ?>"><?php print $lang_shop['buy']; ?></button>
							<?php } ?>
						</div>
					</div>
				</form>
				<?php } else { ?>
				<div class="buy-btn-box clearfix">
					<button class="btn-default" onclick="location.href='<?php print $shop_url.'items/'; ?>'"><?php print $lang_shop['all_objects']; ?></button>
				</div>
				<?php } ?>
			</div>
		</div>
		<?php if($item['available']==1 && $final_price>0) { ?>
		<p class="bill_sum js_currency" data-currency="<?php print (int)$item['pay_type']; ?>" style="display: block;">
			<i class="icon-info"></i> <?php print $lang_shop['mt-final-price']; ?>
			<strong class="bill_amount">1</strong> <?php print $lang_shop['mt-pieces']; ?> <span class="coin15px">&times;<?php print number_format($final_price, 0, '', '.'); ?></span> =
			<img class="ttip" src="<?php print $shop_url.'images/this/'.($item['pay_type']==2 ? 'jcoins.png' : 'coins.png'); ?>" alt="">
			<strong class="bill_price mt-total"><?php print number_format($final_price, 0, '', '.'); ?></strong>
			<?php if($marks_back) { ?>
			<span class="bill_mileage text-success">
				<span class="block-price"><img class="ttip" src="<?php print $shop_url; ?>images/this/jcoins.png" alt=""> <span class="end-price mt-marks"><?php print number_format($marks_back, 0, '', '.'); ?></span></span> <?php print $lang_shop['mt-marks-back']; ?>
			</span>
			<?php } ?>
		</p>
		<?php } ?>
	</div>
</div>
</div>
<script type="text/javascript">
	initFocusClear();
	$('.ttip').tipTip(zs.data.ttip);
	(function () {
		var price = <?php print (int)$final_price; ?>, back = <?php print (int)$jcoins_back; ?>, payType = <?php print (int)$item['pay_type']; ?>;
		var link = '<?php print $buy_link; ?>';
		function fmt(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, '.'); }
		$('#buy .btn-price').on('click', function (e) {
			if ($(this).hasClass('btn-disabled')) { e.preventDefault(); return; }
			$(this).hide();
			$('#buy .btn-buy').show('fade');
		});
		$('#js_button_container .btn-discount').on('click', function () {
			var n = parseInt($(this).val(), 10);
			$('#js_button_container .btn-discount').removeClass('btn-active');
			$(this).addClass('btn-active');
			$('.unitCount, #itemBuy .bill_amount').text(n);
			$('#itemBuy .mt-total').text(fmt(n * price));
			if (payType == 1)
				$('#itemBuy .mt-marks').text(fmt(Math.round(n * price * back / 100)));
			$('#buy .btn-buy').attr('href', link + '?q=' + n).hide();
			$('#buy .btn-price').show();
		});
	})();
</script>
