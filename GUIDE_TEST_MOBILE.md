# 🧪 Guide de Test Mobile - Checklist UX

## 📱 Tester avec Chrome DevTools

### 1. Ouvrir les DevTools Mobile
```
1. Ouvrir Chrome → http://127.0.0.1:5000
2. Appuyer sur F12
3. Cliquer sur l'icône "Toggle device toolbar" (Ctrl+Shift+M)
4. Sélectionner un appareil dans la liste déroulante
```

---

## 📐 Appareils à Tester

### iPhone SE (375 x 667)
- ✅ Plus petit écran iOS courant
- ✅ Teste le breakpoint 400px
- **Navigation** : Header empilé, liens verticaux
- **Cards** : 1 colonne unique
- **Formulaires** : Inputs 16px (pas de zoom)

### iPhone 12/13/14 (390 x 844)
- ✅ Standard iOS moderne
- ✅ Teste le breakpoint 600px
- **Pagination** : Boutons 40x40px minimum
- **Boutons CTA** : 44x44px tactile
- **Images** : Max 300px, object-fit cover

### Galaxy S20 / Pixel 5 (360 x 800)
- ✅ Standard Android
- ✅ Teste le breakpoint 600px
- **Header** : Brand 1rem, nav empilée
- **Sidebar** : Positionné en haut (order: -1)
- **Forms** : Grid-2 → 1 colonne

### iPad Mini (768 x 1024)
- ✅ Tablette portrait
- ✅ Teste le breakpoint 768px
- **Cards** : minmax(260px, 1fr)
- **Navigation** : Verticale < 768px
- **Container** : 96% de largeur

---

## ✅ Checklist par Page

### 🏠 Page d'accueil `/`

#### Desktop (> 960px)
- [ ] Header horizontal avec logo + navigation
- [ ] Sidebar à gauche, cards à droite
- [ ] Grid cards 3-4 colonnes
- [ ] Pagination centrée horizontale

#### Tablette (768px - 960px)
- [ ] Sidebar passe au-dessus des cards
- [ ] Cards en 2-3 colonnes
- [ ] Header commence à s'empiler

#### Mobile (< 768px)
- [ ] **Header complètement empilé**
  - [ ] Logo centré ou aligné gauche
  - [ ] Navigation en colonne (chaque lien = 1 ligne)
  - [ ] Bordures autour des liens
- [ ] **Sidebar en haut** (order: -1)
- [ ] **Cards 1 colonne** (< 600px)
- [ ] **Pagination wrap** avec gap 6px
- [ ] **Boutons minimum 44px** de hauteur

---

### 🎭 Page Spectacle Enfants `/spectacles-enfants`

#### Tests Mobile
- [ ] Titre H1 lisible (1.1rem < 768px)
- [ ] Filtres accessibles (categorie, location)
- [ ] Cards empilées verticalement
- [ ] Images ne débordent pas (max 300px)
- [ ] Badges lisibles (0.7rem si < 400px)

---

### 📝 Formulaire Demande `/demande-animation`

#### Desktop (> 700px)
- [ ] Grid-2 : 2 colonnes (Nom/Prénom, Email/Tél...)

#### Mobile (< 700px)
- [ ] **Grid-2 transformé en 1 colonne**
  - [ ] Nom sur 1 ligne
  - [ ] Prénom sur 1 ligne
  - [ ] Email sur 1 ligne
  - [ ] Téléphone sur 1 ligne
- [ ] **Inputs font-size 16px** (pas de zoom iOS)
- [ ] **Textarea min-height 120px**
- [ ] **Bouton submit pleine largeur** (width: 100%)
- [ ] **Bouton min-height 48px** (tactile)
- [ ] Padding des inputs 12px
- [ ] Wrap à 98% (pas de débordement)

---

### 🔍 Test Détail Spectacle `/spectacle/1`

#### Tests Mobile
- [ ] Image principale responsive
- [ ] Bouton "Booker cet artiste" pleine largeur mobile
- [ ] Bouton min 44px hauteur
- [ ] Description lisible sans zoom horizontal
- [ ] Badges responsive
- [ ] Pas de débordement sur petit écran

---

### 🔐 Login/Register

#### Mobile
- [ ] Formulaire 1 colonne
- [ ] Inputs 16px font-size
- [ ] Boutons pleine largeur
- [ ] Liens "Mot de passe oublié" accessibles (44px)

---

## 🎯 Points Critiques à Vérifier

### 1. Navigation Tactile
```
❌ ÉCHOUE SI :
- Liens < 44px de hauteur
- Navigation horizontale déborde
- Impossible de scroller

✅ RÉUSSI SI :
- Tous liens > 44x44px
- Navigation verticale < 768px
- Bordures visibles autour des liens
```

