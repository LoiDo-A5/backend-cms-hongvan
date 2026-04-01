from django.http import HttpResponse, HttpResponseBadRequest
from PIL import Image, ImageOps
from io import BytesIO
import numpy as np
from rest_framework.views import APIView


class SignatureExtraction(APIView):
    def post(self, request, *args, **kwargs):
        image_file = request.FILES.get('image')
        if not image_file:
            return HttpResponseBadRequest('No image provided')

        image = Image.open(image_file)

        # Convert to grayscale image
        gray = image.convert('L')

        # Apply thresholds automatically
        np_image = np.array(gray)
        mean = np.mean(np_image)
        signature = ImageOps.autocontrast(gray, cutoff=mean)

        # Create images with alpha channels (transparency)
        transparent_img = Image.new('RGBA', signature.size, (0, 0, 0, 0))
        for x in range(signature.width):
            for y in range(signature.height):
                if signature.getpixel((x, y)) < 128:
                    transparent_img.putpixel((x, y), (0, 0, 0, 255))  # Black signature on transparent background

        buffer = BytesIO()
        transparent_img.save(buffer, format='PNG')
        buffer.seek(0)

        return HttpResponse(buffer, content_type='image/png')
