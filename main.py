"""Compatibility entry point.

New deployments should run ``polyocr-service`` or
``uvicorn polyocr.main:create_app --factory``.

Kept so that existing ``python main.py`` invocations and any
``uvicorn main:app`` process manager configuration keep working after the move to
the ``src/polyocr`` package layout.
"""

import os

from polyocr.main import create_app

app = create_app()


def _dev_server() -> None:
    """Run a development server on the loopback interface by default.

    This used to hard-code ``0.0.0.0``, which silently published the service on every
    network interface -- including on a laptop or a shared network, where nothing else
    in the project asks for that. ``polyocr-service`` defaults to ``127.0.0.1``, so
    binding every interface here contradicted the packaged entry point.

    The container still binds ``0.0.0.0`` explicitly in the Dockerfile CMD, which is
    correct there: publishing a port is what makes the container reachable, and the
    exposure is a deliberate, visible choice rather than a hidden default.
    """
    import uvicorn

    host = os.getenv("POLYOCR_HOST", "127.0.0.1")
    port = int(os.getenv("POLYOCR_PORT", "8000"))
    uvicorn.run("polyocr.main:create_app", factory=True, host=host, port=port)


if __name__ == "__main__":
    _dev_server()
