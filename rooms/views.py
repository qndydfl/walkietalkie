from django.views.generic import ListView, CreateView, DetailView, FormView, View, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Room
from .forms import RoomForm, RoomPasswordForm, InviteUserForm
from chat.models import Message


User = get_user_model()

class RoomListView(LoginRequiredMixin, ListView):
    model = Room
    template_name = "rooms/room_list.html"
    context_object_name = "rooms"

    def get_queryset(self):
        return Room.objects.filter(
            is_private=False
        ).select_related("owner").order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["my_private_rooms"] = Room.objects.filter(
            is_private=True,
            members=self.request.user
        ).select_related("owner").order_by("-created_at")

        return context


class RoomCreateView(LoginRequiredMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = "rooms/room_form.html"
    success_url = reverse_lazy("room_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)

        self.object.members.add(self.request.user)

        return response


class RoomPasswordView(LoginRequiredMixin, FormView):
    template_name = "rooms/room_password.html"
    form_class = RoomPasswordForm

    def dispatch(self, request, *args, **kwargs):
        self.room = get_object_or_404(Room, pk=self.kwargs["pk"])

        if not self.room.can_enter(request.user):
            messages.error(request, "이 비공개 방에 입장할 권한이 없습니다.")
            return redirect("room_list")

        if not self.room.has_password():
            request.session[f"room_{self.room.pk}_verified"] = True
            return redirect("room_detail", pk=self.room.pk)

        if request.session.get(f"room_{self.room.pk}_verified"):
            return redirect("room_detail", pk=self.room.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        password = form.cleaned_data["password"]

        if self.room.check_password(password):
            self.request.session[f"room_{self.room.pk}_verified"] = True
            return redirect("room_detail", pk=self.room.pk)

        messages.error(self.request, "비밀번호가 올바르지 않습니다.")
        return self.form_invalid(form)


class RoomDetailView(LoginRequiredMixin, DetailView):
    model = Room
    template_name = "rooms/room_detail.html"
    context_object_name = "room"

    def dispatch(self, request, *args, **kwargs):
        room = get_object_or_404(Room, pk=self.kwargs["pk"])

        if not room.can_enter(request.user):
            messages.error(request, "이 비공개 방에 입장할 권한이 없습니다.")
            return redirect("room_list")

        if room.has_password() and not request.session.get(f"room_{room.pk}_verified"):
            return redirect("room_password", pk=room.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        messages_qs = self.object.messages.select_related(
            "sender",
            "receiver"
        ).filter(
            is_private=False
        ).order_by("-created_at")[:50]

        messages_list = list(reversed(messages_qs))

        for msg in messages_list:
            msg.read_by.add(self.request.user)

        context["messages"] = messages_list
        context["invite_form"] = InviteUserForm()
        context["room_members"] = self.object.members.all()

        return context
    

class InviteUserView(LoginRequiredMixin, View):
    def post(self, request, pk):
        room = get_object_or_404(Room, pk=pk)

        if room.owner != request.user:
            messages.error(request, "방장만 사용자를 초대할 수 있습니다.")
            return redirect("room_detail", pk=room.pk)

        form = InviteUserForm(request.POST)

        if form.is_valid():
            keyword = form.cleaned_data["keyword"].strip()

            user = User.objects.filter(
                Q(username=keyword) | Q(nickname=keyword)
            ).first()

            if not user:
                messages.error(request, "해당 사용자를 찾을 수 없습니다.")
                return redirect("room_detail", pk=room.pk)

            if room.members.filter(id=user.id).exists():
                messages.info(request, "이미 이 방에 참여 중인 사용자입니다.")
                return redirect("room_detail", pk=room.pk)

            room.members.add(user)
            messages.success(request, f"{user.nickname}님을 초대했습니다.")

        return redirect("room_detail", pk=room.pk)
    

class RoomDeleteView(LoginRequiredMixin, DeleteView):
    model = Room
    success_url = reverse_lazy("room_list")

    def dispatch(self, request, *args, **kwargs):
        room = get_object_or_404(
            Room,
            pk=self.kwargs["pk"]
        )

        is_owner = room.owner == request.user
        is_admin = request.user.is_staff

        if not (is_owner or is_admin):
            messages.error(
                request,
                "방장 또는 관리자만 삭제할 수 있습니다."
            )

            return redirect("room_list")

        self.object = room

        return super().dispatch(
            request,
            *args,
            **kwargs
        )

    def delete(self, request, *args, **kwargs):
        room_name = self.get_object().title

        messages.success(
            request,
            f"{room_name} 방이 삭제되었습니다."
        )

        return super().delete(
            request,
            *args,
            **kwargs
        )