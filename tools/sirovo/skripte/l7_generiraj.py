# L7: generator SINTETIČKIH servisnih zapisnika za fiktivni servis Kvaka d.o.o.
# Podaci su izrađeni iz predložaka i rječnika, nisu stvarni zapisnici.
# Isto sjeme (42) uvijek daje iste datoteke.
# Pokretanje: python l7_generiraj.py IZLAZNA_MAPA
import json, random, sys, os

UREDAJI = {  # kanonska vrijednost: (nominativ, akuzativ)
 "perilica rublja": [("perilica rublja","perilicu rublja"),("perilica","perilicu"),("per. rublja","per. rublja"),("veš mašina","veš mašinu"),("perilica rub.","perilicu rub.")],
 "perilica posuđa": [("perilica posuđa","perilicu posuđa"),("perilica suđa","perilicu suđa"),("per. posuđa","per. posuđa"),("mašina za suđe","mašinu za suđe")],
 "sušilica rublja": [("sušilica rublja","sušilicu rublja"),("sušilica","sušilicu"),("suš. rublja","suš. rublja"),("sušilica veša","sušilicu veša")],
 "hladnjak": [("hladnjak","hladnjak"),("frižider","frižider"),("kombinirani hladnjak","kombinirani hladnjak"),("hl.","hl.")],
 "zamrzivač": [("zamrzivač","zamrzivač"),("škrinja","škrinju"),("ledenica","ledenicu"),("zamrz.","zamrz.")],
 "pećnica": [("pećnica","pećnicu"),("ugradbena pećnica","ugradbenu pećnicu"),("rerna","rernu"),("pećn.","pećn.")],
 "mikrovalna pećnica": [("mikrovalna pećnica","mikrovalnu pećnicu"),("mikrovalna","mikrovalnu"),("mikrovalka","mikrovalku")],
 "bojler": [("bojler","bojler"),("el. bojler","el. bojler"),("bojler 80l","bojler 80l"),("električni bojler","električni bojler")],
 "napa": [("napa","napu"),("kuhinjska napa","kuhinjsku napu"),("napa iznad štednjaka","napu iznad štednjaka")],
}
SIMPTOMI = {
 "ne izbacuje vodu": ["ne izbacuje vodu","voda stoji unutra","ne ispumpava","ne odvodi vodu","neizbacuje vodu","stane i ostane puna vode"],
 "curi voda": ["curi voda","curi po podu","pušta vodu ispod","lokva ispod uređaja","kaplje voda","propušta vodu"],
 "ne grije": ["ne grije","ostaje hladno","ne zagrijava","negrije","sve je hladno nakon programa"],
 "ne hladi": ["ne hladi","slabo hladi","unutra toplo","unutra oko 15 st.","nehladi"],
 "ne pali se": ["ne pali se","mrtav uređaj, nema reakcije","ne reagira na tipke","ekran taman","nece se upalit"],
 "bučan rad": ["jako bučan","lupa u radu","strašna buka","zuji i vibrira","škripi kad radi"],
 "ne centrifugira": ["ne centrifugira","rublje ostaje mokro, ne vrti","ne cijedi","nece centrifugu"],
 "ne puni vodu": ["ne puni vodu","ne uzima vodu","javlja grešku za dovod","ne vuče vodu"],
 "ne suši": ["ne suši","rublje mokro nakon ciklusa","suši satima i ne osuši","nesuši"],
}
DIJELOVI = {
 "pumpa": [("pumpa","pumpu"),("odvodna pumpa","odvodnu pumpu"),("pumpa za izbacivanje","pumpu za izbacivanje")],
 "grijač": [("grijač","grijač"),("grijaći element","grijaći element"),("gr.","gr.")],
 "termostat": [("termostat","termostat"),("term.","term.")],
 "remen": [("remen","remen"),("pogonski remen","pogonski remen")],
 "brtva": [("brtva","brtvu"),("gumena brtva","gumenu brtvu"),("guma na vratima","gumu na vratima"),("manžeta","manžetu")],
 "kompresor": [("kompresor","kompresor"),("kompr.","kompr.")],
 "elektronika": [("elektronika","elektroniku"),("upravljačka ploča","upravljačku ploču"),("pločica","pločicu"),("modul","modul")],
 "motor": [("motor","motor"),("motor bubnja","motor bubnja")],
 "ventil": [("ventil","ventil"),("ulazni ventil","ulazni ventil"),("elektroventil","elektroventil")],
 "ventilator": [("ventilator","ventilator"),("vent.","vent.")],
 "magnetron": [("magnetron","magnetron")],
 "senzor": [("senzor","senzor"),("NTC senzor","NTC senzor"),("sonda","sondu")],
}
KOMBINACIJE = {
 "perilica rublja": [("ne izbacuje vodu","pumpa"),("curi voda","brtva"),("ne grije","grijač"),("ne centrifugira","remen"),("ne puni vodu","ventil"),("ne pali se","elektronika"),("bučan rad","motor")],
 "perilica posuđa": [("ne izbacuje vodu","pumpa"),("curi voda","brtva"),("ne grije","grijač"),("ne puni vodu","ventil"),("ne pali se","elektronika")],
 "sušilica rublja": [("ne suši","grijač"),("ne suši","senzor"),("bučan rad","remen"),("ne pali se","elektronika"),("bučan rad","ventilator")],
 "hladnjak": [("ne hladi","kompresor"),("ne hladi","termostat"),("curi voda","brtva"),("bučan rad","ventilator"),("ne pali se","elektronika")],
 "zamrzivač": [("ne hladi","kompresor"),("ne hladi","termostat"),("curi voda","brtva"),("bučan rad","kompresor")],
 "pećnica": [("ne grije","grijač"),("ne grije","termostat"),("ne pali se","elektronika"),("bučan rad","ventilator")],
 "mikrovalna pećnica": [("ne grije","magnetron"),("ne pali se","elektronika"),("bučan rad","ventilator")],
 "bojler": [("ne grije","grijač"),("ne grije","termostat"),("curi voda","brtva")],
 "napa": [("bučan rad","motor"),("ne pali se","elektronika"),("bučan rad","ventilator")],
}
HITNOST = {
 "visoka": ["HITNO","hitno, stranka čeka","treba odmah","danas obavezno","starija osoba, što prije","stranka zove treći put, hitno"],
 "srednja": ["može do petka","termin ovaj tjedan","što prije ali nije kritično","dogovoriti za par dana","srednje hitno"],
 "niska": ["nije hitno","može sljedeći mjesec","kad stignete","stranka nije u žurbi","nije frka"],
}
NALAZ = ["dio: {n}","uzrok {n}","treba zamijeniti {a}","naručiti {a}","sumnja na {a}","mijenjam {a}","{n} za zamjenu","izmjereno, {n} u kvaru"]
NALAZ_NEPOZNATO = ["uzrok još nije utvrđen","treba dodatna dijagnostika","nije jasno koji dio","dio nepoznat dok se ne rastavi"]
IMENA = ["Horvat","Kovačević","Babić","Marić","Jurić","Novak","Knežević","Vuković","Marković","Petrović","Matić","Tomić"]
ULICE = ["Ilica","Vukovarska","Savska","Dubrava","Zvonimirova","Trg Slobode","Radnička","Maksimirska","Gajeva","Selska"]
PREDLOSCI = [
 "{dat} {ulica} {br}. {un} {sim}. {naz}. {hit}.",
 "Stranka {ime} zove, {un} {sim}. Pregled: {naz}. {hit}",
 "Izlazak na teren, {ulica} {br}: pregledano {ua}, {sim}. {naz}. SN {sn}. {hit}",
 "{un} / {sim} / {naz} / {hit}",
 "Nalog {nal}: {un}, stranka kaže da {sim}. {naz}. {hit}. Radni sat {sat}h.",
 "{ime}, {ulica} {br}. Prijava: {sim} ({un}). Na licu mjesta {naz}. Napomena: {hit}.",
 "tel. prijava {dat}: {un} {sim}, {naz}, {hit}",
 "Servis {ua} kod {ime} - {sim}. {naz}. {hit}. Dolazak {sat}h.",
 "KVAR: {sim}. UREDJAJ: {un}. NALAZ: {naz}. PRIORITET: {hit}.",
 "{hit}! {un} {sim} ({ulica} {br}), {naz}.",
 "Kolega javlja s terena, {un} {sim}, {naz}. {hit}. SN {sn}",
 "{dat}. {un}, model nepoznat. {sim}. {naz}. Stranka {ime}. {hit}.",
]
SUSTAV = ("Ti si pomoćnik servisa Kvaka d.o.o. Iz zapisnika tehničara izvuci podatke i vrati samo JSON s poljima uredaj, kvar, dio, hitnost. "
 "Dopuštene vrijednosti. uredaj: " + ", ".join(UREDAJI) + ". kvar: " + ", ".join(SIMPTOMI) + ". dio: " + ", ".join(DIJELOVI) + ", nepoznato. hitnost: niska, srednja, visoka.")

