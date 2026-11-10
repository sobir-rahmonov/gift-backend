from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Category, Favorite, Gift, Order, OrderItem

User = get_user_model()


class BaseAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            "admin_t", password="pass12345", is_staff=True
        )
        cls.user = User.objects.create_user("user_t", password="pass12345")
        cls.other = User.objects.create_user("other_t", password="pass12345")

        cls.cat_flowers = Category.objects.create(name="Gullar", slug="gullar")
        cls.cat_toys = Category.objects.create(name="O'yinchoqlar", slug="oyinchoqlar")

        cls.flower = Gift.objects.create(
            name="Atirgul", price=100000, category=cls.cat_flowers,
            recipient="mother", min_age=20, max_age=80,
        )
        cls.toy = Gift.objects.create(
            name="Konstruktor", price=200000, category=cls.cat_toys,
            recipient="child", min_age=5, max_age=12,
        )
        cls.hidden = Gift.objects.create(
            name="Yashirin sovga", price=50000, category=cls.cat_toys,
            is_active=False,
        )


# ---------------------------------------------------------------- Kategoriya
class CategoryTests(BaseAPITestCase):
    def test_anyone_can_list_categories(self):
        response = self.client.get(reverse("category-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_regular_user_cannot_create_category(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("category-list"), {"name": "Yangi", "slug": "yangi"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_category(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            reverse("category-list"), {"name": "Yangi", "slug": "yangi"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# -------------------------------------------------------------------- Sovg'a
class GiftTests(BaseAPITestCase):
    def test_list_shows_only_active_gifts(self):
        response = self.client.get(reverse("gift-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_admin_sees_hidden_gifts(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("gift-list"))
        self.assertEqual(response.data["count"], 3)

    def test_filter_by_max_price(self):
        response = self.client.get(reverse("gift-list"), {"max_price": 150000})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Atirgul")

    def test_filter_by_category_slug(self):
        response = self.client.get(reverse("gift-list"), {"category": "oyinchoqlar"})
        self.assertEqual(response.data["count"], 1)


class FinderTests(BaseAPITestCase):
    def test_finder_by_recipient_age_and_budget(self):
        response = self.client.get(
            reverse("gift-finder"),
            {"recipient": "mother", "age": 30, "budget": 150000},
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Atirgul")

    def test_finder_for_child(self):
        response = self.client.get(
            reverse("gift-finder"), {"recipient": "child", "age": 8}
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Konstruktor")

    def test_finder_never_returns_inactive(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("gift-finder"), {"budget": 60000})
        self.assertEqual(response.data["count"], 0)


class GiftPermissionTests(BaseAPITestCase):
    def _payload(self):
        return {"name": "Yangi", "price": 90000, "category": self.cat_flowers.id}

    def test_anonymous_cannot_create(self):
        response = self.client.post(reverse("gift-list"), self._payload())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_create(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("gift-list"), self._payload())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(reverse("gift-list"), self._payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_regular_user_cannot_change_price(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("gift-detail", args=[self.flower.id]), {"price": 1}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_change_price(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            reverse("gift-detail", args=[self.flower.id]), {"price": 120000}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.flower.refresh_from_db()
        self.assertEqual(int(self.flower.price), 120000)

    def test_regular_user_cannot_delete(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(reverse("gift-detail", args=[self.flower.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(reverse("gift-detail", args=[self.flower.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------- Auth
class AuthTests(BaseAPITestCase):
    def test_register_success(self):
        response = self.client.post(
            reverse("register"),
            {"username": "newuser", "email": "n@test.uz", "password": "Xk93!mQzPw72"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertFalse(response.data["user"]["is_staff"])

    def test_register_duplicate_username(self):
        response = self.client.post(
            reverse("register"),
            {"username": "user_t", "password": "Xk93!mQzPw72"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        response = self.client.post(
            reverse("register"), {"username": "weakuser", "password": "123456"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        response = self.client.post(
            reverse("login"), {"username": "user_t", "password": "pass12345"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_login_wrong_password(self):
        response = self.client.post(
            reverse("login"), {"username": "user_t", "password": "xato"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_login(self):
        response = self.client.get(reverse("me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_with_token_shows_is_staff(self):
        token = Token.objects.create(user=self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get(reverse("me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "admin_t")
        self.assertTrue(response.data["is_staff"])

    def test_logout_deletes_token(self):
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Token.objects.filter(user=self.user).exists())


# ------------------------------------------------------------------ Buyurtma
class OrderTests(BaseAPITestCase):
    def _payload(self, **extra):
        data = {
            "full_name": "Test Mijoz",
            "phone": "+998901234567",
            "address": "Toshkent, Chilonzor",
            "items": [{"gift": self.flower.id, "quantity": 2}],
        }
        data.update(extra)
        return data

    def _make_order(self, user):
        order = Order.objects.create(
            user=user, full_name="Mijoz", phone="1", address="Manzil"
        )
        OrderItem.objects.create(
            order=order, gift=self.flower, quantity=1, price=self.flower.price
        )
        return order

    def test_guest_can_create_order(self):
        response = self.client.post(reverse("order-list"), self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(Order.objects.get().user)
        self.assertEqual(response.data["status"], "new")

    def test_price_comes_from_server_not_client(self):
        payload = self._payload(
            items=[{"gift": self.flower.id, "quantity": 2, "price": 1}]
        )
        response = self.client.post(reverse("order-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(int(response.data["total_price"]), 200000)
        self.assertEqual(int(OrderItem.objects.get().price), 100000)

    def test_logged_in_order_is_linked_to_user(self):
        self.client.force_authenticate(self.user)
        self.client.post(reverse("order-list"), self._payload(), format="json")
        self.assertEqual(Order.objects.get().user, self.user)

    def test_order_without_items_fails(self):
        response = self.client.post(
            reverse("order-list"), self._payload(items=[]), format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_order_inactive_gift(self):
        payload = self._payload(items=[{"gift": self.hidden.id, "quantity": 1}])
        response = self.client.post(reverse("order-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_anonymous_cannot_list_orders(self):
        response = self.client.get(reverse("order-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_sees_only_own_orders(self):
        self._make_order(self.user)
        self._make_order(self.other)
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("order-list"))
        self.assertEqual(response.data["count"], 1)

    def test_user_cannot_open_other_users_order(self):
        order = self._make_order(self.other)
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("order-detail", args=[order.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_sees_all_orders(self):
        self._make_order(self.user)
        self._make_order(self.other)
        self.client.force_authenticate(self.admin)
        response = self.client.get(reverse("order-list"))
        self.assertEqual(response.data["count"], 2)

    def test_admin_can_change_status(self):
        order = self._make_order(self.user)
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            reverse("order-detail", args=[order.id]),
            {"status": "confirmed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, "confirmed")

    def test_user_cannot_change_status(self):
        order = self._make_order(self.user)
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("order-detail", args=[order.id]),
            {"status": "delivered"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        order.refresh_from_db()
        self.assertEqual(order.status, "new")


# ----------------------------------------------------------------- Sevimlilar
class FavoriteTests(BaseAPITestCase):
    def test_anonymous_cannot_list_favorites(self):
        response = self.client.get(reverse("favorite-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_favorite_twice_does_not_duplicate(self):
        self.client.force_authenticate(self.user)
        first = self.client.post(reverse("favorite-list"), {"gift": self.flower.id})
        second = self.client.post(reverse("favorite-list"), {"gift": self.flower.id})
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(Favorite.objects.filter(user=self.user).count(), 1)

    def test_cannot_favorite_inactive_gift(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("favorite-list"), {"gift": self.hidden.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_toggle_adds_then_removes(self):
        self.client.force_authenticate(self.user)
        first = self.client.post(reverse("favorite-toggle"), {"gift": self.flower.id})
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertTrue(first.data["is_favorite"])

        second = self.client.post(reverse("favorite-toggle"), {"gift": self.flower.id})
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertFalse(second.data["is_favorite"])
        self.assertEqual(Favorite.objects.count(), 0)

    def test_user_sees_only_own_favorites(self):
        Favorite.objects.create(user=self.user, gift=self.flower)
        Favorite.objects.create(user=self.other, gift=self.toy)
        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("favorite-list"))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["gift"], self.flower.id)

    def test_user_can_delete_own_favorite(self):
        fav = Favorite.objects.create(user=self.user, gift=self.flower)
        self.client.force_authenticate(self.user)
        response = self.client.delete(reverse("favorite-detail", args=[fav.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_cannot_delete_other_users_favorite(self):
        fav = Favorite.objects.create(user=self.other, gift=self.toy)
        self.client.force_authenticate(self.user)
        response = self.client.delete(reverse("favorite-detail", args=[fav.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Favorite.objects.filter(id=fav.id).exists())