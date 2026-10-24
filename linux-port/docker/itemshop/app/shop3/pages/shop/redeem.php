<div id="account" class="mCSB_container row-fluid userdata-payments">
    <ul id="accountNav" class="span3">
		<li><a href="<?php print $shop_url; ?>user/transactions/" class="btn-sideitem"><i class="icon-coins"></i><span><?php print $lang_shop['account-transactions']; ?></span></a></li>
		<li><a href="<?php print $shop_url; ?>user/deposit/" class="btn-sideitem"><div class="badge"><?php print $count_not_taken_items; ?></div><i class="icon-stack"></i><span><?php print $lang_shop['my-objects']; ?></span></a></li>
		<li><a href="<?php print $shop_url; ?>user/redeem/" class="btn-sideitem btn-sideitem-active"><i class="icon-barcode"></i><span><?php print $lang_shop['redeem-code']; ?></span></a></li>
	</ul> 
    <div id="accountContent" class="redeem-code span9">
        <h2><?php print $lang_shop['redeem-code']; ?></h2>
		<div class="scrollable_container">
            <div class="box box-account">
                <div class="contrast-box">
					<div class="grey-box">
                        <p class="code-info"><?php print $lang_shop['redeem-info']; ?></p>
                        <img class="code-avatar mCS_img_loaded" src="<?php print $shop_url; ?>images/this/code.png">

						<form action="" method="POST">
							<label class="code-label"><?php print $lang_shop['your-code']; ?>:</label>
							<input type="text" name="code" id="code" class="span7" size="30" placeholder="<?php print $lang_shop['your-code']; ?>">
							<button class="btn-default span3" type="submit" id="submitCode"><?php print $lang_shop['redeem']; ?></button>
						</form>
                    </div>
                </div>
            </div>
		</div>
	</div>
</div>
