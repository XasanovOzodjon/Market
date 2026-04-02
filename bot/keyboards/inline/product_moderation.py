from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def product_moderation_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Mahsulot moderatsiyasi uchun inline tugmalar"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"product_approve:{product_id}"),
            InlineKeyboardButton("❌ Rad etish", callback_data=f"product_reject:{product_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
