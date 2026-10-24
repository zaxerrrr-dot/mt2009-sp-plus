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
				<?php
					// MT2009_PLUS_ITEMSHOP_V3_V2: "Popularne" as the big servers' shop has it under the banners - the
					// most bought offers (Shop::getPopularItems), the cards of include/functions/tile.php.
					$home_items = $shop->getPopularItems(11);
					if(count($home_items))
					{
						$vnums = array_column($home_items, 'vnum');
						$names = $shop->getMultipleNames($vnums);
						$icons = $shop->getMultipleIcon($vnums);
						$descriptions = $shop->getMultipleDesc($vnums);
					}
				?>
				<h2 class="heading-cat"><a class="text-link" href="<?php print $shop_url.'items/popular/'; ?>"><?php print $lang_shop['mt-popular-all']; ?></a><?php print $lang_shop['mt-popular']; ?></h2>
				<div class="carousell rsNoDrag royalSlider contentslider rsDefault visibleNearby card">
					<?php foreach($home_items as $n => $item) print mt2009_render_tile($item, $n, '', 'div'); ?>
				</div>
            </div>
        </div>
    </div>
</div>
