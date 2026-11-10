from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from .models import Category, Favorite, Gift, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    gift_count = serializers.IntegerField(source="gifts.count", read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "gift_count")


class GiftSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    recipient_display = serializers.CharField(
        source="get_recipient_display", read_only=True
    )

    class Meta:
        model = Gift
        fields = (
            "id",
            "name",
            "description",
            "price",
            "category",
            "category_name",
            "recipient",
            "recipient_display",
            "min_age",
            "max_age",
            "image",
            "is_active", 
            "created_at",
        )


class OrderItemSerializer(serializers.ModelSerializer):
    gift_name = serializers.CharField(source="gift.name", read_only=True)
    subtotal = serializers.DecimalField(
        max_digits=14, decimal_places=0, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ("id", "gift", "gift_name", "quantity", "price", "subtotal")
        read_only_fields = ("price",)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total_price = serializers.DecimalField(
        max_digits=14, decimal_places=0, read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "full_name",
            "phone",
            "address",
            "note",
            "status",
            "status_display",
            "items",
            "total_price",
            "created_at",
        )
        read_only_fields = ("status",)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Kamida bitta sovg'a tanlang.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        request = self.context.get("request")
        user = request.user if request and request.user.is_authenticated else None

        order = Order.objects.create(user=user, **validated_data)

        for item in items_data:
            gift = item["gift"]
            if not gift.is_active:
                raise serializers.ValidationError(
                    {"items": f"'{gift.name}' hozir mavjud emas."}
                )
            OrderItem.objects.create(
                order=order,
                gift=gift,
                quantity=item.get("quantity", 1),
                price=gift.price,  # narx serverdan olinadi
            )
        return order

User = get_user_model()




class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs["username"], password=attrs["password"]
        )
        if not user:
            raise serializers.ValidationError("Login yoki parol noto'g'ri.")
        if not user.is_active:
            raise serializers.ValidationError("Akkaunt faol emas.")
        attrs["user"] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_staff")


class FavoriteSerializer(serializers.ModelSerializer):
    gift_detail = GiftSerializer(source="gift", read_only=True)

    class Meta:
        model = Favorite
        fields = ("id", "gift", "gift_detail", "created_at")

    def validate_gift(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Bu sovg'a hozir mavjud emas.")
        return value

class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("id", "status")

    