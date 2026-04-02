from django.db import models
from django.utils.text import slugify
from django.conf import settings
from user.models import CustomUser
from django.utils import timezone
from datetime import timedelta


# ──────────────────────────────────────────────
# Kategoriya
# ──────────────────────────────────────────────
class Category(models.Model):
    """Mahsulot toifasi — har biriga o'z atribut modeli bog'langan"""

    class CategoryType(models.TextChoices):
        PHONE = "phone", "📱 Telefon"
        TV = "tv", "📺 Televizor"
        LAPTOP = "laptop", "💻 Noutbuk"
        CLOTHING = "clothing", "👕 Kiyim"
        SHOES = "shoes", "👟 Oyoq kiyim"
        APPLIANCE = "appliance", "🏠 Maishiy texnika"
        AUTO = "auto", "🚗 Avtomobil"
        FOOD = "food", "🍎 Oziq-ovqat"
        FURNITURE = "furniture", "🪑 Mebel"
        BOOK = "book", "📚 Kitob"
        HOBBY = "hobby", "🎮 O'yin va Hobbi"
        OTHER = "other", "🔧 Boshqa"

    name = models.CharField(max_length=128)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        to='self',
    )
    category_type = models.CharField(
        max_length=20,
        choices=CategoryType.choices,
        default=CategoryType.OTHER,
        help_text="Toifa turi — mahsulotga qanday atribut maydonlari kerakligini aniqlaydi",
    )
    icon = models.ImageField(upload_to="categories/", blank=True)
    description = models.TextField(max_length=512, blank=True)
    is_active = models.BooleanField(default=True)
    order_num = models.PositiveIntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ──────────────────────────────────────────────
# Brand / Brend
# ──────────────────────────────────────────────
class Brand(models.Model):
    """Mahsulot brendi (Samsung, Adidas, Artel ...)"""
    name = models.CharField(max_length=128, unique=True)
    logo = models.ImageField(upload_to="brands/", blank=True)

    class Meta:
        verbose_name = "Brend"
        verbose_name_plural = "Brendlar"

    def __str__(self):
        return self.name


# ──────────────────────────────────────────────
# Rang
# ──────────────────────────────────────────────
class Color(models.Model):
    """Mahsulot ranglari"""
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, blank=True)

    class Meta:
        verbose_name = "Rang"
        verbose_name_plural = "Ranglar"

    def __str__(self):
        return self.name


