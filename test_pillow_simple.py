"""
Test simple de Pillow et WebP
"""
from PIL import Image
from io import BytesIO

print("=" * 60)
print("🧪 TEST PILLOW & WEBP")
print("=" * 60)

# 1. Créer une image
print("\n1. Création image test...")
img = Image.new('RGB', (800, 600), color=(255, 100, 100))
print(f"   ✅ Image créée : {img.size}")

# 2. Sauver en JPEG
print("\n2. Conversion JPEG...")
jpeg_buffer = BytesIO()
img.save(jpeg_buffer, format='JPEG', quality=90)
jpeg_size = jpeg_buffer.getbuffer().nbytes
print(f"   ✅ JPEG : {jpeg_size/1024:.1f} KB")

# 3. Sauver en WebP
print("\n3. Conversion WebP...")
webp_buffer = BytesIO()
img.save(webp_buffer, format='WebP', quality=85)
webp_size = webp_buffer.getbuffer().nbytes
reduction = ((jpeg_size - webp_size) / jpeg_size) * 100
print(f"   ✅ WebP : {webp_size/1024:.1f} KB")
print(f"   ✅ Réduction : -{reduction:.1f}%")

# 4. Vérifier format
webp_buffer.seek(0)
img_webp = Image.open(webp_buffer)
print(f"\n4. Vérification format : {img_webp.format}")

if img_webp.format == 'WEBP':
    print("\n🎉 SUCCÈS : Pillow supporte WebP correctement !")
else:
    print("\n❌ ERREUR : Format incorrect")

print("=" * 60)
