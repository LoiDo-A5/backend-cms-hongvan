from unittest import mock

from botocore.exceptions import ClientError
from rest_framework import status

from core.accounts.tests.api.base_user_test import BaseUserTest


@mock.patch('common.api.s3_presigned.boto3')
class FirmwareUploadApiTests(BaseUserTest):
    def test_get_signed_url_success(self, boto3):
        boto3.client.return_value.generate_presigned_post.return_value = {
            'url': 'https://BUCKET.s3.amazonaws.com/',
            'fields': {
                'key': 'Firmware_20211202_171500.bin',
                'AWSAccessKeyId': 'AWS_KEY',
                'policy': 'POLICY',
                'signature': 'SIGNATURE',
            },
        }

        response = self.client.get(
            '/api/common/s3_presigned/', {
                'bucket': 'bucket_name',
                'key': 'ABC',
                'path': 'firmware',
            },
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['url'], 'https://BUCKET.s3.amazonaws.com/', response.content)
        self.assertEqual(response.data['fields']['key'], 'Firmware_20211202_171500.bin', response.content)

    def test_get_signed_url_fail(self, boto3):
        boto3.client.return_value.generate_presigned_post.side_effect = ClientError(
            {'Error': {'Code': 'ParameterNotFound', 'Message': 'The parameter was not found'}},
            'SignedPostUrl',
        )

        response = self.client.get(
            '/api/common/s3_presigned/', {
                'bucket': 'bucket_name',
                'key': 'ABC',
                'path': 'firmware',
            },
        )

        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data, None)
