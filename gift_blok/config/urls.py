from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Gift Finder — Boshqaruv paneli"
admin.site.site_title = "Gift Finder"
admin.site.index_title = "Xush kelibsiz!"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('main.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)