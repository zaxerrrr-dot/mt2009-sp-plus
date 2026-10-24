<?php if(!$error) { ?>
<div class="mg-breadcrumb-container row-fluid">
	<h2>
		<ul class="breadcrumb">
			<li><?php print $lang_shop['wheel-of-destiny']; ?></li>
		</ul>
	</h2>
</div>
<div id="wheel-game" class=" wheel lvl-<?=$current_level;?>">
	<div id="wheel-stages" class="span2 stg-hidden scrollable_container mCustomScrollbar _mCS_1">
		<?php if($wheel_levels>1) { ?>
		<ul class="wheel-stages">
			<?php
				for($i=$wheel_levels;$i>0;$i--)
				{
					print '<li id="stage-'.$i.'" class="lvl star-'.$i.' ttip'.$shop->checkWheelLevel($i, $current_level).'" tooltip-content="'.$lang_shop['jackpot'.$i].'">
								<i class="before"></i><span>'.$i.'</span><i class="after"></i>
							</li>';
					if($i>1)
						for($j=($i-1)*6;$j>($i-2)*6;$j--)
							print '<li class="stg'.$shop->checkWheelStage(1, $j, $current_stage).'"><span'.$shop->checkWheelStage(2, $j, $current_stage).'></span></li>';
				}
			?>
		</ul>
		<?php } ?>
	</div>
	<?php if($action!='start') { ?>
	<ul class="wheel-menu">
		<li>
			<a id="wheel-prices" class="btn-navitem">
				<span><?php print $lang_shop['wheel-of-destiny']; ?></span>
			</a>
		</li>
	</ul>
	<?php } ?>
	
	<div id="wheel-container" class="span8">
		<div id="wheel" class="clockwise">
			<?php if($wheel_levels>1 && $current_level<$wheel_levels) { ?>
			<div class="wheel-keys">
				<i id="key-3" class="key icon-key-wheel"><i class="before"></i></i>
				<i id="key-7" class="key icon-key-wheel"><i class="before"></i></i>
				<i id="key-11" class="key icon-key-wheel"><i class="before"></i></i>
				<i id="key-15" class="key icon-key-wheel"><i class="before"></i></i>
			</div>
			<?php } ?>
			<div class="wheel-ring"></div>
			<?php
				if($action!="start") {
			?>			
			<div class="wheel-mystery"></div>
			<?php for($i=1;$i<=$wheel_levels;$i++) { ?>
			<div id="teaser<?php print $i; ?>" class="teaser wheel-items" >
					<?php
						$items = $itemsLvl[$i];
						shuffle($items);
						foreach($items as $key => $item)
						{
					?> 				
						<img class="wheel-item-<?php print $key+1; ?> teaser" src="<?php if($item['type']!=3) print $shop_url.'images/'.$icons[$item['vnum']]['src']; else print $shop_url.'images/icons/bonuses/'.$server_item['buff'][$item['vnum']][0].'.png'; ?>" alt="" />
					<?php
						}
					?>					
			</div>
			<?php } ?>
			<div id="wheel-spinner">
				<div class="wheel-btn _wl-sprite ">
					<?php if($wheel_prices[$current_level-1] > $amount_coins){ ?>
					<a id="spinButton" class="fancybox fancybox.ajax" href="<?php print $shop_url; ?>javascript/wheel/">
					<?php } else{ ?>
					<a id="spinButton" class="" href="<?php print $shop_url.'wheel/start/'.$_SESSION['wheel']; ?>">
					<?php } ?>
						<table>
							<tr>
								<td>
									<?php print $lang_shop['spin']; ?><br /> <?php print $lang_shop['now']; ?>!<br />(<?php print $wheel_prices[$current_level-1]; ?>&nbsp;
									<img class="ttip" tooltip-content="<?php print $lang_shop['coins']; ?>" src="<?php print $shop_url."images/this/coins.png"; ?>"/>) 
								</td>
							</tr>
						</table>
					</a>
				</div>
			</div>
			<?php } else { ?>
			<div id="spinner-pointer">         
				<div id="wheel-spinner">
					<div class="wheel-btn running">
						<a id="spinButton" class="" >
							<table>
								<tr>
									<td><?php print $lang_shop['it-spins']; ?></td>
								</tr>
							</table>
						</a>
					</div>
				</div>
			</div>                        
			<div class="wheel-items">
				<?php
					foreach($itemsLvl[$current_level] as $key => $item) {
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
						if($item['count']>1)
							$item_name.=' x '.$item['count'];
				?>
				<div id="pos<?php print $key+1; ?>" class="reward wheel-item-<?php print $key+1; ?>">
					<img id="img-reward-<?php print $key+1; ?>" src="<?php if($item['type']!=3) print $shop_url.'images/'.$icons[$item['vnum']]['src']; else print $shop_url.'images/icons/bonuses/'.$server_item['buff'][$item['vnum']][0].'.png'; ?>" alt="" class="ttip" tooltip-content="<?php print $item_name; ?>" />
				</div>
				<?php
					}
				?>
			</div>
			<?php } ?>
		</div>
	</div>
	
	<div id="wheel-info" class="span2 small">
		<h3 class="wheel-welcome "><span class="welcome-lvl"><?php print $lang_shop['the-level'].' '.$current_level; ?></span></h3>
		<p>
			<?php print $lang_shop['spin-the-wheel']; ?>
			<img class="ttip" tooltip-content="<?php print $lang_shop['coins']; ?>" src="<?php print $shop_url."images/this/coins.png"; ?>" /> <?php print $wheel_prices[$current_level-1]; ?>!  
		</p>
		<?php if($current_level>1){?>
		<div class="wheel-info-timer">
			<h4><?php print $lang_shop['back-to']; ?> <strong class="back-lvl"><?php print $lang_shop['the-level'].' '.$current_level; ?></strong></h4>
			<span id="wheel-timer" class="zicon-hd-time-ingame"></span>
			<button href="<?php print $shop_url; ?>wheel/level1/" class="wheel-over ttip btn-default" tooltip-content="<?php print $lang_shop['wheel-give-up1']; ?> <br> <?php print $lang_shop['wheel-give-up2']; ?>"> <?php print $lang_shop['wheel-give-up3']; ?> </button>
		</div>
		<?php } ?>
	</div>
<?php if($action=="start") { ?>
	<div id="fancybox-reward" class="fancyboxContentContainer">
<?php
	$level_win = $key_win = false;
	
	$item_selected = $shop->getWhellPos($spinCount);
	$item = $itemsLvl[$current_level][$item_selected-1];
	
	$item = $shop->getItemShop($item['id']);
	
	$item_proto = $shop->getItem($item['vnum']);
	
	if($item['time']<=0)
		$item['time'] = $player->getItemProtoDuration($item_proto);
	
	if(($item['type']!=3 && $player->CreateItem($item, $_SESSION['id'], $add_type, [])) || ($item['type']==3 && $account->addBuff($item, $_SESSION['id'])))
	{
		$shop->addItemHistory($item['id'], $_SESSION['id'], 1, 1, $wheel_prices[$current_level-1], 2);
	} else if($add_type=='item' && $item['type']!=3 && $this->getNewPosition($item['vnum'], $_SESSION['id'])==-1)
		$shop->addItemHistory($item['id'], $_SESSION['id'], 0, 1, $wheel_prices[$current_level-1], 2);

	$item = $itemsLvl[$current_level][$item_selected-1];
	
	if(($item_selected == 3 || $item_selected == 7 || $item_selected == 11 || $item_selected == 15) && $current_level<$wheel_levels) {
		$shop->setWheelStage($_SESSION['id'], $current_stage+1);
		$key_win = true;
		if($current_level == 1 && $current_stage+1 == 6){
			$level_win = true;
			$now = $shop->currentTime();
			$time = date('Y-m-d H:i:s', $now + $wheel_lv2_time*60+15);
			$shop->updateWheelLevel($_SESSION['id'], 2, $time);
		} else if($current_level == 2 && $current_stage+1 == 12){
			$level_win = true;
			$now = $shop->currentTime();
			$time = date('Y-m-d H:i:s', $now + $wheel_lv3_time*60+15);
			$shop->updateWheelLevel($_SESSION['id'], 3, $time);
		}
	}
	
	$item = $itemsLvl[$current_level][$item_selected-1];
?>	
		<div id="wheel-reward" class="row-fluid contrast-box stage1">
			<div class="item-showcase span4 grey-box">
				<div id="image" class="picture_wrapper">
					<img id="selectionImageMain" class="image" src="<?php if($item['type']!=3) print $shop_url.'images/'.$icons[$item['vnum']]['src']; else print $shop_url.'images/icons/bonuses/'.$server_item['buff'][$item['vnum']][0].'.png'; ?>" width="242" height="242">
				</div>
			</div>
			<div class="showcase content-showcase grey-box span8 clearfix  expand">
				<h2><?php print $lang_shop['congratulations']; ?></h2>
				<p><?php print $lang_shop['you-won']; ?></p>
				<h3>
					<?php
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
						if($item['count']>1)
							$item_name.=' x '.$item['count'];
						print $item_name;
					?>
				</h3>
				<div class="text-showcase scrollable_container_fancy mCustomScrollbar"><p id="rewardDesc">
					<?php
						$shop_desc = $shop->getDesc($item['vnum']);
						$description_strip_tags = strip_tags($item['description'], '<a>');
						if($description_strip_tags!='')
							print '• '.$description_strip_tags.'<br>';
						else if($shop_desc!='')
							print '• '.$shop_desc.'<br>';
						else if(isset($account_bonuses[$item['vnum']]))
							print '• '.$account_bonuses[$item['vnum']].'<br>';
					?>
				</p></div>
				<div class="level-showcase">
					<?php if($level_win) { ?>
					<p class="lvl-info"><span class="lvl-<?php print $current_level; ?>"><?php print $current_level+1; ?></span><?php print $lang_shop['next-level']; ?></p>
					<?php } else if($key_win) { ?>
					<p class="key-info" id="keyReward"> <i class="icon-key-wheel"><i class="before"></i></i><?php print $lang_shop['found-key']; ?></p>
					<?php } ?>
					<button class="right cancel btn-default" href="<?php print $shop_url; ?>wheel/"><?php print $lang_shop['play']; ?></button>
				</div>
			</div>
		</div>
	</div>
<?php } if($action!='start') { ?>
    <div id="wheel-special-stage" class="wheel-special-stage-articles">
        <div class="contrast-box tabbable" >
			<ul class="nav nav-tabs">
				<?php for($i=1;$i<=$wheel_levels;$i++) { ?>
				<li><a class="heading-tab" href="#stg-<?php print $i ;?>" data-toggle="tab"><?php print $lang_shop['the-level'].' '.$i; ?> </a></li>
				<?php } ?>
			</ul>
			<div class="grey-box">
                <p class="game-desc"><?php print $lang_shop['spin-and-win']; ?></p>
            </div>
			<h3 style="color: #3c1e16;"><?php print $lang_shop['awards-for-level']; ?></h3>
        </div>
        <div class="tab-content" style="padding-top: 5px;">
		<?php for($i=1;$i<=$wheel_levels;$i++) { ?>
			<div class="tab-pane" id="stg-<?php print $i; ?>">
				<div class="carousell-reward-1 carousell-reward royalSlider contentslider rsDefault visibleNearby card rsHorcard">
					<?php
						foreach($shop->getWheelItems($wheel_levels, $i, true) as $item) {
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
					?> 
					<div class="list-item quickbuy">
						<?php if($item['jackpot']) { ?>
 						<p class="item-status item-status sale-status js_currency_default" data-currency="1">
							<i class="zicon-wheel ttip" tooltip-content="Jackpot"></i>
						</p>
						<?php } ?>
						<div class="contrast-box  item-box inner-content clearfix" >
							<div class="desc row-fluid">
								<div class="item-description">
									<h4>
										<a class="fancybox fancybox.ajax card-heading" href="<?php print $shop_url."javascript/info/".$item['id']; ?>"><?php print $item_name; ?></a>
                                    </h4>
									<div class="item-shortdesc clearfix"  >
										<a class="item-thumb fancybox fancybox.ajax" href="<?php print $shop_url."javascript/info/".$item['id']; ?>" title="">
											<img class="item-thumb" src="<?php if($item['type']!=3) print $shop_url.'images/'.$icons[$item['vnum']]['src']; else print $shop_url.'images/icons/bonuses/'.$server_item['buff'][$item['vnum']][0].'.png'; ?>">
										</a>
										<p>
										<?php
											$shop_desc = $descriptions[$item['vnum']];
											$description_strip_tags = strip_tags($item['description'], '<a>');
											if($item['jackpot'])
												print '• Jackpot<br>';
											$item_proto = $shop->getItem($item['vnum']);
											if($item['time']<=0)
												$item['time'] = $player->getItemProtoDuration($item_proto);
											if($item['count']>1)
												print '• '.$lang_shop['available_pieces'].' '.$item['count'].'<br>';
											if($description_strip_tags!='')
												print '• '.$description_strip_tags.'<br>';
											else if($shop_desc!='')
												print '• '.$shop_desc.'<br>';
											else if(isset($account_bonuses[$item['vnum']]))
												print '• '.$account_bonuses[$item['vnum']].'<br>';
											if($item['book']>0)
												print '• '.$skill_name.'<br>';
											else if($item['book_type']=='RANDOM_ALL_CHARS')
												print '• '.$lang_shop['get-random-skill'].'<br>';
											else if($item['book_type']!='FIX')
												print '• '.$lang_shop['get-random-skill-for'].' '.$shop->getLocaleGameByType($item['book_type']).'<br>';
											else if($item['polymorph']>0)
												print '• '.$mob_name.'<br>';
											else if($item['time']>0)
											{
												$item['time'] = $player->getItemProtoDuration($shop->getItem($item['vnum']));
												$duration = $shop->secondsToTime($item['time']*60, $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes']);
												print '• '.$lang_shop['duration'].': '.$duration.'<br>';
											}
											else if($shop->getItem($item['vnum'], 'item_type')=='ITEM_COSTUME' && $item['time']==0)
												print '• '.$lang_shop['duration'].': '.$lang_shop['permanent'].'<br>';
										?>
										</p>
									</div>
								</div>
								<div class="price_desc row-fluid js_currency_default" data-currency="1">
									<button class="btn-default fancybox fancybox.ajax " href="<?php print $shop_url."javascript/info/".$item['id']; ?>"><?php print $lang_shop['details']; ?> &raquo;</button>
								</div>
							</div>
						</div>
					</div>
					<?php
						}
					?>					
				</div>
			</div>
		<?php } ?>
		</div>
    </div>
	<?php } ?>
</div>
<?php } else { ?>
<div id="error" class="contrast-box">
	<div class="dark-grey-box">
		<?php if(!$wheel_web) { ?>
		<h2><?php print $lang_shop['it-has-returned'].' '.$lang_shop['wheel-of-destiny']; ?></h2>
		<p><?php print $lang_shop['wheel-in-game']; ?></p>
		<?php } else { ?>
		<h2><?php print $lang_shop['error']; ?></h2>
		<p><?php print $lang_shop['page-unavailable']; ?></p>
		<?php } ?>
	</div>
</div>
<?php } ?>