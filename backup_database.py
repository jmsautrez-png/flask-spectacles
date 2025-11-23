#!/usr/bin/env python3
"""
Script de backup automatique de la base de données
Utilisation: python backup_database.py
"""
import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_database():
    """Crée une sauvegarde de la base de données SQLite"""
    
    # Chemins
    db_path = Path("instance/app.db")
    backup_dir = Path("backups")
    
    # Créer le dossier de backup s'il n'existe pas
    backup_dir.mkdir(exist_ok=True)
    
    # Vérifier que la base existe
    if not db_path.exists():
        print(f"❌ Base de données introuvable: {db_path}")
        return False
    
    # Nom du backup avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_app_{timestamp}.db"
    backup_path = backup_dir / backup_filename
    
    try:
        # Copier la base de données
        shutil.copy2(db_path, backup_path)
        
        # Taille du fichier
        size_mb = backup_path.stat().st_size / (1024 * 1024)
        
        print(f"✅ Backup créé avec succès!")
        print(f"   Fichier: {backup_path}")
        print(f"   Taille: {size_mb:.2f} MB")
        
        # Nettoyer les anciens backups (garder seulement les 10 derniers)
        cleanup_old_backups(backup_dir, keep=10)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du backup: {e}")
        return False

def cleanup_old_backups(backup_dir: Path, keep: int = 10):
    """Supprime les anciens backups en gardant seulement les N derniers"""
    
    # Lister tous les fichiers de backup
    backups = sorted(
        backup_dir.glob("backup_app_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    # Supprimer les anciens
    for old_backup in backups[keep:]:
        try:
            old_backup.unlink()
            print(f"🗑️  Ancien backup supprimé: {old_backup.name}")
        except Exception as e:
            print(f"⚠️  Impossible de supprimer {old_backup.name}: {e}")

def restore_database(backup_file: str):
    """Restaure une base de données depuis un backup"""
    
    backup_path = Path(backup_file)
    db_path = Path("instance/app.db")
    
    if not backup_path.exists():
        print(f"❌ Fichier de backup introuvable: {backup_path}")
        return False
    
    try:
        # Créer une sauvegarde de sécurité de l'actuelle
        if db_path.exists():
            safety_backup = db_path.with_suffix(".db.before_restore")
            shutil.copy2(db_path, safety_backup)
            print(f"💾 Backup de sécurité créé: {safety_backup}")
        
        # Restaurer
        shutil.copy2(backup_path, db_path)
        print(f"✅ Base de données restaurée depuis: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la restauration: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Mode restauration
        if sys.argv[1] == "--restore" and len(sys.argv) > 2:
            restore_database(sys.argv[2])
        else:
            print("Usage:")
            print("  Backup:     python backup_database.py")
            print("  Restaurer:  python backup_database.py --restore backups/backup_app_YYYYMMDD_HHMMSS.db")
    else:
        # Mode backup par défaut
        backup_database()
