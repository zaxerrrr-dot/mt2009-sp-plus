<?php
	@ob_start();
	require_once("include/functions/header.php");
?>
<!DOCTYPE html>
<html class="no-js" lang="<?php print $language_code; ?>"<?php if($language_code=="ar") print ' dir="rtl"'; ?>>
	<head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
		<meta name="viewport" content="width=device-width">
		<title>Item Shop | <?php print $shop_title; ?></title>
		<link rel="stylesheet" href="<?php print $shop_url; ?>css/bootstrap.css" type="text/css" />
		<link rel="stylesheet" id="gameStyle" href="<?php print $shop_url; ?>css/design.css" type="text/css" />
		<link href="<?php print $shop_url; ?>css/fontawesome/css/all.css" rel="stylesheet">
		<link rel="shortcut icon" href="<?php print $shop_url; ?>images/favicon.ico?v=" />
		<?php if($current_page=='wheel') { ?>
		<link href="<?php print $shop_url; ?>css/wheel.css" rel="stylesheet" type="text/css" />
		<?php } if($language_code=='ar') { ?>
		<style>
			#selectionNameMain {
				float: left;
			}
			.price-label {
				float: right!important;
			}
		</style>
		<?php } ?>
	</head>
	
	<body class="website metin2 ro" data-game="metin2">
		<div id="page" class="row-fluid">
			<div id="page-spin"></div>
			<div id="header" class="header clearfix">
				<div class="<?php if(!$happy_hour_discount && !$wheel_status) print 'span6'; else print 'span5'; ?> logo-block">
					<h1>
						<a class="" href="<?php print $shop_url; ?>">Item Shop | <?php print $shop_title; ?></a>
					</h1>
					<div class="welcome">
						<i class="icon-user"></i><span><a class="text-link" href="<?php print $shop_url; ?>user/deposit"> <?php print $account_name = $account->getAccountData('login', $_SESSION['id']); ?></a></span>
						<i class="icon-earth"></i><span><?php print $languages[$language_code]; ?></span>
					</div>
				</div>
				<div class="<?php if(!$happy_hour_discount && !$wheel_status) print 'span6'; else print 'span7'; ?> payment-block">
					<button class="btn-price <?php if(!$happy_hour_discount) print 'premium'; else print '_premiumBtn'; ?>" href="javascript:void(0)" onClick="openPaymentLink()">
						<?php if($happy_hour_discount) { ?>
						<div id="HHInfo">
							<div class="hh-info-procent">
								<span class="plus">+</span><span class="number"><?php print $happy_hour_discount; ?></span>%
							</div>
							<div class="hh-info-content">
								<div class="hh-info-title">Happy Hour!</div>
								<div class="hh-info-time">
									<span class="timer"></span>
								</div>
							</div>
						</div>
						<?php } ?>
						<img class="ttip" tooltip-content="<?php print $lang_shop['coins']; ?>" src="<?php print $shop_url."images/this/coins.png"; ?>" />
						<?php print $lang_shop['charge-your-account']; ?>
					</button>
					<?php if(!$happy_hour_discount && $wheel_status) { ?>
						<button style="margin-right: 10px; font-size: 13px;" class="btn-default premium" href="javascript:void(0)" onclick="window.location.href = '<?php print $shop_url; ?>wheel/';"><?php print $lang_shop['wheel-of-destiny']; ?></button>
					<?php } ?>
					<ul class="currency_status currency-amount-2">
						<li data-currency="1">
							<span class="ttip" tooltip-content="<?php print $lang_shop['coins']; ?>">
								<span class="block-price">
									<img src="<?php print $shop_url."images/this/coins.png"; ?>" width="16" height="16"  />
									<span id="balances1" class="end-price" data-currency="<?php print $amount_coins; ?>"><?php print number_format($amount_coins, 0, '', '.'); ?></span>
								</span>
							</span>
						</li>
						<li data-currency="2">
							<span class="ttip" tooltip-content="<?php print $lang_shop['jcoins']; ?>">
								<span class="block-price">
									<img src="<?php print $shop_url."images/this/jcoins.png"; ?>"  width="16" height="16" />
									<span id="balances2" class="end-price" data-currency="<?php print $amount_jcoins; ?>"><?php print number_format($amount_jcoins, 0, '', '.'); ?></span>
								</span>
							</span>
						</li>
					</ul>
					<button id="showRightPush" class="account-push" >
						<i class="icon-menu2"></i>
					</button>
				</div>
			</div>
			<div id="contentContainer">
				<nav id="slideMenu" class="clearfix"><h2><i class="icon-user"></i> <?php print $lang_shop['user-panel']; ?></h2>

					<div class="zs-dropdown">
						<button class="dropdown-toggle" type="button" data-toggle="dropdown" style="width: 100%;">
							<span class="dropdown-selection"><?php print '<img src="'.$shop_url.'images/flags/'.$language_code.'.png" style="height: 18px;"/> '.$languages[$language_code]; ?></span>
							<span class="btn-default"><span class="caret"></span></span>
						</button>
						<ul class="dropdown-menu" style="width: 100%;">
						<?php foreach($languages as $key => $lang) if($key!=$language_code) { ?>
							<li>
								<a class="dropdown-option" href="<?php print $shop_url; ?>?lang=<?php print $key; ?>">
									<span><img src="<?php print $shop_url; ?>images/flags/<?php print $key; ?>.png" style="height: 18px;"/> <?php print $lang; ?></span>
								</a>
							</li>
						<?php } ?>
						</ul>
					</div>
				
					<ul class="nav nav-tabs nav-stacked">
						<?php if($account->getAccountData('web_admin', $_SESSION['id'])>=9) { ?>
						<li>
							<a class="btn-sideitem" href="<?php print $shop_url; ?>admin/" target="_blank"> <i class="icon-cogs"></i> <?php print $lang_shop['administration']; ?></a>
						</li>
						<?php } ?>
						<li>
							<a class="btn-sideitem" href="<?php print $shop_url; ?>user/transactions/"> <i class="icon-coins"></i> <?php print $lang_shop['account-transactions']; ?></a>
						</li>
						<li>
							<span class="items-left ttip"> <?php print $count_not_taken_items; ?> </span>
							<a class="btn-sideitem" href="<?php print $shop_url; ?>user/deposit/"><i class="icon-stack"></i> <?php print $lang_shop['my-objects']; ?></a>
						</li>
						<li>
                            <a class="btn-sideitem" href="<?php print $shop_url; ?>user/redeem/"><i class="icon-barcode"></i> <?php print $lang_shop['redeem-code']; ?></a>
                        </li>
						<li>
							<a class="btn-sideitem" href="<?php print $shop_url; ?>logout/"><i class="icon-signup"></i> <?php print $lang_shop['logout']; ?></a>
						</li>
					</ul>
					<?php if($wheel_status) { ?>
					<h2><i class="icon-smile"></i> <?php print $lang_shop['games']; ?></h2>
					<ul class="nav nav-tabs nav-stacked">
						<li>
							<a class="btn-sideitem" href="<?php print $shop_url; ?>wheel">
								<i class="zicon-wheel"></i><span><?php print $lang_shop['wheel-of-destiny']; ?></span>
							</a>
						</li>
					</ul>
					<?php } ?>
				</nav>
				<div id="navigation" class="navbar">
					<div class="container">
						<ul class="nav nav-tabs search">
							<li>
								<a class="btn-navitem icon-home<?php if($current_page=='home') print ' btn-navitem-active'; ?>" href="<?php print $shop_url; ?>"></a>
							</li>
							<li>
								<a href="<?php print $shop_url.'items/'; ?>" title="<?php print $lang_shop['all_objects']; ?>" class="btn-navitem<?php if($current_page=='items' && !$specific_category) print ' btn-navitem-active'; ?>"><?php print $lang_shop['all_objects']; ?></a>
							</li>
							<?php if($wheel_status) { ?>
							<li class="special-category">
								<a href="<?php print $shop_url.'wheel/'; ?>" title="" class="btn-navitem<?php if($current_page=='wheel') print ' btn-navitem-active'; ?>"><?php print $lang_shop['games']; ?></a>
							</li>
							<?php } foreach($categoriesbyid as $key => $category) if($key) { ?>
							<li>
								<a href="<?php print $shop_url.'items/'.$key.'/'; ?>" title="<?php print $category['name']; ?>" class="btn-navitem<?php if($current_page=='items' && $id==$key) print ' btn-navitem-active'; ?>"><?php print $category['name']; ?></a>
							</li>
							<?php } ?>
						</ul>
						
						<div id="searchBar" class="input-append">
							<i class="icon-search"></i>
							<form method="POST" action="<?php print $shop_url; ?>search/">
								<input name="searchString" class="search-input span2 ui-autocomplete-input" type="text" placeholder="<?php print $lang_shop['search-term']; ?>" value="<?php if($searchString) print $searchString; ?>" autocomplete="off">
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
			(function (wd, doc) {
				var w = wd.innerWidth || doc.documentElement.clientWidth;
				var h = wd.innerHeight || doc.documentElement.clientHeight;
				var screenSize = {w: w, h: h};
				if (screenSize.w > 0 && screenSize.w < 801) {
					var cssTag = doc.createElement("link"),
						cssFile = '<?php print $shop_url; ?>css/update.css';
					cssTag.setAttribute("rel", "stylesheet");
					cssTag.setAttribute("type", "text/css");
					cssTag.setAttribute("href", cssFile);
					doc.getElementsByTagName("head")[0].appendChild(cssTag);
				}
			})(window, document);
		</script>
		<script type="text/javascript">
			function openPaymentLink(){
				location.href=("<?php print $shop_url; ?>user/donate");
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
