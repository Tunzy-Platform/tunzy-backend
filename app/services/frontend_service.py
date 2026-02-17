from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter

from app.core import config

router = APIRouter()


@router.get("/{path:path}", include_in_schema=False)
def dashboard(path: str):
    print(path)
    if path.startswith("api/"):
        return {"detail": "Not Found"}

    frontend_path = Path(config.settings.frontend_path or config.BASE_DIR / "static")
    file_path = frontend_path / path
    if path and file_path.exists():
        return FileResponse(file_path)

    return FileResponse(frontend_path / "index.html")
