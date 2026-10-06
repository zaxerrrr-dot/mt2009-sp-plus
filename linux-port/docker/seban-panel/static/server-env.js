// MT2009_PLUS_ENV_EDITOR_V1: "Ustawienia serwera (.env)" - the page's behaviour.
// Fields are rendered by the server (templates/server_env.html); this keeps the
// list of pending changes, checks them against the same rules the updater
// applies (env_schema.py), shows the sticky save bar and the confirmation, and
// polls env.status after a save.
(() => {
  const editor = document.getElementById('env-editor');
  if (!editor) return;
  const schema = JSON.parse(document.getElementById('env-schema').textContent);
  const state = JSON.parse(document.getElementById('env-data').textContent);
  const fields = {};
  schema.fields.forEach(f => { fields[f.key] = f; });
  const labels = schema.services || {};
  const pending = {};        // key -> new value
  const invalid = {};        // key -> reason
  let busy = false;          // a change is queued or running
  const $ = id => document.getElementById(id);
  const bar = $('env-savebar');
  const norm = s => (s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/ł/g, 'l');

  const original = key => {
    const f = fields[key];
    if (f.secret) return null;
    return Object.prototype.hasOwnProperty.call(state.values, key) ? state.values[key] : f.default;
  };
  const shown = (f, v) => {
    if (f.secret) return v ? '•••• (nowe)' : '••••';
    if (v === null || v === undefined) return '—';
    if (f.type === 'bool') return v === '1' ? 'włączone' : 'wyłączone';
    if (f.type === 'enum') { const o = (f.options || []).find(x => x[0] === v); return o ? o[1] : v; }
    return v === '' ? '(puste)' : v;
  };

  // The updater's own checks (env_schema.validate), so a mistake shows at once.
  const IPV4 = '(?:(?:25[0-5]|2[0-4]\\d|1?\\d?\\d)\\.){3}(?:25[0-5]|2[0-4]\\d|1?\\d?\\d)';
  const HOST = '(?:' + IPV4 + '|[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*)';
  const URL_RE = 'https?://[A-Za-z0-9._~:/?&=%+,;@!*()\\[\\]-]+';
  const full = p => { try { return new RegExp('^(?:' + p + ')$'); } catch (e) { return null; } };
  function validate(f, v) {
    if (v !== v.trim()) return 'bez spacji na początku i końcu';
    if (/[\x00-\x1f\x7f$`"'\\#]/.test(v)) return 'niedozwolone znaki ($ ` " \' \\ #)';
    if (v === '') {
      if (f.allow_empty || (f.type === 'enum' && (f.options || []).some(o => o[0] === ''))) return '';
      return 'wartość nie może być pusta';
    }
    const num = Number(v);
    switch (f.type) {
      case 'int':
        if (!/^-?\d{1,9}$/.test(v)) return 'musi być liczbą całkowitą';
        if (f.min !== undefined && num < f.min) return 'najmniej ' + f.min;
        if (f.max !== undefined && num > f.max) return 'najwyżej ' + f.max;
        return '';
      case 'number':
        if (!/^\d{1,6}(\.\d{1,3})?$/.test(v)) return 'liczba, np. 0 albo 1.5';
        if (num < (f.min || 0) || (f.max !== undefined && num > f.max)) return 'zakres ' + (f.min || 0) + '–' + f.max;
        return '';
      case 'bool': return v === '0' || v === '1' ? '' : 'tylko 0 albo 1';
      case 'enum': return (f.options || []).some(o => o[0] === v) ? '' : 'wybierz wartość z listy';
      case 'port': return /^\d{1,5}$/.test(v) && num >= 1 && num <= 65535 ? '' : 'port 1–65535';
      case 'portrange': {
        const m = /^(\d{1,5})-(\d{1,5})$/.exec(v);
        return m && +m[1] >= 1 && +m[1] <= +m[2] && +m[2] <= 65535 ? '' : 'zakres portów, np. 13000-13002';
      }
      case 'address': return full(IPV4).test(v) ? '' : 'adres IPv4, np. 0.0.0.0';
      case 'host': return full(HOST).test(v) ? '' : 'adres IP albo domena (bez http:// i portu)';
      case 'url': return full(URL_RE).test(v) ? '' : 'adres zaczynający się od http:// albo https://';
      case 'path': return /^[A-Za-z0-9._/-]{1,200}$/.test(v) ? '' : 'ścieżka';
      default: {
        if (f.pattern) {
          // env_schema's patterns use _HOST / _URL / _SECRET pieces already expanded.
          const re = full(f.pattern);
          if (re && !re.test(v)) return 'nieprawidłowy format' + (f.hint ? ' (' + f.hint + ')' : '');
        }
        return '';
      }
    }
  }

  // ---- the fields ----------------------------------------------------------
  const cards = [...editor.querySelectorAll('.envf[data-key]')];
  function readControl(card) {
    const f = fields[card.dataset.key];
    if (f.secret) {
      const a = card.querySelector('[data-secret-a]'), b = card.querySelector('[data-secret-b]');
      const form = card.querySelector('.env-secret-form');
      if (!a || !form || form.hidden) return {skip: true};
      if (!a.value && !b.value) return {skip: true};
      if (a.value !== b.value) return {value: a.value, error: 'obie wartości muszą być takie same'};
      return {value: a.value};
    }
    const input = card.querySelector('[data-env-input]');
    if (!input) return {skip: true};
    if (input.type === 'checkbox') return {value: input.checked ? '1' : '0'};
    return {value: input.value};
  }
  function setControl(card, value) {
    const input = card.querySelector('[data-env-input]');
    if (!input) return;
    if (input.type === 'checkbox') input.checked = value === '1';
    else input.value = value;
    const range = card.querySelector('[data-env-range]');
    if (range && value !== '') range.value = value;
    refresh(card);
  }
  function refresh(card) {
    const key = card.dataset.key, f = fields[key];
    const got = readControl(card);
    const toggleText = card.querySelector('[data-toggle-text]');
    if (toggleText) toggleText.textContent = got.value === '1' ? 'włączone' : 'wyłączone';
    let changed = false, error = '';
    if (!got.skip) {
      changed = f.secret ? true : got.value !== original(key);
      error = got.error || (changed ? validate(f, got.value) : '');
    }
    if (changed) pending[key] = got.value; else delete pending[key];
    if (error) invalid[key] = error; else delete invalid[key];
    card.classList.toggle('envf-changed', changed);
    card.classList.toggle('envf-invalid', !!error);
    const err = card.querySelector('[data-error]');
    if (err) { err.hidden = !error; err.textContent = error ? '✗ ' + error : ''; }
    const undo = card.querySelector('[data-undo]');
    if (undo) undo.hidden = !changed;
    const def = card.querySelector('[data-default]');
    if (def) def.hidden = got.skip || got.value === f.default;
    card.classList.toggle('envf-custom', !f.secret && original(key) !== f.default);
    updateBar();
  }
  cards.forEach(card => {
    const key = card.dataset.key, f = fields[key];
    const input = card.querySelector('[data-env-input]');
    const range = card.querySelector('[data-env-range]');
    if (input) {
      input.addEventListener('input', () => { if (range && input.value !== '') range.value = input.value; refresh(card); });
      input.addEventListener('change', () => refresh(card));
    }
    if (range) range.addEventListener('input', () => { input.value = range.value; refresh(card); });
    const open = card.querySelector('[data-secret-open]');
    if (open) {
      const form = card.querySelector('.env-secret-form');
      open.addEventListener('click', () => { form.hidden = false; open.hidden = true; form.querySelector('input').focus(); refresh(card); });
      card.querySelector('[data-secret-cancel]').addEventListener('click', () => {
        form.querySelectorAll('input').forEach(i => { i.value = ''; });
        form.hidden = true; open.hidden = false; refresh(card);
      });
      form.querySelectorAll('input').forEach(i => i.addEventListener('input', () => refresh(card)));
    }
    const undo = card.querySelector('[data-undo]');
    if (undo) undo.addEventListener('click', () => {
      if (f.secret) { const c = card.querySelector('[data-secret-cancel]'); if (c) c.click(); return; }
      setControl(card, original(key));
    });
    const def = card.querySelector('[data-default]');
    if (def) def.addEventListener('click', () => setControl(card, f.default));
    refresh(card);
  });

  // ---- search and filters --------------------------------------------------
  const search = $('env-search'), onlyCustom = $('env-only-custom');
  cards.forEach(card => { card.dataset.norm = norm(card.dataset.search); });
  function applyFilter() {
    const words = norm(search.value).split(/\s+/).filter(Boolean);
    let any = false;
    editor.querySelectorAll('.env-section').forEach(sec => {
      let visible = 0;
      sec.querySelectorAll('.envf').forEach(card => {
        const hit = words.every(w => card.dataset.norm.includes(w)) &&
          (!onlyCustom.checked || card.classList.contains('envf-custom') || card.classList.contains('envf-changed'));
        card.hidden = !hit;
        if (hit) visible++;
      });
      sec.hidden = !visible;
      if (visible && (words.length || onlyCustom.checked)) sec.open = true;
      any = any || visible > 0;
    });
    $('env-empty').hidden = any;
  }
  search.addEventListener('input', applyFilter);
  onlyCustom.addEventListener('change', applyFilter);
  $('env-expand').addEventListener('click', () => editor.querySelectorAll('.env-section').forEach(s => { s.open = true; }));
  $('env-collapse').addEventListener('click', () => editor.querySelectorAll('.env-section').forEach(s => { s.open = false; }));
  if (location.hash && location.hash.startsWith('#env-')) {
    const target = document.getElementById(location.hash.slice(1));
    if (target) { const sec = target.closest('details'); if (sec) sec.open = true; setTimeout(() => target.scrollIntoView({block: 'center'}), 50); }
  }

  // ---- the save bar --------------------------------------------------------
  function servicesFor(keys) {
    const out = [];
    keys.forEach(k => { const f = fields[k]; if (!f || f.build) return; f.services.forEach(s => { if (!out.includes(s)) out.push(s); }); });
    return out;
  }
  function updateBar() {
    const keys = Object.keys(pending);
    editor.querySelectorAll('.env-section').forEach(sec => {
      const n = [...sec.querySelectorAll('.envf.envf-changed')].length;
      const badge = sec.querySelector('[data-sec-changed]');
      badge.hidden = !n; badge.textContent = n ? n + ' zmian' + (n === 1 ? 'a' : (n < 5 ? 'y' : '')) : '';
    });
    if (!state.ready || !keys.length || busy) { bar.hidden = true; document.body.classList.remove('env-bar-open'); return; }
    bar.hidden = false; document.body.classList.add('env-bar-open');
    const bad = Object.keys(invalid).length;
    $('env-savebar-count').textContent = keys.length + (keys.length === 1 ? ' zmiana' : (keys.length < 5 ? ' zmiany' : ' zmian')) + (bad ? ' · ' + bad + ' do poprawienia' : '');
    const svc = servicesFor(keys).filter(s => s !== 'updater');
    $('env-savebar-services').textContent = svc.length ? 'Restart: ' + svc.map(s => labels[s] || s).join(', ') : 'Bez restartu usług';
    $('env-savebar-warn').hidden = !svc.includes('game');
    const save = $('env-save');
    save.textContent = 'Zapisz zmiany (' + keys.length + ')';
    save.disabled = bad > 0;
  }
  $('env-discard').addEventListener('click', () => {
    cards.forEach(card => {
      const f = fields[card.dataset.key];
      if (!(card.dataset.key in pending) && !(card.dataset.key in invalid)) return;
      if (f.secret) { const c = card.querySelector('[data-secret-cancel]'); if (c) c.click(); }
      else setControl(card, original(card.dataset.key));
    });
  });

  // ---- confirmation --------------------------------------------------------
  const dialog = $('env-dialog');
  $('env-save').addEventListener('click', () => {
    const keys = Object.keys(pending);
    if (!keys.length || Object.keys(invalid).length) return;
    const body = $('env-diff-body');
    body.textContent = '';
    keys.forEach(k => {
      const f = fields[k], tr = document.createElement('tr');
      const name = document.createElement('td');
      name.innerHTML = '<b></b><br><code></code>';
      name.querySelector('b').textContent = f.label; name.querySelector('code').textContent = k;
      const was = document.createElement('td'); was.textContent = f.secret ? (state.secrets[k] === 'set' ? '•••• (ustawione)' : '(nieustawione)') : shown(f, original(k));
      const now = document.createElement('td'); now.textContent = shown(f, pending[k]); now.className = 'env-diff-new';
      if (f.dangerous) tr.className = 'env-diff-danger';
      tr.append(name, was, now); body.append(tr);
    });
    const svc = servicesFor(keys);
    const real = svc.filter(s => s !== 'updater');
    $('env-dialog-services').textContent = real.length
      ? 'Zostaną uruchomione ponownie: ' + real.map(s => labels[s] || s).join(', ') + '.'
      : 'Żadna usługa nie zostanie uruchomiona ponownie.';
    if (svc.includes('updater')) $('env-dialog-services').textContent += ' Aktualizator przyjmie zmianę przy swoim następnym uruchomieniu.';
    if (keys.some(k => fields[k].build)) $('env-dialog-services').textContent += ' Ustawienia budowania zadziałają przy następnej przebudowie obrazu gry.';
    $('env-dialog-game').hidden = !real.includes('game');
    $('env-dialog-panel').hidden = !real.includes('seban-panel');
    const danger = keys.some(k => fields[k].dangerous);
    $('env-dialog-danger').hidden = !danger;
    $('env-confirm-word').value = '';
    $('env-dialog-error').hidden = true;
    $('env-dialog-ok').disabled = false;
    dialog.showModal();
    if (danger) $('env-confirm-word').focus();
  });
  $('env-dialog-cancel').addEventListener('click', () => dialog.close());
  $('env-dialog-ok').addEventListener('click', () => {
    const keys = Object.keys(pending);
    const danger = keys.some(k => fields[k].dangerous);
    if (danger && $('env-confirm-word').value.trim().toUpperCase() !== state.danger_word) {
      $('env-dialog-error').hidden = false;
      $('env-dialog-error').textContent = 'Wpisz ' + state.danger_word + ', aby potwierdzić ryzykowne zmiany.';
      return;
    }
    $('env-dialog-ok').disabled = true;
    const form = new URLSearchParams();
    form.set('env_csrf', state.csrf);
    form.set('changes', JSON.stringify(pending));
    form.set('confirm', $('env-confirm-word').value);
    fetch(state.save_url, {method: 'POST', credentials: 'same-origin', body: form, headers: {'Accept': 'application/json'}})
      .then(r => r.json().catch(() => ({ok: false, message: 'Serwer odpowiedział błędem (' + r.status + ').'})))
      .then(res => {
        if (!res.ok) {
          $('env-dialog-ok').disabled = false;
          $('env-dialog-error').hidden = false;
          $('env-dialog-error').textContent = '✗ ' + (res.message || 'Nie zapisano.');
          Object.entries(res.errors || {}).forEach(([k, reason]) => {
            const card = document.getElementById('env-' + k);
            if (card) { invalid[k] = reason; card.classList.add('envf-invalid'); const e = card.querySelector('[data-error]'); e.hidden = false; e.textContent = '✗ ' + reason; }
          });
          return;
        }
        dialog.close();
        showStatus(res.status || {state: 'queued', message: 'Zlecenie zapisane.'});
        startPolling();
      })
      .catch(() => {
        $('env-dialog-ok').disabled = false;
        $('env-dialog-error').hidden = false;
        $('env-dialog-error').textContent = '✗ Brak połączenia z panelem. Spróbuj ponownie.';
      });
  });

  // ---- status of the last change -------------------------------------------
  const STATE_LABEL = {queued: '⏳ czeka na aktualizator', running: '⏳ trwa', ok: '✓ zapisano', failed: '✗ nie udało się', rejected: '✗ odrzucono'};
  function showStatus(st) {
    if (!st || !st.state) return;
    const box = $('env-status');
    box.hidden = false;
    box.className = 'panel env-status env-status-' + st.state;
    $('env-state').textContent = STATE_LABEL[st.state] || st.state;
    $('env-status-message').textContent = st.message || '';
    $('env-status-when').textContent = st.time ? new Date(st.time * 1000).toLocaleString('pl-PL') : '';
    const list = $('env-status-results');
    list.textContent = '';
    Object.entries(st.results || {}).forEach(([k, r]) => {
      if (r.ok && st.state !== 'ok' && st.state !== 'rejected') return;
      if (r.ok && r.changed === false) return;
      const li = document.createElement('li');
      const f = fields[k];
      li.className = r.ok ? 'ok' : 'bad';
      li.textContent = (r.ok ? '✓ ' : '✗ ') + (f ? f.label + ' (' + k + ')' : k) +
        (r.ok ? (r.secret ? ': nowa wartość zapisana' : ': ' + shown(f || {}, r.old === undefined ? null : r.old) + ' → ' + shown(f || {}, r.new)) : ': ' + r.message);
      list.append(li);
    });
    const log = st.log || [];
    $('env-status-log-wrap').hidden = !log.length;
    $('env-status-log').textContent = log.join('\n');
    busy = st.state === 'queued' || st.state === 'running';
    updateBar();
  }
  let polling = false, failures = 0;
  function startPolling() {
    if (polling) return;
    polling = true; busy = true; updateBar();
    const tick = () => {
      fetch(state.status_url, {credentials: 'same-origin', headers: {'Accept': 'application/json'}})
        .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(data => {
          failures = 0;
          showStatus(data.status);
          if (data.status && data.status.busy) { setTimeout(tick, 2000); return; }
          polling = false;
          if (data.status && data.status.state === 'ok') {
            state.values = data.values || state.values;
            state.secrets = data.secrets || state.secrets;
            cards.forEach(card => {
              const f = fields[card.dataset.key];
              if (f.secret) { const c = card.querySelector('[data-secret-cancel]'); if (c) c.click(); const s = card.querySelector('.env-secret-state'); if (s && state.secrets[f.key]) { s.textContent = state.secrets[f.key] === 'set' ? '● ustawione' : '○ nieustawione'; s.className = 'env-secret-state ' + (state.secrets[f.key] === 'set' ? 'is-set' : 'is-unset'); } return; }
              const now = state.values[f.key];
              const meta = card.querySelector('.envf-meta span:nth-child(2) b');
              if (meta && now !== undefined) meta.textContent = now === '' ? '(puste)' : now;
              if (card.classList.contains('envf-changed') && now !== undefined) setControl(card, now); else refresh(card);
            });
          }
          updateBar();
        })
        .catch(() => {
          failures++;
          $('env-status-message').textContent = 'Panel uruchamia się ponownie albo chwilowo nie odpowiada – czekam…';
          if (failures < 300) setTimeout(tick, 3000); else polling = false;
        });
    };
    setTimeout(tick, 1500);
  }
  if (state.status && state.status.state) {
    showStatus(state.status);
    if (state.status.busy) startPolling();
  }
  updateBar();
})();
