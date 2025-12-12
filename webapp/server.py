"""
BRIA Pixel Playground - Production Server

Endpoints:
- POST /api/generate        -> generate pseudo pixel art via BRIA API
- POST /api/convert         -> convert to perfect pixel art (block size selection or auto)
- POST /api/remove-bg       -> remove background from latest/selected image

Storage: Supabase Storage (cloud) - files are uploaded immediately after processing.
Local temp files are cleaned up after upload.
"""

import os
import sys
import tempfile
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from pixel_playground import BriaPixelPlaygroundV2

# Import Supabase storage (required for production)
from supabase_storage import get_storage, is_storage_enabled

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Use system temp directory for ephemeral file processing
TEMP_DIR = Path(tempfile.gettempdir()) / "bria_pixel_playground"
TEMP_DIR.mkdir(exist_ok=True)

STATIC_DIR.mkdir(exist_ok=True)

print(f"[Server] Production mode - Supabase storage only")
print(f"[Server] Temp directory: {TEMP_DIR}")


@contextmanager
def _workdir(path: Path):
    """Temporarily change the working directory."""
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


@contextmanager
def _temp_workdir():
    """Create and use a temporary working directory, cleaned up after use."""
    work_dir = Path(tempfile.mkdtemp(dir=TEMP_DIR))
    prev = Path.cwd()
    os.chdir(work_dir)
    try:
        yield work_dir
    finally:
        os.chdir(prev)
        # Clean up temp files after processing
        try:
            shutil.rmtree(work_dir)
        except Exception as e:
            print(f"[Server] Temp cleanup warning: {e}")


class GenerateRequest(BaseModel):
    prompt: str
    style: str = "16bit"
    seed: Optional[int] = None


class ConvertRequest(BaseModel):
    image_name: Optional[str] = None  # defaults to last generated
    block_size: Optional[int] = None
    auto_detect: bool = True


class RemoveBgRequest(BaseModel):
    image_name: Optional[str] = None  # defaults to last editable / generated


app = FastAPI(title="BRIA Pixel Playground")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static assets only (no local outputs in production)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Try to bootstrap the core pipeline once
try:
    playground = BriaPixelPlaygroundV2()
    INIT_ERROR = None
except Exception as exc:  # noqa: BLE001
    playground = None
    INIT_ERROR = str(exc)


def _ensure_ready():
    """Ensure the playground and storage are initialized."""
    if INIT_ERROR:
        raise HTTPException(status_code=500, detail=f"Init error: {INIT_ERROR}")
    if playground is None:
        raise HTTPException(status_code=500, detail="Playground not initialized")
    if not is_storage_enabled():
        raise HTTPException(status_code=500, detail="Supabase storage not configured")


def _upload_to_cloud(local_path: Path, remote_name: str = None) -> str:
    """
    Upload a file to Supabase storage.
    
    Returns the public URL. Raises exception if upload fails.
    """
    storage = get_storage()
    if not storage:
        raise HTTPException(status_code=500, detail="Storage not available")
    
    if not local_path.exists():
        raise HTTPException(status_code=500, detail=f"File not found: {local_path}")
    
    remote_name = remote_name or local_path.name
    result = storage.upload_file(str(local_path), remote_name)
    
    if not result:
        raise HTTPException(status_code=500, detail=f"Upload failed: {remote_name}")
    
    return result["public_url"]


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the single-page app."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("Frontend not built yet.", status_code=200)
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.post("/api/generate")
def generate(req: GenerateRequest):
    """Generate pseudo pixel art using the BRIA API."""
    _ensure_ready()
    
    with _temp_workdir() as work_dir:
        result = playground.generate_pixel_art(
            req.prompt,
            style=req.style,
            seed=req.seed,
            save_prompts=False,
        )
        
        image_name = Path(result["image_file"]).name
        image_path = work_dir / image_name
        
        # Upload image to Supabase
        image_url = _upload_to_cloud(image_path, image_name)
        
        # Upload structured prompt JSON
        storage = get_storage()
        if storage and result.get("structured_prompt"):
            json_name = image_name.replace("_image.png", "_structured_prompt.json")
            storage.upload_json(result["structured_prompt"], json_name)
    
    # Store in session for subsequent operations
    playground.session["last_web_image"] = image_name
    playground.session["last_image_url"] = image_url
    
    return {
        "image_name": image_name,
        "image_url": image_url,
        "seed": result.get("seed"),
        "style": result.get("style"),
        "style_name": result.get("style_name"),
        "structured_prompt": result.get("structured_prompt"),
    }


