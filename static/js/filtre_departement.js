// Liste des départements limitée à la région choisie (recherche des appels d'offres)
(function () {
  var selectRegion = document.querySelector('select[name="region"]');
  var selectDept = document.querySelector('select[name="departement"]');
  if (!selectRegion || !selectDept || !selectDept.dataset.departementsParRegion) return;

  var parRegion = JSON.parse(selectDept.dataset.departementsParRegion);
  selectRegion.addEventListener('change', function () {
    var choix = parRegion[selectRegion.value] || parRegion[''];
    var actuel = selectDept.value;
    selectDept.innerHTML = '';
    selectDept.add(new Option('Tous les départements', ''));
    choix.forEach(function (c) {
      selectDept.add(new Option(c[1], c[0], false, c[0] === actuel));
    });
  });
})();
