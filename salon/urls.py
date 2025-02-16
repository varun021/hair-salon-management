from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your existing urls ...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 