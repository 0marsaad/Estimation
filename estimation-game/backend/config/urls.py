from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    # OpenAPI schema + Swagger / Redoc UIs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # App endpoints
    path('api/auth/', include('apps.users.urls')),
    path('api/rooms/', include('apps.rooms.urls')),
    path('api/game/', include('apps.game.urls')),
    path('api/scoring/', include('apps.scoring.urls')),
]
