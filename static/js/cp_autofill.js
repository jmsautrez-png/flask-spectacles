// Auto-remplissage ville + region a partir du code postal (API geo.api.gouv.fr)
// Usage : ajouter data-cp-autofill sur l'input CP. Il cherchera dans le meme formulaire
// les inputs name="ville" et name="region" pour les remplir.
(function(){
  function lookup(cp, cb){
    if (!/^\d{5}$/.test(cp)) return;
    fetch('https://geo.api.gouv.fr/communes?codePostal=' + cp + '&fields=nom,codeRegion&format=json')
      .then(function(r){ return r.ok ? r.json() : []; })
      .then(function(communes){
        if (!communes || !communes.length) return;
        // Premiere commune (cas general : 1 seule par CP)
        var c = communes[0];
        // Recuperer le nom de region
        if (!c.codeRegion) { cb(c.nom, null); return; }
        fetch('https://geo.api.gouv.fr/regions/' + c.codeRegion)
          .then(function(r){ return r.ok ? r.json() : null; })
          .then(function(reg){
            cb(c.nom, reg ? reg.nom : null);
          })
          .catch(function(){ cb(c.nom, null); });
      })
      .catch(function(){});
  }

  function setIfEmptyOrConfirm(input, value){
    if (!input || !value) return;
    if (!input.value || input.value.trim() === '') {
      input.value = value;
      input.style.background = 'rgba(76,175,80,0.15)';
      setTimeout(function(){ input.style.background = ''; }, 1500);
    }
  }

  function setSelectIfMatch(select, value){
    if (!select || !value) return;
    var found = false;
    for (var i = 0; i < select.options.length; i++){
      if (select.options[i].value === value){
        select.selectedIndex = i;
        found = true;
        break;
      }
    }
    if (found){
      select.style.background = 'rgba(76,175,80,0.25)';
      setTimeout(function(){ select.style.background = ''; }, 1500);
    }
  }

  function attach(input){
    var form = input.form;
    if (!form) return;
    var run = function(){
      var cp = (input.value || '').trim();
      if (!/^\d{5}$/.test(cp)) return;
      lookup(cp, function(ville, region){
        var inpVille = form.querySelector('input[name="ville"]');
        setIfEmptyOrConfirm(inpVille, ville);
        var elReg = form.querySelector('select[name="region"], input[name="region"]');
        if (elReg){
          if (elReg.tagName === 'SELECT') setSelectIfMatch(elReg, region);
          else setIfEmptyOrConfirm(elReg, region);
        }
      });
    };
    input.addEventListener('blur', run);
    input.addEventListener('change', run);
  }

  document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('input[data-cp-autofill]').forEach(attach);
  });
})();
