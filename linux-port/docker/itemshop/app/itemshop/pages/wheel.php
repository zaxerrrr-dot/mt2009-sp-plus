<?php
	// MT2009_PLUS_KOLA_V1: Kolo Losu - szesc kol z kluczami i trzema poziomami (wczesniej:
	// jedno kolo, tylko poziom 1, bez kluczy - na zyczenie z 20.10.2026 caly system).
	// Aktywne kolo zmienia sie co 14 dni (albo wybiera je administrator w panelu Seban:
	// "Kolo Losu"). Losuje i liczy wylacznie serwer (kola/kola_lib.php, kola_api.php); ta
	// strona to wyglad i animacja w ES3 (stara wbudowana przegladarka klienta: bez
	// ES6, webp, flex, transform - kola/kola.js, kola/kola.css).
	//
	// Stara wbudowana przegladarka potrafi zapamietac cala strone jak statyczna - zabraniamy.
	header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
	header("Pragma: no-cache");
	require_once(__DIR__ . "/../kola/kola_lib.php");
	$isPreview = isset($_GET['preview']);
	if (!isset($_SESSION['id']) && !$isPreview) {
		header("Location: ?s=login");
		exit;
	}

	// Procent jak w zrodle: 7.5 -> "7,5", 0.25 -> "0,25".
	function kola_pct($v, $dec) {
		return rtrim(rtrim(number_format($v, $dec, ',', ''), '0'), ',');
	}

	$kolaError = '';
	$kolaData = null;
	try {
		$settings = kola_settings($sqlServ);
		$wheels = kola_wheels($sqlServ);
		$active = kola_active($sqlServ, null, $settings, $wheels);
		if ((int)$settings['enabled'] !== 1) {
			$kolaError = 'Koło Losu jest teraz wyłączone.';
		} elseif (!$active['id']) {
			$kolaError = 'Koło Losu jest chwilowo niedostępne.';
		} else {
			$wheel = $wheels[$active['id']];
			$pools = kola_pools($sqlServ, $wheel['id']);
			$items = kola_items($sqlServ);
			$look = kola_look();
			$lw = isset($look['wheels'][(string)$wheel['id']]) ? $look['wheels'][(string)$wheel['id']] : array('fields' => array(), 'bg' => '');
			if (!kola_wheel_ready($pools, $items, $wheel)) {
				$kolaError = 'Koło Losu jest chwilowo niedostępne (nagrody w przygotowaniu).';
			} else {
				if (!isset($_SESSION['id'])) {
					if (!isset($_SESSION['kola_trial'])) $_SESSION['kola_trial'] = null;
					$st = kola_trial_state($_SESSION['kola_trial'], $wheel);
					kola_normalize($st, $wheel, time());
					$_SESSION['kola_trial'] = $st;
					$state = kola_state_view($st, $wheel, 0, $settings);
				} else {
					$st = kola_load_state($sqlServ, (int)$_SESSION['acc_id'], $wheel);
					$state = kola_state_view($st, $wheel, kola_balance($sqlServ, (int)$_SESSION['acc_id']), $settings);
				}
				// Ostatni uklad pol (pokazany po wejsciu, gdy gracz juz krecil).
				$lastFields = array();
				foreach (kola_layout_decode($st['layout']) as $p => $e) $lastFields[] = kola_entry_view($e[0], $e[1], $items, $look);
				// "Mozliwe nagrody": pule kazdego poziomu; p = procent jak w zrodle (szansa
				// wpisu przy losowaniu pola swojego rodzaju), s = szansa wygrania go jednym obrotem.
				$prizeTiers = array();
				for ($t = 1; $t <= $wheel['max_tier']; $t++) {
					$nSpecial = count(kola_special_fields($t));
					$tierOut = array();
					foreach (array(1, 0) as $sp) {
						$sum = 0;
						foreach ($pools[$t][$sp] as $e) $sum += $e[2];
						$fieldsOfKind = $sp ? $nSpecial : 16 - $nSpecial;
						$list = array();
						foreach ($pools[$t][$sp] as $e) {
							$v = kola_entry_view($e[0], $e[1], $items, $look);
							$v['p'] = kola_pct($e[2] / 100, 2);
							$v['s'] = kola_pct($sum ? 100.0 * $e[2] / $sum * $fieldsOfKind / 16 : 0, 3);
							$list[] = $v;
						}
						$tierOut[] = $list;
					}
					$prizeTiers[$t] = $tierOut;
				}
				$fieldIcons = array();
				foreach ($lw['fields'] as $t => $files) {
					$fieldIcons[(int)$t] = array();
					foreach ($files as $f) $fieldIcons[(int)$t][] = 'kola/img/' . $f;
				}
				$kolaData = array(
					'wheel' => array('id' => (int)$wheel['id'], 'name' => $wheel['name'], 'maxTier' => (int)$wheel['max_tier'],
						'costs' => $wheel['costs']),
					'state' => $state,
					'fields' => $fieldIcons,
					'last' => $lastFields,
					'prizes' => $prizeTiers,
					'preview' => isset($_SESSION['id']) ? 0 : 1,
				);
			}
		}
	} catch (Exception $e) {
		error_log('kola page: ' . $e->getMessage());
		$kolaError = 'Koło Losu jest chwilowo niedostępne.';
	}
	$pv = $isPreview ? '&preview=1' : '';
	$cssV = @filemtime(__DIR__ . '/../kola/kola.css');
	$jsV = @filemtime(__DIR__ . '/../kola/kola.js');
