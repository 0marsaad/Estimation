from django.urls import path
from . import views

urlpatterns = [
    path('round/', views.round_scores, name='round_scores'),
    path('game/', views.game_scores, name='game_scores'),
]