# ──────────────────────────────────────────────
# Asosiy mahsulot
# ──────────────────────────────────────────────
class Product(models.Model):
    def default_expire():
        return timezone.now() + timedelta(days=30)


    class Status(models.TextChoices):
        MODERATION = "moderation", "Moderatsiyada"
        ACTIVE = "active", "Aktiv"
        REJECTED = "rejected", "Rad etilgan"
        SOLD = "sold", "Sotilgan"
        ARCHIVED = "archived", "Arxivlangan"

    # ── Asosiy ma'lumotlar ──
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")

    title = models.CharField(max_length=200)
    description = models.TextField()

    price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text="Soliq foizi (masalan 10.00 = 10%)",
    )


    # ── Statistika ──
    view_count = models.PositiveIntegerField(default=0)
    favorite_count = models.PositiveIntegerField(default=0)

    # ── Holat ──
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.MODERATION)

    # ── Sanalar ──
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(default=default_expire)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def tax_amount(self):
        from decimal import Decimal
        return (self.price * self.tax_percent / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def price_with_tax(self):
        return self.price + self.tax_amount


# ══════════════════════════════════════════════
#  ATRIBUTLAR — har bir kategoriya uchun alohida
# ══════════════════════════════════════════════

# ── 📱 Telefon ──
class PhoneAttribute(models.Model):
    class OS(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"
        OTHER = "other", "Boshqa"

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="phone_attr")
    model_name = models.CharField(max_length=200, blank=True, help_text="Model: iPhone 15 Pro, Samsung S24...")
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    storage_gb = models.PositiveIntegerField(null=True, blank=True, help_text="Ichki xotira (GB)")
    ram_gb = models.PositiveIntegerField(null=True, blank=True, help_text="RAM (GB)")
    battery_mah = models.PositiveIntegerField(null=True, blank=True, help_text="Batareya (mAh)")
    screen_size = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Ekran (dyuym)")
    os = models.CharField(max_length=10, choices=OS.choices, blank=True)
    sim_count = models.PositiveSmallIntegerField(null=True, blank=True, help_text="SIM karta soni")
    camera_mp = models.PositiveIntegerField(null=True, blank=True, help_text="Kamera (MP)")

    class Meta:
        verbose_name = "Telefon atributi"
        verbose_name_plural = "Telefon atributlari"

    def __str__(self):
        return f"{self.product.title} — {self.model_name}"


# ── 📺 Televizor ──
class TVAttribute(models.Model):
    class Resolution(models.TextChoices):
        HD = "hd", "HD (720p)"
        FHD = "fhd", "Full HD (1080p)"
        QHD = "qhd", "2K (1440p)"
        UHD = "uhd", "4K (2160p)"
        UHD8K = "8k", "8K"

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="tv_attr")
    model_name = models.CharField(max_length=200, blank=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    screen_size = models.PositiveIntegerField(null=True, blank=True, help_text="Ekran (dyuym)")
    resolution = models.CharField(max_length=5, choices=Resolution.choices, blank=True)
    is_smart = models.BooleanField(default=False, help_text="Smart TV")
    refresh_rate = models.PositiveIntegerField(null=True, blank=True, help_text="Yangilanish tezligi (Hz)")
    warranty_months = models.PositiveIntegerField(null=True, blank=True, help_text="Kafolat (oy)")

    class Meta:
        verbose_name = "TV atributi"
        verbose_name_plural = "TV atributlari"

    def __str__(self):
        return f"{self.product.title} — {self.model_name}"


# ── 💻 Noutbuk ──
class LaptopAttribute(models.Model):
    class OS(models.TextChoices):
        WINDOWS = "windows", "Windows"
        MACOS = "macos", "macOS"
        LINUX = "linux", "Linux"
        OTHER = "other", "Boshqa"

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="laptop_attr")
    model_name = models.CharField(max_length=200, blank=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    processor = models.CharField(max_length=100, blank=True, help_text="Protsessor: Intel i7, Apple M2...")
    ram_gb = models.PositiveIntegerField(null=True, blank=True, help_text="RAM (GB)")
    storage_gb = models.PositiveIntegerField(null=True, blank=True, help_text="Xotira (GB)")
    storage_type = models.CharField(max_length=10, blank=True, choices=[("ssd", "SSD"), ("hdd", "HDD"), ("emmc", "eMMC")])
    screen_size = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="Ekran (dyuym)")
    battery_hours = models.PositiveIntegerField(null=True, blank=True, help_text="Batareya (soat)")
    os = models.CharField(max_length=10, choices=OS.choices, blank=True)
    warranty_months = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Noutbuk atributi"
        verbose_name_plural = "Noutbuk atributlari"

    def __str__(self):
        return f"{self.product.title} — {self.model_name}"


# ── 👕 Kiyim ──
class ClothingAttribute(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Erkak"
        FEMALE = "female", "Ayol"
        UNISEX = "unisex", "Uniseks"
        KIDS = "kids", "Bolalar"

    class ClothingSize(models.TextChoices):
        XS = "XS", "XS"
        S = "S", "S"
        M = "M", "M"
        L = "L", "L"
        XL = "XL", "XL"
        XXL = "XXL", "XXL"
        XXXL = "XXXL", "XXXL"

    class Season(models.TextChoices):
        WINTER = "winter", "Qishki"
        SUMMER = "summer", "Yozgi"
        SPRING = "spring", "Bahorgi"
        AUTUMN = "autumn", "Kuzgi"
        ALL = "all", "Barcha mavsumlar"

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="clothing_attr")
    available_sizes = models.JSONField(
        default=list, blank=True,
        help_text='Mavjud razmerlar ro\'yxati, masalan: ["S", "M", "L", "XL"]',
    )
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    material = models.CharField(max_length=100, blank=True, help_text="paxta, teri, sintetik ...")
    season = models.CharField(max_length=10, choices=Season.choices, blank=True)

    class Meta:
        verbose_name = "Kiyim atributi"
        verbose_name_plural = "Kiyim atributlari"

    def __str__(self):
        sizes = ", ".join(self.available_sizes) if self.available_sizes else "—"
        return f"{self.product.title} — {sizes}"


