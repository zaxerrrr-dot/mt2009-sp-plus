/* The browser half of the web pages' translation (MT2009_PLUS_WEB_I18N_V1).
 *
 * The server translates a page before sending it (m2i18n.py / m2i18n.php);
 * this translates what the page's own scripts draw afterwards - a live list,
 * a tooltip, a dialog's question - with the same tables, fetched once from
 * the URL in data-src (or /i18n/<lang>.json next to the page) and cached by
 * the browser. Loaded only on a page that is not in its own language. The
 * same file serves every app (seban-panel, the classic panel, the ItemShop).
 */
(function () {
  'use strict';
  var me = document.currentScript || document.querySelector('script[data-m2i18n]');
  if (!me) return;
  var lang = me.getAttribute('data-m2i18n');
  var src = me.getAttribute('data-src') || ((window.M2I18N_ROOT || '') + '/i18n/' + lang + '.json');
  var PH = /\{(\d+)\}/g;
  var ATTRS = ['title', 'alt', 'placeholder', 'aria-label', 'data-confirm', 'data-title', 'data-tip', 'label'];
  var SKIP = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1, PRE: 1, CODE: 1 };
  var LEADING = /^([^\w(„"'«À-ɏͰ-ϿЀ-ӿ]+)(?=[\w(„"'«À-ɏͰ-ϿЀ-ӿ])/;
  var TRAILING = /(\s*(?:[:：…*!?.]|\.\.\.|\s[→↗›»]|\s\(\?\))+\s*)$/;
  var SPLIT = /(\s+[·|—–\/•]\s+|:\s+|,\s+|\s+\(|\)\s+|\s*[\[\]]\s*)/;
  var LETTER = /[A-Za-zÀ-ɏͰ-ϿЀ-ӿ؀-ۿ]/;
  var exact = {}, patterns = [], regex = [], cache = Object.create(null), ready = false;

  function esc(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  function norm(s) { return s.replace(/\s+/g, ' ').trim(); }

  function compile(source, target) {
    var parts = source.split(PH), rx = '^', groups = [], literal = '';
    for (var i = 0; i < parts.length; i++) {
      if (i % 2 === 0) { rx += esc(parts[i]); if (parts[i].length > literal.length) literal = parts[i]; }
      else { groups.push(+parts[i]); rx += '([\\s\\S]+?)'; }
    }
    return { rx: new RegExp(rx + '$'), groups: groups, target: target, literal: literal };
  }

  function lookup(core, depth) {
    if (Object.prototype.hasOwnProperty.call(exact, core)) return exact[core];
    for (var i = 0; i < patterns.length; i++) {
      var p = patterns[i];
      if (p.literal && core.indexOf(p.literal) < 0) continue;
      var m = p.rx.exec(core);
      if (!m) continue;
      var values = {};
      for (var g = 0; g < p.groups.length; g++) {
        var v = m[g + 1], t = v.trim();
        if (depth < 2 && t) { var inner = lookup(t, depth + 1); if (inner != null) v = v.replace(t, inner); }
        values[p.groups[g]] = v;
      }
      return p.target.replace(PH, function (all, n) { return values[n] != null ? values[n] : all; });
    }
    return null;
  }

  function tr(core, depth) {
    var hit = lookup(core, 0);
    if (hit != null) return hit;
    var m = LEADING.exec(core);
    if (m && depth < 3) {
      var rest = core.slice(m[0].length), out = tr(rest, depth + 1);
      if (out !== rest) return m[1] + out;
    }
    m = TRAILING.exec(core);
    if (m && m.index > 0 && depth < 3) {
      var head = core.slice(0, m.index), o2 = tr(head, depth + 1);
      if (o2 !== head) return o2 + m[1];
    }
    if (depth < 2 && SPLIT.test(core)) {
      var pieces = core.split(SPLIT), changed = false;
      for (var i = 0; i < pieces.length; i += 2) {
        var piece = pieces[i], t = piece.trim();
        if (t && LETTER.test(t)) {
          var o3 = tr(t, depth + 1);
          if (o3 !== t) { pieces[i] = piece.replace(t, o3); changed = true; }
        }
      }
      if (changed) return pieces.join('');
    }
    var result = core;
    for (var r = 0; r < regex.length; r++) result = result.replace(regex[r][0], regex[r][1]);
    return result;
  }

  function translate(text) {
    if (!ready || !text || !LETTER.test(text)) return text;
    var core = norm(text);
    if (!core) return text;
    var out = cache[core];
    if (out === undefined) { out = tr(core, 0); cache[core] = out; }
    if (out === core) return text;
    var lead = text.match(/^\s*/)[0], trail = text.match(/\s*$/)[0];
    return lead + out + trail;
  }
  window.m2i18n = translate;

  function kept(el) { return !!(el && el.closest && el.closest('[translate="no"]')); }

  function walk(node) {
    if (node.nodeType === 3) {
      var p = node.parentElement;
      if (p && (SKIP[p.tagName] || kept(p))) return;
      var t = translate(node.nodeValue);
      if (t !== node.nodeValue) node.nodeValue = t;
      return;
    }
    if (node.nodeType !== 1 || node.getAttribute('translate') === 'no') return;
    for (var a = 0; a < ATTRS.length; a++) {
      var v = node.getAttribute(ATTRS[a]);
      if (v) { var tv = translate(v); if (tv !== v) node.setAttribute(ATTRS[a], tv); }
    }
    if (node.tagName === 'INPUT' && /^(submit|button|reset)$/i.test(node.type) && node.value) {
      var nv = translate(node.value); if (nv !== node.value) node.value = nv;
    }
    if (SKIP[node.tagName]) return;
    for (var c = node.firstChild; c; c = c.nextSibling) walk(c);
  }

  function start() {
    walk(document.body);
    new MutationObserver(function (list) {
      list.forEach(function (mu) {
        if (mu.type === 'childList') {
          mu.addedNodes.forEach(function (n) { if (!kept(n.nodeType === 1 ? n : n.parentElement)) walk(n); });
        } else if (mu.type === 'characterData') {
          var p = mu.target.parentElement;
          if (p && (SKIP[p.tagName] || kept(p))) return;
          var t = translate(mu.target.nodeValue);
          if (t !== mu.target.nodeValue) mu.target.nodeValue = t;
        } else if (mu.type === 'attributes') {
          var el = mu.target, v = el.getAttribute(mu.attributeName);
          if (!v || kept(el)) return;
          var tv = translate(v); if (tv !== v) el.setAttribute(mu.attributeName, tv);
        }
      });
    }).observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTRS });
    // a chart's words are drawn on a canvas, out of the DOM's reach
    if (window.Chart) {
      try {
        window.Chart.register({ id: 'm2i18n', beforeUpdate: function (chart) {
          var d = chart && chart.data; if (!d) return;
          if (Array.isArray(d.labels)) d.labels = d.labels.map(function (l) { return typeof l === 'string' ? translate(l) : l; });
          (d.datasets || []).forEach(function (s) { if (typeof s.label === 'string') s.label = translate(s.label); });
        } });
        Object.values(window.Chart.instances || {}).forEach(function (ch) { try { ch.update('none'); } catch (e) {} });
      } catch (e) {}
    }
  }

  // a script's own dialogs never enter the DOM
  ['alert', 'confirm', 'prompt'].forEach(function (name) {
    var original = window[name];
    if (typeof original !== 'function') return;
    window[name] = function (message) {
      var args = Array.prototype.slice.call(arguments);
      if (typeof message === 'string') args[0] = translate(message);
      return original.apply(window, args);
    };
  });

  fetch(src, { credentials: 'same-origin' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (data) {
    if (!data) return;
    exact = data.exact || {};
    var list = [];
    Object.keys(data.patterns || {}).forEach(function (k) {
      if (/\{\d+\}/.test(k)) { try { list.push(compile(k, data.patterns[k])); } catch (e) {} }
    });
    list.sort(function (a, b) { return b.literal.length - a.literal.length; });
    patterns = list;
    (data.regex || []).forEach(function (r) { try { regex.push([new RegExp(r[0], 'g'), r[1]]); } catch (e) {} });
    ready = true;
    if (document.body) start(); else document.addEventListener('DOMContentLoaded', start);
  }).catch(function () {});
})();
