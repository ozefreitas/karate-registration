import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MatchConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.group_name = f'match_{self.match_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'broadcast_message',
                'text': text_data,
            }
        )

    async def broadcast_message(self, event):
        await self.send(text_data=event['text'])