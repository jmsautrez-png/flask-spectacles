"""File upload, S3 storage, and image optimization utilities."""
from typing import Optional, Tuple
import uuid

from flask import current_app

# Import optionnel de boto3
try:
    import boto3
except ImportError:
    boto3 = None

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}
ALLOWED_MIMETYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"}


def allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def secure_upload_filename(file) -> Tuple[bool, Optional[str], Optional[str]]:
    from werkzeug.utils import secure_filename as werkzeug_secure_filename
    if not file or not file.filename:
        return False, "Aucun fichier fourni", None
    if not allowed_file(file.filename):
        return False, f"Type de fichier non autorisé. Extensions acceptées : {', '.join(ALLOWED_EXTENSIONS)}", None
    safe_name = werkzeug_secure_filename(file.filename)
    if not safe_name or safe_name == '':
        return False, "Nom de fichier invalide", None
    return True, None, safe_name


def validate_file_size(file) -> Tuple[bool, Optional[str]]:
    if not file:
        return True, None
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    max_size = current_app.config.get("MAX_FILE_SIZE", 500 * 1024)
    if file_size > max_size:
        size_mb = file_size / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)
        return False, f"Le fichier est trop volumineux ({size_mb:.2f} MB). Taille maximale autorisée : {max_mb:.0f} MB."
    return True, None


def optimize_image_to_webp(file, quality=85, max_width=1920):
    try:
        from PIL import Image
        from io import BytesIO
        if not file.content_type or not file.content_type.startswith('image/'):
            return None
        if file.content_type == 'application/pdf':
            return None
        file.seek(0)
        Image.MAX_IMAGE_PIXELS = 10_000_000
        img = Image.open(file)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
        output = BytesIO()
        img.save(output, format='WebP', quality=quality, method=6)
        output.seek(0)
        original_size = file.tell() if hasattr(file, 'tell') else 0
        optimized_size = output.getbuffer().nbytes
        if original_size > 0:
            reduction = ((original_size - optimized_size) / original_size) * 100
            current_app.logger.info(f"[WebP] Image optimisée : {original_size/1024:.1f}KB → {optimized_size/1024:.1f}KB (-{reduction:.1f}%)")
        return output
    except Exception as e:
        current_app.logger.warning(f"[WebP] Impossible d'optimiser l'image : {e}")
        file.seek(0)
        return None


def _s3_client():
    s3_bucket = current_app.config.get("S3_BUCKET")
    s3_key = current_app.config.get("S3_KEY")
    s3_secret = current_app.config.get("S3_SECRET")
    s3_region = current_app.config.get("S3_REGION")
    if not (s3_bucket and s3_key and s3_secret and boto3):
        return None
    return boto3.client(
        "s3",
        region_name=s3_region,
        aws_access_key_id=s3_key,
        aws_secret_access_key=s3_secret,
    )


def delete_file_s3(key: str) -> None:
    s3_bucket = current_app.config.get("S3_BUCKET")
    client = _s3_client()
    if not (client and s3_bucket and key):
        return
    try:
        client.delete_object(Bucket=s3_bucket, Key=key)
        current_app.logger.info("[S3] Fichier supprimé: %s", key)
    except Exception as e:
        current_app.logger.warning("[S3] Suppression impossible (%s): %s", key, e)
    # Supprimer aussi le thumbnail associé
    ext = key.rsplit(".", 1)[-1].lower() if "." in key else ""
    if ext in ("png", "jpg", "jpeg", "gif", "webp"):
        thumb_key = "thumb_" + key.rsplit(".", 1)[0] + ".webp"
        try:
            client.delete_object(Bucket=s3_bucket, Key=thumb_key)
        except Exception:
            pass


def upload_file_to_s3(file) -> str:
    from pathlib import Path as _Path
    optimized_file = optimize_image_to_webp(file)
    if optimized_file:
        file_to_upload = optimized_file
        ext = '.webp'
        content_type = 'image/webp'
    else:
        file.seek(0)
        file_to_upload = file
        ext = _Path(file.filename).suffix.lower()
        content_type = file.content_type or "application/octet-stream"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    s3_bucket = current_app.config.get("S3_BUCKET")
    s3_client = _s3_client()
    if s3_client and s3_bucket:
        try:
            s3_client.upload_fileobj(
                file_to_upload, s3_bucket, unique_name,
                ExtraArgs={"ContentType": content_type}
            )
            current_app.logger.info(f"[S3] Fichier uploadé: {unique_name}")
            # Générer le thumbnail à l'upload (évite la génération à la volée)
            if optimized_file:
                try:
                    optimized_file.seek(0)
                    _generate_thumbnail_from_data(
                        optimized_file,
                        "thumb_" + unique_name.rsplit(".", 1)[0] + ".webp"
                    )
                except Exception as e:
                    current_app.logger.warning(f"[THUMB] Erreur thumbnail upload: {e}")
            return unique_name
        except Exception as e:
            current_app.logger.error(f"[S3] Erreur, fallback local: {e}")
            file_to_upload.seek(0)
    file_to_upload.seek(0)
    save_path = _Path(current_app.config["UPLOAD_FOLDER"]) / unique_name
    try:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        if hasattr(file_to_upload, 'save'):
            file_to_upload.save(save_path.as_posix())
        else:
            with open(save_path, 'wb') as f:
                f.write(file_to_upload.getvalue())
        current_app.logger.info(f"[LOCAL] Fichier sauvegardé: {unique_name}")
        # Générer le thumbnail à l'upload
        if optimized_file:
            try:
                optimized_file.seek(0)
                _generate_thumbnail_from_data(
                    optimized_file,
                    "thumb_" + unique_name.rsplit(".", 1)[0] + ".webp"
                )
            except Exception as e:
                current_app.logger.warning(f"[THUMB] Erreur thumbnail local: {e}")
        return unique_name
    except Exception as e:
        current_app.logger.error(f"[LOCAL] Erreur sauvegarde: {e}")
        raise Exception(f"Impossible de sauvegarder le fichier : {e}")


