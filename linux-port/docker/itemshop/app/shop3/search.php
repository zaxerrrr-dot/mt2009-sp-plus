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
	
	if(!isset($_SESSION['id']))
		die();
	
	require_once("include/classes/Medoo.php");
	require_once("include/classes/Shop.php");
	
	use Medoo\Medoo;
	
	$shop_db = new Medoo([
		'database_type' => 'mysql',
		'database_name' => $shop_mysql['database'],
		'server' => $shop_mysql['host'],
		'username' => $shop_mysql['user'],
		'password' => $shop_mysql['password'],
		'port' => $shop_mysql['port'],
		'charset' => 'utf8mb4'	// MT2009_PLUS_ITEMSHOP_V3_V1
	]);
	$shop = new Shop($shop_db);
	// MT2009_PLUS_ITEMSHOP_V3_V4: the wear filter of the pages (include/functions/header.php) for the character of the
	// in-game link - the suggestions are the lines the list shows (a shaman was offered a sword's skin, and the list
	// it led to had none: "brak przedmiotu")
	if(!empty($_SESSION['pid']))
	{
		$sth = $shop_db->pdo->prepare("SELECT job, account_id FROM player.player WHERE id = ?");
		$sth->execute([(int)$_SESSION['pid']]);
		$char = $sth->fetch(PDO::FETCH_ASSOC);
		if($char && (int)$char['account_id'] == (int)$_SESSION['id'])
			$shop->setWearFilter(Shop::wearNames($char['job']));
	}
	
	$searchString = isset($_GET['searchString']) ? $_GET['searchString'] : null;
	$max = isset($_GET['max']) ? $_GET['max'] : null;
	$result = [];
	
	if($searchString && $max && ($max==6 || $max==12) && strlen($searchString)>=3 && strlen($searchString)<=64)
	{
		$searchString = str_replace("±", "+", $searchString);
				
		$result = $shop->getSearchResults($searchString);
		print json_encode($result);
	} else print json_encode($result);
	die();