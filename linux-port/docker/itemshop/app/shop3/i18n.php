<?php
	// MT2009_PLUS_WEB_I18N_V1: the tables /m2i18n-watch.js translates a page's later texts with (the language's
	// i18n/<code>.json under the English one; the game's names stay on the server - too many for every page).
	require_once __DIR__ . '/include/functions/m2i18n.php';
	$code = isset($_GET['lang']) && is_string($_GET['lang']) ? strtolower($_GET['lang']) : '';
	$langs = m2i18n_languages();
	if (!isset($langs[$code]) || $code == M2I18N_SOURCE) {
		http_response_code(404);
		exit;
	}
	$t = m2i18n_tables($code);
	header('Content-Type: application/json; charset=utf-8');
	header('Cache-Control: public, max-age=86400');
	echo json_encode(array('lang' => $code, 'exact' => (object)$t['exact'], 'patterns' => (object)$t['patterns'],
		'regex' => $t['regex']), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
