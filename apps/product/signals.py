import json
import logging
import requests
from django.conf import settings

from .models import Product, ProductImage

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════
#  FIELD LABEL TRANSLATIONS (UZ)
# ═══════════════════════════════════════════
FIELD_LABELS_UZ = {
    "title": "Nomi",
    "description": "Tavsif",
    "price": "Narxi",
    "tax_percent": "Soliq %",
    "brand": "Brend",
    "model_name": "Model",
    "storage_gb": "Xotira (GB)",
    "ram_gb": "RAM (GB)",
    "battery_mah": "Batareya (mAh)",
    "screen_size": "Ekran",
    "camera_mp": "Kamera (MP)",
    "os": "Operatsion tizim",
    "sim_count": "SIM soni",
    "resolution": "Ruxsat",
    "is_smart": "Smart TV",
    "refresh_rate": "Hz",
    "warranty_months": "Kafolat (oy)",
    "processor": "Protsessor",
    "storage_type": "Xotira turi",
    "battery_hours": "Batareya (soat)",
    "available_sizes": "Razmerlar",
    "gender": "Jins",
    "material": "Material",
    "season": "Mavsum",
    "power_watt": "Quvvat (Vt)",
    "energy_class": "Energiya sinfi",
    "weight_kg": "Og'irligi (kg)",
    "dimensions": "O'lcham",
    "make": "Marka",
    "year": "Yil",
    "fuel_type": "Yoqilg'i",
    "transmission": "Uzatma",
    "drive_type": "Yurg'izma",
    "mileage_km": "Probeg (km)",
    "engine_cc": "Motor (cc)",
    "expiry_date": "Yaroqlilik",
    "weight": "Og'irligi",
    "weight_unit": "Og'irlik birligi",
    "is_organic": "Organik",
    "ingredients": "Tarkibi",
    "storage_info": "Saqlash",
    "author": "Muallif",
    "publisher": "Nashriyot",
    "language": "Til",
    "pages": "Sahifalar",
    "isbn": "ISBN",
    "genre": "Janr",
    "hobby_type": "Turi",
    "age_min": "Min yosh",
    "age_max": "Max yosh",
}


