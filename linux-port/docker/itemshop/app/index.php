<?php
	// MT2009_PLUS_ITEMSHOP_V3_MAIN_V1: the main ItemShop of the Yohara line is the shop under /shop3/ (the owner,
	// 27 Oct 2026) - the server's address (the launcher's "ItemShop http://...:7791/") opens it.
	// MT2009_PLUS_ITEMSHOP_V3_ONLY_V1: the old web shop (/itemshop/) is closed - its pages redirect here (Dockerfile).
	header("Location: /shop3/");
	exit;
?>
