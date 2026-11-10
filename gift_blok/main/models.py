from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField("Nomi", max_length=100, unique=True)
    slug = models.SlugField("Slug", max_length=120, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Gift(models.Model):
    class Recipient(models.TextChoices):
        ANY = "any", "Hamma uchun"
        MOTHER = "mother", "Ona"
        FATHER = "father", "Ota"
        WIFE = "wife", "Rafiqa"
        HUSBAND = "husband", "Er"
        FRIEND = "friend", "Do'st"
        CHILD = "child", "Bola"
        COLLEAGUE = "colleague", "Hamkasb"

    name = models.CharField("Nomi", max_length=200)
    description = models.TextField("Tavsif", blank=True)
    price = models.DecimalField("Narxi (so'm)", max_digits=12, decimal_places=0)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="gifts",
        verbose_name="Kategoriya",
    )
    recipient = models.CharField(
        "Kimga",
        max_length=20,
        choices=Recipient.choices,
        default=Recipient.ANY,
    )
    min_age = models.PositiveIntegerField("Minimal yosh", default=0)
    max_age = models.PositiveIntegerField("Maksimal yosh", default=100)
    image = models.ImageField("Rasm", upload_to="gifts/", blank=True, null=True)
    is_active = models.BooleanField("Faol", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sovg'a"
        verbose_name_plural = "Sovg'alar"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name="Foydalanuvchi",
    )
    gift = models.ForeignKey(
        Gift,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name="Sovg'a",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sevimli"
        verbose_name_plural = "Sevimlilar"
        unique_together = ("user", "gift")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} → {self.gift}"


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Yangi"
        CONFIRMED = "confirmed", "Tasdiqlandi"
        DELIVERING = "delivering", "Yetkazilmoqda"
        DELIVERED = "delivered", "Yetkazildi"
        CANCELLED = "cancelled", "Bekor qilindi"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Foydalanuvchi",
    )
    full_name = models.CharField("Ism-familiya", max_length=150)
    phone = models.CharField("Telefon", max_length=20)
    address = models.TextField("Manzil")
    note = models.TextField("Izoh", blank=True)
    status = models.CharField(
        "Holat", max_length=20, choices=Status.choices, default=Status.NEW
    )
    created_at = models.DateTimeField("Buyurtma vaqti", auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Buyurtma #{self.pk} — {self.full_name}"

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="Buyurtma"
    )
    gift = models.ForeignKey(
        Gift, on_delete=models.PROTECT, verbose_name="Sovg'a"
    )
    quantity = models.PositiveIntegerField("Soni", default=1)
    price = models.DecimalField(
        "Narxi (buyurtma vaqtida)", max_digits=12, decimal_places=0
    )

    class Meta:
        verbose_name = "Buyurtma mahsuloti"
        verbose_name_plural = "Buyurtma mahsulotlari"

    def __str__(self):
        return f"{self.gift.name} × {self.quantity}"

    @property
    def subtotal(self):
        return self.price * self.quantity    