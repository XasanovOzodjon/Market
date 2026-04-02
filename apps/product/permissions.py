from rest_framework.permissions import BasePermission


class IsSeller(BasePermission):
    """
    Faqat sotuvchi (role='seller') bo'lgan foydalanuvchilarga ruxsat beradi.
    """
    message = "Faqat sotuvchilar mahsulot qo'sha oladi."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "seller"
        )


class IsSellerOrReadOnly(BasePermission):
    """
    GET, HEAD, OPTIONS — hammaga ruxsat.
    POST (yaratish) — faqat sotuvchilarga.
    """
    message = "Faqat sotuvchilar mahsulot qo'sha oladi."

    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "seller"
        )


class IsProductOwner(BasePermission):
    """
    Mahsulot egasiga ruxsat (update, delete uchun).
    GET — hammaga ruxsat.
    """
    message = "Bu mahsulot sizga tegishli emas."

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return obj.seller == request.user
