from django.test import TestCase

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.share_link import ShareLinkFactory
from artwork.models import ArtWork, ShareLink
from artwork.utils.migrations.migrate_share_link_artwork import migrate_shared_items_to_artwork_field
from core.accounts.factories.user import UserFactory


class MigrateShareLinkArtworkTests(TestCase):
    def test_migrate_artworks_from_shared_items_to_artwork_field(self):
        user = UserFactory()
        artwork1 = ArtworkFactory(owner=user)
        artwork2 = ArtworkFactory(owner=user)
        share_link = ShareLinkFactory(
            user=user,
            shared_items=[
                {'id': artwork1.id, 'type': 'artwork'},
                {'id': artwork2.id, 'type': 'artwork'},
            ],
        )
        
        migrate_shared_items_to_artwork_field(ShareLink, ArtWork)
        
        share_link.refresh_from_db()
        self.assertEqual(share_link.artwork.count(), 2)
        self.assertIn(artwork1, share_link.artwork.all())
        self.assertIn(artwork2, share_link.artwork.all())

    def test_migrate_ignores_non_artwork_items_in_shared_items(self):
        user = UserFactory()
        artwork1 = ArtworkFactory(owner=user)
        share_link = ShareLinkFactory(
            user=user,
            shared_items=[
                {'id': artwork1.id, 'type': 'artwork'},
                {'id': 999, 'type': 'exhibition'},
            ],
        )
        
        migrate_shared_items_to_artwork_field(ShareLink, ArtWork)
        
        share_link.refresh_from_db()
        self.assertEqual(share_link.artwork.count(), 1)
        self.assertIn(artwork1, share_link.artwork.all())

    def test_migrate_handles_empty_shared_items(self):
        share_link = ShareLinkFactory(shared_items=[])
        
        migrate_shared_items_to_artwork_field(ShareLink, ArtWork)
        
        share_link.refresh_from_db()
        self.assertEqual(share_link.artwork.count(), 0)

    def test_migrate_processes_multiple_share_links(self):
        user1 = UserFactory()
        user2 = UserFactory()
        artwork1 = ArtworkFactory(owner=user1)
        artwork2 = ArtworkFactory(owner=user2)
        share_link1 = ShareLinkFactory(
            user=user1,
            shared_items=[{'id': artwork1.id, 'type': 'artwork'}],
        )
        share_link2 = ShareLinkFactory(
            user=user2,
            shared_items=[{'id': artwork2.id, 'type': 'artwork'}],
        )
        
        migrate_shared_items_to_artwork_field(ShareLink, ArtWork)
        
        share_link1.refresh_from_db()
        share_link2.refresh_from_db()
        self.assertEqual(share_link1.artwork.count(), 1)
        self.assertIn(artwork1, share_link1.artwork.all())
        self.assertEqual(share_link2.artwork.count(), 1)
        self.assertIn(artwork2, share_link2.artwork.all())
