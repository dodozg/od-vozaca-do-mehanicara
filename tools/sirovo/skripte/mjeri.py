# Pokreće naredbu, ispis sprema u datoteku i mjeri vrijeme i vršnu memoriju (samo Windows, samo stdlib).
# Pokretanje: python mjeri.py LOG.txt -- naredba argumenti...
# PeakWorkingSetSize = vršni RSS (uključuje mmap stranice težina),
# PeakPagefileUsage  = vršni privatni (commit) dio, bez mmap težina.
import ctypes, ctypes.wintypes as w, os, subprocess, sys, time, threading

class PMC(ctypes.Structure):
    _fields_ = [("cb", w.DWORD), ("PageFaultCount", w.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
class MS(ctypes.Structure):
    _fields_ = [("dwLength", w.DWORD), ("dwMemoryLoad", w.DWORD), ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
GPMI = ctypes.WinDLL("psapi").GetProcessMemoryInfo
GPMI.argtypes = [w.HANDLE, ctypes.POINTER(PMC), w.DWORD]
GPMI.restype = w.BOOL

def memorija(rucka):
    p = PMC(); p.cb = ctypes.sizeof(PMC)
    if GPMI(int(rucka), ctypes.byref(p), p.cb):
        return p.PeakWorkingSetSize, p.PeakPagefileUsage, p.WorkingSetSize, p.PagefileUsage
    return None
def slobodno_mb():
    m = MS(); m.dwLength = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys // 2**20

class Pracenje:
    """Prati vršnu memoriju pokrenutog procesa u pozadinskoj niti."""
    def __init__(self, proc):
        self.proc, self.peak, self.stop = proc, (0, 0), False
        self.nit = threading.Thread(target=self._r, daemon=True); self.nit.start()
    def _r(self):
        while not self.stop and self.proc.poll() is None:
            m = memorija(self.proc._handle)
            if m: self.peak = (max(self.peak[0], m[0]), max(self.peak[1], m[1]))
            time.sleep(0.2)

def pokreni(naredba, log, ulaz=None):
    naredba = [os.path.abspath(naredba[0])] + list(naredba[1:])
    with open(log, "ab") as f:
        f.write(("\n#CMD " + subprocess.list2cmdline(naredba) + "\n#SLOBODNO_MB_PRIJE " + str(slobodno_mb()) + "\n").encode())
        f.flush()
        t = time.time()
        p = subprocess.Popen(naredba, stdout=f, stderr=subprocess.STDOUT, stdin=subprocess.PIPE if ulaz is not None else subprocess.DEVNULL)
        pr = Pracenje(p)
        if ulaz is not None:
            p.stdin.write(ulaz); p.stdin.close()
        p.wait(); pr.stop = True
        tr = time.time() - t
        red = f"\n#MJERI exit={p.returncode} wall_s={tr:.1f} peakWS_MB={pr.peak[0]/2**20:.0f} peakPrivate_MB={pr.peak[1]/2**20:.0f}\n"
        f.write(red.encode())
    return p.returncode, tr, pr.peak[0]/2**20, pr.peak[1]/2**20

if __name__ == "__main__":
    i = sys.argv.index("--")
    r = pokreni(sys.argv[i+1:], sys.argv[1])
    print(f"exit={r[0]} wall_s={r[1]:.1f} peakWS_MB={r[2]:.0f} peakPrivate_MB={r[3]:.0f}")
