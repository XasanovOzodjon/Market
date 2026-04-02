import logging
from telegram.ext import CallbackQueryHandler
from data.config import ADMINS



logger = logging.getLogger(__name__)


def approve_handler(update, context):
    """Mahsulotni tasdiqlash"""
    query = update.callback_query
    query.answer()

    # Faqat adminlar uchun
    if str(query.from_user.id) not in ADMINS:
        query.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    callback_data = query.data  # "product_approve:123"
    try:
        _, product_id = callback_data.split(":")
        product_id = int(product_id)
    except (ValueError, IndexError):
        query.edit_message_caption(caption="❌ Noto'g'ri ma'lumot!")
        return

    from product.models import Product

    try:
        product = Product.objects.get(id=product_id)
        product.status = Product.Status.ACTIVE
        product.save(update_fields=["status"])

        admin_name = query.from_user.full_name or query.from_user.username
        # Captionni yangilash (rasm ostida bo'lsa)
        try:
            old_caption = query.message.caption or ""
            new_caption = (
                f"{old_caption}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ <b>TASDIQLANDI</b>\n"
                f"👤 Admin: {admin_name}"
            )
            query.edit_message_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
        except Exception:
            # Agar rasm bo'lmasa, oddiy xabar sifatida yangilash
            old_text = query.message.text or ""
            new_text = (
                f"{old_text}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ <b>TASDIQLANDI</b>\n"
                f"👤 Admin: {admin_name}"
            )
            query.edit_message_text(text=new_text, parse_mode="HTML", reply_markup=None)

        logger.info(f"Mahsulot #{product_id} tasdiqlandi. Admin: {admin_name}")

    except Product.DoesNotExist:
        try:
            query.edit_message_caption(
                caption="❌ Mahsulot topilmadi! Ehtimol o'chirilgan.",
                reply_markup=None
            )
        except Exception:
            query.edit_message_text(
                text="❌ Mahsulot topilmadi! Ehtimol o'chirilgan.",
                reply_markup=None
            )
    except Exception as e:
        logger.error(f"Mahsulot tasdiqlashda xatolik: {e}")
        query.answer("❌ Xatolik yuz berdi!", show_alert=True)


def reject_handler(update, context):
    """Mahsulotni rad etish"""
    query = update.callback_query
    query.answer()

    # Faqat adminlar uchun
    if str(query.from_user.id) not in ADMINS:
        query.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    callback_data = query.data  # "product_reject:123"
    try:
        _, product_id = callback_data.split(":")
        product_id = int(product_id)
    except (ValueError, IndexError):
        query.edit_message_caption(caption="❌ Noto'g'ri ma'lumot!")
        return

    from product.models import Product

    try:
        product = Product.objects.get(id=product_id)
        product.status = Product.Status.REJECTED
        product.save(update_fields=["status"])

        admin_name = query.from_user.full_name or query.from_user.username
        try:
            old_caption = query.message.caption or ""
            new_caption = (
                f"{old_caption}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ <b>RAD ETILDI</b>\n"
                f"👤 Admin: {admin_name}"
            )
            query.edit_message_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
        except Exception:
            old_text = query.message.text or ""
            new_text = (
                f"{old_text}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ <b>RAD ETILDI</b>\n"
                f"👤 Admin: {admin_name}"
            )
            query.edit_message_text(text=new_text, parse_mode="HTML", reply_markup=None)

        logger.info(f"Mahsulot #{product_id} rad etildi. Admin: {admin_name}")

    except Product.DoesNotExist:
        try:
            query.edit_message_caption(
                caption="❌ Mahsulot topilmadi! Ehtimol o'chirilgan.",
                reply_markup=None
            )
        except Exception:
            query.edit_message_text(
                text="❌ Mahsulot topilmadi! Ehtimol o'chirilgan.",
                reply_markup=None
            )
    except Exception as e:
        logger.error(f"Mahsulot rad etishda xatolik: {e}")
        query.answer("❌ Xatolik yuz berdi!", show_alert=True)


def register_handlers(dp):
    dp.add_handler(CallbackQueryHandler(approve_handler, pattern=r"^product_approve:\d+$"))
    dp.add_handler(CallbackQueryHandler(reject_handler, pattern=r"^product_reject:\d+$"))
    dp.add_handler(CallbackQueryHandler(edit_approve_handler, pattern=r"^edit_approve:\d+$"))
    dp.add_handler(CallbackQueryHandler(edit_reject_handler, pattern=r"^edit_reject:\d+$"))


# ═══════════════════════════════════════════
#  TAHRIRLASH TASDIQLASH / RAD ETISH
# ═══════════════════════════════════════════