def get_attribute_info(product: Product) -> str:
    """Kategoriyaga qarab mahsulot atribut ma'lumotlarini qaytaradi"""
    if not product.category:
        return ""

    cat_type = product.category.category_type
    lines = []

    try:
        if cat_type == "phone" and hasattr(product, 'phone_attr'):
            attr = product.phone_attr
            if attr.model_name:   lines.append(f"📱 <b>Model:</b> {attr.model_name}")
            if attr.color:        lines.append(f"🎨 <b>Rang:</b> {attr.color.name}")
            if attr.storage_gb:   lines.append(f"💾 <b>Xotira:</b> {attr.storage_gb} GB")
            if attr.ram_gb:       lines.append(f"🧠 <b>RAM:</b> {attr.ram_gb} GB")
            if attr.battery_mah:  lines.append(f"🔋 <b>Batareya:</b> {attr.battery_mah} mAh")
            if attr.screen_size:  lines.append(f"📐 <b>Ekran:</b> {attr.screen_size}\"")
            if attr.os:           lines.append(f"⚙️ <b>OS:</b> {attr.get_os_display()}")
            if attr.sim_count:    lines.append(f"📶 <b>SIM:</b> {attr.sim_count} ta")
            if attr.camera_mp:    lines.append(f"📷 <b>Kamera:</b> {attr.camera_mp} MP")

        elif cat_type == "tv" and hasattr(product, 'tv_attr'):
            attr = product.tv_attr
            if attr.model_name:      lines.append(f"📺 <b>Model:</b> {attr.model_name}")
            if attr.color:           lines.append(f"🎨 <b>Rang:</b> {attr.color.name}")
            if attr.screen_size:     lines.append(f"📐 <b>Ekran:</b> {attr.screen_size}\"")
            if attr.resolution:      lines.append(f"🖥 <b>Ruxsat:</b> {attr.get_resolution_display()}")
            smart_text = "Ha" if attr.is_smart else "Yoq"
            lines.append(f"📡 <b>Smart TV:</b> {smart_text}")
            if attr.refresh_rate:    lines.append(f"🔄 <b>Hz:</b> {attr.refresh_rate}")
            if attr.warranty_months: lines.append(f"🛡 <b>Kafolat:</b> {attr.warranty_months} oy")

        elif cat_type == "laptop" and hasattr(product, 'laptop_attr'):
            attr = product.laptop_attr
            if attr.model_name:      lines.append(f"💻 <b>Model:</b> {attr.model_name}")
            if attr.color:           lines.append(f"🎨 <b>Rang:</b> {attr.color.name}")
            if attr.processor:       lines.append(f"⚡ <b>Protsessor:</b> {attr.processor}")
            if attr.ram_gb:          lines.append(f"🧠 <b>RAM:</b> {attr.ram_gb} GB")
            if attr.storage_gb:      lines.append(f"💾 <b>Xotira:</b> {attr.storage_gb} GB ({attr.storage_type.upper() if attr.storage_type else '—'})")
            if attr.screen_size:     lines.append(f"📐 <b>Ekran:</b> {attr.screen_size}\"")
            if attr.battery_hours:   lines.append(f"🔋 <b>Batareya:</b> {attr.battery_hours} soat")
            if attr.os:              lines.append(f"⚙️ <b>OS:</b> {attr.get_os_display()}")
            if attr.warranty_months: lines.append(f"🛡 <b>Kafolat:</b> {attr.warranty_months} oy")

        elif cat_type == "clothing" and hasattr(product, 'clothing_attr'):
            attr = product.clothing_attr
            if attr.available_sizes: lines.append(f"📏 <b>Razmerlar:</b> {', '.join(attr.available_sizes)}")
            if attr.color:           lines.append(f"🎨 <b>Rang:</b> {attr.color.name}")
            if attr.gender:          lines.append(f"👤 <b>Jins:</b> {attr.get_gender_display()}")
            if attr.material:        lines.append(f"🧵 <b>Material:</b> {attr.material}")
            if attr.season:          lines.append(f"🌤 <b>Mavsum:</b> {attr.get_season_display()}")

        elif cat_type == "shoes" and hasattr(product, 'shoes_attr'):
            attr = product.shoes_attr
            if attr.available_sizes: lines.append(f"📏 <b>Razmerlar:</b> {', '.join(str(s) for s in attr.available_sizes)}")
            if attr.color:           lines.append(f"🎨 <b>Rang:</b> {attr.color.name}")
            if attr.gender:          lines.append(f"👤 <b>Jins:</b> {attr.get_gender_display()}")
            if attr.material:        lines.append(f"🧵 <b>Material:</b> {attr.material}")
            if attr.season:          lines.append(f"🌤 <b>Mavsum:</b> {attr.get_season_display()}")

        elif cat_type == "appliance" and hasattr(product, 'appliance_attr'):
            attr = product.appliance_attr
            if attr.model_name:      lines.append(f"🏠 <b>Model:</b> {attr.model_name}")
            if attr.color:           lines.append(f"🎨 <b>Rang:</b> {attr.color.name}")
            if attr.power_watt:      lines.append(f"⚡ <b>Quvvat:</b> {attr.power_watt} Vt")
            if attr.energy_class:    lines.append(f"🔋 <b>Energiya sinfi:</b> {attr.get_energy_class_display()}")
            if attr.weight_kg:       lines.append(f"⚖️ <b>Og'irligi:</b> {attr.weight_kg} kg")
            if attr.dimensions:      lines.append(f"📐 <b>O'lcham:</b> {attr.dimensions}")
            if attr.warranty_months: lines.append(f"🛡 <b>Kafolat:</b> {attr.warranty_months} oy")

        elif cat_type == "auto" and hasattr(product, 'auto_attr'):
            attr = product.auto_attr
            if attr.make:            lines.append(f"🚗 <b>Marka:</b> {attr.make}")
            if attr.model_name:      lines.append(f"🏎 <b>Model:</b> {attr.model_name}")
            if attr.year:            lines.append(f"📅 <b>Yil:</b> {attr.year}")
            if attr.color:           lines.append(f"🎨 <b>Rang:</b> {attr.color.name}")
            if attr.fuel_type:       lines.append(f"⛽ <b>Yoqilg'i:</b> {attr.get_fuel_type_display()}")
            if attr.transmission:    lines.append(f"🔧 <b>Uzatma:</b> {attr.get_transmission_display()}")
            if attr.drive_type:      lines.append(f"🛞 <b>Yurg'izma:</b> {attr.get_drive_type_display()}")
            if attr.mileage_km:      lines.append(f"🛣 <b>Probeg:</b> {attr.mileage_km:,} km")
            if attr.engine_cc:       lines.append(f"🔩 <b>Motor:</b> {attr.engine_cc} cc")

        elif cat_type == "food" and hasattr(product, 'food_attr'):
            attr = product.food_attr
            if attr.weight:          lines.append(f"⚖️ <b>Og'irligi:</b> {attr.weight} {attr.weight_unit}")
            if attr.expiry_date:     lines.append(f"📅 <b>Yaroqlilik:</b> {attr.expiry_date}")
            organic_text = "Ha" if attr.is_organic else "Yoq"
            lines.append(f"🌿 <b>Organik:</b> {organic_text}")
            if attr.ingredients:     lines.append(f"📋 <b>Tarkibi:</b> {attr.ingredients[:100]}")
            if attr.storage_info:    lines.append(f"🧊 <b>Saqlash:</b> {attr.storage_info}")

        elif cat_type == "furniture" and hasattr(product, 'furniture_attr'):
            attr = product.furniture_attr
            if attr.material:        lines.append(f"🧵 <b>Material:</b> {attr.material}")
            if attr.color:           lines.append(f"🎨 <b>Rang:</b> {attr.color.name}")
            if attr.dimensions:      lines.append(f"📐 <b>O'lcham:</b> {attr.dimensions}")
            if attr.weight_kg:       lines.append(f"⚖️ <b>Og'irligi:</b> {attr.weight_kg} kg")
            if attr.warranty_months: lines.append(f"🛡 <b>Kafolat:</b> {attr.warranty_months} oy")

        elif cat_type == "book" and hasattr(product, 'book_attr'):
            attr = product.book_attr
            if attr.author:          lines.append(f"✍️ <b>Muallif:</b> {attr.author}")
            if attr.publisher:       lines.append(f"🏢 <b>Nashriyot:</b> {attr.publisher}")
            if attr.language:        lines.append(f"🌐 <b>Til:</b> {attr.language}")
            if attr.pages:           lines.append(f"📄 <b>Sahifalar:</b> {attr.pages}")
            if attr.isbn:            lines.append(f"🔢 <b>ISBN:</b> {attr.isbn}")
            if attr.genre:           lines.append(f"📚 <b>Janr:</b> {attr.genre}")

        elif cat_type == "hobby" and hasattr(product, 'hobby_attr'):
            attr = product.hobby_attr
            if attr.hobby_type:      lines.append(f"🎮 <b>Turi:</b> {attr.hobby_type}")
            if attr.age_min or attr.age_max:
                age = f"{attr.age_min or '?'}—{attr.age_max or '?'} yosh"
                lines.append(f"👶 <b>Yosh:</b> {age}")
            if attr.material:        lines.append(f"🧵 <b>Material:</b> {attr.material}")

        elif cat_type == "other" and hasattr(product, 'other_attr'):
            attr = product.other_attr
            if attr.material:        lines.append(f"🧵 <b>Material:</b> {attr.material}")
            if attr.color:           lines.append(f"🎨 <b>Rang:</b> {attr.color.name}")
            if attr.weight_kg:       lines.append(f"⚖️ <b>Og'irligi:</b> {attr.weight_kg} kg")
            if attr.warranty_months: lines.append(f"🛡 <b>Kafolat:</b> {attr.warranty_months} oy")

    except Exception as e:
        logger.warning(f"Atribut ma'lumotlarini olishda xatolik (product #{product.id}): {e}")

    return "\n".join(lines)


