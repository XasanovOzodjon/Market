from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from random import randint
from datetime import datetime, timedelta
from django.utils import timezone
import redis
import uuid
import json

def send_email(data):
    pincode = randint(100000, 999999)
    uid = uuid.uuid4()
    
    send_mail(
        subject="Go2Link ni tasqiqlash uchun kod",
        message=f"Assalomu aleykum {data['username']}! Bu tastiqlash kodini hechkimga bermang. bu tasiqlash kodingiz 15 minut davomida amal qiladi. Sizning tasqilash kodingiz: {pincode}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[data['email']],
        fail_silently=False,
    )
    data.pop('conform_password', None)
    password = data.pop('password')
    data['password'] = make_password(password)

    # Verification uchun kerakli ma'lumotlarni qo'shish
    data['pin_code'] = make_password(str(pincode))
    data['count_try'] = 3
    data['create_at'] = timezone.now().isoformat()

    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
    redis_client.set(str(uid), json.dumps(data), ex=900)

    return uid



def check_email_pincode(uid, pincode):
    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
    redis_data = redis_client.get(str(uid))
    if not redis_data:
        return 404

    data = json.loads(redis_data)
    created_at = datetime.fromisoformat(data['create_at'])
    if timezone.is_naive(created_at):
        created_at = timezone.make_aware(created_at)
    if data['count_try'] > 0 and timezone.now() < created_at + timedelta(minutes=15):
        if check_password(f"{pincode}", data['pin_code']):
            return data
        else:
            data['count_try'] -= 1
            redis_client.set(str(uid), json.dumps(data), ex=900)
            return 401
    else:
        redis_client.delete(str(uid))
        return 408