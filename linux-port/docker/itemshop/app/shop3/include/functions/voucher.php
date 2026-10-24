<?php
	// MT2009_PLUS_ITEMSHOP_V3_V3: "Wykorzystaj voucher" of the in-game shop, in the second shop - the same two kinds of
	// codes the game takes in that tab (CItemShopManager::SendUseCodeVoucher):
	//  - our promo codes first (overlay playerbot_voucher.h, the same as "/kod"): common.mt2009_voucher keeps only
	//    SHA2(CONCAT(salt, normalized code), 256) and the rewards; once per account (player.mt2009_voucher_used, the
	//    row first), the items to the ItemShop storage (player.item_award, mall=1, "Magazyn ItemShop"); switched off
	//    with the Seban panel's event flag m2_vouchers_off;
	//  - any other code is a cash voucher of the db core (common.vouchers: use_count < max_use_count, then
	//    account.cash + cash - ClientManager.cpp UseCodeVoucher).
	// 5 tries a minute per account (the game: 5 a minute per character); the answer is the in-game window's text.

	const MT2009_VOUCHER_SALT = 'MT2009PLUS|kody|v1|';	// playerbot_voucher_rules.h VOUCHER_SALT
	const MT2009_VOUCHER_MAX_LEN = 32;

	// playerbot_voucher_rules.h Normalize: case-free, spaces/tabs/dashes/underscores dropped, [A-Z0-9] only, 1..32.
	function mt2009_voucher_normalize($typed)
	{
		$out = '';
		$len = strlen($typed);
		for($i = 0; $i < $len; $i++)
		{
			$c = $typed[$i];
			if($c==' ' || $c=="\t" || $c=='-' || $c=='_' || $c=="\r" || $c=="\n")
				continue;
			if($c>='a' && $c<='z')
				$out .= strtoupper($c);
			else if(($c>='A' && $c<='Z') || ($c>='0' && $c<='9'))
				$out .= $c;
			else
				return '';
			if(strlen($out) > MT2009_VOUCHER_MAX_LEN)
				return '';
		}
		return $out;
	}

	function mt2009_redeem_voucher($typed)
	{
		global $player_db, $account, $shop, $shop_db, $shop_char;
		$aid = (int)$_SESSION['id'];
		$pid = $shop_char ? (int)$shop_char['id'] : 0;
		$pdo = $player_db->pdo;
		$typed = trim($typed);
		if($typed=='')
			return ['ok' => false, 'text' => 'Niepoprawny kod.'];

		// the tries of the last minute (the shop's own table, itemshop3.voucher_tries)
		$shop_db->pdo->exec("DELETE FROM voucher_tries WHERE date < NOW() - INTERVAL 10 MINUTE");
		$sth = $shop_db->pdo->prepare("SELECT COUNT(*) FROM voucher_tries WHERE account = ? AND date > NOW() - INTERVAL 1 MINUTE");
		$sth->execute([$aid]);
		if((int)$sth->fetchColumn() >= 5)
			return ['ok' => false, 'text' => 'Za dużo prób - spróbuj ponownie za minutę.'];
		$shop_db->pdo->prepare("INSERT INTO voucher_tries (account) VALUES (?)")->execute([$aid]);

		$code = mt2009_voucher_normalize($typed);
		if($code!='')
		{
			$sth = $pdo->prepare("SELECT code_hash, vnum, count FROM common.mt2009_voucher WHERE code_hash = SHA2(CONCAT(?, ?), 256) ORDER BY reward_no");
			if(!$sth->execute([MT2009_VOUCHER_SALT, $code]))
				return ['ok' => false, 'text' => 'Kody są chwilowo niedostępne - spróbuj później.'];
			$rewards = [];
			$hash = '';
			foreach($sth->fetchAll(PDO::FETCH_ASSOC) as $row)
				if((int)$row['vnum'] > 0)
				{
					$hash = $row['code_hash'];
					$rewards[] = [(int)$row['vnum'], max(1, (int)$row['count'])];
				}
			if(count($rewards) && preg_match('/^[0-9a-f]{64}$/', $hash))
			{
				$off = $pdo->query("SELECT lValue FROM player.quest WHERE dwPID = 0 AND szName = 'm2_vouchers_off' AND szState = '' LIMIT 1");
				if($off && (int)$off->fetchColumn() != 0)
					return ['ok' => false, 'text' => 'Kody bonusowe są wyłączone na tym serwerze.'];
				$taken = $pdo->prepare("INSERT IGNORE INTO player.mt2009_voucher_used (account_id, code_hash, pid, used_at) VALUES (?, ?, ?, NOW())");
				if(!$taken->execute([$aid, $hash, $pid]))
					return ['ok' => false, 'text' => 'Kody są chwilowo niedostępne - spróbuj później.'];
				if($taken->rowCount() != 1)
					return ['ok' => false, 'text' => 'Ten kod został już wykorzystany na tym koncie.'];
				$login = $account->getAccountData('login', $aid);
				$names = $shop->getMultipleNames(array_column($rewards, 0));
				$what = [];
				$give = $pdo->prepare("INSERT INTO player.item_award (pid, login, vnum, count, given_time, why, socket0, socket1, socket2, mall) VALUES (?, ?, ?, ?, NOW(), 'Kod promocyjny', 0, 0, 0, 1)");
				foreach($rewards as $r)
				{
					$give->execute([$aid, $login, $r[0], $r[1]]);
					$what[] = (isset($names[$r[0]]) ? $names[$r[0]] : $r[0]).($r[1] > 1 ? ' x'.$r[1] : '');
				}
				return ['ok' => true, 'text' => 'Kod zrealizowany: '.implode(', ', $what).' (Magazyn ItemShop).'];
			}
		}

		// a cash voucher of the db core
		$sth = $pdo->prepare("SELECT id, max_use_count, use_count, cash FROM common.vouchers WHERE code = ?");
		$sth->execute([mb_substr($typed, 0, 64)]);
		$rows = $sth->fetchAll(PDO::FETCH_ASSOC);
		if(count($rows) != 1)
			return ['ok' => false, 'text' => 'Niepoprawny kod.'];
		$v = $rows[0];
		$use = $pdo->prepare("UPDATE common.vouchers SET use_count = use_count + 1 WHERE id = ? AND use_count < max_use_count");
		$use->execute([(int)$v['id']]);
		if($use->rowCount() != 1)
			return ['ok' => false, 'text' => 'Kod został już wykorzystany.'];
		if((int)$v['cash'] > 0)
			$account->addCoinsByID(1, (int)$v['cash'], $aid);
		return ['ok' => true, 'text' => 'Pomyślnie wykorzystano kupon!'.((int)$v['cash'] > 0 ? ' +'.number_format((int)$v['cash'], 0, '', '.').' SM' : '')];
	}