def send_to_telegram(product: Product):
    """
    Mahsulot ma'lumotlari + BARCHA rasmlar + inline tugmalar bilan adminlarga yuborish.
    Telegram sendMediaGroup — bir nechta rasm, birinchisiga caption.
    1 ta rasm bo'lsa sendPhoto, rasm yo'q bo'lsa sendMessage.
    """
    attr_info = get_attribute_info(product)
    attr_block = f"\n\n📋 <b>Xususiyatlar:</b>\n{attr_info}" if attr_info else ""

    caption = (
        f"🆕 <b>Yangi mahsulot moderatsiyada!</b>\n\n"
        f"📦 <b>Nomi:</b> {product.title}\n"
        f"📁 <b>Kategoriya:</b> {product.category.name if product.category else '—'}\n"
        f"🏷 <b>Brend:</b> {product.brand.name if product.brand else '—'}\n"
        f"💰 <b>Narxi:</b> {product.price:,.2f} UZS\n"
        f"📊 <b>Soliq:</b> {product.tax_percent}%\n"
        f"💵 <b>Umumiy narxi:</b> {product.price_with_tax:,.2f} UZS\n"
        f"👤 <b>Sotuvchi:</b> {product.seller.get_full_name() or product.seller.email}\n"
        f"📝 <b>Tavsif:</b> {product.description[:200]}{'...' if len(product.description) > 200 else ''}"
        f"{attr_block}\n\n"
        f"🆔 <b>ID:</b> {product.id}"
    )

    # Telegram caption limit — 1024 belgi (sendPhoto/sendMediaGroup)
    if len(caption) > 1024:
        caption = caption[:1020] + "..."

    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Tasdiqlash", "callback_data": f"product_approve:{product.id}"},
                {"text": "❌ Rad etish", "callback_data": f"product_reject:{product.id}"},
            ]
        ]
    }

    token = settings.TELEGRAM_BOT_TOKEN

    # Barcha rasmlarni olish (max 10 ta — Telegram limiti)
    images = ProductImage.objects.filter(product=product).order_by('-is_main', 'order')[:10]

    for chat_id in settings.TELEGRAM_ADMINS:
        try:
            if images.count() > 1:
                # ── Bir nechta rasm: sendMediaGroup + keyin tugmalar alohida ──
                files = {}
                media = []
                for idx, img in enumerate(images):
                    attach_name = f"photo{idx}"
                    files[attach_name] = open(img.image.path, 'rb')
                    item = {
                        "type": "photo",
                        "media": f"attach://{attach_name}",
                    }
                    # Caption faqat birinchi rasmga
                    if idx == 0:
                        item["caption"] = caption
                        item["parse_mode"] = "HTML"
                    media.append(item)

                url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
                resp = requests.post(
                    url,
                    data={
                        "chat_id": chat_id,
                        "media": json.dumps(media),
                    },
                    files=files,
                )
                # Fayllarni yopish
                for f in files.values():
                    f.close()

                if not resp.ok:
                    logger.error(f"Telegram sendMediaGroup xatolik: {resp.text}")

                # sendMediaGroup da reply_markup qo'llab-quvvatlanmaydi,
                # shuning uchun tugmalarni alohida xabar sifatida yuboramiz
                btn_url = f"https://api.telegram.org/bot{token}/sendMessage"
                btn_resp = requests.post(btn_url, json={
                    "chat_id": chat_id,
                    "text": f"⬆️ #{product.id} — <b>{product.title}</b> uchun qaror:",
                    "parse_mode": "HTML",
                    "reply_markup": inline_keyboard,
                })
                if not btn_resp.ok:
                    logger.error(f"Telegram tugma yuborishda xatolik: {btn_resp.text}")

            elif images.count() == 1:
                # ── Bitta rasm: sendPhoto + tugmalar ──
                img = images.first()
                url = f"https://api.telegram.org/bot{token}/sendPhoto"
                with open(img.image.path, 'rb') as photo:
                    resp = requests.post(
                        url,
                        data={
                            "chat_id": chat_id,
                            "caption": caption,
                            "parse_mode": "HTML",
                            "reply_markup": json.dumps(inline_keyboard),
                        },
                        files={"photo": photo},
                    )
                if not resp.ok:
                    logger.error(f"Telegram sendPhoto xatolik: {resp.text}")

            else:
                # ── Rasm yo'q: sendMessage ──
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                resp = requests.post(url, json={
                    "chat_id": chat_id,
                    "text": caption,
                    "parse_mode": "HTML",
                    "reply_markup": inline_keyboard,
                })
                if not resp.ok:
                    logger.error(f"Telegram sendMessage xatolik: {resp.text}")

        except Exception as e:
            logger.error(f"Telegramga xabar yuborishda xatolik (chat_id={chat_id}): {e}")


