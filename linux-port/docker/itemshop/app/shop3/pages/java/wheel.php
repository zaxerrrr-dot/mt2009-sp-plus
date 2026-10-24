<div id="notEnoughCash" class="contrast-box sys-message">
    <div class="dark-grey-box clearfix">
        <div class="clearfix">
            <div class="item-showcase   span2">
                <div id="image" class=" ">
                    <img class="item-thumb" src="<?php print $shop_url; ?>images/wheel/wheel-thumb.png">
                </div>
            </div>
            <div class="money-showcase span5">
                <h2><?php print $lang_shop['not-enough-coins']; ?></h2>
                <div class="currency_status_box">
                    <p><?php print $lang_shop['balance']; ?>:</p>
                    <ul class="currency_status clearfix">
						<li><span><img src="<?php print $shop_url."images/this/coins.png"; ?>" width="16" height="16"/> <?php print number_format($amount_coins, 0, '', '.'); ?></span></li>
						<li><span><img src="<?php print $shop_url."images/this/jcoins.png"; ?>" width="16" height="16"/> <?php print number_format($amount_jcoins, 0, '', '.'); ?></span></li>
					</ul>
				</div>
			</div>
        </div>
    </div>
    <div class="alternativ_payment clearfix">
        <div class="alternativ_payment_head">
            <h3><?php print $lang_shop['what-can-i-do'];?></h3>
            <div class="clearfix">
                <script type="text/javascript">
                    function openPaymentLink()
                    {
						location.href=("<?php print $shop_url; ?>user/donate");
                    }
                </script>  
				<button class="btn-price premium happyhour" href="javascript:void(0)" onClick="openPaymentLink()" title="">
					<img class="ttip" tooltip-content="<?php print $lang_shop['coins']; ?>" src="<?php print $shop_url."images/this/coins.png"; ?>" /> <?php print $lang_shop['charge-your-account']; ?>
				</button>
				<p><?php print $lang_shop['coins-can-be-purchased']; ?></p>
            </div>
        </div>
    </div>
</div>