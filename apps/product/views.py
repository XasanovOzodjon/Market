import logging
from django.shortcuts import get_object_or_404
from django.db import models

import json
from decimal import Decimal

logger = logging.getLogger(__name__)

from .models import Product, ProductImage, Favorite, Category, Brand, Color, PendingProductEdit
from .serializer import (
    ProductSerializer, CategorySerializer, FavoriteSerializer,
    BrandSerializer, ColorSerializer,
    ATTR_MAP, ALL_ATTR_FIELDS,
)

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .filters import ProductFilter
from .pagination import ProductPagination
from .permissions import IsSellerOrReadOnly, IsSeller, IsProductOwner

from .signals import send_to_telegram, send_edit_to_telegram

from redis import Redis


redis = Redis(host="localhost", port=6379, db=0)


class ProductListCreateView(ListCreateAPIView):

    serializer_class = ProductSerializer
    permission_classes = [IsSellerOrReadOnly]
    pagination_class = ProductPagination

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter
    ]

    filterset_class = ProductFilter

    search_fields = [
        "title",
        "description"
    ]

    ordering_fields = [
        "price",
        "created_at",
        "view_count"
    ]

    def get_queryset(self):
        return Product.objects.filter(
            status=Product.Status.ACTIVE
        ).select_related("category", "seller").prefetch_related("images")

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)


