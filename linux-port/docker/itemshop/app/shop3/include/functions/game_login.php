<?php
	// MT2009_PLUS_SHOP3_TOKEN_V1 - the in-game login of the ItemShop (the owner, 10 Nov 2026: "always signed in as the
	// account currently in game, right after login and on every open").
	//
	// What went wrong: the game's link (ACMD(do_in_game_mall)) was signed with md5(pid . account id . "GF9001") only, and
	// Account::AutoLoginShop wrote the account into whatever session the client's browser already had - no new session
	// id, and on any link it did not take (blocked by its own clock, a stale or broken link) it simply went on with that
	// session. The client's embedded browser keeps the session cookie for the whole game process, so after a switch to
	// another account the shop showed the previous account (or the login form) and the player had to "Wyloguj" and type
	// the other account's login and password. The static md5 also never expired - a link seen once logged in for ever.
	//
	// Now every open from the game (Shift+F12, the ItemShop buttons) brings a fresh token minted by the game core
	// (overlay mt2009_shop3_token.cpp): aid, ts, n and tok = HMAC-SHA256(key, "shop3|1|pid|aid|ts|n"). This page
	//   - takes it for SHOP3_TOKEN_TTL seconds and once (the nonce is burnt in the container's temp directory),
	//   - checks that the character belongs to that account and the account may play,
	//   - throws away the browser's old session completely (another account's or not) and starts a new one with a new
	//     id, signed in as exactly that account and character,
	//   - on any failure logs the old session out as well and asks to open the shop again from the game - never the
	//     previous account, never the login form inside the game.
	// The plain web login (the login form, pages/shop/login.php) works as before.
	//
	// The old static link (pid + sas only) is refused unless M2_SHOP3_LEGACY_SAS=1 (a core without this change).

	define('SHOP3_TOKEN_TTL', 21600);	// MT2009_PLUS_SHOP3_TOKEN_V2 (players, 10 Nov 2026: "Otwórz sklep ponownie z gry"): 6 h - the client may keep
	// the link it got at login and open it later; the token stays signed and bound to its account and character		// seconds a token lives (the game answers "/in_game_mall" at once)
	define('SHOP3_TOKEN_SKEW', 30);		// a token "from the future" by up to this much (two containers, one clock)

	function shop3_token_key()
	{
		$secret = getenv('M2_SHOP3_TOKEN_SECRET');
		if ($secret !== false && $secret !== '')
			return $secret;
		$db_password = getenv('M2_DB_PASSWORD');
		if ($db_password === false || $db_password === '')
			return null;
		return 'mt2009plus-shop3-token|' . $db_password;
	}

	// One use per token: a file named after the nonce, created exclusively. Old ones are swept now and then.
	function shop3_token_burn($nonce)
	{
		$dir = rtrim(sys_get_temp_dir(), '/') . '/mt2009-shop3-tokens';
		if (!is_dir($dir))
			@mkdir($dir, 0700, true);
		if (!is_dir($dir) || !is_writable($dir))
			return true;	// no place to remember it - the 120 s life still holds
		if (mt_rand(1, 50) == 1)
			foreach ((array)@glob($dir . '/*') as $old)
				if (@filemtime($old) < time() - 2 * (SHOP3_TOKEN_TTL + SHOP3_TOKEN_SKEW))
					@unlink($old);
		$fh = @fopen($dir . '/' . $nonce, 'x');
		if ($fh === false)
			return false;	// used already
		fclose($fh);
		return true;
	}

	// Throws the browser's session away and starts an empty one with a new id (the cookie is sent again).
	function shop3_session_reset()
	{
		$keep = [];
		foreach (['lang', 'm2_lang', 'm2_lang_chosen'] as $k)
			if (isset($_SESSION[$k]))
				$keep[$k] = $_SESSION[$k];
		$_SESSION = [];
		@session_regenerate_id(true);
		foreach ($keep as $k => $v)
			$_SESSION[$k] = $v;
	}

	function shop3_no_store()
	{
		header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0, private');
		header('Pragma: no-cache');
		header('Expires: Thu, 01 Jan 1970 00:00:00 GMT');
	}

	// "Open the shop again from the game" - for a link that did not sign in. The page has no account on it.
	function shop3_game_login_failed($why)
	{
		global $shop_url, $shop_title, $lang_shop;
		error_log('shop3 in-game login refused: ' . $why . ' (pid=' . (isset($_GET['pid']) ? substr((string)$_GET['pid'], 0, 12) : '-') . ')');
		shop3_session_reset();
		shop3_no_store();
		// 200, not 403: the client's embedded IE puts its own "friendly" error page over a short 4xx answer.
		include 'pages/shop/reopen.php';
		die();
	}

	// Checks the link and signs in; returns only when the request is no in-game link at all.
	function shop3_game_login($account, $player)
	{
		global $shop_url, $game_ishop_key;

		if (!isset($_GET['pid']) || (!isset($_GET['tok']) && !isset($_GET['sas'])))
			return;

		$pid = (string)$_GET['pid'];
		if (!ctype_digit($pid) || strlen($pid) > 10 || (int)$pid <= 0)
			shop3_game_login_failed('bad pid');

		$owner = $player->getPlayerData('account_id', (int)$pid);
		if (!$owner)
			shop3_game_login_failed('no such character');
		$owner = (int)$owner;

		if (isset($_GET['tok']))
		{
			$aid = isset($_GET['aid']) ? (string)$_GET['aid'] : '';
			$ts = isset($_GET['ts']) ? (string)$_GET['ts'] : '';
			$nonce = isset($_GET['n']) ? (string)$_GET['n'] : '';
			$tok = strtolower((string)$_GET['tok']);
			if (!ctype_digit($aid) || strlen($aid) > 10 || !ctype_digit($ts) || strlen($ts) > 12
				|| !preg_match('/^[0-9a-f]{32}$/', $nonce) || !preg_match('/^[0-9a-f]{64}$/', $tok))
				shop3_game_login_failed('malformed token');
			$key = shop3_token_key();
			if ($key === null)
				shop3_game_login_failed('no token key (M2_SHOP3_TOKEN_SECRET / M2_DB_PASSWORD)');
			$expect = hash_hmac('sha256', 'shop3|1|' . $pid . '|' . $aid . '|' . $ts . '|' . $nonce, $key);
			if (!hash_equals($expect, $tok))
				shop3_game_login_failed('bad signature');
			if ((int)$aid !== $owner)
				shop3_game_login_failed('character not of the account');
			// A genuine token that is old or used already (the browser asked for the link twice, a reload) while this
			// browser is signed in as exactly its account and character: that session stays - nothing of another
			// account can be shown by it.
			$same_session = !empty($_SESSION['game']) && isset($_SESSION['id']) && (int)$_SESSION['id'] === $owner
				&& isset($_SESSION['pid']) && (int)$_SESSION['pid'] === (int)$pid;
			$age = time() - (int)$ts;
			$fresh = $age <= SHOP3_TOKEN_TTL && $age >= -SHOP3_TOKEN_SKEW;
			// MT2009_PLUS_SHOP3_TOKEN_V2: a reused genuine token (the client opens the shop again with the link it got) is fine -
			// it is signed and bound to this account and character; the session is reset to them below.
			shop3_token_burn($nonce);
			if (!$fresh)
			{
				if ($same_session && $account->gameLoginAllowed($owner))
				{
					shop3_no_store();
					header('Location: ' . $shop_url);
					die();
				}
				shop3_game_login_failed($fresh ? 'token used already' : 'expired token (age ' . $age . ' s)');
			}
		}
		else
		{
			// The core's old static link - only where that core still runs.
			// MT2009_PLUS_SHOP3_TOKEN_V2: older clients (before 3.0.23) send only this link - accepted unless the operator set
			// M2_SHOP3_LEGACY_SAS=0; the session is reset to this account below, so another account's shop is never shown
			if (getenv('M2_SHOP3_LEGACY_SAS') === '0')
				shop3_game_login_failed('static link without token');
			$sas = strtolower((string)$_GET['sas']);
			if (!preg_match('/^[0-9a-f]{32}$/', $sas) || !hash_equals(md5($pid . $owner . $game_ishop_key), $sas))
				shop3_game_login_failed('bad sas');
		}

		// The game let this account in a moment ago (the core checked its status and availDt); only a ban since then
		// stops it here. availDt is not compared with PHP's clock (another zone than the database's could read a
		// fresh account as blocked).
		if (!$account->gameLoginAllowed($owner))
			shop3_game_login_failed('account not OK');

		shop3_session_reset();
		$account->startGameSession($owner, (int)$pid);
		shop3_no_store();
		header('Location: ' . $shop_url);
		die();
	}
?>
