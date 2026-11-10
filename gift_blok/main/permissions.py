from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """
    Hamma ko'ra oladi (GET).
    Qo'shish, tahrirlash, o'chirish faqat admin (is_staff) uchun.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrAdmin(BasePermission):
    """
    Buyurtmani faqat egasi yoki admin ko'ra oladi.
    """

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and obj.user_id == request.user.id
        )