BEZ_DIJAKRITIKA = str.maketrans("čćžšđČĆŽŠĐ","cczsdCCZSD")
def pokvari(t, r):
    # sum kakav pišu ljudi na terenu: bez dijakritika, mala slova, zamjena slova, bez interpunkcije
    if r.random() < .3: t = t.translate(BEZ_DIJAKRITIKA)
    if r.random() < .3: t = t.lower()
    if r.random() < .25:
        rijeci = t.split(" ")
        for _ in range(r.randint(1,2)):
            i = r.randrange(len(rijeci)); w = rijeci[i]
            if len(w) > 4 and w.isalpha():
                j = r.randrange(1,len(w)-2); rijeci[i] = w[:j]+w[j+1]+w[j]+w[j+2:]
        t = " ".join(rijeci)
    if r.random() < .15: t = t.replace(". ", " ").replace(", ", " ")
    return t
def zapisnik(r):
    u = r.choice(list(UREDAJI)); kv, di = r.choice(KOMBINACIJE[u]); hi = r.choice(list(HITNOST))
    if r.random() < .12: di = "nepoznato"
    un, ua = r.choice(UREDAJI[u]); sim = r.choice(SIMPTOMI[kv])
    if di == "nepoznato": naz = r.choice(NALAZ_NEPOZNATO)
    else:
        n, a = r.choice(DIJELOVI[di]); naz = r.choice(NALAZ).format(n=n, a=a)
    t = r.choice(PREDLOSCI).format(dat=f"{r.randint(1,28)}.{r.randint(1,12)}.", ulica=r.choice(ULICE), br=r.randint(1,120), un=un, ua=ua, sim=sim, naz=naz,
        hit=r.choice(HITNOST[hi]), ime=r.choice(IMENA), sn=f"{r.randint(10,99)}{r.choice('ABCKMX')}{r.randint(1000,9999)}", nal=r.randint(2000,9000), sat=r.choice(["0,5","1","1,5","2"]))
    return pokvari(t, r), {"uredaj":u, "kvar":kv, "dio":di, "hitnost":hi}
