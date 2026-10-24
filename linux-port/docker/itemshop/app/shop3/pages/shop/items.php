<?php
	if(!$specific_category && count($all_items))
		$id = $all_items[0]['category'];
?>
<div id="category">
	<h2>
        <ul class="breadcrumb">
			<?php if($searchString==null) { ?>
			<li>
				<a href="<?php print $shop_url.'items/'; ?>">
					<?php print $lang_shop['all_objects']; ?>
					<span class="item_count">(<?php print $count_all; ?>)</span>
				</a>
			</li>
			<?php } else { ?>
			<li>
				<a href="" title=""><?php print $lang_shop['search-result'].' "'.$searchString.'"'; ?></a>
				<span class="item_count">(<?php print $count_all; ?>)</span>
			</li>
			<?php } if($specific_category){ ?>
			<li>&rsaquo;</li>
			<li>
				<a href="<?php print $shop_url.'items/'.$id.'/'; ?>">
					<?php print $categoriesbyid[$id]['name']; ?>
					<span class="item_count">(<?php print $count_cat; ?>)</span>
				</a>
			</li>
			<?php } else if(!$specific_category && count($all_items)) { ?>
			<li>&rsaquo;</li>
			<li>
				<a href="<?php print $shop_url.'items/'.$id.'/'; ?>">
					<?php print $categoriesbyid[$id]['name']; ?>
					<span class="item_count">(<?php print $shop->getItemShopCount($id, true, $searchString); ?>)</span>
				</a>
			</li>
			<?php } ?>
		</ul>
	</h2>
    <div class="tabbable tabs-left">
		<ul id="subnavi" class="nav nav-tabs">
			<?php
			if(count($categoriesbyid)<=6)
			{
				foreach($categoriesbyid as $key => $category) if($key) {
					if($key==$id)
						$sel = " btn-catitem-active";
					else 
						$sel = "";
			?>
				<li>
					<a class="btn-catitem<?php print $sel; ?>" href="<?php print $shop_url.'items/'.$key.'/'; ?>">
						<i height="32" width="32" class="icon <?php print $categoriesbyid[$key]['icon']; ?>" class="icon"></i><br>
						<?php print $categoriesbyid[$key]['name']; ?>
					</a>
				</li>
			<?php
				}
			} else {
				$i=0;
				$second = array_slice($categoriesbyid, 5, null, true);
				
				foreach($categoriesbyid as $key => $category)
					if($i<5 && $key)
					{
						if($key==$id)
							$sel = " btn-catitem-active";
						else 
							$sel = "";
						$i++;
				?>
					<li>
						<a class="btn-catitem<?php print $sel; ?>" href="<?php print $shop_url.'items/'.$key.'/'; ?>">
							<i height="32" width="32" class="icon <?php print $category['icon']; ?>" class="icon"></i><br>
							<?php print $category['name']; ?>
						</a>
					</li>
				<?php } ?>
				<li class="has-subnavi">
					<a class="btn-catitem<?php if(isset($second[$id])) print ' btn-catitem-active'; ?>" href="javascript:void(0)">
						<i height="32" width="32" class="icon fas fa-angle-double-right"></i><br>
						<?php print $lang_shop['more']; ?>
					</a>

					<ul class="dropdown-menu up">
						<?php foreach($second as $key => $category) if($key) {
								if($key==$id)
									$sel = " btn-catitem-active";
								else 
									$sel = "";
								$i++; ?>
						<li>
							<a class="btn-subcatitem<?php print $sel; ?>" href="<?php print $shop_url.'items/'.$key.'/'; ?>"><i height="32" width="32" class="icon <?php print $categoriesbyid[$key]['icon']; ?>" class="icon"></i><?php print $categoriesbyid[$key]['name']; ?></a>
						</li>
						<?php } ?>
					</ul>

				</li>
			<?php } ?>
		</ul>
        <div class="tab-content">
			<div class="scrollable_container row-fluid">
				<?php if((!$specific_category && $count_all==0) || ($specific_category && $count_cat==0)){ ?>
				<div class="no-selected-currency js_currency" data-currency="2"><?php print $lang_shop['no-items'];?></div>
				<?php } else{ ?>
				<ul class="item-list card clearfix">
					<?php
						foreach($all_items as $key => $item)
						{
							if($key && isset($all_items[$key-1]) && $all_items[$key-1]['category']!=$item['category'])
								print '<ul class="item-list card clearfix">';
							
							$item_name = $names[$item['vnum']];
							if($item['type']==3)
								$item_name = $account_bonuses[$item['vnum']];
							if($item['book']>0)
							{
								$skill_name = $shop->getSkill($item['book']);
								$item_name.=' - '.$skill_name;
							} else if($item['book_type']!='FIX') {
								if($item['book_type']=='RANDOM_ALL_CHARS')
									$skill_name = $lang_shop['random-skill'];
								else
									$skill_name = $shop->getLocaleGameByType($item['book_type']);
								$item_name.=' - '.$skill_name;
							} else if($item['polymorph']>0)
							{
								$mob_name = $shop->getMob($item['polymorph']);
								$item_name.=' - '.$mob_name;
							}
							$final_price = $shop->getItemPrice($item['coins'], $item['discount']);
							$can_pay = true;
							$old_time = time() - strtotime($item['date']);
							$item_proto = $shop->getItem($item['vnum']);

							if($item['time']<=0)
								$item['time'] = $player->getItemProtoDuration($item_proto);
							
							$addon = $player->getItemBonusesAddon($item_proto, $item['vnum']);
							
							$bonuses = [];
							for($i=0;$i<=6;$i++)
								if($item['attrtype'.$i]>0 && $item['attrvalue'.$i]>0 && count($bonuses)<4)
									$bonuses[] = [$item['attrtype'.$i], $item['attrvalue'.$i]];
							/*
							if(!count($bonuses))
								$bonuses = $player->getItemBonuses($item_proto, $item['vnum'], 4);
							*/
							if(count($addon) || count($bonuses))
								$bonuses_name = $shop->getSpecificBonuses(array_merge(array_column($bonuses, 0), array_column($addon, 0)));
					?>
					<li class="list-item shown js_currency quickbuy" data-currency="1">
						<?php if($item['discount']>0 || $item['time']>0 || ($old_time <= 7*60*60*24) || ($item_proto['item_type']=='ITEM_COSTUME' && $item['time']==0) || $item['expire']!=null){ ?>
 						<p class="item-status item-status <?php if($item['discount']>0 || $item['expire']!=null) print 'sale-status'; else print 'new-status'; ?> js_currency_default" data-currency="1">
						<?php if($item['discount']>0) {
							$discount_left = strtotime($item['discount_expire'])-$shop->currentTime();
							if($discount_left<0)
							{
								$discount_left = 0;
								$shop->updateExpireDate($item['id']);
								$item['discount'] = 0;
							} else {
						?>
							<i class="zicon-hd-discount ttip" tooltip-content="<?php print $lang_shop['items-with-discount']; ?>"></i>
						<?php } } if($item['expire']!=null) {
							$time_left = strtotime($item['expire'])-$shop->currentTime();
							
							if($time_left<0)
							{
								$time_left = 0;
								$shop->deleteItem($item['id']);
							} else {
						?>
							<i class="zicon-hd-time-ingame ttip" tooltip-content="<?php print $lang_shop['offer-expires'].' '.$shop->secondsToTime($time_left, $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes']); ?>"></i>
						<?php } } if($item['time']>0) {
							$duration = $shop->secondsToTime($item['time']*60, $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes']);
						?>
							<i class="zicon-hd-time-real ttip" tooltip-content="<?php print $lang_shop['duration'].': '.$duration; ?>"></i>
						<?php } else if($item_proto['item_type']=='ITEM_COSTUME' && $item['time']==0) { ?>
							<i class="zicon-hd-time-real ttip" tooltip-content="<?php print $lang_shop['duration'].': '.$lang_shop['permanent']; ?>"></i>
						<?php } if(time() - strtotime($item['date']) <= 7*60*60*24) { ?>
							<i class="zicon-hd-new2 ttip" tooltip-content="<?php print $lang_shop['new-object']; ?>"></i>
						<?php } ?>
						</p>
						<?php } ?>
						<div class="contrast-box item-box inner-content clearfix" >
							<div class="desc row-fluid">
								<div class="item-description">
									<h4>
										<a class="fancybox fancybox.ajax card-heading" href="<?php print $shop_url."javascript/info/".$item['id']; ?>" title="<?php print $item_name; ?>"><?php print $item_name; ?></a>
                                    </h4>
									<div class="item-shortdesc clearfix"  >
										<a class="item-thumb fancybox fancybox.ajax" href="<?php print $shop_url."javascript/info/".$item['id']; ?>" title="<?php print $item_name; ?>">
											<img class="item-thumb" src="<?php if($item['type']!=3) print $shop_url.'images/'.$icons[$item['vnum']]['src']; else print $shop_url.'images/icons/bonuses/'.$server_item['buff'][$item['vnum']][0].'.png'; ?>">
										</a>
										<span class="category-link">
											<i height="15" width="15" class="icon <?php print $categoriesbyid[$item['category']]['icon']; ?>"></i>
											<a href="<?php print $shop_url.'items/'.$item['category'].'/'; ?>" title="<?php print $categoriesbyid[$item['category']]['name']; ?>"><?php print $categoriesbyid[$item['category']]['name']; ?></a>
										</span>
										<p><?php
											$shop_desc = $descriptions[$item['vnum']];
											if($item['type']==2)
												print '• '.$lang_shop['bonus_selection'].'<br>';
											if($item['limit_all']>0)
												print '• '.$lang_shop['available_pieces'].' <strong>'.$item['limit_all'].'</strong><br>';
											if($item['limit_account']>0)
											{
												$count_account = $shop->checkLimitAccount($item['id'], $_SESSION['id']);
												print '• '.$lang_shop['purchase_limit'].': <strong>'.($item['limit_account']-$count_account).'</strong><br>';
											}
											$description_strip_tags = strip_tags($item['description'], '<a>');
											if($description_strip_tags!='')
												print '• '.$description_strip_tags.'<br>';
											else if($shop_desc!='')
												print '• '.$shop_desc.'<br>';
											else if(isset($account_bonuses[$item['vnum']]))
												print '• '.$account_bonuses[$item['vnum']].'<br>';
											if($shop->getItem($item['vnum'], 'limit_type0')=='LEVEL')
											{
												$level = $shop->getItem($item['vnum'], 'limit_value0');
												if($level<1)
													$level=1;
												print '• '.$lang_shop['required-level'].' '.$level.'<br>';
											}
											if($item['book']>0)
												print '• '.$skill_name.'<br>';
											else if($item['book_type']=='RANDOM_ALL_CHARS')
												print '• '.$lang_shop['get-random-skill'].'<br>';
											else if($item['book_type']!='FIX')
												print '• '.$lang_shop['get-random-skill-for'].' '.$shop->getLocaleGameByType($item['book_type']).'<br>';
											else if($item['polymorph']>0)
												print '• '.$mob_name.'<br>';
											else if($item['time']>0)
												print '• '.$lang_shop['duration'].': '.$duration.'<br>';
											else if($item_proto['item_type']=='ITEM_COSTUME' && $item['time']==0)
												print '• '.$lang_shop['duration'].': '.$lang_shop['permanent'].'<br>';
											if(count($bonuses))
												foreach($bonuses as $bonus)
													if(isset($bonuses_name[$bonus[0]]))
														print '• '.sprintf($bonuses_name[$bonus[0]], $bonus[1]).'<br>';
											if(count($addon))
												foreach($addon as $bonus)
													if(isset($bonuses_name[$bonus[0]]))
														print '• '.sprintf($bonuses_name[$bonus[0]], $bonus[1]).'<br>';
										?></p>
									</div>
								</div>
								<div class="price_desc row-fluid js_currency_default" data-currency="1">
									<button class="btn-default fancybox fancybox.ajax" href="<?php print $shop_url."javascript/info/".$item['id']; ?>"><?php print $lang_shop['details']; ?> &raquo;</button>
									<p class="span5 price<?php if($item['discount']>0) print ' sale'; ?>">
										<span class="price-label"><?php print $lang_shop['price_object']; ?>:</span>
										<span class="block-price">
											<?php if($item['pay_type']==1) { if($final_price>$amount_coins) $can_pay = false; ?>
											<img class="ttip" src="<?php print $shop_url."images/this/coins.png"; ?>" tooltip-content="<?php print $lang_shop['coins']; ?>" />
											<?php } else if($item['pay_type']==2){ if($final_price>$amount_jcoins) $can_pay = false; ?>
											<img class="ttip" src="<?php print $shop_url."images/this/jcoins.png"; ?>" tooltip-content="<?php print $lang_shop['jcoins']; ?>" />
											<?php } ?>
											<span class="end-price"><?php print number_format($final_price, 0, '', '.'); ?></span>
											<?php if($item['discount']>0) { ?>
											<span class="old-price"><?php print number_format($item['coins'], 0, '', '.'); ?></span>
											<?php } ?>
										</span>
									</p>
									<button class="span5 btn-price<?php if(!$can_pay || ($item['limit_account'] && $count_account>=$item['limit_account']) || ($item['expire']!=null && $time_left<=0)) print ' btn-disabled not-available'; ?>">
										<span class="block-price">
											<?php if($item['pay_type']==1) { ?>
											<img class="ttip" src="<?php print $shop_url."images/this/coins.png"; ?>" tooltip-content="<?php print $lang_shop['coins']; ?>" />
											<?php } else if($item['pay_type']==2){ ?>
											<img class="ttip" src="<?php print $shop_url."images/this/jcoins.png"; ?>" tooltip-content="<?php print $lang_shop['jcoins']; ?>" />
											<?php } ?>
											<span class="end-price"><?php print number_format($final_price, 0, '', '.'); ?></span>
										</span>
									</button>
									<button class="span5 btn-buy fancybox fancybox.ajax" href="<?php print $shop_url."javascript/"; if($item['type']==2 || ($item['limit_account'] && $count_account>=$item['limit_account']) || ($item['expire']!=null && $time_left<=0)) print 'info'; else print 'buy'; print "/".$item['id']; ?>"><?php print $lang_shop['buy']; ?></button>
								</div>
							</div>
						</div>    						
					</li>      
					<?php
							if(isset($all_items[$key+1]) && $all_items[$key+1]['category']!=$item['category'])
								print '</ul><h3 class="clearfix">'.$categoriesbyid[$all_items[$key+1]['category']]['name'].' <span class="item_count">('.$shop->getItemShopCount($all_items[$key+1]['category'], true, $searchString).')</span></h3>';
						}
					?>
				</ul>
				<?php } ?>
                <br class="clearfloat">
            </div>
        </div>
    </div>
</div>