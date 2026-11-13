
    console.log('✅ Script chargé');

    // Select all matched shows
    const selectAllMatched = document.getElementById('select-all-matched');
    if (selectAllMatched) {
        selectAllMatched.addEventListener('change', function() {
            const checked = this.checked;
            document.querySelectorAll('.matched-cb:not(:disabled)').forEach(cb => {
                cb.checked = checked;
                // Synchronise l'état visuel de la ligne + le compteur.
                cb.dispatchEvent(new Event('change'));
            });
        });
    }
    // Update matched count when individual checkboxes change
    document.querySelectorAll('.matched-cb').forEach(cb => {
        cb.addEventListener('change', updateMatchedCount);
    });
    function updateMatchedCount() {
        const count = document.querySelectorAll('.matched-cb:checked:not(:disabled)').length;
        const el = document.getElementById('matched-count');
        if (el) el.textContent = count;
    }

    // Ligne cliquable + état visuel (vert coché / gris décoché)
    function updateRowState(tr, cb) {
        tr.classList.toggle('row-checked', cb.checked);
    }
    document.querySelectorAll('tr.matched-row').forEach(tr => {
        const cb = tr.querySelector('.matched-cb');
        if (!cb) return;
        updateRowState(tr, cb);
        tr.addEventListener('click', function(e) {
            // Ne pas intercepter les clics sur liens, cases, boutons, labels ou badges avec tooltip
            if (e.target.closest('a, input, label, button, [title]')) return;
            cb.checked = !cb.checked;
            cb.dispatchEvent(new Event('change'));
        });
        cb.addEventListener('change', function() {
            updateRowState(tr, cb);
        });
    });
    
    // Filtre par tranche de distance : les lignes hors tranche sont masquées et désactivées
    // (donc non envoyées), leur coche est conservée. Les lignes sans distance restent visibles.
    const selectDistance = document.getElementById('filtre-distance');
    const tranchesDistance = {
        '1-80': { min: 0, max: 80 },
        '80-140': { min: 80, max: 140 },
        '140-250': { min: 140, max: 250 }
    };
    function appliquerFiltreDistance() {
        const t = tranchesDistance[selectDistance.value];
        document.querySelectorAll('tr.matched-row').forEach(tr => {
            const cb = tr.querySelector('.matched-cb');
            const km = parseFloat(tr.dataset.km);
            const visible = !t || isNaN(km) || ((km > t.min || t.min === 0) && km <= t.max);
            tr.style.display = visible ? '' : 'none';
            cb.disabled = !visible;
        });
        updateMatchedCount();
    }
    if (selectDistance) {
        selectDistance.addEventListener('change', appliquerFiltreDistance);
    }

    // Fonction pour sélectionner/désélectionner toutes les régions
    function selectAllRegions() {
        console.log('Toggle toutes les régions');
        const checkboxes = document.querySelectorAll('.region-checkbox');
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        checkboxes.forEach(cb => cb.checked = !allChecked);
    }
    
    // Validation avant soumission
    document.addEventListener('DOMContentLoaded', function() {
        console.log('✅ DOM chargé');
        
        const form = document.querySelector('form');
        if (!form) {
            console.error('❌ Formulaire non trouvé');
            return;
        }
        
        console.log('✅ Formulaire trouvé, ajout du listener');
        
        form.addEventListener('submit', function(e) {
            console.log('📤 Événement submit déclenché');
            
            // Vérifier le type d'action
            const clickedBtn = e.submitter;
            const action = clickedBtn ? clickedBtn.value : '';
            
            if (action === 'send_matched_recap_only') {
                const matchedChecked = document.querySelectorAll('.matched-cb:checked:not(:disabled)');
                if (matchedChecked.length === 0) {
                    e.preventDefault();
                    alert('⚠️ Cochez au moins une compagnie à inclure dans le récap');
                    return false;
                }
                return true;
            }
            
            if (action === 'send_matched') {
                const matchedChecked = document.querySelectorAll('.matched-cb:checked:not(:disabled)');
                if (matchedChecked.length === 0) {
                    e.preventDefault();
                    alert('⚠️ Veuillez sélectionner au moins une compagnie');
                    return false;
                }
                return true;
            }
            
            console.log('✅ Soumission du formulaire en cours...');
            return true;
        });
        
        // Détection automatique de la région à partir du lieu
        detecterRegion();
    });
    
    // Mapping des villes françaises vers leurs régions
    const villeVersRegion = {
        // Île-de-France
        'paris': 'Île-de-France', 'boulogne-billancourt': 'Île-de-France', 'saint-denis': 'Île-de-France',
        'argenteuil': 'Île-de-France', 'montreuil': 'Île-de-France', 'nanterre': 'Île-de-France',
        'créteil': 'Île-de-France', 'versailles': 'Île-de-France', 'vitry-sur-seine': 'Île-de-France',
        'colombes': 'Île-de-France', 'asnières-sur-seine': 'Île-de-France', 'courbevoie': 'Île-de-France',
        'aulnay-sous-bois': 'Île-de-France', 'rueil-malmaison': 'Île-de-France', 'champigny-sur-marne': 'Île-de-France',
        'aubervilliers': 'Île-de-France', 'drancy': 'Île-de-France', 'noisy-le-grand': 'Île-de-France',
        'levallois-perret': 'Île-de-France', 'issy-les-moulineaux': 'Île-de-France', 'cergy': 'Île-de-France',
        'evry': 'Île-de-France', 'meaux': 'Île-de-France', 'melun': 'Île-de-France', 'pontoise': 'Île-de-France',
        'mantes-la-jolie': 'Île-de-France', 'sartrouville': 'Île-de-France', 'maisons-alfort': 'Île-de-France',
        
        // Auvergne-Rhône-Alpes
        'lyon': 'Auvergne-Rhône-Alpes', 'villeurbanne': 'Auvergne-Rhône-Alpes', 'saint-etienne': 'Auvergne-Rhône-Alpes',
        'grenoble': 'Auvergne-Rhône-Alpes', 'clermont-ferrand': 'Auvergne-Rhône-Alpes', 'annecy': 'Auvergne-Rhône-Alpes',
        'valence': 'Auvergne-Rhône-Alpes', 'chambery': 'Auvergne-Rhône-Alpes', 'bourg-en-bresse': 'Auvergne-Rhône-Alpes',
        'roanne': 'Auvergne-Rhône-Alpes', 'vienne': 'Auvergne-Rhône-Alpes', 'annemasse': 'Auvergne-Rhône-Alpes',
        'thonon-les-bains': 'Auvergne-Rhône-Alpes', 'aurillac': 'Auvergne-Rhône-Alpes', 'le puy-en-velay': 'Auvergne-Rhône-Alpes',
        'montelimar': 'Auvergne-Rhône-Alpes', 'oyonnax': 'Auvergne-Rhône-Alpes', 'albertville': 'Auvergne-Rhône-Alpes',
        
        // Provence-Alpes-Côte d'Azur
        'marseille': "Provence-Alpes-Côte d'Azur", 'nice': "Provence-Alpes-Côte d'Azur", 'toulon': "Provence-Alpes-Côte d'Azur",
        'aix-en-provence': "Provence-Alpes-Côte d'Azur", 'avignon': "Provence-Alpes-Côte d'Azur", 'antibes': "Provence-Alpes-Côte d'Azur",
        'cannes': "Provence-Alpes-Côte d'Azur", 'la seyne-sur-mer': "Provence-Alpes-Côte d'Azur", 'hyeres': "Provence-Alpes-Côte d'Azur",
        'frejus': "Provence-Alpes-Côte d'Azur", 'arles': "Provence-Alpes-Côte d'Azur", 'grasse': "Provence-Alpes-Côte d'Azur",
        'martigues': "Provence-Alpes-Côte d'Azur", 'aubagne': "Provence-Alpes-Côte d'Azur", 'gap': "Provence-Alpes-Côte d'Azur",
        'digne-les-bains': "Provence-Alpes-Côte d'Azur", 'menton': "Provence-Alpes-Côte d'Azur", 'salon-de-provence': "Provence-Alpes-Côte d'Azur",
        
        // Nouvelle-Aquitaine
        'bordeaux': 'Nouvelle-Aquitaine', 'limoges': 'Nouvelle-Aquitaine', 'poitiers': 'Nouvelle-Aquitaine',
        'merignac': 'Nouvelle-Aquitaine', 'pessac': 'Nouvelle-Aquitaine', 'pau': 'Nouvelle-Aquitaine',
        'la rochelle': 'Nouvelle-Aquitaine', 'angouleme': 'Nouvelle-Aquitaine', 'bayonne': 'Nouvelle-Aquitaine',
        'brive-la-gaillarde': 'Nouvelle-Aquitaine', 'niort': 'Nouvelle-Aquitaine', 'perigueux': 'Nouvelle-Aquitaine',
        'agen': 'Nouvelle-Aquitaine', 'mont-de-marsan': 'Nouvelle-Aquitaine', 'biarritz': 'Nouvelle-Aquitaine',
        'arcachon': 'Nouvelle-Aquitaine', 'dax': 'Nouvelle-Aquitaine', 'cognac': 'Nouvelle-Aquitaine',
        
        // Occitanie
        'toulouse': 'Occitanie', 'montpellier': 'Occitanie', 'nimes': 'Occitanie', 'perpignan': 'Occitanie',
        'beziers': 'Occitanie', 'narbonne': 'Occitanie', 'carcassonne': 'Occitanie', 'albi': 'Occitanie',
        'tarbes': 'Occitanie', 'castres': 'Occitanie', 'sete': 'Occitanie', 'montauban': 'Occitanie',
        'ales': 'Occitanie', 'rodez': 'Occitanie', 'cahors': 'Occitanie', 'auch': 'Occitanie',
        'mende': 'Occitanie', 'foix': 'Occitanie', 'lourdes': 'Occitanie', 'millau': 'Occitanie',
        
        // Grand Est
        'strasbourg': 'Grand Est', 'reims': 'Grand Est', 'metz': 'Grand Est', 'mulhouse': 'Grand Est',
        'nancy': 'Grand Est', 'colmar': 'Grand Est', 'troyes': 'Grand Est', 'charleville-mezieres': 'Grand Est',
        'chalons-en-champagne': 'Grand Est', 'epinal': 'Grand Est', 'thionville': 'Grand Est', 'haguenau': 'Grand Est',
        'saint-dizier': 'Grand Est', 'bar-le-duc': 'Grand Est', 'verdun': 'Grand Est', 'sedan': 'Grand Est',
        
        // Hauts-de-France
        'lille': 'Hauts-de-France', 'amiens': 'Hauts-de-France', 'roubaix': 'Hauts-de-France',
        'dunkerque': 'Hauts-de-France', 'tourcoing': 'Hauts-de-France', 'calais': 'Hauts-de-France',
        'douai': 'Hauts-de-France', 'lens': 'Hauts-de-France', 'valenciennes': 'Hauts-de-France',
        'beauvais': 'Hauts-de-France', 'arras': 'Hauts-de-France', 'saint-quentin': 'Hauts-de-France',
        'compiegne': 'Hauts-de-France', 'boulogne-sur-mer': 'Hauts-de-France', 'laon': 'Hauts-de-France',
        'soissons': 'Hauts-de-France', 'cambrai': 'Hauts-de-France', 'bethune': 'Hauts-de-France',
        
        // Pays de la Loire
        'nantes': 'Pays de la Loire', 'angers': 'Pays de la Loire', 'le mans': 'Pays de la Loire',
        'saint-nazaire': 'Pays de la Loire', 'la roche-sur-yon': 'Pays de la Loire', 'cholet': 'Pays de la Loire',
        'laval': 'Pays de la Loire', 'saumur': 'Pays de la Loire', 'les sables-d\'olonne': 'Pays de la Loire',
        
        // Bretagne
        'rennes': 'Bretagne', 'brest': 'Bretagne', 'quimper': 'Bretagne', 'lorient': 'Bretagne',
        'vannes': 'Bretagne', 'saint-brieuc': 'Bretagne', 'saint-malo': 'Bretagne', 'lanester': 'Bretagne',
        'fougeres': 'Bretagne', 'concarneau': 'Bretagne', 'morlaix': 'Bretagne', 'lannion': 'Bretagne',
        
        // Normandie
        'le havre': 'Normandie', 'rouen': 'Normandie', 'caen': 'Normandie', 'cherbourg': 'Normandie',
        'evreux': 'Normandie', 'dieppe': 'Normandie', 'alencon': 'Normandie', 'lisieux': 'Normandie',
        'saint-lo': 'Normandie', 'argentan': 'Normandie', 'granville': 'Normandie', 'honfleur': 'Normandie',
        'deauville': 'Normandie', 'fecamp': 'Normandie', 'vernon': 'Normandie',
        
        // Centre-Val de Loire
        'tours': 'Centre-Val de Loire', 'orleans': 'Centre-Val de Loire', 'bourges': 'Centre-Val de Loire',
        'blois': 'Centre-Val de Loire', 'chartres': 'Centre-Val de Loire', 'chateauroux': 'Centre-Val de Loire',
        'joue-les-tours': 'Centre-Val de Loire', 'dreux': 'Centre-Val de Loire', 'vierzon': 'Centre-Val de Loire',
        'montargis': 'Centre-Val de Loire', 'amboise': 'Centre-Val de Loire', 'chinon': 'Centre-Val de Loire',
        
        // Bourgogne-Franche-Comté
        'dijon': 'Bourgogne-Franche-Comté', 'besancon': 'Bourgogne-Franche-Comté', 'belfort': 'Bourgogne-Franche-Comté',
        'chalon-sur-saone': 'Bourgogne-Franche-Comté', 'auxerre': 'Bourgogne-Franche-Comté', 'nevers': 'Bourgogne-Franche-Comté',
        'macon': 'Bourgogne-Franche-Comté', 'montbeliard': 'Bourgogne-Franche-Comté', 'sens': 'Bourgogne-Franche-Comté',
        'le creusot': 'Bourgogne-Franche-Comté', 'dole': 'Bourgogne-Franche-Comté', 'lons-le-saunier': 'Bourgogne-Franche-Comté',
        'vesoul': 'Bourgogne-Franche-Comté', 'beaune': 'Bourgogne-Franche-Comté',
        
        // Corse
        'ajaccio': 'Corse', 'bastia': 'Corse', 'porto-vecchio': 'Corse', 'corte': 'Corse',
        'calvi': 'Corse', 'bonifacio': 'Corse', 'propriano': 'Corse',
        
        // DOM-TOM
        'fort-de-france': 'Martinique', 'le lamentin': 'Martinique', 'pointe-a-pitre': 'Guadeloupe',
        'les abymes': 'Guadeloupe', 'cayenne': 'Guyane', 'saint-denis': 'La Réunion',
        'saint-pierre': 'La Réunion', 'le port': 'La Réunion', 'mamoudzou': 'Mayotte'
    };
    
    function normaliserTexte(texte) {
        return texte.toLowerCase()
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .replace(/[^a-z\s-]/g, '')
            .trim();
    }
    
    function detecterRegion() {
        const lieu = "{{ demande.lieu_ville }}";
        const lieuNormalise = normaliserTexte(lieu);
        const badge = document.getElementById('region-detectee');
        
        // Chercher une correspondance directe
        if (villeVersRegion[lieuNormalise]) {
            badge.textContent = '🗺️ Région suggérée : ' + villeVersRegion[lieuNormalise];
            badge.style.display = 'inline';
            // Pré-cocher la région correspondante
            precocherRegion(villeVersRegion[lieuNormalise]);
            return;
        }
        
        // Chercher une correspondance partielle
        for (const [ville, region] of Object.entries(villeVersRegion)) {
            if (lieuNormalise.includes(ville) || ville.includes(lieuNormalise)) {
                badge.textContent = '🗺️ Région suggérée : ' + region;
                badge.style.display = 'inline';
                precocherRegion(region);
                return;
            }
        }
        
        // Vérifier si le lieu contient directement un nom de région
        const regions = ['ile-de-france', 'auvergne-rhone-alpes', 'provence-alpes-cote d\'azur', 
            'nouvelle-aquitaine', 'occitanie', 'grand est', 'hauts-de-france', 'pays de la loire',
            'bretagne', 'normandie', 'centre-val de loire', 'bourgogne-franche-comte', 'corse',
            'guadeloupe', 'martinique', 'guyane', 'la reunion', 'mayotte'];
        
        for (const reg of regions) {
            if (lieuNormalise.includes(reg)) {
                badge.textContent = '🗺️ Région détectée : ' + reg.charAt(0).toUpperCase() + reg.slice(1);
                badge.style.display = 'inline';
                return;
            }
        }
        
        badge.textContent = '⚠️ Région non détectée automatiquement';
        badge.className = 'badge bg-warning text-dark ms-2';
        badge.style.display = 'inline';
    }
    
    function precocherRegion(regionName) {
        // Chercher la checkbox correspondant à cette région et la pré-cocher
        const checkboxes = document.querySelectorAll('.region-checkbox');
        checkboxes.forEach(cb => {
            if (cb.value.toLowerCase().includes(regionName.toLowerCase()) || 
                regionName.toLowerCase().includes(cb.value.toLowerCase())) {
                cb.checked = true;
                cb.parentElement.style.background = '#d4edda';
                cb.parentElement.style.borderRadius = '4px';
                cb.parentElement.style.padding = '2px 6px';
            }
        });
    }
