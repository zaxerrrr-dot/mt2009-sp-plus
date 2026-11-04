/* MT2009_PLUS_DB_EDITOR_GROUPS_V1: the "Grupy potworów" edit form - monster / group pickers
   (a datalist filled from /db/grupy/api/szukaj), the name next to a number, more rows. */
(function () {
  "use strict";
  var base = location.pathname.replace(/\/grupy(\/.*)?$/, "/grupy");
  var names = {};
  var timer = null;

  function fill(input) {
    var q = input.value.trim();
    var kind = input.getAttribute("data-dbg-pick");
    var list = document.getElementById(kind === "g" ? "dbg-groups" : "dbg-mobs");
    if (!list || !q || (q.length < 2 && !/^\d+$/.test(q))) { return; }
    fetch(base + "/api/szukaj?typ=" + kind + "&q=" + encodeURIComponent(q), {credentials: "same-origin"})
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (rows) {
        list.innerHTML = "";
        rows.forEach(function (row) {
          var option = document.createElement("option");
          option.value = String(row.vnum);
          option.label = row.label;
          option.textContent = row.label;
          list.appendChild(option);
          names[kind + row.vnum] = row.label;
        });
        label(input);
      })
      .catch(function () {});
  }

  function label(input) {
    var cell = input.parentNode.querySelector("[data-dbg-label]");
    var key = input.getAttribute("data-dbg-pick") + input.value.trim();
    if (cell && names[key]) { cell.textContent = names[key]; }
    else if (cell && !input.value.trim()) { cell.textContent = ""; }
  }

  document.addEventListener("input", function (event) {
    var input = event.target;
    if (!input.matches || !input.matches("[data-dbg-pick]")) { return; }
    label(input);
    clearTimeout(timer);
    timer = setTimeout(function () { fill(input); }, 220);
  });

  document.addEventListener("click", function (event) {
    var button = event.target.closest ? event.target.closest("[data-dbg-add],[data-dbg-clear]") : null;
    if (!button) { return; }
    if (button.hasAttribute("data-dbg-clear")) {
      var row = button.closest("tr");
      row.querySelectorAll("input").forEach(function (i) { i.value = ""; });
      var cell = row.querySelector("[data-dbg-label]");
      if (cell) { cell.textContent = ""; }
      return;
    }
    var body = document.querySelector("[data-dbg-rows] tbody");
    if (!body || !body.rows.length) { return; }
    var copy = body.rows[body.rows.length - 1].cloneNode(true);
    copy.querySelectorAll("input").forEach(function (i) { i.value = ""; });
    var small = copy.querySelector("[data-dbg-label]");
    if (small) { small.textContent = ""; }
    body.appendChild(copy);
    var first = copy.querySelector("input");
    if (first) { first.focus(); }
  });
}());
