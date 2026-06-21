"""
Script para poblar la base de datos con datos de ejemplo.
Ejecutar con: python seed_data.py

Crea:
- 1 usuario admin + 1 usuario customer
- 3 categorías principales + 9 subcategorías
- 20+ productos de tecnología con inventario
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import User, Category, Product, Inventory
from app.utils.security import hash_password
from datetime import datetime


def seed():
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Verificar si ya hay datos
        if db.query(User).first():
            print("⚠️  La base de datos ya tiene datos. Abortando seed.")
            return

        print("[+] Iniciando seed de datos...")

        # =============================================
        # USUARIOS
        # =============================================
        admin = User(
            full_name="Admin Tienda",
            email="admin@tiendatech.com",
            hashed_password=hash_password("admin123"),
            role="admin",
        )
        customer = User(
            full_name="Carlos López",
            email="carlos@email.com",
            hashed_password=hash_password("cliente123"),
            role="customer",
        )
        db.add_all([admin, customer])
        db.flush()
        print("[OK] Usuarios creados (admin@tiendatech.com / admin123, carlos@email.com / cliente123)")

        # =============================================
        # CATEGORÍAS PRINCIPALES
        # =============================================
        cat_laptops = Category(name="Laptops", description="Computadoras portátiles de todas las gamas")
        cat_celulares = Category(name="Celulares", description="Smartphones y teléfonos móviles")
        cat_accesorios = Category(name="Accesorios", description="Accesorios y periféricos de tecnología")
        db.add_all([cat_laptops, cat_celulares, cat_accesorios])
        db.flush()

        # SUBCATEGORÍAS DE LAPTOPS
        sub_gaming = Category(name="Gaming", description="Laptops para gaming de alto rendimiento", parent_id=cat_laptops.id)
        sub_ultrabooks = Category(name="Ultrabooks", description="Laptops ultradelgadas y ligeras", parent_id=cat_laptops.id)
        sub_empresariales = Category(name="Empresariales", description="Laptops para uso profesional y empresarial", parent_id=cat_laptops.id)

        # SUBCATEGORÍAS DE CELULARES
        sub_gama_alta = Category(name="Gama Alta", description="Smartphones premium y flagship", parent_id=cat_celulares.id)
        sub_gama_media = Category(name="Gama Media", description="Smartphones con buena relación calidad-precio", parent_id=cat_celulares.id)
        sub_gama_economica = Category(name="Gama Económica", description="Smartphones accesibles y funcionales", parent_id=cat_celulares.id)

        # SUBCATEGORÍAS DE ACCESORIOS
        sub_audio = Category(name="Audio", description="Audífonos, bocinas y equipos de sonido", parent_id=cat_accesorios.id)
        sub_fundas = Category(name="Fundas y Protectores", description="Fundas, protectores de pantalla y estuches", parent_id=cat_accesorios.id)
        sub_cargadores = Category(name="Cargadores y Cables", description="Cargadores, cables y adaptadores", parent_id=cat_accesorios.id)

        db.add_all([
            sub_gaming, sub_ultrabooks, sub_empresariales,
            sub_gama_alta, sub_gama_media, sub_gama_economica,
            sub_audio, sub_fundas, sub_cargadores,
        ])
        db.flush()
        print("[OK] Categorías creadas (3 principales + 9 subcategorías)")

        # =============================================
        # PRODUCTOS + INVENTARIO
        # =============================================
        products_data = [
            # --- LAPTOPS GAMING ---
            {
                "name": "ASUS ROG Strix G16",
                "sku": "LAP-ASUS-ROG-001",
                "description": "Laptop gaming con Intel Core i9, RTX 4070, 16GB RAM, 1TB SSD, pantalla 16\" 165Hz",
                "price": 34999.99,
                "brand": "ASUS",
                "category_id": sub_gaming.id,
                "stock": 15,
                "min_stock": 3,
            },
            {
                "name": "MSI Katana 15",
                "sku": "LAP-MSI-KAT-001",
                "description": "Laptop gaming con Intel Core i7, RTX 4060, 16GB RAM, 512GB SSD, pantalla 15.6\" 144Hz",
                "price": 22999.99,
                "brand": "MSI",
                "category_id": sub_gaming.id,
                "stock": 20,
                "min_stock": 5,
            },
            {
                "name": "Lenovo Legion 5 Pro",
                "sku": "LAP-LEN-LEG-001",
                "description": "Laptop gaming con AMD Ryzen 7, RTX 4070, 32GB RAM, 1TB SSD, pantalla 16\" 240Hz",
                "price": 38999.99,
                "brand": "Lenovo",
                "category_id": sub_gaming.id,
                "stock": 8,
                "min_stock": 2,
            },
            # --- ULTRABOOKS ---
            {
                "name": "MacBook Air M3",
                "sku": "LAP-APP-MBA-001",
                "description": "MacBook Air con chip M3, 8GB RAM, 256GB SSD, pantalla Liquid Retina 13.6\"",
                "price": 27999.99,
                "brand": "Apple",
                "category_id": sub_ultrabooks.id,
                "stock": 25,
                "min_stock": 5,
            },
            {
                "name": "Dell XPS 13 Plus",
                "sku": "LAP-DEL-XPS-001",
                "description": "Ultrabook con Intel Core Ultra 7, 16GB RAM, 512GB SSD, pantalla OLED 13.4\"",
                "price": 32999.99,
                "brand": "Dell",
                "category_id": sub_ultrabooks.id,
                "stock": 12,
                "min_stock": 3,
            },
            # --- LAPTOPS EMPRESARIALES ---
            {
                "name": "ThinkPad X1 Carbon Gen 12",
                "sku": "LAP-LEN-TPX-001",
                "description": "Laptop empresarial con Intel Core Ultra 7, 16GB RAM, 512GB SSD, pantalla 14\" 2.8K",
                "price": 35999.99,
                "brand": "Lenovo",
                "category_id": sub_empresariales.id,
                "stock": 10,
                "min_stock": 3,
            },
            {
                "name": "HP EliteBook 840 G11",
                "sku": "LAP-HP-ELI-001",
                "description": "Laptop empresarial con Intel Core Ultra 5, 16GB RAM, 256GB SSD, pantalla 14\" FHD",
                "price": 24999.99,
                "brand": "HP",
                "category_id": sub_empresariales.id,
                "stock": 18,
                "min_stock": 5,
            },
            # --- CELULARES GAMA ALTA ---
            {
                "name": "iPhone 16 Pro Max",
                "sku": "CEL-APP-I16-001",
                "description": "iPhone 16 Pro Max 256GB, chip A18 Pro, pantalla Super Retina XDR 6.9\", cámara 48MP",
                "price": 29999.99,
                "brand": "Apple",
                "category_id": sub_gama_alta.id,
                "stock": 30,
                "min_stock": 10,
            },
            {
                "name": "Samsung Galaxy S24 Ultra",
                "sku": "CEL-SAM-S24-001",
                "description": "Galaxy S24 Ultra 256GB, Snapdragon 8 Gen 3, pantalla Dynamic AMOLED 6.8\", S Pen incluido",
                "price": 25999.99,
                "brand": "Samsung",
                "category_id": sub_gama_alta.id,
                "stock": 25,
                "min_stock": 8,
            },
            {
                "name": "Google Pixel 9 Pro",
                "sku": "CEL-GOO-PX9-001",
                "description": "Pixel 9 Pro 128GB, chip Tensor G4, pantalla LTPO OLED 6.3\", cámara con IA avanzada",
                "price": 21999.99,
                "brand": "Google",
                "category_id": sub_gama_alta.id,
                "stock": 15,
                "min_stock": 5,
            },
            # --- CELULARES GAMA MEDIA ---
            {
                "name": "Samsung Galaxy A55",
                "sku": "CEL-SAM-A55-001",
                "description": "Galaxy A55 128GB, Exynos 1480, pantalla Super AMOLED 6.6\", batería 5000mAh",
                "price": 8999.99,
                "brand": "Samsung",
                "category_id": sub_gama_media.id,
                "stock": 40,
                "min_stock": 10,
            },
            {
                "name": "Xiaomi Redmi Note 13 Pro",
                "sku": "CEL-XIA-RN13-001",
                "description": "Redmi Note 13 Pro 256GB, Snapdragon 7s Gen 2, pantalla AMOLED 6.67\", cámara 200MP",
                "price": 6999.99,
                "brand": "Xiaomi",
                "category_id": sub_gama_media.id,
                "stock": 50,
                "min_stock": 15,
            },
            # --- CELULARES GAMA ECONÓMICA ---
            {
                "name": "Motorola Moto G24",
                "sku": "CEL-MOT-G24-001",
                "description": "Moto G24 128GB, Helio G85, pantalla IPS 6.6\", batería 5000mAh, cámara 50MP",
                "price": 3499.99,
                "brand": "Motorola",
                "category_id": sub_gama_economica.id,
                "stock": 60,
                "min_stock": 20,
            },
            {
                "name": "Samsung Galaxy A15",
                "sku": "CEL-SAM-A15-001",
                "description": "Galaxy A15 128GB, Helio G99, pantalla Super AMOLED 6.5\", batería 5000mAh",
                "price": 3999.99,
                "brand": "Samsung",
                "category_id": sub_gama_economica.id,
                "stock": 45,
                "min_stock": 15,
            },
            # --- ACCESORIOS: AUDIO ---
            {
                "name": "AirPods Pro 2",
                "sku": "ACC-APP-APP-001",
                "description": "AirPods Pro 2da gen con USB-C, cancelación activa de ruido, audio espacial adaptativo",
                "price": 5499.99,
                "brand": "Apple",
                "category_id": sub_audio.id,
                "stock": 35,
                "min_stock": 10,
            },
            {
                "name": "Sony WH-1000XM5",
                "sku": "ACC-SON-WH5-001",
                "description": "Audífonos over-ear con cancelación de ruido líder, 30 horas de batería, Bluetooth 5.3",
                "price": 7999.99,
                "brand": "Sony",
                "category_id": sub_audio.id,
                "stock": 20,
                "min_stock": 5,
            },
            {
                "name": "JBL Flip 6",
                "sku": "ACC-JBL-FL6-001",
                "description": "Bocina portátil Bluetooth, resistente al agua IP67, 12 horas de batería, sonido JBL Pro",
                "price": 2499.99,
                "brand": "JBL",
                "category_id": sub_audio.id,
                "stock": 30,
                "min_stock": 8,
            },
            # --- ACCESORIOS: FUNDAS ---
            {
                "name": "Funda OtterBox Defender iPhone 16",
                "sku": "ACC-OTT-DEF-001",
                "description": "Funda ultra resistente para iPhone 16, protección multicapa, compatible con MagSafe",
                "price": 1299.99,
                "brand": "OtterBox",
                "category_id": sub_fundas.id,
                "stock": 50,
                "min_stock": 15,
            },
            {
                "name": "Protector de Pantalla Zagg Galaxy S24",
                "sku": "ACC-ZAG-PRO-001",
                "description": "Protector de pantalla de vidrio templado para Samsung Galaxy S24 Ultra, anti-huellas",
                "price": 599.99,
                "brand": "Zagg",
                "category_id": sub_fundas.id,
                "stock": 80,
                "min_stock": 20,
            },
            # --- ACCESORIOS: CARGADORES ---
            {
                "name": "Cargador Anker 65W USB-C",
                "sku": "ACC-ANK-65W-001",
                "description": "Cargador GaN de 65W con 2 puertos USB-C y 1 USB-A, carga rápida para laptop y celular",
                "price": 899.99,
                "brand": "Anker",
                "category_id": sub_cargadores.id,
                "stock": 40,
                "min_stock": 10,
            },
            {
                "name": "Cable USB-C a USB-C Belkin 2m",
                "sku": "ACC-BEL-CBC-001",
                "description": "Cable USB-C trenzado de 2 metros, USB 3.2, carga rápida 240W, transferencia 20Gbps",
                "price": 449.99,
                "brand": "Belkin",
                "category_id": sub_cargadores.id,
                "stock": 100,
                "min_stock": 25,
            },
        ]

        for p_data in products_data:
            stock = p_data.pop("stock")
            min_stock = p_data.pop("min_stock")

            product = Product(**p_data)
            db.add(product)
            db.flush()

            inv = Inventory(
                product_id=product.id,
                stock=stock,
                min_stock=min_stock,
                last_restock=datetime.utcnow(),
            )
            db.add(inv)

        db.commit()
        print(f"[OK] Productos creados ({len(products_data)} productos con inventario)")

        print("\n[*] Seed completado exitosamente!")
        print("\n[*] Credenciales de prueba:")
        print("   Admin:   admin@tiendatech.com / admin123")
        print("   Cliente: carlos@email.com / cliente123")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error durante el seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
