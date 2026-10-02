// Vérification live d'un SIRET : Luhn + appel à recherche-entreprises.api.gouv.fr
// Informatif uniquement — ne bloque jamais le submit.
// S'attache automatiquement à tout <input name="siret"> sur la page.
(function(){
  var API_URL = 'https://recherche-entreprises.api.gouv.fr/search';
  var DEBOUNCE_MS = 500;

  function luhnOk(s){
    if (!/^\d{14}$/.test(s)) return false;
    var total = 0;
    for (var i = 0; i < 14; i++){
      var n = parseInt(s.charAt(i), 10);
      if (i % 2 === 0){
        n *= 2;
        if (n > 9) n -= 9;
      }
      total += n;
    }
    return total % 10 === 0;
  }

  function ensureStatusEl(input){
    if (input._siretStatus) return input._siretStatus;
    var el = document.createElement('div');
    el.className = 'siret-live-status';
    el.style.cssText = 'margin-top:6px; font-size:0.85rem; line-height:1.4; min-height:18px; transition:color 0.2s;';
    // Insère juste après le champ (ou son parent label si input est enfant direct)
    var anchor = input;
    // Si l'input est à l'intérieur d'un <label>, insérer après le label (sinon côté UI ça pousse le label)
    if (anchor.parentNode) {
      anchor.parentNode.insertBefore(el, anchor.nextSibling);
    }
    input._siretStatus = el;
    return el;
  }

  function setStatus(el, html, color){
    el.innerHTML = html;
    el.style.color = color || '';
  }

  function clearStatus(el){
    el.innerHTML = '';
  }

  function callINSEE(siret, onDone){
    var url = API_URL + '?q=' + encodeURIComponent(siret) + '&page=1&per_page=1';
    var controller = (typeof AbortController !== 'undefined') ? new AbortController() : null;
    var timeoutId = setTimeout(function(){ if (controller) controller.abort(); }, 4500);
    fetch(url, controller ? { signal: controller.signal } : undefined)
      .then(function(r){ clearTimeout(timeoutId); return r.ok ? r.json() : null; })
      .then(function(data){
        if (!data || !data.results || !data.results.length){ onDone(null); return; }
        var found = null;
        data.results.forEach(function(res){
          var siege = res.siege || {};
          if (siege.siret === siret){
            found = { nom: res.nom_complet || res.nom_raison_sociale || siege.denomination_usuelle || '', etat: siege.etat_administratif || null };
          }
          (res.matching_etablissements || []).forEach(function(etab){
            if (!found && etab.siret === siret){
              found = { nom: res.nom_complet || res.nom_raison_sociale || '', etat: etab.etat_administratif || null };
            }
          });
        });
        onDone(found);
      })
      .catch(function(){ clearTimeout(timeoutId); onDone(undefined); });
  }

  function attach(input){
    if (input._siretBound) return;
    input._siretBound = true;
    var statusEl = ensureStatusEl(input);
    var debounceTimer = null;
    var lastQueried = null;

    function run(){
      var raw = (input.value || '').replace(/\D/g, '');
      if (!raw){ clearStatus(statusEl); return; }
      if (raw.length < 14){
        setStatus(statusEl, '…saisie en cours (' + raw.length + '/14 chiffres)', '#90a4ae');
        return;
      }
      if (raw.length > 14){
        setStatus(statusEl, '✗ Trop de chiffres (SIRET = 14 chiffres)', '#ef5350');
        return;
      }
      if (!luhnOk(raw)){
        setStatus(statusEl, '✗ SIRET invalide (clé de contrôle incorrecte)', '#ef5350');
        return;
      }
      // Luhn OK → check INSEE
      if (lastQueried === raw) return;  // évite les double-fetch
      lastQueried = raw;
      setStatus(statusEl, '⏳ Vérification auprès de l\'INSEE…', '#90caf9');
      callINSEE(raw, function(info){
        if (info === undefined){
          setStatus(statusEl, '⚪ Vérification impossible (API indisponible) — sera revérifié à l\'enregistrement', '#9e9e9e');
          return;
        }
        if (info === null){
          setStatus(statusEl, '⚠ SIRET non trouvé dans la base INSEE', '#ff9800');
          return;
        }
        var active = (info.etat === 'A' || info.etat === 'Actif' || info.etat == null);
        var nom = (info.nom || '').trim() || '(nom non renseigné)';
        if (active){
          setStatus(statusEl, '✓ Entreprise active : <strong>' + escapeHtml(nom) + '</strong>', '#66bb6a');
        } else {
          setStatus(statusEl, '⚠ Entreprise trouvée mais inactive (' + escapeHtml(info.etat || '?') + ') : ' + escapeHtml(nom), '#ff9800');
        }
      });
    }

    function escapeHtml(s){
      return String(s).replace(/[&<>"']/g, function(c){
        return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c];
      });
    }

    input.addEventListener('input', function(){
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(run, DEBOUNCE_MS);
    });
    input.addEventListener('blur', function(){
      if (debounceTimer) clearTimeout(debounceTimer);
      run();
    });
    // Pré-vérification si valeur présente au chargement (ex: retour sur /profil)
    if ((input.value || '').replace(/\D/g, '').length === 14) run();
  }

  document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('input[name="siret"]').forEach(attach);
  });
})();
