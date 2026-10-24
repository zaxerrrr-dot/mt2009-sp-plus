<div id="landing" class="scrollable_container">
	<div class="row-fluid">
		<div class="span12">
            <div class="row-fluid">
                <div id="promo-area" class="span12">
					<div id="zs-prmo-slider" class="span8">
						<div id="prmoSlider" class="royalSlider rsMinW">
						<?php foreach($shop->getFirstSlide() as $slide) { ?>
							<div class="rsContent slide1">
								<div class="bContainer">
									<a href="<?php if(substr($slide['link'], 0, 4) != "http") print $shop_url; print $slide['link']; ?>">
										<img src="<?php if(substr($slide['img'], 0, 4) != "http") print $shop_url; print $slide['img']; ?>">
										<?php if($slide['text']!='' || $slide['title']!='') { ?>
										<div class="slider_banner">
											<h3><?php if($slide['title']=='') print $shop_title; else print $slide['title']; ?></h3>
											<?php if($slide['text']!='') { ?>
											<p><?php print $slide['text']; ?></p>
											<?php } ?>
										</div>
										<?php } ?>
									</a>
								</div>
							</div>
						<?php } ?>
						</div>
					</div>
					<?php $secondSlide = $shop->getSecondSlide(); ?>
					<div id="zs-prmo-ad" class="span4">
						<div class="call-to-action contrast-box">
							<?php if(!$happy_hour_discount) { ?>
							<a class="hh-content" href="<?php if(substr($secondSlide['link'], 0, 4) != "http") print $shop_url; print $secondSlide['link']; ?>">
							<img src="<?php if(substr($secondSlide['img'], 0, 4) != "http") print $shop_url; print $secondSlide['img']; ?>">
							<div class="slider_banner">
							<?php if($secondSlide['text']!='' || $secondSlide['title']!='') { ?>
								<h3><?php if($secondSlide['title']=='') print $shop_title; else print $secondSlide['title']; ?></h3>        
								<?php if($secondSlide['text']!='') { ?>
								<p><?php print $secondSlide['text']; ?></p>      
								<?php } ?>
							<?php } ?>
							</div>
							</a>
							<?php } else { ?>
							<div id="happy-hour">
								<img src="<?php print $shop_url; ?>images/this/happy-hour.jpg"/>
								<a class="hh-content" href="javascript:void(0)" onClick="openPaymentLink()">
									<div class="hh-box">
										<p class="hh-text"><?php print $lang_shop['time_left']; ?>:<br/><span class="hh-timer"></span> <span class="hh-percent">+<?php print $happy_hour_discount; ?></span>% <?php print $lang_shop['coins'];?>!</p>
									</div>
									<div class="hh-box-btn">
										<button class="hh btn-price"><?php print $lang_shop['charge-your-account']; ?></button>
									</div>
								</a>
							</div>
							<?php } ?>
						</div>
					</div>
				</div>
            </div>
        </div>
        <br class="clearfloat">
        <div class="row-fluid">
            <div class="item-sample span12">
				<h2 class="heading-cat"><a class="text-link" href="<?php print $shop_url.'items/'; ?>"><?php print $lang_shop['all_objects']; ?></a><?php print $lang_shop['recently-added']; ?></h2>
				<div class="carousell royalSlider contentslider rsDefault visibleNearby card">
				<?php
					$latest_objects = $shop->getLatestObjects();
					if(count($latest_objects))
					{
						$vnums = array_column($latest_objects, 'vnum');
						$names = $shop->getMultipleNames($vnums);
						$icons = $shop->getMultipleIcon($vnums);
						$descriptions = $shop->getMultipleDesc($vnums);
					}
					
					if(count($latest_objects)>=3 && count($latest_objects)<10)
					{
						$initial = $latest_objects;
						while(count($latest_objects)<10)
							$latest_objects = array_merge($latest_objects, $initial);
					}
					
					foreach($latest_objects as $item) {
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
					<div class="span4 list-item quickbuy">
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
						<div class="contrast-box  item-box inner-content clearfix" >
							<div class="desc row-fluid">
								<div class="item-description">
									<h4>
										<a class="fancybox fancybox.ajax card-heading"  href="<?php print $shop_url."javascript/info/".$item['id']; ?>" title="<?php print $item_name; ?>"><?php print $item_name; ?></a>
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
											else if($shop_desc!='' && $item['type']!=3)
												print '• '.$shop->getDesc($item['vnum']).'<br>';
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
					</div>
				<?php
					}
				?>
				</div>
            </div>
        </div>
    </div>
</div>