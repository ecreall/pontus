
import io
import os
from PIL import Image, ImageFilter

from pontus import log


IMAGES_FORMATS = [{'id': 'big', 'size': (600, 400)},
                  {'id': 'xlarge', 'size': (400, 200)},
                  {'id': 'large', 'size': (300, 200)},
                  {'id': 'medium', 'size': (125, 188)},
                  {'id': 'small', 'size': (128, 85)},
                  {'id': 'profil', 'size': (140, 140)}]


AVAILABLE_FORMATS = [img_format['id'] for img_format in IMAGES_FORMATS]


def generate_images(fp, filename):
    result = []
    for img_format in IMAGES_FORMATS:
        try:
            img = Image.open(fp)
            if img.mode == 'P':
                img = img.convert('RGB')
        except OSError as e:
            log.warning(e)
            return result

        size = img_format['size']
        img.thumbnail(size, Image.ANTIALIAS)
        buf = io.BytesIO()
        ext = os.path.splitext(filename)[1].lower()
        try:
            img.save(buf, Image.EXTENSION.get(ext, 'jpeg'))
            buf.seek(0)
            img_data = img_format.copy()
            img_data['fp'] = buf
            result.append(img_data)
        except Exception as e:
            log.warning(e)


    return result
