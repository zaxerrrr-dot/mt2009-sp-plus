<?php
	// MT2009_PLUS_ITEMSHOP_V3_V2: the item list as the big servers' shop draws it - the path with the counts and
	// the sort choice on the right, the categories on the left with their icons, the cards of
	// include/functions/tile.php.
	// MT2009_PLUS_ITEMSHOP_V3_V3: the in-game shop's buttons, all of them in its order (itemshop3.categories): the
	// lists, "Wykorzystaj voucher", "Konto Premium" and "Doładuj SM!" (the support page in the system's browser);
	// "Polecane" starts with the window's premium (and flash offer) card, "Kupony SM" with its note, "Oferty
	// Błyskawiczne" says when there is none.
	if(!$specific_category && !$list_mode && count($all_items))
		$id = $all_items[0]['category'];
	$active_cat = ($specific_category || (!$list_mode && !$searchString)) ? (int)$id : 0;
	$active_kind = isset($categoriesbyid[$active_cat]['kind']) ? $categoriesbyid[$active_cat]['kind'] : '';
	$list_titles = ['popular' => $lang_shop['mt-popular']];
	$cat_link = function($key) use ($shop_url, $categoriesbyid) {
		$kind = isset($categoriesbyid[$key]['kind']) ? $categoriesbyid[$key]['kind'] : 'items';
		if($kind=='topup')
			return 'href="javascript:void(0)" onclick="openPaymentLink()"';
		if($kind=='voucher')
			return 'href="'.$shop_url.'user/redeem/"';
		if($kind=='premium')
			return 'href="'.$shop_url.'user/premium/"';
		return 'href="'.$shop_url.'items/'.$key.'/"';
	};
