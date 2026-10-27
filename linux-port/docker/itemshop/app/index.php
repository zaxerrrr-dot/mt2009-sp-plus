<?php
	// MT2009_PLUS_ITEMSHOP_V3_MAIN_V1: the main ItemShop of the Yohara line is the shop under /shop3/ (the owner,
	// 27 Oct 2026) - the server's address (the launcher's "ItemShop http://...:7791/") opens it. The old web shop
	// stays reachable at /itemshop/ (its icons are the new shop's pictures, the container's health check reads it).
	header("Location: /shop3/");
	exit;
?>