def poruke(t, o):
    return {"messages":[{"role":"system","content":SUSTAV},{"role":"user","content":t},{"role":"assistant","content":json.dumps(o, ensure_ascii=False)}]}
if __name__ == "__main__":
    izlaz = sys.argv[1]; r = random.Random(42)
    vidjeno, svi = set(), []
    while len(svi) < 300:
        t, o = zapisnik(r)
        if t not in vidjeno: vidjeno.add(t); svi.append((t, o))
    for ime, dio in (("train.jsonl", svi[:240]), ("val.jsonl", svi[240:])):
        with open(os.path.join(izlaz, ime), "w", encoding="utf-8", newline="\n") as f:
            for t, o in dio: f.write(json.dumps(poruke(t, o), ensure_ascii=False)+"\n")
    with open(os.path.join(izlaz, "sustav.txt"), "w", encoding="utf-8", newline="\n") as f: f.write(SUSTAV)
    with open(os.path.join(izlaz, "shema.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"type":"object","properties":{"uredaj":{"enum":list(UREDAJI)},"kvar":{"enum":list(SIMPTOMI)},"dio":{"enum":list(DIJELOVI)+["nepoznato"]},"hitnost":{"enum":["niska","srednja","visoka"]}},"required":["uredaj","kvar","dio","hitnost"],"additionalProperties":False}, f, ensure_ascii=False, indent=1)
    print("train", 240, "val", 60)
    for t, o in svi[:6]: print(t, "=>", json.dumps(o, ensure_ascii=False))
