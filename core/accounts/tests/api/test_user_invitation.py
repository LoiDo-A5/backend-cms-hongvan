from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.certificate_request import CertificateRequestFactory
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from rest_framework import status


class UserInvitationApiTests(BaseUserTest):
    def test_user_invitation_with_artwork_success(self):
        recipient = UserFactory()
        artwork = ArtworkFactory()

        data = {
            'sender': self.user.id,
            'recipient': recipient.id,
            'artwork': artwork.id,
            'email': recipient.email,
            'password': recipient.password,
            'role_recipient': 1,
        }
        response = self.client.post(
            '/api/accounts/user_invitation/', data,
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)

    def test_user_invitation_with_certificate_success(self):
        recipient = UserFactory()
        certificate = ArtworkCertificateFactory()

        data = {
            'sender': self.user.id,
            'recipient': recipient.id,
            'certificate': certificate.id,
            'email': recipient.email,
            'password': recipient.password,
            'role_recipient': 1,
        }
        response = self.client.post(
            '/api/accounts/user_invitation/', data,
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)

    def test_user_invitation_with_request_certificate_success(self):
        recipient = UserFactory()
        certificate_request = CertificateRequestFactory()

        data = {
            'sender': self.user.id,
            'recipient': recipient.id,
            'certificate_request': certificate_request.id,
            'email': recipient.email,
            'password': recipient.password,
            'role_recipient': 1,
        }
        response = self.client.post(
            '/api/accounts/user_invitation/', data,
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)

    def test_user_invitation(self):
        recipient = UserFactory()

        data = {
            'sender': self.user.id,
            'recipient': recipient.id,
            'email': recipient.email,
            'password': recipient.password,
            'role_recipient': 1,
        }
        response = self.client.post(
            '/api/accounts/user_invitation/', data,
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
