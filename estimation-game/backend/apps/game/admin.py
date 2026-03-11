from django.contrib import admin
from .models import Game, Round, Bid, Estimation, TrickResult

admin.site.register(Game)
admin.site.register(Round)
admin.site.register(Bid)
admin.site.register(Estimation)
admin.site.register(TrickResult)
