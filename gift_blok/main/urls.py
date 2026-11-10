from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    FavoriteViewSet,
    GiftViewSet,
    OrderViewSet,
    login,
    logout,
    me,
    register,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("gifts", GiftViewSet, basename="gift")
router.register("orders", OrderViewSet, basename="order")
router.register("favorites", FavoriteViewSet, basename="favorite")

urlpatterns = [
    path("auth/register/", register, name="register"),
    path("auth/login/", login, name="login"),
    path("auth/logout/", logout, name="logout"),
    path("auth/me/", me, name="me"),
    path("", include(router.urls)),
]