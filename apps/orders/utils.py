from .models import Order
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_address_text(user):
    """Foydalanuvchi manzilini formatlash"""
    try:
        addr = getattr(user, 'user_address', None)
        if addr:
            return f"{addr.address}, {addr.city}, {addr.country}"
        return "Manzil ko'rsatilmagan"
    except Exception:
        return "Manzil ko'rsatilmagan"


def _send_telegram(chat_id, message):
    """Telegram ga xabar yuborish (ichki funksiya)"""
    if not hasattr(settings, 'TELEGRAM_BOT_TOKEN') or not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN sozlanmagan")
        return False
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Telegram xabar yuborildi: chat_id={chat_id}")
        return True
    except requests.RequestException as e:
        logger.error(f"Telegramga xabar yuborishda xatolik (chat_id={chat_id}): {e}")
        return False


def _get_order_details(order):
    """Buyurtma ma'lumotlarini olish"""
    product_title = getattr(order.product, 'title', "Noma'lum")
    buyer_name = order.buyer.get_full_name() if order.buyer else "Noma'lum"
    buyer_address = get_address_text(order.buyer)
    
    shop_name = "Noma'lum"
    try:
        if hasattr(order.seller, 'seller_profile') and order.seller.seller_profile:
            shop_name = order.seller.seller_profile.shop_name
    except Exception:
        pass
    
    return {
        'product_title': product_title,
        'buyer_name': buyer_name,
        'buyer_address': buyer_address,
        'shop_name': shop_name
    }


def send_new_order_to_seller(order: Order):
    """Yangi buyurtma haqida FAQAT sotuvchiga xabar yuborish"""
    
    if not order.seller or not order.seller.telegramID:
        logger.warning(f"Sotuvchining telegram ID si yo'q: order_id={order.id}")
        return
    
    details = _get_order_details(order)
    
    seller_message = (
        f"🆕 <b>Yangi buyurtma! | ID:{order.id}</b>\n\n"
        f"📦 <b>Mahsulot:</b> {details['product_title']} | ID:{order.product.id}\n"
        f"👤 <b>Buyurtuvchi:</b> {details['buyer_name']} | ID:{order.buyer.id}\n"
        f"📍 <b>Manzil:</b> {details['buyer_address']}\n"
        f"💰 <b>Narxi:</b> {order.final_price} UZS\n"
        f"🕐 <b>Yaratilgan vaqt:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"\n<i>Buyurtmani qabul qilish uchun tizimga kiring.</i>"
    )
    
    _send_telegram(order.seller.telegramID, seller_message)


def send_order_accepted_to_admin(order: Order):
    """Buyurtma qabul qilinganda ADMINLARGA xabar yuborish"""
    
    admin_ids = getattr(settings, 'TELEGRAM_ADMINS', [])
    if not admin_ids:
        logger.warning("TELEGRAM_ADMINS sozlanmagan")
        return
    
    details = _get_order_details(order)
    
    admin_message = (
        f"✅ <b>Buyurtma qabul qilindi! | ID:{order.id}</b>\n\n"
        f"📦 <b>Mahsulot:</b> {details['product_title']} | ID:{order.product.id}\n"
        f"🏪 <b>Sotuvchi:</b> {details['shop_name']} | ID:{order.seller.id}\n"
        f"👤 <b>Buyurtuvchi:</b> {details['buyer_name']} | ID:{order.buyer.id}\n"
        f"📍 <b>Manzil:</b> {details['buyer_address']}\n"
        f"💰 <b>Narxi:</b> {order.final_price} UZS\n"
        f"🕐 <b>Yaratilgan vaqt:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}\n"
    )
    
    for admin_id in admin_ids:
        _send_telegram(admin_id, admin_message)


# Eski funksiya - backward compatibility uchun
def send_telegram_message(order: Order):
    """Telegram orqali buyurtma haqida xabar yuborish (eski funksiya)"""
    send_new_order_to_seller(order)