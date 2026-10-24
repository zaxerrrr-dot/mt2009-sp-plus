<?php
	$languages = array(
		"ar" => "العربية",//RTL
		"cs" => "Český",
		"da" => "Dansk",
		"de" => "Deutsch",
		"el" => "Ελληνικά",
		"en" => "English",
		"es" => "Español",
		"fr" => "Français",
		"hu" => "Magyar",
		"it" => "Italiano",
		"nl" => "Nederlands",
		"pl" => "Polski",
		"pt" => "Português",
		"ro" => "Română",
		"ru" => "Русские",
		"tr" => "Türk"
	);
	
	if(isSet($_GET['lang']))
		$language_code = $_GET['lang'];
	else if(isSet($_SESSION['lang']))
		$language_code = $_SESSION['lang'];
	else if(isSet($_COOKIE['lang']))
		$language_code = $_COOKIE['lang'];
	else if(isset($_SERVER['HTTP_ACCEPT_LANGUAGE']))
		$language_code = substr($_SERVER['HTTP_ACCEPT_LANGUAGE'], 0, 2);
	else
		$language_code = 'en';
	
	if(!isset($languages[$language_code]))
		$language_code = 'en';
	
	$_SESSION['lang'] = $language_code;
	setcookie('lang', $language_code, time() + (3600 * 24 * 30));
	
	include 'include/languages/'.$language_code.'.php';
?>