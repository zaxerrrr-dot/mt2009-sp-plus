<!DOCTYPE html>
<html class="no-js">
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
		<meta name="viewport" content="width=device-width">
		<title>Item Shop | <?php print $shop_title; ?></title>
		<link rel="shortcut icon" type="image/x-icon" href="<?php print $shop_url; ?>images/favicon.ico?">
		
		<link rel="stylesheet" href="<?php print $shop_url; ?>css/bootstrap.css" type="text/css" />
		<link rel="stylesheet" id="gameStyle" href="<?php print $shop_url; ?>css/design.css" type="text/css" />
		<script type="text/javascript">
			(function (wd, doc) {
				var w = wd.innerWidth || doc.documentElement.clientWidth;
				var h = wd.innerHeight || doc.documentElement.clientHeight;
				var screenSize = {w: w, h: h};
				if (screenSize.w > 0 && screenSize.w < 801) {
					var cssTag = doc.createElement("link"),
						cssFile = 'css/update.css';
					cssTag.setAttribute("rel", "stylesheet");
					cssTag.setAttribute("type", "text/css");
					cssTag.setAttribute("href", cssFile);
					doc.getElementsByTagName("head")[0].appendChild(cssTag);
				}
			})(window, document);
		</script>
		<meta name="description" content="">
		<meta name="viewport" content="width=device-width">
    </head>
    <body class="ingame metin2 ro">
        <div id="page" class="row-fluid">
            <div id="header" class="header clearfix">
                <div class="span5">
                    <h1>
                        <a class="<?php print $shop_url; ?>"><?php print $shop_title; ?></a>
                    </h1>
                </div>
            </div>
            <div id="contentContainer">
                <div class="content clearfix">
					<div id="error" class="contrast-box">
						<div class="dark-grey-box">
							<h2><i class="icon-user left" style="margin-top: 5px;"></i> <?php print $lang_shop['login']; ?></h2>
							<p><?php print $lang_shop['to-use-shop']; ?></p>

					<?php if($error && $error==1) { ?>
					<div class="alert alert-danger alert-dismissible">
						<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">×</span></button>
						<?php print $lang_shop['incorrect-password']; ?>
					</div>
					<?php } else if($error && $error==2) { ?>
					<div class="alert alert-danger alert-dismissible">
						<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">×</span></button>
						<?php print $lang_shop['blocked_account']; ?>
					</div>
					<?php } ?>
							<form method="POST" action="">
								<label class="col-sm-2 control-label" for="u_id"><?php print $lang_shop['name_login']; ?>: </label>
								<input name="username" id="username" class="input_left" tabindex="1" pattern=".{5,64}" maxlength="64" placeholder="<?php print $lang_shop['name_login']; ?>" required="" type="text" autocomplete="new-password"/>
								<br />
								<label class="col-sm-2 control-label" for="u_pw"><?php print $lang_shop['password']; ?>: </label>
								<input name="password" id="password" tabindex="2" class="input_left" pattern=".{5,16}" maxlength="16" placeholder="<?php print $lang_shop['password']; ?>" required="" type="password" autocomplete="new-password"/>
								<br />
								<input name="login" class="btn-price" type="submit" id="input_left" tabindex="3" value="<?php print $lang_shop['login']; ?>" />
							</form>
							<div class="btn_wrapper"></div>
						</div>
					</div>
                </div>
                <div id="overlayMask"></div>
			</div>
        </div>
	</body>
</html>
