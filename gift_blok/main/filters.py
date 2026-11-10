import django_filters

from .models import Gift


class GiftFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = django_filters.CharFilter(field_name="category__slug")

    class Meta:
        model = Gift
        fields = ["category", "recipient", "min_price", "max_price"]