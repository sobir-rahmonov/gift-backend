# Gift Finder: Backend

Sovg'a tanlash platformasining server qismi (REST API + admin panel).
Foydalanuvchi kimga sovg'a olayotganini, yoshini va budjetini kiritadi, tizim mos sovg'alarni qaytaradi.

## Imkoniyatlar

- Sovg'alar va kategoriyalar ro'yxati, qidiruv, filter va saralash
- **Sovg'a topish** (`finder`): kimga, yosh va budjet bo'yicha tanlash
- Ro'yxatdan o'tish va kirish (token orqali)
- Sevimlilar (yurakcha tugmasi uchun `toggle` bilan)
- Buyurtma berish (mehmon ham, kirgan foydalanuvchi ham)
- Admin: sovg'a, kategoriya qo'shish/tahrirlash/o'chirish, buyurtma holatini o'zgartirish
- Django admin paneli (`/admin/`)

## Texnologiyalar

Python 3.13, Django, Django REST Framework, django-filter, django-cors-headers, Pillow, SQLite.

## Loyiha tuzilmasi

```
gift_blok/
├── config/          # sozlamalar (settings.py) va asosiy urls.py
├── main/            # asosiy ilova
│   ├── models.py        # Category, Gift, Favorite, Order, OrderItem
│   ├── serializers.py   # ma'lumotlarni JSON ga o'tkazish va tekshirish
│   ├── views.py         # API logikasi
│   ├── filters.py       # sovg'alar filtri
│   ├── permissions.py   # ruxsatlar (admin / egasi)
│   ├── admin.py         # Django admin sozlamalari
│   ├── urls.py          # API manzillari
│   └── tests.py         # testlar
├── media/           # yuklangan rasmlar (git'ga kirmaydi)
├── manage.py
└── requirements.txt
```

## O'rnatish va ishga tushirish

Windows (CMD) uchun:

```cmd
cd gift_blok
python -m venv env
env\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Server `http://127.0.0.1:8000` da ishlaydi.

- API: `http://127.0.0.1:8000/api/`
- Admin panel: `http://127.0.0.1:8000/admin/`

## Testlar

```cmd
python manage.py test
```

Testlar vaqtinchalik baza yaratadi, shuning uchun `db.sqlite3` dagi ma'lumotlarga tegmaydi.
Ular narx serverdan olinishini, ruxsatlarni, buyurtma va sevimlilar mantiqini tekshiradi.

## API

Asosiy manzil: `/api/`. Ro'yxatlar sahifalanadi (bir sahifada 12 ta): `{ count, next, previous, results }`.

### Autentifikatsiya

Kirgandan keyin olingan tokenni har so'rovga qo'shing:

```
Authorization: Token <token>
```

| Manzil | Usul | Tavsif |
|---|---|---|
| `/api/auth/register/` | POST | Ro'yxatdan o'tish. Token va foydalanuvchini qaytaradi |
| `/api/auth/login/` | POST | Kirish. Token va `is_staff` ni qaytaradi |
| `/api/auth/me/` | GET | Joriy foydalanuvchi |
| `/api/auth/logout/` | POST | Chiqish (tokenni o'chiradi) |

### Sovg'alar va kategoriyalar

| Manzil | Usul | Kim | Tavsif |
|---|---|---|---|
| `/api/categories/` | GET | hamma | Kategoriyalar |
| `/api/categories/` | POST, PUT, PATCH, DELETE | admin | Boshqarish |
| `/api/gifts/` | GET | hamma | Sovg'alar (adminga nofaollari ham) |
| `/api/gifts/{id}/` | GET | hamma | Bitta sovg'a |
| `/api/gifts/` | POST, PATCH, DELETE | admin | Boshqarish (rasm: `multipart/form-data`) |
| `/api/gifts/finder/` | GET | hamma | Sovg'a topish |

Sovg'alar filtri: `category` (slug), `recipient`, `min_price`, `max_price`, `search`, `ordering` (`price`, `-price`, `created_at`), `page`.

Sovg'a topish misoli:

```
GET /api/gifts/finder/?recipient=mother&age=45&budget=300000
```

`recipient` qiymatlari: `any`, `mother`, `father`, `wife`, `husband`, `friend`, `child`, `colleague`.

### Buyurtmalar

| Manzil | Usul | Kim | Tavsif |
|---|---|---|---|
| `/api/orders/` | POST | hamma | Buyurtma berish |
| `/api/orders/` | GET | kirgan | O'z buyurtmalari (admin: hammasi, `?status=` filtri) |
| `/api/orders/{id}/` | GET | egasi / admin | Bitta buyurtma |
| `/api/orders/{id}/` | PATCH | admin | Holatni o'zgartirish |

Buyurtma berish misoli:

```json
{
  "full_name": "Ali Valiyev",
  "phone": "+998901234567",
  "address": "Toshkent, Chilonzor",
  "note": "",
  "items": [{ "gift": 1, "quantity": 2 }]
}
```

Narx har doim serverda sovg'aning joriy narxidan olinadi, mijoz yuborgan narx hisobga olinmaydi.

Holatlar: `new`, `confirmed`, `delivering`, `delivered`, `cancelled`.

### Sevimlilar (kirish shart)

| Manzil | Usul | Tavsif |
|---|---|---|
| `/api/favorites/` | GET | Mening sevimlilarim |
| `/api/favorites/` | POST | Qo'shish: `{ "gift": 3 }` |
| `/api/favorites/{id}/` | DELETE | O'chirish |
| `/api/favorites/toggle/` | POST | Bor bo'lsa o'chiradi, yo'q bo'lsa qo'shadi |

## Ruxsatlar

| Rol | Imkoniyat |
|---|---|
| Mehmon | Sovg'alarni ko'rish, buyurtma berish |
| Foydalanuvchi | + sevimlilar, o'z buyurtmalarini ko'rish |
| Admin (`is_staff`) | + sovg'a, kategoriya boshqaruvi, barcha buyurtmalar va holatini o'zgartirish |

## Eslatmalar

- Buyurtmada ishlatilgan sovg'ani o'chirib bo'lmaydi, uni nofaol qiling.
- Ichida sovg'asi bor kategoriyani o'chirib bo'lmaydi.
- Productionga chiqarishdan oldin: `DEBUG = False`, yangi `SECRET_KEY`, `ALLOWED_HOSTS` ni to'ldiring va `CORS_ALLOW_ALL_ORIGINS` o'rniga `CORS_ALLOWED_ORIGINS` ro'yxatini bering.