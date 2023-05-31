import asyncio
import json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async

from .models import Thread, ChatMessage


class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print('connected', event)
        
        # await asyncio.sleep(10)
        # await self.send({
        #     "type": "websocket.close"
        # })
        other_user = self.scope['url_route']['kwargs']['username']
        me = self.scope['user']
        # print(other_user, me)
        thread_obj = await self.get_thread(me, other_user)
        self.thread_obj = thread_obj
        # print(thread_obj)
        chat_room = f'thread_{thread_obj.pk}'
        self.chat_room = chat_room
        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )
        await self.send({
            "type": "websocket.accept"
        })
        # await self.send({
        #     "type": "websocket.send",
        #     "text": "Hello world"
        # })

    async def websocket_receive(self, event):
        # when a message is received from the websocket
        print('received', event)
        front_text = event.get('text', None)
        if front_text is not None:
            print(front_text)
            loaded_dict_data = json.loads(front_text)
            msg = loaded_dict_data.get('message')
            print(msg)
            user = self.scope['user']
            self.user = user
            username = 'default'
            if user.is_authenticated:
                username = user.username
            myFinalResponse = {
                'message': msg,
                'username': username
            }
            await self.create_chat(msg)
            await self.channel_layer.group_send(
                self.chat_room,
                {
                    "type": "chat_message",
                    "text": json.dumps(myFinalResponse)
                }

            )
            # await self.send({
            #     "type": "websocket.send",
            #     "text": json.dumps(myFinalResponse)
            # })

    async def chat_message(self, event):
        await self.send({
            "type": "websocket.send",
            "text": event['text']
        })

    async def websocket_disconnect(self, event):
        # when the socket connects
        print('disconnected', event)

    @database_sync_to_async
    def get_thread(self, user, other_username):
        return Thread.objects.get_or_new(user, other_username)[0]

    @database_sync_to_async
    def create_chat(self, msg):
        ChatMessage.objects.create(thread=self.thread_obj, user=self.user, message=msg)