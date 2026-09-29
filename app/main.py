from pathlib import Path
import tempfile

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.demo_scanner import scan_demo


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


app = FastAPI(
    title="DepGuard",
    description="Supply Chain Security Analyzer",
    version="1.0.0-demo"
)


app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "application": "DepGuard",
        "mode": "demo"
    }


@app.get("/")
def home():
    from fastapi.responses import FileResponse

    return FileResponse(
        STATIC_DIR / "index.html"
    )


@app.post("/api/scan")
async def scan_dependency_file(
    file: UploadFile = File(...)
):
    """
    Jury-demo scan endpoint.

    The uploaded file is validated and then the deterministic
    three-package demo analysis is returned.

    No uploaded package is installed or executed.
    """

    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={
                "error": "No filename provided."
            }
        )

    allowed_extensions = {
        ".json",
        ".txt",
        ".xml"
    }

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in allowed_extensions:
        return JSONResponse(
            status_code=400,
            content={
                "error": (
                    "Unsupported file type. "
                    "Use .json, .txt or .xml."
                )
            }
        )

    try:

        content = await file.read()

        if not content:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Uploaded file is empty."
                }
            )

        with tempfile.NamedTemporaryFile(
            delete=True,
            suffix=extension
        ) as temporary_file:

            temporary_file.write(content)
            temporary_file.flush()

            report = scan_demo()

        report["uploaded_file"] = file.filename

        return report

    except Exception as error:

        return JSONResponse(
            status_code=500,
            content={
                "error": "Demo scan failed.",
                "detail": str(error)
            }
        )
