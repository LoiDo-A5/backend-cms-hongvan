from artwork.factories.artwork import ArtworkFactory
from artwork.models import ArtWork
from artwork.models.artwork_artist import ArtworkArtist
from artwork.utils.migrations.migrate_move_data_to_artwork_artist import move_data_to_artwork_artist
from common.tests.isolated_cache_test_case import TestCase
from core.accounts.factories.user import UserFactory


class MigrateMoveDataToArtworkArtist(TestCase):
    def test_migrate_move_data_to_artwork_artist(self):
        artwork = ArtworkFactory(artist_name='Tam', contact_info_artist='tam@art.com', year_of_birth_artist='1980')
        artwork1 = ArtworkFactory(artist_name='Loi', contact_info_artist='loi@art.com', year_of_birth_artist='1990')
        artwork2 = ArtworkFactory(artist_name='Son', contact_info_artist='son@art.com', year_of_birth_artist='2000')

        move_data_to_artwork_artist(ArtWork, ArtworkArtist)

        artwork.refresh_from_db()
        artwork1.refresh_from_db()
        artwork2.refresh_from_db()

        self.assertIsNotNone(artwork.artist_artwork)
        self.assertEqual(artwork.artist_artwork.artist_name, 'Tam')
        self.assertEqual(artwork.artist_artwork.contact_info, 'tam@art.com')
        self.assertEqual(artwork.artist_artwork.year_of_birth, '1980')

        self.assertIsNotNone(artwork1.artist_artwork)
        self.assertEqual(artwork1.artist_artwork.artist_name, 'Loi')
        self.assertEqual(artwork1.artist_artwork.contact_info, 'loi@art.com')
        self.assertEqual(artwork1.artist_artwork.year_of_birth, '1990')

        self.assertIsNotNone(artwork2.artist_artwork)
        self.assertEqual(artwork2.artist_artwork.artist_name, 'Son')
        self.assertEqual(artwork2.artist_artwork.contact_info, 'son@art.com')
        self.assertEqual(artwork2.artist_artwork.year_of_birth, '2000')

    def test_migrate_move_data_to_artwork_artist_with_duplicate(self):
        user = UserFactory()
        artwork = ArtworkFactory(owner=user ,artist_name='Tam', contact_info_artist='tam@art.com', year_of_birth_artist='1980')
        artwork1 = ArtworkFactory(owner=user, artist_name='Tam', contact_info_artist='tam@art.com', year_of_birth_artist='1980')

        move_data_to_artwork_artist(ArtWork, ArtworkArtist)

        artwork.refresh_from_db()
        artwork1.refresh_from_db()

        self.assertEqual(artwork.artist_artwork, artwork1.artist_artwork)
        self.assertEqual(artwork.artist_artwork.artist_name, 'Tam')
        self.assertEqual(artwork.artist_artwork.year_of_birth, '1980')

    def test_migrate_move_data_to_artwork_artist_with_no_artist_name(self):
        artwork = ArtworkFactory(artist_name='', contact_info_artist='tam@art.com', year_of_birth_artist='1980',
                                 artist_artwork=None)
        artwork1 = ArtworkFactory(artist_name=None, contact_info_artist='loi@art.com', year_of_birth_artist='1990',
                                  artist_artwork=None)

        move_data_to_artwork_artist(ArtWork, ArtworkArtist)

        artwork.refresh_from_db()
        artwork1.refresh_from_db()

        self.assertIsNone(artwork.artist_artwork)
        self.assertIsNone(artwork1.artist_artwork)
