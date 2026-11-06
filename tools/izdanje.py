"""Čita trenutačno izdanje iz IZMJENE.md, jedinog mjesta na kojem se broj izdanja upisuje."""
import re
from dataclasses import dataclass
from pathlib import Path

IZMJENE = Path(__file__).resolve().parent.parent / "IZMJENE.md"
NASLOV = re.compile(r"^## (\d{4}\.\d{1,2}(?:\.\d+)?)[ \t]*$", re.M)
STANJE = re.compile(r"Stanje alata i mjerenja: (\d{1,2}\. \d{1,2}\. \d{4}\.)")


@dataclass
class Izdanje:
    oznaka: str    # 2026.11 ili 2026.11.1
    stanje: str    # 4. 11. 2026.
    biljeske: str  # tekst odjeljka iz IZMJENE.md

    @property
    def tag(self) -> str:
        return f"v{self.oznaka}"


def kao_brojevi(oznaka: str) -> tuple:
    """Oznaka za usporedbu: 2026.9 je starije od 2026.11, a 2026.11 od 2026.11.1."""
    return tuple(int(d) for d in oznaka.split("."))


def procitaj(tekst: str | None = None) -> Izdanje:
    tekst = IZMJENE.read_text(encoding="utf-8") if tekst is None else tekst
    naslovi = list(NASLOV.finditer(tekst))
    if not naslovi:
        raise SystemExit("IZMJENE.md: nema naslova izdanja u obliku '## 2026.11'.")
    prvi = naslovi[0]
    kraj = naslovi[1].start() if len(naslovi) > 1 else len(tekst)
    # Ispravak unutar izdanja ne mijenja mjerenja, pa nasljeđuje datum prethodnog zapisa.
    stanje = STANJE.search(tekst, prvi.end())
    if not stanje:
        raise SystemExit("IZMJENE.md: nedostaje redak 'Stanje alata i mjerenja: D. M. GGGG.'.")
    return Izdanje(prvi.group(1), stanje.group(1), tekst[prvi.end():kraj].strip())
