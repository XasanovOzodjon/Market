from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q

from user.models import UserAdress
from product.models import Product

from .models import Order
from .serializers import OrderSerializer, CreateOrderSerializer, AddressSerializer
from .utils import send_telegram_message, send_order_accepted_to_admin

import logging

logger = logging.getLogger(__name__)


class OrdersView(APIView):
    """
    GET: Foydalanuvchi buyurtmalarini ko'rish
    POST: Yangi buyurtma yaratish
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.query_params.get("role")

        # Optimizatsiya: select_related va prefetch_related
        queryset = Order.objects.select_related(
            'product', 'buyer', 'seller',
            'buyer__user_address', 'seller__seller_profile'
        ).prefetch_related('product__images')

        if role == "buyer":
            orders = queryset.filter(buyer=request.user)
        elif role == "seller":
            orders = queryset.filter(seller=request.user)
        else:
            orders = queryset.filter(
                Q(buyer=request.user) | Q(seller=request.user)
            )

        # Eng yangilarini birinchi ko'rsatish
        orders = orders.order_by('-created_at')

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        """Yangi buyurtma yaratish"""
        serializer = CreateOrderSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        product_id = data.get("product_id")

        # Mahsulotni olish
        try:
            product = Product.objects.select_related('seller').get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Mahsulot topilmadi"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Tekshiruvlar
        if product.status != Product.Status.ACTIVE:
            return Response(
                {"detail": "Mahsulot sotuvda emas"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user == product.seller:
            return Response(
                {"detail": "O'zingizning mahsulotingizni sotib ololmaysiz"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Manzil logikasi
        user_address = getattr(request.user, "user_address", None)
        use_saved = data.get("use_saved_address", False)
        
        # Yangi manzil ma'lumotlari
        address_fields = ["address", "city", "country", "postal_code"]
        has_new_address = all(data.get(field) for field in address_fields)

        if has_new_address:
            # Yangi manzil yaratish yoki mavjudni yangilash
            address_data = {
                'address': data['address'],
                'city': data['city'],
                'country': data['country'],
                'postal_code': data['postal_code']
            }
            
            if user_address:
                # Mavjud manzilni yangilash
                for key, value in address_data.items():
                    setattr(user_address, key, value)
                user_address.save()
            else:
                # Yangi manzil yaratish
                user_address = UserAdress.objects.create(
                    user=request.user,
                    **address_data
                )
        elif not user_address and not use_saved:
            return Response(
                {"detail": "Yetkazib berish manzilini kiriting"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buyurtma yaratish
        order = Order.objects.create(
            product=product,
            buyer=request.user,
            seller=product.seller,
            final_price=product.price_with_tax,
            notes=data.get("notes", "")
        )

        # Telegram xabar yuborish (async qilish mumkin)
        try:
            send_telegram_message(order=order)
        except Exception as e:
            logger.error(f"Telegram xabar yuborishda xatolik: {e}")

        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    """
    GET: Bitta buyurtma tafsilotlari
    PATCH: Buyurtma statusini yangilash
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            order = Order.objects.select_related(
                'product', 'buyer', 'seller',
                'buyer__user_address', 'seller__seller_profile'
            ).prefetch_related('product__images').get(id=pk)

            # Faqat buyer yoki seller ko'ra oladi
            if request.user not in [order.buyer, order.seller]:
                return None

            return order
        except Order.DoesNotExist:
            return None

    def get(self, request, pk):
        order = self.get_object(request, pk)

        if not order:
            return Response(
                {"detail": "Buyurtma topilmadi yoki ruxsat yo'q"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = OrderSerializer(order)
        return Response(serializer.data)

    @transaction.atomic
    def patch(self, request, pk):
        order = self.get_object(request, pk)

        if not order:
            return Response(
                {"detail": "Buyurtma topilmadi yoki ruxsat yo'q"},
                status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get("status")

        if not new_status:
            return Response(
                {"detail": "Status ko'rsatilmagan"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Sotuvchi harakatlari
        if request.user == order.seller:
            if order.status != Order.Status.PENDING:
                return Response(
                    {"detail": "Faqat 'pending' holatdagi buyurtmani o'zgartirish mumkin"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if new_status == Order.Status.AGREED:
                order.status = Order.Status.AGREED
                order.save()
                
                # Buyurtma qabul qilindi - adminga xabar yuborish
                try:
                    send_order_accepted_to_admin(order)
                except Exception as e:
                    logger.error(f"Admin ga xabar yuborishda xatolik: {e}")
                
                serializer = OrderSerializer(order)
                return Response(serializer.data)

            elif new_status == Order.Status.CANCELED:
                order.status = Order.Status.CANCELED

            else:
                return Response(
                    {"detail": "Sotuvchi faqat 'agreed' yoki 'canceled' holatga o'zgartira oladi"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Haridor harakatlari
        elif request.user == order.buyer:
            if new_status == Order.Status.COMPLETED:
                if order.status != Order.Status.AGREED:
                    return Response(
                        {"detail": "Faqat 'agreed' holatdagi buyurtmani yakunlash mumkin"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                order.status = Order.Status.COMPLETED

                # Mahsulotni sotilgan deb belgilash
                product = order.product
                product.status = Product.Status.SOLD
                product.save(update_fields=["status"])

                # Sotuvchi statistikasini yangilash
                try:
                    seller_profile = order.seller.seller_profile
                    seller_profile.total_sales += 1
                    seller_profile.save(update_fields=["total_sales"])
                except Exception as e:
                    logger.warning(f"Sotuvchi profili yangilanmadi: {e}")

            elif new_status == Order.Status.CANCELED:
                if order.status not in [Order.Status.PENDING, Order.Status.AGREED]:
                    return Response(
                        {"detail": "Bu buyurtmani bekor qilib bo'lmaydi"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                order.status = Order.Status.CANCELED

            else:
                return Response(
                    {"detail": "Haridor faqat 'completed' yoki 'canceled' holatga o'zgartira oladi"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        else:
            return Response(
                {"detail": "Ruxsat yo'q"},
                status=status.HTTP_403_FORBIDDEN
            )

        order.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)


class UserAddressView(APIView):
    """
    GET: Foydalanuvchi manzilini olish
    POST/PUT: Manzilni yaratish/yangilash
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            address = request.user.user_address
            serializer = AddressSerializer(address)
            return Response(serializer.data)
        except UserAdress.DoesNotExist:
            return Response(
                {"detail": "Manzil topilmadi"},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Mavjud manzilni yangilash yoki yangi yaratish
        address, created = UserAdress.objects.update_or_create(
            user=request.user,
            defaults=serializer.validated_data
        )

        response_serializer = AddressSerializer(address)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    def put(self, request):
        return self.post(request)