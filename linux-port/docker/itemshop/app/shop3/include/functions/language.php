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
	
	// MT2009_PLUS_ITEMSHOP_V3_V1: the server is Polish - one language, whatever the browser asks for
	// (the item names, descriptions and bonus names of itemshop3 are Polish only).
	$languages = array("pl" => "Polski");
	$language_code = 'pl';
	
	$_SESSION['lang'] = $language_code;
	
	include 'include/languages/'.$language_code.'.php';
?>