class ProductDetailView(RetrieveUpdateDestroyAPIView):

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsProductOwner]

    def retrieve(self, request, *args, **kwargs):

        product = self.get_object()

        if request.user.is_authenticated:
            identifier = f"user:{request.user.id}"
        else:
            ip = request.META.get("REMOTE_ADDR")
            identifier = f"ip:{ip}"

        redis_key = f"product_view:{product.id}:{identifier}"

        if not redis.exists(redis_key):
            Product.objects.filter(id=product.id).update(
                view_count=models.F("view_count") + 1
            )
            redis.set(redis_key, 1)

        serializer = self.get_serializer(product)

        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        PATCH/PUT → o'zgarishlarni bevosita qo'llamaydi.
        PendingProductEdit yaratadi, mahsulotni moderatsiyaga yuboradi,
        Telegramga diff bilan xabar ketadi.
        Admin tasdiqlasa → o'zgarishlar qo'llanadi.
        """
        product = self.get_object()
        data = request.data

        # ── Kategoriya o'zgartirilmasin ──
        if "category" in data:
            incoming_cat = int(data["category"])
            if incoming_cat != product.category_id:
                return Response(
                    {"detail": "Kategoriyani o'zgartirish mumkin emas!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # ── O'zgarishlarni hisoblash (diff) ──
        changes = {}

        # Asosiy maydonlar
        field_labels = {
            "title": "Nomi",
            "description": "Tavsif",
            "price": "Narxi",
            "tax_percent": "Soliq %",
        }

        for field, label in field_labels.items():
            if field in data:
                old_val = getattr(product, field)
                new_val = data[field]
                # Decimal / string taqqoslash
                if field in ("price", "tax_percent"):
                    try:
                        old_cmp = str(Decimal(str(old_val)).normalize())
                        new_cmp = str(Decimal(str(new_val)).normalize())
                    except Exception:
                        old_cmp, new_cmp = str(old_val), str(new_val)
                else:
                    old_cmp, new_cmp = str(old_val), str(new_val)

                if old_cmp != new_cmp:
                    changes[field] = {
                        "label": label,
                        "old": str(old_val),
                        "new": str(new_val),
                    }

        # Brand
        if "brand_id" in data:
            old_brand = product.brand.name if product.brand else "—"
            new_brand_id = data["brand_id"]
            if new_brand_id:
                try:
                    new_brand = Brand.objects.get(id=new_brand_id).name
                except Brand.DoesNotExist:
                    new_brand = str(new_brand_id)
            else:
                new_brand = "—"
            old_brand_id = product.brand_id or ""
            if str(old_brand_id) != str(new_brand_id or ""):
                changes["brand"] = {
                    "label": "Brend",
                    "old": old_brand,
                    "new": new_brand,
                }

        # Atributlar
        cat_type = product.category.category_type if product.category else None
        if cat_type and cat_type in ATTR_MAP:
            field_name, model_cls, serializer_cls = ATTR_MAP[cat_type]
            attr_data = data.get(field_name)
            if attr_data and isinstance(attr_data, dict):
                existing_attr = getattr(product, field_name, None)
                for attr_key, attr_new_val in attr_data.items():
                    if attr_key == "color_id":
                        continue  # skip color for simplicity
                    old_attr_val = ""
                    if existing_attr:
                        old_attr_val = getattr(existing_attr, attr_key, "")
                    if str(old_attr_val or "") != str(attr_new_val or ""):
                        changes[f"{field_name}.{attr_key}"] = {
                            "label": f"Atribut: {attr_key}",
                            "old": str(old_attr_val or "—"),
                            "new": str(attr_new_val or "—"),
                        }

        # Agar hech narsa o'zgarmagan bo'lsa
        if not changes:
            return Response(
                {"detail": "Hech qanday o'zgarish topilmadi."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── PendingProductEdit yaratish ──
        previous_status = product.status

        # Eski pending bo'lsa — o'chiramiz
        PendingProductEdit.objects.filter(product=product).delete()

        # O'zgarishlar JSON sifatida + asl request data ni ham saqlash
        pending = PendingProductEdit.objects.create(
            product=product,
            changes_json={
                "diff": changes,
                "raw_data": data,
            },
            previous_status=previous_status,
        )

        # Mahsulotni moderatsiyaga yuborish
        product.status = Product.Status.MODERATION
        product.save(update_fields=["status"])

        # Telegramga xabar
        try:
            send_edit_to_telegram(product, changes)
        except Exception as e:
            logger.error(f"Tahrir Telegramga yuborishda xatolik: {e}")

        return Response(
            {"detail": "O'zgarishlar moderatsiyaga yuborildi. Admin tasdiqlashini kuting."},
            status=status.HTTP_200_OK,
        )


class GetAllCategories(APIView):

    serializer_class = CategorySerializer

    def get(self, request, slug=None):

        if slug:
            category = get_object_or_404(Category, slug=slug)
            data = CategorySerializer(category).data
            return Response(data, status=200)

        categories = Category.objects.all()
        data = CategorySerializer(categories, many=True).data

        return Response(data, status=200)


class GetProductsByCategory(APIView):

    serializer_class = ProductSerializer

    def get(self, request, slug):

        category = get_object_or_404(Category, slug=slug)

        products = Product.objects.filter(
            category=category,
            status=Product.Status.ACTIVE
        )

        data = ProductSerializer(products, many=True).data

        return Response(data, status=200)


class SetProductArchive(APIView):

    permission_classes = [IsSeller]
    serializer_class = ProductSerializer

    def post(self, request, pk):

        product = get_object_or_404(Product, id=pk)

        if product.seller != request.user:
            return Response(
                {"detail": "Bu Product sizga tegishli emas"},
                status=403
            )

        if product.status == Product.Status.ARCHIVED:
            return Response(
                {"detail": "Bu Product allaqachon arxivda"},
                status=400
            )

        product.status = Product.Status.ARCHIVED
        product.save()

        return Response({"detail": "Product arxiv qilindi"})


class SetProductSold(APIView):

    permission_classes = [IsSeller]
    serializer_class = ProductSerializer

    def post(self, request, pk):

        product = get_object_or_404(Product, id=pk)

        if product.seller != request.user:
            return Response(
                {"detail": "Bu Product sizga tegishli emas"},
                status=403
            )

        if product.status == Product.Status.SOLD:
            return Response(
                {"detail": "Bu Product allaqachon tugagan deb belgilangan"},
                status=400
            )

        product.status = Product.Status.SOLD
        product.save()

        return Response({"detail": "Product tugagan deb belgilandi"})


class FavoritesView(APIView):

    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteSerializer

    def get(self, request):

        favorites = Favorite.objects.filter(user=request.user)

        data = FavoriteSerializer(favorites, many=True).data

        return Response(data)


    def post(self, request):

        product_id = request.data.get("product_id")

        if not product_id:
            return Response(
                {"detail": "Product id required"},
                status=400
            )

        product = get_object_or_404(Product, id=product_id)

        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            return Response(
                {"detail": "Bu product allaqachon sevimlilarda"},
                status=400
            )

        return Response(
            {"detail": "Product qo'shildi"},
            status=201
        )


    def delete(self, request, pk):

        favorite = get_object_or_404(
            Favorite,
            id=pk,
            user=request.user
        )

        favorite.delete()

        return Response(
            {"detail": "Sevimli o'chirildi"},
            status=204
        )


class ProductImageUploadView(APIView):

    permission_classes = [IsSeller]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = ProductSerializer

    def post(self, request, product_id):

        product = Product.objects.filter(
            id=product_id,
            seller=request.user
        ).first()

        if not product:
            return Response(
                {"detail": "Product topilmadi yoki sizga tegishli emas"},
                status=404
            )

        images = request.FILES.getlist("images")

        if not images:
            return Response(
                {"detail": "Rasm yuborilmadi"},
                status=400
            )

        if len(images) > 10:
            return Response(
                {"detail": "Maximum 10 ta rasm yuklash mumkin"},
                status=400
            )

        last_order = ProductImage.objects.filter(
            product=product
        ).count()

        created_ids = []

        for idx, image in enumerate(images):

            img = ProductImage.objects.create(
                product=product,
                image=image,
                order=last_order + idx
            )

            created_ids.append(img.id)

        # Barcha rasmlar yuklangandan keyin — moderatsiyadagi mahsulotni Telegramga yuborish
        if product.status == Product.Status.MODERATION:
            try:
                send_to_telegram(product)
            except Exception as e:
                logger.error(f"Telegramga yuborishda xatolik: {e}")

        return Response(
            {
                "detail": "Rasmlar yuklandi",
                "image_ids": created_ids
            },
            status=201
        )