### 2. Formulaires iOS
```
❌ ÉCHOUE SI :
- Input font-size < 16px → Zoom involontaire iOS
- Select font-size < 16px → Zoom involontaire
- Bouton submit < 44px hauteur

✅ RÉUSSI SI :
- Tous inputs 16px minimum
- Padding 12px confortable
- Bouton submit pleine largeur mobile
```

### 3. Cards & Images
```
❌ ÉCHOUE SI :
- Images débordent sur petit écran
- Cards en 2 colonnes serrées < 600px
- Texte coupé ou non lisible

✅ RÉUSSI SI :
- 1 colonne unique < 600px
- Images max 300px avec object-fit
- Texte lisible sans zoom
```

### 4. Pagination
```
❌ ÉCHOUE SI :
- Boutons pagination trop petits (< 40px)
- Débordement horizontal
- Pas de wrap sur petit écran

✅ RÉUSSI SI :
- Boutons 40x40px minimum
- Flex-wrap avec gap 6px
- Pagination centrée
```

---

## 🔬 Tests Spécifiques

### Test 1 : Zoom Involontaire iOS
```
1. Ouvrir /demande-animation sur iPhone SE
2. Taper dans le champ "Email"
3. Vérifier : PAS DE ZOOM automatique

✅ RÉUSSI si font-size = 16px
❌ ÉCHOUE si font-size < 16px → zoom automatique
```

### Test 2 : Touch Targets
```
1. Ouvrir / sur Galaxy S20
2. Essayer de cliquer sur TOUS les boutons avec le doigt
3. Vérifier : Clic précis sans manquer

✅ RÉUSSI si min 44x44px partout
❌ ÉCHOUE si boutons trop petits
```

### Test 3 : Débordement Horizontal
```
1. Ouvrir toutes les pages sur iPhone SE (375px)
2. Vérifier : AUCUN scroll horizontal

✅ RÉUSSI si container 96-98% max
❌ ÉCHOUE si scroll horizontal visible
```

### Test 4 : Responsive Breakpoints
```
1. Ouvrir Chrome DevTools
2. Mode Responsive
3. Redimensionner de 320px à 1200px lentement
4. Vérifier : Transitions fluides aux breakpoints

Breakpoints :
- 400px : Body 14px, H1 1rem
- 600px : Cards 1 colonne, grid-2 → 1
- 700px : Demande form 1 colonne
- 768px : Header empilé, nav verticale
- 960px : Sidebar au-dessus
```

---

## 📊 Lighthouse Mobile Audit

### Lancer Lighthouse
```
1. Ouvrir Chrome DevTools (F12)
2. Onglet "Lighthouse"
3. Cocher "Mobile"
4. Décocher "Desktop"
5. Categories : Performance, Accessibility, SEO
6. Cliquer "Analyze page load"
```

### Scores Attendus
- **Performance** : > 85/100
- **Accessibility** : > 90/100 (touch targets, contrast)
- **Best Practices** : > 90/100
- **SEO** : > 95/100 (mobile-friendly)

---

## 🐛 Problèmes Courants

### Problème : Zoom iOS sur Focus Input
**Cause** : font-size < 16px sur input/select
**Solution** : Vérifier static/css/style.css ligne 194-196
```css
.demande-form input,
.demande-form select {
  font-size: 16px; /* ← DOIT être 16px minimum */
}
```

### Problème : Scroll Horizontal
**Cause** : Élément plus large que viewport
**Solution** : Vérifier container width en %
```css
.container { width: min(1540px, 94%); } /* Desktop */
@media (max-width: 600px) {
  .demande-wrap { width: 98%; } /* Mobile */
}
```

### Problème : Boutons Trop Petits
**Cause** : height < 44px
**Solution** : Vérifier ligne 716-720
```css
a, button {
  min-height: 44px;
  min-width: 44px;
}
```

---

## ✨ Validation Finale

### ✅ Tous les tests passés si :
1. Aucun zoom involontaire iOS sur focus input
2. Tous boutons/liens > 44x44px
3. Aucun scroll horizontal sur iPhone SE (375px)
4. Cards 1 colonne < 600px
5. Header empilé < 768px
6. Formulaires 1 colonne < 700px
7. Navigation verticale mobile accessible
8. Images ne débordent pas (max 300px)

### 🎉 Site 100% Mobile-Friendly !

---

## 📸 Screenshots Recommandés

Prendre des captures d'écran pour documentation :
1. iPhone SE - Page d'accueil
2. iPhone SE - Formulaire demande
3. Galaxy S20 - Détail spectacle
4. iPad Mini - Navigation
5. Lighthouse Mobile Score

---

**Date** : 2026-01-05
**Version** : 1.0
**Status** : ✅ Prêt pour tests mobiles
