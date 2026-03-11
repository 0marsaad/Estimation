from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.game_start, name='game_start'),
    path('state/', views.game_state, name='game_state'),
    path('bid/', views.bid, name='bid'),
    path('estimate/', views.estimate, name='estimate'),
    path('play/', views.play, name='play'),
    path('next-round/', views.next_round, name='next_round'),
    path('scores/', views.scores, name='scores'),
    path('advance/', views.advance_phase_view, name='advance_phase'),
]
