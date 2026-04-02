import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

CustomUser = get_user_model()

class GoogleAuthService:
    
    @staticmethod
    def generate_google_auth_url():
        url = f'https://accounts.google.com/o/oauth2/v2/auth?'\
                f'client_id={settings.GOOGLE_CLIENT_ID}&'\
                f'redirect_uri={settings.GOOGLE_REDIRECT_URL}&'\
                'scope=email%20profile&'\
                'response_type=code'
        return url
    
    @staticmethod
    def get_access_token(code: str):
        data = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': settings.GOOGLE_REDIRECT_URL,
        }
        response = requests.post(settings.GOOGLE_TOKEN_URL, data=data)

        if response.status_code != 200:
            return False
        
        access_token = response.json()['access_token']
        return access_token
    
    @staticmethod
    def get_user_info(access_token: str):
        response = requests.get(settings.GOOGLE_USER_INFO_URL, headers={'Authorization': f'Bearer {access_token}'})

        if response.status_code != 200:
            return False

        user = response.json()
        return user

    @staticmethod
    def get_user(user):
        userdata = CustomUser.objects.filter(email=user['email']).first()
        if not userdata:
            userdata = CustomUser(
                username = user['email'].split('@')[0],
                email = user['email'],
                first_name = user.get('given_name', ''),
                last_name = user.get('family_name', '' ),
                
            )
            userdata.save()
        
        return userdata
    
    @staticmethod
    def get_token(user):
        tokens = {
            'refresh': str(RefreshToken.for_user(user)),
            'access': str(AccessToken.for_user(user))
            
        }

        return tokens

    @staticmethod
    def login_by_google(code: str):
        access_token = GoogleAuthService.get_access_token(code)
        user_info = GoogleAuthService.get_user_info(access_token)
        user = GoogleAuthService.get_user(user_info)
        tokens = GoogleAuthService.get_token(user)

        return tokens
    

def get_tokens_for_user(user):

    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def create_user(data):
    user = CustomUser.objects.create_user(**data)
    return user

def set_number(telegram_id, number):
    user = CustomUser.objects.filter(telegram_id=telegram_id).first()
    
    if user:
        user.phone_number = number
        user.save()
        return True
    return False
    