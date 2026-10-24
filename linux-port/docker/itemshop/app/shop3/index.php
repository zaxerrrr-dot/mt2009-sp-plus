<?php
	@ob_start();
	require_once("include/functions/header.php");
	require_once("include/functions/tile.php");
	// MT2009_PLUS_ITEMSHOP_V3_V2: the page as the big servers' shop of the owner's saved page (23.10.2026) - its
	// stylesheets (css/shop-base.css, css/shop-theme.css, their pictures in images/gf, nothing loaded from
	// outside), its header, top bar and markup; our texts, our logo, our currencies.
	$char_name = $shop_char ? $shop_char['name'] : $account->getAccountData('login', $_SESSION['id']);
?>
<!DOCTYPE html>
<html class="no-js" lang="pl">
	<head>
		<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
		<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
		<meta name="viewport" content="width=device-width">
		<title><?php print $lang_shop['site_title'].' | '.$shop_title; ?></title>
		<link rel="stylesheet" href="<?php print $shop_url; ?>css/shop-base.css" type="text/css">
		<link rel="stylesheet" id="gameStyle" href="<?php print $shop_url; ?>css/shop-theme.css" type="text/css">
		<link rel="stylesheet" href="<?php print $shop_url; ?>css/fontawesome/css/all.css" type="text/css">
		<link rel="stylesheet" href="<?php print $shop_url; ?>css/mt2009.css" type="text/css">
		<link rel="shortcut icon" href="<?php print $shop_url; ?>images/favicon.ico">
		<?php if($current_page=='wheel') { ?>
		<link href="<?php print $shop_url; ?>css/wheel.css" rel="stylesheet" type="text/css">
		<?php } ?>
	</head>
	<body class="website metin2 pl no-dailies" data-game="metin2">
		<div id="page" class="row-fluid">
			<div id="page-spin"></div>
			<div id="header" class="header clearfix">
				<div class="span5 logo-block">
					<h1>
						<a href="<?php print $shop_url; ?>"><?php print $shop_title; ?></a>
					</h1>
					<div class="welcome">
						<i class="icon-user"></i><span><a class="text-link" href="<?php print $shop_url; ?>user/deposit/"> <?php print htmlspecialchars($char_name); ?></a></span><i class="icon-earth"></i><span><?php print $shop_title; ?></span>
					</div>
				</div>
				<div class="span7 payment-block">
					<button class="btn-price _premiumBtn premium" href="javascript:void(0)" onclick="openPaymentLink()" title="">
						<img class="ttip" src="<?php print $shop_url; ?>images/this/coins.png" alt="">
						<span class="premium-name"><?php print $lang_shop['mt-topup']; ?></span>
					</button>
					<ul class="currency_status currency-amount-3">
						<li data-currency="1">
							<span class="ttip" tooltip-content="<?php print $lang_shop['coins']; ?>">
								<span class="block-price">
									<img src="<?php print $shop_url; ?>images/this/coins.png" width="16" height="16" alt="<?php print $lang_shop['coins']; ?>">
									<span id="balances1" class="end-price" data-currency="<?php print $amount_coins; ?>"><?php print number_format($amount_coins, 0, '', '.'); ?></span>
								</span>
							</span>
						</li>
						<li data-currency="2">
							<span class="ttip" tooltip-content="<?php print $lang_shop['jcoins']; ?>">
								<span class="block-price">
									<img src="<?php print $shop_url; ?>images/this/jcoins.png" width="16" height="16" alt="<?php print $lang_shop['jcoins']; ?>">
									<span id="balances2" class="end-price" data-currency="<?php print $amount_jcoins; ?>"><?php print number_format($amount_jcoins, 0, '', '.'); ?></span>
								</span>
							</span>
						</li>
					</ul>
					<button id="showRightPush" class="account-push"><i class="icon-menu2"></i></button>
				</div>
			</div><!-- header -->
			<div id="contentContainer">
				<nav id="slideMenu" class="clearfix">
					<h2><i class="icon-user"></i> <?php print $lang_shop['user-panel']; ?></h2>
					<div class="account-infos">
						<img class="avatar" height="45" width="45" src="<?php print $shop_url; ?>images/gf/avatar.png" alt="">
						<span class="buy-for"><?php print $lang_shop['mt-buying-for']; ?></span>
						<p class="selected-player"><?php print $lang_shop['name']; ?>: <?php print htmlspecialchars($char_name); ?><br><?php print $lang_shop['mt-server']; ?>: <?php print $shop_title; ?></p>
					</div>
					<ul class="nav nav-tabs nav-stacked">
						<li>
							<a class="btn-sideitem" href="<?php print $shop_url; ?>user/transactions/"><i class="icon-coins"></i> <?php print $lang_shop['account-transactions']; ?></a>
						</li>
						<li>
							<span class="items-left ttip"> <?php print $count_not_taken_items; ?> </span>
							<a class="btn-sideitem" href="<?php print $shop_url; ?>user/deposit/"><i class="icon-stack"></i> <?php print $lang_shop['my-objects']; ?></a>
						</li>
						<li>
							<a class="btn-sideitem" href="<?php print $shop_url; ?>user/redeem/"><i class="icon-barcode"></i> <?php print $lang_shop['mt-use-voucher']; ?></a>
						</li>
						<li>
							<a class="btn-sideitem" href="<?php print $shop_url; ?>user/premium/"><i class="icon-star"></i> <?php print $lang_shop['mt-premium']; ?></a>
						</li>
						<li>
							<a class="btn-sideitem" href="<?php print $shop_url; ?>logout/"><i class="icon-signup"></i> <?php print $lang_shop['logout']; ?></a>
						</li>
					</ul>
				</nav>
				<div id="navigation" class="navbar">
					<div class="container">
						<ul class="nav nav-tabs search">
							<li<?php if($current_page=='home') print ' class="active"'; ?>>
								<a class="btn-navitem icon-home<?php if($current_page=='home') print ' btn-navitem-active'; ?>" href="<?php print $shop_url; ?>"></a>
							</li>
							<?php
								// MT2009_PLUS_ITEMSHOP_V3_V3: "Polecane" (the in-game window's first button) in the place of "Nowości"
								// (the in-game lines have no date), "Za Smocze Znaki" = its "Smocze Znaki" (category 12).
								$nav_mode = ($current_page=='items') ? ($list_mode ? $list_mode : ($specific_category && $id==12 ? 'mileage' : ($specific_category && $id==1 ? 'featured' : ($searchString ? 'search' : 'all')))) : '';
								$nav = [
									['all', $shop_url.'items/', $lang_shop['all_objects'], ''],
									['featured', $shop_url.'items/1/', $lang_shop['mt-featured'], ''],
									['popular', $shop_url.'items/popular/', $lang_shop['mt-popular'], ''],
									['mileage', $shop_url.'items/12/', $lang_shop['mt-for-marks'], 'special-category'],
								];
								foreach($nav as $n) {
							?>
							<li<?php if($n[3]) print ' class="'.$n[3].'"'; ?>>
								<a href="<?php print $n[1]; ?>" title="" class="btn-navitem<?php if($nav_mode==$n[0]) print ' btn-navitem-active'; ?>"><?php print $n[2]; ?></a>
							</li>
							<?php } ?>
						</ul>
						<div id="searchBar" class="input-append">
							<i class="icon-search"></i>
							<form method="POST" action="<?php print $shop_url; ?>search/">
								<input name="searchString" class="search-input span2 ui-autocomplete-input" type="text" placeholder="<?php print $lang_shop['search-term']; ?>" value="<?php if($searchString) print htmlspecialchars($searchString); ?>" autocomplete="off">
								<button class="btn-default btn-search" type="submit"><?php print $lang_shop['search']; ?></button>
							</form>
						</div>
						<div class="nav-collapse collapse"></div>
					</div>
				</div>

				<div class="content clearfix">
					<?php
						switch ($current_page) {
							case 'home':
								include 'pages/shop/home.php';
								break;
							case 'items':
								include 'pages/shop/items.php';
								break;
							case 'transactions':
								include 'pages/shop/transactions.php';
								break;
							case 'deposit':
								include 'pages/shop/deposit.php';
								break;
							case 'redeem':
								include 'pages/shop/redeem.php';
								break;
							case 'premium':	// MT2009_PLUS_ITEMSHOP_V3_V3: "Konto Premium" of the in-game shop
								include 'pages/shop/premium.php';
								break;
							case 'wheel':
								include 'pages/shop/wheel.php';
								break;
							default:
								include 'pages/shop/home.php';
						}
					?>
				</div>
			</div>
		</div>

		<script type="text/javascript">
			var shop_url = "<?php print $shop_url; ?>";
			// MT2009_PLUS_ITEMSHOP_V3_V2: no css/update.css any more (the package's small-screen sheet was made for its
			// older stylesheet); the body class "small" below is enough for the big servers' one.
		</script>
		<script type="text/javascript">
			// MT2009_PLUS_ITEMSHOP_V3_V2: "Doładuj SM" - the owner's support page in the system's browser (the game's
			// browser hands other hosts and new windows over to it; a normal browser opens a new tab).
			function openPaymentLink(){
				window.open("<?php print $topup_url; ?>", "_blank");
			}
		</script> 
		<script type="text/javascript">
			var zs = zs || {};
			zs.data = zs.data || {};
			zs.data.timeBefore = (new Date()).getTime();
			zs.data.game = 'metin2';
			zs.data.dir = 'ltr';
			zs.data.loca = {};
			zs.module = zs.module || {};
			zs.module.small = zs.module.small || false;
			zs.fn = {};
			zs.data.detailRedirect = '';

		</script>
		<script type="text/javascript" src="<?php print $shop_url; ?>js/javascript.js"></script>
		<script type="text/javascript" src="<?php print $shop_url; ?>js/javascript_.js"></script>
		<script type="text/javascript" src="<?php print $shop_url; ?>js/mt2009.js"></script>
		<script type="text/javascript">
			(function (wd, doc) {
				var w, h;
				w = wd.innerWidth || doc.documentElement.clientWidth; 
				h = wd.innerHeight || doc.documentElement.clientHeight;
				var screenSize = {w: w, h: h};
				if (screenSize.w > 0 && screenSize.w < 801) {
					$(document).ready(function() {
						$('body').addClass('small');
						$('.currency_status')
							.find('.block-price img').after('<br>').end()
							.show();
					});
					zs.module.small =  true;
				}
			})(window, document);
		</script>
		<?php if($happy_hour_discount) { ?>
		<script>
		$(document).ready(function() {
			if ($('.hh-info-time span.timer').length) {
				$('.hh-info-time span.timer').countdown({
					until: +<?php print $happy_hour_expire; ?>,
					format: 'dHMS',
					padZeroes: true,
					layout: '{d<}<span class="number">{dn}</span>d{d>} {h<}<span class="number">{hn}</span>h{h>} <span class="number">{mnn}</span>m <span class="number">{snn}</span>s '
				});
			}
			if ($('#happy-hour').length) {
				$('#happy-hour .hh-timer').countdown({
					until: +<?php print $happy_hour_expire; ?>,
					format: 'dHMS',
					compact: true
				});
			}
		});
		</script>
		<?php } if($current_page=='wheel' && !$error) { ?>
		<script type="text/javascript" src="<?php print $shop_url; ?>js/wheel.js"></script>
		<script type="text/javascript"> 
			var action = false;
			var dir = zs.data.dir || {};
			var wl = {
				url       : '<?php print $shop_url; ?>wheel/',
				totalStg  : 11,
				restStg   : 11,
				prevLvl   : 1,
				time      : 0,
				lvl       : 1,
				dir       :  (dir == 'rtl') ?  'left' : 'right',
				usePrespin: false
			}
			<?php if($action!="start") { ?>
			wl.doTeaser = true;
			<?php } else{ ?>			
			wl.spinCount      = <?php print $spinCount; ?>;
			wl.slowDownCount  = 9;
			wl.clockwise      = 1;
			wl.startingDelay  = 100;
			wl.gotKey         = 0;
			wl.gotLastKey     = 0;
			wl.rewardPosition = 0;
			wl.currentStage   = 2;
			wl.stagesLvl      = 6;
			<?php } ?>
		$(document).ready(function() {
			setStages();
			<?php if($action!="start") {
				if($wheel_prices[$current_level-1] <= $amount_coins) { ?>
				$('#spinButton').click(function(event) {
					{
						start(event, $(this));
					}
				});
				<?php } ?>
				$('#wheel-stages .ttip').tipTip({
					delay: zs.data.ttip.delay,
					fadeIn: zs.data.ttip.fadeIn,
					defaultPosition: wl.dir,
					attribute : zs.data.ttip.attribute,
					maxWidth: zs.data.ttip.maxWidth
				});
				setTimeout( function(){
					teaser(1, 1);
				}, 1000);
			<?php } else{ ?>
				animation();
				action = true;
			<?php } if($current_level>1) { ?>
				$('#wheel-timer').countdown({
					until: +<?php print $level_time; ?>,
					format: 'HMS',
					compact: true,
					expiryText: '<?php print $lang_shop['time-up']; ?>'
				});
				$('.wheel-over').click(function(){
					location.href = $(this).attr('href');
				});
				window.setTimeout(function() {
					window.location.href = '<?php print $shop_url; ?>wheel/';
				}, <?php print $level_time*1000; ?>);
			<?php } ?>
			});
			
			window.addEventListener('keydown', function (event) {
				if (event.keyCode) {
					event.preventDefault();
					return false;
				}
			});
		</script>
		<?php } ?>
	</body>
</html>
