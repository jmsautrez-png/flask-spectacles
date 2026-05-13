// Initialise TinyMCE sur tous les <textarea data-richtext>.
// Synchronise la valeur (textarea) à chaque frappe pour conserver les
// scripts existants (compteurs SEO, validations) qui lisent textarea.value.
(function(){
  if (typeof tinymce === 'undefined') return;
  document.addEventListener('DOMContentLoaded', function(){
    if (!document.querySelector('textarea[data-richtext]')) return;
    tinymce.init({
      selector: 'textarea[data-richtext]',
      license_key: 'gpl',
      menubar: false,
      branding: false,
      promotion: false,
      height: 320,
      language: 'fr_FR',
      language_url: 'https://cdn.jsdelivr.net/npm/tinymce-i18n@25.7.7/langs7/fr_FR.js',
      plugins: 'lists link autolink',
      toolbar:
        'undo redo | blocks | ' +
        'bold italic underline | bullist numlist | ' +
        'alignleft aligncenter alignright | ' +
        'link removeformat | pastetext',
      block_formats: 'Paragraphe=p; Titre=h2; Sous-titre=h3',
      paste_block_drop: false,
      paste_data_images: false,
      paste_remove_styles_if_webkit: true,
      paste_webkit_styles: 'none',
      smart_paste: true,
      browser_spellcheck: true,
      contextmenu: 'link copy paste',
      content_style:
        'body{font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#222;background:#fff;}' +
        'p{margin:0 0 8px 0;}',
      setup: function(editor){
        editor.on('init Change KeyUp Undo Redo SetContent', function(){
          // Synchronise la <textarea> sous-jacente
          editor.save();
          // Déclenche un évènement input pour les compteurs existants
          var ta = editor.getElement();
          if (ta) ta.dispatchEvent(new Event('input', { bubbles: true }));
        });
        editor.on('init', function(){
          prefillIfEmpty(editor);
        });
      },
    });
  });

  // ===== Pré-remplissage : titre + ville + dpt + région =====
  function getVal(form, names){
    if (!form) return '';
    for (var i = 0; i < names.length; i++){
      var el = form.querySelector('[name="' + names[i] + '"]');
      if (el && el.value && el.value.trim()) return el.value.trim();
    }
    return '';
  }

  function getField(ta, form, dataKey, names){
    // 1) data-prefill-* sur le textarea (admin : champs hors du form principal)
    if (ta && ta.dataset && ta.dataset[dataKey] && ta.dataset[dataKey].trim()){
      return ta.dataset[dataKey].trim();
    }
    // 2) recherche dans le form du textarea
    return getVal(form, names);
  }

  function buildPrefill(ta, form){
    var title = getField(ta, form, 'prefillTitle',       ['title', 'titre']);
    var city  = getField(ta, form, 'prefillVille',       ['ville', 'location', 'lieu_ville']);
    var dept  = getField(ta, form, 'prefillDepartement', ['departement']);
    var reg   = getField(ta, form, 'prefillRegion',      ['region']);
    if (!title && !city && !reg) return '';

    // Extrait le code (ex: "69") depuis "Rhône (69)" si possible
    var deptCode = '';
    var deptName = dept;
    var m = dept && dept.match(/^(.+?)\s*\((\d{2,3}[AB]?)\)\s*$/i);
    if (m){ deptName = m[1].trim(); deptCode = m[2]; }

    var titleHtml = title ? '« <strong>' + escapeHtml(title) + '</strong> »' : 'Ce spectacle';
    var locParts = [];
    if (city){
      var cityStr = '<strong>' + escapeHtml(city) + '</strong>';
      if (deptCode) cityStr += ' (' + escapeHtml(deptName) + ', ' + escapeHtml(deptCode) + ')';
      else if (deptName) cityStr += ' (' + escapeHtml(deptName) + ')';
      locParts.push('à ' + cityStr);
    }
    if (reg){
      locParts.push('dans toute la région <strong>' + escapeHtml(reg) + '</strong>');
    }

    var sentence;
    if (locParts.length){
      sentence = titleHtml + ' est un spectacle disponible ' + locParts.join(' et ') + '.';
    } else {
      sentence = titleHtml + ' —';
    }
    return '<p>' + sentence + '</p><p><em style="color:#888;">[Rédigez ici la suite : durée, public, ambiance…]</em></p>';
  }

  function escapeHtml(s){
    return String(s).replace(/[&<>"]/g, function(c){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];
    });
  }

  function prefillIfEmpty(editor){
    var current = (editor.getContent({format:'text'}) || '').trim();
    if (current) return; // description déjà remplie : on ne touche pas
    var ta = editor.getElement();
    var form = ta ? ta.form : null;
    var html = buildPrefill(ta, form);
    if (html) editor.setContent(html);
  }
})();
