from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .models import Review
from .serializers import ReviewSerializer
from .services import update_seller_rating

from orders.models import Order

class ReviewsView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):

        seller_id = request.query_params.get("seller_id")

        reviews = Review.objects.all()

        if seller_id:
            reviews = reviews.filter(seller_id=seller_id)

        serializer = ReviewSerializer(reviews, many=True)

        return Response(serializer.data)
    
class CreateReviewView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        order_id = request.data.get("order_id")
        rating = request.data.get("rating")
        comment = request.data.get("comment", "")

        order = Order.objects.filter(id=order_id).first()

        if not order:
            return Response(
                {"detail": "Order topilmadi"},
                status=404
            )

        if order.buyer != request.user:
            return Response(
                {"detail": "Faqat buyer review yozishi mumkin"},
                status=403
            )

        if order.status != Order.Status.COMPLETED:
            return Response(
                {"detail": "Faqat sotib olingan order uchun review yoziladi"},
                status=400
            )

        if hasattr(order, "review"):
            return Response(
                {"detail": "Bu order uchun review mavjud"},
                status=400
            )

        review = Review.objects.create(
            order=order,
            buyer=request.user,
            seller=order.seller,
            rating=rating,
            comment=comment
        )

        update_seller_rating(order.seller)

        serializer = ReviewSerializer(review)

        return Response(serializer.data, status=201)