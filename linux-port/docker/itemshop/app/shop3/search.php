<?php
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
		'password' => $shop_mysql['password']
	]);
	$shop = new Shop($shop_db);
	
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