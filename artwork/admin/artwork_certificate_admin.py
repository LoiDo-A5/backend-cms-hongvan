import qrcode
import os
import hashlib
import json
from hashids import Hashids

from activity_log.models import CertificateLog
from artwork.models import ImageArtwork
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO

from django.http import HttpResponse
from django.contrib.staticfiles import finders
from django.conf import settings
from django.contrib import admin
from django.utils.translation import gettext as _

from zipfile import ZipFile
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from artwork.utils.const import TYPE_IMAGE, PLATFORM_NAME


class ArtworkCertificateAdmin(admin.ModelAdmin):
    actions = ['export_certificate_and_qr_code_en', 'export_certificate_and_qr_code_vi',
               'export_certificate_and_qr_code_bilingual']
    list_display = ('id', 'artwork_edition', 'code', 'artwork', 'owner', 'certificate_shipping',
                    'status', 'created_at', 'updated_at')
    list_filter = ('issued_by', 'issued_to')
    search_fields = ('code', 'issued_by__name', 'issued_to__name', 'status')

    readonly_fields = ('code', 'created_at', 'updated_at')

    def artwork(self, obj):
        if obj.artwork_edition and obj.artwork_edition.artwork:
            return f'{obj.artwork_edition.artwork.id} | {obj.artwork_edition.artwork.title}'
        return None

    def generate_certificate_view(self, certificate, language='en', qr_image=None,
                                  template_prefix='certificate-physical'):
        if certificate.artwork_edition is None:
            return HttpResponse('Cannot export certificate: Artwork edition is not associated with this certificate.')

        template = self.load_template_image(f'{template_prefix}-{language}.png')
        draw = ImageDraw.Draw(template)

        x_shift = 0
        if template_prefix == 'certificate-physical-and-tearm-condition':
            x_shift = 2480

        # Paths to font files
        regular_font_path = finders.find('ReadexPro-ExtraLight.ttf')
        bold_font_path = finders.find('ReadexPro-Bold.ttf')
        large_bold_font_path = finders.find('Afacad-Bold.ttf')

        # Font sizes
        regular_font_size = 28
        medium_font_size = 38
        large_font_size = 80

        # Regular fonts
        regular_font_small = ImageFont.truetype(regular_font_path, regular_font_size)
        regular_font_medium = ImageFont.truetype(regular_font_path, medium_font_size)

        # Bold fonts
        bold_font_medium = ImageFont.truetype(bold_font_path, medium_font_size)
        bold_font_large = ImageFont.truetype(large_bold_font_path, large_font_size)

        artwork_edition = certificate.artwork_edition
        created_at = certificate.created_at
        created_at_format = created_at.strftime('%d.%m.%Y')

        artwork = certificate.artwork_edition.artwork
        issued_user = certificate.issued_by
        issued_user_name = issued_user.legal_name if hasattr(issued_user, 'legal_name') else issued_user.username
        edition_number = 'Unique' if artwork.total_edition == 1 else artwork_edition.edition_number
        year_created = artwork.year_created if artwork.year_created else artwork.period_created or ''
        medium = artwork.medium.name
        title = artwork.title
        size_text = ''
        if artwork.size and artwork.size.height and artwork.size.width:
            size_text = f'{artwork.size.height}cm x {artwork.size.width}cm'
            if artwork.size.depth:
                size_text += f' x {artwork.size.depth}cm'
            size_text = size_text.replace('.00cm', 'cm')

        if edition_number == 'Unique':
            text_edition_number = edition_number
        else:
            text_edition_number = f'{edition_number}/{artwork.total_edition}'

        coordinates = {
            'certificate_number': (434, 356),

            'issue_date': (390, 397),

            'issued_user_name_bold': (175, 598),
            'issued_user_name_near_qr_code': (1450, 2320),
            'issued_user_role_en_near_qr_code': (1450, 2370),
            'issued_user_role_vi_near_qr_code': (1450, 2410),
            'artist_id': (348, 716),

            'text_title': (175, 1930),
            'artwork_title': (530, 1930),

            'text_size': (175, 2100),
            'size_artwork': (530, 2100),

            'text_medium': (175, 2200),
            'artwork_medium': (530, 2200),

            'text_creation_year': (175, 1700),
            'creation_year': (530, 1700),

            'text_edition_number': (175, 1750),
            'edition_number': (530, 1750),

            'content_undersigned': (175, 800),
            'content_property': (175, 2580),
        }

        if x_shift:
            coordinates = {k: (v[0] + x_shift, v[1]) for k, v in coordinates.items()}

        draw.text(coordinates['certificate_number'], f'{certificate.id}', fill='black', font=regular_font_small)
        draw.text(coordinates['issue_date'], f'{created_at_format}', fill='black', font=regular_font_small)

        draw.text(coordinates['issued_user_name_bold'], issued_user_name, fill='black', font=bold_font_large)
        draw.text(coordinates['issued_user_name_near_qr_code'], issued_user_name, fill='black', font=bold_font_medium)
        if language == 'vi':
            draw.text(
                coordinates['issued_user_role_vi_near_qr_code'],
                'Nghệ sĩ',
                fill='black',
                font=regular_font_small,
            )
        elif language == 'bilingual':
            draw.text(coordinates['issued_user_role_en_near_qr_code'], 'Artist', fill='black', font=regular_font_small)
            draw.text(coordinates['issued_user_role_vi_near_qr_code'], 'Nghệ sĩ', fill='black', font=regular_font_small)
        else:
            draw.text(coordinates['issued_user_role_en_near_qr_code'], 'Artist', fill='black', font=regular_font_small)
        draw.text(coordinates['artist_id'], f'{issued_user.uuid}', fill='black', font=regular_font_small)

        # Language-specific labels
        if language == 'vi':
            text_labels = {
                'title': 'Tiêu đề tác phẩm:',
                'size': 'Kích thước:',
                'medium': 'Chất liệu:',
                'creation_year': 'Năm hoàn thành:',
                'edition': 'Phiên bản #:',
            }
        else:
            text_labels = {
                'title': 'Title of artwork:',
                'size': 'Size:',
                'medium': 'Medium:',
                'creation_year': 'Year completed:',
                'edition': 'Edition #:',
            }

        draw.text(coordinates['text_title'], text_labels['title'], fill='black', font=regular_font_medium)

        self.draw_undersigned_text(draw, certificate, coordinates, regular_font_medium, bold_font_medium, language)
        new_artwork_y = self.draw_artwork_detail(draw, coordinates, bold_font_medium, max_width=650,
                                                 detail=title, detail_content='artwork_title')
        new_size_artwork_y = new_artwork_y + 15
        coordinates['text_size'] = (coordinates['text_size'][0], new_size_artwork_y)
        coordinates['size_artwork'] = (coordinates['size_artwork'][0], new_size_artwork_y)

        if size_text:
            draw.text(coordinates['text_size'], text_labels['size'], fill='black', font=regular_font_medium)
            draw.text(coordinates['size_artwork'], size_text, fill='black', font=regular_font_medium)
            updated_size_artwork_y = self.draw_artwork_detail(draw, coordinates, regular_font_medium, max_width=650,
                                                              detail=size_text, detail_content='size_artwork')
            new_medium_artwork_y = updated_size_artwork_y + 15
        else:
            new_medium_artwork_y = new_artwork_y + 15

        coordinates['text_medium'] = (coordinates['text_medium'][0], new_medium_artwork_y)
        coordinates['artwork_medium'] = (coordinates['artwork_medium'][0], new_medium_artwork_y)
        draw.text(coordinates['text_medium'], text_labels['medium'], fill='black', font=regular_font_medium)
        updated_medium_artwork_y = self.draw_artwork_detail(draw, coordinates, regular_font_medium, max_width=650,
                                                            detail=medium, detail_content='artwork_medium')
        new_creation_artwork_y = updated_medium_artwork_y + 15
        coordinates['text_creation_year'] = (coordinates['text_creation_year'][0], new_creation_artwork_y)
        coordinates['creation_year'] = (coordinates['creation_year'][0], new_creation_artwork_y)
        draw.text(coordinates['creation_year'], f'{year_created}', fill='black', font=regular_font_medium)
        updated_creation_artwork_y = self.draw_artwork_detail(draw, coordinates, regular_font_medium, max_width=650,
                                                              detail=text_labels['creation_year'],
                                                              detail_content='text_creation_year')

        new_edition_artwork_y = updated_creation_artwork_y + 15
        coordinates['text_edition_number'] = (coordinates['text_edition_number'][0], new_edition_artwork_y)
        coordinates['edition_number'] = (coordinates['edition_number'][0], new_edition_artwork_y)
        draw.text(coordinates['text_edition_number'], text_labels['edition'], fill='black', font=regular_font_medium)
        draw.text(coordinates['edition_number'], f'{text_edition_number}', fill='black', font=bold_font_medium)

        image_artwork = ImageArtwork.objects.filter(artwork=artwork_edition.artwork).first()
        if image_artwork:
            self.process_and_paste_artwork_image(template, image_artwork, x_shift=x_shift)

        certificate_signature = certificate.signature

        if certificate_signature:
            self.process_and_paste_artist_signature(template, certificate_signature, x_shift=x_shift)

        if qr_image:
            self.process_and_paste_qr_code(template, qr_image, x_shift=x_shift)

        with BytesIO() as buffer:
            template.save(buffer, 'PNG')
            buffer.seek(0)
            response = HttpResponse(buffer.read(), content_type='image/png')
            response['Content-Disposition'] = \
                (f'attachment; filename="{certificate.id}_{artwork.title}_{artwork_edition.edition_number}'
                 f'_certificate.png"')
        return response

    def load_template_image(self, filename):
        template_image_path = finders.find(filename)
        return Image.open(template_image_path)

    def process_and_paste_artwork_image(self, template, image_artwork, max_width=1204, max_height=680, x_shift=0):
        image_coordinates = (175 + x_shift, 1020)
        artwork_image_path = image_artwork.image
        artwork_image = Image.open(artwork_image_path)
        width_image, height_image = artwork_image.size

        if width_image >= 2.5 * height_image:
            max_width = 1520

        if width_image > height_image:
            width_resize = max_width
            height_resize = int((max_width * height_image) / width_image)
        else:
            height_resize = max_height
            width_resize = int((max_height * width_image) / height_image)

        # Ensure dimensions do not exceed the max constraints
        if width_resize > max_width:
            width_resize = max_width
            height_resize = int((max_width * height_image) / width_image)
        if height_resize > max_height:
            height_resize = max_height
            width_resize = int((max_height * width_image) / height_image)

        resized_artwork_image = artwork_image.resize((int(width_resize), int(height_resize)),
                                                     Image.Resampling.LANCZOS)
        image_to_paste = resized_artwork_image

        # Handle transparency if present
        if image_to_paste.mode == 'RGBA':
            mask = image_to_paste.split()[3]
        else:
            mask = None

        template.paste(image_to_paste, image_coordinates, mask)

    def process_and_paste_artist_signature(self, template, certificate_signature, x_shift=0):
        signature_coordinates = (1360 + x_shift, 2050)
        signature_image = Image.open(certificate_signature)
        signature_image.thumbnail((430, 300), Image.Resampling.LANCZOS)
        resized_signature_image = signature_image

        if resized_signature_image.mode == 'RGBA':
            # When pasting an image with transparency, use the alpha channel as the mask
            mask = resized_signature_image.split()[3]
        else:
            mask = None
        template.paste(resized_signature_image, signature_coordinates, mask)

    def process_and_paste_qr_code(self, template, qr_image, qr_size=450, x_shift=0):
        qr_coordinates = (1840 + x_shift, 2550)
        with BytesIO() as buffer:
            qr_image.save(buffer, format='PNG')
            buffer.seek(0)
            qr_img = Image.open(buffer).copy()
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        template.paste(qr_img, qr_coordinates)

    def wrap_text(self, text, font, max_width, draw):
        lines = []
        words = text.split()
        line = ''

        for word in words:
            test_line = line + word + ' '
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            if text_width > max_width:
                lines.append(line)
                line = word + ' '
            else:
                line = test_line

        if line:
            lines.append(line)
        return lines

    def draw_artwork_detail(self, draw, coordinates, regular_font_medium, max_width, detail, detail_content):
        line_spacing = 10
        coordinates = coordinates[detail_content]
        updated_y = self.add_wrapped_text(draw, detail, regular_font_medium, max_width, coordinates, line_spacing)
        return updated_y

    def draw_undersigned_text(self, draw, certificate, coordinates, regular_font_medium, bold_font_medium,
                              language='en'):
        issued_user = certificate.issued_by
        issued_user_name = issued_user.legal_name if hasattr(issued_user, 'legal_name') else issued_user.username

        if language == 'vi':
            created_at = certificate.created_at
            created_at_format = f'{created_at.day} tháng {created_at.month} năm {created_at.year}'
            segments = [
                ('Chứng nhận này xác nhận tính xác thực của tác phẩm nghệ thuật được đề cập. '
                 'Giấy chứng nhận này được cấp vào ngày ', regular_font_medium),
                (created_at_format, bold_font_medium),
                (' bởi hoạ sĩ ', regular_font_medium),
                (issued_user_name, bold_font_medium),
                (' và đảm bảo tính chính xác của các chi tiết và mô tả đi kèm.', regular_font_medium),
            ]
        else:
            created_at_format = certificate.created_at.strftime('%B %d, %Y')
            segments = [
                ('This certifies the authenticity of the artwork mentioned. '
                 'This certificate was issued on ', regular_font_medium),
                (created_at_format, bold_font_medium),
                (' by artist ', regular_font_medium),
                (issued_user_name, bold_font_medium),
                (' and guarantees the accuracy of the details and descriptions.', regular_font_medium),
            ]

        max_width = 2100
        line_spacing = 20
        coordinates = coordinates['content_undersigned']
        self.add_wrapped_text_mixed(draw, segments, max_width, coordinates, line_spacing)

    def draw_property_text(self, draw, certificate, coordinates, regular_font_medium):
        owner_name = certificate.owner.user.name if certificate.owner.user and certificate.owner.user.name \
            else certificate.owner.name
        first_sentence = f'This certificate belongs to {owner_name}'
        second_sentence = (
            f'Non account, born in {certificate.owner.year_of_birth}, identification number '
            f'Address {certificate.owner.address}'
        )

        if certificate.owner.contract_number:
            second_sentence += f', according to transaction contract number {certificate.owner.contract_number}.'

        max_width = 1150
        line_spacing = 30
        coordinates_first = coordinates['content_property']

        wrapped_first = self.wrap_text(first_sentence, regular_font_medium, max_width, draw)

        first_sentence_height = 0
        for line in wrapped_first:
            line_height = self.calculate_text_height(line, regular_font_medium, draw)
            first_sentence_height += line_height + line_spacing
        if first_sentence_height > 0:
            first_sentence_height -= line_spacing

        coordinates_second = (coordinates_first[0], coordinates_first[1] + first_sentence_height + line_spacing)

        self.add_wrapped_text(draw, first_sentence, regular_font_medium, max_width, coordinates_first, line_spacing)
        self.add_wrapped_text(draw, second_sentence, regular_font_medium, max_width, coordinates_second, line_spacing)

    def add_wrapped_text_mixed(self, draw, segments, max_width, coordinates, line_spacing):
        x_start = coordinates[0]
        x = x_start
        y = coordinates[1]

        for text, font in segments:
            words = text.split(' ')
            for i, word in enumerate(words):
                word_to_draw = word if i == len(words) - 1 else word + ' '
                bbox = draw.textbbox((0, 0), word_to_draw, font=font)
                word_width = bbox[2] - bbox[0]
                word_height = bbox[3] - bbox[1]

                if x + word_width > x_start + max_width and x > x_start:
                    x = x_start
                    y += word_height + line_spacing

                draw.text((x, y), word_to_draw, fill='black', font=font)
                x += word_width

        return y

    def add_wrapped_text(self, draw, text, font, max_width, coordinates, line_spacing, fill='black'):
        wrapped_lines = self.wrap_text(text, font, max_width, draw)
        y_offset = coordinates[1]

        for line in wrapped_lines:
            draw.text((coordinates[0], y_offset), line, fill=fill, font=font)
            text_height = self.calculate_text_height(line, font, draw)
            y_offset += text_height + line_spacing

        return y_offset  # Return the Y-coordinate just below the last line of text

    def calculate_text_height(self, text, font, draw):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]

    def export_certificate_and_qr_code_en(self, request, queryset):
        return self._export_certificate_and_qr_code(request, queryset, language='en')
    export_certificate_and_qr_code_en.short_description = 'Export Certificate & QR Code (English)'

    def export_certificate_and_qr_code_vi(self, request, queryset):
        return self._export_certificate_and_qr_code(request, queryset, language='vi')
    export_certificate_and_qr_code_vi.short_description = 'Export Certificate & QR Code (Tiếng Việt)'

    def export_certificate_and_qr_code_bilingual(self, request, queryset):
        return self._export_certificate_and_qr_code_bilingual(request, queryset)
    export_certificate_and_qr_code_bilingual.short_description = 'Export certificate and qr code bilingual'

    def _export_certificate_and_qr_code(self, request, queryset, language='en'):
        temp_folder = os.path.join(settings.MEDIA_ROOT, 'temp_certificates')
        os.makedirs(temp_folder, exist_ok=True)

        for certificate in queryset:
            CertificateLog.objects.create(
                user=request.user,
                certificate=certificate,
                data=_('Admin of GladiusArt printed the QR code of your certificate.'),
            )

        with BytesIO() as zip_buffer:
            with ZipFile(zip_buffer, 'w') as zip_file:
                for certificate in queryset:
                    self.process_certificate(certificate, temp_folder, zip_file, language)

            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="physical_certificate_and_qr_code_files.zip"'
            return response

    def _export_certificate_and_qr_code_bilingual(self, request, queryset):
        temp_folder = os.path.join(settings.MEDIA_ROOT, 'temp_certificates')
        os.makedirs(temp_folder, exist_ok=True)

        for certificate in queryset:
            CertificateLog.objects.create(
                user=request.user,
                certificate=certificate,
                data=_('Admin of GladiusArt printed the QR code of your certificate.'),
            )

        with BytesIO() as zip_buffer:
            with ZipFile(zip_buffer, 'w') as zip_file:
                for certificate in queryset:
                    self.process_certificate_tearm_condition_and_qr(certificate, temp_folder, zip_file)

            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = (
                'attachment; filename="certificate_physical_and_tearm_condition_and_qr_code_files.zip"'
            )
            return response

    def generate_certificate_qr_code(self, certificate, pieces):
        certificate_code_artwork = str(certificate.code)
        qr_images = []

        part_length = len(certificate_code_artwork) // pieces

        edition_id = int(certificate.artwork_edition_id)

        for i in range(pieces):
            start = i * part_length
            end = None if i == pieces - 1 else start + part_length
            code_part = certificate_code_artwork[start:end]

            hash_object = hashlib.sha256()
            hashids = Hashids()
            encoded_id = hashids.encode(certificate.id)

            hash_object.update(code_part.encode())
            hash_object.update(settings.SECRET_KEY.encode())
            hash_object.update(encoded_id.encode())

            hashed_code = hash_object.hexdigest()

            qr_data = {
                'platform': PLATFORM_NAME,
                'edition_id': edition_id,
                'order': i + 1,
                'total_code': pieces,
                'code': hashed_code,
            }

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(qr_data, separators=(',', ':'), ensure_ascii=False))
            qr.make(fit=True)

            img = qr.make_image(fill='black', back_color='white')
            qr_images.append(img)

        return qr_images

    def generate_term_and_condition(self, language='en'):
        template_term_and_condition = self.load_template_image(f'term-and-condition-{language}.png')
        with BytesIO() as buffer:
            template_term_and_condition.save(buffer, 'PNG')
            buffer.seek(0)
            response = HttpResponse(buffer.read(), content_type='image/png')
            response['Content-Disposition'] = 'attachment'
        return response

    def process_certificate(self, certificate, temp_folder, zip_file, language='en'):
        artwork = certificate.artwork_edition.artwork
        piece_artwork = artwork.piece
        artwork_edition = certificate.artwork_edition

        # Generate all QR codes: piece + 1 total
        qr_images = self.generate_certificate_qr_code(certificate, piece_artwork + 1)

        # First QR code is embedded on the certificate, rest are for the painting
        certificate_qr = qr_images[0]
        painting_qr_images = qr_images[1:]

        languages = ['en', 'vi'] if language == 'bilingual' else [language]

        for lang in languages:
            lang_suffix = f'_{lang}' if language == 'bilingual' else ''

            # Generate certificate with embedded QR code
            view_response = self.generate_certificate_view(certificate, language=lang, qr_image=certificate_qr)
            term_and_condition = self.generate_term_and_condition(language=lang)

            # Open certificate image (page 1)
            with BytesIO(view_response.content) as cert_buffer:
                cert_img = Image.open(cert_buffer).copy()

            # Open term_and_condition image (page 2)
            with BytesIO(term_and_condition.content) as tc_buffer:
                tc_img = Image.open(tc_buffer).copy()

            # Create combined PDF: physical_certificate (page 1) + term_and_condition (page 2)
            combined_pdf_path = self.generate_pdf_path(
                temp_folder, certificate, artwork, artwork_edition, TYPE_IMAGE.VIEW, lang_suffix,
            )
            self.create_combined_certificate_pdf(cert_img, tc_img, combined_pdf_path)
            zip_file.write(combined_pdf_path, os.path.basename(combined_pdf_path))
            os.remove(combined_pdf_path)

        # QR codes for painting (language-agnostic, excluding the one on certificate)
        if painting_qr_images:
            qr_pdf_path = self.generate_pdf_path(
                temp_folder, certificate, artwork, artwork_edition, TYPE_IMAGE.QR_CODE,
            )
            self.create_pdf(painting_qr_images, TYPE_IMAGE.QR_CODE, qr_pdf_path, certificate=certificate)
            zip_file.write(qr_pdf_path, os.path.basename(qr_pdf_path))
            os.remove(qr_pdf_path)

    def generate_pdf_path(self, temp_folder, certificate, artwork, artwork_edition, img_name, lang_suffix=''):
        artwork_title = artwork.title if artwork.title and artwork.title.upper() != 'N/A' else 'UntitledArtwork'
        edition_number = str(artwork_edition.edition_number) if artwork_edition.edition_number is not None else 'N_A'
        base_filename = f'{certificate.id}_{artwork_title}_{edition_number}'

        if img_name == TYPE_IMAGE.VIEW:
            return os.path.join(temp_folder,
                                f'{base_filename}_physical_certificate{lang_suffix}.pdf')
        elif img_name.startswith(TYPE_IMAGE.QR_CODE):
            return os.path.join(temp_folder,
                                f'{base_filename}_qr_code.pdf')
        return None

    def create_combined_certificate_pdf(self, cert_img, tc_img, pdf_path):
        """Create a single PDF with physical_certificate as page 1 and term_and_condition as page 2."""
        canvas_obj = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        # Page 1: physical certificate
        self.draw_view_image(cert_img, canvas_obj, width, height)
        canvas_obj.showPage()

        # Page 2: term and condition
        self.draw_view_image(tc_img, canvas_obj, width, height)

        canvas_obj.save()

    def create_two_page_pdf(self, page1_img, page2_img, pdf_path):
        canvas_obj = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        self.draw_view_image(page1_img, canvas_obj, width, height)
        canvas_obj.showPage()
        self.draw_view_image(page2_img, canvas_obj, width, height)
        canvas_obj.save()

    def process_certificate_tearm_condition_and_qr(self, certificate, temp_folder, zip_file):
        artwork = certificate.artwork_edition.artwork
        piece_artwork = artwork.piece
        artwork_edition = certificate.artwork_edition

        qr_images = self.generate_certificate_qr_code(certificate, piece_artwork + 1)
        certificate_qr = qr_images[0]
        painting_qr_images = qr_images[1:]

        view_vi_response = self.generate_certificate_view(
            certificate,
            language='vi',
            qr_image=certificate_qr,
            template_prefix='certificate-physical-and-tearm-condition',
        )
        view_en_response = self.generate_certificate_view(
            certificate,
            language='en',
            qr_image=certificate_qr,
            template_prefix='certificate-physical-and-tearm-condition',
        )

        with BytesIO(view_vi_response.content) as cert_vi_buffer:
            cert_vi_img = Image.open(cert_vi_buffer).copy()
        with BytesIO(view_en_response.content) as cert_en_buffer:
            cert_en_img = Image.open(cert_en_buffer).copy()

        cert_vi_img = cert_vi_img.rotate(-90, expand=True)
        cert_en_img = cert_en_img.rotate(-90, expand=True)

        artwork_title = artwork.title if artwork.title and artwork.title.upper() != 'N/A' else 'UntitledArtwork'
        edition_number = str(artwork_edition.edition_number) if artwork_edition.edition_number is not None else 'N_A'
        base_filename = f'{certificate.id}_{artwork_title}_{edition_number}'
        combined_pdf_path = os.path.join(
            temp_folder,
            f'{base_filename}_certificate_physical_and_tearm_condition.pdf',
        )
        self.create_two_page_pdf(cert_en_img, cert_vi_img, combined_pdf_path)
        zip_file.write(combined_pdf_path, os.path.basename(combined_pdf_path))
        os.remove(combined_pdf_path)

        if painting_qr_images:
            qr_pdf_path = self.generate_pdf_path(
                temp_folder, certificate, artwork, artwork_edition, TYPE_IMAGE.QR_CODE,
            )
            self.create_pdf(painting_qr_images, TYPE_IMAGE.QR_CODE, qr_pdf_path, certificate=certificate)
            zip_file.write(qr_pdf_path, os.path.basename(qr_pdf_path))
            os.remove(qr_pdf_path)

    def create_pdf(self, images, img_name, pdf_path, certificate=None):
        canvas_obj = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter

        if img_name.startswith(TYPE_IMAGE.VIEW) or img_name.startswith(TYPE_IMAGE.TERM_CONDITION):
            self.draw_view_image(images[0], canvas_obj, width, height)
        elif img_name.startswith(TYPE_IMAGE.QR_CODE):
            if certificate:
                margin = 24
                gutter = 18
                slot_width = (width - (margin * 2) - gutter) / 2
                slot_height = (height - (margin * 2) - gutter) / 2

                for i in range(0, len(images), 4):
                    if i != 0:
                        canvas_obj.showPage()

                    positions = [
                        # Top left
                        (margin, margin + slot_height + gutter),
                        # Top right
                        (margin + slot_width + gutter, margin + slot_height + gutter),
                        # Bottom left
                        (margin, margin),
                        # Bottom right
                        (margin + slot_width + gutter, margin),
                    ]

                    for j in range(4):
                        idx = i + j
                        if idx >= len(images):
                            break
                        page_img = self.generate_qr_code_certificate_page(
                            certificate,
                            images[idx],
                            piece_index=idx + 1,
                            total_pieces=len(images),
                        )
                        slot_x, slot_y = positions[j]
                        self.draw_image_in_slot(
                            canvas_obj,
                            page_img,
                            slot_x=slot_x,
                            slot_y=slot_y,
                            slot_width=slot_width,
                            slot_height=slot_height,
                        )
            else:
                self.draw_multiple_qr_codes(images, canvas_obj, width, height)

        canvas_obj.save()

    def draw_image_in_slot(self, canvas_obj, img, slot_x, slot_y, slot_width, slot_height):
        img_width, img_height = img.size
        aspect_ratio = img_width / img_height

        new_width = slot_width
        new_height = int(new_width / aspect_ratio)
        if new_height > slot_height:
            new_height = slot_height
            new_width = int(aspect_ratio * new_height)

        x_position = slot_x + (slot_width - new_width) / 2
        y_position = slot_y + (slot_height - new_height) / 2

        with BytesIO() as buffer:
            img.save(buffer, format='PNG')
            buffer.seek(0)
            canvas_obj.drawImage(ImageReader(buffer), x_position, y_position, width=new_width, height=new_height)

    def generate_qr_code_certificate_page(self, certificate, qr_image, piece_index=None, total_pieces=None):
        template = self.load_template_image('qr_code_certificate.png').convert('RGBA')
        draw = ImageDraw.Draw(template)

        regular_font_path = finders.find('ReadexPro-ExtraLight.ttf')
        bold_font_path = finders.find('ReadexPro-Bold.ttf')

        info_regular_font = ImageFont.truetype(regular_font_path, 45)
        info_bold_font = ImageFont.truetype(bold_font_path, 45)

        artwork_edition = certificate.artwork_edition
        artwork = artwork_edition.artwork

        issued_user = certificate.issued_by
        issued_user_name = issued_user.legal_name if hasattr(issued_user, 'legal_name') else issued_user.username

        edition_number = 'Unique' if artwork.total_edition == 1 else artwork_edition.edition_number
        if edition_number == 'Unique':
            text_edition_number = edition_number
        else:
            text_edition_number = f'{edition_number}/{artwork.total_edition}'

        year_created = artwork.year_created if artwork.year_created else artwork.period_created or ''
        medium = artwork.medium.name
        title = artwork.title
        size_text = ''
        if artwork.size and artwork.size.height and artwork.size.width:
            size_text = f'{artwork.size.height}cm x {artwork.size.width}cm'
            if artwork.size.depth:
                size_text += f' x {artwork.size.depth}cm'
            size_text = size_text.replace('.00cm', 'cm')

        qr_size = 800
        with BytesIO() as buffer:
            qr_image.save(buffer, format='PNG')
            buffer.seek(0)
            qr_img = Image.open(buffer).convert('RGBA')

        qr_gray = qr_img.convert('L')
        qr_content_mask = ImageOps.invert(qr_gray)
        bbox = qr_content_mask.getbbox()
        if bbox:
            qr_img = qr_img.crop(bbox)

        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

        left_box_x0 = 42
        left_box_y0 = 42
        left_box_x1 = 566
        left_box_y1 = 534
        qr_offset_x = 250
        qr_offset_y = 250
        qr_x = left_box_x0 + int(((left_box_x1 - left_box_x0) - qr_size) / 2) + qr_offset_x
        qr_y = left_box_y0 + int(((left_box_y1 - left_box_y0) - qr_size) / 2) + qr_offset_y
        template.alpha_composite(qr_img, dest=(qr_x, qr_y))

        # Top-right info box (match provided screenshot)
        info_shift_x = 600
        info_x0, info_y0 = 545 + info_shift_x, 22
        info_x1, info_y1 = 1005 + info_shift_x, 265
        draw.rectangle([(info_x0, info_y0), (info_x1, info_y1)], fill='white')

        info_text_shift_x = 40
        label_x = info_x0 + 20 + info_text_shift_x
        value_shift_x = 120
        value_x = info_x0 + 320 + info_text_shift_x + value_shift_x
        info_margin_top = 50
        y = info_y0 + info_margin_top
        row_gap = 90

        draw.text((label_x, y), 'Title of artwork:', fill='black', font=info_regular_font)
        draw.text((value_x, y), title or 'N/A', fill='black', font=info_bold_font)
        y += row_gap

        draw.text((label_x, y), 'Size:', fill='black', font=info_regular_font)
        draw.text((value_x, y), size_text or 'N/A', fill='black', font=info_regular_font)
        y += row_gap

        draw.text((label_x, y), 'Medium:', fill='black', font=info_regular_font)
        draw.text((value_x, y), medium or 'N/A', fill='black', font=info_regular_font)
        y += row_gap

        draw.text((label_x, y), 'Year completed:', fill='black', font=info_regular_font)
        draw.text((value_x, y), str(year_created) if year_created else 'N/A', fill='black', font=info_regular_font)
        y += row_gap

        draw.text((label_x, y), 'Edition #:', fill='black', font=info_regular_font)
        draw.text((value_x, y), str(text_edition_number) if text_edition_number else 'N/A',
                  fill='black', font=info_bold_font)

        # Bottom-right artist box (match screenshot: white text on black background)
        template_width, template_height = template.size
        artist_x = label_x
        bottom_margin = 105
        artist_label_y = template_height - bottom_margin
        artist_gap = 70
        artist_name_y = artist_label_y - artist_gap
        draw.text((artist_x, artist_name_y), issued_user_name, fill='black', font=info_bold_font)
        draw.text((artist_x, artist_label_y), 'Artist', fill='black', font=info_regular_font)

        return template.convert('RGB')

    def draw_view_image(self, img, canvas_obj, page_width, page_height):
        img_width, img_height = img.size
        aspect_ratio = img_width / img_height
        new_width = page_width
        new_height = int(new_width / aspect_ratio)

        if new_height > page_height:
            new_height = page_height
            new_width = int(aspect_ratio * new_height)

        x_position = (page_width - new_width) / 2
        y_position = (page_height - new_height) / 2

        with BytesIO() as buffer:
            img.save(buffer, format='PNG')
            buffer.seek(0)
            canvas_obj.drawImage(ImageReader(buffer), x_position, y_position, width=new_width, height=new_height)

    def draw_multiple_qr_codes(self, images, canvas_obj, page_width, page_height):
        positions = self.get_qr_positions(len(images), page_width, page_height)

        for i, img in enumerate(images):
            if i % len(positions) == 0 and i != 0:
                canvas_obj.showPage()  # create new page pdf
            x, y = positions[i % len(positions)]
            img = img.resize((150, 150), Image.Resampling.LANCZOS)
            with BytesIO() as buffer:
                img.save(buffer, format='PNG')
                buffer.seek(0)
                canvas_obj.drawImage(ImageReader(buffer), x, y, width=150, height=150)

    def get_qr_positions(self, piece, width, height):
        qr_size = 150
        positions = [
            (100, height - qr_size - 100),  # Top left
            (width - qr_size - 100, height - qr_size - 100),  # Top right
            (100, 100),  # Bottom left
            (width - qr_size - 100, 100),  # Bottom right
        ]
        return positions
