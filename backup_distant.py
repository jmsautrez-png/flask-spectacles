"""
Backup distant : PostgreSQL (Render) + photos S3 -> dossier local (Dropbox).

Usage :
    python backup_distant.py

Configuration : variables d'environnement (depuis .env) :
    DATABASE_URL          (postgresql://user:pass@host:port/dbname)
    S3_BUCKET, S3_KEY, S3_SECRET, S3_REGION
    BACKUP_DIR            (optionnel, défaut: C:\\Users\\utilisateur\\Dropbox\\site spectaclemant distant)

Prérequis :
    - pg_dump installé (PostgreSQL client tools)  -> https://www.postgresql.org/download/windows/
      Vérifier : pg_dump --version
    - boto3 (déjà dans requirements.txt)
"""
from __future__ import annotations

import os
import sys
import time
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("[ERREUR] boto3 manquant. Installez : pip install boto3")
    sys.exit(1)


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DEFAULT_BACKUP_DIR = r"C:\Users\utilisateur\Dropbox\site spectaclemant distant"
BACKUP_DIR = Path(os.environ.get("BACKUP_DIR", DEFAULT_BACKUP_DIR))

DATABASE_URL = os.environ.get("DATABASE_URL", "").replace("postgres://", "postgresql://", 1)
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_KEY = os.environ.get("S3_KEY") or os.environ.get("AWS_ACCESS_KEY_ID")
S3_SECRET = os.environ.get("S3_SECRET") or os.environ.get("AWS_SECRET_ACCESS_KEY")
S3_REGION = os.environ.get("S3_REGION") or os.environ.get("AWS_REGION", "eu-west-3")

DATE_TAG = datetime.now().strftime("%Y-%m-%d_%H-%M")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def ensure_dirs() -> tuple[Path, Path, Path]:
    """Cree l'arborescence de backup.

    - photos/ : dossier MUTUALISE a la racine de BACKUP_DIR (incremental, miroir du bucket S3).
    - database/<DATE_TAG>/db_*.dump : un sous-dossier date par execution pour les dumps DB.
    """
    base = BACKUP_DIR
    db_dir = base / "database" / DATE_TAG
    photos_dir = base / "photos"  # miroir partage, pas date
    db_dir.mkdir(parents=True, exist_ok=True)
    photos_dir.mkdir(parents=True, exist_ok=True)
    return base, db_dir, photos_dir


# ----------------------------------------------------------------------
# 1) Backup PostgreSQL
# ----------------------------------------------------------------------
def find_pg_dump() -> str | None:
    """Cherche pg_dump dans le PATH, puis dans C:\\Program Files\\PostgreSQL\\<version>\\bin
    en privilegiant la version la plus recente (compatibilite serveur)."""
    # 1) PATH
    in_path = shutil.which("pg_dump")
    candidates = []
    # 2) Installations Windows standard
    pg_root = Path(r"C:\Program Files\PostgreSQL")
    if pg_root.exists():
        for d in pg_root.iterdir():
            exe = d / "bin" / "pg_dump.exe"
            if exe.exists() and d.name.isdigit():
                candidates.append((int(d.name), str(exe)))
    # Trie par numero de version decroissant
    candidates.sort(reverse=True)
    if candidates:
        return candidates[0][1]
    return in_path


