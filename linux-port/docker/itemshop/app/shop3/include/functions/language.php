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

	// MT2009_PLUS_WEB_I18N_V1: the visitor's language (include/functions/m2i18n.php). The shop and its
	// catalogue stay Polish underneath ($_SESSION['lang'] picks the database's columns); the texts of
	// include/languages/pl.php are put in the visitor's language here - they also reach the page's scripts,
	// which the translation of the finished page leaves alone - and the rest of the page by the output
	// buffer's callback when it is sent.
	require_once __DIR__ . '/m2i18n.php';
	$m2_lang = m2i18n_lang();
	if ($m2_lang != 'pl') {
		foreach ($lang_shop as $m2_key => $m2_text)
			if (is_string($m2_text))
				$lang_shop[$m2_key] = m2i18n_text($m2_text, $m2_lang);
		unset($m2_key, $m2_text);
	}
	ob_start('m2i18n_output');
?>