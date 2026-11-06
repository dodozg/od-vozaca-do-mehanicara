# L6: preuzima čisti tekst članaka s Wikipedije (CC BY-SA) za mjerenje perpleksnosti i kalibraciju imatrixa.
# Mjereni izvadci priloženi su u podaci/tekst; ova skripta preuzima trenutačne članke, a oni se mijenjaju.
# Pokretanje: python l6_tekstovi.py IZLAZNA_MAPA
import json, os, sys, time, urllib.parse, urllib.request, re
izlaz = sys.argv[1]; os.makedirs(izlaz, exist_ok=True)
SETOVI = {
 "ppl_hr": ("hr", ["Nikola Tesla", "Voda", "Rimsko Carstvo", "Računalo", "Sunčev sustav", "Hrvatska"], 30000),
 "ppl_en": ("en", ["Nikola Tesla", "Water", "Roman Empire", "Computer", "Solar System", "Car"], 45000),
 "kal_hr": ("hr", ["Dubrovnik", "Jadransko more", "Električna energija"], 9000),
 "kal_en": ("en", ["Dubrovnik", "Adriatic Sea", "Electricity"], 9000),
}
for ime, (lang, naslovi, granica) in SETOVI.items():
    dijelovi = []
    for n in naslovi:
        time.sleep(8)  # Wikipedia vraća 429 ako se pita prebrzo
        q = urllib.parse.urlencode({"action":"query","prop":"extracts","explaintext":1,"format":"json","redirects":1,"titles":n})
        z = urllib.request.Request(f"https://{lang}.wikipedia.org/w/api.php?{q}", headers={"User-Agent":"llm-prirucnik-lab/1.0 (edukacijska mjerenja)"})
        d = json.load(urllib.request.urlopen(z, timeout=60))
        for p in d["query"]["pages"].values():
            t = p.get("extract", "")
            t = re.split(r"\n== *(Literatura|Izvori|Vanjske poveznice|Bilješke|References|External links|Notes|See also|Vidi još|Further reading|Sources) *==", t)[0]
            t = re.sub(r"\n{2,}", "\n", t)
            print(ime, n, len(t)); dijelovi.append(t[:granica//max(1,len(naslovi)-2)])
    s = "\n".join(dijelovi)[:granica]
    with open(os.path.join(izlaz, ime + ".txt"), "w", encoding="utf-8", newline="\n") as f: f.write(s)
    print("==", ime, len(s), "znakova")
