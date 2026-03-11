import random
import string
from django.db import models
from django.conf import settings


def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class Room(models.Model):
    class Status(models.TextChoices):
        WAITING = 'WAITING', 'Waiting'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        FINISHED = 'FINISHED', 'Finished'

    room_code = models.CharField(max_length=6, unique=True, default=generate_room_code)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rooms'

    def __str__(self):
        return f'Room {self.room_code} ({self.status})'


class Player(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='players')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    seat_position = models.PositiveSmallIntegerField()  # 0–3
    total_score = models.IntegerField(default=0)

    class Meta:
        db_table = 'players'
        unique_together = [('room', 'seat_position'), ('room', 'user')]

    def __str__(self):
        return f'{self.user.username} in {self.room.room_code} (seat {self.seat_position})'
