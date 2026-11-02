"""SVM web application backend (FastAPI). Run from the project root:  python -m uvicorn svm_variant.webapp.backend.main:app --port 8000
Real SVM inference only: there is no generator and no other classifier behind this API."""
import io
import time

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image, UnidentifiedImageError

from . import config, results
from .ml import svm

Image.MAX_IMAGE_PIXELS = config.MAX_IMAGE_SIDE * config.MAX_IMAGE_SIDE
app = FastAPI(title="Brain Tumor MRI SVM", version="1.0.0", description="Academic research prototype: HOG + SVM brain tumour MRI classifier. Not a medical device.")
app.add_middleware(CORSMiddleware, allow_origins=config.ALLOWED_ORIGINS, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
START = time.time()
DISCLAIMER = "Academic research prototype. Outputs are not a medical diagnosis and must not be used for clinical decisions."
CAVEATS = [
    "This is the project's own HOG + SVM model. Its measured performance is on the project's 492-image test partition (see the metrics page); it is not an estimate for new patients, scanners or sites.",
    "The values shown are SVM decision scores (one-vs-rest), not calibrated probabilities.",
    "No out-of-distribution check is performed: any image will receive one of the four labels.",
    "Patient-level independence of the training and test data is not proven.",
]


def err(status, code, message, **extra):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, **extra}})


@app.exception_handler(RequestValidationError)
async def _validation(_: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    return err(422, "invalid_request", f"{'.'.join(str(x) for x in first.get('loc', [])[1:])}: {first.get('msg', 'invalid request')}")


@app.get("/api/health")
def health():
    return {"status": "ok", "uptime_seconds": round(time.time() - START, 1), "disclaimer": DISCLAIMER}


@app.get("/api/models/status")
def models_status():
    ok = svm.ensure()
    out = {"disclaimer": DISCLAIMER, "classifier": {"name": svm.name, "available": ok, "error": svm.error, "license": "scikit-learn (BSD-3-Clause)", "classes": config.CLASSES}}
    if ok:
        c = svm.cfg
        out["classifier"].update({"kernel": c["kernel"], "svc_params": c["svc_params"], "hog_variant": c["hog_variant"], "n_features": c["n_features"], "image_size": c["image_size"],
                                  "n_support_vectors": c["n_support_vectors"], "model_sha256": svm.model_sha256, "matches_evaluated_model": True})
    out["generator"] = {"available": False, "reason": "This application has no image generator: it is the SVM classification variant of the project."}
    return out


@app.post("/api/classify")
async def classify(file: UploadFile = File(...)):
    if not svm.ensure():
        return err(503, "classifier_unavailable", "The SVM classifier could not be loaded.", detail=svm.error)
    data = await file.read(config.MAX_UPLOAD_BYTES + 1)
    if len(data) > config.MAX_UPLOAD_BYTES:
        return err(413, "file_too_large", f"Image is larger than {config.MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    if not data:
        return err(400, "empty_file", "The uploaded file is empty.")
    try:
        probe = Image.open(io.BytesIO(data))
        fmt = probe.format
        if fmt not in ("PNG", "JPEG"):
            return err(415, "unsupported_type", f"Unsupported image format {fmt}. Upload a PNG or JPEG.")
        w, h = probe.size
        if min(w, h) < config.MIN_IMAGE_SIDE or max(w, h) > config.MAX_IMAGE_SIDE:
            return err(422, "bad_dimensions", f"Image is {w}x{h}; sides must be between {config.MIN_IMAGE_SIDE} and {config.MAX_IMAGE_SIDE} pixels.")
        img = Image.open(io.BytesIO(data)); img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError):
        return err(415, "not_an_image", "The file could not be read as a PNG or JPEG image.")
    t0 = time.time()
    idx, scores = svm.predict(img)
    cls = config.CLASSES[idx]
    order = sorted(range(4), key=lambda i: -scores[i])
    return {"predicted_class": cls, "predicted_label": config.CLASS_LABELS[cls], "decision_scores": [{"class": c, "label": config.CLASS_LABELS[c], "score": scores[i]} for i, c in enumerate(config.CLASSES)],
            "margin_top1_minus_top2": scores[order[0]] - scores[order[1]], "model": svm.name, "kernel": svm.cfg["kernel"], "input_size": [w, h],
            "inference_ms": round((time.time() - t0) * 1000, 1), "disclaimer": DISCLAIMER, "caveats": CAVEATS}


@app.get("/api/metrics")
def get_metrics():
    try:
        return results.metrics()
    except FileNotFoundError as e:
        return err(503, "metrics_unavailable", f"Saved result file missing: {str(e.filename).replace(str(config.PROJECT_ROOT), '.')}")


@app.get("/api/experiment")
def get_experiment():
    try:
        return results.experiment()
    except FileNotFoundError as e:
        return err(503, "experiment_unavailable", f"Saved result file missing: {str(e.filename).replace(str(config.PROJECT_ROOT), '.')}")


@app.get("/api/gallery")
def get_gallery():
    return {"items": results.gallery(), "note": "Figures generated from the saved SVM outputs; 'result' = computed from the saved test predictions, 'data' = dataset images, 'audit' = split checks."}


@app.get("/api/gallery/image/{item_id}")
def gallery_image(item_id: str):
    p = results.gallery_path(item_id)
    if p is None:
        return err(404, "not_found", "Unknown gallery image.")
    return FileResponse(p, media_type="image/png")
