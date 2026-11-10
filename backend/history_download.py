"""Background refresh for the historical CSV scanner."""

from threading import Lock

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

router = APIRouter(prefix="/api/scanner/download")
lock = Lock()
state = {"status": "idle", "total": 0, "downloaded": 0, "failed": [], "error": None}


def refresh():
    try:
        from download_stocks import DATA, download_stock, stock_universe

        symbols = stock_universe()
        DATA.mkdir(exist_ok=True)
        with lock:
            state["total"] = len(symbols)
        for symbol in symbols:
            try:
                download_stock(symbol)
            except Exception:
                with lock:
                    state["failed"].append(symbol)
            else:
                with lock:
                    state["downloaded"] += 1
        with lock:
            state["status"] = "complete"
    except Exception:
        with lock:
            state.update(status="error", error="Could not start the download. Check network access and install backend/requirements-download.txt.")


@router.get("")
def progress():
    with lock:
        return {**state, "failed": list(state["failed"])}


@router.post("", status_code=202)
def start(request: Request, tasks: BackgroundTasks):
    if request.headers.get("origin") not in {"http://127.0.0.1:3000", "http://localhost:3000"}:
        raise HTTPException(403, "Start the download from the local dashboard")
    with lock:
        if state["status"] != "running":
            state.update(status="running", total=0, downloaded=0, failed=[], error=None)
            tasks.add_task(refresh)
    return progress()
