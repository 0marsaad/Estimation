"""
WebSocket consumer for real-time game events.

Each room has its own channel group: "room_{room_code}"

Events sent to client:
    room_join, player_ready, dash_call_declared, bid_submitted,
    bid_winner, estimate_submitted, round_finished, score_updated, game_finished

Events received from client:
    { "type": "<event_name>", ...payload }
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


class GameConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.group_name = f'room_{self.room_code}'

        user = self.scope.get('user')
        if not user or isinstance(user, AnonymousUser):
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(self.group_name, {
            'type': 'game_event',
            'event': 'room_join',
            'username': user.username,
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Invalid JSON'}))
            return

        event_type = data.get('type')
        handler = getattr(self, f'handle_{event_type}', None)
        if handler:
            await handler(data)
        else:
            await self.send(text_data=json.dumps({'error': f'Unknown event: {event_type}'}))

    # ---- Outbound helpers ----

    async def game_event(self, event):
        """Relay group messages to the WebSocket client."""
        payload = {k: v for k, v in event.items() if k != 'type'}
        await self.send(text_data=json.dumps(payload))

    # ---- Inbound handlers ----

    async def handle_player_ready(self, data):
        await self.channel_layer.group_send(self.group_name, {
            'type': 'game_event',
            'event': 'player_ready',
            'username': self.scope['user'].username,
        })

    async def handle_dash_call_declared(self, data):
        await self.channel_layer.group_send(self.group_name, {
            'type': 'game_event',
            'event': 'dash_call_declared',
            'username': self.scope['user'].username,
            'is_dash_call': data.get('is_dash_call', False),
        })

    async def handle_bid_submitted(self, data):
        await self.channel_layer.group_send(self.group_name, {
            'type': 'game_event',
            'event': 'bid_submitted',
            'username': self.scope['user'].username,
            'tricks_called': data.get('tricks_called'),
            'trump': data.get('trump'),
            'is_pass': data.get('is_pass', False),
        })

    async def handle_estimate_submitted(self, data):
        await self.channel_layer.group_send(self.group_name, {
            'type': 'game_event',
            'event': 'estimate_submitted',
            'username': self.scope['user'].username,
            'tricks_estimated': data.get('tricks_estimated'),
        })

    async def handle_round_finished(self, data):
        await self.channel_layer.group_send(self.group_name, {
            'type': 'game_event',
            'event': 'round_finished',
            'round_number': data.get('round_number'),
        })

    async def handle_score_updated(self, data):
        await self.channel_layer.group_send(self.group_name, {
            'type': 'game_event',
            'event': 'score_updated',
            'scores': data.get('scores', []),
        })
