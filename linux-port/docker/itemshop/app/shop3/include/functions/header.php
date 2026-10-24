<?php
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
			'port' => $game_mysql['port']
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
			'port' => $game_mysql['port']
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
    		'password' => $shop_mysql['password']
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
	$add_type = $settingsDB['add_type']['value'];
	$wolfman_character = $settingsDB['wolfman_character']['value'] ? true:false;
	$jcoins_back = $settingsDB['jcoins_back']['value'];
	
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
	
	if($current_page=='paypal')
	{
		if (isset($_POST["txn_id"]) && isset($_POST["txn_type"]) && isset($_POST["item_number"]) && isset($_POST["payment_status"]) && isset($_POST["mc_gross"])&& isset($_POST["mc_currency"])&& isset($_POST["receiver_email"])&& isset($_POST["custom"]) && strtolower($_POST['receiver_email']) == strtolower($paypal_email) && strtolower($_POST["mc_currency"]) == "eur")
		{
			$req = 'cmd=_notify-validate';
			foreach ($_POST as $key => $value) {
				$value = urlencode(stripslashes($value));
				$value = preg_replace('/(.*[^%^0^D])(%0A)(.*)/i','${1}%0D%0A${3}',$value);// IPN fix
				$req .= "&$key=$value";
			}

			$curl_result='';
			$ch = curl_init();
			//curl_setopt($ch, CURLOPT_URL,'https://www.sandbox.paypal.com/cgi-bin/webscr'); - DevMode
			curl_setopt($ch, CURLOPT_URL,'https://www.paypal.com/cgi-bin/webscr');
			curl_setopt($ch, CURLOPT_RETURNTRANSFER,1);
			curl_setopt($ch, CURLOPT_POST, 1);
			curl_setopt($ch, CURLOPT_POSTFIELDS, $req);
			curl_setopt($ch,CURLOPT_USERAGENT,'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13');
			curl_setopt($ch, CURLOPT_HTTPHEADER, array("Content-Type: application/x-www-form-urlencoded", "Content-Length: " . strlen($req)));
			curl_setopt($ch, CURLOPT_HEADER , 1);
			curl_setopt($ch, CURLOPT_VERBOSE, 1);
			curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, true);
			curl_setopt($ch, CURLOPT_TIMEOUT, 30);

			$curl_result = curl_exec($ch);

			curl_close($ch);
			
			if (strpos($curl_result, "VERIFIED")!==false) {
				$coins = $shop->getDonateValues(intval($_POST['mc_gross']), 0);
				
				if($happy_hour_discount && $happy_hour_expire<0)
				{
					$happy_hour_discount = 0;
					$shop->stopHappyHour();
				} else if($happy_hour_discount)
					$coins = $coins + round($coins*$happy_hour_discount/100);
				
				if($coins)
				{
					$account_id = $account->getAccountDataByLogin('id', $_POST['custom']);
					$shop->addTransaction($account_id, 0, intval($_POST['mc_gross']), $coins, $_POST['txn_id'], $_POST['payer_email']);
					$account->addCoinsByLogin(1, $coins, $_POST['custom']);
				}
			}
		}
		die();
	} else if($current_page=='epayouts' && $_SERVER["REMOTE_ADDR"]==$epayouts_ip)
	{
		$type = isset($_GET['type']) ? $_GET['type'] : null;
	
		$all_payments = array_column($payment_names, 0);
		$type = array_search($type, $all_payments);
		
		if($type) {
			$price = isset($_GET['price']) ? $_GET['price'] : null;
			$ucode = isset($_GET['ucode']) ? $_GET['ucode'] : null;
			$currency = isset($_GET['currency']) ? $_GET['currency'] : null;
			$result = isset($_GET['result']) ? $_GET['result'] : null;
			$code = isset($_GET['code']) ? $_GET['code'] : '';
			$email = isset($_GET['email']) ? $_GET['email'] : '';
			
			$coins = $shop->getDonateValues(intval($price), $type);
			if($happy_hour_discount && $happy_hour_expire<0)
			{
				$happy_hour_discount = 0;
				$shop->stopHappyHour();
			} else if($happy_hour_discount)
				$coins = $coins + round($coins*$happy_hour_discount/100);
			
			if($currency && $price && strtolower($currency)=='eur' && strtolower($result)=='ok' && $coins)
			{
				$shop->addTransaction($account->getAccountDataByLogin('id', $ucode), $type, $price, $coins, $code, $email);
				$account->addCoinsByLogin(1, $coins, $ucode);
			}
		}
		die();
	}
	
	if($account->is_loggedin())
	{
		if(!$account->checkStatus($_SESSION['id']))
		{
			$account->doLogout();
			
			header("Location: ".$shop_url);
			die();
		}
		$categories = $shop->getAllCategories();
		$categoriesbyid = array();
		foreach($categories as $category)
		{
			$categoriesbyid[$category['id']]['icon'] = $category['icon'];
			
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

		$amount_coins = $account->getAccountData('coins', $_SESSION['id']);
		$amount_jcoins = $account->getAccountData('jcoins', $_SESSION['id']);
		$count_not_taken_items = $shop->countNotTakenItems($_SESSION['id']);
		$searchString = null;

		$account_bonuses=[];
		foreach($server_item['buff'] as $key => $bonus)
			$account_bonuses[$key]=$bonus[1];
		
		$account_bonuses = $shop->getAccountBonuses($account_bonuses);
		
		if($account->getAccountData('web_admin', $_SESSION['id'])>=9)
		{
			$delete = isset($_GET['delete']) ? $_GET['delete'] : null;
			
			if($delete)
			{
				$shop->deleteItem($delete);
				header("Location: ".$shop_url);
				die();
			}
		}
		
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
			
			if($id && $id==intval($id) && $shop->checkCategoryShop($id) && $searchString==null)
			{
				$specific_category = true;
				$count_cat = $shop->getItemShopCount($id, $specific_category);
			}

			$all_items = $shop->getItemShopItems($id, $specific_category, $searchString);
			
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
				$item_name = $shop->getName($item['vnum']);
				$bonus_selection = [[], []];
				
				if($item['expire']!=null)
				{
					$time_left = strtotime($item['expire'])-$shop->currentTime();
					if($time_left<0)
					{
						$time_left = $item['available'] = 0;
						$shop->deleteItem($item['id']);
					}
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
			if(isset($_POST['code']))
			{
				$redeem_item = $shop->getRedeemCode($_POST['code']);
				if($shop->checkRedeemCode($_POST['code']))
				{
					$shop->deleteRedeemCode($_POST['code']);
					if(!$shop->checkRedeemCode($_POST['code']))
					{
						if($redeem_item['type']==1 || $redeem_item['type']==2)
						{
							$account->addCoinsByID($redeem_item['type'], $redeem_item['item'], $_SESSION['id']);
							
							header("Location: ".$shop_url."user/redeem/");
							die();
						}
						else {
							$shop->addItemHistory($redeem_item['item'], $_SESSION['id'], 0, 1, 0, 3, 0, 0);
							
							header("Location: ".$shop_url."user/deposit/");
							die();
						}
					}
				}
			}
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