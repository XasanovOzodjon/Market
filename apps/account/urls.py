from django.urls import path
from .views import RegistarView, EmailCheckView, GoogleAuthView, GoogleACallBackView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)

urlpatterns = [
    path('registar/', RegistarView.as_view(), name='registar'),
    path('emailcheck/', EmailCheckView.as_view(), name='emailcheck'),
    path('google/', GoogleAuthView.as_view(), name='google'),
    path('googleCallback', GoogleACallBackView.as_view(), name='googleback'),
    
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    
    
    
]