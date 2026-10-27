<?php
	// MT2009_PLUS_ITEMSHOP_V3_V1: the second ItemShop (the "V3 Itemshop Premium" web package by Metin2CMS,
	// metin2cms.cf, 2019 - its DB layer is Medoo 1.7.3, MIT), opened
	// in the client's built-in browser with Shift+F12). Everything comes from the container's
	// environment (docker-compose.yml, the same M2_DB_* the old shop next door uses), never from this
	// file: the package shipped a root login, a PayPal address and a licence key here.
	//
	// The links are relative to the host the client opened, so the shop works on any address the
	// game's mall_url names (127.0.0.1:7791 at home, the VPS address on a server).
	$shop_url = "/shop3/";

	// MT2009_PLUS_ITEMSHOP_V3_TZ_V1: PHP's clock in the container's zone (TZ = M2_TZ, docker-compose.yml) - the
	// same as the database's. PHP ran on UTC while account.availDt (the account's creation time) is the
	// database's local time, so a new account - the admin of a fresh install too - read as blocked
	// ("To konto zostalo zablokowane") for the first one or two hours (Account::check_availDt).
	$mt2009_tz = getenv('TZ');
	if (!$mt2009_tz || !@date_default_timezone_set($mt2009_tz))
		date_default_timezone_set('UTC');

	$shop_title = "MT2009 PLUS";
	// The game core signs the in-game link with md5(pid . account_id . key); r40250 uses "GF9001"
	// (ACMD(do_in_game_mall)), the old shop's /ishop reads the same variable.
	$game_ishop_key = getenv('M2_MALL_SAS_KEY') ?: 'GF9001';

	// Game databases (account, player) - the server's own.
	$game_mysql = [		'host'		=> getenv('M2_DB_HOST') ?: 'mariadb',
						'user' 		=> getenv('M2_DB_USER') ?: 'metin2',
						'password'	=> getenv('M2_DB_PASSWORD') ?: '',
						'port'      => 3306
	];
	// The shop's own tables and the views onto our catalogue (mariadb/playerbot/itemshop3_schema.sql).
	$shop_mysql = [		'host'		=> getenv('M2_DB_HOST') ?: 'mariadb',
						'database' 	=> 'itemshop3',
						'user' 		=> getenv('M2_DB_USER') ?: 'metin2',
						'password'	=> getenv('M2_DB_PASSWORD') ?: '',
						'port'      => 3306
	];