?>
<div id="category">
	<h2>
		<ul class="breadcrumb">
			<?php if($searchString==null) { ?>
			<li><a href="<?php print $shop_url.'items/'; ?>" title="<?php print $lang_shop['all_objects']; ?>"><?php print $lang_shop['all_objects']; ?></a><span class="item_count">(<?php print $count_all; ?>)</span></li>
			<?php } else { ?>
			<li><a href="" title=""><?php print $lang_shop['search-result'].' "'.htmlspecialchars($searchString).'"'; ?></a><span class="item_count">(<?php print $count_all; ?>)</span></li>
			<?php } if($list_mode) { ?>
			<li>&rsaquo;</li>
			<li><a href="<?php print $shop_url.'items/'.$list_mode.'/'; ?>"><?php print $list_titles[$list_mode]; ?></a><span class="item_count">(<?php print $count_cat; ?>)</span></li>
			<?php } else if($specific_category) { ?>
			<li>&rsaquo;</li>
			<li><a href="<?php print $shop_url.'items/'.$id.'/'; ?>" title="<?php print $categoriesbyid[$id]['name']; ?>"><?php print $categoriesbyid[$id]['name']; ?></a><span class="item_count">(<?php print $count_cat; ?>)</span></li>
			<?php } ?>
		</ul>
		<div class="drop-sort-by">
			<form method="post" id="formArticlesSort" action="" onsubmit="return false;">
				<label> <?php print $lang_shop['mt-sort']; ?>:</label>
				<div id="searchDropdown" class="dropdown">
					<i class="icon-filter"></i>
					<button class="dropdown-toggle" type="button" data-toggle="dropdown">
						<span class="buttonText"><?php print $lang_shop['mt-sort-standard']; ?></span>
						<span class="btn-default"><span class="caret"></span></span>
					</button>
					<ul class="dropdown-menu dropdown-menu-inverted">
						<li class="dropdown-header"><i class="icon-loop3"></i><?php print $lang_shop['mt-sort']; ?></li>
						<?php foreach(['standard' => 'mt-sort-standard', 'name-up' => 'mt-sort-name-up', 'name-down' => 'mt-sort-name-down', 'price-up' => 'mt-sort-price-up', 'price-down' => 'mt-sort-price-down'] as $sort => $text) { ?>
						<li><a class="sort-option<?php if($sort=='standard') print ' active'; ?>" href="javascript:void(0);" data-value="<?php print $sort; ?>"><?php print $lang_shop[$text]; ?></a></li>
						<?php } ?>
					</ul>
				</div>
			</form>
		</div>
	</h2>
	<div class="tabbable tabs-left">
		<ul id="subnavi" class="nav nav-tabs mt-subnavi">
			<?php foreach($categoriesbyid as $key => $category) { if(!$key) continue; ?>
			<li>
				<a class="btn-catitem mt-catitem cat-<?php print $key; if($key==$active_cat) print ' btn-catitem-active'; if(in_array($category['kind'], ['auctions', 'premium', 'topup'])) print ' mt-cat-'.$category['kind']; ?>" <?php print $cat_link($key); ?><?php if($category['kind']=='topup') print ' title="'.$lang_shop['mt-open-url'].'"'; ?>>
					<?php print mt2009_category_icon($key, 20); ?><span><?php print htmlspecialchars($category['name']); ?></span>
				</a>
			</li>
			<?php } ?>
		</ul>
		<div class="tab-content" style="display: block;">
			<div class="scrollable_container row-fluid">
				<?php if($specific_category && $active_kind=='featured') { ?>
				<div class="mt-feature-card contrast-box clearfix">
					<img src="<?php print $shop_url; ?>images/item/premium.png" alt="">
					<p><?php print $lang_shop['mt-premium-card']; ?></p>
					<a class="btn-default" href="<?php print $shop_url; ?>user/premium/"><?php print $lang_shop['mt-check']; ?></a>
				</div>
				<?php if($shop->getItemShopCount(15, true) > 0) { ?>
				<div class="mt-feature-card mt-feature-auction contrast-box clearfix">
					<img src="<?php print $shop_url; ?>images/item/auctions.png" alt="">
					<p><?php print $lang_shop['mt-auctions-card']; ?></p>
					<a class="btn-default" href="<?php print $shop_url; ?>items/15/"><?php print $lang_shop['mt-check']; ?></a>
				</div>
				<?php } } else if($specific_category && $active_cat==13) { ?>
				<div class="mt-feature-card contrast-box clearfix">
					<img src="<?php print $shop_url; ?>images/item/search_item.png" alt="">
					<p><?php print $lang_shop['mt-vouchers-card']; ?></p>
				</div>
				<?php } ?>
				<?php if(!count($all_items)) { ?>
				<?php if(!($specific_category && $active_kind=='featured')) { ?>
				<div class="no-selected-currency js_currency" data-currency="2"><?php print ($specific_category && $active_kind=='auctions') ? $lang_shop['mt-no-auctions'] : $lang_shop['no-items']; ?></div>
				<?php } ?>
				<?php } else {
					$open = false;
					$in_line = 0;
					foreach($all_items as $key => $item)
					{
						$new_group = !$list_mode && !$specific_category && ($key==0 || $all_items[$key-1]['category']!=$item['category']);
						if($new_group || $key==0)
						{
							if($open)
								print '</ul>';
							if($new_group && $key>0 && isset($categoriesbyid[$item['category']]))
								print '<h3 class="clearfix">'.$categoriesbyid[$item['category']]['name'].' <span class="item_count">('.$shop->getItemShopCount($item['category'], true).')</span></h3>';
							print '<ul class="item-list card clearfix">';
							$open = true;
							$in_line = 0;
						}
						$in_line++;
						print mt2009_render_tile($item, $key, $in_line % 3 == 0 ? ' last-in-line' : '');
					}
					if($open)
						print '</ul>';
					// MT2009_PLUS_ITEMSHOP_V3_V1: the pages of header.php, with the package's own links.
					if($items_pages > 1)
					{
						$pagination_saved = $pagination;
						$pagination = $items_per_page;
						print '<div class="pagination">'.$shop->createLinksPagination($items_link, $items_page, $items_total).'</div>';
						$pagination = $pagination_saved;
					}
				} ?>
				<br class="clearfloat">
			</div>
		</div>
	</div>
</div>
