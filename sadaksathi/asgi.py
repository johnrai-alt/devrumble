"""
Equivalent of src/server.js's `http.createServer(app)` + `initSockets(httpServer)`:
one process serves both the HTTP/DRF app and the WebSocket (traffic tile
subscription) endpoints, routed by protocol type.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sadaksathi.settings")

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
import traffic.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        URLRouter(traffic.routing.websocket_urlpatterns)
    ),
})
