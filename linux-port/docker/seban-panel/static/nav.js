// Seban Panel navigation v2 (MT2009_PLUS_SEBAN_NAV_V2): drawer on small
// screens, remembered menu groups, quick search (Ctrl+K or "/") and the
// sticky "Na tej stronie" section bar with the current section highlighted.
// Vanilla JS, no dependencies. Every localStorage call is guarded: a private
// window or blocked storage only loses the remembered groups and history.
(() => {
  const ROOT = window.SEBAN_ROOT || '';
  const store = {
    get(key, fallback) { try { const v = JSON.parse(localStorage.getItem(key)); return v == null ? fallback : v; } catch (_) { return fallback; } },
    set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) {} },
  };
  const norm = s => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/g, 'l');
  const escapeHtml = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---- drawer (phones/tablets) -------------------------------------------
  const toggle = document.getElementById('nav-toggle');
  const backdrop = document.getElementById('nav-backdrop');
  function closeNav() { document.body.classList.remove('nav-open'); if (toggle) toggle.setAttribute('aria-expanded', 'false'); }
  if (toggle) toggle.addEventListener('click', () => {
    const open = document.body.classList.toggle('nav-open');
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  if (backdrop) backdrop.addEventListener('click', closeNav);
  document.querySelectorAll('aside.site-nav .sn-nav a').forEach(a => a.addEventListener('click', closeNav));

  // ---- remembered groups -------------------------------------------------
  const OPEN_KEY = 'seban.nav.open';
  const opened = new Set(store.get(OPEN_KEY, []));
  document.querySelectorAll('.sn-group[data-group]').forEach(group => {
    if (opened.has(group.dataset.group)) group.open = true;
    group.addEventListener('toggle', () => {
      if (group.open) opened.add(group.dataset.group); else opened.delete(group.dataset.group);
      store.set(OPEN_KEY, [...opened]);
    });
  });
  const activeLink = document.querySelector('.sn-link.is-active');
  if (activeLink && activeLink.scrollIntoView) {
    const aside = document.getElementById('site-nav');
    if (aside && activeLink.offsetTop > aside.clientHeight - 80) aside.scrollTop = activeLink.offsetTop - aside.clientHeight / 2;
  }

  // ---- data for the quick search ------------------------------------------
  let data = {pages: [], search: [], current: {}};
  try { data = JSON.parse(document.getElementById('cmdk-data').textContent); } catch (_) {}
  const RECENT_KEY = 'seban.nav.recent';
  const here = location.pathname + location.search;
  if (data.current && data.current.l) {
    const recent = store.get(RECENT_KEY, []).filter(r => r && r.u !== here);
    recent.unshift({l: data.current.l, g: data.current.g, i: data.current.i, u: here});
    store.set(RECENT_KEY, recent.slice(0, 8));
  }

  // ---- quick search (command palette) ------------------------------------
  const dialog = document.getElementById('cmdk');
  const input = document.getElementById('cmdk-input');
  const list = document.getElementById('cmdk-list');
  let results = [], selected = 0;

  function tocEntries() {
    return [...document.querySelectorAll('#page-toc .page-toc-track a[href^="#"]:not([hidden])')]
      .map(a => ({l: a.textContent.trim(), g: '', i: '§', u: a.getAttribute('href'), d: '', k: 'na tej stronie sekcja'}));
  }

  function search(query) {
    const q = norm(query).trim();
    const sections = [];
    if (!q) {
      const recent = store.get(RECENT_KEY, []).filter(r => r.u !== here).slice(0, 5);
      if (recent.length) sections.push({head: 'Ostatnio odwiedzane', items: recent.map(r => Object.assign({d: r.g}, r))});
      const toc = tocEntries();
      if (toc.length) sections.push({head: 'Na tej stronie', items: toc});
      const byGroup = new Map();
      data.pages.filter(p => p.i !== '§').forEach(p => { if (!byGroup.has(p.g)) byGroup.set(p.g, []); byGroup.get(p.g).push(p); });
      byGroup.forEach((items, head) => sections.push({head, items}));
      return sections;
    }
    const tokens = q.split(/\s+/).filter(Boolean);
    const scored = [];
    data.pages.concat(tocEntries()).forEach(p => {
      const label = norm(p.l);
      const hay = label + ' ' + norm(p.g) + ' ' + norm(p.d) + ' ' + norm(p.k);
      if (!tokens.every(t => hay.includes(t))) return;
      let score = label.startsWith(q) ? 0 : label.includes(tokens[0]) ? 1 : 2;
      if (p.i === '§') score += .5;
      scored.push({p, score});
    });
    scored.sort((a, b) => a.score - b.score || a.p.l.localeCompare(b.p.l, 'pl'));
    if (scored.length) sections.push({head: 'Strony i sekcje', items: scored.slice(0, 12).map(s => Object.assign({d: s.p.g || 'na tej stronie'}, s.p))});
    const raw = query.trim();
    sections.push({head: 'Szukaj „' + raw + '”', items: data.search.map(s => ({l: s.l + ': ' + raw, i: s.i, d: '', u: s.u + (s.u.includes('?') ? '&' : '?') + 'q=' + encodeURIComponent(raw)}))});
    return sections;
  }

  function render() {
    const sections = search(input.value);
    results = [];
    let html = '';
    sections.forEach(section => {
      html += '<li class="cmdk-head" role="presentation">' + escapeHtml(section.head) + '</li>';
      section.items.forEach(item => {
        const idx = results.push(item) - 1;
        html += '<li class="cmdk-item" role="option" id="cmdk-opt-' + idx + '" data-idx="' + idx + '"><a href="' + escapeHtml(item.u) + '"><span class="cmdk-ico" aria-hidden="true">' + escapeHtml(item.i || '›') + '</span><span>' + escapeHtml(item.l) + (item.d ? '<small>' + escapeHtml(item.d) + '</small>' : '') + '</span>' + (item.g && item.g !== item.d ? '<em>' + escapeHtml(item.g) + '</em>' : '') + '</a></li>';
      });
    });
    list.innerHTML = html || '<li class="cmdk-empty">Brak wyników.</li>';
    select(0);
  }

  function select(idx) {
    if (!results.length) return;
    selected = (idx + results.length) % results.length;
    list.querySelectorAll('.cmdk-item.is-sel').forEach(li => li.classList.remove('is-sel'));
    const li = list.querySelector('[data-idx="' + selected + '"]');
    if (li) { li.classList.add('is-sel'); li.scrollIntoView({block: 'nearest'}); input.setAttribute('aria-activedescendant', li.id); }
  }

  function go(item) {
    if (!item) return;
    if (item.u.startsWith('#')) {
      dialog.close();
      const target = document.getElementById(item.u.slice(1));
      if (target) { target.scrollIntoView({behavior: reduceMotion ? 'auto' : 'smooth'}); history.replaceState(null, '', item.u); }
      return;
    }
    window.location.href = item.u;
  }

  function openPalette() {
    if (!dialog || dialog.open) return;
    closeNav();
    input.value = '';
    render();
    try { dialog.showModal(); } catch (_) { dialog.setAttribute('open', ''); }
    input.focus();
  }

  if (dialog && input && list) {
    document.addEventListener('click', event => {
      if (event.target.closest('[data-cmdk-open]')) { event.preventDefault(); openPalette(); }
    });
    document.addEventListener('keydown', event => {
      const typing = event.target.closest && event.target.closest('input,textarea,select,[contenteditable="true"]');
      if ((event.ctrlKey || event.metaKey) && !event.altKey && (event.key === 'k' || event.key === 'K')) { event.preventDefault(); dialog.open ? dialog.close() : openPalette(); return; }
      if (event.key === '/' && !typing && !dialog.open && !event.ctrlKey && !event.metaKey && !event.altKey) { event.preventDefault(); openPalette(); }
      if (event.key === 'Escape' && document.body.classList.contains('nav-open')) closeNav();
    });
    input.addEventListener('input', render);
    input.addEventListener('keydown', event => {
      if (event.key === 'ArrowDown') { event.preventDefault(); select(selected + 1); }
      else if (event.key === 'ArrowUp') { event.preventDefault(); select(selected - 1); }
      else if (event.key === 'Enter') { event.preventDefault(); go(results[selected]); }
    });
    list.addEventListener('mousemove', event => {
      const li = event.target.closest('.cmdk-item');
      if (li && Number(li.dataset.idx) !== selected) select(Number(li.dataset.idx));
    });
    list.addEventListener('click', event => {
      const li = event.target.closest('.cmdk-item');
      if (!li || event.ctrlKey || event.metaKey || event.shiftKey || event.button) return;
      event.preventDefault();
      go(results[Number(li.dataset.idx)]);
    });
    dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  }

  // ---- "Na tej stronie" section bar ---------------------------------------
  const slug = s => norm(s).replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40);
  let tocLinks = [];

  function buildToc() {
    const main = document.querySelector('main');
    const slot = main && main.querySelector('#page-toc');
    tocLinks = [];
    if (!slot) return;
    if ('static' in slot.dataset) {
      // Server-written bar (settings pages): hide chips whose section is
      // switched off by a feature flag, and group labels left with nothing.
      slot.querySelectorAll('.page-toc-track a[href^="#"]').forEach(a => { a.hidden = !document.getElementById(a.getAttribute('href').slice(1)); });
      slot.querySelectorAll('.page-toc-part').forEach(part => {
        let node = part.nextElementSibling, any = false;
        while (node && !node.classList.contains('page-toc-part')) { if (!node.hidden) any = true; node = node.nextElementSibling; }
        part.hidden = !any;
      });
    } else {
      const seen = new Set(), items = [];
      main.querySelectorAll('h2').forEach(h => {
        if (h.closest('dialog,#page-toc,.page-topbar,[hidden],template')) return;
        const target = h.closest('section,article,.panel') || h;
        if (seen.has(target) || target === main) return;
        seen.add(target);
        let text = h.textContent.replace(/\s+/g, ' ').trim().replace(/^[^\p{L}\p{N}]+/u, '');
        if (!text) return;
        if (text.length > 34) text = text.slice(0, 32).trim() + '…';
        if (!target.id) {
          const base = 'sekcja-' + (slug(text) || items.length + 1);
          let id = base, n = 2;
          while (document.getElementById(id)) id = base + '-' + n++;
          target.id = id;
        }
        items.push({id: target.id, text});
      });
      if (items.length < 4 || document.body.dataset.endpoint === 'dashboard') { slot.hidden = true; slot.innerHTML = ''; return; }
      slot.innerHTML = '<span class="page-toc-title">Na tej stronie</span><div class="page-toc-track"></div>';
      const track = slot.lastElementChild;
      items.forEach(item => {
        const a = document.createElement('a');
        a.href = '#' + item.id;
        a.textContent = item.text;
        track.appendChild(a);
      });
      slot.hidden = false;
    }
    tocLinks = [...slot.querySelectorAll('.page-toc-track a[href^="#"]:not([hidden])')]
      .map(a => ({a, target: document.getElementById(a.getAttribute('href').slice(1))}))
      .filter(x => x.target);
    tocLinks.forEach(({a, target}) => a.addEventListener('click', event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey) return;
      event.preventDefault();
      target.scrollIntoView({behavior: reduceMotion ? 'auto' : 'smooth'});
      history.replaceState(null, '', a.getAttribute('href'));
    }));
    spy();
  }

  let spyQueued = false;
  function spy() {
    spyQueued = false;
    if (!tocLinks.length) return;
    const slot = document.getElementById('page-toc');
    // Sections scrolled to by a chip stop just under the bar (scroll-margin-top),
    // so the line sits a little below the bar's bottom edge.
    const line = (slot ? slot.getBoundingClientRect().bottom : 0) + 40;
    let current = null;
    tocLinks.forEach(x => { if (x.target.getBoundingClientRect().top <= line) current = x; });
      tocLinks.forEach(x => x.a.classList.toggle('is-active', x === current));
    if (current) {
      const track = current.a.parentElement;
      const left = current.a.offsetLeft - track.offsetLeft;
      if (left < track.scrollLeft || left + current.a.offsetWidth > track.scrollLeft + track.clientWidth) track.scrollLeft = Math.max(0, left - 24);
    }
  }
  window.addEventListener('scroll', () => { if (!spyQueued) { spyQueued = true; requestAnimationFrame(spy); } }, {passive: true});
  window.addEventListener('resize', () => { if (!spyQueued) { spyQueued = true; requestAnimationFrame(spy); } });

  function init() {
    buildToc();
    if (location.hash) {
      const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target) target.scrollIntoView();
    }
  }
  // Pages build part of their content in their own scripts, so wait for the
  // whole document; ajax-forms.js swaps <main> after a form - rebuild then.
  if (document.readyState === 'complete') init(); else window.addEventListener('load', init);
  const main = document.querySelector('main');
  if (main && window.MutationObserver) {
    let pending = null;
    new MutationObserver(() => { clearTimeout(pending); pending = setTimeout(buildToc, 60); }).observe(main, {childList: true});
  }
  // Exposed for pages that want a deep link into their own sections.
  window.SebanNav = {open: openPalette, rebuildToc: buildToc, root: ROOT};
})();
