"""
Equivalent of src/app.js:

    app.use('/auth', authRoutes);
    app.use('/incidents', incidentsRoutes);
    app.use('/traffic', trafficRoutes);
    app.use('/routing', routingRoutes);
    app.use('/analytics', analyticsRoutes);
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.http import JsonResponse

from incidents.search_views import SearchView


def health(request):
    # app.get('/health', (req, res) => res.json({ status: 'ok' }))
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health", health),
    path("auth/", include("accounts.urls")),
    path("incidents/", include("incidents.urls")),
    path("traffic/", include("traffic.urls")),
    path("routing/", include("routing.urls")),
    path("analytics/", include("analytics.urls")),
    path("search", SearchView.as_view()),  # bottom-nav "search" tab
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
