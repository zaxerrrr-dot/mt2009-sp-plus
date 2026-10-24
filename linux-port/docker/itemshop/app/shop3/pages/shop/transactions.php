<div id="account" class="mCSB_container row-fluid userdata-payments">
    <ul id="accountNav" class="span3">
		<li><a href="<?php print $shop_url; ?>user/transactions/" class="btn-sideitem btn-sideitem-active"><i class="icon-coins"></i><span><?php print $lang_shop['account-transactions']; ?></span></a></li>
		<li><a href="<?php print $shop_url; ?>user/deposit/" class="btn-sideitem"><div class="badge"><?php print $count_not_taken_items; ?></div><i class="icon-stack"></i><span><?php print $lang_shop['my-objects']; ?></span></a></li>
		<li><a href="<?php print $shop_url; ?>user/redeem/" class="btn-sideitem "><i class="icon-barcode"></i><span><?php print $lang_shop['redeem-code']; ?></span></a></li>
	</ul> 
    <div id="accountContent" class="depot span9">
        <h2><?php print $lang_shop['account-transactions']; ?></h2>
		<div class="scrollable_container">
<div class="box box-account">
                <h3><?php print $lang_shop['balance']; ?>:</h3>
                <div class="contrast-box">
                    <div class="inner_box">
                        <div class="row-fluid">
							<div class="left">
                                <span title="" class="balance block-price">
                                    <small class="currency-txt"><?php print $lang_shop['coins']; ?></small>
                                    <img class="ttip mCS_img_loaded" src="<?php print $shop_url."images/this/coins.png"; ?>">
                                     <span class="end-price" data-currency="<?php print $amount_coins; ?>"><?php print number_format($amount_coins, 0, '', '.'); ?></span>
                                </span>
                                                                                                                                                                                        <span title="" class="block-price">
                                        <small class="currency-txt"><?php print $lang_shop['jcoins']; ?></small>
                                        <img class="ttip mCS_img_loaded" src="<?php print $shop_url."images/this/jcoins.png"; ?>" width="16" height="16" alt="Jetoane Dragon">
                                        <span class="end-price" data-currency="<?php print $amount_jcoins; ?>"><?php print number_format($amount_jcoins, 0, '', '.'); ?></span>
                                    </span>
							</div>
                            <div class="right">
                                <div class="account_payment_button">
                                    <p><?php print $lang_shop['what-can-i-do']; ?></p>
									<button class="btn-price _premiumBtn premium" href="javascript:void(0)" onclick="openPaymentLink()" title="">
										<img class="ttip mCS_img_loaded" src="<?php print $shop_url."images/this/coins.png"; ?>" alt="">
										<span class="premium-name"><?php print $lang_shop['charge-your-account']; ?></span>
									</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
			<br><br>
		
            <div class="box box-account">
                <div class="contrast-box">
                    <div class="inner_box">
						<table>
							<colgroup>
								<col width="20%"/>
								<col width="30%"/>
								<col width="25%"/>
								<col width="25%"/>
							</colgroup>

							<tbody>
					<?php
						foreach($transactions as $item) {
					?>
								<tr>
									<td><?php print date("d-m-Y H:i", strtotime($item['date'])); ?></td>
									<td><?php print $payment_names[$item['type']][1]; ?></td>
									<td><?php print number_format($item['amount'], 0, '', '.'); ?> &euro;</td>
									<td>
									<img class="ttip" src="<?php print $shop_url."images/this/coins.png"; ?>" tooltip-content="<?php print $lang_shop['coins']; ?>" />
									<span class="end-price"><?php print number_format($item['value'], 0, '', '.'); ?></span>
									</td>
								</tr>
					<?php
						}
					?>
							</tbody>
						</table>
						
						<?php
							if($show_pagination)
							{
								print '<div class="pagination">';
								print $shop->createLinksPagination($shop_url.'user/transactions/', $page_number, $history_count);
								print '</div>';
							}
						?>
                </div>
            </div>
		</div>
	</div>
</div>
