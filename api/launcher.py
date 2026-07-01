from __future__ import annotations

import os
import threading

_STARTED = False


def api_baslat(log_func=None) -> bool:
    """Mobil API'yi arka planda başlatır. FastAPI/uvicorn yoksa programı bozmaz."""
    global _STARTED
    if _STARTED:
        return True

    # İstenirse kapatılabilir: set DAL_ERP_API=0
    if os.environ.get("DAL_ERP_API", "1").strip() in ("0", "false", "False", "hayir", "HAYIR"):
        return False

    host = os.environ.get("DAL_ERP_API_HOST", "0.0.0.0")
    port = int(os.environ.get("DAL_ERP_API_PORT", "8000"))

    try:
        import uvicorn

        from api.server import app, local_ip
    except Exception as exc:
        if log_func:
            log_func(f"Mobil API başlatılamadı. fastapi/uvicorn kurulu olmayabilir: {exc}", "API")
        return False

    def _run():
        config = uvicorn.Config(app, host=host, port=port, log_level="warning", access_log=False)
        server = uvicorn.Server(config)
        server.run()

    thread = threading.Thread(target=_run, daemon=True, name="DAL-ERP-Mobile-API")
    thread.start()
    _STARTED = True
    if log_func:
        log_func(f"Mobil API aktif: http://{local_ip()}:{port}", "API")
    return True
