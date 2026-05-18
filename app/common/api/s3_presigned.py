import logging

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from rest_framework import serializers
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.authentication import TokenAuthentication

from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


def create_presigned_post(
    bucket_name, object_name,
    fields=None, conditions=None, expiration=3600,
):
    """Generate a presigned URL S3 POST request to upload a file

    :param bucket_name: string
    :param object_name: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """

    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_post(
            bucket_name,
            object_name,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expiration,
        )
    except ClientError as e:
        logging.error(e)
        return None

    return response


class S3PresignedSerializer(serializers.Serializer):
    key = serializers.CharField(required=True)

    def process(self):
        key = self.validated_data['key']
        return create_presigned_post(settings.AWS_STORAGE_BUCKET_NAME, f'{key}')


class S3PresignedApi(GenericAPIView):
    serializer_class = S3PresignedSerializer
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get(self, request):
        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        data = serializer.process()
        return Response(data=data, status=status.HTTP_200_OK)
