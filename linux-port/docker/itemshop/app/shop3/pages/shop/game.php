<?php
	// MT2009_PLUS_ITEMSHOP_V3_V4: the top bar's "Koło Losu" (game/wheel/) for a client that cannot open the game's window
	// itself - the exe of round 2 (CWebBrowser.c Mt2009TakeGameUrl) never loads this link, it hands "wheel" to root
	// uiitemshopv3.py, which closes the shop and opens uiwheel.py. Here: where the wheel is and its key.
?>
<div id="category">
	<h2>
		<ul class="breadcrumb">
			<li><a href="<?php print $shop_url; ?>"><?php print $lang_shop['mt-home']; ?></a></li>
			<li>&rsaquo;</li>
			<li><a href="<?php print $shop_url; ?>game/wheel/"><?php print $lang_shop['mt-wheel-title']; ?></a></li>
		</ul>
	</h2>
	<div class="mt-feature-card contrast-box clearfix mt-game-card">
		<img src="<?php print $shop_url; ?>images/wheel/key.png" width="34" height="34" alt="">
		<p><strong><?php print $lang_shop['mt-wheel-title']; ?></strong><br><?php print $lang_shop['mt-wheel-text']; ?><br><span class="mt-note"><?php print $lang_shop['mt-wheel-old-client']; ?></span></p>
		<a class="btn-default" href="<?php print $shop_url; ?>"><?php print $lang_shop['mt-wheel-back']; ?></a>
	</div>
</div>
