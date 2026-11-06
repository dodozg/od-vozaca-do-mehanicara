#!/usr/bin/env python3
"""Otvara build/knjiga-ispis.html u headless Chromeu, ceka da Paged.js zavrsi prijelom, pa ispisuje PDF.

Treba paket websocket-client. Pokretanje:  python tools/ispisi_pdf.py izlaz.pdf
"""
import base64
import functools
import http.server
import json
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

import websocket

KORIJEN = Path(__file__).resolve().parent.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


class Tihi(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main(izlaz: str):
    handler = functools.partial(Tihi, directory=str(KORIJEN / "build"))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port_web = srv.server_address[1]

    profil = tempfile.mkdtemp(prefix="knjiga-chrome-")
    port = 9333
    ch = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", f"--remote-debugging-port={port}",
                           "--remote-allow-origins=*", f"--user-data-dir={profil}", "about:blank"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                ciljevi = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
                stranica = next(c for c in ciljevi if c["type"] == "page")
                break
            except Exception:
                time.sleep(0.5)
        ws = websocket.create_connection(stranica["webSocketDebuggerUrl"], timeout=600, max_size=None)
        n = [0]

        def poziv(metoda, **par):
            n[0] += 1
            ws.send(json.dumps({"id": n[0], "method": metoda, "params": par}))
            while True:
                o = json.loads(ws.recv())
                if o.get("id") == n[0]:
                    if "error" in o:
                        raise RuntimeError(o["error"])
                    return o["result"]

        poziv("Page.enable")
        poziv("Runtime.enable")
        poziv("Page.navigate", url=f"http://127.0.0.1:{port_web}/knjiga-ispis.html")

        pocetak = time.time()
        zadnji, isti = -1, 0
        while time.time() - pocetak < 540:
            time.sleep(2)
            r = poziv("Runtime.evaluate", expression="document.querySelectorAll('.pagedjs_page').length", returnByValue=True)
            broj = r["result"].get("value", 0)
            isti = isti + 1 if broj == zadnji and broj > 0 else 0
            zadnji = broj
            if isti >= 4:
                break
        print("stranica:", zadnji, "za", round(time.time() - pocetak), "s")
        # Fontovi moraju biti gotovi prije ispisa.
        poziv("Runtime.evaluate", expression="document.fonts.ready.then(()=>true)", awaitPromise=True)
        rez = poziv("Page.printToPDF", printBackground=True, preferCSSPageSize=True, generateTaggedPDF=False)
        Path(izlaz).write_bytes(base64.b64decode(rez["data"]))
        print("PDF:", izlaz, Path(izlaz).stat().st_size // 1024, "KB")
        ws.close()
    finally:
        ch.terminate()
        srv.shutdown()


if __name__ == "__main__":
    main(sys.argv[1])
