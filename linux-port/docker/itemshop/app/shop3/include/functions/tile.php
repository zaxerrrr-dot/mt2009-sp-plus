<?php
	// MT2009_PLUS_ITEMSHOP_V3_V2: one offer as the big servers' shop draws it (the owner's saved page of
	// 23.10.2026): title with the status icon, the picture without a frame, the category with its icon, the
	// short description, and at the bottom the price button (green; grey when it cannot be paid) that turns
	// into "Kup", for stackable items with the quantity choice on the left. Used by the home page carousel and
	// the item lists (pages/shop/home.php, items.php).
	// MT2009_PLUS_ITEMSHOP_V3_V6: also the second shop's own lines (itemshop3.v3_lines - the big servers' list, the set
	// pieces, the set chests with their own picture and 1/3/5/10 at once).
	// MT2009_PLUS_ITEMSHOP_V3_V3: the lines are the in-game shop's (itemshop3.shop onto common.itemshop_items): its
	// name with the window's suffix, its quantities (1, 5, 10 within the stack size), its level floor, the VIP
	// effects (refused while the premium account runs), promotions and flash offers; the picture at its own size in
	// a column of its own (no stretched, pixelated icon over the text); the description cut at a word.

	// The category icons (itemshop3.categories icon): images/gf/cat_<icon>.png - the shop's own pictures and, in
	// their colour, Font Awesome's (made once from css/fontawesome).
	function mt2009_category_icon($category_id, $size = 32)
	{
		global $shop_url, $categoriesbyid;
		if($category_id === 'more')
			$name = 'more';
		else
			$name = isset($categoriesbyid[$category_id]['icon']) && $categoriesbyid[$category_id]['icon']!='' ? $categoriesbyid[$category_id]['icon'] : 'gem';
		return '<img width="'.$size.'" height="'.$size.'" src="'.$shop_url.'images/gf/cat_'.$name.'.png" class="icon" alt="">';
	}

	// The item picture: img/item/<vnum>.png (tools/itemshop3/gen_shop_icons.py), else the web catalogue's icon, else
	// the shop's empty picture - never a broken image.
	// MT2009_PLUS_ITEMSHOP_V3_V6: a line with its own picture (a set chest: images/chests/<id>.png, 242 px as the big
	// servers' detail picture; the cards take the 98 px one, <id>_98.png).
	function mt2009_item_image($item, $big = false)
	{
		global $shop_url, $server_item, $icons, $shop;
		if(!empty($item['image']))
		{
			$small = preg_replace('/\.png$/', '_98.png', $item['image']);
			$dir = dirname(__DIR__, 2).'/';
			if(!$big && is_file($dir.$small))
				return $shop_url.$small;
			return is_file($dir.$item['image']) ? $shop_url.$item['image'] : $shop_url.'images/this/noicon.png';
		}
		if($item['type']==3)
			return $shop_url.'images/icons/bonuses/'.$server_item['buff'][$item['vnum']][0].'.png';
		$dir = dirname(__DIR__, 2).'/images/';
		if(is_file($dir.'item/'.(int)$item['vnum'].'.png'))
			return $shop_url.'images/item/'.(int)$item['vnum'].'.png';
		$src = isset($icons[$item['vnum']]['src']) ? $icons[$item['vnum']]['src'] : $shop->getIcon($item['vnum']);
		if(!is_file($dir.$src))
			return $shop_url.'images/this/noicon.png';
		return $shop_url.'images/'.$src;
	}

	function mt2009_item_name($item)
	{
		global $names, $shop, $account_bonuses, $lang_shop;
		if(isset($item['name']) && $item['name']!='')
			$item_name = $item['name'];
		else
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

	// The description of a line as plain lines: the web catalogue's text for the vnum (the view's description), else
	// the client's tooltip text (include/db/client_itemdesc.json, tools/itemshop3/gen_client_desc.py). "<br>" and
	// new lines are separate lines (the cards ran "30 dni.Tylko dla postaci" together).
	function mt2009_item_desc_lines($item)
	{
		global $descriptions;
		static $client = null;
		$text = isset($item['description']) ? (string)$item['description'] : '';
		if(trim(strip_tags($text))=='' && isset($descriptions[$item['vnum']]))
			$text = (string)$descriptions[$item['vnum']];
		if(trim(strip_tags($text))=='')
		{
			if($client === null)
			{
				$file = dirname(__DIR__).'/db/client_itemdesc.json';
				$client = is_file($file) ? json_decode(file_get_contents($file), true) : [];
				if(!is_array($client))
					$client = [];
			}
			$text = isset($client[(string)(int)$item['vnum']]) ? $client[(string)(int)$item['vnum']] : '';
		}
		$text = preg_replace('#<\s*br\s*/?\s*>|</p>|\r?\n#i', "\n", $text);
		$lines = [];
		foreach(explode("\n", strip_tags($text)) as $line)
		{
			$line = trim(preg_replace('/\s+/u', ' ', html_entity_decode($line, ENT_QUOTES, 'UTF-8')));
			if($line!='')
				$lines[] = $line;
		}
		return $lines;
	}

	// Does the description already say how long the item lasts (the web catalogue's "Czas: 30 dni.")?
	function mt2009_desc_has_time($lines)
	{
		foreach($lines as $line)
			if(preg_match('/^(•\s*)?Czas( trwania)?\s*:/iu', $line))
				return true;
		return false;
	}

	// Cut at a word, never in the middle of one.
	function mt2009_cut_words($text, $max)
	{
		if(mb_strlen($text) <= $max)
			return $text;
		$cut = mb_substr($text, 0, $max);
		$sp = mb_strrpos($cut, ' ');
		if($sp !== false && $sp > $max * 0.6)
			$cut = mb_substr($cut, 0, $sp);
		return rtrim($cut, " ,.;:-").'…';
	}

	// The short description of a card: up to three lines of about 110 characters in all, cut at a word with "…"
	// (the whole text is in the item's window).
	function mt2009_short_desc($item, $item_proto)
	{
		global $shop, $lang_shop;
		$lines = mt2009_item_desc_lines($item);
		if(!empty($item['auction']))
		{
			// a flash offer: its time and limit first (the card's few lines would cut them off)
			$first = [mt2009_auction_line($item)];
			if((int)$item['auction_account_limit'] > 0)
				$first[] = sprintf($lang_shop['mt-auction-limit-info'], (int)$item['auction_account_limit']);
			$lines = array_merge($first, $lines);
		}
		if($item['count']>1)
			$lines[] = $lang_shop['mt-count'].': '.$item['count'];
		if(!empty($item['min_level']))
			$lines[] = sprintf($lang_shop['mt-min-level'], (int)$item['min_level']);
		if(count($shop->getCostumeSets($item['vnum'])))
			$lines[] = $lang_shop['mt-set-part'];
		if(!empty($item['chest']))
			$lines = [$lang_shop['mt-chest-short']];	// MT2009_PLUS_ITEMSHOP_V3_V6
		$out = [];
		$left = 110;
		foreach($lines as $line)
		{
			if($left < 12 || count($out) >= 3)
			{
				if(mb_substr($out[count($out) - 1], -1)!='…')
					$out[count($out) - 1] .= ' …';
				break;
			}
			$short = mt2009_cut_words($line, $left);
			$out[] = htmlspecialchars($short);
			$left -= mb_strlen($short) + 14;
			if(mb_substr($short, -1)=='…')
				break;
		}
		return count($out) ? '•	'.implode('<br>•	', $out) : '';
	}

	function mt2009_price_html($pay_type, $price)
	{
		global $shop_url, $lang_shop;
		$img = $pay_type==2 ? 'jcoins.png' : 'coins.png';
		$alt = $pay_type==2 ? $lang_shop['jcoins'] : $lang_shop['coins'];
		return '<span class="block-price"><img class="ttip" src="'.$shop_url.'images/this/'.$img.'" alt="'.$alt.'" tooltip-content="'.$alt.'">'
			.'<span class="end-price" data-value="'.(int)$price.'">'.number_format($price, 0, '', '.').'</span></span>';
	}

	// The quantities the in-game window offers (ItemShopQuestion.SetButtons): 1, 5 with a stack of 5, 10 with 10.
	function mt2009_quantities($item)
	{
		// MT2009_PLUS_ITEMSHOP_V3_V6: a set chest - 1, 3, 5 or 10 at once (each one rolled on its own)
		if(!empty($item['chest']))
			return (int)$item['count'] > 1 ? [1] : [1, 3, 5, 10];	// MT2009_PLUS_ITEMSHOP_V3_V8: a pack (10+1, 20+3) once at a time
		if(empty($item['stackable']) || $item['type']!=1)
			return [1];
		$max = isset($item['max_stack']) ? (int)$item['max_stack'] : 1;
		$q = [1];
		if($max >= 5)
			$q[] = 5;
		if($max >= 10)
			$q[] = 10;
		return $q;
	}

	// Why the line cannot be bought now ('' = it can): the Arezzo module off, a flash offer not running, the level
	// floor, a VIP effect while the premium account runs (CItemShopManager::BuyItem), too little currency.
	function mt2009_buy_block($item, $final_price, $qty = 1)
	{
		global $lang_shop, $shop_char, $amount_coins, $amount_jcoins, $premium_active, $shop;
		// MT2009_PLUS_ISHOP_ROTACJA_V1: a costume set chest that is not one of today's, a set piece of no chest of today -
		// refused here, so in buy.php and buy_chest.php too (server side, not only hidden)
		if(isset($shop) && $shop && ($rot = $shop->rotationBlock($item)) != '')
			return $rot;
		if(!empty($item['arezzo_locked']))
			return $lang_shop['mt-arezzo-off'];
		if(!empty($item['auction']) && $item['available']!=1)
			return (!empty($item['auction_start']) && strtotime($item['auction_start']) > time()) ? $lang_shop['mt-auction-not-started'] : $lang_shop['mt-auction-ended'];
		if($item['available']!=1)
			return $lang_shop['mt-not-available'];
		if(!empty($item['min_level']) && (!$shop_char || (int)$shop_char['level'] < (int)$item['min_level']))
			return sprintf($lang_shop['mt-min-level'], (int)$item['min_level']);
		if(!empty($item['vip']) && !empty($premium_active))
			return $lang_shop['mt-vip-premium'];
		$balance = $item['pay_type']==2 ? $amount_jcoins : $amount_coins;
		if($final_price * $qty > $balance)
			return $item['pay_type']==2 ? $lang_shop['mt-not-enough-marks'] : $lang_shop['not-enough-coins'];
		return '';
	}

	// The time a flash offer still runs / starts in, for the card and the window.
	function mt2009_auction_line($item)
	{
		global $shop, $lang_shop;
		if(empty($item['auction']))
			return '';
		$now = time();
		$start = strtotime($item['auction_start']);
		$end = strtotime($item['expire']);
		if($now < $start)
			return sprintf($lang_shop['mt-auction-starts'], strip_tags($shop->secondsToTime($start - $now, $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes'])));
		if($now < $end)
			return sprintf($lang_shop['mt-auction-ends'], strip_tags($shop->secondsToTime(max(60, $end - $now), $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes'])));
		return $lang_shop['mt-auction-ended'];
	}

	function mt2009_render_tile($item, $position = 0, $extra_class = '', $tag = 'li')
	{
		global $shop, $player, $shop_url, $lang_shop, $categoriesbyid;

		$item_name = mt2009_item_name($item);
		$item_proto = $shop->getItem($item['vnum']);
		$final_price = $shop->getItemPrice($item['coins'], $item['discount']);
		$block = mt2009_buy_block($item, $final_price);
		$can_pay = $block=='';
		$info = $shop_url.'javascript/info/'.$item['id'];
		$cat = $item['category'];
		$cat_name = isset($categoriesbyid[$cat]['name']) ? $categoriesbyid[$cat]['name'] : '';

		if($item['time']<=0 && $item_proto)
			$item['time'] = $player->getItemProtoDuration($item_proto);

		$status = '';
		if(!empty($item['auction']))
			$status = '<i class="zicon-hd-time-real ttip" tooltip-content="'.htmlspecialchars(mt2009_auction_line($item)).'"></i>';
		else if(!empty($item['promo']))
			$status = '<i class="zicon-hd-discount ttip" tooltip-content="'.$lang_shop['items-with-discount'].'"></i>';
		else if($item['time']>0)
			$status = '<i class="zicon-hd-time-real ttip" tooltip-content="'.$lang_shop['duration'].': '.strip_tags($shop->secondsToTime($item['time']*60, $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes'])).'"></i>';

		$counts = $can_pay ? mt2009_quantities($item) : [1];

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
				<div class="item-shortdesc mt-shortdesc clearfix">
					<a class="item-thumb mt-thumb fancybox fancybox.ajax" href="<?php print $info; ?>" title="">
						<span class="mt-thumb-cell"><img class="mt-icon" src="<?php print mt2009_item_image($item); ?>" alt="<?php print htmlspecialchars($item_name); ?>" onerror="this.onerror=null;this.src='<?php print $shop_url; ?>images/this/noicon.png';"></span>
					</a>
					<div class="mt-shorttext">
						<span class="category-link">
							<?php print mt2009_category_icon($cat, 15); ?>
							<a href="<?php print $shop_url.'items/'.$cat.'/'; ?>" title="<?php print htmlspecialchars($cat_name); ?>"><?php print htmlspecialchars($cat_name); ?></a>
						</span>
						<div class="fancybox fancybox.ajax" href="<?php print $info; ?>">
							<p><?php print mt2009_short_desc($item, $item_proto); ?></p>
						</div>
					</div>
				</div>
			</div>
			<div class="item-footer price_desc row-fluid js_currency_default" data-currency="<?php print (int)$item['pay_type']; ?>">
				<div class="action-box left">
					<?php if(count($counts) > 1) { ?>
					<div class="zs-dropdown">
						<button class="dropdown-toggle" type="button" data-toggle="dropdown">
							<span class="dropdown-selection" data-count="1" data-price="<?php print (int)$final_price; ?>">1</span>
							<span class="btn-default"><span class="caret"></span></span>
						</button>
						<ul class="dropdown-menu">
							<?php foreach($counts as $n) { ?>
							<li><a class="dropdown-option mt-qty" data-count="<?php print $n; ?>" data-text="<?php print $n; ?>" data-price="<?php print $n*$final_price; ?>" data-href="<?php print $info.'/?q='.$n; ?>"><span><?php print $n; ?></span></a></li>
							<?php } ?>
						</ul>
					</div>
					<?php } else if(!empty($item['promo']) && (int)$item['base_price'] > (int)$final_price) { ?>
					<span class="mt-old-price"><?php print mt2009_price_html($item['pay_type'], $item['base_price']); ?></span>
					<?php } ?>
				</div>
				<div class="action-box right">
					<?php if($can_pay) { ?>
					<?php // MT2009_PLUS_ITEMSHOP_V3_V4: the price opens the item's window (picture, Informacje, for whom, how many,
					      // "Kup" there buys at once) with the card's quantity - no "Kup" on the card any more (the owner's round 2) ?>
					<button class="span5 right btn-price mt-price-info fancybox fancybox.ajax" href="<?php print $info.'/?q=1'; ?>"><?php print mt2009_price_html($item['pay_type'], $final_price); ?></button>
					<?php } else { ?>
					<button class="span5 right btn-disabled not-available ttip fancybox fancybox.ajax" href="<?php print $info; ?>" tooltip-content="<?php print htmlspecialchars($block); ?>"><?php print mt2009_price_html($item['pay_type'], $final_price); ?></button>
					<?php } ?>
				</div>
			</div>
		</div>
	</div>
</<?php print $tag; ?>>
<?php
		return ob_get_clean();
	}
