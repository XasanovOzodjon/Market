from django.shortcuts import redirect, render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminUser
from user.models import CustomUser
from django.views.generic import TemplateView


class AddSeller(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """Barcha foydalanuvchilarni qaytaradi."""
        users = CustomUser.objects.all().values(
            'id', 'username', 'email', 'role', 'is_staff'
        )
        return Response({'Users': list(users)})

    def post(self, request):
        """
        action='promote' → foydalanuvchini sotuvchiga aylantiradi
        action='demote'  → sotuvchini xaridorga qaytaradi
        """
        user_id = request.data.get('user_id')
        action  = request.data.get('action', 'promote')  # 'promote' yoki 'demote'

        if not user_id:
            return Response({'error': 'user_id majburiy.'}, status=400)

        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Foydalanuvchi topilmadi.'}, status=404)

        # ── PROMOTE ──
        if action == 'promote':
            if user.role == 'seller':
                return Response({'error': f'{user.username} allaqachon sotuvchi.'}, status=400)
            if user.is_staff:
                return Response({'error': 'Admin foydalanuvchini sotuvchiga aylantirish mumkin emas.'}, status=400)

            user.role = 'seller'
            user.save()
            return Response({
                'message': f'{user.username} sotuvchiga aylantir ildi.',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                }
            })

        # ── DEMOTE ──
        elif action == 'demote':
            if user.role != 'seller':
                return Response({'error': f'{user.username} sotuvchi emas.'}, status=400)

            user.role = 'customer'
            user.save()
            return Response({
                'message': f'{user.username} sotuvchidan olindi.',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                }
            })

        else:
            return Response({'error': "Noto'g'ri action. 'promote' yoki 'demote' bo'lishi kerak."}, status=400)


class AdminDashboard(TemplateView):
    template_name = 'admin.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth')
        if not request.user.is_staff:
            return redirect('home')
        return render(request, self.template_name)
