import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, Room
from accounts.models import CustomUser
import base64

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, code):
       await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)

        if 'markOwnUnreadMessagesAsRead' in data:
            await self.handle_mark_own_unread_messages_as_read(data)
        else:
            message = data['message']
            username = data['username']
            date_added = data['date_added']
            room = data['room']
            image = data.get('image')
            file = data.get('file')

            if file:
                await self.save_file_upload(username, room, file)

            elif message:
                await self.save_message(username, room, message, date_added)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': username,
                    'date_added': date_added,
                    'room': room,
                    'image': image,
                    'file': file,
                }
            )

    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        date_added = event['date_added']
        room = event['room']
        image = event.get('image')
        file = event.get('file')

        await self.send(text_data=json.dumps({
                'message': message,
                'username': username,
                'room': room,
                'date_added': date_added,
                'image': image,
                'file': file,
        }))

    async def handle_mark_own_unread_messages_as_read(self, data):
        username = data.get('username')
        room = data.get('room')

        await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'is_read',
                    'markAsRead': True,
                    'username': username,
                    'room': room,
                }
            )

    async def is_read(self, event):
        username = event['username']
        room = event['room']

        await self.send(text_data=json.dumps({
                'markAsRead': True,
                'username': username,
                'room': room,
        }))
        
    @sync_to_async
    def save_message(self, username, room, message, date_added):
        user = CustomUser.objects.get(username=username)
        room = Room.objects.get(slug=room)
        
        saved_message = Message.objects.create(user=user, room=room, content=message, date_added=date_added)

    @sync_to_async
    def save_file_upload(self, username, room, file):
        user = CustomUser.objects.get(username=username)
        room = Room.objects.get(slug=room)

        file_bytes = base64.b64decode(file)
        Message.objects.create(user=user, room=room, file=file_bytes)

    @sync_to_async
    def mark_message_as_read(self, username, room):
        user = CustomUser.objects.get(username=username)
        room = Room.objects.get(slug=room)

        # 対象のユーザーが送信したメッセージを取得し、未読のものを既読に設定する
        Message.objects.filter(user=user, room=room, is_read=False).update(is_read=True)