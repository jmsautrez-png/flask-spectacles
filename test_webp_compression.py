"""
Test de la fonction de compression WebP
"""
from app import app
from io import BytesIO
from PIL import Image

print("=" * 70)
print("🧪 TEST COMPRESSION WEBP")
print("=" * 70)

with app.app_context():
    # Créer une image de test
    print("\n1. Création d'une image de test (800x600 JPEG)...")
    img = Image.new('RGB', (800, 600), color=(255, 100, 100))
    
    # Sauvegarder en JPEG dans un BytesIO
    jpeg_buffer = BytesIO()
    img.save(jpeg_buffer, format='JPEG', quality=90)
    jpeg_size = jpeg_buffer.tell()
    jpeg_buffer.seek(0)
    
    print(f"   Taille JPEG originale : {jpeg_size/1024:.1f} KB")
    
    # Créer un objet FileStorage simulé
    class FakeFile:
        def __init__(self, buffer):
            self.buffer = buffer
            self.content_type = 'image/jpeg'
            self.filename = 'test.jpg'
        
        def seek(self, position, whence=0):
            self.buffer.seek(position, whence)
        
        def tell(self):
            return self.buffer.tell()
        
        def read(self):
            return self.buffer.read()
    
    fake_file = FakeFile(jpeg_buffer)
    
    # Tester la compression WebP
    print("\n2. Test de la fonction optimize_image_to_webp()...")
    from app import optimize_image_to_webp
    
    try:
        result = optimize_image_to_webp(fake_file, quality=85, max_width=1920)
        
        if result:
            webp_size = result.getbuffer().nbytes
            reduction = ((jpeg_size - webp_size) / jpeg_size) * 100
            
            print(f"   ✅ Conversion réussie !")
            print(f"   Taille WebP : {webp_size/1024:.1f} KB")
            print(f"   Réduction : -{reduction:.1f}%")
            print(f"   Gain : {(jpeg_size - webp_size)/1024:.1f} KB")
            
            # Vérifier que c'est bien du WebP
            result.seek(0)
            webp_img = Image.open(result)
            print(f"   Format détecté : {webp_img.format}")
            print(f"   Dimensions : {webp_img.size}")
            
            if webp_img.format == 'WEBP':
                print("\n🎉 TEST RÉUSSI : La compression WebP fonctionne parfaitement !")
            else:
                print("\n⚠️  ATTENTION : Le format n'est pas WebP")
        else:
            print("   ❌ La fonction a retourné None")
            
    except Exception as e:
        print(f"   ❌ Erreur lors de la compression : {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
