<?php
	// MT2009_PLUS_ITEMSHOP_V3_V2: the item list as the big servers' shop draws it - the path with the counts and
	// the sort choice on the right, the categories on the left with their icons (five, the rest under "Więcej"),
	// the cards of include/functions/tile.php.
	if(!$specific_category && !$list_mode && count($all_items))
		$id = $all_items[0]['category'];
	$active_cat = ($specific_category || (!$list_mode && !$searchString)) ? (int)$id : 0;
	$list_titles = ['new' => $lang_shop['mt-new'], 'popular' => $lang_shop['mt-popular']];
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
			<?php } else if(count($all_items) && isset($categoriesbyid[$id])) { ?>
			<li>&rsaquo;</li>
			<li><a href="<?php print $shop_url.'items/'.$id.'/'; ?>" title="<?php print $categoriesbyid[$id]['name']; ?>"><?php print $categoriesbyid[$id]['name']; ?></a><span class="item_count">(<?php print $shop->getItemShopCount($id, true, $searchString); ?>)</span></li>
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
		<ul id="subnavi" class="nav nav-tabs">
			<?php
				$cats = [];
				foreach($categoriesbyid as $key => $category)
					if($key)
						$cats[$key] = $category;
				$first = array_slice($cats, 0, count($cats) > 6 ? 5 : 6, true);
				$second = array_slice($cats, count($first), null, true);
				foreach($first as $key => $category) {
			?>
			<li>
				<a class="btn-catitem cat-<?php print $key; if(mb_strlen($category['name']) > 14) print ' long'; if($key==$active_cat) print ' btn-catitem-active'; ?>" href="<?php print $shop_url.'items/'.$key.'/'; ?>">
					<?php print mt2009_category_icon($key, 32); ?>
					<br>
					<?php print $category['name']; ?>
				</a>
			</li>
			<?php } if(count($second)) { ?>
			<li class="has-subnavi">
				<a class="btn-catitem<?php if(isset($second[$active_cat])) print ' btn-catitem-active'; ?>" href="javascript:void(0)">
					<?php print mt2009_category_icon('more', 32); ?>
					<br>
					<?php print $lang_shop['more']; ?>
				</a>
				<ul class="dropdown-menu up">
					<?php foreach($second as $key => $category) { ?>
					<li>
						<a class="btn-subcatitem<?php if($key==$active_cat) print ' btn-catitem-active'; ?>" href="<?php print $shop_url.'items/'.$key.'/'; ?>"><?php print $category['name']; ?></a>
					</li>
					<?php } ?>
				</ul>
			</li>
			<?php } ?>
		</ul>
		<div class="tab-content" style="display: block;">
			<div class="scrollable_container row-fluid">
				<?php if(!count($all_items)) { ?>
				<div class="no-selected-currency js_currency" data-currency="2"><?php print $lang_shop['no-items']; ?></div>
				<?php } else {
					$open = false;
					$in_line = 0;
					foreach($all_items as $key => $item)
					{
						$new_group = !$list_mode && ($key==0 || $all_items[$key-1]['category']!=$item['category']);
						if($new_group || $key==0)
						{
							if($open)
								print '</ul>';
							if($new_group && $key>0 && isset($categoriesbyid[$item['category']]))
								print '<h3 class="clearfix">'.$categoriesbyid[$item['category']]['name'].' <span class="item_count">('.$shop->getItemShopCount($item['category'], true, $searchString).')</span></h3>';
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
