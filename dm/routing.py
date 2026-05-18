from django.urls import path
from .consumers import DirectMessageConsumer

websocket_urlpatterns = [
    path("ws/dm/<int:room_id>/", DirectMessageConsumer.as_asgi()),
]