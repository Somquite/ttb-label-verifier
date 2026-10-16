import asyncio
import io
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from .ocr import extract
from .validation import validate

MAX_BYTES = 12 * 1024 * 1024
MAX_FILES = 20  # Free-tier safety limit; 300-file batching needs larger hosting
app = FastAPI(title='TTB Label Verification Prototype', version='1.0.0')
app.add_middleware(CORSMiddleware, allow_origins=[s.strip() for s in os.getenv('CORS_ORIGINS','http://localhost:5173,http://localhost:8080').split(',')], allow_methods=['GET','POST'], allow_headers=['*'])
executor = ThreadPoolExecutor(max_workers=1)

@app.get('/api/health')
def health(): return {'status':'ok'}

def process(content, filename, application):
    start=time.perf_counter()
    try:
        image=Image.open(io.BytesIO(content))
        image.verify()
        image=Image.open(io.BytesIO(content))
        if image.width*image.height > 25_000_000: raise ValueError('Image exceeds 25 megapixels')
    except (UnidentifiedImageError, OSError, ValueError) as e:
        raise ValueError('Invalid or oversized image: '+str(e))
    items=extract(image)
    lines=[x['text'] for x in items]
    verification=validate(application,lines)
    return {'filename':filename,'elapsed_ms':round((time.perf_counter()-start)*1000), 'ocr_lines':items, **verification}

@app.post('/api/verify')
async def verify(files: list[UploadFile] = File(...), application: str = Form(...)):
    if len(files)>MAX_FILES: raise HTTPException(400,'Maximum 20 files per batch on free hosting')
    try:
        data=json.loads(application)
        if not isinstance(data,dict): raise ValueError()
    except (ValueError,TypeError): raise HTTPException(400,'application must be a JSON object')
    results=[]
    loop=asyncio.get_running_loop()
    for f in files:
        if not (f.content_type or '').startswith('image/'):
            results.append({'filename':f.filename,'error':'Only image files are accepted'}); continue
        content=await f.read(MAX_BYTES+1)
        if len(content)>MAX_BYTES:
            results.append({'filename':f.filename,'error':'File exceeds 12 MB'}); continue
        try:
            result=await loop.run_in_executor(executor,process,content,f.filename or 'image',data)
            results.append(result)
        except Exception as e:
            # Avoid leaking internal errors or filesystem paths to clients.
            results.append({'filename':f.filename,'error': 'Image could not be analyzed. Confirm model installation and image quality.' if not isinstance(e,ValueError) else str(e)})
    return {'results':results,'total':len(results)}

# Single Render web service: serve the compiled React UI and API on one origin.
STATIC_DIR = os.getenv('STATIC_DIR', '/app/static')
if os.path.isdir(STATIC_DIR):
    app.mount('/assets', StaticFiles(directory=os.path.join(STATIC_DIR, 'assets')), name='assets')
    @app.get('/', include_in_schema=False)
    def index(): return FileResponse(os.path.join(STATIC_DIR, 'index.html'))
