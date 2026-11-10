from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Favorite, Gift, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "gift_count", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Sovg'alar soni")
    def gift_count(self, obj):
        return obj.gifts.count()


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = (
        "image_preview",
        "name",
        "category",
        "recipient",
        "formatted_price",
        "age_range",
        "is_active",
        "created_at",
    )
    list_display_links = ("image_preview", "name")
    list_editable = ("is_active",)          # ro'yxatning o'zida faol/nofaol qilish
    list_filter = ("is_active", "category", "recipient", "created_at")
    search_fields = ("name", "description")
    list_per_page = 20
    date_hierarchy = "created_at"
    readonly_fields = ("image_preview_large", "created_at", "updated_at")
    actions = ["make_active", "make_inactive"]

    fieldsets = (
        ("Asosiy ma'lumot", {
            "fields": ("name", "description", "category"),
        }),
        ("Narx va maqsadli auditoriya", {
            "fields": ("price", "recipient", ("min_age", "max_age")),
        }),
        ("Rasm", {
            "fields": ("image", "image_preview_large"),
        }),
        ("Holat", {
            "fields": ("is_active", "created_at", "updated_at"),
        }),
    )

    @admin.display(description="Rasm")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:50px;height:50px;object-fit:cover;border-radius:8px;" />',
                obj.image.url,
            )
        return "—"

    @admin.display(description="Rasm (ko'rinishi)")
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px;border-radius:12px;" />',
                obj.image.url,
            )
        return "Rasm yuklanmagan"

    @admin.display(description="Narxi", ordering="price")
    def formatted_price(self, obj):
        return f"{int(obj.price):,} so'm".replace(",", " ")

    @admin.display(description="Yosh")
    def age_range(self, obj):
        return f"{obj.min_age}–{obj.max_age}"

    @admin.action(description="Tanlanganlarni faollashtirish")
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} ta sovg'a faollashtirildi.")

    @admin.action(description="Tanlanganlarni nofaol qilish")
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} ta sovg'a nofaol qilindi.")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "gift", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "gift__name")
    autocomplete_fields = ("gift",)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("gift",)
    readonly_fields = ("subtotal_display",)

    @admin.display(description="Jami")
    def subtotal_display(self, obj):
        if obj.pk:
            return f"{int(obj.subtotal):,} so'm".replace(",", " ")
        return "—"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "phone",
        "colored_status",
        "status",
        "total_display",
        "created_at",
    )
    list_display_links = ("id", "full_name")
    list_editable = ("status",)          # holatni ro'yxatning o'zida o'zgartirish
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "phone", "address", "id")
    date_hierarchy = "created_at"
    list_per_page = 20
    inlines = [OrderItemInline]
    readonly_fields = ("total_display", "created_at", "updated_at")
    actions = ["mark_confirmed", "mark_delivered", "mark_cancelled"]

    fieldsets = (
        ("Mijoz", {"fields": ("user", "full_name", "phone", "address", "note")}),
        ("Buyurtma holati", {"fields": ("status", "total_display", "created_at", "updated_at")}),
    )

    @admin.display(description="Holat (rangli)")
    def colored_status(self, obj):
        colors = {
            "new": "#2563eb",
            "confirmed": "#d97706",
            "delivering": "#7c3aed",
            "delivered": "#16a34a",
            "cancelled": "#dc2626",
        }
        return format_html(
            '<b style="color:{};">{}</b>',
            colors.get(obj.status, "#000"),
            obj.get_status_display(),
        )

    @admin.display(description="Umumiy summa")
    def total_display(self, obj):
        return f"{int(obj.total_price):,} so'm".replace(",", " ")

    @admin.action(description="Tasdiqlandi deb belgilash")
    def mark_confirmed(self, request, queryset):
        queryset.update(status=Order.Status.CONFIRMED)

    @admin.action(description="Yetkazildi deb belgilash")
    def mark_delivered(self, request, queryset):
        queryset.update(status=Order.Status.DELIVERED)

    @admin.action(description="Bekor qilish")
    def mark_cancelled(self, request, queryset):
        queryset.update(status=Order.Status.CANCELLED)    