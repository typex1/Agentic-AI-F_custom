"""
station_api_server.py — a tiny stand-in "Rate-My-Station" REST API (read-only)

This is deliberately dumb: an in-memory dataset served as JSON over HTTP using
only the Python standard library. It stands in for the real Rate-My-Station API
so the Task 2 solution is self-contained. Your agent's tools should treat it as
a black box and talk to it only over HTTP.

Endpoints (all GET, all read-only):
    GET /stations                 -> [{id, name, city}, ...]
    GET /stations/search?q=<str>  -> [{id, name, city}, ...]  (name/city match)
    GET /stations/<id>            -> {id, name, city, lines, review_count, ratings}
    GET /stations/<id>/ratings    -> {station_id, cleanliness, safety,
                                       accessibility, punctuality}

Start it in-process with `start_server()`, which binds 127.0.0.1 on an ephemeral
port and runs in a daemon thread, returning the base URL.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# --- The "database": a handful of stations with rating breakdowns (0-5) ---
_STATIONS: dict[int, dict] = {
    1: {
        "id": 1, "name": "Köln Hauptbahnhof", "city": "Köln",
        "lines": ["ICE", "IC", "RE", "S-Bahn"], "review_count": 1240,
        "ratings": {"cleanliness": 3.2, "safety": 3.8, "accessibility": 4.5, "punctuality": 2.9},
    },
    2: {
        "id": 2, "name": "Köln Messe/Deutz", "city": "Köln",
        "lines": ["ICE", "RE", "S-Bahn"], "review_count": 610,
        "ratings": {"cleanliness": 4.1, "safety": 4.0, "accessibility": 4.2, "punctuality": 3.5},
    },
    3: {
        "id": 3, "name": "Düsseldorf Hauptbahnhof", "city": "Düsseldorf",
        "lines": ["ICE", "IC", "RE", "S-Bahn"], "review_count": 980,
        "ratings": {"cleanliness": 3.6, "safety": 3.4, "accessibility": 4.3, "punctuality": 3.1},
    },
    4: {
        "id": 4, "name": "Berlin Hauptbahnhof", "city": "Berlin",
        "lines": ["ICE", "IC", "RE", "S-Bahn", "U-Bahn"], "review_count": 2100,
        "ratings": {"cleanliness": 4.4, "safety": 4.1, "accessibility": 4.8, "punctuality": 3.3},
    },
    5: {
        "id": 5, "name": "München Hauptbahnhof", "city": "München",
        "lines": ["ICE", "IC", "RE", "S-Bahn", "U-Bahn"], "review_count": 1730,
        "ratings": {"cleanliness": 4.0, "safety": 3.9, "accessibility": 4.6, "punctuality": 3.0},
    },
}


def _summary(s: dict) -> dict:
    return {"id": s["id"], "name": s["name"], "city": s["city"]}


class _Handler(BaseHTTPRequestHandler):
    # Silence the default per-request stderr logging.
    def log_message(self, *args) -> None:  # noqa: D401
        return

    def _send(self, status: int, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]

        # GET /stations  and  GET /stations/search?q=...
        if parts == ["stations"]:
            return self._send(200, [_summary(s) for s in _STATIONS.values()])

        if parts == ["stations", "search"]:
            q = (parse_qs(parsed.query).get("q", [""])[0] or "").lower().strip()
            hits = [
                _summary(s) for s in _STATIONS.values()
                if q in s["name"].lower() or q in s["city"].lower()
            ]
            return self._send(200, hits)

        # GET /stations/<id>  and  GET /stations/<id>/ratings
        if len(parts) >= 2 and parts[0] == "stations" and parts[1].isdigit():
            station = _STATIONS.get(int(parts[1]))
            if station is None:
                return self._send(404, {"error": f"station {parts[1]} not found"})
            if len(parts) == 2:
                return self._send(200, station)
            if len(parts) == 3 and parts[2] == "ratings":
                return self._send(200, {"station_id": station["id"], **station["ratings"]})

        return self._send(404, {"error": "unknown endpoint"})


def start_server(host: str = "127.0.0.1", port: int = 0) -> tuple[str, ThreadingHTTPServer]:
    """Start the API in a daemon thread. Returns (base_url, server).

    Port 0 asks the OS for a free ephemeral port, so this never clashes.
    """
    httpd = ThreadingHTTPServer((host, port), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    actual_port = httpd.server_address[1]
    return f"http://{host}:{actual_port}", httpd


if __name__ == "__main__":
    # Allow running the API on its own for manual poking (fixed port 8077).
    base_url, httpd = start_server(port=8077)
    print(f"Rate-My-Station API serving at {base_url}  (Ctrl-C to stop)")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        httpd.shutdown()
