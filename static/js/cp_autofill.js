// Auto-remplissage ville + region a partir du code postal (API geo.api.gouv.fr)
// Usage : ajouter data-cp-autofill sur l'input CP. Cherche dans le meme <form>
// les champs name="ville" et name="region" (input ou select).
(function(){
  function lookup(cp, cb){
    if (!/^\d{5}$/.test(cp)) return;
    fetch('https://geo.api.gouv.fr/communes?codePostal=' + cp + '&fields=nom,codeRegion,codeDepartement,departement&format=json')
      .then(function(r){ return r.ok ? r.json() : []; })
      .then(function(communes){
        if (!communes || !communes.length) {
          console.warn('[cp_autofill] aucune commune pour CP', cp);
          return;
        }
        var c = communes[0];
        var dept = null;
        if (c.departement && c.departement.nom && c.departement.code) {
          dept = c.departement.nom + ' (' + c.departement.code + ')';
        } else if (c.codeDepartement) {
          dept = c.codeDepartement;
        }
        if (!c.codeRegion) { cb(c.nom, null, dept); return; }
        fetch('https://geo.api.gouv.fr/regions/' + c.codeRegion)
          .then(function(r){ return r.ok ? r.json() : null; })
          .then(function(reg){ cb(c.nom, reg ? reg.nom : null, dept); })
          .catch(function(err){
            console.warn('[cp_autofill] erreur fetch region', err);
            cb(c.nom, null, dept);
          });
      })
      .catch(function(err){
        console.warn('[cp_autofill] erreur fetch communes', err);
      });
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
      if (!/^\d{5}$/.test(cp)) return;
      lookup(cp, function(ville, region, departement){
        var inpVille = form.querySelector('input[name="ville"]');
        setInput(inpVille, ville);
        var elReg = form.querySelector('select[name="region"], input[name="region"]');
        if (elReg){
          if (elReg.tagName === 'SELECT') setSelect(elReg, region);
          else setInput(elReg, region);
        }
        var inpDept = form.querySelector('input[name="departement"]');
        setInput(inpDept, departement);
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
