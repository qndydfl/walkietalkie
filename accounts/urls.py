from django.urls import path
from .views import ProfileUpdateView

urlpatterns = [
    path("profile/edit/", ProfileUpdateView.as_view(), name="profile_edit"),
]