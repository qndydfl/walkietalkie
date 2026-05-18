import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import DirectRoom, DirectMessage


class DirectMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group_name = f"dm_{self.room_id}"
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        allowed = await self.is_room_member()

        if not allowed:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "").strip()

        if not message:
            return

        saved = await self.save_message(message)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "dm_message",
                "message_id": saved["id"],
                "message": saved["content"],
                "sender_id": self.user.id,
                "sender": self.user.nickname,
                "created_at": saved["created_at"],
                "read_count": saved["read_count"],
            }
        )

    async def dm_message(self, event):
        await self.mark_as_read(event["message_id"])

        await self.send(text_data=json.dumps({
            "type": "dm_message",
            "message_id": event["message_id"],
            "message": event["message"],
            "sender_id": event["sender_id"],
            "sender": event["sender"],
            "created_at": event["created_at"],
            "read_count": event["read_count"],
        }))

    @database_sync_to_async
    def is_room_member(self):
        return DirectRoom.objects.filter(
            id=self.room_id,
            users=self.user
        ).exists()

    @database_sync_to_async
    def save_message(self, content):
        room = DirectRoom.objects.get(id=self.room_id)

        message = DirectMessage.objects.create(
            room=room,
            sender=self.user,
            content=content
        )

        message.read_by.add(self.user)

        return {
            "id": message.id,
            "content": message.content,
            "created_at": message.created_at.strftime("%H:%M"),
            "read_count": message.read_by.count(),
        }

    @database_sync_to_async
    def mark_as_read(self, message_id):
        message = DirectMessage.objects.get(id=message_id)
        message.read_by.add(self.user)