<?php
	// MT2009_PLUS_WEB_I18N_V1: the ItemShop in other languages - the PHP twin of the panels' m2i18n.py.
	//
	// The shop is written in Polish (pages/*.php, include/languages/pl.php, the catalogue's rows). A visitor in
	// another language gets the finished page translated: every text between tags and every title/alt/
	// placeholder that i18n/<code>.json (with i18n/<code>/*.json: the game's own names and texts) knows -
	// whole, by a {0}-pattern, or piece by piece around " · ", ": " - is put in their language, and
	// /m2i18n-watch.js does the same in the browser for what a script draws later. A language is a file:
	// dropping i18n/xx.json in adds it to the switch. A Polish page is sent byte for byte as it was.
	//
	// The language, first that says one: ?lang=xx (remembered), the m2lang cookie (shared with the panels),
	// the language the player chose in the game client (player.player.language, sent by the client as /lang),
	// the server's default language (M2_DEFAULT_LANGUAGE, MT2009_PLUS_LANGUAGE_DEFAULT_V1), and only without one the
	// browser's - only one that does not list Polish at all - and Polish.

	define('M2I18N_DIR', realpath(__DIR__ . '/../../../i18n') ?: (__DIR__ . '/../../../i18n'));
	define('M2I18N_SOURCE', 'pl');
	define('M2I18N_FALLBACK', 'en');

	function m2i18n_order() {
		return array('pl', 'en', 'de', 'tr', 'ro', 'es', 'it', 'fr', 'pt', 'cz', 'hu', 'gr', 'ae', 'uk');
	}

	function m2i18n_files($code) {
		$out = array();
		if (!preg_match('/^[a-z]{2}(-[a-z]{2})?$/', $code))
			return $out;
		if (is_file(M2I18N_DIR . '/' . $code . '.json'))
			$out[] = M2I18N_DIR . '/' . $code . '.json';
		if (is_dir(M2I18N_DIR . '/' . $code)) {
			$more = glob(M2I18N_DIR . '/' . $code . '/*.json');
			sort($more);
			$out = array_merge($out, $more);
		}
		return $out;
	}

	// [code => name] of every language there is, Polish first
	function m2i18n_languages() {
		static $langs = null;
		if ($langs !== null)
			return $langs;
		$langs = array('pl' => 'Polski');
		foreach ((array)@scandir(M2I18N_DIR) as $entry) {
			// a language is its main file; i18n/<code>/ alone (names) is not one yet
			if (!preg_match('/^([a-z]{2}(-[a-z]{2})?)\.json$/', (string)$entry, $mm) || isset($langs[$mm[1]]))
				continue;
			$code = $mm[1];
			$files = m2i18n_files($code);
			if (!$files)
				continue;
			$name = $code;
			$data = @json_decode(@file_get_contents($files[0]), true);
			if (is_array($data) && isset($data['_meta']['name']))
				$name = $data['_meta']['name'];
			$langs[$code] = $name;
		}
		$order = m2i18n_order();
		uksort($langs, function ($a, $b) use ($order) {
			$ia = array_search($a, $order); $ib = array_search($b, $order);
			$ia = $ia === false ? 99 : $ia; $ib = $ib === false ? 99 : $ib;
			return $ia == $ib ? strcmp($a, $b) : $ia - $ib;
		});
		return $langs;
	}

	function m2i18n_norm($text) {
		return trim(preg_replace('/\s+/u', ' ', $text));
	}

	function m2i18n_read($code) {
		$data = array('exact' => array(), 'patterns' => array(), 'regex' => array(), 'names' => array());
		foreach (m2i18n_files($code) as $file) {
			$part = @json_decode(@file_get_contents($file), true);
			if (!is_array($part))
				continue;
			foreach (array('exact', 'patterns', 'names') as $key)
				if (isset($part[$key]) && is_array($part[$key]))
					foreach ($part[$key] as $k => $v)
						if (is_string($v) && trim($v) !== '')
							$data[$key][m2i18n_norm((string)$k)] = $v;
			if (isset($part['regex']) && is_array($part['regex']))
				foreach ($part['regex'] as $r)
					if (is_array($r) && count($r) == 2)
						$data['regex'][] = $r;
		}
		return $data;
	}

	// the language's tables, with the fallback's (English) under them
	function m2i18n_tables($code) {
		static $cache = array();
		if (isset($cache[$code]))
			return $cache[$code];
		$own = m2i18n_read($code);
		$t = $own;
		if ($code != M2I18N_FALLBACK && $code != M2I18N_SOURCE) {
			$fb = m2i18n_read(M2I18N_FALLBACK);
			foreach (array('exact', 'patterns', 'names') as $key)
				$t[$key] = $own[$key] + $fb[$key];
			$t['regex'] = array_merge($own['regex'], $fb['regex']);
		}
		$compiled = array();
		foreach ($t['patterns'] as $src => $dst) {
			if (!preg_match('/\{\d+\}/', $src))
				continue;
			$parts = preg_split('/\{(\d+)\}/', $src, -1, PREG_SPLIT_DELIM_CAPTURE);
			$rx = '';
			$groups = array();
			$literal = '';
			foreach ($parts as $i => $part) {
				if ($i % 2 == 0) {
					$rx .= preg_quote($part, '~');
					if (mb_strlen($part) > mb_strlen($literal))
						$literal = $part;
				} else {
					$groups[] = (int)$part;
					$rx .= '(.+?)';
				}
			}
			$compiled[] = array('~^' . $rx . '$~su', $groups, $dst, $literal);
		}
		usort($compiled, function ($a, $b) { return mb_strlen($b[3]) - mb_strlen($a[3]); });
		$t['compiled'] = $compiled;
		$cache[$code] = $t;
		return $t;
	}

	function m2i18n_lookup($core, $t, $depth = 0) {
		if (isset($t['exact'][$core]))
			return $t['exact'][$core];
		if (isset($t['names'][$core]))
			return $t['names'][$core];
		foreach ($t['compiled'] as $p) {
			if ($p[3] !== '' && strpos($core, $p[3]) === false)
				continue;
			if (!preg_match($p[0], $core, $m))
				continue;
			$values = array();
			foreach ($p[1] as $idx => $number) {
				$value = $m[$idx + 1];
				$trim = trim($value);
				if ($depth < 2 && $trim !== '') {
					$inner = m2i18n_lookup($trim, $t, $depth + 1);
					if ($inner !== null)
						$value = str_replace($trim, $inner, $value);
				}
				$values[$number] = $value;
			}
			return preg_replace_callback('/\{(\d+)\}/', function ($g) use ($values) {
				return isset($values[(int)$g[1]]) ? $values[(int)$g[1]] : $g[0];
			}, $p[2]);
		}
		return null;
	}

	function m2i18n_translate($core, $t, $depth = 0) {
		$hit = m2i18n_lookup($core, $t);
		if ($hit !== null)
			return $hit;
		if ($depth < 3 && preg_match('/^([^\w(„"\'«]+)(?=[\w(„"\'«])/u', $core, $m)) {
			$rest = substr($core, strlen($m[1]));
			$out = m2i18n_translate($rest, $t, $depth + 1);
			if ($out !== $rest)
				return $m[1] . $out;
		}
		if ($depth < 3 && preg_match('/(\s*(?:[:：…*!?.]|\.\.\.|\s[→↗›»]|\s\(\?\))+\s*)$/u', $core, $m) && strlen($m[1]) < strlen($core)) {
			$head = substr($core, 0, strlen($core) - strlen($m[1]));
			$out = m2i18n_translate($head, $t, $depth + 1);
			if ($out !== $head)
				return $out . $m[1];
		}
		$split = '/((?<=[.!?…])\s+|\s+[·|—–\/•]\s+|:\s+|,\s+|\s+\(|\)\s+|\s*[\[\]]\s*)/u';
		if ($depth < 2 && preg_match($split, $core)) {
			$pieces = preg_split($split, $core, -1, PREG_SPLIT_DELIM_CAPTURE);
			$changed = false;
			for ($i = 0; $i < count($pieces); $i += 2) {
				$piece = trim($pieces[$i]);
				if ($piece !== '' && preg_match('/\pL/u', $piece)) {
					$out = m2i18n_translate($piece, $t, $depth + 1);
					if ($out !== $piece) {
						$pieces[$i] = str_replace($piece, $out, $pieces[$i]);
						$changed = true;
					}
				}
			}
			if ($changed)
				return implode('', $pieces);
		}
		$result = $core;
		foreach ($t['regex'] as $r) {
			$out = @preg_replace('~' . str_replace('~', '\~', $r[0]) . '~u', $r[1], $result);
			if (is_string($out))
				$result = $out;
		}
		return $result;
	}

	// one text (not HTML) in the language; unchanged when unknown
	function m2i18n_text($text, $code = null) {
		static $cache = array();
		$code = $code ?: m2i18n_lang();
		if ($code == M2I18N_SOURCE || !is_string($text) || $text === '' || !preg_match('/\pL/u', $text))
			return $text;
		$core = m2i18n_norm($text);
		if ($core === '')
			return $text;
		$key = $code . "\0" . $core;
		if (!isset($cache[$key]))
			$cache[$key] = m2i18n_translate($core, m2i18n_tables($code));
		$out = $cache[$key];
		if ($out === $core)
			return $text;
		preg_match('/^\s*/u', $text, $lead);
		preg_match('/\s*$/u', $text, $trail);
		return $lead[0] . $out . $trail[0];
	}

	function m2i18n_attr_value($value, $code) {
		if ($value === '' || strpos($value, '<?') !== false)
			return $value;
		$plain = html_entity_decode($value, ENT_QUOTES | ENT_HTML5, 'UTF-8');
		$out = m2i18n_text($plain, $code);
		return $out === $plain ? $value : htmlspecialchars($out, ENT_QUOTES, 'UTF-8');
	}

	// a whole page (or a fragment) in the language
	function m2i18n_html($body, $code = null, $script = true) {
		$code = $code ?: m2i18n_lang();
		if ($code == M2I18N_SOURCE || !is_string($body) || $body === '')
			return $body;
		$stash = array();
		$keep = function ($m) use (&$stash) {
			$stash[] = $m[1];
			return "<!--\x00M2" . (count($stash) - 1) . "\x00-->";
		};
		$work = preg_replace_callback('~(<(script|style|textarea|pre|code)\b[^>]*>.*?</\2\s*>)~is', $keep, $body);
		$work = preg_replace_callback('~(<([a-zA-Z][\w-]*)\b[^>]*\btranslate=["\']no["\'][^>]*>.*?</\2\s*>)~is', $keep, $work);
		$parts = preg_split('~(<(?:[^>"\']|"[^"]*"|\'[^\']*\')*>)~s', $work, -1, PREG_SPLIT_DELIM_CAPTURE);
		$out = '';
		foreach ($parts as $part) {
			if ($part === '')
				continue;
			if ($part[0] == '<') {
				if (strncmp($part, '</', 2) && strncmp($part, '<!', 2)) {
					$part = preg_replace_callback('~\b(title|alt|placeholder|aria-label|data-confirm|data-title|data-tip|tooltip-content|label)=(["\'])(.*?)\2~s', function ($m) use ($code) {
						return $m[1] . '=' . $m[2] . m2i18n_attr_value($m[3], $code) . $m[2];
					}, $part);
					if (stripos($part, '<input') === 0 && preg_match('~\btype=["\']?(submit|button|reset)\b~i', $part))
						$part = preg_replace_callback('~\bvalue=(["\'])(.*?)\1~s', function ($m) use ($code) {
							return 'value=' . $m[1] . m2i18n_attr_value($m[2], $code) . $m[1];
						}, $part, 1);
				}
				$out .= $part;
			} elseif (preg_match('/\pL/u', $part)) {
				$plain = html_entity_decode($part, ENT_QUOTES | ENT_HTML5, 'UTF-8');
				$tr = m2i18n_text($plain, $code);
				$out .= $tr === $plain ? $part : htmlspecialchars($tr, ENT_NOQUOTES, 'UTF-8');
			} else {
				$out .= $part;
			}
		}
		do {
			$before = $out;
			$out = preg_replace_callback("~<!--\x00M2(\d+)\x00-->~", function ($m) use ($stash) { return $stash[(int)$m[1]]; }, $out);
		} while ($out !== $before);
		$web = array('cz' => 'cs', 'gr' => 'el', 'ae' => 'ar', 'dk' => 'da');
		$out = preg_replace('~(<html\b[^>]*\blang=)(["\'])[\w-]*\2~i', '$1$2' . (isset($web[$code]) ? $web[$code] : $code) . '$2' . ($code == 'ae' ? ' dir="rtl"' : ''), $out, 1);
		if ($script && stripos($out, '</body>') !== false && strpos($out, 'data-m2i18n=') === false) {
			$v = 0;
			foreach (array_merge(m2i18n_files($code), m2i18n_files(M2I18N_FALLBACK)) as $f)
				$v = max($v, (int)@filemtime($f));
			$tag = '<script src="/m2i18n-watch.js?v=' . $v . '" data-m2i18n="' . $code . '" data-src="/shop3/i18n.php?lang=' . $code . '&amp;v=' . $v . '" defer></script>';
			$pos = strripos($out, '</body>');
			$out = substr($out, 0, $pos) . $tag . substr($out, $pos);
		}
		return $out;
	}

	// a JSON answer's texts
	function m2i18n_json_value($value, $code) {
		if (is_array($value)) {
			foreach ($value as $k => $v)
				$value[$k] = m2i18n_json_value($v, $code);
			return $value;
		}
		if (is_string($value)) {
			if (strpos($value, '<') !== false && strpos($value, '>') !== false)
				return m2i18n_html($value, $code, false);
			return m2i18n_text($value, $code);
		}
		return $value;
	}

	// the output buffer's callback: HTML or JSON, in the visitor's language
	function m2i18n_output($buffer) {
		$code = m2i18n_lang();
		if ($code == M2I18N_SOURCE || $buffer === '')
			return $buffer;
		$type = '';
		foreach (headers_list() as $h)
			if (stripos($h, 'Content-Type:') === 0)
				$type = strtolower($h);
		$trim = ltrim($buffer);
		if (strpos($type, 'json') !== false || ($type === '' && ($trim !== '' && ($trim[0] == '{' || $trim[0] == '[')))) {
			$data = json_decode($buffer, true);
			if ($data === null)
				return $buffer;
			return json_encode(m2i18n_json_value($data, $code), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
		}
		if ($type !== '' && strpos($type, 'html') === false)
			return $buffer;
		return m2i18n_html($buffer, $code, stripos($buffer, '</body>') !== false);
	}

	// MT2009_PLUS_LANGUAGE_DEFAULT_V1: the server's default language (M2_DEFAULT_LANGUAGE in .env) when the shop has it
	function m2i18n_server_default() {
		$code = strtolower(trim((string)getenv('M2_DEFAULT_LANGUAGE')));
		$alias = array('cs' => 'cz', 'el' => 'gr', 'ar' => 'ae');
		if (isset($alias[$code]))
			$code = $alias[$code];
		$langs = m2i18n_languages();
		return ($code !== '' && isset($langs[$code])) ? $code : null;
	}

	function m2i18n_accept($accept) {
		$wanted = array();
		foreach (explode(',', (string)$accept) as $part) {
			$bits = explode(';', trim($part));
			$tag = strtolower(trim($bits[0]));
			$q = 1.0;
			foreach (array_slice($bits, 1) as $b)
				if (strpos(trim($b), 'q=') === 0)
					$q = (float)substr(trim($b), 2);
			if ($tag !== '')
				$wanted[] = array($q, explode('-', $tag)[0]);
		}
		usort($wanted, function ($a, $b) { return $b[0] < $a[0] ? -1 : ($b[0] > $a[0] ? 1 : 0); });
		$alias = array('cs' => 'cz', 'el' => 'gr', 'ar' => 'ae');
		$tags = array();
		foreach ($wanted as $w)
			$tags[] = isset($alias[$w[1]]) ? $alias[$w[1]] : $w[1];
		if (in_array('pl', $tags))
			return null;
		$langs = m2i18n_languages();
		foreach ($tags as $tag)
			if (isset($langs[$tag]))
				return $tag;
		return null;
	}

	// the player's language from the game (player.player.language, MT2009_PLUS_LANGUAGE), when there is one
	function m2i18n_player_lang($pdo, $pid) {
		if (!$pdo || !$pid)
			return null;
		try {
			$st = $pdo->prepare("SELECT language FROM player.player WHERE id = ? LIMIT 1");
			$st->execute(array((int)$pid));
			$code = strtolower((string)$st->fetchColumn());
		} catch (Exception $e) {
			return null;   // a server whose player table has no language column yet
		}
		$langs = m2i18n_languages();
		return isset($langs[$code]) ? $code : null;
	}

	function m2i18n_set($code) {
		$langs = m2i18n_languages();
		if (!isset($langs[$code]))
			return false;
		$GLOBALS['m2i18n_lang'] = $code;
		return true;
	}

	function m2i18n_lang() {
		if (isset($GLOBALS['m2i18n_lang']))
			return $GLOBALS['m2i18n_lang'];
		$langs = m2i18n_languages();
		$code = null;
		if (isset($_GET['lang']) && is_string($_GET['lang']) && isset($langs[strtolower($_GET['lang'])])) {
			$code = strtolower($_GET['lang']);
			if (!headers_sent())
				setcookie('m2lang', $code, array('expires' => time() + 31536000, 'path' => '/', 'samesite' => 'Lax'));
			if (session_status() === PHP_SESSION_ACTIVE)
				$_SESSION['m2_lang_chosen'] = 1;
		} elseif (isset($_COOKIE['m2lang']) && isset($langs[$_COOKIE['m2lang']])) {
			$code = $_COOKIE['m2lang'];
		} elseif (session_status() === PHP_SESSION_ACTIVE && isset($_SESSION['m2_lang']) && isset($langs[$_SESSION['m2_lang']])) {
			$code = $_SESSION['m2_lang'];
		} elseif (($code = m2i18n_server_default()) !== null) {
			// the server's default; the player's own game language (header.php) still comes before it
			$GLOBALS['m2i18n_how'] = 'server';
			$GLOBALS['m2i18n_lang'] = $code;
			return $code;
		} else {
			$code = m2i18n_accept(isset($_SERVER['HTTP_ACCEPT_LANGUAGE']) ? $_SERVER['HTTP_ACCEPT_LANGUAGE'] : '');
		}
		$GLOBALS['m2i18n_how'] = $code ? (isset($_GET['lang']) || isset($_COOKIE['m2lang']) || isset($_SESSION['m2_lang']) ? 'chosen' : 'browser') : 'default';
		$code = $code ?: M2I18N_SOURCE;
		$GLOBALS['m2i18n_lang'] = $code;
		return $code;
	}

	// the switch (a select that reloads the page with ?lang=)
	function m2i18n_switch_html() {
		$langs = m2i18n_languages();
		if (count($langs) < 2)
			return '';
		$cur = m2i18n_lang();
		$html = '<span class="m2-lang" translate="no"><select aria-label="Język / Language" onchange="var u=new URL(location.href);u.searchParams.set(\'lang\',this.value);location.href=u.toString()">';
		foreach ($langs as $code => $name)
			$html .= '<option value="' . $code . '"' . ($code == $cur ? ' selected' : '') . '>' . htmlspecialchars($name, ENT_QUOTES, 'UTF-8') . '</option>';
		return $html . '</select></span>';
	}