def backup_database(db_dir: Path) -> bool:
    if not DATABASE_URL:
        log("⚠ DATABASE_URL non définie -> skip backup DB.")
        return False

    pg_dump_exe = find_pg_dump()
    if not pg_dump_exe:
        log("✗ pg_dump introuvable dans le PATH ni dans C:\\Program Files\\PostgreSQL\\.")
        log("  Installez PostgreSQL client : https://www.postgresql.org/download/windows/")
        log("  IMPORTANT : choisissez la même version majeure que le serveur (Render = PG 18).")
        return False

    log(f"  pg_dump utilisé : {pg_dump_exe}")
    out_file = db_dir / f"db_{DATE_TAG}.dump"
    log(f"→ pg_dump vers {out_file.name} ...")

    # Format custom (-Fc) : compressé, restaurable avec pg_restore
    cmd = [
        pg_dump_exe,
        "--dbname", DATABASE_URL,
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--file", str(out_file),
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        size_mb = out_file.stat().st_size / (1024 * 1024)
        log(f"✓ DB sauvegardée : {out_file.name} ({size_mb:.2f} MB)")
        if result.stderr:
            log(f"  (info pg_dump) {result.stderr.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        log(f"✗ pg_dump a échoué : {e.stderr or e}")
        return False


# ----------------------------------------------------------------------
# 2) Backup photos S3
# ----------------------------------------------------------------------
def backup_s3(photos_dir: Path) -> bool:
    if not all([S3_BUCKET, S3_KEY, S3_SECRET]):
        log("⚠ Variables S3 incomplètes (S3_BUCKET / S3_KEY / S3_SECRET) -> skip photos.")
        return False

    log(f"→ Téléchargement S3 bucket '{S3_BUCKET}' (région {S3_REGION}) ...")
    s3 = boto3.client(
        "s3",
        aws_access_key_id=S3_KEY,
        aws_secret_access_key=S3_SECRET,
        region_name=S3_REGION,
    )

    paginator = s3.get_paginator("list_objects_v2")
    total, downloaded, skipped, errors = 0, 0, 0, 0
    total_bytes = 0

    try:
        for page in paginator.paginate(Bucket=S3_BUCKET):
            for obj in page.get("Contents", []) or []:
                total += 1
                key = obj["Key"]
                size = obj["Size"]
                # Reproduit la hiérarchie des "dossiers" S3 sur le disque
                local_path = photos_dir / key.replace("/", os.sep)
                local_path.parent.mkdir(parents=True, exist_ok=True)

                # Skip si déjà présent avec même taille (incrémental simple)
                if local_path.exists() and local_path.stat().st_size == size:
                    skipped += 1
                    continue

                # Retry pour contourner Dropbox qui verrouille les fichiers pendant la sync
                last_err = None
                for attempt in range(5):
                    try:
                        s3.download_file(S3_BUCKET, key, str(local_path))
                        downloaded += 1
                        total_bytes += size
                        if downloaded % 50 == 0:
                            log(f"  ... {downloaded} fichiers téléchargés")
                        last_err = None
                        break
                    except PermissionError as e:
                        last_err = e
                        time.sleep(0.5 * (attempt + 1))
                    except ClientError as e:
                        last_err = e
                        break
                if last_err is not None:
                    errors += 1
                    log(f"  ✗ {key} : {last_err}")
    except ClientError as e:
        log(f"✗ Erreur S3 (accès au bucket) : {e}")
        return False

    mb = total_bytes / (1024 * 1024)
    log(f"✓ S3 terminé : {downloaded} téléchargés ({mb:.2f} MB), "
        f"{skipped} déjà à jour, {errors} erreurs (total objets bucket : {total})")
    return errors == 0


# ----------------------------------------------------------------------
# 3) Nettoyage des vieux backups (garde les N derniers)
# ----------------------------------------------------------------------
def cleanup_old_backups(keep: int = 14) -> None:
    """Garde les `keep` dumps de DB datés les plus récents, supprime les plus anciens.
    Le dossier `photos/` mutualisé n'est jamais supprimé."""
    db_root = BACKUP_DIR / "database"
    if not db_root.exists():
        return
    backups = sorted(
        [d for d in db_root.iterdir() if d.is_dir() and len(d.name) >= 10],
        key=lambda p: p.name,
        reverse=True,
    )
    for old in backups[keep:]:
        log(f"  🗑 Suppression ancien dump DB : {old.name}")
        shutil.rmtree(old, ignore_errors=True)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main() -> int:
    log("=" * 60)
    log(f"BACKUP DISTANT -> {BACKUP_DIR}")
    log("=" * 60)

    if not BACKUP_DIR.parent.exists():
        log(f"✗ Le dossier parent n'existe pas : {BACKUP_DIR.parent}")
        log("  Vérifiez que Dropbox est bien installé / le chemin est correct.")
        return 1

    base, db_dir, photos_dir = ensure_dirs()
    log(f"Dossier de cette session : {base}")

    ok_db = backup_database(db_dir)
    ok_s3 = backup_s3(photos_dir)

    cleanup_old_backups(keep=14)

    log("=" * 60)
    if ok_db and ok_s3:
        log("✅ BACKUP TERMINÉ AVEC SUCCÈS")
        return 0
    log("⚠ BACKUP TERMINÉ AVEC AVERTISSEMENTS (voir lignes ci-dessus)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
