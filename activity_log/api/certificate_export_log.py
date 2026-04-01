from rest_framework.permissions import IsAuthenticated

from rest_framework.generics import ListAPIView

from activity_log.models import CertificateLog
from activity_log.serializers.certificate_log import CertificateExportLogSerializer
from artwork.utils.const import EXPORT


class CertificateExportLogApi(ListAPIView):
    queryset = CertificateLog.objects.all()
    serializer_class = CertificateExportLogSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        certificate_id = self.request.query_params.get('certificate_id')
        queryset = CertificateLog.objects.filter(certificate_id=certificate_id, action_type=EXPORT)
        return queryset
