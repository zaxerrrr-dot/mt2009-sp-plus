<?php
	$error = $no_space = false;
	
	if($shop->getHystoryItem($history_id, $_SESSION['id'], "taken")==1)
	{
		if(!$player->CreateItem($item, $_SESSION['id'], $add_type, []))
		{
			$no_space = true;
			$shop->updateTakenHistory($history_id, 0);
		}
	} else $error = true;
	
if(!$error) {
?>
<div id="confirmation">
    <div id="itemConfirmation" class="contrast-box">
		<div class="row-fluid clearfix">
            <div class="item-showcase grey-box span4">
                <div id="image" class="picture_wrapper">
					<img id="selectionImageMain" class="image" src="<?php if($item['type']!=3) print $shop_url.'images/'.$shop->getIcon($item['vnum']); else print $shop_url.'images/icons/bonuses/'.$server_item['buff'][$item['vnum']][0].'.png'; ?>" width="242" height="242" />
				</div>
			</div>
            <div class="item-confirmation grey-box clearfix span8">
                <h3><?php if(!$no_space) print $lang_shop['distributed-object']; else print $lang_shop['distribute']; ?></h3>
                <div class="scrollable_container reward mCustomScrollbar">
					<p class="confirmed"><?php print $item_name; ?></p>
					<p><?php if(!$no_space) print $lang_shop['find-in-warehouse']; else print $lang_shop['no-space'].' <a href="'.$shop_url.'user/deposit/">'.$lang_shop['my-objects'].'</a>'; ?></p>
				</div>
                <button class="right btn-default" onclick="javascript:$.fancybox.close();"><?php print $lang_shop['continue-shopping'];?></button>
            </div>
        </div>
    </div>
</div>
<script type="text/javascript">
	$(document).ready(function () {
		cardMargin();
		$('.btn-buy.fancybox, .btn-default.fancybox, .item-thumb.fancybox, .card-heading.fancybox, .btn-price.fancybox').click(function () {
			$('.fancybox-overlay').removeClass('reload');
		});
		$('.fancybox-overlay').addClass('reload');
	});
</script>
<?php } else include 'pages/java/error.php'; ?>