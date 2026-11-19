/* SPDX-FileCopyrightText: 2026 cloud-project contributors
   SPDX-License-Identifier: AGPL-3.0-or-later
   Menü-Umschalter und clientseitige Suche. Keine externen Ressourcen. */
(function () {
  "use strict";
  var btn = document.querySelector(".nav-toggle");
  var nav = document.getElementById("hauptnav");
  if (btn && nav) {
    btn.addEventListener("click", function () {
      var open = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!open));
      nav.classList.toggle("open", !open);
    });
  }

  var results = document.getElementById("search-results");
  if (!results) return;
  var status = document.getElementById("search-status");
  var input = document.getElementById("sq");
  var q = new URLSearchParams(location.search).get("q") || "";
  input.value = q;
  if (!q.trim()) { status.textContent = "Bitte einen Suchbegriff eingeben."; return; }

  function norm(s) { return (s || "").toLowerCase(); }
  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  function snippet(text, term) {
    var i = norm(text).indexOf(term);
    if (i < 0) return "";
    var a = Math.max(0, i - 80), b = Math.min(text.length, i + term.length + 120);
    var s = (a > 0 ? "… " : "") + text.slice(a, b) + (b < text.length ? " …" : "");
    var re = new RegExp("(" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
    return esc(s).replace(re, "<mark>$1</mark>");
  }

  status.textContent = "Suche läuft …";
  fetch("suche-index.json").then(function (r) { return r.json(); }).then(function (idx) {
    var terms = norm(q).split(/\s+/).filter(Boolean);
    var hits = [];
    idx.forEach(function (e) {
      var score = 0, ok = true;
      terms.forEach(function (t) {
        var s = 0;
        if (norm(e.t).indexOf(t) >= 0) s += 10;
        if (norm(e.s).indexOf(t) >= 0) s += 5;
        e.h.forEach(function (h) { if (norm(h).indexOf(t) >= 0) s += 3; });
        var x = norm(e.x), p = 0, n = 0;
        while ((p = x.indexOf(t, p)) >= 0 && n < 20) { n++; p += t.length; }
        s += n;
        if (!s) ok = false;
        score += s;
      });
      if (ok) hits.push({ e: e, score: score });
    });
    hits.sort(function (a, b) { return b.score - a.score; });
    status.textContent = hits.length ? hits.length + " Treffer für „" + q + "“" : "Keine Treffer für „" + q + "“.";
    results.innerHTML = hits.map(function (h) {
      return '<li><a href="' + esc(h.e.u) + '">' + esc(h.e.t) + "</a><p>" +
        (snippet(h.e.x, terms[0]) || esc(h.e.s)) + "</p></li>";
    }).join("");
  }).catch(function () {
    status.textContent = "Der Suchindex konnte nicht geladen werden.";
  });
})();
