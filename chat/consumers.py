import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from rooms.models import Room
from .models import Message
from accounts.models import User

online_users = {}


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"room_{self.room_id}"
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        online_users.setdefault(self.room_id, {})
        online_users[self.room_id][self.user.id] = {
            "id": self.user.id,
            "nickname": self.user.nickname,
            "name": self.user.name,
        }

        await self.accept()
        await self.broadcast_users()

    async def disconnect(self, close_code):
        if self.room_id in online_users:
            online_users[self.room_id].pop(self.user.id, None)

        await self.broadcast_users()

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        data_type = data.get("type", "chat")

        if data_type == "audio":
            audio_data = data.get("audio")
            receiver_id = data.get("receiver_id")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "voice_message",
                    "audio": audio_data,
                    "sender_id": self.user.id,
                    "sender": self.user.nickname,
                    "receiver_id": receiver_id,
                    "message_type": "private" if receiver_id else "public",
                }
            )
            return

        message = data.get("message", "").strip()
        receiver_id = data.get("receiver_id")

        if not message:
            return

        is_private = bool(receiver_id)

        saved_message = await self.save_message(
            room_id=self.room_id,
            sender_id=self.user.id,
            receiver_id=receiver_id,
            content=message,
            is_private=is_private,
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message_id": saved_message["id"],
                "message": saved_message["content"],
                "sender_id": self.user.id,
                "sender": self.user.nickname,
                "receiver_id": receiver_id,
                "message_type": "private" if is_private else "public",
                "created_at": saved_message["created_at"],
                "read_count": saved_message["read_count"],
            }
        )

    async def chat_message(self, event):
        receiver_id = event.get("receiver_id")

        if event["message_type"] == "private":
            if str(self.user.id) not in [str(event["sender_id"]), str(receiver_id)]:
                return

        await self.send(text_data=json.dumps(event))

    async def broadcast_users(self):
        users = list(online_users.get(self.room_id, {}).values())

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_list",
                "users": users,
            }
        )

    async def user_list(self, event):
        await self.send(text_data=json.dumps({
            "type": "users",
            "users": event["users"],
        }))

    async def voice_message(self, event):
        receiver_id = event.get("receiver_id")

        if event["message_type"] == "private":
            if str(self.user.id) not in [str(event["sender_id"]), str(receiver_id)]:
                return

        if str(self.user.id) == str(event["sender_id"]):
            return

        await self.send(text_data=json.dumps({
            "type": "audio",
            "audio": event["audio"],
            "sender_id": event["sender_id"],
            "sender": event["sender"],
            "message_type": event["message_type"],
        }))

    @database_sync_to_async
    def save_message(self, room_id, sender_id, receiver_id, content, is_private):
        room = Room.objects.get(id=room_id)
        sender = User.objects.get(id=sender_id)

        receiver = None
        if receiver_id:
            receiver = User.objects.get(id=receiver_id)

        message = Message.objects.create(
            room=room,
            sender=sender,
            receiver=receiver,
            content=content,
            is_private=is_private,
        )

        message.read_by.add(sender)

        return {
            "id": message.id,
            "content": message.content,
            "created_at": message.created_at.strftime("%Y-%m-%d %H:%M"),
            "read_count": message.read_by.count(),
        }