# ── 👟 Oyoq kiyim ──
class ShoesAttribute(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Erkak"
        FEMALE = "female", "Ayol"
        UNISEX = "unisex", "Uniseks"
        KIDS = "kids", "Bolalar"

    class Season(models.TextChoices):
        WINTER = "winter", "Qishki"
        SUMMER = "summer", "Yozgi"
        SPRING = "spring", "Bahorgi"
        AUTUMN = "autumn", "Kuzgi"
        ALL = "all", "Barcha mavsumlar"

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="shoes_attr")
    available_sizes = models.JSONField(
        default=list, blank=True,
        help_text='Mavjud razmerlar ro\'yxati, masalan: [36, 37, 38, 39, 40]',
    )
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    material = models.CharField(max_length=100, blank=True, help_text="teri, zamsha, tekstil...")
    season = models.CharField(max_length=10, choices=Season.choices, blank=True)

    class Meta:
        verbose_name = "Oyoq kiyim atributi"
        verbose_name_plural = "Oyoq kiyim atributlari"

    def __str__(self):
        sizes = ", ".join(str(s) for s in self.available_sizes) if self.available_sizes else "—"
        return f"{self.product.title} — {sizes}"


# ── 🏠 Maishiy texnika ──
class ApplianceAttribute(models.Model):
    class EnergyClass(models.TextChoices):
        A_PLUS_PLUS_PLUS = "a+++", "A+++"
        A_PLUS_PLUS = "a++", "A++"
        A_PLUS = "a+", "A+"
        A = "a", "A"
        B = "b", "B"
        C = "c", "C"

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="appliance_attr")
    model_name = models.CharField(max_length=200, blank=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    power_watt = models.PositiveIntegerField(null=True, blank=True, help_text="Quvvat (Vt)")
    energy_class = models.CharField(max_length=5, choices=EnergyClass.choices, blank=True)
    warranty_months = models.PositiveIntegerField(null=True, blank=True, help_text="Kafolat (oy)")
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Og'irligi (kg)")
    dimensions = models.CharField(max_length=100, blank=True, help_text="O'lcham: 60x60x85 sm")

    class Meta:
        verbose_name = "Maishiy texnika atributi"
        verbose_name_plural = "Maishiy texnika atributlari"

    def __str__(self):
        return f"{self.product.title} — {self.model_name}"


# ── 🚗 Avtomobil ──
class AutoAttribute(models.Model):
    class FuelType(models.TextChoices):
        PETROL = "petrol", "Benzin"
        DIESEL = "diesel", "Dizel"
        GAS = "gas", "Gaz"
        ELECTRIC = "electric", "Elektr"
        HYBRID = "hybrid", "Gibrid"

    class Transmission(models.TextChoices):
        MANUAL = "manual", "Mexanika"
        AUTOMATIC = "automatic", "Avtomat"
        ROBOT = "robot", "Robot"
        CVT = "cvt", "Variator"

    class DriveType(models.TextChoices):
        FRONT = "front", "Oldi"
        REAR = "rear", "Orqa"
        AWD = "awd", "To'liq"

    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="auto_attr")
    make = models.CharField(max_length=100, blank=True, help_text="Marka: Chevrolet, Toyota...")
    model_name = models.CharField(max_length=100, blank=True, help_text="Model: Malibu, Camry...")
    year = models.PositiveIntegerField(null=True, blank=True, help_text="Ishlab chiqarilgan yil")
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    fuel_type = models.CharField(max_length=10, choices=FuelType.choices, blank=True)
    transmission = models.CharField(max_length=10, choices=Transmission.choices, blank=True)
    drive_type = models.CharField(max_length=5, choices=DriveType.choices, blank=True)
    mileage_km = models.PositiveIntegerField(null=True, blank=True, help_text="Probeg (km)")
    engine_cc = models.PositiveIntegerField(null=True, blank=True, help_text="Motor hajmi (cc)")

    class Meta:
        verbose_name = "Avtomobil atributi"
        verbose_name_plural = "Avtomobil atributlari"

    def __str__(self):
        return f"{self.product.title} — {self.make} {self.model_name}"


# ── 🍎 Oziq-ovqat ──
class FoodAttribute(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="food_attr")
    expiry_date = models.DateField(null=True, blank=True, help_text="Yaroqlilik muddati")
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weight_unit = models.CharField(
        max_length=5, default="kg",
        choices=[("g", "gramm"), ("kg", "kilogramm"), ("l", "litr"), ("ml", "millilitr")],
    )
    is_organic = models.BooleanField(default=False, help_text="Organik mahsulotmi?")
    ingredients = models.TextField(blank=True, help_text="Tarkibi")
    storage_info = models.CharField(max_length=200, blank=True, help_text="Saqlash sharoiti")

    class Meta:
        verbose_name = "Oziq-ovqat atributi"
        verbose_name_plural = "Oziq-ovqat atributlari"

    def __str__(self):
        return f"{self.product.title} — {self.weight}{self.weight_unit}"


