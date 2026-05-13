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
      plugins: 'lists link autolink paste',
      toolbar:
        'undo redo | blocks | ' +
        'bold italic underline | bullist numlist | ' +
        'alignleft aligncenter alignright | ' +
        'link removeformat',
      block_formats: 'Paragraphe=p; Titre=h2; Sous-titre=h3',
      paste_as_text: false,
      paste_data_images: false,
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
      },
    });
  });
})();
