<div id="account" class="mCSB_container row-fluid userdata-payments">
    <ul id="accountNav" class="span3">
		<li><a href="<?php print $shop_url; ?>user/transactions/" class="btn-sideitem"><i class="icon-coins"></i><span><?php print $lang_shop['account-transactions']; ?></span></a></li>
		<li><a href="<?php print $shop_url; ?>user/deposit/" class="btn-sideitem btn-sideitem-active"><div class="badge"><?php print $count_not_taken_items; ?></div><i class="icon-stack"></i><span><?php print $lang_shop['my-objects']; ?></span></a></li>
		<li><a href="<?php print $shop_url; ?>user/redeem/" class="btn-sideitem "><i class="icon-barcode"></i><span><?php print $lang_shop['redeem-code']; ?></span></a></li>
	</ul> 
    <div id="accountContent" class="depot span9">
        <h2><?php print $lang_shop['my-objects']; ?></h2>
		<div class="scrollable_container">
            <div class="box box-account">
                <div class="contrast-box">
                    <div class="inner_box">
						<table>
							<colgroup>
								<col width="20%"/>
								<col width="45%"/>
								<col width="15%"/>
								<col width="20%"/>
							</colgroup>

							<tbody>
					<?php
						foreach($history as $item) {
							$i = $shop->getItemShop($item['item']);
							$item_name = $shop->getName($i['vnum']);
							if($i['type']==3)
								$item_name = $account_bonuses[$i['vnum']];
							
							if($i['book']>0)
							{
								$skill_name = $shop->getSkill($i['book']);
								$item_name.=' - '.$skill_name;
							} else if($i['book_type']!='FIX') {
								if($i['book_type']=='RANDOM_ALL_CHARS')
									$skill_name = $lang_shop['random-skill'];
								else
									$skill_name = $shop->getLocaleGameByType($i['book_type']);
								$item_name.=' - '.$skill_name;
							} else if($i['polymorph']>0)
							{
								$mob_name = $shop->getMob($i['polymorph']);
								$item_name.=' - '.$mob_name;
							}
							if($item['from_account'])
								$item_name.= ' ['.$lang_shop['gift'].']';
							else if($item['to_player'])
								$item_name.= ' ['.$lang_shop['sent-to'].' '.$player->getPlayerData('name', $item['to_player']).']';
					?>
								<tr>
									<td><?php print date("d-m-Y H:i", strtotime($item['date'])); ?></td>
									<td><a class="fancybox fancybox.ajax card-heading" href="<?php print $shop_url."javascript/info/".$item['item']; ?>" title="<?php print $item_name; ?>"><?php print $item_name; ?></a></td>
									<td>
									<?php if($item['pay_type']==1) { ?>
									<img class="ttip" src="<?php print $shop_url."images/this/coins.png"; ?>" tooltip-content="<?php print $lang_shop['coins']; ?>" />
									<?php } else if($item['pay_type']==2){ ?>
									<img class="ttip" src="<?php print $shop_url."images/this/jcoins.png"; ?>" tooltip-content="<?php print $lang_shop['jcoins']; ?>" />
									<?php } ?>	
									<span class="end-price"><?php print number_format($item['coins'], 0, '', '.'); ?></span>
									</td>
									<td>
									<?php if($item['taken']==1) print $lang_shop['distributed-object']; else { ?>
										<button href="<?php print $shop_url."javascript/share/".$item['id']; ?>" class=" btn-default fancybox fancybox.ajax assign"><?php print $lang_shop['distribute'];?></button>
									<?php } ?>
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
								print $shop->createLinksPagination($shop_url.'user/deposit/', $page_number, $history_count);
								print '</div>';
							}
						?>
                </div>
            </div>
		</div>
	</div>
</div>
