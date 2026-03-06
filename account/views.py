from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from redis import Redis
from uuid import uuid4
import json
from .servise import create_user, get_tokens_for_user
from .models import CustomUser

from rest_framework.views import APIView

class TelegramAuth(APIView):
    def get(self, request: Request) -> Response:
        redis = Redis(host='localhost', port=6379, db=0)
        unicID = str(uuid4())
        redis.set(unicID, 'empty', ex=900)
        tg_url = f"https://t.me/olxluxcopyBot?start={unicID}"
        
        redis.close()
        return Response({"tg_url": tg_url, 
                         "unicID": unicID}, status=200)
    
        
    def post(self, request: Request) -> Response:
        redis = Redis(host='localhost', port=6379, db=0)
        data = request.data
        unicID = data.get("unicID")

        if not unicID:
            return Response({"error": "unicID is required"}, status=status.HTTP_400_BAD_REQUEST)

        if redis.exists(unicID):
            redis_value = redis.get(unicID)
            if not redis_value:
                return Response({"error": "invalid unicID or time end"}, status=status.HTTP_400_BAD_REQUEST)
            redis_value = redis_value.decode() if isinstance(redis_value, bytes) else redis_value
            if redis_value == 'empty':
                return Response({"error": "Telegram verification pending"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                tokens = json.loads(redis_value)
            except Exception as e:
                return Response({"error": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"tokens": tokens}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "invalid unicID or time end"}, status=status.HTTP_400_BAD_REQUEST)

class TelegramVerificationView(APIView):
    
        
    def post(self, request: Request) -> Response:
        data = request.data
        unicID = data.get("unicID")
        
        redis = Redis(host='localhost', port=6379, db=0)
        
        
        
        
        if redis.exists(unicID):
            redis_data = redis.get(unicID)

            if redis_data:
                data = json.loads(redis_data.decode())
            else:
                return Response({"error": "invalid"})
            redis.delete(unicID)
            
            user = CustomUser.objects.filter(telegram_id=data['telegram_id']).first()
            
            if not user:
                user = create_user(data=data)
                
            tokens = json.dumps(get_tokens_for_user(user=user))
            
            redis.set(unicID, tokens, ex=900)
            
            return Response({"status": "secusful"}, status=201)

            
            
            
            
        else:
            return Response({"status": "error", "message": "Invalid or expired unicID"}, status=400)