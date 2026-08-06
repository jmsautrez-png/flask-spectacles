/* Ma sélection (panier NON marchand) — stockage local navigateur, sans compte.
   Permet à un acheteur de spectacle de regrouper plusieurs spectacles pour les
   retrouver facilement, puis contacter chaque compagnie depuis sa fiche. */
(function () {
  "use strict";

  var KEY = "maSelection";
  var MAX_ITEMS = 30; // garde-fou : évite une sélection démesurée côté navigateur

  function read() {
    try {
      var raw = localStorage.getItem(KEY);
      var arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr : [];
    } catch (e) {
      return [];
    }
  }

  function write(listArr) {
    try {
      localStorage.setItem(KEY, JSON.stringify(listArr));
    } catch (e) {
      /* quota plein ou stockage indisponible : on ignore silencieusement */
    }
    updateBadge();
    document.dispatchEvent(new CustomEvent("selection:changed"));
  }

  function list() {
    return read();
  }

  function count() {
    return read().length;
  }

  function has(id) {
    var sid = String(id);
    return read().some(function (i) {
      return String(i.id) === sid;
    });
  }

  function add(item) {
    if (!item || item.id == null) return false;
    var l = read();
    if (l.length >= MAX_ITEMS) {
      alert("Votre sélection est pleine (" + MAX_ITEMS + " spectacles maximum).");
      return false;
    }
    var sid = String(item.id);
    if (!l.some(function (i) { return String(i.id) === sid; })) {
      l.push({
        id: sid,
        title: item.title || "",
        cie: item.cie || "",
        ville: item.ville || "",
        img: item.img || ""
      });
      write(l);
    }
    return true;
  }

  function remove(id) {
    var sid = String(id);
    write(read().filter(function (i) {
      return String(i.id) !== sid;
    }));
  }

  function clear() {
    write([]);
  }

  function toggle(btn) {
    if (!btn) return;
    var id = btn.getAttribute("data-sel-id");
    if (has(id)) {
      remove(id);
    } else {
      add({
        id: id,
        title: btn.getAttribute("data-sel-title"),
        cie: btn.getAttribute("data-sel-cie"),
        ville: btn.getAttribute("data-sel-ville"),
        img: btn.getAttribute("data-sel-img")
      });
    }
    paintButton(btn);
  }

  function paintButton(btn) {
    if (!btn) return;
    var id = btn.getAttribute("data-sel-id");
    var compact = btn.classList.contains("btn-selection--sm");
    if (has(id)) {
      btn.classList.add("in-selection");
      btn.setAttribute("aria-pressed", "true");
      btn.innerHTML = compact ? "\u2713 S\u00e9lectionn\u00e9" : "\u2713 Dans ma s\u00e9lection";
    } else {
      btn.classList.remove("in-selection");
      btn.setAttribute("aria-pressed", "false");
      btn.innerHTML = compact ? "\u2795 S\u00e9lectionner" : "\u2795 Ajouter \u00e0 ma s\u00e9lection";
    }
  }

  function paintAll() {
    var btns = document.querySelectorAll(".btn-selection");
    Array.prototype.forEach.call(btns, paintButton);
  }

  function updateBadge() {
    var n = count();
    var badges = document.querySelectorAll("[data-selection-badge]");
    Array.prototype.forEach.call(badges, function (el) {
      el.textContent = n;
      el.style.display = n > 0 ? "" : "none";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    updateBadge();
    paintAll();
  });

  // Synchronise l'affichage entre onglets ouverts.
  window.addEventListener("storage", function (e) {
    if (e.key === KEY) {
      updateBadge();
      paintAll();
      document.dispatchEvent(new CustomEvent("selection:changed"));
    }
  });

  window.Selection = {
    list: list,
    count: count,
    has: has,
    add: add,
    remove: remove,
    clear: clear,
    toggle: toggle,
    paintAll: paintAll,
    updateBadge: updateBadge
  };
})();
