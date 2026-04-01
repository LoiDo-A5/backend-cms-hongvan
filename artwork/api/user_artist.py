from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from artwork.models import ArtworkArtist
from core.accounts.models import User
from core.accounts.api.user_api import UserSerializer


class UserArtworkArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtworkArtist
        fields = ('artist_name', 'contact_info', 'year_of_birth', 'year_of_death')

    def validate(self, attrs):
        user = self.context['request'].user
        if self.instance.create_user != user:
            raise PermissionDenied('You do not have permission to edit this artist.')

        if ArtworkArtist.objects.filter(artist_name=attrs.get('artist_name'),
                                        year_of_birth=attrs.get('year_of_birth'),
                                        create_user=user).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError(
                'An artist with the same name, year of birth already exists.',
            )

        return attrs


class UserArtistApi(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, identifier):
        try:
            artist = get_object_or_404(User, uuid=identifier)
            serializer = UserSerializer(artist)
            return Response(serializer.data)
        except Http404:
            artist = get_object_or_404(ArtworkArtist, id=identifier)
            serializer = UserArtworkArtistSerializer(artist)

            return Response(serializer.data)

    def patch(self, request, identifier):
        artist = get_object_or_404(ArtworkArtist, pk=identifier)
        serializer = UserArtworkArtistSerializer(artist, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
