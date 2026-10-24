<div id="itemDetails" class="row-fluid contrast-box">
	<div class="span12">
		<h2 id="name">
            <div class="price">
				<?php
					if($final_price>0) {
				?>
				<span class="price-label"> <?php print $lang_shop['price_object']; ?>: </span>
				<span class="amount js_currency" data-currency="1" >
					<span class="block-price">
						<?php if($item['pay_type']==1) { ?>
						<img class="ttip" src="<?php print $shop_url."images/this/coins.png"; ?>" tooltip-content="<?php print $lang_shop['coins']; ?>" />
						<?php } else if($item['pay_type']==2) { ?>
						<img class="ttip" src="<?php print $shop_url."images/this/jcoins.png"; ?>" tooltip-content="<?php print $lang_shop['jcoins']; ?>" />
						<?php } ?>
						<span class="end-price old-price"> <?php print number_format($item['coins'], 0, '', '.'); ?></span>
						<?php if($item['discount']>0) { ?>
						<span class="end-price red sale-amount"><?php print number_format($final_price, 0, '', '.'); ?></span>
						<?php } ?>
					</span>
				</span>
				<?php } else if($item['wheel_level']>0 && $final_price==0)
							print '<div class="price"><span class="free-label">'.$lang_shop['wheel-of-destiny'].'</span></div>';
				else print '<div class="price"><span class="free-label">'.$lang_shop['free'].'</span></div>'; ?>
			</div>
			<span id="selectionNameMain"> <?php print $item_name; ?> </span>
		</h2>
		<div class="meta-infos clearfix">
			<div class="breadcrumb">
                <span><a href="<?php print $shop_url.'items/'; ?>"><?php print $lang_shop['all_objects']; ?></a>&rsaquo;</span>
				<?php if(isset($categoriesbyid[$item['category']]['name'])) { ?>
				<span><a href="<?php print $shop_url.'items/'.$item['category'].'/'; ?>"><?php print $categoriesbyid[$item['category']]['name']; ?></a>&rsaquo;</span>
				<?php } ?>
				<span class="active"><?php print $item_name; ?></span>
			</div>
			<?php if($item['discount']>0) { ?>
			<p class="item-status sale-status"><?php print $lang_shop['reduced'];?></p>
			<?php } if($item['pay_type']==1 && $jcoins_back){ ?>
			<p class="bill_mileage text-success">
				<?php print $lang_shop['credited-with']; ?>
				<span class="block-price">
					<img class="ttip" src="<?php print $shop_url."images/this/jcoins.png"; ?>" tooltip-content="<?php print $lang_shop['jcoins']; ?>" />
					<span class="end-mileage"><?php print number_format(round($final_price*$jcoins_back/100), 0, '', '.'); ?></span>
				</span>.
			</p>
			<?php } ?>
		</div>
		<div id="pictureShowcase">
			<div class="item-info clearfix">
				<div class="item-showcase grey-box  span4">
					<div id="image" class="picture_wrapper ">
						<img id="selectionImageMain" class="image" src="<?php if($item['type']!=3) print $shop_url.'images/'.$shop->getIcon($item['vnum']); else print $shop_url.'images/icons/bonuses/'.$server_item['buff'][$item['vnum']][0].'.png'; ?>" width="242" height="242" />
					</div>
				</div>
				<div class="tabbable item-description span8">
					<ul class="nav nav-tabs">
						<?php if($item['type']==2) { ?>
						<li class="active"><a href="#bonus_selection" data-toggle="tab"><?php print $lang_shop['bonus_selection']; ?></a></li>
						<?php } ?>
						<li<?php if($item['type']!=2) print ' class="active"'; ?>><a href="#info" data-toggle="tab"><?php print $lang_shop['info']; ?></a></li>
						<?php if($description!='' || $item['description']!='') { ?>
						<li><a href="#description" data-toggle="tab"><?php print $lang_shop['description']; ?></a></li>
						<?php } if(count($bonuses)) { ?>
						<li><a href="#bonuses" data-toggle="tab"><?php print $lang_shop['bonuses']; ?></a></li>
						<?php } ?>
					</ul>
					<div class="tab-content ">
						<?php $hide_buy = false; if($item['type']==2) { ?>
						<div class="tab-pane scrollable_container_fancy grey-box active" id="bonus_selection">
							<p id="selectionShortMain">
								<div class="form-group">
									<?php
										$i=0;
										$new_link = '';
										foreach($bonus_selection[0] as $key => $bonus) { $new_link.=$key.','; ?>
										<select class="form-control" style="width: 100%" name="attrtype<?php print $i; ?>" id="attrtype<?php print $i; ?>" style="margin-bottom: 1rem;" form="buy_item" required>
											<option value="<?php print $key; ?>" selected="selected"><?php print sprintf($bonuses_name[$key], $bonus); ?></option>
										</select>
									<?php $i++; } foreach($bonus_selection[1] as $key => $bonus) if($i<$item['bonuses_count']) { ?>
										<select onChange="use(this, '<?php print $shop_url."javascript/buy/".$item['id']; ?>/')" style="width: 100%" class="form-control" name="attrtype<?php print $i; ?>" id="attrtype<?php print $i; ?>" style="margin-bottom: 1rem;" form="buy_item" required>
											<option value="" selected="selected"><?php print $lang_shop['bonus_selection'].' #'.($i+1); ?></option>
											<?php foreach($bonus_selection[1] as $key => $bonus) { ?>
											<option value="<?php print $key; ?>"><?php print sprintf($bonuses_name[$key], $bonus); ?></option>
											<?php } ?>
										</select>
									<?php $i++; $hide_buy = true; } 
										$new_link = rtrim($new_link,",");
									?>
								</div>
							</p>
						</div>
						<?php } ?>
						<div class="tab-pane scrollable_container_fancy grey-box<?php if($item['type']!=2) print ' active'; ?>" id="info">
							<p id="selectionShortMain">
										<?php
											if($item['limit_account']>0)
											{
												if(($item['limit_account']-$count_account)==0)
													print '<p class="text-info limit-info"><i class="icon-info"></i>'.$lang_shop['reached-limit'].'</p>';
												else
													print '<p class="text-info limit-info"><i class="icon-info"></i>'.$lang_shop['purchase_limit'].': <strong>'.($item['limit_account']-$count_account).'</strong></p>';
											}
											if($item['expire']!=null && $time_left>0)
												print '• '.$lang_shop['offer-expires'].' '.$shop->secondsToTime($time_left, $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes']).'<br>';
											if($item['type']==2)
												print '• '.$lang_shop['bonus_selection'].'<br>';
											if($item['limit_all']>0)
												print '• '.$lang_shop['available_pieces'].' <strong>'.$item['limit_all'].'</strong><br>';
											if($shop->getItem($item['vnum'], 'limit_type0')=='LEVEL')
											{
												$level = $shop->getItem($item['vnum'], 'limit_value0');
												if($level<1)
													$level=1;
												print '• '.$lang_shop['required-level'].' '.$level.'<br>';
											}
											if($item['type']==3 && isset($account_bonuses[$item['vnum']]))
												print '• '.$account_bonuses[$item['vnum']].'<br>';
											if($item['book']>0)
												print '• '.$item_name.'<br>';
											else if($item['book_type']=='RANDOM_ALL_CHARS')
												print '• '.$lang_shop['get-random-skill'].'<br>';
											else if($item['book_type']!='FIX')
												print '• '.$lang_shop['get-random-skill-for'].' '.$shop->getLocaleGameByType($item['book_type']).'<br>';
											else if($item['polymorph']>0)
												print '• '.$mob_name.'<br>';
											else if($item['time']>0) {
												$duration = $shop->secondsToTime($item['time']*60, $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes']);
												print '• '.$lang_shop['duration'].': '.$duration.'<br>';
											}
											else if($item_proto['item_type']=='ITEM_COSTUME' && $item['time']==0)
												print '• '.$lang_shop['duration'].': '.$lang_shop['permanent'].'<br>';
											if(count($addon))
												foreach($addon as $bonus)
													if(isset($bonuses_name[$bonus[0]]))
														print '• '.sprintf($bonuses_name[$bonus[0]], $bonus[1]).'<br>';
										?>
							</p>
						</div>
						<div class="tab-pane scrollable_container_fancy grey-box " id="description">
							<p id="selectionLongMain"><?php if($item['description']!='') {
									$info_description = str_replace("<p>", "", $item['description']);
									$info_description = str_replace("</p>", "<br />", $info_description);
									print $info_description;
								} else print $shop->getDesc($item['vnum']); ?></p>
						</div>
						<?php if(count($bonuses)) { ?>
						<div class="tab-pane scrollable_container_fancy grey-box " id="bonuses">
							<p id="selectionLongMain">
							<?php foreach($bonuses as $bonus) if(isset($bonuses_name[$bonus[0]])) print '• '.sprintf($bonuses_name[$bonus[0]], $bonus[1]).'<br>'; ?>
							</p>
						</div>
						<?php } ?>
					</div>
				</div>
			</div>
		</div>
    </div>
</div>

<div id="itemBuy" class="contrast-box">
    <div class="grey-box clearfix">
        <div class=" dark-grey-box clearfix">
			<div class="contrast-box 1 ">
				<label class="js_currency">
					<?php if($item['friend'] && $can_pay && $item['available']) { ?>
					<span class="unitCount"> &nbsp;&nbsp; <i class="icon-users"></i> <?php print $lang_shop['buy-for-friend']; ?></span>
					<span style="display: block;">
						<div id="searchBar" class="input-append">
							<form>
								<input style="width: 175px;" id="friendChar" class="search-input span2 ui-autocomplete-input" type="text" placeholder="<?php print $lang_shop['char-name']; ?>" value="" autocomplete="off">
								<button id="friend_buy1" class="btn-default btn-search" type="button"<?php if($hide_buy) print ' style="display: none;"'; ?>><?php print $lang_shop['buy']; ?></button>
								<button id="friend_buy2" class="btn-default fancybox fancybox.ajax btn-buy" type="submit" style="display: none" href="<?php print $shop_url."javascript/buy/".$item['id']; if($item['type']==2 && $new_link!='') print '/'.$new_link; else print '/friend/'; ?>"><?php print $lang_shop['buy-now']; ?></button>
							</form>
						</div>
					</span>
					<?php } else { ?>
					<span class="unitCount"> &nbsp;&nbsp; <i class="icon-info"></i> <?php print $item['count'].' x '.$item_name; ?></span>
					<?php } if($item['pay_type']==1 && $jcoins_back){ ?>
					<br>
					<span class="unitCount"> &nbsp;&nbsp; <i class="fas fa-coins"></i>
						<span class="bill_mileage text-success">
							<?php print $lang_shop['credited-with']; ?>
							<span class="block-price">
								<img class="ttip" src="<?php print $shop_url."images/this/jcoins.png"; ?>" tooltip-content="<?php print $lang_shop['jcoins']; ?>" />
								<span class="end-mileage"><?php print number_format(round($final_price*$jcoins_back/100), 0, '', '.'); ?></span>
							</span>.       
						</span>
					</span>
					<?php } if($account->getAccountData('web_admin', $_SESSION['id'])>=9) { ?>
					<br><span class="unitCount"> &nbsp;&nbsp; <i class="far fa-trash-alt"></i> <span class="bill_mileage text-danger"><a href="<?php print $shop_url.'?delete='.$item['id']; ?>" onclick="return confirm('<?php print $lang_shop['check-delete']; ?>')"><?php print $lang_shop['delete']; ?></a></span></span>
					<span class="unitCount"> &nbsp;&nbsp; <i class="far fa-edit"></i> <span class="bill_mileage text-info"><a href="<?php print $shop_url.'admin/items/edit/'.$item['id']; ?>" target="_blank"><?php print $lang_shop['edit']; ?></a></span></span>
					<?php } ?>
				</label>
				
				<div class="arrow"></div>
			</div>
			<?php if($item['available']==1) { ?>
			<div id="buy">
				<form action="" method="get" name="test" onsubmit="return false;">
                    <p><?php print $lang_shop['now-available']; ?></p>
					<p class="bill_price block-price">
						<?php if($item['pay_type']==1) { ?>
						<img class="ttip" src="<?php print $shop_url."images/this/coins.png"; ?>" tooltip-content="<?php print $lang_shop['coins']; ?>" />
						<?php } else if($item['pay_type']==2){ ?>
						<img class="ttip" src="<?php print $shop_url."images/this/jcoins.png"; ?>" tooltip-content="<?php print $lang_shop['jcoins']; ?>" />
						<?php } ?>	
						<span class="end-price"><?php print number_format($final_price, 0, '', '.'); ?></span>
					</p>
					<div class="buy-btn-box clearfix"  >
                        <div class="btn-group ">
							<button type="button" class="btn-price<?php if(!$can_pay) print ' btn-disabled'; ?>"<?php if($hide_buy) print ' style="display: none;"'; ?> name="changer"><?php print $lang_shop['buy']; ?></button>
							<button class="js_currency fancybox fancybox.ajax btn-buy" href="<?php print $shop_url."javascript/buy/".$item['id']; if($item['type']==2 && $new_link!='') print '/'.$new_link; ?>"><?php print $lang_shop['buy-now']; ?></button>
							<button class="js_currency btn-disabled ttip btn-disabled-template" style="display: none;" href="javascript:void(0);" tooltip-content=""><?php print $lang_shop['buy']; ?></button>
						</div>
					</div>
				</form>
			</div>
			<?php } else { ?>
			<div id="buy">
				<div class="buy-btn-box clearfix">
					<?php if($item['wheel_level']>0 && $final_price==0 && $wheel_status) { ?>
					<button class="btn-default" onclick="location.href='<?php print $shop_url.'wheel/'; ?>'"><?php print $lang_shop['wheel-of-destiny']; ?></button>
					<?php } else { ?>
					<button class="btn-default" onclick="location.href='<?php print $shop_url.'items/'; ?>'"><?php print $lang_shop['all_objects']; ?></button>
					<?php } ?>
				</div>
			</div>
			<?php } ?>
		</div>       
    </div>
</div>

<script type="text/javascript">
	initFocusClear();

	<?php if($item['type']==2) { ?>
	var new_link = '';
	<?php } if($item['friend']) { ?>
	var friend = '';
	<?php } ?>
    // Init tooltip
	$('.ttip').tipTip(zs.data.ttip);
	
    var zs = zs || {};
	zs.buyClick = function(event) {
		if ($(this).hasClass('btn-disabled')) {
            event.preventDefault();
            return;
        }
        $('.buy-btn-box .btn-price, .gifting').hide();
        $('#buy .btn-buy').show('fade');
    };
	zs.buyClickFriend = function(event) {
		if ($(this).hasClass('btn-disabled')) {
            event.preventDefault();
            return;
        }
        $('#friend_buy1').hide();
        $('#friend_buy2').show('fade');
    };
	
    $(document).ready(function () {
        $('#buy .btn-price').on('click', zs.buyClick);
        $('#friend_buy1').on('click', zs.buyClickFriend);
		<?php if($item['friend']) { ?>
		$("#friendChar").on("change paste keyup", function() {
			friend = $(this).val();
			<?php if($item['type']==2) { ?>
			if(new_link!='')
				friend_link = new_link+"/"+friend;
			else
			<?php } ?>
				friend_link = "<?php print $shop_url."javascript/buy/".$item['id']; ?>/friend/"+friend;
			$("#friend_buy2").attr("href", friend_link);
		});
		<?php } ?>
    });
	
	<?php if(!$can_pay) { ?>
        var reason = '<?php print $lang_shop['not-enough-coins']; ?>';
        var disabledBtn = $('.btn-disabled-template');

        if (disabledBtn.attr('tooltip-content') != reason)
            disabledBtn.attr('tooltip-content', reason).tipTip(zs.data.ttip);
        disabledBtn.show();

        $('.buy-btn-box .btn-buy').hide();
        $('.buy-btn-box .btn-price').hide();
	<?php } if($item['type']==2) { ?>
		var used = [];

		function isset(variable) {
			return typeof variable !== typeof undefined;
		}

		function use(select, buy_link) {
			var parent = select.parentNode;
			new_link = '';
			var show_button = true;
				
			for (var i = 0; i < parent.children.length; ++i)
				if (parent.children[i].value != '')
				{
					new_link = new_link + parent.children[i].value + ",";
					used[parent.children[i].value] = 0;
				} else show_button = false;
			
			if(!show_button)
			{
				$("#buy .btn-price").hide();
				$("#buy .btn-buy").hide();
				<?php if($item['friend']) { ?>
				$('#friend_buy1').hide();
				$('#friend_buy2').hide();
				<?php } ?>
			}
			else
			{
				$("#buy .btn-price").show();
				<?php if($item['friend']) { ?>
				$('#friend_buy1').show('fade');
				<?php } ?>
			}
			
			new_link = buy_link + new_link.substring(0, new_link.length - 1);

			$("#buy .btn-buy").attr("href", new_link);
			<?php if($item['friend']) { ?>
			if(friend)
				new_link = new_link+"/"+friend;
			$("#friend_buy2").attr("href", new_link);
			<?php } ?>
			var selects = $('select');
				
			for (var i = 0; i < selects.length; ++i)
				for (var j = 0; j < selects[i].length; ++j)
					if(selects[i][j].selected)
					{
						selects[i][j].hidden = false;
						selects[i][j].disabled = false;
					}
					else if(isset(used[selects[i][j].value]))
					{
						selects[i][j].hidden = true;
						selects[i][j].disabled = true;
					}
					else
					{
						selects[i][j].hidden = false;
						selects[i][j].disabled = false;
					}
			used = [];
		}
	<?php } ?>
</script>