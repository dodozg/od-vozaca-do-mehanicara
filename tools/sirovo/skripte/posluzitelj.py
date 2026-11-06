# Pomoćni modul: pokreće llama-server, čeka spremnost, šalje JSON zahtjeve (samo stdlib), mjeri vršnu memoriju.
import json, os, subprocess, time, urllib.request, urllib.error
import mjeri

class Posluzitelj:
    def __init__(self, model, log, port=8080, args=()):
        self.url = f"http://127.0.0.1:{port}"
        self.naredba = [os.path.abspath("llama/llama-server.exe"), "-m", model, "--port", str(port), "--host", "127.0.0.1", *map(str, args)]
        self.log = log
    def __enter__(self):
        self.f = open(self.log, "ab")
        self.f.write(("\n#CMD " + subprocess.list2cmdline(self.naredba) + f"\n#SLOBODNO_MB_PRIJE {mjeri.slobodno_mb()}\n").encode()); self.f.flush()
        self.t0 = time.time()
        self.p = subprocess.Popen(self.naredba, stdout=self.f, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        self.pr = mjeri.Pracenje(self.p)
        while True:
            if self.p.poll() is not None: raise RuntimeError(f"posluzitelj je stao, exit={self.p.returncode}")
            try:
                with urllib.request.urlopen(self.url + "/health", timeout=2) as r:
                    if r.status == 200: break
            except (urllib.error.URLError, ConnectionError, TimeoutError): pass
            time.sleep(0.2)
        self.ucitavanje_s = time.time() - self.t0
        return self
    def post(self, put, tijelo, vrijeme=900):
        z = urllib.request.Request(self.url + put, json.dumps(tijelo, ensure_ascii=False).encode("utf-8"), {"Content-Type": "application/json"})
        with urllib.request.urlopen(z, timeout=vrijeme) as r: return json.loads(r.read().decode("utf-8"))
    def get(self, put):
        with urllib.request.urlopen(self.url + put, timeout=60) as r: return json.loads(r.read().decode("utf-8"))
    def memorija_mb(self): return self.pr.peak[0]/2**20, self.pr.peak[1]/2**20
    def __exit__(self, *a):
        self.pr.stop = True
        self.f.write(f"\n#MJERI ucitavanje_s={self.ucitavanje_s:.1f} peakWS_MB={self.pr.peak[0]/2**20:.0f} peakPrivate_MB={self.pr.peak[1]/2**20:.0f}\n".encode())
        self.p.terminate(); self.p.wait(); self.f.close()
