<?php
	// MT2009_PLUS_SHOP3_TOKEN_V1: a link from the game that did not sign in (expired, used already, another account's
	// character, a core without the token) - include/functions/game_login.php has logged the browser's old session out.
	// No account on this page, no login form: the shop is opened again from the game, which brings a fresh token.
	$mt_reopen_title = isset($lang_shop['mt-reopen-title']) ? $lang_shop['mt-reopen-title'] : 'Otwórz sklep ponownie z gry';
	$mt_reopen_text = isset($lang_shop['mt-reopen-text']) ? $lang_shop['mt-reopen-text'] : '';
?>
<!DOCTYPE html>
<html class="no-js">
	<head>
		<meta charset="utf-8">
		<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
		<meta name="viewport" content="width=device-width">
		<title><?php print htmlspecialchars($mt_reopen_title); ?> | <?php print htmlspecialchars($shop_title); ?></title>
		<link rel="stylesheet" href="<?php print $shop_url; ?>css/shop-base.css" type="text/css" />
		<link rel="stylesheet" id="gameStyle" href="<?php print $shop_url; ?>css/shop-theme.css" type="text/css" />
	</head>
	<body class="ingame metin2 pl">
		<div id="page" class="row-fluid">
			<div id="header" class="header clearfix">
				<div class="span5">
					<h1><a><?php print htmlspecialchars($shop_title); ?></a></h1>
				</div>
			</div>
			<div id="contentContainer">
				<div class="content clearfix">
					<div id="error" class="contrast-box">
						<div class="dark-grey-box">
							<h2><i class="icon-user left" style="margin-top: 5px;"></i> <?php print htmlspecialchars($mt_reopen_title); ?></h2>
							<p><?php print htmlspecialchars($mt_reopen_text); ?></p>
						</div>
					</div>
				</div>
			</div>
		</div>
	</body>
</html>
