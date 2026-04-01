from rest_framework import status, mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from django.http import Http404

from artwork.models.certificate_request import CertificateRequest
from artwork.serializers.certificate_request import ApproveCertificateRequestSerializer
from artwork.serializers.certificate_request import UpdateCertificateRequestSerializer
from artwork.serializers.certificate_request import RejectCertificateRequestSerializer
from artwork.serializers.certificate_request import ReviewCertificateSerializer


class CertificateRequestViewSet(mixins.UpdateModelMixin, GenericViewSet):
    queryset = CertificateRequest.objects.all()
    serializer_class = RejectCertificateRequestSerializer
    permission_classes = (IsAuthenticated,)
    search_fields = ('artwork_edition__artwork__title', 'status')

    def get_serializer_class(self):
        if self.action == 'approve_certificate_request':
            return ApproveCertificateRequestSerializer
        if self.action == 'review_certificate_request':
            return ReviewCertificateSerializer
        if self.action == 'partial_update':
            return UpdateCertificateRequestSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=['post'])
    def approve_certificate_request(self, request, *args, **kwargs):
        instance = self.get_object()
        has_certificate = getattr(instance.artwork_edition, 'certificate', None)
        has_permission_approve = instance.request_to == self.request.user

        if not has_permission_approve:
            raise PermissionDenied('You do not have permission to approve this certificate request.')
        if has_certificate:
            raise PermissionDenied('This artwork edition already has a certificate.')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.process(instance)

        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def reject_certificate_request(self, request, *args, **kwargs):
        instance = self.get_object()
        has_certificate = getattr(instance.artwork_edition, 'certificate', None)
        has_permission_approve = instance.request_to == self.request.user

        if not has_permission_approve:
            raise PermissionDenied('You do not have permission to reject this certificate request.')
        if has_certificate:
            raise PermissionDenied('This artwork edition already has a certificate.')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.process(instance)

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def review_certificate_request(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        try:
            artwork = get_object_or_404(self.get_queryset(), id=pk)
            serializer = self.get_serializer(artwork)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Http404:
            return Response({'detail': 'not found.'}, status=status.HTTP_404_NOT_FOUND)
