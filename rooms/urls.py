from django.urls import path
from .views import (
    RoomListView, 
    RoomCreateView, 
    RoomDetailView, 
    RoomPasswordView, 
    InviteUserView,
    RoomDeleteView,
)


urlpatterns = [
    path("", RoomListView.as_view(), name="room_list"),
    path("rooms/create/", RoomCreateView.as_view(), name="room_create"),
    path("rooms/<int:pk>/password/", RoomPasswordView.as_view(), name="room_password"),
    path("rooms/<int:pk>/invite/", InviteUserView.as_view(), name="room_invite"),
    path("rooms/<int:pk>/delete/", RoomDeleteView.as_view(), name="room_delete"),
    path("rooms/<int:pk>/", RoomDetailView.as_view(), name="room_detail"),
]