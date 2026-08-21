"""
Equivalent of src/sockets/index.js (JWT handshake auth) combined with
src/sockets/trafficNamespace.js (tile-scoped subscribe/unsubscribe rooms).

Socket.io and Django Channels aren't wire-compatible — this is a plain
WebSocket endpoint, not a Socket.io server — but the behaviour matches:
clients connect with an access token, then join/leave "tile:<geohash>"
groups so they only receive updates for map tiles they're viewing, not
the whole city.

The ingest worker / traffic app should broadcast to a group when new
readings land, e.g.:

    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    async_to_sync(get_channel_layer().group_send)(
        f"tile_{geohash}", {"type": "traffic.update", "data": data}
    )
"""
import json
import logging

import jwt as pyjwt
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from accounts.tokens import verify_access_token

logger = logging.getLogger(__name__)


class TrafficConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Equivalent of io.use((socket, next) => { ... }) in sockets/index.js.
        # Socket.io reads `socket.handshake.auth.token`; a plain WebSocket
        # has no equivalent handshake payload, so the same access token is
        # passed as a query string param instead: ws://.../ws/traffic/?token=...
        token = self.scope["query_string"].decode()
        token = dict(p.split("=", 1) for p in token.split("&") if "=" in p).get("token")

        if not token:
            await self.close(code=4001)  # "Missing token"
            return

        try:
            self.user_payload = verify_access_token(token)
        except pyjwt.InvalidTokenError:
            await self.close(code=4001)  # "Invalid or expired token"
            return

        self.subscribed_tiles = set()
        await self.accept()
        logger.info(f"Socket connected: user {self.user_payload['sub']}")

    async def disconnect(self, close_code):
        if hasattr(self, "subscribed_tiles"):
            for geohash in list(self.subscribed_tiles):
                await self.channel_layer.group_discard(f"tile_{geohash}", self.channel_name)
        if hasattr(self, "user_payload"):
            logger.info(f"Socket disconnected: user {self.user_payload['sub']}")

    async def receive_json(self, content, **kwargs):
        # Equivalent of socket.on('tile:subscribe', ...) / socket.on('tile:unsubscribe', ...)
        event = content.get("event")
        geohash = content.get("geohash")
        if not geohash:
            return

        if event == "tile:subscribe":
            await self.channel_layer.group_add(f"tile_{geohash}", self.channel_name)
            self.subscribed_tiles.add(geohash)
        elif event == "tile:unsubscribe":
            await self.channel_layer.group_discard(f"tile_{geohash}", self.channel_name)
            self.subscribed_tiles.discard(geohash)

    async def traffic_update(self, event):
        # Handler for group_send({"type": "traffic.update", "data": ...});
        # equivalent of io.to(`tile:${geohash}`).emit('traffic:update', data).
        await self.send_json({"event": "traffic:update", "data": event["data"]})
