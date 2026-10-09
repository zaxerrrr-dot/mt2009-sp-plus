// Podgląd rynku (MT2009_PLUS_MARKET_PREVIEW_V1): the page's script; data in #mk-data.
(function(){
'use strict';
var D = JSON.parse(document.getElementById('mk-data').textContent);
var T = D.texts;
var $ = function(id){ return document.getElementById(id); };
function esc(s){ return String(s == null ? '' : s).replace(/[&<>"']/g, function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
function fmt(key, args){ var s = T[key] || key; for (var k in (args||{})) s = s.split('{'+k+'}').join(args[k]); return s; }
function num(n){ n = Math.round(Number(n) || 0); return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }
var PLACEHOLDER = '<span class="ph" title="' + esc(T.icon_none) + '">?</span>';
// An icon that does not load is the same grey "?", never a broken image.
function iconFailed(ev){
  var t = ev.target;
  if (!t || t.tagName !== 'IMG' || !t.closest || !t.closest('.mk-icon')) return;
  var box = t.parentNode; t.remove(); if (box && !box.querySelector('.ph')) box.insertAdjacentHTML('beforeend', PLACEHOLDER);
}
document.addEventListener('error', iconFailed, true);
function bonusesWord(n){
  if (n === 1) return T.bonuses_1;
  var t = n % 10, h = n % 100;
  if (t >= 2 && t <= 4 && (h < 12 || h > 14)) return fmt('bonuses_few', {n: n});
  return fmt('bonuses_n', {n: n});
}

// ---- state <-> URL --------------------------------------------------------
var FIELDS = ['q','cat','sub','pmin','pmax','unit','lmin','lmax','rmin','rmax','cls','nbmin','maxonly',
  'nmaxmin','avgmin','avgmax','sklmin','sklmax','ks','emp','seller','sname','shop','vnum','var','deals','dmin',
  'hideslip','expired','rare','sort','page','per','b1','b1v','b2','b2v','b3','b3v'];
var DEFAULTS = D.defaults;
var state = {};
function readUrl(){
  var p = new URLSearchParams(location.search); state = {};
  FIELDS.forEach(function(k){ var v = p.get(k); state[k] = (v === null ? DEFAULTS[k] : v); });
}
function writeUrl(push){
  var p = new URLSearchParams();
  FIELDS.forEach(function(k){ var v = state[k]; if (v !== undefined && v !== null && String(v) !== String(DEFAULTS[k])) p.set(k, v); });
  var url = location.pathname + (p.toString() ? '?' + p.toString() : '');
  if (push) history.pushState(null, '', url); else history.replaceState(null, '', url);
}

// ---- the form ---------------------------------------------------------------
var TEXT_INPUTS = ['q','pmin','pmax','lmin','lmax','avgmin','avgmax','sklmin','sklmax','sname','dmin'];
var SELECTS = ['sort','rmin','rmax','cls','nbmin','nmaxmin','ks','emp','seller'];
var CHECKS = ['unit','maxonly','deals','hideslip','expired','rare'];
function parsePrice(s){
  s = String(s || '').trim().toLowerCase().replace(/ /g, ' ').replace(/\s*yang$/, '');
  if (!s) return null;
  var m = s.replace(/ /g, '').match(/^(\d+)(?:[.,](\d+))?(k{1,4})$/);
  if (m) { var sc = Math.pow(1000, m[3].length), v = parseInt(m[1], 10) * sc;
    if (m[2]) v += Math.floor(parseInt(m[2], 10) * sc / Math.pow(10, m[2].length)); return v; }
  if (/^\d+$/.test(s)) return parseInt(s, 10);
  if (/^\d{1,3}([ .,_]\d{3})+$/.test(s)) return parseInt(s.replace(/[ .,_]/g, ''), 10);
  return NaN;
}
function validInt(s, lo, hi){ s = String(s || '').trim(); if (!s) return true; if (!/^\d{1,9}$/.test(s)) return false;
  var n = parseInt(s, 10); return n >= lo && n <= hi; }
var RULES = {pmin: function(v){ var p = parsePrice(v); return p === null || !isNaN(p); }, pmax: null,
  lmin: function(v){ return validInt(v, 0, 255); }, lmax: null, avgmin: function(v){ return validInt(v, 0, 200); },
  avgmax: null, sklmin: null, sklmax: null, dmin: function(v){ return validInt(v, 0, 100); }};
RULES.pmax = RULES.pmin; RULES.lmax = RULES.lmin; RULES.avgmax = RULES.sklmin = RULES.sklmax = RULES.avgmin;
function validate(){
  var ok = true;
  Object.keys(RULES).forEach(function(k){
    var el = $('mk-' + k); if (!el) return;
    var good = RULES[k](el.value); el.classList.toggle('mk-bad', !good); if (!good) ok = false;
  });
  return ok;
}
function toForm(){
  TEXT_INPUTS.forEach(function(k){ var el = $('mk-' + k); if (el) el.value = state[k] || ''; });
  SELECTS.forEach(function(k){ var el = $('mk-' + k); if (el) el.value = state[k] || (k === 'sort' ? 'deals' : ''); });
  CHECKS.forEach(function(k){ var el = $('mk-' + k); if (el) el.checked = String(state[k]) === '1'; });
  drawBonusRows();
  validate();
}
function fromForm(){
  TEXT_INPUTS.forEach(function(k){ var el = $('mk-' + k); var v = el ? el.value.trim() : '';
    state[k] = (RULES[k] && !RULES[k](v)) ? '' : v; });
  SELECTS.forEach(function(k){ var el = $('mk-' + k); if (el) state[k] = el.value; });
  CHECKS.forEach(function(k){ var el = $('mk-' + k); if (el) state[k] = el.checked ? '1' : '0'; });
  for (var i = 1; i <= 3; i++) {
    var b = $('mk-b' + i), bv = $('mk-b' + i + 'v');
    state['b' + i] = b ? b.value : ''; state['b' + i + 'v'] = (bv && validInt(bv.value, 0, 100000)) ? bv.value.trim() : '';
  }
}
var bonusRows = 1;
function drawBonusRows(){
  var box = $('mk-bonuses'); box.innerHTML = '';
  for (var i = 3; i >= 1; i--) if (state['b' + i]) { bonusRows = Math.max(bonusRows, i); break; }
  for (var i = 1; i <= bonusRows; i++) {
    var row = document.createElement('div'); row.className = 'mk-bonusrow';
    var opts = '<option value="">' + esc(T.f_bonus_none) + '</option>' + D.bonuses.map(function(b){
      return '<option value="' + b.p + '">' + esc(b.t) + '</option>'; }).join('');
    row.innerHTML = '<select id="mk-b' + i + '">' + opts + '</select><input id="mk-b' + i +
      'v" inputmode="numeric" placeholder="' + esc(T.f_bonus_min) + '" aria-label="' + esc(T.f_bonus_min) + '">';
    box.appendChild(row);
    $('mk-b' + i).value = state['b' + i] || ''; $('mk-b' + i + 'v').value = state['b' + i + 'v'] || '';
  }
  $('mk-bonus-add').style.display = bonusRows >= 3 ? 'none' : '';
}
function weaponFilters(){
  var weapons = state.cat === 'weapons', gear = ['weapons','armour','shields_helmets','jewellery','boots',''].indexOf(state.cat) >= 0;
  document.querySelectorAll('.mk-weapon-only').forEach(function(el){ el.style.display = weapons ? '' : 'none'; });
  document.querySelectorAll('.mk-gear-only').forEach(function(el){ el.style.display = gear ? '' : 'none'; });
}

// ---- loading --------------------------------------------------------------
var timer = null, seq = 0, last = null, polling = null;
function schedule(){ clearTimeout(timer); timer = setTimeout(function(){ apply(false); }, 800); }
function apply(push){ if (!validate()) return; fromForm(); state.page = '1'; load(push); }
function query(extra){
  var p = new URLSearchParams();
  FIELDS.forEach(function(k){ var v = state[k]; if (v !== undefined && v !== null && v !== '') p.set(k, v); });
  if (extra) for (var k in extra) p.set(k, extra[k]);
  return p.toString();
}
function load(push, extra){
  writeUrl(push); weaponFilters(); drawChips();
  var my = ++seq;
  $('mk-count').innerHTML = '<span class="mk-spin"></span>';
  fetch(D.api + '?' + query(extra), {credentials: 'same-origin', headers: {'Accept': 'application/json'}})
    .then(function(r){
      if (r.status === 429) throw {kind: 'fast'};
      if (r.status === 401) throw {kind: 'login'};
      var ct = r.headers.get('content-type') || '';
      if (!r.ok || ct.indexOf('json') < 0) throw {kind: 'error'};
      return r.json();
    })
    .then(function(data){ if (my !== seq) return; last = data; draw(data);
      if (data.building || !data.generated_at) { clearTimeout(polling); polling = setTimeout(function(){ load(false); }, 2500); } })
    .catch(function(e){ if (my !== seq) return; drawError(e && e.kind); });
}
function drawError(kind){
  var msg = kind === 'fast' ? T.too_fast : kind === 'login' ? T.login : T.load_error;
  $('mk-count').textContent = '';
  $('mk-list').innerHTML = '<div class="mk-card mk-state"><b>' + esc(msg) + '</b><button type="button" class="mk-btn" id="mk-retry">' +
    esc(T.retry) + '</button></div>';
  $('mk-pager').innerHTML = '';
  $('mk-retry').onclick = function(){ load(false); };
  if (kind === 'fast') setTimeout(function(){ load(false); }, 1500);
}

// ---- drawing ----------------------------------------------------------------
function drawCats(counts){
  var ul = $('mk-cats'), html = '';
  var all = counts ? counts.all : 0;
  html += '<li><div class="mk-cat' + (!state.cat ? ' on' : '') + '" data-cat="" data-sub=""><span>' + esc(T.cat_all) +
    '</span><span class="n">' + num(all) + '</span></div></li>';
  D.categories.forEach(function(c){
    var cc = counts && counts.cats[c.key] ? counts.cats[c.key] : {n: 0, subs: {}};
    var on = state.cat === c.key && !state.sub;
    html += '<li><div class="mk-cat' + (on ? ' on' : '') + (cc.n ? '' : ' empty') + '" data-cat="' + c.key + '" data-sub=""><span>' +
      esc(c.name) + (c.subs.length ? ' ▾' : '') + '</span><span class="n">' + num(cc.n) + '</span></div>';
    if (c.subs.length) {
      html += '<ul class="mk-subs' + (state.cat === c.key ? ' open' : '') + '">';
      c.subs.forEach(function(s){
        var n = cc.subs[s.key] || 0;
        html += '<li><div class="mk-cat' + (state.cat === c.key && state.sub === s.key ? ' on' : '') + (n ? '' : ' empty') +
          '" data-cat="' + c.key + '" data-sub="' + s.key + '"><span>' + esc(s.name) + '</span><span class="n">' + num(n) + '</span></div></li>';
      });
      html += '</ul>';
    }
    html += '</li>';
  });
  ul.innerHTML = html;
}
function drawChips(){
  var box = $('mk-chips'), html = '';
  if (state.shop) html += '<span class="mk-chip">' + esc(fmt('only_shop', {name: (last && last.shop ? last.shop.label : '#' + state.shop)})) +
    '<button type="button" class="mk-link" data-chip="shop">' + esc(T.remove) + '</button></span>';
  if (state.vnum) html += '<span class="mk-chip">' + esc(fmt('only_item', {name: (last && last.item ? last.item : '#' + state.vnum)})) +
    '<button type="button" class="mk-link" data-chip="vnum">' + esc(T.remove) + '</button></span>';
  box.innerHTML = html;
}
function classBadges(o){
  if (o.cls_all) return '';
  var names = o.classes.map(function(c){ return D.classes[c]; });
  return '<span class="mk-tag">' + esc(names.join(', ')) + '</span>';
}
// A weapon's average and skill damage count as bonuses; soul stones in the
// sockets are no bonus and get a label of their own.
function bonusCount(o){ return o.bonuses.length + (o.avg ? 1 : 0) + (o.skl ? 1 : 0); }
function bonusList(o){
  var html = '';
  if (o.avg) html += '<div class="l"><span class="t">' + esc(T.avg) + ' ' + o.avg + '%</span><span class="r"></span></div>';
  if (o.skl) html += '<div class="l"><span class="t">' + esc(T.skl) + ' ' + o.skl + '%</span><span class="r"></span></div>';
  o.bonuses.forEach(function(b){
    html += '<div class="l' + (b.max ? ' max' : '') + '"><span class="t">' + esc(b.t) + '</span><span class="r">' +
      (b.pve || b.pvp ? esc(fmt('pve_pvp', {a: b.pve || '–', b: b.pvp || '–'})) : '') + '</span></div>';
  });
  if (o.stones.length) html += '<div class="sub">' + esc(T.stones) + ': ' + o.stones.map(function(s){ return esc(s.n); }).join(', ') + '</div>';
  return html;
}
function offerHtml(o, i){
  var plus = o.plus >= 0 ? ' <span class="plus">+' + o.plus + '</span>' : '';
  var stack = o.cnt > 1 ? '<span class="stack">×' + num(o.cnt) + '</span>' : '';
  // No icon is the grey "?" frame, and a picture that fails to load becomes
  // that frame too (iconFailed).
  var icon = o.icon ? '<img src="' + esc(o.icon) + '" alt="" loading="lazy">' : PLACEHOLDER;
  var tags = '';
  if (o.lvl > 0) tags += '<span class="mk-tag">' + esc(fmt('from_level', {n: o.lvl})) + '</span>';
  tags += classBadges(o);
  if (!o.running) tags += '<span class="mk-tag bad">' + esc(T.shop_closed) + '</span>';
  if (o.slip) tags += '<span class="mk-tag bad">' + esc(T.slip) + '</span>';
  var flag = o.flag ? '<img src="' + esc(o.flag) + '" alt="' + esc(D.empires[o.emp - 1]) + '" title="' + esc(D.empires[o.emp - 1]) + '">' : '';
  tags += '<span class="mk-seller">' + flag + '<span class="who" data-shop="' + o.owner + '" title="' + esc(T.seller_title) + '">' +
    esc(o.seller || ('#' + o.owner)) + '</span> · <span class="shopname" title="' + esc(o.shop_name + ' — ' + o.where) + '">' +
    esc(o.shop_name) + '</span> · <span class="mk-muted">' + esc(o.where) + '</span> <a href="' + esc(D.player + o.owner) +
    '" title="Karta postaci sprzedawcy">↗</a></span>';
  var nBon = bonusCount(o), ksLabel = o.stones.length ? fmt('stones_n', {n: o.stones.length}) : '';
  var bonBtn = nBon || o.stones.length ? '<div class="mk-bon"><button type="button" class="mk-btn2" data-bon="' + i + '" style="padding:3px 9px;font-size:12px">' +
    esc(nBon ? bonusesWord(nBon) : ksLabel) + ' ▾</button>' + (nBon && ksLabel ? '<span class="mk-tag mk-ks">' + esc(ksLabel) + '</span>' : '') +
    '<div class="mk-bon-list" id="mk-bon-' + i + '">' + bonusList(o) + '</div></div>' : '';
  var right = '<div class="mk-price">' + num(o.price) + '<small>' + esc(T.yang) + '</small></div>';
  if (o.cnt > 1) right += '<div class="mk-unit">' + esc(fmt('per_unit', {p: num(o.unit)})) + '</div>';
  // A rare item's badge replaces the bargain's, cheap or not.
  if (o.rare) {
    right += '<span class="mk-rare" title="' + esc(fmt('rare_title', {n: num(o.rcnt)}) +
      (o.ref ? ' · ' + fmt('ref_price', {p: num(o.ref)}) : '')) + '">' + esc(T.rare) + '</span>';
  } else if (o.deal !== null && o.deal >= D.deal_badge) {
    // Every bargain has its "?", whose box (dealHtml) shows on hover, on
    // focus and on a tap - a title shows on no phone.
    right += '<span class="mk-deal">' + esc(fmt('deal', {n: o.deal})) + '<button type="button" class="q' +
      (o.deal >= D.deal_suspect ? ' warn' : '') + '" data-deal="' + i + '" aria-label="' + esc(T.deal_help) +
      '" aria-expanded="false">?</button></span>';
  } else if (o.deal !== null && o.deal < 0) {
    right += '<span class="mk-dear" title="' + esc(fmt('ref_price', {p: num(o.ref)})) + '">' + esc(fmt('dearer', {n: -o.deal})) + '</span>';
  }
  if (o.running) right += '<button type="button" class="mk-btn" data-tp="' + i + '" title="' + esc(T.tp_title) + '">' + esc(T.tp) + '</button>';
  return '<div class="mk-offer' + (o.running ? '' : ' closed') + '"><input type="checkbox" data-cmp="' + o.id + '" title="' +
    esc(T.compare_pick) + '"' + (picked[o.id] ? ' checked' : '') + '><div class="mk-icon" data-tip="' + i + '">' + icon +
    '</div><div style="min-width:0"><div class="mk-name" data-item="' + i + '" title="' + esc(T.item_title) + '">' + esc(o.name) +
    plus + stack + '</div><div class="mk-tags">' + tags + '</div>' + bonBtn + '</div><div class="mk-right">' + right + '</div></div>';
}
function draw(data){
  hidePop();
  $('mk-when').textContent = data.generated_at ? fmt('data_from', {t: data.generated_text}) : T.building;
  if (data.building && data.generated_at) $('mk-when').innerHTML = '<span class="mk-spin"></span>' + esc(fmt('data_from', {t: data.generated_text}));
  $('mk-count').textContent = fmt('offers_n', {n: num(data.total)});
  Object.keys(data.errors || {}).forEach(function(k){ var el = $('mk-' + k); if (el) el.classList.add('mk-bad'); });
  drawCats(data.counts);
  drawChips();
  drawChart(data.chart);
  var list = $('mk-list');
  if (!data.generated_at) { list.innerHTML = '<div class="mk-card mk-state"><span class="mk-spin"></span>' + esc(T.building) +
      (data.error ? '<br><small>' + esc(data.error) + '</small>' : '') + '</div>'; $('mk-pager').innerHTML = ''; return; }
  if (!data.rows.length) {
    list.innerHTML = '<div class="mk-card mk-state"><b>' + esc(T.empty) + '</b><button type="button" class="mk-btn" id="mk-empty-clear">' +
      esc(T.clear_filters) + '</button></div>';
    $('mk-empty-clear').onclick = clearAll; $('mk-pager').innerHTML = ''; return;
  }
  list.innerHTML = data.rows.map(offerHtml).join('');
  var pg = '<button type="button" class="mk-btn2" data-page="' + (data.page - 1) + '"' + (data.page <= 1 ? ' disabled' : '') + '>' + esc(T.page_prev) +
    '</button><span class="mk-muted">' + esc(fmt('page_of', {a: data.page, b: data.pages})) + '</span><button type="button" class="mk-btn2" data-page="' +
    (data.page + 1) + '"' + (data.page >= data.pages ? ' disabled' : '') + '>' + esc(T.page_next) + '</button><label class="mk-muted">' +
    esc(T.per_page) + ' <select id="mk-per">' + [25, 50, 100].map(function(n){ return '<option' + (n === data.per ? ' selected' : '') + '>' + n + '</option>'; }).join('') +
    '</select></label>';
  $('mk-pager').innerHTML = pg;
  $('mk-per').onchange = function(){ state.per = this.value; state.page = '1'; load(true); };
}
function drawChart(chart){
  var box = $('mk-chart');
  if (!chart) { box.style.display = 'none'; box.innerHTML = ''; return; }
  box.style.display = '';
  var pts = chart.points || [];
  var head = '<div class="mk-sec">' + esc(T.chart_title) + ' — ' + esc(chart.name) + '</div>';
  if (pts.length < 2) { box.innerHTML = head + '<p class="mk-muted">' + esc(T.chart_none) + '</p>'; return; }
  var W = 900, H = 150, L = 64, R = 10, Tm = 8, B = 22;
  var t0 = pts[0][0], t1 = pts[pts.length - 1][0], lo = Infinity, hi = -Infinity;
  pts.forEach(function(p){ lo = Math.min(lo, p[2] || p[1]); hi = Math.max(hi, p[1]); });
  if (hi <= lo) { hi = lo * 1.1 + 1; lo = lo * 0.9; }
  var x = function(t){ return L + (W - L - R) * (t - t0) / Math.max(1, t1 - t0); };
  var y = function(v){ return Tm + (H - Tm - B) * (1 - (v - lo) / (hi - lo)); };
  var line = pts.map(function(p, i){ return (i ? 'L' : 'M') + x(p[0]).toFixed(1) + ' ' + y(p[1]).toFixed(1); }).join(' ');
  var low = pts.map(function(p, i){ return (i ? 'L' : 'M') + x(p[0]).toFixed(1) + ' ' + y(p[2] || p[1]).toFixed(1); }).join(' ');
  var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none" role="img" aria-label="' + esc(T.chart_title) + '">';
  [lo, (lo + hi) / 2, hi].forEach(function(v){ svg += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y(v) + '" y2="' + y(v) +
    '" stroke="#332B1D" stroke-dasharray="3 4"/><text x="' + (L - 6) + '" y="' + (y(v) + 4) + '" fill="#A89D84" font-size="11" text-anchor="end">' + num(v) + '</text>'; });
  [t0, t1].forEach(function(t, i){ var d = new Date(t * 1000); svg += '<text x="' + x(t) + '" y="' + (H - 6) + '" fill="#A89D84" font-size="11" text-anchor="' +
    (i ? 'end' : 'start') + '">' + d.toLocaleDateString() + '</text>'; });
  svg += '<path d="' + low + '" fill="none" stroke="#6B6350" stroke-width="1.5"/><path d="' + line + '" fill="none" stroke="#E9B64B" stroke-width="2"/></svg>';
  box.innerHTML = head + svg;
}

// ---- the tooltip --------------------------------------------------------------
var tip = $('mk-tip');
function tipHtml(o){
  var h = '<div class="nm">' + esc(o.name) + (o.plus >= 0 ? ' <span class="plus">+' + o.plus + '</span>' : '') + '</div>';
  if (o.lvl > 0) h += '<div>' + esc(fmt('tt_level', {n: o.lvl})) + '</div>';
  if (!o.cls_all) h += '<div>' + esc(fmt('tt_classes', {c: o.classes.map(function(c){ return D.classes[c]; }).join(', ')})) + '</div>';
  if (o.base.length) h += '<div class="hr"></div>' + o.base.map(function(s){ return '<div>' + esc(s) + '</div>'; }).join('');
  if (o.bonuses.length || o.avg || o.skl) {
    h += '<div class="hr"></div>';
    if (o.avg) h += '<div class="bn">' + esc(T.avg) + ' ' + o.avg + '%</div>';
    if (o.skl) h += '<div class="bn">' + esc(T.skl) + ' ' + o.skl + '%</div>';
    h += o.bonuses.map(function(b){ return '<div class="bn' + (b.max ? ' max' : '') + '">' + esc(b.t) + '</div>'; }).join('');
  }
  if (o.stones.length) h += '<div class="hr"></div>' + o.stones.map(function(s){ return '<div>' + esc(s.n) + '</div>'; }).join('');
  return h;
}
// ---- the bargain's box ("?") -----------------------------------------------------
var pop = $('mk-pop'), popFor = null, popPinned = false;
function yangOf(o, value){ return o.cnt > 1 ? fmt('per_unit', {p: num(value)}) : num(value) + ' ' + T.yang; }
function dealHtml(o){
  var how = o.rsrc === 3 ? T.deal_how_week : T.deal_how_sheet;
  var h = '<div><b>' + esc(fmt('deal_box_offer', {p: yangOf(o, o.cnt > 1 ? o.unit : o.price)})) + '</b></div>';
  h += '<div>' + esc(fmt('deal_box_usual', {p: yangOf(o, o.ref)})) + '</div><div class="mk-muted">' + esc(how) + '</div>';
  h += '<div class="rule">' + esc(fmt('deal_box_rule', {n: D.deal_badge})) + '</div>';
  if (o.deal >= D.deal_suspect) h += '<div class="warn">' + esc(T.deal_suspect) + '</div>';
  return h;
}
function placePop(el){
  var r = el.getBoundingClientRect(), w = pop.offsetWidth, hgt = pop.offsetHeight;
  var x = Math.min(innerWidth - w - 8, Math.max(8, r.right - w)), y = r.bottom + 6;
  if (y + hgt > innerHeight - 8) y = Math.max(8, r.top - hgt - 6);
  pop.style.left = x + 'px'; pop.style.top = y + 'px';
}
function showPop(el, pinned){
  var o = last && last.rows[+el.dataset.deal]; if (!o) return;
  if (popFor && popFor !== el) popFor.setAttribute('aria-expanded', 'false');
  pop.innerHTML = dealHtml(o); pop.classList.add('on'); placePop(el);
  popFor = el; popPinned = !!pinned; el.setAttribute('aria-expanded', 'true');
}
function hidePop(){
  pop.classList.remove('on'); if (popFor) popFor.setAttribute('aria-expanded', 'false'); popFor = null; popPinned = false;
}
function moveTip(ev){ var w = tip.offsetWidth, hgt = tip.offsetHeight, x = ev.clientX + 16, y = ev.clientY + 14;
  if (x + w > innerWidth - 8) x = ev.clientX - w - 12; if (y + hgt > innerHeight - 8) y = Math.max(8, innerHeight - hgt - 8);
  tip.style.left = x + 'px'; tip.style.top = y + 'px'; }

// ---- comparison ----------------------------------------------------------------
var picked = {};
function drawCmpBar(){
  var n = Object.keys(picked).length;
  $('mk-cmpbar').classList.toggle('on', n >= 1);
  $('mk-cmp-open').textContent = fmt('compare', {n: n});
  $('mk-cmp-open').disabled = n < 2;
}
function openCompare(){
  var items = Object.keys(picked).map(function(k){ return picked[k]; });
  $('mk-cmp').style.gridTemplateColumns = 'repeat(' + items.length + ', minmax(0, 1fr))';
  $('mk-cmp').innerHTML = items.map(function(o){
    var rows = [[T.c_plus, o.plus >= 0 ? '+' + o.plus : '–'], [T.c_level, o.lvl || '–'],
      [T.c_bonuses, o.bonuses.length ? o.bonuses.map(function(b){ return (b.max ? '★ ' : '') + esc(b.t); }).join('<br>') : '–'],
      [T.avg, o.avg ? o.avg + '%' : '–'], [T.skl, o.skl ? o.skl + '%' : '–'],
      [T.stones, o.stones.length ? o.stones.map(function(s){ return esc(s.n); }).join('<br>') : '–'],
      [T.c_price, num(o.price) + ' ' + esc(T.yang) + (o.cnt > 1 ? '<br><small>' + esc(fmt('per_unit', {p: num(o.unit)})) + '</small>' : '')],
      [T.c_deal, o.rare ? T.rare : (o.deal !== null ? o.deal + '%' : '–')], [T.c_seller, esc(o.seller) + ' · ' + esc(o.shop_name)]];
    return '<div class="col"><div class="mk-name" style="cursor:default">' + esc(o.name) + (o.plus >= 0 ? ' <span class="plus">+' + o.plus + '</span>' : '') +
      '</div>' + rows.map(function(r){ return '<div class="row"><span>' + esc(r[0]) + '</span><span style="text-align:right">' +
      (r[0] === T.c_bonuses || r[0] === T.stones || r[0] === T.c_price || r[0] === T.c_seller ? r[1] : esc(r[1])) + '</span></div>'; }).join('') + '</div>';
  }).join('');
  $('mk-modal').classList.add('on');
}

// ---- TP -----------------------------------------------------------------------
var toastTimer = null;
function toast(msg, kind, keep){
  var el = $('mk-toast'); el.className = 'mk-toast on' + (kind ? ' ' + kind : ''); el.innerHTML = msg;
  clearTimeout(toastTimer); if (!keep) toastTimer = setTimeout(function(){ el.className = 'mk-toast'; }, 7000);
}
var tpLog = [];
function teleport(o){
  toast(esc(T.tp_sending), '', true);
  fetch(D.teleport, {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
    body: JSON.stringify({x: o.x, y: o.y, channel: o.ch || 1})})
    .then(function(r){ var ct = r.headers.get('content-type') || ''; if (ct.indexOf('json') < 0) throw {kind: 'login'}; return r.json(); })
    .then(function(d){
      var msg;
      if (d.ok) msg = fmt('tp_done', {name: d.name, shop: o.shop_name || o.seller, ch: o.ch || 1});
      else if (d.error === 'no_human_player' || d.error === 'player_offline') msg = T.tp_offline;
      else msg = fmt('tp_failed', {why: d.status || d.error || '?'});
      toast(esc(msg), d.ok ? 'ok' : 'bad');
      tpLog.unshift(new Date().toLocaleTimeString() + ' · ' + (o.seller || '#' + o.owner) + ' · ' + o.shop_name + ' → ' + msg);
      tpLog = tpLog.slice(0, 8);
      $('mk-hist').innerHTML = tpLog.map(function(t){ return '<div>' + esc(t) + '</div>'; }).join('');
    })
    .catch(function(e){ toast(esc(e && e.kind === 'login' ? T.login : T.tp_net), 'bad'); });
}

// ---- events -------------------------------------------------------------------
function clearAll(){ state = {}; FIELDS.forEach(function(k){ state[k] = DEFAULTS[k]; });
  bonusRows = 1; toForm(); load(true); }
document.addEventListener('input', function(ev){
  var id = ev.target && ev.target.id || ''; if (id.indexOf('mk-') !== 0) return;
  validate(); schedule();
});
document.addEventListener('change', function(ev){
  var id = ev.target && ev.target.id || '';
  if (id === 'mk-sort') { fromForm(); state.page = '1'; load(true); return; }
  if (id.indexOf('mk-') === 0 && id !== 'mk-per' && ev.target.type !== 'text' && ev.target.type !== 'search') schedule();
  if (ev.target.dataset && ev.target.dataset.cmp) {
    var oid = ev.target.dataset.cmp;
    if (ev.target.checked) {
      if (Object.keys(picked).length >= 4) { ev.target.checked = false; toast(esc(T.compare_max), 'bad'); return; }
      for (var i = 0; i < last.rows.length; i++) if (String(last.rows[i].id) === oid) picked[oid] = last.rows[i];
    } else delete picked[oid];
    drawCmpBar();
  }
});
document.addEventListener('click', function(ev){
  var d = ev.target.closest ? ev.target.closest('[data-deal]') : null;
  if (d) { if (popFor === d && popPinned) hidePop(); else showPop(d, true); return; }
  if (popFor && !(ev.target.closest && ev.target.closest('#mk-pop'))) hidePop();
  var t = ev.target.closest ? ev.target.closest('[data-cat],[data-page],[data-bon],[data-tp],[data-shop],[data-item],[data-chip]') : null;
  if (!t) return;
  if (t.dataset.cat !== undefined && t.classList.contains('mk-cat')) { fromForm(); state.cat = t.dataset.cat; state.sub = t.dataset.sub;
    state.page = '1'; load(true); return; }
  if (t.dataset.page !== undefined) { if (t.disabled) return; state.page = t.dataset.page; load(true); window.scrollTo(0, 0); return; }
  if (t.dataset.bon !== undefined) { var b = $('mk-bon-' + t.dataset.bon); if (b) b.classList.toggle('open'); return; }
  if (t.dataset.tp !== undefined) { teleport(last.rows[+t.dataset.tp]); return; }
  if (t.dataset.shop !== undefined) { fromForm(); state.shop = t.dataset.shop; state.page = '1'; load(true); return; }
  if (t.dataset.item !== undefined) { var o = last.rows[+t.dataset.item]; fromForm(); state.vnum = String(o.vnum);
    state['var'] = String(o['var'] || ''); state.sort = 'price_asc'; $('mk-sort').value = 'price_asc'; state.page = '1'; load(true); return; }
  if (t.dataset.chip !== undefined) { state[t.dataset.chip] = ''; if (t.dataset.chip === 'vnum') state['var'] = ''; state.page = '1'; load(true); }
});
document.addEventListener('mouseover', function(ev){
  var d = ev.target.closest ? ev.target.closest('[data-deal]') : null;
  if (d && !popPinned) showPop(d, false);
  var t = ev.target.closest ? ev.target.closest('[data-tip]') : null;
  if (!t || !last) return; tip.innerHTML = tipHtml(last.rows[+t.dataset.tip]); tip.style.display = 'block'; moveTip(ev);
});
document.addEventListener('mousemove', function(ev){ if (tip.style.display === 'block') moveTip(ev); });
document.addEventListener('mouseout', function(ev){ var t = ev.target.closest ? ev.target.closest('[data-tip]') : null; if (t) tip.style.display = 'none';
  var d = ev.target.closest ? ev.target.closest('[data-deal]') : null; if (d && d === popFor && !popPinned) hidePop(); });
document.addEventListener('focusin', function(ev){ var d = ev.target.closest ? ev.target.closest('[data-deal]') : null; if (d && !popPinned) showPop(d, false); });
document.addEventListener('focusout', function(ev){ var d = ev.target.closest ? ev.target.closest('[data-deal]') : null; if (d && d === popFor && !popPinned) hidePop(); });
window.addEventListener('scroll', function(){ if (popFor) placePop(popFor); }, true);
window.addEventListener('resize', function(){ if (popFor) placePop(popFor); });
$('mk-apply').onclick = function(){ apply(true); };
$('mk-clear').onclick = clearAll;
$('mk-refresh').onclick = function(){ load(false, {refresh: '1'}); };
$('mk-bonus-add').onclick = function(){ fromForm(); bonusRows = Math.min(3, bonusRows + 1); drawBonusRows(); };
$('mk-sidetoggle').onclick = function(){ $('mk-side').classList.toggle('open'); };
$('mk-cmp-open').onclick = openCompare;
$('mk-cmp-close').onclick = function(){ $('mk-modal').classList.remove('on'); };
$('mk-modal').onclick = function(ev){ if (ev.target === this) this.classList.remove('on'); };
$('mk-cmp-clear').onclick = function(){ picked = {}; document.querySelectorAll('[data-cmp]').forEach(function(c){ c.checked = false; }); drawCmpBar(); };
document.addEventListener('keydown', function(ev){ if (ev.key === 'Escape') { $('mk-modal').classList.remove('on'); hidePop(); } });
window.addEventListener('popstate', function(){ readUrl(); toForm(); load(false); });
readUrl(); toForm(); load(false); drawCmpBar();
})();
