// Auto-remplissage ville + region + departement a partir du code postal
// (API geo.api.gouv.fr). Si plusieurs communes pour le meme CP, propose
// une liste cliquable a cote du champ Ville.
(function(){
  function fetchCommunes(cp, cb){
    if (!/^\d{5}$/.test(cp)) return;
    fetch('https://geo.api.gouv.fr/communes?codePostal=' + cp + '&fields=nom,codeRegion,codeDepartement,departement&format=json')
      .then(function(r){ return r.ok ? r.json() : []; })
      .then(function(communes){
        if (!communes || !communes.length) {
          console.warn('[cp_autofill] aucune commune pour CP', cp);
          cb([]);
          return;
        }
        cb(communes);
      })
      .catch(function(err){
        console.warn('[cp_autofill] erreur fetch communes', err);
        cb([]);
      });
  }

  function fetchRegionName(codeRegion, cb){
    if (!codeRegion) { cb(null); return; }
    fetch('https://geo.api.gouv.fr/regions/' + codeRegion)
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(reg){ cb(reg ? reg.nom : null); })
      .catch(function(){ cb(null); });
  }

  function flash(el){
    if (!el) return;
    var prev = el.style.borderColor;
    el.style.borderColor = '#4caf50';
    el.style.boxShadow = '0 0 0 2px rgba(76,175,80,0.35)';
    setTimeout(function(){
      el.style.borderColor = prev || '';
      el.style.boxShadow = '';
    }, 1500);
  }

  function setInput(input, value){
    if (!input || value == null) return;
    input.value = value;
    flash(input);
  }

  function setSelect(select, value){
    if (!select || !value) return;
    var found = false;
    for (var i = 0; i < select.options.length; i++){
      if (select.options[i].value === value){
        select.selectedIndex = i;
        found = true;
        break;
      }
    }
    if (found) flash(select);
    else console.warn('[cp_autofill] region inconnue dans le select :', value);
  }

  function deptFromCommune(c){
    if (c.departement && c.departement.nom && c.departement.code) {
      return c.departement.nom + ' (' + c.departement.code + ')';
    }
    if (c.codeDepartement) return c.codeDepartement;
    return null;
  }

  function applyCommune(form, c){
    var dept = deptFromCommune(c);
    var inpVille = form.querySelector('input[name="ville"], input[name="location"], input[name="lieu_ville"]');
    setInput(inpVille, c.nom);
    var inpDept = form.querySelector('input[name="departement"]');
    setInput(inpDept, dept);
    var elReg = form.querySelector('select[name="region"], input[name="region"]');
    if (elReg){
      fetchRegionName(c.codeRegion, function(regionName){
        if (elReg.tagName === 'SELECT') setSelect(elReg, regionName);
        else setInput(elReg, regionName);
      });
    }
  }

  function ensurePicker(anchor){
    if (anchor._cpPicker) return anchor._cpPicker;
    var picker = document.createElement('div');
    picker.style.cssText = 'margin-top:6px;padding:8px;border:1px solid #90caf9;background:#e3f2fd;border-radius:6px;font-size:0.9em;color:#0d47a1;display:none;';
    anchor.parentNode.insertBefore(picker, anchor.nextSibling);
    anchor._cpPicker = picker;
    return picker;
  }

  function showPicker(form, communes){
    var anchor = form.querySelector('input[name="ville"], input[name="location"], input[name="lieu_ville"]')
              || form.querySelector('input[data-cp-autofill]');
    if (!anchor) return;
    var picker = ensurePicker(anchor);
    picker.innerHTML = '';
    var label = document.createElement('div');
    label.textContent = 'Plusieurs communes pour ce code postal — choisissez la votre :';
    label.style.cssText = 'margin-bottom:6px;font-weight:500;';
    picker.appendChild(label);
    var wrap = document.createElement('div');
    wrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px;';
    communes.forEach(function(c){
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = c.nom;
      btn.style.cssText = 'padding:4px 10px;border-radius:4px;border:1px solid #1976d2;background:#fff;color:#0d47a1;cursor:pointer;font-size:0.92em;';
      btn.addEventListener('click', function(){
        applyCommune(form, c);
        picker.style.display = 'none';
      });
      wrap.appendChild(btn);
    });
    picker.appendChild(wrap);
    picker.style.display = 'block';
  }

  function hidePicker(form){
    var anchor = form.querySelector('input[name="ville"], input[name="location"], input[name="lieu_ville"]')
              || form.querySelector('input[data-cp-autofill]');
    if (anchor && anchor._cpPicker) anchor._cpPicker.style.display = 'none';
  }

  function attach(input){
    if (input.dataset.cpAutofillBound === '1') return;
    input.dataset.cpAutofillBound = '1';
    var form = input.form;
    if (!form) {
      console.warn('[cp_autofill] input CP hors <form>', input);
      return;
    }
    var run = function(){
      var cp = (input.value || '').trim();
      if (!/^\d{5}$/.test(cp)) { hidePicker(form); return; }
      fetchCommunes(cp, function(communes){
        if (!communes.length) { hidePicker(form); return; }
        // Toujours appliquer la 1ere : remplit dept + region (identiques pour ce CP)
        applyCommune(form, communes[0]);
        if (communes.length > 1) showPicker(form, communes);
        else hidePicker(form);
      });
    };
    input.addEventListener('blur', run);
    input.addEventListener('change', run);
    input.addEventListener('input', function(){
      var v = (input.value || '').trim();
      if (/^\d{5}$/.test(v)) run();
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('input[data-cp-autofill]').forEach(attach);
  });
})();
