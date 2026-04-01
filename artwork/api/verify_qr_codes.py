from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework import serializers
from rest_framework import status

from activity_log.models import CertificateLog
from artwork.models import ArtworkCertificate
from django.conf import settings
import hashlib
from hashids import Hashids

from artwork.utils.const import VERIFY


class QRCodeSerializer(serializers.Serializer):
    platform = serializers.CharField()
    edition_id = serializers.IntegerField()
    order = serializers.IntegerField()
    total_code = serializers.IntegerField()
    code = serializers.CharField()


class VerifyQrCodes(APIView):
    def post(self, request, *args, **kwargs):
        user = self.request.user
        serializer = QRCodeSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        qr_codes = serializer.validated_data

        if not qr_codes:
            return Response({'message': 'No QR codes provided'}, status=status.HTTP_400_BAD_REQUEST)

        edition_id = qr_codes[0]['edition_id']
        total_codes = qr_codes[0]['total_code']

        for qr_code in qr_codes:
            if qr_code['edition_id'] != edition_id:
                return Response({'message': 'Edition id does not match'},
                                status=status.HTTP_400_BAD_REQUEST)

        if len(qr_codes) != total_codes:
            return Response({'message': 'Number of QR codes does not match the total code value'},
                            status=status.HTTP_400_BAD_REQUEST)

        certificate = get_object_or_404(ArtworkCertificate, artwork_edition_id=edition_id)
        certificate_code = str(certificate.code)
        part_length = len(certificate_code) // total_codes

        qr_codes = sorted(qr_codes, key=lambda x: x['order'])
        valid_codes = 0

        for i, qr_code in enumerate(qr_codes):
            start = i * part_length
            end = start + part_length
            code_part = certificate_code[start:end]

            hash_object = hashlib.sha256()
            hashids = Hashids()
            encoded_id = hashids.encode(certificate.id)

            hash_object.update(code_part.encode())
            hash_object.update(settings.SECRET_KEY.encode())
            hash_object.update(encoded_id.encode())

            hashed_code = hash_object.hexdigest()
            if hashed_code == qr_code['code']:
                valid_codes += 1

        if valid_codes > 0 and valid_codes == len(qr_codes):
            if not user.is_anonymous:
                CertificateLog.objects.create(
                    user=user,
                    certificate=certificate,
                    action_type=VERIFY,
                )
            return Response({'certificate_code': certificate_code}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'QR codes do not match'}, status=status.HTTP_400_BAD_REQUEST)
