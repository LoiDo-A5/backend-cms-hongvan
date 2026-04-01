from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from artwork.models.artwork_certificate import ArtworkCertificate
from artwork.serializers.artwork_certificate import (
    TransferOwnerSerializer,
    TransferOwnerWithRoleArtistSerializer, TransferOwnerArtworkWithRoleArtistSerializer,
)


class TransferOwnerApi(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransferOwnerSerializer

    def post(self, request, code):
        certificate = get_object_or_404(
            ArtworkCertificate.objects.select_related(
                'issued_to',
                'artwork_edition',
                'artwork_edition__artwork',
            ),
            code=code,
        )

        serializer = self.get_serializer(
            data=request.data,
            context={
                'request': request,
                'certificate': certificate,
            },
        )
        serializer.is_valid(raise_exception=True)

        result = serializer.process()
        certificate = result['certificate']
        from_user_id = result['from_user_id']
        to_user_id = result['to_user_id']

        return Response(
            {
                'success': True,
                'certificate_id': certificate.id,
                'certificate_code': str(certificate.code),
                'from_user_id': from_user_id,
                'to_user_id': to_user_id,
                'message': 'Ownership transferred',
            },
            status=status.HTTP_200_OK,
        )


class TransferOwnerArtworkWithRoleArtistApi(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransferOwnerArtworkWithRoleArtistSerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={
                'request': request,
            },
        )
        serializer.is_valid(raise_exception=True)

        result = serializer.process()

        return Response(
            {
                'success': True,
                'from_user_id': result['from_user_id'],
                'to_user_id': result['to_user_id'],
                'artwork_id': result['artwork_id'],
                'message': 'Ownership transferred',
            },
            status=status.HTTP_200_OK,
        )


class TransferOwnerWithRoleArtistApi(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransferOwnerWithRoleArtistSerializer

    def post(self, request, code):
        certificate = get_object_or_404(
            ArtworkCertificate.objects.select_related(
                'issued_to',
                'artwork_edition',
                'artwork_edition__artwork',
            ),
            code=code,
        )

        serializer = self.get_serializer(
            data=request.data,
            context={
                'request': request,
                'certificate': certificate,
            },
        )
        serializer.is_valid(raise_exception=True)

        result = serializer.process()
        certificate = result['certificate']
        from_user_id = result['from_user_id']
        to_user_id = result['to_user_id']

        return Response(
            {
                'success': True,
                'certificate_id': certificate.id,
                'certificate_code': str(certificate.code),
                'from_user_id': from_user_id,
                'to_user_id': to_user_id,
                'message': 'Ownership transferred',
            },
            status=status.HTTP_200_OK,
        )
