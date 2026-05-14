# Lead Crawler: navodila za Barbaro

## Kaj je to

Orodje, ki samodejno najde podjetja (zobozdravnike, fizioterapevte, mizarje, mehanike ...) in preveri stanje njihovih spletnih strani. Za vsako podjetje pove: ali ima stran, ali je stran varna, hitra, mobilno prilagojena, ali ima socialna omrežja.

Rezultat je tabela z ocenami: HOT, WARM ali LOW.

## Kako poženem

V Terminalu (črno okno):

```
cd ~/Projects/grafeio/lead-crawler
python3 main.py all
```

To traja nekaj minut. Ko je končano, odpri datoteko:

```
open output/leads_scored.csv
```

To odpre tabelo v Numbers ali Excelu.

## Kako berem rezultate

### Stolpci, ki te zanimajo

| Stolpec | Kaj pomeni |
|---|---|
| **classification** | HOT, WARM ali LOW |
| **score** | Višji = boljši lead za naju |
| **name** | Ime podjetja |
| **category** | Panoga (zobozdravnik, mizar ...) |
| **phone** | Telefon |
| **website** | Spletna stran (prazno = nima!) |
| **google_rating** | Ocena na Google Maps |
| **reasons** | Zakaj je lead zanimiv (v angleščini) |

### Kaj pomenijo ocene

**HOT (60+):** Takoj kontaktiraj. Podjetje nima spletne strani ali pa je stran v zelo slabem stanju (brez varnostnega certifikata, ni mobilno prilagojena, zastarela).

**WARM (30 do 59):** Vredno pozornosti. Stran obstaja, ampak ima opazne pomanjkljivosti.

**LOW (pod 30):** Stran je solidna. Za zdaj ni nujno.

## Kako preverim eno podjetje

Če te zanima konkretno podjetje:

```
python3 main.py quick https://primer-firme.si
```

To takoj izpiše diagnostiko. Primer:

```
Stran:          https://luxdental.si/
Dosegljiva:     DA
SSL:            NE        ← brez ključavnice v brskalniku!
Mobilna:        DA
Copyright:      2019      ← 7 let stara stran
Score:          50
Klasifikacija:  WARM
Razlogi:        ni SSL certifikata; copyright 2019; 4 slik brez alt besedila
```

## Kaj rečem stranki

### Če NIMA spletne strani

„Opazili smo, da vas potencialne stranke ne morejo najti na spletu. Mlajša generacija išče storitve izključno prek telefona in Googla. Brez spletne strani izgubljate ta del strank."

### Če ima SLABO stran

„Vaša spletna stran nima varnostnega certifikata. To pomeni, da obiskovalci v brskalniku vidijo opozorilo „Ni varno", kar zmanjšuje zaupanje. Google vas zaradi tega tudi slabše uvršča v rezultatih iskanja."

„Vaša spletna stran ni mobilno prilagojena. Več kot 70 % obiskovalcev pride s telefonom. Če stran ni prilagojena, odidejo v 3 sekundah."

„Vaša stran nima opisa za iskalnike. Ko nekdo poišče vašo storitev na Googlu, se prikaže prazen rezultat namesto opisa vaše ponudbe."

## Katere panoge iščemo

Zdravstvo: zobozdravniki, zobotehniki, fizioterapevti, maserji.
Lepota: kozmetični saloni, frizerji, manikura/pedikura, obrvi in trepalnice.
Živali: pasji saloni.
Avto: mehaniki, kleparstvo/lakirnica, avto elektrika, vulkanizerstvo.
Obrt: mizarji, suhomontažerji, vodovodarji, električarji, ključavničarji, slikopleskarji, tesarji, krovci, keramičarji, steklarji, klima servisi.

Če želiš dodati novo panogo, povej Mojci. Doda se v eni vrstici.

## Kako dodam novo mesto

V datoteki `config.py` odkomentiraš mesto:

```python
SEARCH_LOCATIONS = [
    "Maribor",
    # "Ljubljana",    ← odstrani # na začetku
    # "Celje",
]
```

Ali pa povej Mojci, da to naredi.

## Kako pogosto poženem

Enkrat na teden je dovolj. Ponedeljek zjutraj: poženeš, pregledaš HOT leade, pripraviš kontakte za teden.

## Kje so datoteke

Vse v mapi `output/`:

| Datoteka | Kaj je |
|---|---|
| leads_scored.csv | **Glavni rezultat.** To odpreš. |
| diagnostics.csv | Podrobna diagnostika vsake strani |
| businesses_all.csv | Vsa najdena podjetja |

Vsak zagon prepiše stare datoteke. Če želiš shraniti prejšnje rezultate, preimenuj mapo (npr. `output-2026-05-12`).
