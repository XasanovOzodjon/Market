from django.shortcuts import get_object_or_404
from django.db import models

from .models import Product, ProductImage, Favorite, Category
from .serializer import ProductSerializer, CategorySerializer, FavoriteSerializer

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

from redis import Redis


redis = Redis(host="localhost", port=6379, db=0)


class ProductListCreateView(ListCreateAPIView):

    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
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
    permission_classes = [IsAuthenticatedOrReadOnly]

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


class SetProductPublish(APIView):

    permission_classes = [IsAuthenticated]
    serializer_class = ProductSerializer

    def post(self, request, pk):

        product = get_object_or_404(Product, id=pk)

        if product.seller != request.user:
            return Response(
                {"detail": "Bu Product sizga tegishli emas"},
                status=403
            )

        if product.status == Product.Status.ACTIVE:
            return Response(
                {"detail": "Bu Product allaqachon public"},
                status=400
            )

        product.status = Product.Status.ACTIVE
        product.save()

        return Response({"detail": "Product public qilindi"})


class SetProductArchive(APIView):

    permission_classes = [IsAuthenticated]
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

    permission_classes = [IsAuthenticated]
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

    permission_classes = [IsAuthenticated]
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

        return Response(
            {
                "detail": "Rasmlar yuklandi",
                "image_ids": created_ids
            },
            status=201
        )