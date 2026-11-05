<?php
	// MT2009_PLUS_KOLA_V1: Kolo Losu - logika po stronie serwera (wszystkie losowania,
	// stan i pieniadze tutaj; strona i okno F12 tylko pokazuja wynik).
	//
	// Mechanika 1:1 z oryginalu (opis: /opt/metin2/cache/yohara/kola-mechanika.md):
	//   * 16 pol, pola glownych nagrod: poziom 1 -> {1}, 2 -> {1,9}, 3 -> {1,7,11};
	//   * przed kazdym obrotem kazde z 16 pol jest losowane od nowa (wazone, ze zwracaniem)
	//     z puli glownej albo standardowej biezacego poziomu;
	//   * kolo staje na kazdym polu z ta sama szansa 1/16;
	//   * pola kluczy 3, 7, 11, 15: ponizej najwyzszego poziomu trafienie = klucz (nagroda
	//     z pola tez jest wydawana); 4 klucze = nastepny poziom na 930 s, potem powrot na 1;
	//   * "Opusc ten poziom" = poziom 1, klucze od zera.
	//
	// Te same tabele i ta sama kolejnosc krokow ma gra (playerbot_wheel.h, okno F12):
	// jedna transakcja, wiersz kola_state konta zablokowany FOR UPDATE, Smocze Monety
	// zdejmowane warunkowym UPDATE (cash >= koszt), nagroda do player.item_award jak
	// zwykly zakup. Dwa obroty tego samego konta (dwie karty, strona i F12) ida jeden
	// po drugim, a saldo nigdy nie zejdzie ponizej zera.

	define('KOLA_FIELDS', 16);

	function kola_special_fields($tier) {
		$map = array(1 => array(1), 2 => array(1, 9), 3 => array(1, 7, 11));
		return isset($map[$tier]) ? $map[$tier] : $map[1];
	}

	function kola_key_fields() {
		return array(3, 7, 11, 15);
	}

	// MT2009_PLUS_KOLA_KEYS_V1 (wlasciciel 21.10.2026: "zauwazalnie wieksza szansa na pola z kluczem"): ponizej
	// najwyzszego poziomu kolo staje na jednym z 4 pol z kluczem z szansa key_chance % (domyslnie 40; oryginal
	// rowno 4 z 16 = 25%), inaczej na jednym z 12 pozostalych - tak samo jak StopField() w playerbot_wheel.h.
	function kola_stop_field($tier, $maxTier, $settings) {
		if ($tier >= $maxTier) return random_int(1, KOLA_FIELDS);
		$chance = max(0, min(100, (int)(isset($settings['key_chance']) ? $settings['key_chance'] : 40)));
		$keys = kola_key_fields();
		if (random_int(1, 100) <= $chance) return $keys[random_int(0, count($keys) - 1)];
		$rest = array_values(array_diff(range(1, KOLA_FIELDS), $keys));
		return $rest[random_int(0, count($rest) - 1)];
	}

	// Dane do wygladu (ikony pol, tla, nazwy i opisy przedmiotow zrodla) - mechanika
	// (koszty, pule, wagi, vnumy) jest wylacznie w bazie.
	function kola_look() {
		static $c = null;
		if ($c === null) {
			$c = json_decode(@file_get_contents(__DIR__ . '/kola.json'), true);
			if (!is_array($c)) $c = array('wheels' => array(), 'src_items' => array());
		}
		return $c;
	}

	function kola_q($db, $sql) {
		$r = mysqli_query($db, $sql);
		if ($r === false) {
			throw new Exception('SQL: ' . mysqli_error($db));
		}
		return $r;
	}

	// Zapytanie, ktorego blad nie jest bledem strony (np. tabel jeszcze nie ma - migracja
	// nie przeszla): false zamiast wyjatku (PHP 8 rzuca mysqli_sql_exception).
	function kola_try_q($db, $sql) {
		try {
			return mysqli_query($db, $sql);
		} catch (Exception $e) {
			return false;
		}
	}

	function kola_settings($db) {
		$s = array('enabled' => '1', 'override_wheel' => '0', 'rotation_anchor' => '1792360800',
			'rotation_days' => '14', 'rotation_order' => '243,162,238,239,240,241,246',
			'tier_seconds' => '930', 'keys_needed' => '4', 'key_chance' => '40');
		$r = kola_try_q($db, "SELECT name, value FROM itemshop.kola_settings");
		if ($r) {
			while ($row = mysqli_fetch_assoc($r)) $s[$row['name']] = $row['value'];
		}
		return $s;
	}

	function kola_wheels($db) {
		$out = array();
		$r = kola_try_q($db, "SELECT id, name, max_tier, cost1, cost2, cost3, ord FROM itemshop.kola_wheel ORDER BY ord, id");
		if ($r) {
			while ($row = mysqli_fetch_assoc($r)) {
				$row['id'] = (int)$row['id'];
				$row['max_tier'] = max(1, min(3, (int)$row['max_tier']));
				$row['costs'] = array(1 => (int)$row['cost1'], 2 => (int)$row['cost2'], 3 => (int)$row['cost3']);
				$out[$row['id']] = $row;
			}
		}
		return $out;
	}

	// Rotacja co rotation_days dni po liscie rotation_order, od rotation_anchor (unix);
	// override_wheel != 0 (panel) wylacza rotacje. Ta sama rachuba w playerbot_wheel.h.
	function kola_active($db, $now = null, $settings = null, $wheels = null) {
		if ($now === null) $now = time();
		if ($settings === null) $settings = kola_settings($db);
		if ($wheels === null) $wheels = kola_wheels($db);
		$order = array();
		foreach (explode(',', $settings['rotation_order']) as $id) {
			$id = (int)trim($id);
			if ($id && isset($wheels[$id])) $order[] = $id;
		}
		if (!$order) $order = array_keys($wheels);
		$days = max(1, (int)$settings['rotation_days']);
		$period = $days * 86400;
		$anchor = (int)$settings['rotation_anchor'];
		$n = (int)floor(($now - $anchor) / $period);
		$out = array('id' => 0, 'mode' => 'auto', 'from' => $anchor + $n * $period, 'until' => $anchor + ($n + 1) * $period,
			'order' => $order, 'next' => 0);
		if ($order) {
			$cnt = count($order);
			$idx = (($n % $cnt) + $cnt) % $cnt;
			$out['id'] = $order[$idx];
			$out['next'] = $order[($idx + 1) % $cnt];
		}
		$ov = (int)$settings['override_wheel'];
		if ($ov && isset($wheels[$ov])) {
			$out['id'] = $ov;
			$out['mode'] = 'admin';
		}
		return $out;
	}

	// [tier][special 0/1] => lista array(src_id, count, weight x100)
	function kola_pools($db, $wid) {
		$out = array();
		$r = kola_q($db, "SELECT tier, special, src_id, count, weight FROM itemshop.kola_pool WHERE wheel_id=" . (int)$wid . " ORDER BY tier, special, ord");
		while ($row = mysqli_fetch_assoc($r)) {
			$out[(int)$row['tier']][(int)$row['special']][] = array($row['src_id'], (int)$row['count'], (int)$row['weight']);
		}
		return $out;
	}

	function kola_items($db) {
		$out = array();
		$r = kola_try_q($db, "SELECT src_id, vnum, count_mul, socket0, socket1, socket2, expire_rel, icon_vnum, status, name, src_name, note, src_icon FROM itemshop.kola_item");
		if ($r) {
			while ($row = mysqli_fetch_assoc($r)) $out[$row['src_id']] = $row;
		}
		return $out;
	}

	// Wazone losowanie jednego wpisu puli (wagi w setnych, liczby calkowite: dokladnie
	// wagi zrodla, bez bledow zaokraglen).
	function kola_pick($list) {
		$total = 0;
		foreach ($list as $e) $total += $e[2];
		if ($total <= 0) return $list[count($list) - 1];
		$roll = random_int(1, $total);
		foreach ($list as $e) {
			$roll -= $e[2];
			if ($roll <= 0) return $e;
		}
		return $list[count($list) - 1];
	}

	// Uklad 16 pol na jeden obrot: [pozycja 1..16] => array(src, count, weight, special)
	function kola_layout($pools, $tier) {
		$special = kola_special_fields($tier);
		$out = array();
		for ($pos = 1; $pos <= KOLA_FIELDS; $pos++) {
			$isSpecial = in_array($pos, $special) ? 1 : 0;
			$e = kola_pick($pools[$tier][$isSpecial]);
			$out[$pos] = array($e[0], $e[1], $e[2], $isSpecial);
		}
		return $out;
	}

	function kola_layout_encode($layout) {
		$parts = array();
		for ($pos = 1; $pos <= KOLA_FIELDS; $pos++) {
			$e = $layout[$pos];
			$parts[] = str_replace(array('|', '#'), '', $e[0]) . '|' . (int)$e[1] . '|' . (int)$e[3];
		}
		return implode('#', $parts);
	}

	function kola_layout_decode($text) {
		$out = array();
		if ($text === '' || $text === null) return $out;
		$pos = 1;
		foreach (explode('#', $text) as $p) {
			$f = explode('|', $p);
			if (count($f) < 3) continue;
			$out[$pos++] = array($f[0], (int)$f[1], 0, (int)$f[2]);
		}
		return count($out) == KOLA_FIELDS ? $out : array();
	}

	function kola_token() {
		return bin2hex(random_bytes(8));
	}

	// Kolo sie zmienilo albo czas wyzszego poziomu minal -> poziom 1. Zwraca true, gdy zmienil stan.
	function kola_normalize(&$st, $wheel, $now) {
		$changed = false;
		if ((int)$st['wheel_id'] !== (int)$wheel['id']) {
			$st['wheel_id'] = (int)$wheel['id'];
			$st['tier'] = 1; $st['keys_count'] = 0; $st['tier_until'] = 0; $st['layout'] = '';
			$changed = true;
		}
		if ((int)$st['tier'] > (int)$wheel['max_tier'] || (int)$st['tier'] < 1) {
			$st['tier'] = 1; $st['keys_count'] = 0; $st['tier_until'] = 0;
			$changed = true;
		}
		if ((int)$st['tier'] > 1 && (int)$st['tier_until'] <= $now) {
			$st['tier'] = 1; $st['keys_count'] = 0; $st['tier_until'] = 0;
			$changed = true;
		}
		return $changed;
	}

	function kola_icon_url($src, $item, $look) {
		if ($item && (int)$item['src_icon'] && isset($look['src_items'][$src]['img'])) {
			return 'kola/img/' . $look['src_items'][$src]['img'];
		}
		if ($item && ((int)$item['icon_vnum'] || (int)$item['vnum'])) {
			$v = (int)$item['icon_vnum'] ? (int)$item['icon_vnum'] : (int)$item['vnum'];
			$f = ($v < 10000) ? sprintf('%05d', $v) : (string)$v;
			if (file_exists(__DIR__ . '/../img/item/' . $f . '.png')) return 'img/item/' . $f . '.png';
			// ikony, ktorych sklep nie mial (wyciete z paczki ikon klienta)
			if (file_exists(__DIR__ . '/img/v_' . (int)$item['vnum'] . '.png')) return 'kola/img/v_' . (int)$item['vnum'] . '.png';
		}
		if (isset($look['src_items'][$src]['img'])) return 'kola/img/' . $look['src_items'][$src]['img'];
		return 'img/error.png';
	}

	// Jak wpis wyglada na stronie: nazwa naszego przedmiotu, ikona, opis.
	function kola_entry_view($src, $count, $items, $look) {
		$it = isset($items[$src]) ? $items[$src] : null;
		$name = $it && $it['name'] !== '' ? $it['name'] : (isset($look['src_items'][$src]['name']) ? $look['src_items'][$src]['name'] : $src);
		$desc = '';
		if ($it && in_array($it['status'], array('ok', 'inny_czas')) && isset($look['src_items'][$src]['desc'])) {
			$desc = $look['src_items'][$src]['desc'];
		}
		$icon = kola_icon_url($src, $it, $look);
		// 'g': ikona zrodla (ilosc i czas sa na obrazku) - bez wlasnej plakietki z iloscia
		return array('n' => $name, 'c' => (int)$count * max(1, $it ? (int)$it['count_mul'] : 1),
			'i' => $icon, 'g' => strpos($icon, 'kola/img/i_') === 0 ? 1 : 0, 'd' => $desc);
	}

	// Kolo jest grywalne tylko, gdy kazda nagroda ma vnum (inaczej nie byloby czego wydac).
	function kola_wheel_ready($pools, $items, $wheel) {
		for ($t = 1; $t <= $wheel['max_tier']; $t++) {
			foreach (array(0, 1) as $sp) {
				if (empty($pools[$t][$sp])) return false;
				foreach ($pools[$t][$sp] as $e) {
					if (!isset($items[$e[0]]) || !(int)$items[$e[0]]['vnum']) return false;
				}
			}
		}
		return true;
	}

	function kola_state_row($db, $accId, $lock) {
		$r = kola_q($db, "SELECT account_id, wheel_id, tier, keys_count, tier_until, layout, token, last_token, last_result, spins, spent FROM itemshop.kola_state WHERE account_id=" . (int)$accId . ($lock ? " FOR UPDATE" : ""));
		return mysqli_fetch_assoc($r);
	}

	function kola_state_save($db, $st) {
		kola_q($db, "UPDATE itemshop.kola_state SET wheel_id=" . (int)$st['wheel_id'] . ", tier=" . (int)$st['tier']
			. ", keys_count=" . (int)$st['keys_count'] . ", tier_until=" . (int)$st['tier_until']
			. ", layout='" . mysqli_real_escape_string($db, $st['layout']) . "', token='" . mysqli_real_escape_string($db, $st['token'])
			. "', last_token='" . mysqli_real_escape_string($db, $st['last_token']) . "', last_result="
			. ($st['last_result'] === null ? "NULL" : "'" . mysqli_real_escape_string($db, $st['last_result']) . "'")
			. ", spins=" . (int)$st['spins'] . ", spent=" . (int)$st['spent'] . ", updated_at=NOW() WHERE account_id=" . (int)$st['account_id']);
	}

	// Stan konta do wyswietlenia (bez blokady); poprawia go, gdy kolo sie zmienilo / czas minal.
	function kola_load_state($db, $accId, $wheel) {
		kola_q($db, "INSERT IGNORE INTO itemshop.kola_state (account_id, wheel_id, token, updated_at) VALUES (" . (int)$accId . ", " . (int)$wheel['id'] . ", '" . kola_token() . "', NOW())");
		mysqli_begin_transaction($db);
		try {
			$st = kola_state_row($db, $accId, true);
			$changed = kola_normalize($st, $wheel, time());
			if ($st['token'] === '') { $st['token'] = kola_token(); $changed = true; }
			if ($changed) kola_state_save($db, $st);
			mysqli_commit($db);
		} catch (Exception $e) {
			mysqli_rollback($db);
			throw $e;
		}
		return $st;
	}

	function kola_balance($db, $accId) {
		$r = kola_q($db, "SELECT cash FROM account.account WHERE id=" . (int)$accId);
		$row = mysqli_fetch_assoc($r);
		return $row ? (int)$row['cash'] : 0;
	}

	// Stan dla przegladarki (JSON).
	function kola_state_view($st, $wheel, $balance, $settings) {
		$now = time();
		return array(
			'wheel' => (int)$wheel['id'],
			'tier' => (int)$st['tier'],
			'maxTier' => (int)$wheel['max_tier'],
			'keys' => (int)$st['keys_count'],
			'keysNeeded' => (int)$settings['keys_needed'],
			'left' => (int)$st['tier'] > 1 ? max(0, (int)$st['tier_until'] - $now) : 0,
			'cost' => (int)$wheel['costs'][(int)$st['tier']],
			'balance' => (int)$balance,
			'token' => $st['token'],
		);
	}

	// Jeden obrot. $accId/$login konta; $token z formularza strony (null = bez tokenu).
	// Zwraca tablice dla JSON-a: ok, error, state, layout, position, prize...
	function kola_spin($db, $accId, $login, $token, $via) {
		$settings = kola_settings($db);
		if ((int)$settings['enabled'] !== 1) return array('ok' => false, 'error' => 'Koło Losu jest teraz wyłączone.');
		$wheels = kola_wheels($db);
		$active = kola_active($db, null, $settings, $wheels);
		if (!$active['id']) return array('ok' => false, 'error' => 'Koło Losu jest chwilowo niedostępne.');
		$wheel = $wheels[$active['id']];
		$pools = kola_pools($db, $wheel['id']);
		$items = kola_items($db);
		if (!kola_wheel_ready($pools, $items, $wheel)) return array('ok' => false, 'error' => 'Koło Losu jest chwilowo niedostępne (nagrody w przygotowaniu).');
		$look = kola_look();
		$now = time();
		$keysNeeded = max(1, (int)$settings['keys_needed']);
		$tierSeconds = max(1, (int)$settings['tier_seconds']);

		kola_q($db, "INSERT IGNORE INTO itemshop.kola_state (account_id, wheel_id, token, updated_at) VALUES (" . (int)$accId . ", " . (int)$wheel['id'] . ", '" . kola_token() . "', NOW())");
		mysqli_begin_transaction($db);
		try {
			$st = kola_state_row($db, $accId, true);
			// Ten sam token co poprzedni obrot (odswiezenie, podwojne klikniecie, ponowione
			// zadanie po zerwanym polaczeniu): ten sam wynik jeszcze raz, bez placenia.
			if ($token !== null && $token !== '' && $token === $st['last_token'] && $st['last_result']) {
				mysqli_commit($db);
				$res = json_decode($st['last_result'], true);
				if (is_array($res)) { $res['replay'] = true; return $res; }
				return array('ok' => false, 'error' => 'Odśwież stronę.');
			}
			if ($token !== null && $token !== $st['token']) {
				// Stan zmienil sie gdzie indziej (druga karta, okno F12) - strona musi go wczytac.
				kola_normalize($st, $wheel, $now);
				mysqli_commit($db);
				return array('ok' => false, 'stale' => true, 'error' => 'Stan koła zmienił się (np. w grze lub w innym oknie) - wczytano go ponownie.',
					'state' => kola_state_view($st, $wheel, kola_balance($db, $accId), $settings));
			}
			kola_normalize($st, $wheel, $now);
			$tier = (int)$st['tier'];
			$cost = (int)$wheel['costs'][$tier];
			kola_q($db, "UPDATE account.account SET cash=cash-" . $cost . " WHERE id=" . (int)$accId . " AND cash>=" . $cost);
			if (mysqli_affected_rows($db) != 1) {
				mysqli_rollback($db);
				$bal = kola_balance($db, $accId);
				return array('ok' => false, 'error' => 'Za mało Smoczych Monet: masz ' . $bal . ' SM, obrót kosztuje ' . $cost . ' SM.');
			}
			$layout = kola_layout($pools, $tier);
			$pos = kola_stop_field($tier, (int)$wheel['max_tier'], $settings);
			$won = $layout[$pos];
			$it = $items[$won[0]];
			$count = (int)$won[1] * max(1, (int)$it['count_mul']);
			$keyHit = in_array($pos, kola_key_fields()) && $tier < (int)$wheel['max_tier'];
			$keysBefore = (int)$st['keys_count'];
			if ($keyHit) {
				$st['keys_count'] = (int)$st['keys_count'] + 1;
				if ($st['keys_count'] >= $keysNeeded) {
					$st['tier'] = $tier + 1;
					$st['keys_count'] = 0;
					$st['tier_until'] = $now + $tierSeconds;
				}
			}
			$date = date('Y-m-d H:i:s', $now);
			// Przedmiot na czas rzeczywisty z innym czasem niz w proto: koniec liczony od teraz.
			$socket0 = (int)$it['expire_rel'] > 0 ? $now + (int)$it['expire_rel'] : (int)$it['socket0'];
			kola_q($db, "INSERT INTO player.item_award (pid, login, vnum, count, given_time, why, socket0, socket1, socket2, mall) VALUES ("
				. (int)$accId . ", '" . mysqli_real_escape_string($db, $login) . "', " . (int)$it['vnum'] . ", " . $count . ", '" . $date
				. "', 'ItemShop Kolo Losu', " . $socket0 . ", " . (int)$it['socket1'] . ", " . (int)$it['socket2'] . ", 1)");
			kola_q($db, "INSERT INTO itemshop.kola_spin_log (account_id, login, via, wheel_id, tier, cost, position, special, src_id, vnum, count, name, status, key_hit, keys_after, tier_after, created_at) VALUES ("
				. (int)$accId . ", '" . mysqli_real_escape_string($db, $login) . "', '" . mysqli_real_escape_string($db, $via) . "', " . (int)$wheel['id'] . ", " . $tier . ", " . $cost . ", " . $pos . ", " . (int)$won[3]
				. ", '" . mysqli_real_escape_string($db, $won[0]) . "', " . (int)$it['vnum'] . ", " . $count . ", '" . mysqli_real_escape_string($db, $it['name'])
				. "', '" . mysqli_real_escape_string($db, $it['status']) . "', " . ($keyHit ? 1 : 0) . ", " . (int)$st['keys_count'] . ", " . (int)$st['tier'] . ", '" . $date . "')");
			$st['layout'] = kola_layout_encode($layout);
			$st['spins'] = (int)$st['spins'] + 1;
			$st['spent'] = (int)$st['spent'] + $cost;
			$usedToken = $st['token'];
			$st['last_token'] = $usedToken;
			$st['token'] = kola_token();
			$fields = array();
			for ($p = 1; $p <= KOLA_FIELDS; $p++) {
				$fv = kola_entry_view($layout[$p][0], $layout[$p][1], $items, $look);
				unset($fv['d']);
				$fields[] = $fv;
			}
			$res = array(
				'ok' => true,
				'position' => $pos,
				'special' => (int)$won[3],
				'key' => $keyHit ? 1 : 0,
				'tierBefore' => $tier,
				'keysBefore' => $keysBefore,
				'fields' => $fields,
				'prize' => kola_entry_view($won[0], $won[1], $items, $look),
				'cost' => $cost,
			);
			$bal = kola_balance($db, $accId);
			$res['state'] = kola_state_view($st, $wheel, $bal, $settings);
			$st['last_result'] = json_encode($res);
			kola_state_save($db, $st);
			mysqli_commit($db);
			return $res;
		} catch (Exception $e) {
			mysqli_rollback($db);
			error_log('kola_spin: ' . $e->getMessage());
			return array('ok' => false, 'error' => 'Błąd serwera - nic nie zostało pobrane. Spróbuj ponownie.');
		}
	}

	function kola_exit($db, $accId) {
		$settings = kola_settings($db);
		$wheels = kola_wheels($db);
		$active = kola_active($db, null, $settings, $wheels);
		if (!$active['id']) return array('ok' => false, 'error' => 'Koło Losu jest chwilowo niedostępne.');
		$wheel = $wheels[$active['id']];
		kola_q($db, "INSERT IGNORE INTO itemshop.kola_state (account_id, wheel_id, token, updated_at) VALUES (" . (int)$accId . ", " . (int)$wheel['id'] . ", '" . kola_token() . "', NOW())");
		mysqli_begin_transaction($db);
		try {
			$st = kola_state_row($db, $accId, true);
			kola_normalize($st, $wheel, time());
			$st['tier'] = 1; $st['keys_count'] = 0; $st['tier_until'] = 0;
			kola_state_save($db, $st);
			mysqli_commit($db);
		} catch (Exception $e) {
			mysqli_rollback($db);
			return array('ok' => false, 'error' => 'Błąd serwera. Spróbuj ponownie.');
		}
		return array('ok' => true, 'state' => kola_state_view($st, $wheel, kola_balance($db, $accId), $settings));
	}

	// Podglad bez logowania (?preview=1, iframe na stronie projektu): ta sama mechanika,
	// stan w sesji, bez pieniedzy, bez nagrod, bez logu.
	function kola_trial_spin($db, &$sess) {
		$settings = kola_settings($db);
		$wheels = kola_wheels($db);
		$active = kola_active($db, null, $settings, $wheels);
		if (!$active['id']) return array('ok' => false, 'error' => 'Koło Losu jest chwilowo niedostępne.');
		$wheel = $wheels[$active['id']];
		$pools = kola_pools($db, $wheel['id']);
		$items = kola_items($db);
		if (!kola_wheel_ready($pools, $items, $wheel)) return array('ok' => false, 'error' => 'Koło Losu jest chwilowo niedostępne (nagrody w przygotowaniu).');
		$look = kola_look();
		$now = time();
		$st = kola_trial_state($sess, $wheel);
		kola_normalize($st, $wheel, $now);
		$tier = (int)$st['tier'];
		$keysNeeded = max(1, (int)$settings['keys_needed']);
		$layout = kola_layout($pools, $tier);
		$pos = kola_stop_field($tier, (int)$wheel['max_tier'], $settings);
		$won = $layout[$pos];
		$keyHit = in_array($pos, kola_key_fields()) && $tier < (int)$wheel['max_tier'];
		$keysBefore = (int)$st['keys_count'];
		if ($keyHit) {
			$st['keys_count']++;
			if ($st['keys_count'] >= $keysNeeded) {
				$st['tier'] = $tier + 1; $st['keys_count'] = 0; $st['tier_until'] = $now + (int)$settings['tier_seconds'];
			}
		}
		$sess = $st;
		$fields = array();
		for ($p = 1; $p <= KOLA_FIELDS; $p++) $fields[] = kola_entry_view($layout[$p][0], $layout[$p][1], $items, $look);
		return array('ok' => true, 'trial' => true, 'position' => $pos, 'special' => (int)$won[3], 'key' => $keyHit ? 1 : 0,
			'tierBefore' => $tier, 'keysBefore' => $keysBefore, 'fields' => $fields,
			'prize' => kola_entry_view($won[0], $won[1], $items, $look), 'cost' => (int)$wheel['costs'][$tier],
			'state' => kola_state_view($st, $wheel, 0, $settings));
	}

	function kola_trial_exit($db, &$sess) {
		$settings = kola_settings($db);
		$wheels = kola_wheels($db);
		$active = kola_active($db, null, $settings, $wheels);
		if (!$active['id']) return array('ok' => false, 'error' => 'Koło Losu jest chwilowo niedostępne.');
		$wheel = $wheels[$active['id']];
		$st = kola_trial_state($sess, $wheel);
		kola_normalize($st, $wheel, time());
		$st['tier'] = 1; $st['keys_count'] = 0; $st['tier_until'] = 0;
		$sess = $st;
		return array('ok' => true, 'state' => kola_state_view($st, $wheel, 0, $settings));
	}

	function kola_trial_state(&$sess, $wheel) {
		if (!is_array($sess)) {
			$sess = array('account_id' => 0, 'wheel_id' => (int)$wheel['id'], 'tier' => 1, 'keys_count' => 0, 'tier_until' => 0,
				'layout' => '', 'token' => 'podglad', 'last_token' => '', 'last_result' => null, 'spins' => 0, 'spent' => 0);
		}
		return $sess;
	}
?>
