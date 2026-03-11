from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status

from user.models import CustomUser
from rest_framework.permissions import IsAuthenticated
from .serializer import SellerProfileSerializer
from user.models import SellerProfile
from rest_framework.parsers import MultiPartParser, FormParser
from product.models import Product
from product.serializer import ProductSerializer

from rest_framework.views import APIView
# Create your views here.
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SellerProfileSerializer
    parser_classes = [MultiPartParser, FormParser]
    
    def get(self, request: Request) -> Response:
        """
        Foydalanuvchining seller profilini qaytaradi.
        """
        profile = SellerProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"detail": "Seller profile mavjud emas"}, status=404)
        data = self.serializer_class(profile).data
        return Response(data, status=200)

    def put(self, request: Request) -> Response:
        """
        Foydalanuvchining seller profilini yangilaydi.
        """
        profile = SellerProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"detail": "Seller profile mavjud emas"}, status=404)
        
        serializer = self.serializer_class(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        
        return Response(serializer.errors, status=400)
    
    
class UpdateToSellerView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SellerProfileSerializer
    
    def post(self, request: Request) -> Response:
        user = request.user
        serializer = self.serializer_class(data=request.data)
        if user.role == CustomUser.Role.SELLER:
            return Response({"detail": "Siz allaqachon seller hisoblanasiz"}, status=400)
        
        if serializer.is_valid():
            serializer.save(user=request.user)

            user.role = CustomUser.Role.SELLER
            user.save()

            return Response({'seller': serializer.data}, status=200)

        return Response(serializer.errors, status=400)
            
class GetDetailsSelerProfile(APIView):
    serializer_class = SellerProfileSerializer
    
    def get(self, request: Request, seller_id) -> Response:
        user = CustomUser.objects.filter(id=seller_id, role=CustomUser.Role.SELLER).first()
        if not user:
            return Response({"detail": "Seller topilmadi"}, status=404)
        
        data = self.serializer_class(user.seller_profile).data
        
        return Response({'seller': data}, status=status.HTTP_200_OK)
    
class GetSellerProductsView(APIView):
    def get(self, request: Request, seller_id) -> Response:
        user = CustomUser.objects.filter(id=seller_id, role=CustomUser.Role.SELLER).first()
        if not user:
            return Response({"detail": "Seller topilmadi"}, status=404)
        
        products = Product.objects.filter(seller=user, status=Product.Status.ACTIVE)
        serializer = ProductSerializer(products, many=True)
        
        return Response({'products': serializer.data}, status=status.HTTP_200_OK)