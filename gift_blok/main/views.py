from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .filters import GiftFilter
from .models import Category, Favorite, Gift, Order
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdmin
from .serializers import (
    CategorySerializer,
    FavoriteSerializer,
    GiftSerializer,
    LoginSerializer,
    OrderSerializer,
    OrderStatusSerializer,
    RegisterSerializer,
    UserSerializer,
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None




class GiftViewSet(viewsets.ModelViewSet):
    serializer_class = GiftSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = GiftFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at"]

    def get_queryset(self):
        qs = Gift.objects.select_related("category")
        user = self.request.user
        # Admin hammasini ko'radi, oddiy foydalanuvchi faqat faollarini
        if user.is_authenticated and user.is_staff:
            return qs
        return qs.filter(is_active=True)

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def finder(self, request):
        """
        Asosiy funksiya: kimga, yoshi va budjet bo'yicha mos sovg'alar.
        Misol: /api/gifts/finder/?recipient=mother&age=45&budget=300000
        """
        qs = Gift.objects.filter(is_active=True).select_related("category")

        recipient = request.query_params.get("recipient")
        age = request.query_params.get("age")
        budget = request.query_params.get("budget")

        if recipient:
            qs = qs.filter(Q(recipient=recipient) | Q(recipient="any"))
        if age and age.isdigit():
            qs = qs.filter(min_age__lte=int(age), max_age__gte=int(age))
        if budget and budget.isdigit():
            qs = qs.filter(price__lte=int(budget))

        serializer = self.get_serializer(qs.order_by("price"), many=True)
        return Response({"count": qs.count(), "results": serializer.data})




class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = OrderSerializer
    filterset_fields = ["status"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.action in ("partial_update", "update"):
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated(), IsOwnerOrAdmin()]

    def get_queryset(self):
        qs = Order.objects.prefetch_related("items__gift")
        user = self.request.user
        if user.is_staff:
            return qs
        return qs.filter(user=user)

    def get_serializer_class(self):
        if self.action in ("partial_update", "update"):
            return OrderStatusSerializer
        return OrderSerializer



class FavoriteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        # Har kim faqat o'z sevimlilarini ko'radi
        return Favorite.objects.filter(user=self.request.user).select_related(
            "gift", "gift__category"
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, gift=serializer.validated_data["gift"]
        )
        data = self.get_serializer(favorite).data
        return Response(
            data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def toggle(self, request):
        """
        Yurakcha tugmasi uchun: bor bo'lsa o'chiradi, yo'q bo'lsa qo'shadi.
        Body: {"gift": 3}
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        gift = serializer.validated_data["gift"]
        favorite = Favorite.objects.filter(user=request.user, gift=gift).first()
        if favorite:
            favorite.delete()
            return Response({"is_favorite": False})
        Favorite.objects.create(user=request.user, gift=gift)
        return Response({"is_favorite": True}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {"token": token.key, "user": UserSerializer(user).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "user": UserSerializer(user).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)    