// MT2009_PLUS_KOLA_V1: Kolo Losu - wyglad i animacja (ES3: stara wbudowana przegladarka
// klienta, IE7-11 - bez let/const/=>, Promise, classList, dataset, addEventListener,
// JSON tylko gdy jest). Liczby animacji 1:1 z oryginalu: 1000 ms do pierwszego kroku,
// 100 ms na krok, ostatnie 10 krokow wolniej (+900-u*90 ms), 32 kroki + pole wygranej,
// nagroda pokazana 1500 ms po zatrzymaniu (+1700 ms z kluczem), 3000 ms pozniej
// powrot do animacji spoczynku. Losuje wylacznie serwer (kola_api.php).
(function () {
	var D = window.KOLA;
	if (!D) return;

	// pozycje pol (wzgledem .kola-items) i kluczy (wzgledem .kola-keys) z oryginalu
	var U = [[-22.5, 145.5], [-9.71176, 209.79082], [26.70606, 264.29394], [81.20918, 300.71176], [145.5, 313.5],
		[209.79082, 300.71176], [264.29394, 264.29394], [300.71176, 209.79082], [313.5, 145.5], [300.71176, 81.20918],
		[264.29394, 26.70606], [209.79082, -9.71176], [145.5, -22.5], [81.20918, -9.71176], [26.70606, 26.70606],
		[-9.71176, 81.20918]];
	var K = [[-22.5, 195.5], [-5.90574, 278.92499], [41.35072, 349.64928], [112.07501, 396.90574], [195.5, 413.5],
		[278.92499, 396.90574], [349.64928, 349.64928], [396.90574, 278.92499], [413.5, 195.5], [396.90574, 112.07501],
		[349.64928, 41.35072], [278.92499, -5.90574], [195.5, -22.5], [112.07501, -5.90574], [41.35072, 41.35072],
		[-5.90574, 112.07501]];
	var KEY_FIELDS = [3, 7, 11, 15];
	var SPECIAL = { 1: [1], 2: [1, 9], 3: [1, 7, 11] };
	var COIN = '<img class="kola-coin" src="kola/img/coin.png" alt="" />';

	var st = D.state;           // stan z serwera
	var deadline = 0;           // koniec czasu poziomu (zegar przegladarki)
	var busy = false;           // obrot w toku (od klikniecia do pokazania nagrody)
	var playing = false;        // pola nagrod widoczne (do 3 s po nagrodzie)
	var idleGen = 0;            // pokolenie animacji spoczynku
	var spinGen = 0;
	var syncing = false;

	function $(id) { return document.getElementById(id); }
	function now() { return new Date().getTime(); }
	function esc(s) {
		return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
	}
	function has(a, v) { for (var i = 0; i < a.length; i++) { if (a[i] === v) return true; } return false; }
	function pad(n) { return n < 10 ? '0' + n : '' + n; }
	function hms(s) { return pad(Math.floor(s / 3600)) + ':' + pad(Math.floor((s % 3600) / 60)) + ':' + pad(s % 60); }
	function num(el, prop) { var v = parseFloat(el.style[prop]); return isNaN(v) ? 0 : v; }

	// --- animacje: jeden zegar, kolejki per element (jak lancuchy Promise oryginalu) ---
	var EASE_P = function (e) { return 0.5 - Math.cos(e * Math.PI) / 2; };
	var EASE_M = function (e) { return Math.sqrt(1 - Math.pow(e - 1, 2)); };
	var EASE_H = function (e) { return e; };
	var tweens = [];
	function setOpacity(el, v) {
		el.style.opacity = String(v);
		el.style.filter = v >= 1 ? '' : 'alpha(opacity=' + Math.round(v * 100) + ')';
	}
	function applyTw(tw, p) {
		var k, a, v;
		for (k in tw.props) {
			if (!tw.props.hasOwnProperty(k)) continue;
			a = tw.props[k];
			v = a[0] + (a[1] - a[0]) * p;
			if (k === 'opacity') setOpacity(tw.el, v);
			else tw.el.style[k] = v.toFixed(3) + 'px';
		}
	}
	function tween(el, props, dur, ease, done) {
		var tw = { el: el, props: props, d: dur, ease: ease, s: now(), done: done };
		tweens.push(tw);
		applyTw(tw, 0);
		return tw;
	}
	// kolejka: krok startuje po skonczeniu poprzedniego tego samego elementu;
	// fn(next) dostaje funkcje "gotowe".
	function queue(el, fn) {
		if (!el.kq) el.kq = [];
		el.kq.push(fn);
		if (el.kq.length === 1) runQueue(el);
	}
	function runQueue(el) {
		if (!el.kq || !el.kq.length) return;
		var fn = el.kq[0];
		fn(function () { el.kq.shift(); runQueue(el); });
	}
	function frame() {
		var t = now(), i, tw, p;
		for (i = 0; i < tweens.length; i++) {
			tw = tweens[i];
			p = tw.d <= 0 ? 1 : Math.min(1, (t - tw.s) / tw.d);
			applyTw(tw, tw.ease(p));
			if (p >= 1) {
				tweens.splice(i, 1);
				i--;
				if (tw.done) tw.done();
			}
		}
	}
	setInterval(frame, 16);

	// --- XHR (bez fetch/Promise) ---
	function post(params, ok, fail) {
		var xhr = null;
		try { xhr = new XMLHttpRequest(); } catch (e) {
			try { xhr = new ActiveXObject('Msxml2.XMLHTTP'); } catch (e2) {
				try { xhr = new ActiveXObject('Microsoft.XMLHTTP'); } catch (e3) { fail(); return; }
			}
		}
		var body = [], k;
		for (k in params) { if (params.hasOwnProperty(k)) body.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k])); }
		if (D.preview) body.push('preview=1');
		xhr.onreadystatechange = function () {
			if (xhr.readyState !== 4) return;
			if (xhr.status < 200 || xhr.status >= 300) { fail(); return; }
			var data = null;
			try { data = window.JSON ? JSON.parse(xhr.responseText) : eval('(' + xhr.responseText + ')'); } catch (e) { data = null; }
			if (!data) { fail(); return; }
			ok(data);
		};
		xhr.open('POST', 'kola_api.php?_=' + now(), true);
		xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
		xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
		xhr.send(body.join('&'));
	}

	// --- rysowanie ---
	function wheelClass() {
		$('kolaWheel').className = 'kola-wheel kola-lvl-' + st.tier + (playing ? ' kola-playing' : '') +
			(st.tier >= st.maxTier ? ' kola-maxtier' : '');
	}

	function renderStages() {
		var html = [], e, r, s, cls, slot;
		for (e = st.maxTier; e >= 1; e--) {
			cls = 'kola-lvl kola-star-' + e;
			if (e === st.tier) cls += ' kola-current';
			html.push('<li class="' + cls + '">' + (e === st.tier ? '<i class="kola-arrow-l"></i>' : '') + '<span>' + e + '</span>' +
				(e === st.tier ? '<i class="kola-arrow-r"></i>' : '') + (e > st.tier ? '<i class="kola-lock"></i>' : '') + '</li>');
			if (e > 1) {
				r = e - 1;
				for (s = 4; s >= 1; s--) {
					slot = '';
					if (st.tier > r || (st.tier === r && s <= st.keys)) slot = (r === 1 ? 'kola-f1' : 'kola-f2');
					else if (st.tier === r && s === st.keys + 1) slot = 'kola-cur';
					html.push('<li class="kola-stg"><span class="' + slot + '"' + (slot === 'kola-cur' ? ' id="kolaCurSlot"' : '') + '></span></li>');
				}
			}
		}
		var ul = $('kolaStages');
		ul.innerHTML = html.join('');
		ul.style.top = Math.max(0, Math.round((475 - ul.offsetHeight) / 2)) + 'px';
	}

	function renderWelcome() {
		var cost = st.cost;
		var h = '<h3>Witaj na poziomie ' + st.tier + '</h3><p>Zakręć kołem za jedyne ' + COIN + ' ' + cost + '!</p>';
		if (st.tier > 1) {
			h += '<div class="kola-timer"><h4>Powrót na poziom <b>1</b></h4><span class="kola-time" id="kolaTime">' +
				hms(Math.max(0, Math.ceil((deadline - now()) / 1000))) + '</span>' +
				'<a class="kola-exit" id="kolaExit" href="javascript:void(0)">Opuść ten poziom</a></div>';
		}
		$('kolaWelcome').innerHTML = h;
		var ex = $('kolaExit');
		if (ex) ex.onclick = exitTier;
	}

	function renderBalance() {
		if (D.preview) {
			$('kolaBalance').innerHTML = 'Podgląd: obroty na próbę, bez Smoczych Monet i bez nagród.';
			return;
		}
		$('kolaBalance').innerHTML = 'Masz ' + COIN + ' <b>' + st.balance + '</b> SM';
		var hc = $('headerCashValue');
		if (hc) hc.innerHTML = String(st.balance);
	}

	function renderBtn() {
		var b = $('kolaBtn');
		if (busy) {
			b.className = 'kola-btn kola-running';
			$('kolaBtnText').innerHTML = 'KRĘCI SIĘ...';
		} else {
			b.className = 'kola-btn';
			$('kolaBtnText').innerHTML = 'ZAKRĘĆ<br />TERAZ!<br />(' + st.cost + '&nbsp;' + COIN + ')';
		}
	}

	function renderItems(fields) {
		var box = $('kolaItems'), i, f, d, h = [];
		for (i = 1; i <= 16; i++) {
			f = fields[i - 1];
			h.push('<div class="kola-reward" id="kolaR' + i + '" style="top:' + U[i - 1][0] + 'px;left:' + U[i - 1][1] +
				'px;width:45px;height:45px"><img src="' + esc(f.i) + '" alt="" title="' + esc((f.c > 1 ? f.c + '× ' : '') + f.n) + '" />' +
				(f.c > 1 && !f.g ? '<b>' + f.c + '</b>' : '') + '</div>');
		}
		box.innerHTML = h.join('');
	}

	function renderKeys() {
		var h = [], i, p;
		for (i = 0; i < KEY_FIELDS.length; i++) {
			p = KEY_FIELDS[i];
			h.push('<i class="kola-key" id="kolaK' + p + '" style="top:' + K[p - 1][0] + 'px;left:' + K[p - 1][1] +
				'px;width:56px;height:56px"><img src="kola/img/key.png" alt="" /></i>');
		}
		$('kolaKeys').innerHTML = h.join('');
	}

	function renderPrize(f) {
		$('kolaPrize').innerHTML = '<img src="' + esc(f.i) + '" alt="" /><span>' + (f.c > 1 ? f.c + '× ' : '') + esc(f.n) +
			'</span><small>' + (D.preview ? 'Podgląd - bez nagrody.' : 'W magazynie ItemShopu w grze.') + '</small>';
	}

	function msg(t) { $('kolaMsg').innerHTML = t ? esc(t) : ''; }

	function applyState(s) {
		if (!s) return;
		if (s.wheel && s.wheel !== D.wheel.id) { window.location.reload(); return; }
		st = s;
		deadline = st.tier > 1 ? now() + st.left * 1000 : 0;
	}

	function renderAll() {
		wheelClass();
		renderStages();
		renderWelcome();
		renderBalance();
		renderBtn();
	}

	// --- spoczynek: ikony pol wszystkich poziomow wyskakuja po kolei (oryginal: ea()) ---
	function buildIdle() {
		var box = $('kolaIdle'), h = [], t, p, list;
		for (t = 1; t <= st.maxTier; t++) {
			list = D.fields[t] || D.fields[String(t)] || [];
			for (p = 1; p <= 16; p++) {
				if (!list[p - 1]) continue;
				h.push('<img class="kola-idle-ikon" id="kolaI' + t + '_' + p + '" src="' + esc(list[p - 1]) + '" alt="" />');
			}
		}
		box.innerHTML = h.join('');
	}
	function stopIdle() {
		idleGen++;
		var box = $('kolaIdle'), imgs = box.getElementsByTagName('img'), i;
		for (i = 0; i < imgs.length; i++) imgs[i].style.display = 'none';
	}
	function startIdle() {
		idleGen++;
		var gen = idleGen;
		var imgs = $('kolaIdle').getElementsByTagName('img'), i;
		for (i = 0; i < imgs.length; i++) { imgs[i].style.display = 'none'; imgs[i].kq = null; }
		var step = function (r, l) {
			if (gen !== idleGen) return;
			if (l > 16) { r += 1; l = 1; }
			if (r > st.maxTier) r = 1;
			var img = $('kolaI' + r + '_' + l);
			if (img) {
				var top = U[l - 1][0], left = U[l - 1][1];
				img.style.width = '0px'; img.style.height = '0px';
				img.style.top = (top + 20) + 'px'; img.style.left = (left + 20) + 'px';
				img.style.display = 'block';
				tween(img, { width: [0, 45], height: [0, 45], top: [top + 20, top], left: [left + 20, left] }, 400, EASE_P, function () {
					setTimeout(function () {
						if (gen !== idleGen) return;
						tween(img, { width: [45, 0], height: [45, 0], top: [top, top + 20], left: [left, left + 20] }, 400, EASE_P, function () {
							if (gen === idleGen) img.style.display = 'none';
						});
					}, 800);
				});
			}
			setTimeout(function () { step(r, l + 1); }, 200);
		};
		step(1, 1);
	}

	function setFrame(c) {
		var p = c <= 0 ? '0 0' : '-' + ((c - 1) * 436) + 'px 0';
		$('kolaSpinner').style.backgroundPosition = p;
		$('kolaPointer').style.backgroundPosition = p;
	}

	// pole mija wskazowke: podskok 10 px (100 ms w gore, 400 ms w dol)
	function bump(c) {
		var el = $('kolaR' + c);
		if (!el) return;
		queue(el, function (next) {
			var t0 = num(el, 'top');
			tween(el, { top: [t0, t0 - 10] }, 100, EASE_P, function () {
				tween(el, { top: [t0 - 10, t0] }, 400, EASE_P, next);
			});
		});
	}

	// wygrana: pole rosnie i "pulsuje" (+60, -40, +30, -20, +10 px)
	function pop(c) {
		var el = $('kolaR' + c), seq = [[60, -30, 200], [-40, 20, 300], [30, -15, 300], [-20, 10, 400], [10, -5, 400]], i;
		if (!el) return;
		el.style.zIndex = '15';
		for (i = 0; i < seq.length; i++) {
			(function (d) {
				queue(el, function (next) {
					var w = num(el, 'width'), h = num(el, 'height'), t = num(el, 'top'), l = num(el, 'left');
					tween(el, { width: [w, w + d[0]], height: [h, h + d[0]], top: [t, t + d[1]], left: [l, l + d[1]] }, d[2], EASE_P, next);
				});
			})(seq[i]);
		}
	}

	function offsetIn(el, root) {
		var x = 0, y = 0;
		while (el && el !== root) { x += el.offsetLeft; y += el.offsetTop; el = el.offsetParent; }
		return [x, y];
	}

	// klucz leci z pola na drabinke (800 + 400 + 300 ms)
	function flyKey(c) {
		var key = $('kolaK' + c), slot = $('kolaCurSlot'), game = $('kolaGame');
		if (!key || !slot) return;
		var ko = offsetIn($('kolaKeys'), game), so = offsetIn(slot, game);
		var tx = so[0] - ko[0] + (slot.offsetWidth - 56) / 2, ty = so[1] - ko[1] + (slot.offsetHeight - 56) / 2;
		var l0 = num(key, 'left'), t0 = num(key, 'top');
		key.style.zIndex = '6';
		queue(key, function (next) { tween(key, { left: [l0, l0 - 28], top: [t0, t0 - 28] }, 800, EASE_M, next); });
		queue(key, function (next) { tween(key, { left: [l0 - 28, tx], top: [t0 - 28, ty] }, 400, EASE_M, next); });
		queue(key, function (next) {
			tween(key, { opacity: [1, 0], width: [56, 19], height: [56, 14.5] }, 300, EASE_H, function () {
				slot.className = st.tier === 1 ? 'kola-f1' : 'kola-f2';
				key.style.display = 'none';
				next();
			});
		});
	}

	function spin() {
		if (busy) return;
		busy = true;
		spinGen++;
		var gen = spinGen, t0 = now();
		msg('');
		stopIdle();
		renderBtn();
		post({ a: 'spin', t: st.token || '' }, function (res) {
			if (gen !== spinGen) return;
			if (!res.ok) {
				busy = false;
				if (res.login) { window.location.href = '?s=login'; return; }
				if (res.state) applyState(res.state);
				renderAll();
				msg(res.error || 'Nie udało się zakręcić kołem.');
				startIdle();
				return;
			}
			var tierBefore = res.tierBefore, keysBefore = res.keysBefore;
			// do konca animacji pokazujemy stan sprzed obrotu (poziom/klucze), saldo juz po
			var after = res.state;
			st.balance = after.balance;
			st.token = after.token;
			renderBalance();
			playing = true;
			renderItems(res.fields);
			renderKeys();
			wheelClass();
			var a = 32 + res.position;
			var step = function (l) {
				if (gen !== spinGen) return;
				var c = l % 16;
				if (c === 0) c = 16;
				setFrame(c);
				var u = a - l, n = 100;
				if (u <= 10) n += 900 - u * 90;
				if (l === a) {
					pop(c);
					var o = 1500;
					if (res.key) { flyKey(c); o += 1700; }
					setTimeout(function () { finish(res, gen); }, o);
					return;
				}
				bump(c);
				setTimeout(function () { step(l + 1); }, n);
			};
			setTimeout(function () { step(1); }, Math.max(0, 1000 - (now() - t0)));
		}, function () {
			busy = false;
			renderBtn();
			msg('Błąd połączenia. Spróbuj ponownie.');
			startIdle();
		});
	}

	function finish(res, gen) {
		if (gen !== spinGen) return;
		renderPrize(res.prize);
		var tierChanged = res.state.tier !== st.tier;
		applyState(res.state);
		if (res.key || tierChanged) renderStages();
		busy = false;
		wheelClass();
		renderWelcome();
		renderBalance();
		renderBtn();
		setTimeout(function () {
			if (gen !== spinGen || busy) return;
			playing = false;
			setFrame(0);
			wheelClass();
			renderKeys();
			startIdle();
		}, 3000);
	}

	function exitTier() {
		if (busy || st.tier <= 1) return;
		busy = true;
		post({ a: 'exit' }, function (res) {
			busy = false;
			if (res.ok) {
				applyState(res.state);
				spinGen++;
				playing = false;
				setFrame(0);
				renderAll();
				renderKeys();
				startIdle();
			} else msg(res.error || '');
		}, function () { busy = false; msg('Błąd połączenia. Spróbuj ponownie.'); });
	}

	function sync() {
		if (syncing || busy || D.preview) return;
		syncing = true;
		post({ a: 'state' }, function (res) {
			syncing = false;
			if (res.ok && !busy) { applyState(res.state); renderAll(); }
		}, function () { syncing = false; });
	}

	// zegar poziomu
	setInterval(function () {
		if (st.tier <= 1 || !deadline) return;
		var left = Math.max(0, Math.ceil((deadline - now()) / 1000));
		var el = $('kolaTime');
		if (el) el.innerHTML = hms(left);
		if (left <= 0 && !busy) {
			if (D.preview) {
				st.tier = 1; st.keys = 0; st.cost = D.wheel.costs[1] || D.wheel.costs['1']; deadline = 0;
				renderAll();
			} else sync();
		}
	}, 500);

	// --- "Mozliwe nagrody" ---
	var curTab = 1;
	function percentMain(t) { return { 1: '6,25', 2: '12,5', 3: '18,75' }[t]; }
	function card(t, sp, i, e) {
		return '<a class="kola-card" href="javascript:void(0)" id="kolaC' + t + '_' + sp + '_' + i + '"><span>' +
			(e.c > 1 ? e.c + '× ' : '') + esc(e.n) + '</span><img src="' + esc(e.i) + '" alt="" /><b>' + e.p + '%</b></a>';
	}
	function renderPools(t) {
		curTab = t;
		var tabs = [], i, x;
		for (x = 1; x <= D.wheel.maxTier; x++) {
			tabs.push('<a href="javascript:void(0)" id="kolaTab' + x + '"' + (x === t ? ' class="kola-sel"' : '') + '>poziom ' + x + '</a>');
		}
		$('kolaTabs').innerHTML = tabs.join('');
		for (x = 1; x <= D.wheel.maxTier; x++) {
			(function (n) { $('kolaTab' + n).onclick = function () { renderPools(n); return false; }; })(x);
		}
		var pools = D.prizes[t] || D.prizes[String(t)];
		var h = '<p class="kola-how">Koło ma 16 pól i zatrzymuje się na każdym z taką samą szansą: 1/16. Przed każdym ' +
			'zakręceniem pola są wypełniane od nowa, osobno dla każdego pola: pola głównych nagród z puli głównych nagród, ' +
			'pozostałe z puli standardowej. Procent na karcie to szansa, że przedmiot trafi na pole swojego rodzaju. ' +
			'Szansa na główną nagrodę na poziomie ' + t + ': <b>' + percentMain(t) + '%</b>.' +
			(t < D.wheel.maxTier ? ' Pola 3, 7, 11 i 15 dają klucz - 4 klucze otwierają bramę na poziom ' + (t + 1) + '.' : '') + '</p>';
		h += '<div class="kola-group">Główne nagrody</div>';
		for (i = 0; i < pools[0].length; i++) h += card(t, 0, i, pools[0][i]);
		h += '<div class="kola-clear"></div><div class="kola-group">Nagrody standardowe</div>';
		for (i = 0; i < pools[1].length; i++) h += card(t, 1, i, pools[1][i]);
		h += '<div class="kola-clear"></div>';
		$('kolaPools').innerHTML = h;
		$('kolaPools').scrollTop = 0;
		for (x = 0; x < 2; x++) {
			for (i = 0; i < pools[x].length; i++) {
				(function (sp, n) { $('kolaC' + t + '_' + sp + '_' + n).onclick = function () { detail(pools[sp][n]); return false; }; })(x, i);
			}
		}
	}
	function detail(e) {
		var d = esc(e.d || '').replace(/\n/g, '<br />');
		$('kolaDetailBody').innerHTML = '<img src="' + esc(e.i) + '" alt="" /><h3>' + (e.c > 1 ? e.c + '× ' : '') + esc(e.n) + '</h3>' +
			'<p>Prawdopodobieństwo: <b>' + e.p + '%</b><br />Szansa na jeden obrót: ' + e.s + '%</p>' + (d ? '<p>' + d + '</p>' : '') +
			'<div class="kola-clear"></div>';
		$('kolaDetail').style.display = 'block';
	}
	$('kolaPrices').onclick = function () { renderPools(Math.min(st.tier, D.wheel.maxTier)); $('kolaModal').style.display = 'block'; return false; };
	$('kolaModalClose').onclick = function () { $('kolaModal').style.display = 'none'; return false; };
	$('kolaDetailClose').onclick = function () { $('kolaDetail').style.display = 'none'; return false; };
	$('kolaBtn').onclick = function () { spin(); return false; };

	// start
	applyState(st);
	renderAll();
	renderKeys();
	buildIdle();
	if (D.last && D.last.length === 16) renderItems(D.last);
	startIdle();
})();
