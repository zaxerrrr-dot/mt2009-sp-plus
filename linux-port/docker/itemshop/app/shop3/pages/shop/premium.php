<?php
	// MT2009_PLUS_ITEMSHOP_V3_V3: "Konto Premium" of the in-game shop (itemshop_subscriptionwindow.py): what it is, the
	// three main benefits and the others (the window's icons, its texts), and the button to the support page (the
	// system's browser, as "Doładuj SM").
	$premium_benefits = [
		['70005', 'SUBSCRIPTION_BENEFIT_EXP', 'mt-sub-exp'], ['70043', 'SUBSCRIPTION_BENEFIT_DROP', 'mt-sub-drop'],
		['premium', 'SUBSCRIPTION_BENEFIT_CHANNEL', 'mt-sub-channel'], ['70002', '', 'mt-sub-pickup'],
		['71113', '', 'mt-sub-item-view'], ['71068', '', 'mt-sub-love'], ['71008', '', 'mt-sub-fish'],
		['71009', '', 'mt-sub-deposit'], ['71011', '', 'mt-sub-emotion'], ['71095', '', 'mt-sub-passage'],
		['71017', '', 'mt-sub-gold'], ['50200', '', 'mt-sub-shop'],
	];
	$premium_until = $account->getAccountData('premium_expire', $_SESSION['id']);
	$premium_left = $premium_until ? strtotime($premium_until) - $shop->currentTime() : 0;
?>
<div id="account" class="mCSB_container row-fluid userdata-payments">
    <ul id="accountNav" class="span3">
		<li><a href="<?php print $shop_url; ?>user/transactions/" class="btn-sideitem"><i class="icon-coins"></i><span><?php print $lang_shop['account-transactions']; ?></span></a></li>
		<li><a href="<?php print $shop_url; ?>user/deposit/" class="btn-sideitem"><i class="icon-stack"><span class="badge"><?php print $count_not_taken_items; ?></span></i><span><?php print $lang_shop['my-objects']; ?></span></a></li>
		<li><a href="<?php print $shop_url; ?>user/redeem/" class="btn-sideitem"><i class="icon-barcode"></i><span><?php print $lang_shop['mt-use-voucher']; ?></span></a></li>
		<li><a href="<?php print $shop_url; ?>user/premium/" class="btn-sideitem btn-sideitem-active"><i class="icon-star"></i><span><?php print $lang_shop['mt-premium']; ?></span></a></li>
	</ul>
    <div id="accountContent" class="mt-premium span9">
        <h2><?php print $lang_shop['mt-premium']; ?></h2>
		<div class="scrollable_container">
            <div class="box box-account">
                <div class="contrast-box">
					<div class="grey-box mt-premium-box">
						<?php if($premium_left > 0) { ?>
						<p class="text-success"><strong><?php print $lang_shop['mt-premium-active']; ?> <?php print $shop->secondsToTime($premium_left, $lang_shop['days'], $lang_shop['hours'], $lang_shop['minutes']); ?></strong></p>
						<?php } ?>
						<h3><?php print $lang_shop['mt-sub-title1']; ?></h3>
						<p><?php print $lang_shop['mt-sub-desc1']; ?></p>
						<h3><?php print $lang_shop['mt-sub-title2']; ?></h3>
						<p><?php print $lang_shop['mt-sub-desc2']; ?></p>
						<ul class="mt-benefits">
						<?php foreach($premium_benefits as $n => $b) { if($n == 3) { ?>
						</ul>
						<p><?php print sprintf($lang_shop['mt-sub-desc3'], count($premium_benefits) - 3); ?></p>
						<ul class="mt-benefits mt-benefits-more">
						<?php } ?>
							<li><img src="<?php print $shop_url.'images/item/'.$b[0].'.png'; ?>" alt="" onerror="this.onerror=null;this.src='<?php print $shop_url; ?>images/this/noicon.png';"><span><?php print $lang_shop[$b[2]]; ?></span></li>
						<?php } ?>
						</ul>
						<p class="mt-premium-price"><strong><?php print $lang_shop['mt-sub-desc4']; ?></strong></p>
						<button class="btn-price premium" type="button" onclick="openPaymentLink()"><?php print $lang_shop['mt-sub-button']; ?></button>
						<p class="mt-note"><?php print $lang_shop['mt-open-url']; ?></p>
					</div>
                </div>
            </div>
		</div>
	</div>
</div>
