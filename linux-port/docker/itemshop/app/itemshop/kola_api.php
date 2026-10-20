<?php
	// MT2009_PLUS_KOLA_V1: Kolo Losu - zadania strony (osobny punkt wejscia, jak dawny
	// wheel_spin.php: index.php owija kazda strone w <html>, co zepsuloby JSON).
	//   POST a=spin  t=<token>  - jeden obrot (koszt, nagroda, klucze - kola/kola_lib.php)
	//   POST a=exit             - "Opusc ten poziom"
	//   POST a=state            - stan konta (po uplywie czasu poziomu, po zmianie w grze)
	// Bez logowania (?preview=1) to samo na niby: stan w sesji, bez SM i bez nagrod.
	session_start();
	require("../user/config.php");
	require_once(__DIR__ . "/kola/kola_lib.php");
	header('Content-Type: application/json; charset=utf-8');
	header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
	header('Pragma: no-cache');

	function kola_out($data) {
		echo json_encode($data);
		exit;
	}

	if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
		kola_out(array('ok' => false, 'error' => 'Niepoprawne zadanie.'));
	}
	$action = isset($_POST['a']) ? (string)$_POST['a'] : '';
	$preview = isset($_POST['preview']) && $_POST['preview'] === '1';
	$logged = isset($_SESSION['id']) && isset($_SESSION['acc_id']);

	try {
		if (!$logged) {
			if (!$preview) kola_out(array('ok' => false, 'error' => 'Musisz być zalogowany.', 'login' => true));
			if (!isset($_SESSION['kola_trial'])) $_SESSION['kola_trial'] = null;
			if ($action === 'spin') kola_out(kola_trial_spin($sqlServ, $_SESSION['kola_trial']));
			if ($action === 'exit') kola_out(kola_trial_exit($sqlServ, $_SESSION['kola_trial']));
			kola_out(array('ok' => false, 'error' => 'Niepoprawne zadanie.'));
		}
		$accId = (int)$_SESSION['acc_id'];
		$login = (string)$_SESSION['id'];
		if ($action === 'spin') {
			$token = isset($_POST['t']) ? preg_replace('/[^0-9a-f]/', '', (string)$_POST['t']) : '';
			kola_out(kola_spin($sqlServ, $accId, $login, $token, 'www'));
		}
		if ($action === 'exit') {
			kola_out(kola_exit($sqlServ, $accId));
		}
		if ($action === 'state') {
			$settings = kola_settings($sqlServ);
			$wheels = kola_wheels($sqlServ);
			$active = kola_active($sqlServ, null, $settings, $wheels);
			if (!$active['id']) kola_out(array('ok' => false, 'error' => 'Koło Losu jest chwilowo niedostępne.'));
			$wheel = $wheels[$active['id']];
			$st = kola_load_state($sqlServ, $accId, $wheel);
			// Inne kolo niz na stronie (rotacja albo panel) - strona przeladowuje sie cala.
			kola_out(array('ok' => true, 'state' => kola_state_view($st, $wheel, kola_balance($sqlServ, $accId), $settings)));
		}
	} catch (Exception $e) {
		error_log('kola_api: ' . $e->getMessage());
		kola_out(array('ok' => false, 'error' => 'Błąd serwera. Spróbuj ponownie.'));
	}
	kola_out(array('ok' => false, 'error' => 'Niepoprawne zadanie.'));
?>
