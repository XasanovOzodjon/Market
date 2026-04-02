from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.conf import settings
from urllib.parse import urlencode
from .emailService import send_email, check_email_pincode
from .auth_services import GoogleAuthService
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from redis import Redis
from uuid import uuid4
import json

CustomUser = get_user_model()

from .serializers import RegistarSerializer, EmailCheckSerializer

class RegistarView(APIView):
    serializer_class = RegistarSerializer
    @extend_schema(tags=["Auth"])
    def post(self, request: Request) -> Response:
        serializer = RegistarSerializer(data=request.data)
        
        
        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            
            user_username = CustomUser.objects.filter(
                username=validated_data['username']
            ).first()
            
            if user_username:
                return Response(
                    {'message': 'Bu username band'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            user_email = CustomUser.objects.filter(
                email = validated_data['email']
            )
            if user_email:
                return Response(
                    {'message': 'Bu email ruyxatdan utgan'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            uid = send_email(validated_data)
            return Response({
                'uid': uid
            })

class EmailCheckView(APIView):
    serializer_class = EmailCheckSerializer
    @extend_schema(tags=["Auth"])
    def post(self, request: Request) -> Response:
        serializer = EmailCheckSerializer(data = request.data)

        if serializer.is_valid(raise_exception=True):
            data = check_email_pincode(**serializer.validated_data)
            
            match data:
                case 404:
                    return Response({'message':'Not fount'}, status=status.HTTP_404_NOT_FOUND)
                case 408:
                    return Response({'message':'Time out'}, status=status.HTTP_408_REQUEST_TIMEOUT)
                case 401:
                    return Response({'message':'Invalid pincode'}, status=status.HTTP_401_UNAUTHORIZED)
                case 400:
                    return Response({'message':'Bad request'}, status=status.HTTP_400_BAD_REQUEST)
            
            
            user = CustomUser(
                username = data['username'],
                email = data['email'],
                password = data['password']
            )
            user.save()
            tokens = GoogleAuthService.get_token(user)
            return Response(tokens, status=status.HTTP_201_CREATED)
            

class GoogleAuthView(APIView):
    serializer_class = None
    @extend_schema(
        tags=["Auth"],
        responses={200: inline_serializer(
            name="GoogleAuthResponse",
            fields={
                "message": serializers.CharField(),
                "google_auth_link": serializers.URLField(),
            },
        )},
    )
    def post(self, request: Request) -> Response:
        url = GoogleAuthService.generate_google_auth_url()
        return Response(
            {
                'message': 'google orqali auth qilish uchun link',
                'google_auth_link': url
            }
        )


class GoogleACallBackView(APIView):
    @extend_schema(
        tags=["Auth"],
        parameters=[],
        responses={302: None},
        description="Google OAuth2 callback. Redirects with tokens as URL params.",
    )
    def get(self, request: Request) -> Response:
        code = request.query_params.get('code')
        if code is None:
            return redirect(f'{settings.FRONTEND_URL}/?error=code_required')
        
        tokens = GoogleAuthService.login_by_google(code)
        
        if not tokens:
            return redirect(f'{settings.FRONTEND_URL}/?error=google_auth_failed')
        
        # Tokenlarni URL parametr sifatida frontend sahifaga yuborish
        params = urlencode({
            'access': tokens.get('access', ''),
            'refresh': tokens.get('refresh', ''),
            'google_auth': 'success'
        })
        return redirect(f'{settings.FRONTEND_URL}/?{params}')
