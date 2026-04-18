import os
from PIL import Image

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '../instance/uploads')
THUMB_DIR = os.path.join(os.path.dirname(__file__), '../instance/thumbnails')
THUMB_SIZE = (400, 300)

os.makedirs(THUMB_DIR, exist_ok=True)

for fname in os.listdir(UPLOAD_DIR):
    if not fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        continue
    src = os.path.join(UPLOAD_DIR, fname)
    dst = os.path.join(THUMB_DIR, fname.rsplit('.', 1)[0] + '.webp')
    try:
        with Image.open(src) as img:
            img = img.convert('RGB')
            img.thumbnail(THUMB_SIZE, Image.LANCZOS)
            img.save(dst, 'WEBP', quality=80)
            print(f'Thumbnail créé : {dst}')
    except Exception as e:
        print(f'Erreur {fname}: {e}')
