<?php
	// MT2009_PLUS_ITEMSHOP_V3_V1: the package's payment page (PayPal / e-payouts through its own
	// pmfeserver.php) is not shipped - nothing on this server is bought for money. The header's
	// "charge your account" button lands here.
?>
<!DOCTYPE html>
<html lang="pl">
	<head>
		<meta charset="utf-8">
		<meta http-equiv="X-UA-Compatible" content="IE=edge">
		<title>Item Shop | <?php print $shop_title; ?></title>
		<link rel="stylesheet" href="<?php print $shop_url; ?>css/bootstrap.css" type="text/css" />
		<link rel="stylesheet" id="gameStyle" href="<?php print $shop_url; ?>css/design.css" type="text/css" />
	</head>
	<body class="website metin2 ro">
		<div id="page" class="row-fluid">
			<div class="content clearfix" style="padding: 40px; text-align: center;">
				<h2><?php print $lang_shop['coins']; ?></h2>
				<p>Smocze Monety (SM) zdobywasz grając na serwerze (zadania, wydarzenia, kupony).<br />
				Smocze Znaki (SZ) dostajesz z powrotem przy każdym zakupie za Smocze Monety.</p>
				<p><a class="btn-default premium" href="<?php print $shop_url; ?>">Wróć do sklepu</a></p>
			</div>
		</div>
	</body>
</html>
