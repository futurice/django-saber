from django.conf import settings
from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, RequestFactory
from django.utils.timezone import now
from django.core.urlresolvers import reverse

from test_project.models import Ace, Hearts, Player
from djangosaber.saber import Memory, Traverse, key

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

        ace1,_ = Ace.objects.get_or_create(name='A1', pla_yer=player1)
        ace2,_ = Ace.objects.get_or_create(name='A2', pla_yer=player1)
        ace3,_ = Ace.objects.get_or_create(name='A3', pla_yer=player2)
        h1,_ = Hearts.objects.get_or_create(name='H1', player=player2)
        h2,_ = Hearts.objects.get_or_create(name='H2', player=player2)

        memory = Memory(controllers=['test_project.controllers'])
        memory.initialize()
        self.assertEquals(ace1.id, memory.data['ace'][0].id)
        self.assertEquals(h1.id, memory.data['hearts'][0].id)

        self.assertEquals(Ace.objects.all().count(), len(memory.data['ace']))
        self.assertEquals(Hearts.objects.all().count(), len(memory.data['hearts']))

        world = Traverse(memory.data)
        self.assertEquals(world.ace[0].beats_hearts(), Ace.objects.all().first().beats_hearts())
        self.assertTrue(False == world.player[0].winning() == Player.objects.all().first().winning())
        
        self.assertEquals(world.ace[0].pk, ace1.pk)

    def test_relation(self):
        player1,_ = Player.objects.get_or_create(name='Bob')
        ace1,_ = Ace.objects.get_or_create(name='A1', pla_yer=player1)

        memory = Memory(controllers=['test_project.controllers'])
        memory.initialize()
        world = Traverse(memory.data)
        self.assertEqual(world.ace[0].pla_yer.name, 'Bob')

    def test_index_creation(self):
        player1,_ = Player.objects.get_or_create(name='Bob')
        player2,_ = Player.objects.get_or_create(name='Jane')

        ace1,_ = Ace.objects.get_or_create(name='A1', pla_yer=player1)
        ace2,_ = Ace.objects.get_or_create(name='A2', pla_yer=player1)
        ace3,_ = Ace.objects.get_or_create(name='A3', pla_yer=player2)
        h1,_ = Hearts.objects.get_or_create(name='H1', player=player2)
        h2,_ = Hearts.objects.get_or_create(name='H2', player=player2)

        exclude=['contenttype', 'group', 'permission',]
        mem = Memory(controllers=['test_project.controllers'])
        mem.initialize(exclude=exclude)
        mem.create_indexes(exclude=exclude)

        db = Traverse(mem.data)
        p = filter(lambda x: getattr(x, 'id')==player1.pk, db.player)[0]

        self.assertEquals(key('player', str(p.id)), 'player.%s'%p.id)
        self.assertEquals([k.id for k in p.ace], [ace1.pk, ace2.pk])

        #  map(operator.attrgetter('id') => aget('id')
        self.assertEquals([k.id for k in db.index_lookup('player', p.id, 'ace')],
                          [ace1.pk, ace2.pk])

        # reverse FK
        from pprint import pprint as pp
        self.assertTrue(isinstance(db.hearts[0].player, object))
        self.assertEquals(db.hearts[0].player.id, player2.pk)

        self.assertEquals(db.ace[0].pla_yer.id, player1.id)

        self.assertEquals(
                len(db.player[0].ace),
                len(player1.ace_set.all()))

        self.assertEquals(
                len(db.player[0].ace_set),
                len([ace1.pk, ace2.pk]))

        self.assertEquals(
                len(db.player[0].ace_set.all()),
                len([ace1.pk, ace2.pk]))

        self.assertEquals(db.player[0].ace_set[0].id, ace1.pk)

