# encoding=utf8
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, AbstractUser

from test_project import controllers

class BaseModel(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(default=now, db_index=True)

    class Meta:
        abstract = True

class Cards(BaseModel, controllers.CardsController):

    class Meta:
        abstract = True

class Player(BaseModel, controllers.PlayerController):
    pass

class Ace(Cards, controllers.AceController):
    player = models.ForeignKey(Player)

class Hearts(Cards, controllers.HeartsController):
    broken = models.BooleanField(default=False)
    player = models.ForeignKey(Player)
