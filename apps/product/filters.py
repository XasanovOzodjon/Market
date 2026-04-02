import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):

    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    # Brend bo'yicha filter
    brand = django_filters.NumberFilter(field_name="brand_id")

    # ── 📱 Telefon ──
    phone_os = django_filters.CharFilter(field_name="phone_attr__os")
    phone_storage = django_filters.NumberFilter(field_name="phone_attr__storage_gb")
    phone_ram = django_filters.NumberFilter(field_name="phone_attr__ram_gb")

    # ── 📺 TV ──
    tv_resolution = django_filters.CharFilter(field_name="tv_attr__resolution")
    tv_smart = django_filters.BooleanFilter(field_name="tv_attr__is_smart")

    # ── 💻 Noutbuk ──
    laptop_os = django_filters.CharFilter(field_name="laptop_attr__os")
    laptop_ram = django_filters.NumberFilter(field_name="laptop_attr__ram_gb")
    laptop_storage_type = django_filters.CharFilter(field_name="laptop_attr__storage_type")

    # ── 👕 Kiyim ──
    clothing_size = django_filters.CharFilter(field_name="clothing_attr__available_sizes", lookup_expr="contains")
    clothing_gender = django_filters.CharFilter(field_name="clothing_attr__gender")
    clothing_season = django_filters.CharFilter(field_name="clothing_attr__season")
    clothing_color = django_filters.NumberFilter(field_name="clothing_attr__color_id")

    # ── 👟 Oyoq kiyim ──
    shoes_size = django_filters.NumberFilter(field_name="shoes_attr__available_sizes", lookup_expr="contains")
    shoes_gender = django_filters.CharFilter(field_name="shoes_attr__gender")
    shoes_season = django_filters.CharFilter(field_name="shoes_attr__season")

    # ── 🏠 Maishiy texnika ──
    appliance_energy = django_filters.CharFilter(field_name="appliance_attr__energy_class")

    # ── 🚗 Avtomobil ──
    auto_fuel = django_filters.CharFilter(field_name="auto_attr__fuel_type")
    auto_transmission = django_filters.CharFilter(field_name="auto_attr__transmission")
    auto_year_min = django_filters.NumberFilter(field_name="auto_attr__year", lookup_expr="gte")
    auto_year_max = django_filters.NumberFilter(field_name="auto_attr__year", lookup_expr="lte")
    auto_mileage_max = django_filters.NumberFilter(field_name="auto_attr__mileage_km", lookup_expr="lte")

    # ── 🍎 Oziq-ovqat ──
    is_organic = django_filters.BooleanFilter(field_name="food_attr__is_organic")

    # ── 📚 Kitob ──
    book_language = django_filters.CharFilter(field_name="book_attr__language")
    book_genre = django_filters.CharFilter(field_name="book_attr__genre", lookup_expr="icontains")

    class Meta:
        model = Product
        fields = [
            "category",
            "category__category_type",
            "brand",
        ]