from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic.base import RedirectView

urlpatterns = [
    # Intercept and redirect Django's default /admin/ to your custom OrnaStyle portal
    path('admin/', RedirectView.as_view(pattern_name='dashboard', permanent=False)),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)