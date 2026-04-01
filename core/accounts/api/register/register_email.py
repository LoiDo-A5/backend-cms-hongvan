from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.accounts.api.user_api import UserSerializer
from core.accounts.models import User
from django.utils.translation import gettext


class RegisterEmailSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    name = serializers.CharField(required=False)
    role = serializers.CharField(allow_null=True, required=False)
    year_of_birth = serializers.IntegerField(required=False, allow_null=True)
    place_of_birth = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = (
            'name',
            'email',
            'phone_number',
            'password1',
            'password2',
            'time_zone',
            'role',
            'year_of_birth',
            'place_of_birth',
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError(gettext("The two password fields didn't match."))

        attrs['password'] = attrs.pop('password1')
        attrs.pop('password2')

        email = attrs.get('email', None)
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                'email': 'Email address already in use',
            })

        phone_number = attrs.get('phone_number', None)
        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            raise serializers.ValidationError({
                'phone_number': 'Phone number already in use',
            })

        attrs['username'] = email if email else phone_number
        return attrs

    def process_register_member(self):
        user = User(
            is_active=True,
            is_phone_verified=False,
            **self.validated_data,
        )
        password = self.validated_data['password']
        user.set_password(password)
        user.save()

        return user, None


class RegisterEmailApi(GenericAPIView):
    serializer_class = RegisterEmailSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, _ = serializer.process_register_member()

        return Response(
            {
                'user': UserSerializer(user).data,
            }, status.HTTP_200_OK,
        )
