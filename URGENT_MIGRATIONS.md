# 🚨 URGENT - Migrations SQL à exécuter MAINTENANT

L'application est déployée mais les migrations ne sont pas appliquées.
**L'application ne fonctionnera pas tant que ces commandes ne seront pas exécutées.**

## 1️⃣ Connectez-vous à votre base de données

### Via Render Dashboard
1. Allez sur https://dashboard.render.com
2. Cliquez sur votre service PostgreSQL (base de données)
3. Cliquez sur **"Connect"** → **"External Connection"**
4. Copiez la commande `psql`

### Via le service web
1. Cliquez sur votre service web
2. Cliquez sur **"Shell"** dans le menu

## 2️⃣ Exécutez ces commandes SQL

```sql
-- Migration 1: Colonne is_private
ALTER TABLE demande_animation ADD COLUMN IF NOT EXISTS is_private BOOLEAN DEFAULT FALSE;

-- Migration 2: Colonne email
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- Migration 3: Colonne created_at
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Migration 4: Extension location (peut prendre 5-10 secondes)
ALTER TABLE shows ALTER COLUMN location TYPE VARCHAR(500);

-- Migration 5: Extension category (peut prendre 5-10 secondes)
ALTER TABLE shows ALTER COLUMN category TYPE VARCHAR(500);
```

## 3️⃣ Vérifiez que les colonnes existent

```sql
-- Vérifier users
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'users' AND column_name IN ('email', 'created_at');

-- Vérifier demande_animation
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'demande_animation' AND column_name = 'is_private';

-- Vérifier shows
SELECT column_name, character_maximum_length FROM information_schema.columns 
WHERE table_name = 'shows' AND column_name IN ('location', 'category');
```

Résultats attendus :
- `users` → 2 lignes (email, created_at)
- `demande_animation` → 1 ligne (is_private)
- `shows` → 2 lignes avec `character_maximum_length = 500`

## 4️⃣ Redémarrez l'application

- Via Render Dashboard : **Manual Deploy** → **Clear build cache & deploy**
- Ou attendez quelques secondes (Render redémarre automatiquement)

## ⏱️ Temps total estimé : 2 minutes

---

## 🆘 Méthode alternative si psql ne fonctionne pas

### Via Python Shell (Render)
```bash
python << 'EOF'
from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE demande_animation ADD COLUMN IF NOT EXISTS is_private BOOLEAN DEFAULT FALSE"))
        db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255)"))
        db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
        db.session.execute(text("ALTER TABLE shows ALTER COLUMN location TYPE VARCHAR(500)"))
        db.session.execute(text("ALTER TABLE shows ALTER COLUMN category TYPE VARCHAR(500)"))
        db.session.commit()
        print("✅ Migrations appliquées avec succès!")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.session.rollback()
EOF
```

---

## ❓ Pourquoi cette erreur ?

Le code a été déployé avec les nouveaux modèles, mais la base de données n'a pas été migrée.
C'est normal - vous devez **toujours** migrer la base de données avant ou juste après le déploiement.

## 📊 État actuel

- ❌ Production : colonnes manquantes → **erreur 500**
- ✅ Local : colonnes présentes → **fonctionne**

Après les migrations :
- ✅ Production : colonnes présentes → **fonctionne** ✨
