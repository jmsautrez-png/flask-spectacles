"""
Migration des images existantes vers le format WebP
Convertit toutes les photos JPG/PNG en WebP pour optimiser le stockage et les performances.
"""

import os
import sys
from pathlib import Path
from io import BytesIO
from PIL import Image
from app import app, db
from models.models import Show

def convert_image_to_webp(input_path, quality=85, max_width=1920):
    """
    Convertit une image locale en WebP.
    
    Args:
        input_path: Chemin du fichier image
        quality: Qualité WebP (0-100)
        max_width: Largeur maximale
    
    Returns:
        BytesIO contenant l'image WebP, ou None si erreur
    """
    try:
        # Ouvrir l'image
        img = Image.open(input_path)
        
        # Convertir en RGB si nécessaire (pour PNG avec transparence)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionner si nécessaire
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Convertir en WebP
        output = BytesIO()
        img.save(output, format='WEBP', quality=quality, method=6)
        output.seek(0)
        
        return output
        
    except Exception as e:
        print(f"❌ Erreur conversion {input_path}: {e}")
        return None


def migrate_local_storage():
    """
    Migre les images du stockage local (instance/uploads).
    """
    uploads_dir = Path("instance/uploads")
    
    if not uploads_dir.exists():
        print("⚠️  Dossier instance/uploads introuvable")
        return
    
    print(f"📂 Dossier uploads: {uploads_dir.absolute()}")
    
    with app.app_context():
        # Récupérer tous les spectacles
        shows = Show.query.all()
        total_shows = len(shows)
        print(f"📊 {total_shows} spectacles à vérifier\n")
        
        converted_count = 0
        skipped_count = 0
        error_count = 0
        
        for idx, show in enumerate(shows, 1):
            print(f"[{idx}/{total_shows}] Spectacle #{show.id}: {show.title}")
            
            # Traiter les 3 photos possibles
            for photo_num in range(1, 4):
                if photo_num == 1:
                    file_name_attr = 'file_name'
                    mime_attr = 'file_mimetype'
                else:
                    file_name_attr = f'file_name{photo_num}'
                    mime_attr = f'file_mimetype{photo_num}'
                
                file_name = getattr(show, file_name_attr)
                
                # Vérifier si une photo existe
                if not file_name:
                    continue
                
                # Vérifier si c'est déjà en WebP
                if file_name.lower().endswith('.webp'):
                    print(f"  ✓ Photo {photo_num} déjà en WebP: {file_name}")
                    skipped_count += 1
                    continue
                
                # Vérifier si c'est une image à convertir
                ext = file_name.rsplit('.', 1)[-1].lower()
                if ext not in ('jpg', 'jpeg', 'png', 'gif'):
                    print(f"  ⊘ Photo {photo_num} non convertible ({ext}): {file_name}")
                    skipped_count += 1
                    continue
                
                # Chemin du fichier
                file_path = uploads_dir / file_name
                
                if not file_path.exists():
                    print(f"  ⚠️  Fichier introuvable: {file_name}")
                    error_count += 1
                    continue
                
                # Taille originale
                original_size = file_path.stat().st_size
                
                # Convertir en WebP
                webp_data = convert_image_to_webp(file_path)
                
                if not webp_data:
                    print(f"  ❌ Échec conversion: {file_name}")
                    error_count += 1
                    continue
                
                # Nouveau nom de fichier
                new_file_name = file_name.rsplit('.', 1)[0] + '.webp'
                new_file_path = uploads_dir / new_file_name
                
                # Sauvegarder le fichier WebP
                with open(new_file_path, 'wb') as f:
                    f.write(webp_data.read())
                
                new_size = new_file_path.stat().st_size
                reduction = ((original_size - new_size) / original_size) * 100
                
                print(f"  ✅ Photo {photo_num} convertie: {file_name} → {new_file_name}")
                print(f"     Taille: {original_size:,} → {new_size:,} bytes ({reduction:.1f}% de réduction)")
                
                # Mettre à jour la base de données
                setattr(show, file_name_attr, new_file_name)
                setattr(show, mime_attr, 'image/webp')
                
                # Supprimer l'ancien fichier
                try:
                    file_path.unlink()
                    print(f"     🗑️  Ancien fichier supprimé")
                except Exception as e:
                    print(f"     ⚠️  Erreur suppression ancien fichier: {e}")
                
                converted_count += 1
            
            # Sauvegarder les modifications après chaque spectacle
            db.session.commit()
            print()
        
        # Résumé
        print("=" * 60)
        print("📊 RÉSUMÉ DE LA MIGRATION")
        print("=" * 60)
        print(f"✅ Images converties: {converted_count}")
        print(f"⊘  Images ignorées: {skipped_count}")
        print(f"❌ Erreurs: {error_count}")
        print(f"📁 Total spectacles traités: {total_shows}")


def migrate_s3_storage():
    """
    Migre les images du stockage S3 (à implémenter si nécessaire).
    """
    print("⚠️  Migration S3 non implémentée dans cette version")
    print("   Les images S3 seront converties lors du prochain re-upload")


if __name__ == "__main__":
    print("=" * 60)
    print("🔄 MIGRATION DES IMAGES VERS WEBP")
    print("=" * 60)
    print()
    
    # Vérifier Pillow
    try:
        from PIL import Image
        print("✅ Pillow (PIL) installé")
    except ImportError:
        print("❌ Pillow non installé!")
        print("   Installez-le avec: pip install Pillow")
        sys.exit(1)
    
    print()
    
    # Question de confirmation
    response = input("⚠️  Cette opération va convertir toutes les images JPG/PNG en WebP.\n   Voulez-vous continuer? (oui/non): ")
    
    if response.lower() not in ('oui', 'o', 'yes', 'y'):
        print("❌ Migration annulée")
        sys.exit(0)
    
    print()
    
    # Démarrer la migration
    migrate_local_storage()
    
    print()
    print("✅ Migration terminée!")