# ── 🪑 Mebel ──
class FurnitureAttribute(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="furniture_attr")
    material = models.CharField(max_length=100, blank=True, help_text="yog'och, metall, plastik...")
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    dimensions = models.CharField(max_length=100, blank=True, help_text="O'lcham: 120x60x75 sm")
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    warranty_months = models.PositiveIntegerField(null=True, blank=True, help_text="Kafolat (oy)")

    class Meta:
        verbose_name = "Mebel atributi"
        verbose_name_plural = "Mebel atributlari"

    def __str__(self):
        return f"{self.product.title} — mebel"


# ── 📚 Kitob ──
class BookAttribute(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="book_attr")
    author = models.CharField(max_length=200, blank=True, help_text="Muallif")
    publisher = models.CharField(max_length=200, blank=True, help_text="Nashriyot")
    language = models.CharField(max_length=50, blank=True, help_text="Til: O'zbek, Rus, Ingliz...")
    pages = models.PositiveIntegerField(null=True, blank=True, help_text="Sahifalar soni")
    isbn = models.CharField(max_length=20, blank=True, help_text="ISBN raqami")
    genre = models.CharField(max_length=100, blank=True, help_text="Janr: fantastika, tarix...")

    class Meta:
        verbose_name = "Kitob atributi"
        verbose_name_plural = "Kitob atributlari"

    def __str__(self):
        return f"{self.product.title} — {self.author}"


# ── 🎮 O'yin va Hobbi ──
class HobbyAttribute(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="hobby_attr")
    hobby_type = models.CharField(max_length=100, blank=True, help_text="Turi: o'yinchoq, sport, musiqa...")
    age_min = models.PositiveIntegerField(null=True, blank=True, help_text="Minimal yosh")
    age_max = models.PositiveIntegerField(null=True, blank=True, help_text="Maksimal yosh")
    material = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Hobbi atributi"
        verbose_name_plural = "Hobbi atributlari"

    def __str__(self):
        return f"{self.product.title} — {self.hobby_type}"


# ── 🔧 Boshqa ──
class OtherAttribute(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="other_attr")
    material = models.CharField(max_length=100, blank=True)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    warranty_months = models.PositiveIntegerField(null=True, blank=True, help_text="Kafolat (oy)")

    class Meta:
        verbose_name = "Boshqa atribut"
        verbose_name_plural = "Boshqa atributlar"

    def __str__(self):
        return f"{self.product.title} — boshqa"


# ──────────────────────────────────────────────
# Mahsulot rasmlari
# ──────────────────────────────────────────────
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    order = models.PositiveIntegerField()
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mahsulot rasmi"
        verbose_name_plural = "Mahsulot rasmlari"
        ordering = ["-is_main", "order"]

    def __str__(self):
        return f"{self.product.title} — rasm #{self.order}"

    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)


# ──────────────────────────────────────────────
# Sevimli (Favorite)
# ──────────────────────────────────────────────
class Favorite(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="favorites")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "product"]
        verbose_name = "Sevimli"
        verbose_name_plural = "Sevimlilar"

    def __str__(self):
        return f"{self.user} → {self.product.title}"


# ──────────────────────────────────────────────
# Tahrirlash kutish (Pending Edit)
# ──────────────────────────────────────────────
class PendingProductEdit(models.Model):
    """
    Sotuvchi mahsulotni tahrirlasa — o'zgarishlar shu yerda saqlanadi.
    Admin Telegramda tasdiqlasa → product ga apply bo'ladi.
    Rad etsa → o'chiriladi, product eski holda qoladi.
    """
    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name="pending_edit"
    )
    changes_json = models.JSONField(
        help_text="O'zgartirilgan maydonlar: {field: {old: ..., new: ...}}"
    )
    previous_status = models.CharField(
        max_length=20,
        help_text="Tahrirlashdan oldingi holat (tasdiqlanganda qaytariladi)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kutilayotgan tahrir"
        verbose_name_plural = "Kutilayotgan tahrirlar"

    def __str__(self):
        return f"Tahrir — {self.product.title} (#{self.product.id})"