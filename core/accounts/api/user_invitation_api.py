from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status

from artwork.models import ArtWork, ArtworkCertificate, CertificateRequest
from core.accounts.models import UserInvitation, User
from django.conf import settings
from django.core.mail import send_mail


class UserInvitationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_null=True)
    password = serializers.CharField(write_only=True)
    sender = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    role_recipient = serializers.CharField(allow_null=True, required=False)

    class Meta:
        model = UserInvitation
        fields = (
            'sender',
            'recipient',
            'artwork',
            'certificate',
            'certificate_request',
            'email',
            'role_recipient',
            'password',
        )

    def send_invitation_email(self, username, password, email, artwork, certificate, cer_request):
        title_artwork = next((title for title in [
            getattr(artwork, 'title', None),
            getattr(certificate.artwork_edition.artwork, 'title', None)
            if certificate and certificate.artwork_edition and certificate.artwork_edition.artwork else None,
            getattr(cer_request.artwork_edition.artwork, 'title', None)
            if cer_request and cer_request.artwork_edition and cer_request.artwork_edition.artwork else None,
        ] if title is not None), 'Artwork')

        if artwork is not None:
            email_subject_vi = 'Xác nhận sáng tác'
            email_subject_en = 'Copyright Confirmation'
        elif certificate is not None:
            email_subject_vi = 'Xác nhận quyền sở hữu'
            email_subject_en = 'Certificate Issuance'
        elif cer_request is not None:
            email_subject_vi = 'Cấp bản chứng nhận'
            email_subject_en = 'Ownership Confirmation'
        else:
            email_subject_vi = 'Thông tin'
            email_subject_en = 'Information'

        subject = 'Mời bạn tham gia vào hệ thống'
        message_html = ('<p>Kính gửi,<br>'
                        'Dear,</p>'

                        f'<p>Chúng tôi xin thông báo bạn vừa nhận được yêu cầu <strong>[{email_subject_vi}]</strong> '
                        f'liên quan đến tác phẩm <strong>[{title_artwork}]</strong> thông qua '
                        f'nền tảng <strong>GladiusArt</strong>.<br>'
                        'We would like to inform you that you have just received a request for '
                        f'<strong>[{email_subject_en}]</strong> '
                        f'regarding the work <strong>[{title_artwork}]</strong> through the '
                        f'<strong>GladiusArt</strong> platform.</p>'

                        '<p><strong>Vui lòng truy cập</strong>'
                        ' <a href="https://gladiusart.com/">https://gladiusart.com/</a> .'
                        ' Sau đó, bạn có thể đăng nhập ngay và bắt đầu xét duyệt các yêu cầu hiện có bằng thông '
                        'tin tài khoản như sau:<br>'
                        '<strong>Please visit</strong>'
                        ' <a href="https://gladiusart.com/">https://gladiusart.com/</a>.'
                        ' Then, you can log in immediately and start reviewing the pending requests with the '
                        'following account information:</p>'

                        '<p><strong>Tài khoản của bạn:</strong><br>'
                        'Username: {username}<br>'
                        'Password: {password}</p>'

                        '<p><strong>Your account:</strong><br>'
                        'Username: {username}<br>'
                        'Password: {password}</p>'

                        '<p><strong>Giới thiệu về GladiusArt:</strong><br>'
                        'Chúng tôi là một đội ngũ đam mê về việc xây dựng một cộng đồng đam mê nghệ thuật,'
                        ' nơi mà mọi người có thể tương tác và trao đổi kiến thức, kinh nghiệm trong môi trường trực '
                        'tuyến dễ dàng và thoải mái.'
                        ' Nền tảng của chúng tôi không chỉ cung cấp các tài nguyên hữu ích mà còn thúc đẩy sự kết '
                        'nối giữa những người qua nhiều ngôn ngữ khác nhau.</p>'

                        '<p><strong>About GladiusArt:</strong><br>'
                        'We are a team passionate about building a community of art enthusiasts, where everyone '
                        'can interact and exchange knowledge and experiences in an online environment easily and '
                        'comfortably.'
                        ' Our platform not only provides useful resources but also fosters connections among people'
                        ' from various language backgrounds.</p>'

                        '<p>Nếu bạn có bất kỳ câu hỏi hoặc ý kiến đóng góp, đừng ngần ngại liên hệ với chúng tôi'
                        ' qua số điện thoại <strong>0919304647 (Trương Đình Bảo)</strong>,'
                        ' email <strong>gladiusartproject@gmail.com</strong>, hoặc'
                        ' zalo <strong>0919304647</strong>.<br>'
                        'If you have any questions or feedback, please feel free to contact us'
                        ' via phone at <strong>0919304647 (Trương Đình Bảo)</strong>,'
                        ' email at <strong>gladiusartproject@gmail.com</strong>, or'
                        ' Zalo at <strong>0919304647</strong>.</p>'

                        '<p>Chúng tôi rất mong được chào đón Quý vị đến với cộng đồng của chúng tôi!<br>'
                        'We are looking forward to welcoming you to our community!</p>'
                        ).format(username=username, password=password, title_artwork=title_artwork)

        sender_email = settings.EMAIL_HOST_USER
        recipient_email = email

        send_mail(
            subject,
            message_html,
            sender_email,
            [recipient_email],
            fail_silently=False,
            html_message=message_html,
        )

    def process_tracking_invitation(self):
        password = self.validated_data['password']
        recipient = User.objects.get(id=self.validated_data['recipient'].id)

        artwork = None
        artwork_obj = self.validated_data.get('artwork')
        if artwork_obj is not None:
            artwork = ArtWork.objects.filter(id=artwork_obj.id).first()

        certificate = None
        certificate_obj = self.validated_data.get('certificate')
        if certificate_obj is not None:
            certificate = ArtworkCertificate.objects.filter(id=certificate_obj.id).first()

        certificate_request = None
        certificate_request_obj = self.validated_data.get('certificate_request')
        if certificate_request_obj is not None:
            certificate_request = CertificateRequest.objects.filter(id=certificate_request_obj.id).first()

        invitation = UserInvitation.objects.create(
            sender=self.context['request'].user,
            recipient=recipient,
            email=self.validated_data.get('email', recipient.email),
            role_recipient=self.validated_data.get('role_recipient', recipient.role),
            artwork=artwork,
            certificate=certificate,
            certificate_request=certificate_request,
        )

        self.send_invitation_email(recipient.username, password, recipient.email, artwork, certificate,
                                   certificate_request)

        return invitation


class UserInvitationApi(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserInvitationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = serializer.process_tracking_invitation()

        return Response(
            {
                'invitation': UserInvitationSerializer(invitation).data,
            }, status=status.HTTP_200_OK,
        )