def _apply_pending_edit(product, pending):
    """
    PendingProductEdit dagi raw_data ni product ga qo'llaydi.
    """
    from product.models import (
        PendingProductEdit,
        Brand,
        PhoneAttribute, TVAttribute, LaptopAttribute,
        ClothingAttribute, ShoesAttribute, ApplianceAttribute,
        AutoAttribute, FoodAttribute, FurnitureAttribute,
        BookAttribute, HobbyAttribute, OtherAttribute,
    )
    from product.serializer import ATTR_MAP

    raw_data = pending.changes_json.get("raw_data", {})

    # Asosiy maydonlarni yangilash
    if "title" in raw_data:
        product.title = raw_data["title"]
    if "description" in raw_data:
        product.description = raw_data["description"]
    if "price" in raw_data:
        from decimal import Decimal
        product.price = Decimal(str(raw_data["price"]))
    if "tax_percent" in raw_data:
        from decimal import Decimal
        product.tax_percent = Decimal(str(raw_data["tax_percent"]))

    # Brand
    if "brand_id" in raw_data:
        brand_id = raw_data["brand_id"]
        if brand_id:
            try:
                product.brand = Brand.objects.get(id=brand_id)
            except Brand.DoesNotExist:
                pass
        else:
            product.brand = None

    product.save()

    # Atributlar
    cat_type = product.category.category_type if product.category else None
    if cat_type and cat_type in ATTR_MAP:
        field_name, model_cls, _ = ATTR_MAP[cat_type]
        attr_data = raw_data.get(field_name)
        if attr_data and isinstance(attr_data, dict):
            # color_id ni to'g'ri qayta ishlash
            model_cls.objects.update_or_create(
                product=product,
                defaults=attr_data,
            )


def edit_approve_handler(update, context):
    """Tahrirlashni tasdiqlash — o'zgarishlar qo'llanadi"""
    query = update.callback_query
    query.answer()

    if str(query.from_user.id) not in ADMINS:
        query.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    try:
        _, product_id = query.data.split(":")
        product_id = int(product_id)
    except (ValueError, IndexError):
        query.edit_message_text(text="❌ Noto'g'ri ma'lumot!", reply_markup=None)
        return

    from product.models import Product, PendingProductEdit

    try:
        product = Product.objects.get(id=product_id)
        pending = PendingProductEdit.objects.get(product=product)

        # O'zgarishlarni qo'llash
        _apply_pending_edit(product, pending)

        # Statusni qaytarish (eski holat yoki active)
        prev_status = pending.previous_status
        if prev_status in (Product.Status.ACTIVE, Product.Status.MODERATION):
            product.status = Product.Status.ACTIVE
        else:
            product.status = prev_status
        product.save(update_fields=["status"])

        # Pending ni o'chirish
        pending.delete()

        admin_name = query.from_user.full_name or query.from_user.username

        old_text = query.message.text or ""
        new_text = (
            f"{old_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ <b>TAHRIR TASDIQLANDI</b>\n"
            f"O'zgarishlar qo'llandi.\n"
            f"👤 Admin: {admin_name}"
        )
        query.edit_message_text(text=new_text, parse_mode="HTML", reply_markup=None)

        logger.info(f"Tahrir #{product_id} tasdiqlandi. Admin: {admin_name}")

    except PendingProductEdit.DoesNotExist:
        query.edit_message_text(
            text="❌ Kutilayotgan tahrir topilmadi! Ehtimol allaqachon ko'rib chiqilgan.",
            reply_markup=None
        )
    except Product.DoesNotExist:
        query.edit_message_text(
            text="❌ Mahsulot topilmadi! Ehtimol o'chirilgan.",
            reply_markup=None
        )
    except Exception as e:
        logger.error(f"Tahrir tasdiqlashda xatolik: {e}")
        query.answer("❌ Xatolik yuz berdi!", show_alert=True)


def edit_reject_handler(update, context):
    """Tahrirlashni rad etish — o'zgarishlar bekor, eski holat qaytariladi"""
    query = update.callback_query
    query.answer()

    if str(query.from_user.id) not in ADMINS:
        query.answer("⛔ Sizda ruxsat yo'q!", show_alert=True)
        return

    try:
        _, product_id = query.data.split(":")
        product_id = int(product_id)
    except (ValueError, IndexError):
        query.edit_message_text(text="❌ Noto'g'ri ma'lumot!", reply_markup=None)
        return

    from product.models import Product, PendingProductEdit

    try:
        product = Product.objects.get(id=product_id)
        pending = PendingProductEdit.objects.get(product=product)

        # Eski statusni qaytarish
        prev_status = pending.previous_status
        if prev_status == Product.Status.MODERATION:
            # Agar yangi mahsulot bo'lsa, moderatsiyada qoldirish
            product.status = Product.Status.ACTIVE
        else:
            product.status = prev_status
        product.save(update_fields=["status"])

        # Pending ni o'chirish (o'zgarishlar qo'llanmaydi)
        pending.delete()

        admin_name = query.from_user.full_name or query.from_user.username

        old_text = query.message.text or ""
        new_text = (
            f"{old_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"❌ <b>TAHRIR RAD ETILDI</b>\n"
            f"O'zgarishlar bekor qilindi.\n"
            f"👤 Admin: {admin_name}"
        )
        query.edit_message_text(text=new_text, parse_mode="HTML", reply_markup=None)

        logger.info(f"Tahrir #{product_id} rad etildi. Admin: {admin_name}")

    except PendingProductEdit.DoesNotExist:
        query.edit_message_text(
            text="❌ Kutilayotgan tahrir topilmadi! Ehtimol allaqachon ko'rib chiqilgan.",
            reply_markup=None
        )
    except Product.DoesNotExist:
        query.edit_message_text(
            text="❌ Mahsulot topilmadi! Ehtimol o'chirilgan.",
            reply_markup=None
        )
    except Exception as e:
        logger.error(f"Tahrir rad etishda xatolik: {e}")
        query.answer("❌ Xatolik yuz berdi!", show_alert=True)