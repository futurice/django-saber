from django.conf import settings
from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, RequestFactory
from django.utils.timezone import now
from django.core.urlresolvers import reverse

from .models import Ace, Hearts, Player
from djangosaber.saber import Memory, Traverse

class BaseSuite(TransactionTestCase):
    pass

class SaberTest(BaseSuite):
    def setUp(self):
        self.rf = RequestFactory()

    def test_controller_missing(self):
        player1,_ = Player.objects.get_or_create(name='Bob')
        memory = Memory()
        memory.initialize()
        world = Traverse(memory.data)
        with self.assertRaises(AttributeError):
            world.player[0].winning()

    def test_access(self):
        player1,_ = Player.objects.get_or_create(name='Bob')
        player2,_ = Player.objects.get_or_create(name='Jane')

        ace1,_ = Ace.objects.get_or_create(name='A1', player=player1)
        ace2,_ = Ace.objects.get_or_create(name='A2', player=player1)
        ace3,_ = Ace.objects.get_or_create(name='A3', player=player2)
        h1,_ = Hearts.objects.get_or_create(name='H1', player=player2)
        h2,_ = Hearts.objects.get_or_create(name='H2', player=player2)

        memory = Memory(controllers=['test_project.controllers'])
        memory.initialize()
        self.assertEquals(ace1.id, memory.data['ace'][0]['id'])
        self.assertEquals(h1.id, memory.data['hearts'][0]['id'])

        self.assertEquals(Ace.objects.all().count(), len(memory.data['ace']))
        self.assertEquals(Hearts.objects.all().count(), len(memory.data['hearts']))

        world = Traverse(memory.data)
        self.assertEquals(world.ace[0].beats_hearts(), Ace.objects.all().first().beats_hearts())
        self.assertTrue(False == world.player[0].winning() == Player.objects.all().first().winning())

    def test_relation(self):
        player1,_ = Player.objects.get_or_create(name='Bob')
        ace1,_ = Ace.objects.get_or_create(name='A1', player=player1)

        memory = Memory(controllers=['test_project.controllers'])
        memory.initialize()
        world = Traverse(memory.data)
        self.assertEqual(world.ace[0].player.name, 'Bob')