upload_file_local = upload_file_to_s3


def _generate_thumbnail_from_data(image_data, thumb_name, thumb_size=(400, 300), quality=80):
    """Génère un thumbnail depuis des données image en mémoire et le stocke (S3 ou local)."""
    from pathlib import Path as _Path
    from io import BytesIO
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = 10_000_000
        image_data.seek(0)
        img = Image.open(image_data)
        img = img.convert("RGB")
        img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        output = BytesIO()
        img.save(output, "WEBP", quality=quality)
        img.close()
        output.seek(0)

        s3_client = _s3_client()
        s3_bucket = current_app.config.get("S3_BUCKET")
        if s3_client and s3_bucket:
            try:
                s3_client.upload_fileobj(
                    output, s3_bucket, thumb_name,
                    ExtraArgs={"ContentType": "image/webp"}
                )
                current_app.logger.info(f"[THUMB] Thumbnail S3: {thumb_name}")
                return thumb_name
            except Exception as e:
                current_app.logger.warning(f"[THUMB] Erreur upload S3 thumbnail: {e}")
                output.seek(0)

        thumb_dir = _Path(current_app.config.get("THUMBNAIL_FOLDER",
                          _Path(current_app.config["UPLOAD_FOLDER"]).parent / "thumbnails"))
        thumb_dir.mkdir(parents=True, exist_ok=True)
        with open(thumb_dir / thumb_name, 'wb') as f:
            f.write(output.getvalue())
        current_app.logger.info(f"[THUMB] Thumbnail local: {thumb_name}")
        return thumb_name
    except Exception as e:
        current_app.logger.warning(f"[THUMB] Erreur génération thumbnail: {e}")
        return None


def generate_thumbnail(filename, thumb_size=(400, 300), quality=80):
    """Vérifie si un thumbnail existe (local/S3). Génère uniquement depuis fichier local.
    Ne télécharge PAS l'original depuis S3 (évite les pics mémoire)."""
    from pathlib import Path as _Path
    from io import BytesIO

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
        return None

    thumb_name = "thumb_" + filename.rsplit(".", 1)[0] + ".webp"

    # Vérifier cache local
    thumb_dir = _Path(current_app.config.get("THUMBNAIL_FOLDER",
                      _Path(current_app.config["UPLOAD_FOLDER"]).parent / "thumbnails"))
    if (thumb_dir / thumb_name).exists():
        return thumb_name

    # Vérifier S3
    s3_client = _s3_client()
    s3_bucket = current_app.config.get("S3_BUCKET")
    if s3_client and s3_bucket:
        try:
            s3_client.head_object(Bucket=s3_bucket, Key=thumb_name)
            return thumb_name  # Existe sur S3
        except Exception:
            pass

    # Générer uniquement depuis fichier local (pas de download S3 = pas de pic mémoire)
    local_path = _Path(current_app.config["UPLOAD_FOLDER"]) / filename
    if not local_path.exists():
        return None

    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = 10_000_000
        img = Image.open(local_path)
        img_rgb = img.convert("RGB")
        img_rgb.thumbnail(thumb_size, Image.Resampling.LANCZOS)
        output = BytesIO()
        img_rgb.save(output, "WEBP", quality=quality)
        img.close()
        img_rgb.close()
        output.seek(0)

        if s3_client and s3_bucket:
            try:
                s3_client.upload_fileobj(
                    output, s3_bucket, thumb_name,
                    ExtraArgs={"ContentType": "image/webp"}
                )
                current_app.logger.info(f"[THUMB] Thumbnail S3: {thumb_name}")
                return thumb_name
            except Exception:
                output.seek(0)

        thumb_dir.mkdir(parents=True, exist_ok=True)
        with open(thumb_dir / thumb_name, 'wb') as f:
            f.write(output.getvalue())
        current_app.logger.info(f"[THUMB] Thumbnail local: {thumb_name}")
        return thumb_name
    except Exception as e:
        current_app.logger.warning(f"[THUMB] Erreur thumbnail {filename}: {e}")
        return None
