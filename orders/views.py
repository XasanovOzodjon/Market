from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q

from .models import Order
from .serializers import OrderSerializer
from product.models import Product


class OrdersView(APIView):

    permission_classes = [IsAuthenticated]

    # GET /orders/
    def get(self, request):

        role = request.query_params.get("role")

        if role == "buyer":
            orders = Order.objects.filter(buyer=request.user)

        elif role == "seller":
            orders = Order.objects.filter(seller=request.user)

        else:
            orders = Order.objects.filter(
                Q(buyer=request.user) |
                Q(seller=request.user)
            )

        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)


    # POST /orders/
    def post(self, request):

        product_id = request.data.get("product_id")

        product = Product.objects.filter(id=product_id).first()

        if not product:
            return Response(
                {"detail": "Product topilmadi"},
                status=404
            )

        if product.status != Product.Status.ACTIVE:
            return Response(
                {"detail": "Product sotuvda emas"},
                status=400
            )

        order = Order.objects.create(
            product=product,
            buyer=request.user,
            seller=product.seller,
            final_price=product.price,
            notes=request.data.get("notes", "")
        )

        serializer = OrderSerializer(order)

        return Response(serializer.data, status=201)
    
class OrderDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):

        order = Order.objects.filter(id=pk).first()

        if not order:
            return None

        if request.user not in [order.buyer, order.seller]:
            return None

        return order


    # GET /orders/{id}/
    def get(self, request, pk):

        order = self.get_object(request, pk)

        if not order:
            return Response({"detail": "Topilmadi"}, status=404)

        serializer = OrderSerializer(order)

        return Response(serializer.data)


    # PATCH /orders/{id}/
    def patch(self, request, pk):

        order = self.get_object(request, pk)

        if not order:
            return Response({"detail": "Topilmadi"}, status=404)

        new_status = request.data.get("status")

        # seller action
        if request.user == order.seller:

            if order.status != Order.Status.PENDING:
                return Response({"detail": "Status o'zgartirib bo'lmaydi"}, status=400)

            if new_status == Order.Status.AGREED:
                order.status = Order.Status.AGREED
                order.meeting_location = request.data.get("meeting_location")
                order.meeting_time = request.data.get("meeting_time")

            elif new_status == Order.Status.CANCELED:
                order.status = Order.Status.CANCELED

        # buyer action
        elif request.user == order.buyer:

            if order.status != Order.Status.AGREED:
                return Response({"detail": "Order hali kelishilmagan"}, status=400)

            if new_status == Order.Status.COMPLETED:

                order.status = Order.Status.COMPLETED

                product = order.product
                product.status = product.Status.SOLD
                product.save(update_fields=["status"])

                seller_profile = order.seller.seller_profile
                seller_profile.total_sales += 1
                seller_profile.save(update_fields=["total_sales"])

            elif new_status == Order.Status.CANCELED:
                order.status = Order.Status.CANCELED

        else:
            return Response({"detail": "Ruxsat yo'q"}, status=403)

        order.save()

        serializer = OrderSerializer(order)

        return Response(serializer.data)