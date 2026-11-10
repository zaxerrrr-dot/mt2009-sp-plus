<?php
	// MT2009_PLUS_ITEMSHOP_V3_MAIN_V1: the game's signed link ("/ishop?pid=..&c=..&sid=..&sas=..", ACMD(do_in_game_mall))
	// opens the main ItemShop of the Yohara line, /shop3/, which checks the same pid + sas (shop3/include/functions/
	// header.php) - the game's own window (uiitemshopv3.py) asks for /shop3/ itself; this is the way of anything
	// else that follows the link (the old web window, an outside browser). The old web shop (/itemshop/) is closed on
	// the Yohara line (MT2009_PLUS_ITEMSHOP_V3_ONLY_V1) and its auto-login that stood here is gone.
	// MT2009_PLUS_SHOP3_TOKEN_V1: the game's fresh login token (aid, ts, n, tok - shop3 include/functions/game_login.php)
	// goes along; the page is never kept by a browser cache.
	header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0, private');
	$mt2009Query = array();
	foreach (array('pid', 'c', 'sid', 'sas', 'aid', 'ts', 'n', 'tok') as $mt2009Key) {
		if (isset($_GET[$mt2009Key]) && is_string($_GET[$mt2009Key]))
			$mt2009Query[$mt2009Key] = $_GET[$mt2009Key];
	}
	header("Location: /shop3/" . ($mt2009Query ? "?" . http_build_query($mt2009Query) : ""));
	exit;
?>
