from django.urls import path
from .views import (
    DirectRoomListView,
    DirectRoomDetailView,
    StartDirectRoomView,
)

urlpatterns = [
    path("dm/", DirectRoomListView.as_view(), name="dm_list"),
    path("dm/start/<int:user_id>/", StartDirectRoomView.as_view(), name="dm_start"),
    path("dm/<int:pk>/", DirectRoomDetailView.as_view(), name="dm_detail"),
]