?>
<link href="kola/kola.css?v=<?php echo $cssV; ?>" rel="stylesheet" type="text/css" />
<div id="container">
	<?php include("pages/etc.php") ?>
<?php if ($kolaError !== '' || !$kolaData) { ?>
	<div id="kolaGame" class="kola-off">
		<div class="kola-offbox">
			<h3>Koło Losu</h3>
			<p><?php echo htmlspecialchars($kolaError !== '' ? $kolaError : 'Koło Losu jest chwilowo niedostępne.'); ?></p>
			<p><a href="?s=home<?php echo $pv; ?>">&laquo; Wróć do sklepu</a></p>
		</div>
	</div>
<?php } else { ?>
	<div id="kolaGame" style="background-image:url(kola/img/<?php echo htmlspecialchars($lw['bg']); ?>)">
		<ul id="kolaStages" class="kola-stages"></ul>
		<div id="kolaWheel" class="kola-wheel kola-lvl-1">
			<div class="kola-lay kola-slices"></div>
			<div id="kolaPointer" class="kola-lay kola-pointer"></div>
			<div class="kola-lay kola-ring"></div>
			<div id="kolaItems" class="kola-items"></div>
			<div id="kolaIdle" class="kola-items"></div>
			<div id="kolaKeys" class="kola-keys"></div>
			<div id="kolaSpinner" class="kola-lay kola-spinner"></div>
			<div id="kolaBtn" class="kola-btn"><table cellpadding="0" cellspacing="0"><tr><td id="kolaBtnText"></td></tr></table></div>
		</div>
		<div id="kolaSide" class="kola-side">
			<h2 id="kolaTitle"><?php echo htmlspecialchars($wheel['name']); ?></h2>
			<?php if ($active['mode'] === 'auto') { ?>
			<p class="kola-rot">Następne koło: <?php echo date('d.m.Y', $active['until']); ?></p>
			<?php } ?>
			<div id="kolaWelcome" class="kola-welcome"></div>
			<div id="kolaBalance" class="kola-balance"></div>
			<div class="kola-last">
				<h4>Ostatnia nagroda</h4>
				<div id="kolaPrize" class="kola-prize"><span class="kola-empty">Zakręć kołem.</span></div>
			</div>
			<div id="kolaMsg" class="kola-msg"></div>
		</div>
		<a id="kolaPrices" class="kola-prices" href="javascript:void(0)">Możliwe nagrody</a>
		<a class="kola-back" href="?s=home<?php echo $pv; ?>">&laquo; Wróć do sklepu</a>
		<div id="kolaModal" class="kola-modal" style="display:none">
			<div class="kola-modal-box">
				<a id="kolaModalClose" class="kola-close" href="javascript:void(0)">&times;</a>
				<h3>Możliwe nagrody</h3>
				<div id="kolaTabs" class="kola-tabs"></div>
				<div id="kolaPools" class="kola-pools"></div>
			</div>
		</div>
		<div id="kolaDetail" class="kola-detail" style="display:none">
			<div class="kola-detail-box">
				<a id="kolaDetailClose" class="kola-close" href="javascript:void(0)">&times;</a>
				<div id="kolaDetailBody"></div>
			</div>
		</div>
	</div>
	<script type="text/javascript">
	var KOLA = <?php echo json_encode($kolaData, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT); ?>;
	</script>
	<script type="text/javascript" src="kola/kola.js?v=<?php echo $jsV; ?>"></script>
<?php } ?>
</div>