def send_edit_to_telegram(product: Product, changes: dict):
    """
    Mahsulot tahrirlanganda adminlarga diff bilan xabar yuborish.
    changes = { field_key: { label, old, new }, ... }
    """

    # Diff formatini tayyorlash
    diff_lines = []
    for key, info in changes.items():
        label = info.get("label", key)
        # Atribut kalitidagi prefixni tozalash
        if "." in key:
            _, attr_key = key.split(".", 1)
            label = FIELD_LABELS_UZ.get(attr_key, attr_key)
        else:
            label = FIELD_LABELS_UZ.get(key, label)

        old_val = info.get("old", "—")
        new_val = info.get("new", "—")

        # Uzun qiymatlarni qisqartirish
        if len(str(old_val)) > 80:
            old_val = str(old_val)[:77] + "..."
        if len(str(new_val)) > 80:
            new_val = str(new_val)[:77] + "..."

        diff_lines.append(
            f"  📌 <b>{label}:</b>\n"
            f"     ❌ <s>{old_val}</s>\n"
            f"     ✅ {new_val}"
        )

    diff_text = "\n".join(diff_lines)

    caption = (
        f"✏️ <b>Mahsulot tahrirlandi — moderatsiya!</b>\n\n"
        f"📦 <b>Nomi:</b> {product.title}\n"
        f"📁 <b>Kategoriya:</b> {product.category.name if product.category else '—'}\n"
        f"💰 <b>Narxi:</b> {product.price:,.2f} UZS\n"
        f"👤 <b>Sotuvchi:</b> {product.seller.get_full_name() or product.seller.email}\n"
        f"🆔 <b>ID:</b> {product.id}\n\n"
        f"📝 <b>O'zgartirilgan maydonlar:</b>\n"
        f"{diff_text}"
    )

    # Telegram caption limit
    if len(caption) > 4096:
        caption = caption[:4092] + "..."

    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Tahrirni tasdiqlash", "callback_data": f"edit_approve:{product.id}"},
                {"text": "❌ Tahrirni rad etish", "callback_data": f"edit_reject:{product.id}"},
            ]
        ]
    }

    token = settings.TELEGRAM_BOT_TOKEN

    for chat_id in settings.TELEGRAM_ADMINS:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            resp = requests.post(url, json={
                "chat_id": chat_id,
                "text": caption,
                "parse_mode": "HTML",
                "reply_markup": inline_keyboard,
            })
            if not resp.ok:
                logger.error(f"Telegram edit xabar xatolik: {resp.text}")

        except Exception as e:
            logger.error(f"Telegram edit xabar yuborishda xatolik (chat_id={chat_id}): {e}")
