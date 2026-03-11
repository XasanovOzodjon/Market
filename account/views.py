from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from redis import Redis
from uuid import uuid4
import json

from rest_framework.permissions import AllowAny
from .serializer import GetUIDSerializer

from rest_framework.views import APIView

class TelegramAuth(APIView):
    serializer_class = GetUIDSerializer
    permission_classes = [AllowAny]
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
        data = self.serializer_class(data=request.data)
        if not data.is_valid():
            return Response(data.errors, status=status.HTTP_400_BAD_REQUEST)
        
        unicID = request.data.get("unicID")

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

       
