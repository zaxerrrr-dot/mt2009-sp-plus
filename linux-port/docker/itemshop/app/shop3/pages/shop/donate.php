<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html xmlns:exsl="http://exslt.org/common">
<head>
<title>Payment <?php print $shop_title; ?></title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<link type="text/css" rel="stylesheet" href="<?php print $shop_url; ?>css/donate.css">
<link rel="shortcut icon" href="<?php print $shop_url; ?>images/favicon.ico?v=">
<script language="javascript" type="text/javascript" src="<?php print $shop_url; ?>js/payment.js"></script><script type="text/javascript">
        var xmlUrl = '<?php print $shop_url.'pmfeserver.php?login='.$account->getAccountData('login', $_SESSION['id']); ?>';

        $(document).ready(function(){
          new Payment(
            xmlUrl,
            {caching:225,fadeInTime:100,xmlErrorUrl:'errorxml/error.xml',xmlCache:true,enableErrorPage:true,enableLog:false,google_GTM:true,iovation:false,iovationTimeout:300,game_id:'metin2',styleparam:'website',modules:{backButton:'metin2.ingame',paysafecard:true,counter:true,couponButton:false,checkoutNotice:true}}
          );
        });
      </script><script type="text/javascript">
      var sessionId='0';
      dataLayer = [{
      'game': 'metin2',
      'language': 'en',
      'eventProcessId': '0',
      'sessionId' : sessionId
      }];
      </script>
</head>
<body class="loading">
<noscript></noscript>
<div id="container"></div>
</body>
</html>
