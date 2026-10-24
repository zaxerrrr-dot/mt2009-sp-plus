<?php
	// MT2009_PLUS_ITEMSHOP_V3_V2: one offer as the big servers' shop draws it (the owner's saved page of
	// 23.10.2026): title with the status icon, the picture without a frame, the category with its icon, the
	// short description, and at the bottom the price button (green; grey when it cannot be paid) that turns
	// into "Kup", for stackable items with the quantity choice on the left. Used by the home page carousel and
	// the item lists (pages/shop/home.php, items.php).

	// Our ten categories (itemshop.ishop_category) and their icons: the shop's own pictures where it has one
	// for the same kind of offer, Font Awesome otherwise.
	function mt2009_category_icon($category_id, $size = 32)
	{
		global $shop_url;
		// images/gf/cat_*.png: the shop's three own (refine, service, star) and, in its colour, Font Awesome's
		// magic, scissors, shirt, khanda, paw, horse, shield (made once from css/fontawesome).
		$images = [1 => 'refine', 2 => 'magic', 3 => 'service', 4 => 'star', 5 => 'cut', 6 => 'tshirt', 7 => 'khanda',
			8 => 'paw', 9 => 'horse', 10 => 'shield-alt', 'more' => 'more'];
		$name = isset($images[$category_id]) ? $images[$category_id] : 'gem';
		return '<img width="'.$size.'" height="'.$size.'" src="'.$shop_url.'images/gf/cat_'.$name.'.png" class="icon" alt="">';
	}

	// The item picture: the old shop's icon (img/item/<icon>.png, 32 px wide) or, when that file is missing, the
	// shop's empty picture - never a broken image (the owner's screenshot: Buffi showed a crossed box).
	function mt2009_item_image($item)
	{
		global $shop_url, $server_item, $icons, $shop;
		if($item['type']==3)
			return $shop_url.'images/icons/bonuses/'.$server_item['buff'][$item['vnum']][0].'.png';
		$src = isset($icons[$item['vnum']]['src']) ? $icons[$item['vnum']]['src'] : $shop->getIcon($item['vnum']);
		if(!is_file(dirname(__DIR__, 2).'/images/'.$src))
			return $shop_url.'images/this/noicon.png';
		return $shop_url.'images/'.$src;
	}

	function mt2009_item_name($item)
	{
		global $names, $shop, $account_bonuses, $lang_shop;
		$item_name = isset($names[$item['vnum']]) ? $names[$item['vnum']] : $shop->getName($item['vnum']);
		if($item['type']==3)
			$item_name = $account_bonuses[$item['vnum']];
		if($item['book']>0)
			$item_name.=' - '.$shop->getSkill($item['book']);
		else if($item['book_type']!='FIX')
			$item_name.=' - '.($item['book_type']=='RANDOM_ALL_CHARS' ? $lang_shop['random-skill'] : $shop->getLocaleGameByType($item['book_type']));
		else if($item['polymorph']>0)
			$item_name.=' - '.$shop->getMob($item['polymorph']);
		return $item_name;
	}

	// The short description of a card: a few lines, cut with "..." like the big servers' shop.
	function mt2009_short_desc($item, $item_proto)
	{
		global $descriptions, $shop, $player, $lang_shop;
		$lines = [];
		$text = strip_tags((string)$item['description']);
		if($text=='' && isset($descriptions[$item['vnum']]))
			$text = strip_tags((string)$descriptions[$item['vnum']]);
		$text = trim(preg_replace('/\s+/u', ' ', $text));
		if($text!='')
			$lines[] = $text;
		if($item['count']>1)
			$lines[] = $lang_shop['mt-count'].': '.$item['count'];
		if(count($shop->getCostumeSets($item['vnum'])))
			$lines[] = $lang_shop['mt-set-part'];
		$out = '';
		$left = 118;
		foreach($lines as $line)
		{
			if($left <= 0)
				break;
			if(mb_strlen($line) > $left)
			{
				$line = rtrim(mb_substr($line, 0, $left)).'...';
				$left = 0;
			}
			else
				$left -= mb_strlen($line) + 12;
			$out .= '•	'.htmlspecialchars($line).'<br>';
		}
		return $out;
	}

	function mt2009_price_html($pay_type, $price)
	{
		global $shop_url, $lang_shop;
		$img = $pay_type==2 ? 'jcoins.png' : 'coins.png';
		$alt = $pay_type==2 ? $lang_shop['jcoins'] : $lang_shop['coins'];
		return '<span class="block-price"><img class="ttip" src="'.$shop_url.'images/this/'.$img.'" alt="'.$alt.'" tooltip-content="'.$alt.'">'
			.'<span class="end-price" data-value="'.(int)$price.'">'.number_format($price, 0, '', '.').'</span></span>';
	}

	function mt2009_render_tile($item, $position = 0, $extra_class = '', $tag = 'li')
	{
		global $shop, $player, $shop_url, $lang_shop, $categoriesbyid, $amount_coins, $amount_jcoins, $jcoins_back;

		$item_name = mt2009_item_name($item);
		$item_proto = $shop->getItem($item['vnum']);
		$final_price = $shop->getItemPrice($item['coins'], $item['discount']);
		$balance = $item['pay_type']==2 ? $amount_jcoins : $amount_coins;
		$can_pay = $final_price <= $balance;
		$info = $shop_url.'javascript/info/'.$item['id'];
		$buy = $shop_url.'javascript/buy/'.$item['id'];
		$cat = $item['category'];
		$cat_name = isset($categoriesbyid[$cat]['name']) ? $categoriesbyid[$cat]['name'] : '';

		if($item['time']<=0 && $item_proto)
			$item['time'] = $player->getItemProtoDuration($item_proto);

		$status = '';
		if($item['discount']>0)
			$status = '<i class="zicon-hd-discount ttip" tooltip-content="'.$lang_shop['items-with-discount'].'"></i>';
		else if($item['time']>0)
			$status = '<i class="zicon-hd-time-real ttip" tooltip-content="'.$lang_shop['duration'].': '.$shop->secondsToTime($item['time']*60, $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes']).'"></i>';
		else if(time() - strtotime($item['date']) <= 7*24*3600)
			$status = '<i class="zicon-hd-new2 ttip" tooltip-content="'.$lang_shop['new-object'].'"></i>';

		$stackable = !empty($item['stackable']) && $item['type']==1;
		$counts = $stackable ? [1, 5, 10, 20, 50] : [];

		ob_start();
?>
<<?php print $tag; ?> class="<?php if($tag=='div') print 'span4 '; ?>list-item shown js_currency quickbuy<?php print $extra_class; ?>" data-currency="<?php print (int)$item['pay_type']; ?>" data-sort-price="<?php print (int)$final_price; ?>" data-sort-name="<?php print htmlspecialchars($item_name); ?>" data-sort-sort="<?php print (int)$position; ?>">
	<div class="contrast-box item-box inner-content clearfix">
		<div class="desc row-fluid">
			<div class="item-description">
				<?php if($status!='') { ?>
				<p class="item-status js_currency_default" data-currency="<?php print (int)$item['pay_type']; ?>"><?php print $status; ?></p>
				<?php } ?>
				<h4>
					<a class="card-heading fancybox fancybox.ajax" href="<?php print $info; ?>" title="<?php print htmlspecialchars($item_name); ?>"><?php print htmlspecialchars($item_name); ?></a>
				</h4>
				<div class="item-shortdesc clearfix">
					<a class="item-thumb fancybox fancybox.ajax" href="<?php print $info; ?>" title="">
						<div class="item-thumb">
							<img class="item-thumb-63 mt-icon" src="<?php print mt2009_item_image($item); ?>" alt="<?php print htmlspecialchars($item_name); ?>" onerror="this.onerror=null;this.src='<?php print $shop_url; ?>images/this/noicon.png';">
						</div>
					</a>
					<span class="category-link">
						<?php print mt2009_category_icon($cat, 15); ?>
						<a href="<?php print $shop_url.'items/'.$cat.'/'; ?>" title="<?php print htmlspecialchars($cat_name); ?>"><?php print htmlspecialchars($cat_name); ?></a>
					</span>
					<div class="fancybox fancybox.ajax" href="<?php print $info; ?>">
						<p><?php print mt2009_short_desc($item, $item_proto); ?></p>
					</div>
				</div>
			</div>
			<div class="item-footer price_desc row-fluid js_currency_default" data-currency="<?php print (int)$item['pay_type']; ?>">
				<div class="action-box left">
					<?php if(count($counts) && $can_pay) { ?>
					<div class="zs-dropdown">
						<button class="dropdown-toggle" type="button" data-toggle="dropdown">
							<span class="dropdown-selection" data-count="1" data-price="<?php print (int)$final_price; ?>">1</span>
							<span class="btn-default"><span class="caret"></span></span>
						</button>
						<ul class="dropdown-menu">
							<?php foreach($counts as $n) { ?>
							<li><a class="dropdown-option mt-qty" data-count="<?php print $n; ?>" data-text="<?php print $n; ?>" data-price="<?php print $n*$final_price; ?>" data-href="<?php print $buy.'/?q='.$n; ?>"><span><?php print $n; ?></span></a></li>
							<?php } ?>
						</ul>
					</div>
					<?php } ?>
				</div>
				<div class="action-box right">
					<?php if($can_pay && $item['available']==1) { ?>
					<button class="span5 right btn-price"><?php print mt2009_price_html($item['pay_type'], $final_price); ?></button>
					<button class="span5 right btn-buy fancybox fancybox.ajax" href="<?php print $buy.'/?q=1'; ?>"><?php print $lang_shop['buy']; ?></button>
					<?php } else { ?>
					<button class="span5 right btn-disabled not-available ttip fancybox fancybox.ajax" href="<?php print $info; ?>" tooltip-content="<?php print $item['pay_type']==2 ? $lang_shop['mt-not-enough-marks'] : $lang_shop['not-enough-coins']; ?>"><?php print mt2009_price_html($item['pay_type'], $final_price); ?></button>
					<?php } ?>
				</div>
			</div>
		</div>
	</div>
</<?php print $tag; ?>>
<?php
		return ob_get_clean();
	}
?>
