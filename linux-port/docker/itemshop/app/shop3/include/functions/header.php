<?php
	// MT2009_PLUS_ITEMSHOP_V3_V1: a session of its own - the old shop next door (/itemshop/) keeps
	// the login in $_SESSION['id'] too, as a name where this one keeps the account id, and on the
	// shared PHPSESSID each would have logged the other out.
	session_name('MT2009SHOP3');
	session_set_cookie_params(['path' => '/shop3/', 'httponly' => true]);
	session_start();
	
	header('Cache-control: private');
	include 'config.php';
	include 'include/functions/items.php';
	
	include 'include/functions/language.php';
	
	$current_page = isset($_GET['p']) ? $_GET['p'] : 'home';
	
	require_once("include/classes/Medoo.php");
	require_once("include/classes/Shop.php");
	require_once("include/classes/Player.php");
	require_once("include/classes/Account.php");
	
	use Medoo\Medoo;
	
	try {
		$account_db = new Medoo([
			'database_type' => 'mysql',
			'database_name' => 'account',
			'server' => $game_mysql['host'],
			'username' => $game_mysql['user'],
			'password' => $game_mysql['password'],
			'port' => $game_mysql['port'],
			'charset' => 'utf8mb4'	// MT2009_PLUS_ITEMSHOP_V3_V1
		]);

    	} catch (Exception $e) {
		//echo 'Caught exception: ',  $e->getMessage(), "\n";
		die("The Connection to the database of game.account is not available.");
    }
	try {
		$player_db = new Medoo([
			'database_type' => 'mysql',
			'database_name' => 'player',
			'server' => $game_mysql['host'],
			'username' => $game_mysql['user'],
			'password' => $game_mysql['password'],
			'port' => $game_mysql['port'],
			'charset' => 'utf8mb4'	// MT2009_PLUS_ITEMSHOP_V3_V1
		]);
    	} catch (Exception $e) {
		//echo 'Caught exception: ',  $e->getMessage(), "\n";
		die("The Connection to the database of game.player is not available.");
    }
	try {
    	$shop_db = new Medoo([
    		'database_type' => 'mysql',
    		'database_name' => $shop_mysql['database'],
    		'server' => $shop_mysql['host'],
    		'username' => $shop_mysql['user'],
    		'password' => $shop_mysql['password'],
    		'port' => $shop_mysql['port'],
    		'charset' => 'utf8mb4'	// MT2009_PLUS_ITEMSHOP_V3_V1
    	]);
    	} catch (Exception $e) {
		//echo 'Caught exception: ',  $e->getMessage(), "\n";
		die("The Connection to the database of shop is not available.");
    }
	
	$shop = new Shop($shop_db);
	$account = new Account($account_db);
	$player = new Player($player_db, $shop, $account, $server_item);
	$account->setPlayerDB($player);
	
	$settingsDB = $shop->getSettings();
	$paypal_email = $settingsDB['paypal']['value'];
	$pagination = intval($settingsDB['pagination']['value']);
	// MT2009_PLUS_ITEMSHOP_V3_V1: always player.item_award - the db core hands it over in the
	// game (the "item" mode writes straight into a bag the running core does not read back).
	$add_type = 'item_award';
	$wolfman_character = $settingsDB['wolfman_character']['value'] ? true:false;
	// MT2009_PLUS_ITEMSHOP_V3_V2: the owner's rule (24.10.2026) - a Smocze Monety purchase gives 100 % of the price
	// back as Smocze Znaki (the in-game shop does the same); the package's setting (10) is not read any more.
	$jcoins_back = 100;
	// "Doładuj SM" (the header button, "not enough coins"): the owner's support page, opened by the client in
	// the system's browser (the exe sends links to other hosts there - client-patches/exe CWebBrowser.c).
	$topup_url = 'https://buycoffee.to/mt2009plus';
	
	$happy_hour_discount = $settingsDB['discount']['value'];
	$happy_hour_expire = strtotime($settingsDB['discount']['date'])-$shop->currentTime();
	
	$epayouts_ip = $settingsDB['epayouts_ip']['value'];
	$epayouts_uid = $settingsDB['epayouts_uid']['value'];
	$epayouts_mid = $settingsDB['epayouts_mid']['value'];
	
	$wheel_status = $settingsDB['wheel_status']['value'];
	$wheel_levels = $settingsDB['wheel_levels']['value'];
	$wheel_prices = [$settingsDB['wheel_lv1']['value'], $settingsDB['wheel_lv2']['value'], $settingsDB['wheel_lv3']['value']];
	$wheel_lv2_time = $settingsDB['wheel_lv2_time']['value'];
	$wheel_lv3_time = $settingsDB['wheel_lv3_time']['value'];
	$wheel_web = $settingsDB['wheel_web']['value'];

	if(isset($_GET['pid']) && isset($_GET['sas']))
		$account->AutoLoginShop($_GET['pid'], $_GET['sas']);
	
	// MT2009_PLUS_ITEMSHOP_V3_V1: the package's PayPal IPN and e-payouts callbacks (?p=paypal,
	// ?p=epayouts) are gone - a singleplayer server sells nothing for money, and both credited
	// coins to whatever login the request named.

	if($account->is_loggedin())
	{
		if(!$account->checkStatus($_SESSION['id']))
		{
			$account->doLogout();
			
			header("Location: ".$shop_url);
			die();
		}
		$categories = $shop->getAllCategories();
		// MT2009_PLUS_ITEMSHOP_V3_V4: in the menu's order (the view's sort), each with its parent (0 = a top one)
		usort($categories, function($a, $b) {
			return (isset($a['sort']) ? (int)$a['sort'] : (int)$a['id']) - (isset($b['sort']) ? (int)$b['sort'] : (int)$b['id']);
		});
		$categoriesbyid = array();
		foreach($categories as $category)
		{
			$categoriesbyid[$category['id']]['icon'] = $category['icon'];
			// MT2009_PLUS_ITEMSHOP_V3_V3: what the category is (itemshop3.categories: items, featured, marks, auctions,
			// voucher, premium, topup - the in-game window's buttons)
			$categoriesbyid[$category['id']]['kind'] = isset($category['kind']) ? $category['kind'] : 'items';
			$categoriesbyid[$category['id']]['parent'] = isset($category['parent']) ? (int)$category['parent'] : 0;
			
			if($category[$_SESSION['lang']]!=null && $category[$_SESSION['lang']]!='')
				$categoriesbyid[$category['id']]['name'] = $category[$_SESSION['lang']];
			else if($category['en']!=null && $category['en']!='')
				$categoriesbyid[$category['id']]['name'] = $category['en'];
			else if($category['ro']!=null && $category['ro']!='')
				$categoriesbyid[$category['id']]['name'] = $category['ro'];
			else
			{
				foreach($languages as $key => $lang)
					if(!in_array($key, [$_SESSION['lang'], 'ro', 'en']) && $category[$key]!=null && $category[$key]!='')
						$categoriesbyid[$category['id']]['name'] = $category[$key];
			}
			if(!isset($categoriesbyid[$category['id']]['name']))
				$categoriesbyid[$category['id']]['name'] = 'CAT '.$id;
		}
		$categoriesbyid[0]['name'] = $lang_shop['wheel-of-destiny'];
		
		if($happy_hour_discount && $happy_hour_expire<0)
		{
			$happy_hour_discount = 0;
			$shop->stopHappyHour();
		}

		// MT2009_PLUS_ITEMSHOP_V3_V2: the character of the in-game link (Account::AutoLoginShop) - its name for the
		// purchase box, and the wear filter: a man does not see women's costumes, a class no item of another
		// class only (the item's antiflags; races 0..8: warrior, ninja, sura, shaman, then the other sex, lycan).
		$shop_char = null;
		if(!empty($_SESSION['pid']))
		{
			$shop_char = $player_db->get("player", ["id", "name", "job", "level", "account_id"], ["id" => (int)$_SESSION['pid']]);
			if(!$shop_char || (int)$shop_char['account_id'] != (int)$_SESSION['id'])
				$shop_char = null;
		}
		if($shop_char)
			$shop->setWearFilter(Shop::wearNames($shop_char['job']));	// MT2009_PLUS_ITEMSHOP_V3_V4: shared with search.php

		// MT2009_PLUS_ITEMSHOP_V3_V1: Smocze Monety (cash) and Smocze Znaki (cash_mark - MT2009_PLUS_SZ_UNIFIED_V1).
		$amount_coins = $account->getCoins(1, $_SESSION['id']);
		$amount_jcoins = $account->getCoins(2, $_SESSION['id']);
		// MT2009_PLUS_ITEMSHOP_V3_V3: the premium account (account.premium_expire, the game's subscription) - while it
		// runs the in-game shop sells no VIP effect (CItemShopManager::BuyItem).
		$premium_until = $account->getAccountData('premium_expire', $_SESSION['id']);
		$premium_active = $premium_until && strtotime($premium_until) > $shop->currentTime();
		$count_not_taken_items = $shop->countNotTakenItems($_SESSION['id']);
		$searchString = null;

		$account_bonuses=[];
		foreach($server_item['buff'] as $key => $bonus)
			$account_bonuses[$key]=$bonus[1];
		
		$account_bonuses = $shop->getAccountBonuses($account_bonuses);
		
		// MT2009_PLUS_ITEMSHOP_V3_V1: the admin's ?delete=<id> is gone with the admin panel.
		
		if($current_page=="items")
		{
			if(isset($_POST['searchString']))
			{
				header("Location: ".$shop_url."search/".str_replace("+", "±", $_POST['searchString']));
				die();
			}
			$id = isset($_GET['id']) ? $_GET['id'] : null;
			$searchString = isset($_GET['searchString']) ? $_GET['searchString'] : null;
			
			if($searchString)
				$searchString = str_replace("±", "+", $searchString);
			
			$specific_category = false;
			$count_all = $shop->getItemShopCount(null, false, $searchString);
			
			// MT2009_PLUS_ITEMSHOP_V3_V2: the top bar's "Popularne" (items/popular/). MT2009_PLUS_ITEMSHOP_V3_V3: no
			// "Nowości" any more (the in-game lines have no date) - an old link goes to "Polecane".
			if($id==='new')
			{
				header("Location: ".$shop_url."items/1/");
				die();
			}
			// MT2009_PLUS_ITEMSHOP_V3_V3: the in-game window's buttons that are no list - the voucher tab, the premium
			// account page; the top-up link opens the system's browser (index.php) and lands here only without script.
			if($id && $id==intval($id) && isset($categoriesbyid[(int)$id]))
			{
				$kind = $categoriesbyid[(int)$id]['kind'];
				$target = ['voucher' => 'user/redeem/', 'premium' => 'user/premium/', 'topup' => 'user/premium/'];
				if(isset($target[$kind]))
				{
					header("Location: ".$shop_url.$target[$kind]);
					die();
				}
			}
			$list_mode = ($searchString==null && in_array($id, ['popular'], true)) ? $id : null;
			if($list_mode)
			{
				$all_items = $shop->getPopularItems(60);
				$count_cat = count($all_items);
			}
			else
			{
			if($id && $id==intval($id) && $shop->checkCategoryShop($id) && $searchString==null)
			{
				$specific_category = true;
				$count_cat = $shop->getItemShopCount($id, $specific_category);
			}

			$all_items = $shop->getItemShopItems($id, $specific_category, $searchString);
			}
			
			// MT2009_PLUS_ITEMSHOP_V3_V1: pages of 60 - the package put every offer on one page,
			// and our catalogue (2500 offers, 900 in Fryzury +) made that 5 MB of HTML for the
			// client's embedded browser. items/<category or 0>/<page>/ (.htaccess).
			$items_per_page = 60;
			$items_total = count($all_items);
			$items_pages = ($searchString || $list_mode) ? 1 : max(1, (int)ceil($items_total / $items_per_page));
			$items_page = isset($_GET['n']) ? (int)$_GET['n'] : 1;
			if($items_page < 1 || $items_page > $items_pages)
				$items_page = 1;
			$items_link = $shop_url.'items/'.($specific_category ? intval($id) : 0).'/';
			if($items_pages > 1)
				$all_items = array_slice($all_items, ($items_page - 1) * $items_per_page, $items_per_page);
			
			if(count($all_items))
			{
				$vnums = array_column($all_items, 'vnum');
				$names = $shop->getMultipleNames($vnums);
				$icons = $shop->getMultipleIcon($vnums);
				$descriptions = $shop->getMultipleDesc($vnums);
			}
		} else if($current_page=="javascript")
		{
			$type = isset($_GET['type']) ? $_GET['type'] : null;
			$id = isset($_GET['id']) ? $_GET['id'] : null;
			$bonus_selected = isset($_GET['new']) ? $_GET['new'] : null;
			$friend = isset($_GET['friend']) ? $_GET['friend'] : null;
			// MT2009_PLUS_ITEMSHOP_V3_V2: how many to buy (?q=, the card's or the window's choice; 1 for an item
			// that does not stack - pages/java/buy.php checks it against the offer).
			// MT2009_PLUS_ITEMSHOP_V3_V3: as many as the in-game shop lets buy at once (BuyItem: 1..10); more is refused
			// in pages/java/buy.php, not cut down.
			$buy_qty = isset($_GET['q']) ? (int)$_GET['q'] : 1;
			$account_id = $_SESSION['id'];
			$from_account = $to_player = 0;
			
			if($type=='wheel')
			{
				include 'pages/java/wheel.php';
				die();
			} else if($type=='share')
			{
				$history_id = $id;
				$id = $shop->getHystoryItem($id, $_SESSION['id'], "item");
				if(!$id || !$shop->updateTakenHistory($history_id, 1))
				{
					include 'pages/java/error.php';
					die();
				}
			}
			
			if($shop->checkItemShop($id))
			{
				$item = $shop->getItemShop($id);
				$final_price = $shop->getItemPrice($item['coins'], $item['discount']);
				// MT2009_PLUS_ITEMSHOP_V3_V3: the line's name as the in-game window shows it (with its suffix)
				$item_name = isset($item['name']) && $item['name']!='' ? $item['name'] : $shop->getName($item['vnum']);
				$bonus_selection = [[], []];
				
				if($item['expire']!=null)
				{
					// MT2009_PLUS_ITEMSHOP_V3_V3: a flash offer's end (the view's available says if it sells now);
					// the package deleted an expired offer here - our lines are the in-game shop's, never deleted.
					$time_left = strtotime($item['expire'])-$shop->currentTime();
					if($time_left<0)
						$time_left = $item['available'] = 0;
				}
				if($item['discount']>0)
				{
					$discount_left = strtotime($item['discount_expire'])-$shop->currentTime();
					
					if($discount_left<0)
					{
						$discount_left = 0;
						$shop->updateExpireDate($item['id']);
						$final_price = $shop->getItemPrice($item['coins'], 0);
					}
				}
				if($item['type']==3)
					$item_name = $account_bonuses[$item['vnum']];
				else if($item['type']==2)
					$bonus_selection = $shop->getSelectionBonus($item['bonuses']);
				
				if($item['limit_account'])
				{
					$count_account = $shop->checkLimitAccount($item['id'], $_SESSION['id']);

					if($count_account>=$item['limit_account'])
						$item['available']=0;
				}
				
				$can_pay = true;
				
				$item_proto = $shop->getItem($item['vnum']);
				
				if($item['time']<=0)
					$item['time'] = $player->getItemProtoDuration($item_proto);
				
				$addon = $player->getItemBonusesAddon($item_proto, $item['vnum']);
				
				$bonuses = [];
				for($i=0;$i<=6;$i++)
					if($item['attrtype'.$i]>0 && $item['attrvalue'.$i]>0)
						$bonuses[] = [$item['attrtype'.$i], $item['attrvalue'.$i]];
				/*
				if(!count($bonuses))
					$bonuses = $player->getItemBonuses($item_proto, $item['vnum']);
				*/
				if(count($addon) || count($bonuses) || $item['type']==2)
					$bonuses_name = $shop->getSpecificBonuses(array_merge(array_column($bonuses, 0), array_column($addon, 0), array_keys($bonus_selection[0]), array_keys($bonus_selection[1])));

				$description = $shop->getDesc($item['vnum']);
				
				if($item['book']>0)
				{
					$skill_name = $shop->getSkill($item['book']);
					$item_name.=' - '.$skill_name;
				} else if($item['book_type']!='FIX') {
					if($item['book_type']=='RANDOM_ALL_CHARS')
						$skill_name = $lang_shop['random-skill'];
					else
						$skill_name = $shop->getLocaleGameByType($item['book_type']);
					$item_name.=' - '.$skill_name;
				} else if($item['polymorph']>0)
				{
					$mob_name = $shop->getMob($item['polymorph']);
					$item_name.=' - '.$mob_name;
				}
				
				if(($item['pay_type']==1 && $final_price>$amount_coins) || ($item['pay_type']==2 && $final_price>$amount_jcoins))
					$can_pay = false;
				
				switch ($type) {
					case 'info':
						include 'pages/java/info.php';
						break;
					case 'buy':
						include 'pages/java/buy.php';
						break;
					case 'share':
						include 'pages/java/share.php';
						break;
				}
			} else if($type=='error')
				$shop->getItemError($id, $bonus_selected);
			else include 'pages/java/error.php';
			die();
		} else if($current_page=='deposit') {
			$page_number = isset($_GET['n']) ? $_GET['n'] : 1;
			$history_count = $shop->countAllItems($_SESSION['id']);
			$show_pagination = false;
			
			if(!is_numeric($page_number) || $page_number<1)
				$page_number = 1;
			else if(ceil($history_count/$pagination)<$page_number)
				$page_number = 1;
			if($history_count>$pagination)
				$show_pagination = true;
			
			$history = $shop->getHistoryItem($_SESSION['id'], $page_number);
		} else if($current_page=='transactions') {
			$page_number = isset($_GET['n']) ? $_GET['n'] : 1;
			$history_count = $shop->countAllTransactions($_SESSION['id']);
			$show_pagination = false;
			
			if(!is_numeric($page_number) || $page_number<1)
				$page_number = 1;
			else if(ceil($history_count/$pagination)<$page_number)
				$page_number = 1;
			if($history_count>$pagination)
				$show_pagination = true;
			
			$transactions = $shop->getTransactionsItem($_SESSION['id'], $page_number);
		} else if($current_page=='redeem') {
			// MT2009_PLUS_ITEMSHOP_V3_V3: "Wykorzystaj voucher" of the in-game shop - our promo codes and the cash
			// vouchers, as the game redeems them (include/functions/voucher.php); POST, then back here with the answer.
			if(isset($_POST['code']))
			{
				require_once 'include/functions/voucher.php';
				$_SESSION['voucher_answer'] = mt2009_redeem_voucher((string)$_POST['code']);
				header("Location: ".$shop_url."user/redeem/");
				die();
			}
			$voucher_answer = isset($_SESSION['voucher_answer']) ? $_SESSION['voucher_answer'] : null;
			unset($_SESSION['voucher_answer']);
		}
				else if($current_page=='logout') {
			$account->doLogout();
			
			header("Location: ".$shop_url);
			die();
		}
		else if($current_page=="donate") {
			include 'pages/shop/donate.php';
			die();
		} else if($current_page=="wheel") {
			if(!$wheel_status)
			{
				header("Location: ".$shop_url);
				die();
			}
			$error = false;
			
			for($i=1;$i<=$wheel_levels;$i++)
				if($shop->countWheelItems($i)<16)
					$error = true;
			
			if(!$wheel_web && !$account->is_in_game())
				$error = true;
			
			$action = isset($_GET['action']) ? $_GET['action'] : null;
			
			$current_stats = $shop->getWheelStats($_SESSION['id'], $wheel_levels);
			$current_level = $current_stats[0];
			$current_stage = $current_stats[1];
			$last_spin = strtotime($current_stats[2])-($shop->currentTime());
			
			if($last_spin>0)
				$error = true;
			
			if(!$error)
			{
				$current_time = $current_stats[3];

				$wheel_items = $shop->getWheelItems($wheel_levels);
				$level_time = 0;
				
				if($current_level>1)
				{
					$level_time = strtotime($current_time)-$shop->currentTime();
					if($level_time<0 || $action=='level1')
					{
						$current_level = 1;
						$current_stage = 0;
						$level_time = 0;
						$now = $shop->currentTime();
						$time = date('Y-m-d H:i:s', $now);
						$shop->updateWheelLevel($_SESSION['id'], 1, $time);
						$shop->setWheelStage($_SESSION['id'], 0);
					}
				}

				if(count($wheel_items))
				{
					$names = $shop->getMultipleNames($wheel_items);
					$icons = $shop->getMultipleIcon($wheel_items);
					$descriptions = $shop->getMultipleDesc($wheel_items);
				}
				for($i=1;$i<=$wheel_levels;$i++)
					$itemsLvl[$i] = $shop->getWheelItems($wheel_levels, $i);
				
				$checkWheelPlayer = $shop->checkWheelPlayer($_SESSION['id']);
				
				if($action=="start" && $checkWheelPlayer)
				{
					$security_key = isset($_GET['key']) ? $_GET['key'] : null;
					if(!isset($_SESSION['wheel']) || $security_key==null || $security_key!=$_SESSION['wheel'] || $last_spin>0)
					{
						header("Location: ".$shop_url."wheel");
						die();
					}
					$paid = false;
					
					$now = $shop->currentTime();
					$time = date('Y-m-d H:i:s', $now + 11);
					$shop->updateWheelLastSpin($_SESSION['id'], $time);
					
					$spinCount = rand(32,75);
					if($wheel_prices[$current_level-1]<=$amount_coins)
						$paid = $account->payCoins(1, $wheel_prices[$current_level-1]);
					if(!$paid)
					{
						header("Location: ".$shop_url."wheel");
						die();
					}
				}
			}
			$_SESSION['wheel'] = uniqid();
		}
		
	} else if($current_page=="javascript") {
		include 'pages/java/error.php';
		die();
	}
	else if(basename($_SERVER["SCRIPT_FILENAME"], '.php')!='admin') {
		$error = false;
		if(isset($_POST['username']) && isset($_POST['password']))
			$error = $account->doLogin($_POST['username'], $_POST['password']);
		
		include 'pages/shop/login.php';
		die();
	}