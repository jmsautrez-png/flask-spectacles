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
        return unique_name
    except Exception as e:
        current_app.logger.error(f"[LOCAL] Erreur sauvegarde: {e}")
        raise Exception(f"Impossible de sauvegarder le fichier : {e}")


upload_file_local = upload_file_to_s3
