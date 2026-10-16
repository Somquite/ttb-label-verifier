"""Low-memory offline OCR for free-tier deployment. No external API calls."""
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import pytesseract
from pytesseract import Output

def extract(image: Image.Image):
    image = ImageOps.exif_transpose(image).convert('RGB')
    image.thumbnail((1700, 1700))
    image = ImageEnhance.Contrast(image).enhance(1.4)
    image = image.filter(ImageFilter.SHARPEN)
    data = pytesseract.image_to_data(image, lang='eng', config='--oem 1 --psm 11', output_type=Output.DICT, timeout=25)
    groups = {}
    for i, word in enumerate(data['text']):
        word = word.strip()
        try: conf = float(data['conf'][i])
        except (ValueError, TypeError): continue
        if not word or conf < 30: continue
        key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
        groups.setdefault(key, []).append((word, conf))
    return [{'text':' '.join(w for w,_ in words), 'confidence':round(sum(c for _,c in words)/len(words)/100,3)} for words in groups.values()]
