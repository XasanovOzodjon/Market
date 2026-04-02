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
        Foydalanuvchi ma'lumotlarini qaytaradi.
        Agar seller bo'lsa, seller profilini ham qaytaradi.
        """
        user_data = {
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "role": request.user.role,
            "phone_number": request.user.phone_number,
        }
        
        if request.user.role == CustomUser.Role.SELLER:
            profile = SellerProfile.objects.filter(user=request.user).first()
            if profile:
                user_data["seller_profile"] = self.serializer_class(profile).data
        
        return Response(user_data, status=200)

    def put(self, request: Request) -> Response:
        """
        Foydalanuvchining seller profilini yangilaydi.
        """
        if request.user.role != CustomUser.Role.SELLER:
            return Response({"detail": "Siz sotuvchi emassiz"}, status=403)
        
        profile = SellerProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"detail": "Seller profile mavjud emas"}, status=404)
        
        serializer = self.serializer_class(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        
        return Response(serializer.errors, status=400)
            
class GetDetailsSelerProfile(APIView):
    serializer_class = SellerProfileSerializer
    
    def get(self, request: Request, seller_id) -> Response:
        user = CustomUser.objects.filter(id=seller_id, role=CustomUser.Role.SELLER).first()
        if not user:
            return Response({"detail": "Seller topilmadi"}, status=404)
        
        profile = SellerProfile.objects.filter(user=user).first()
        if not profile:
            return Response({"detail": "Seller profili to'ldirilmagan"}, status=404)
        
        data = self.serializer_class(profile).data
        
        return Response({'seller': data}, status=status.HTTP_200_OK)
    
class GetSellerProductsView(APIView):
    def get(self, request: Request, seller_id) -> Response:
        user = CustomUser.objects.filter(id=seller_id, role=CustomUser.Role.SELLER).first()
        if not user:
            return Response({"detail": "Seller topilmadi"}, status=404)
        
        # Agar o'zi bo'lsa — barcha mahsulotlarni ko'radi
        # Boshqa foydalanuvchi bo'lsa — faqat aktiv mahsulotlar
        if request.user.is_authenticated and request.user.id == user.id:
            products = Product.objects.filter(seller=user)
        else:
            products = Product.objects.filter(seller=user, status=Product.Status.ACTIVE)
        
        serializer = ProductSerializer(products, many=True)
        
        return Response({'products': serializer.data}, status=status.HTTP_200_OK)