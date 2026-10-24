<?php
	// MT2009_PLUS_ITEMSHOP_V3_V3: "Wykorzystaj voucher" as the in-game shop has it (itemshop_usevoucher.py) - a code,
	// "Wykorzystaj", the answer below (header.php -> include/functions/voucher.php).
?>
<div id="account" class="mCSB_container row-fluid userdata-payments">
    <ul id="accountNav" class="span3">
		<li><a href="<?php print $shop_url; ?>user/transactions/" class="btn-sideitem"><i class="icon-coins"></i><span><?php print $lang_shop['account-transactions']; ?></span></a></li>
		<li><a href="<?php print $shop_url; ?>user/deposit/" class="btn-sideitem"><i class="icon-stack"><span class="badge"><?php print $count_not_taken_items; ?></span></i><span><?php print $lang_shop['my-objects']; ?></span></a></li>
		<li><a href="<?php print $shop_url; ?>user/redeem/" class="btn-sideitem btn-sideitem-active"><i class="icon-barcode"></i><span><?php print $lang_shop['mt-use-voucher']; ?></span></a></li>
		<li><a href="<?php print $shop_url; ?>user/premium/" class="btn-sideitem"><i class="icon-star"></i><span><?php print $lang_shop['mt-premium']; ?></span></a></li>
	</ul> 
    <div id="accountContent" class="redeem-code span9">
        <h2><?php print $lang_shop['mt-use-voucher']; ?></h2>
		<div class="scrollable_container">
            <div class="box box-account">
                <div class="contrast-box">
					<div class="grey-box">
                        <p class="code-info"><?php print $lang_shop['mt-voucher-info']; ?></p>
                        <img class="code-avatar mCS_img_loaded" src="<?php print $shop_url; ?>images/this/code.png" alt="">
						<form action="<?php print $shop_url; ?>user/redeem/" method="POST">
							<label class="code-label"><?php print $lang_shop['your-code']; ?>:</label>
							<input type="text" name="code" id="code" class="span7" size="30" maxlength="64" autocomplete="off" placeholder="<?php print $lang_shop['mt-voucher-placeholder']; ?>">
							<button class="btn-default span3" type="submit" id="submitCode"><?php print $lang_shop['mt-voucher-use']; ?></button>
						</form>
						<?php if($voucher_answer) { ?>
						<p class="mt-voucher-answer <?php print $voucher_answer['ok'] ? 'text-success' : 'text-error'; ?>"><?php print htmlspecialchars($voucher_answer['text']); ?></p>
						<?php } ?>
                    </div>
                </div>
            </div>
		</div>
	</div>
</div>
