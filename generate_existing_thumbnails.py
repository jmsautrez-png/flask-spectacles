"""
Script one-shot : génère les thumbnails pour toutes les images existantes sur S3.
À exécuter en local (pas sur Render) : python generate_existing_thumbnails.py

Traite les images une par une pour limiter la mémoire.
"""
import os
import sys
from io import BytesIO

try:
    import boto3
    from PIL import Image
except ImportError:
    print("Installez boto3 et Pillow : pip install boto3 Pillow")
    sys.exit(1)

# --- Configuration S3 (depuis les variables d'environnement) ---
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_KEY = os.environ.get("S3_KEY") or os.environ.get("AWS_ACCESS_KEY_ID")
S3_SECRET = os.environ.get("S3_SECRET") or os.environ.get("AWS_SECRET_ACCESS_KEY")
S3_REGION = os.environ.get("S3_REGION", "eu-west-3")

if not all([S3_BUCKET, S3_KEY, S3_SECRET]):
    print("Variables d'environnement requises : S3_BUCKET, S3_KEY, S3_SECRET")
    print("Exemple : S3_BUCKET=monbucket S3_KEY=xxx S3_SECRET=yyy python generate_existing_thumbnails.py")
    sys.exit(1)

THUMB_SIZE = (400, 300)
QUALITY = 80
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp")

Image.MAX_IMAGE_PIXELS = 10_000_000

s3 = boto3.client(
    "s3",
    region_name=S3_REGION,
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET,
)


def list_all_keys():
    """Liste toutes les clés du bucket S3."""
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys


def thumb_exists(thumb_key):
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=thumb_key)
        return True
    except Exception:
        return False


def generate_thumb(key):
    """Télécharge l'image, génère le thumbnail, upload sur S3."""
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=key)
        data = response["Body"].read()

        img = Image.open(BytesIO(data))
        img = img.convert("RGB")
        img.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)

        output = BytesIO()
        img.save(output, "WEBP", quality=QUALITY)
        img.close()
        del data  # Libérer la mémoire de l'original
        output.seek(0)

        thumb_key = "thumb_" + key.rsplit(".", 1)[0] + ".webp"
        s3.upload_fileobj(
            output, S3_BUCKET, thumb_key,
            ExtraArgs={"ContentType": "image/webp"}
        )
        return thumb_key
    except Exception as e:
        print(f"  ERREUR {key}: {e}")
        return None


def main():
    print(f"Bucket: {S3_BUCKET}")
    print(f"Région: {S3_REGION}")
    print("Listage des fichiers S3...")

    all_keys = list_all_keys()
    image_keys = [k for k in all_keys if any(k.lower().endswith(ext) for ext in IMAGE_EXTS)
                  and not k.startswith("thumb_")]

    print(f"Total fichiers: {len(all_keys)}")
    print(f"Images (sans thumbs): {len(image_keys)}")

    created = 0
    skipped = 0
    errors = 0

    for i, key in enumerate(image_keys, 1):
        thumb_key = "thumb_" + key.rsplit(".", 1)[0] + ".webp"
        if thumb_exists(thumb_key):
            skipped += 1
            print(f"  [{i}/{len(image_keys)}] SKIP {key} (thumb existe)")
            continue

        result = generate_thumb(key)
        if result:
            created += 1
            print(f"  [{i}/{len(image_keys)}] OK   {key} → {result}")
        else:
            errors += 1

    print(f"\nTerminé! Créés: {created}, Ignorés: {skipped}, Erreurs: {errors}")


if __name__ == "__main__":
    main()
