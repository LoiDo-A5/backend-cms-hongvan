from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io


class SignatureExtractionTest(TestCase):
    def test_signature_extraction_with_varying_intensity(self):
        image = Image.new('RGB', (100, 100), color='white')
        for x in range(50):
            for y in range(50):
                image.putpixel((x, y), (0, 0, 0))

        image_file = io.BytesIO()
        image.save(image_file, format='JPEG')
        image_file.name = 'test_varying_intensity.jpg'
        image_file.seek(0)
        uploaded_file = SimpleUploadedFile('test_varying_intensity.jpg',
                                           image_file.read(), content_type='image/jpeg')

        response = self.client.post('/api/artwork/signature_extraction/', {'image': uploaded_file})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')

    def test_signature_extraction_failure_no_image(self):
        response = self.client.post('/api/artwork/signature_extraction/', {})
        self.assertEqual(response.status_code, 400)
