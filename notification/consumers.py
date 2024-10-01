import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from regular_lesson.models import Lesson
from accounts.models import CustomUser
from notification.models import Notification

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "notification"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        type = text_data_json['type']
        user_id = text_data_json['user_id']
        message = text_data_json['message']

        if type == 'contact':
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'contact',
                    'user_id': user_id,
                    'message': message,
                }
            )

            await self.create_notification(user_id, message)
            
    async def contact(self, event):
        user_id = event['user_id']
        message = event['message']

        await self.send(text_data=json.dumps({
            'type': 'message',
            'user_id': user_id,
            'message': message,
        }))

    @sync_to_async
    def create_notification(self, user_id, message):
        owner = CustomUser.objects.get(is_owner=True)
        sender = CustomUser.objects.get(id=user_id)

        # 通知の作成
        Notification.objects.create(
            user=owner,
            message=message,
            sender=sender,
        )