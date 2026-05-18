from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count

from .models import DirectRoom, DirectMessage

User = get_user_model()


class DirectRoomListView(LoginRequiredMixin, ListView):
    model = DirectRoom
    template_name = "dm/dm_list.html"
    context_object_name = "dm_rooms"

    def get_queryset(self):
        return DirectRoom.objects.filter(
            users=self.request.user
        ).prefetch_related("users").order_by("-created_at")


class StartDirectRoomView(LoginRequiredMixin, View):
    def post(self, request, user_id):
        other_user = get_object_or_404(User, id=user_id)

        if other_user == request.user:
            return redirect("dm_list")

        room = DirectRoom.objects.annotate(
            user_count=Count("users")
        ).filter(
            users=request.user
        ).filter(
            users=other_user
        ).filter(
            user_count=2
        ).first()

        if not room:
            room = DirectRoom.objects.create()
            room.users.add(request.user, other_user)

        return redirect("dm_detail", pk=room.pk)


class DirectRoomDetailView(LoginRequiredMixin, DetailView):
    model = DirectRoom
    template_name = "dm/dm_detail.html"
    context_object_name = "dm_room"

    def dispatch(self, request, *args, **kwargs):
        room = get_object_or_404(DirectRoom, pk=self.kwargs["pk"])

        if not room.users.filter(id=request.user.id).exists():
            return redirect("dm_list")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        messages = self.object.messages.select_related(
            "sender"
        ).order_by("-created_at")[:50]

        messages = list(reversed(messages))

        for msg in messages:
            msg.read_by.add(self.request.user)

        other_user = self.object.users.exclude(
            id=self.request.user.id
        ).first()

        context["messages"] = messages
        context["other_user"] = other_user

        return context