@app.post("/api/convert")
def convert(req: ConvertRequest):
    """Convert pseudo pixel art to perfect pixel art."""
    _ensure_ready()
    
    target_name = req.image_name or playground.session.get("last_web_image")
    if not target_name:
        raise HTTPException(status_code=400, detail="No image specified.")

    storage = get_storage()
    
    with _temp_workdir() as work_dir:
        # Download image from Supabase to temp directory
        input_path = work_dir / target_name
        image_data = storage.download_file(target_name, str(input_path))
        
        if not image_data:
            raise HTTPException(status_code=404, detail=f"Image not found in storage: {target_name}")

        try:
            result = playground.convert_to_perfect_pixelart(
                input_png=str(input_path),
                block_size=req.block_size,
                auto_detect=req.auto_detect,
            )
        except Exception as exc:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Conversion error: {exc}")

        if not result:
            raise HTTPException(status_code=500, detail="Conversion failed.")

        # Upload all generated files to Supabase
        svg_url = None
        raster_url = None
        editable_url = None
        
        if result.get("svg_file"):
            svg_path = work_dir / result["svg_file"]
            svg_url = _upload_to_cloud(svg_path)
        
        if result.get("rasterized_png_file"):
            raster_path = work_dir / result["rasterized_png_file"]
            raster_url = _upload_to_cloud(raster_path)
        
        if result.get("editable_png_file"):
            edit_path = work_dir / result["editable_png_file"]
            editable_url = _upload_to_cloud(edit_path)
            # Store for remove-bg operation
            playground.session["editable_png_file"] = result["editable_png_file"]

    return {
        "detected_block_size": result.get("detected_block_size"),
        "svg_file": Path(result["svg_file"]).name if result.get("svg_file") else None,
        "rasterized_png": Path(result["rasterized_png_file"]).name if result.get("rasterized_png_file") else None,
        "editable_png": Path(result["editable_png_file"]).name if result.get("editable_png_file") else None,
        "svg_url": svg_url,
        "raster_url": raster_url,
        "editable_url": editable_url,
    }


@app.post("/api/remove-bg")
def remove_bg(req: RemoveBgRequest):
    """Remove background from a generated or converted image."""
    _ensure_ready()
    
    candidate = req.image_name or playground.session.get("editable_png_file") or playground.session.get("last_web_image")
    if not candidate:
        raise HTTPException(status_code=400, detail="No image specified.")

    storage = get_storage()
    
    with _temp_workdir() as work_dir:
        # Download image from Supabase
        input_path = work_dir / candidate
        image_data = storage.download_file(candidate, str(input_path))
        
        if not image_data:
            raise HTTPException(status_code=404, detail=f"Image not found in storage: {candidate}")

        result = playground.remove_background(str(input_path))

        if not result:
            raise HTTPException(status_code=500, detail="Background removal failed.")

        name = Path(result["local_image_path"]).name
        nobg_path = work_dir / name
        
        # Upload to Supabase
        image_url = _upload_to_cloud(nobg_path, name)
    
    return {
        "image_name": name,
        "image_url": image_url,
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    storage_ok = is_storage_enabled()
    return {
        "status": "ok" if storage_ok else "degraded",
        "init_error": INIT_ERROR,
        "storage": "supabase" if storage_ok else "not configured",
        "mode": "production"
    }
