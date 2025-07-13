F# K-ARRAY COMPLETE EXTRACTION TODOLIST

## DESCRIZIONE DEL TASK GENERALE

**OBIETTIVO**: Processare sistematicamente TUTTI i link dalla sitemap K-Array per creare un dataset completo di retrival (RAG) con qualità MVP e zero-hallucination compliance.

**STRATEGIA QUALITÀ**:
- ✅ Qualità > Velocità ("qualità > velocità") 
- ✅ Zero-hallucination: ogni specifica tecnica deve avere citazione esatta dalla fonte
- ✅ Source attribution completa per ogni informazione estratta
- ✅ Cross-verification tra pagine HTML e PDF datasheets quando possibile
- ✅ Tracking sistematico per assicurare copertura completa (no link saltati)

**METODO DI ESTRAZIONE**:
1. Utilizzare WebFetch per ogni URL con prompt multipli specializzati MVP per massima qualità
2. Processare un URL alla volta per garantire controllo qualità totale
3. Estrarre SOLO informazioni esplicitamente dichiarate nel contenuto  
4. Mai inferire, stimare, assumere o speculare valori
5. Ogni specifica tecnica deve includere citazione esatta: (Source: "testo esatto")
6. Se un'informazione non è esplicitamente dichiarata, marcare come "Not specified"
7. Timeout + 2 retry per ogni URL, poi marcatura [❌]
8. Verifica qualitativa obbligatoria su ogni singolo URL processato

**FILTRI APPLICATI**:
- ❌ Esclusi file > 20MB (troppo grandi)
- ❌ Esclusi formati non supportati (.pkg, .exe, .dmg, .zip, ecc.)
- ❌ Esclusi link malformati o rotti
- ❌ Escluse pagine di login/registrazione
- ✅ Inclusi: pagine HTML, PDF datasheets, pagine prodotti, case studies, applicazioni

**PROGRESS TRACKING**:
- [ ] = Non processato
- [✅] = Completato con successo e verificato qualità
- [❌] = Fallito o non accessibile  
- [⚠️] = Processato ma qualità da rivedere
- [⏭️] = Saltato (non rilevante o non supportato)


---

## URLS DA PROCESSARE ()


### CATEGORIA: PRODOTTI - KOMMANDER SERIES
#1 [✅] https://www.k-array.com/en/product/kommander-ka104
#2 [✅] https://www.k-array.com/en/product/kommander-ka208
#3 [✅] https://www.k-array.com/en/product/kommander-ka24
#4 [✅] https://www.k-array.com/en/product/kommander-ka84
#5 [✅] https://www.k-array.com/en/product/kommander-ka68
#6 [✅] https://www.k-array.com/en/product/Kommander-KA02I
#7 [✅] https://www.k-array.com/en/product/Kommander-KA14i
#8 [✅] https://www.k-array.com/en/product/kommander-ka28
#9 [✅] https://www.k-array.com/en/product/kommander-ka02
#10 [✅] https://www.k-array.com/en/product/kommander-ka14
#11 [✅] https://www.k-array.com/en/product/kommander-ka34
#12 [✅] https://www.k-array.com/en/product/Kommander-KA18
#13 [✅] https://www.k-array.com/en/product/Kommander-KA04
#14 [✅] https://www.k-array.com/en/product/Kommander-KA18+
#15 [✅] https://www.k-array.com/en/product/kommander-ka28+
#16 [✅] https://www.k-array.com/en/product/kommander-ka68+
#17 [✅] https://www.k-array.com/en/product/kommander-ka104live
#18 [✅] https://www.k-array.com/en/product/kommander-ka208live
#19 [✅] https://www.k-array.com/en/product/kommander-ka208+
#20 [✅] https://www.k-array.com/en/product/kommander-ka208live+

### CATEGORIA: PRODOTTI - TORNADO SERIES
#21 [✅] https://www.k-array.com/en/product/tornado-kt2
#22 [✅] https://www.k-array.com/en/product/tornado-kt2c

### CATEGORIA: PRODOTTI - KOBRA SERIES
#23 [✅] https://www.k-array.com/en/product/kobra-kk52-i
#24 [✅] https://www.k-array.com/en/product/kobra-kk102-i

### CATEGORIA: PRODOTTI - PYTHON SERIES
#25 [✅] https://www.k-array.com/en/product/python-kp52-i
#26 [✅] https://www.k-array.com/en/product/python-kp102-i

### CATEGORIA: PRODOTTI - THUNDER SERIES
#27 [✅] https://www.k-array.com/en/product/thunder-kmt18p
#28 [✅] https://www.k-array.com/en/product/thunder-ks2pI
#29 [✅] https://www.k-array.com/en/product/thunder-kmt12p
#30 [✅] https://www.k-array.com/en/product/thunder-ks5I
#31 [✅] https://www.k-array.com/en/product/thunder-ks3I
#32 [✅] https://www.k-array.com/en/product/thunder-ks3pI
#33 [✅] https://www.k-array.com/en/product/thunder-ks4I
#34 [✅] https://www.k-array.com/en/product/thunder-ks4pI
#35 [✅] https://www.k-array.com/en/product/thunder-kmt218
#36 [✅] https://www.k-array.com/en/product/thunder-kmt18i
#37 [✅] https://www.k-array.com/en/product/thunder-ks2I
#38 [✅] https://www.k-array.com/en/product/thunder-kmt21-i
#39 [✅] https://www.k-array.com/en/product/thunder-ks5pI
#40 [✅] https://www.k-array.com/en/product/thunder-ks1I
#41 [✅] https://www.k-array.com/en/product/thunder-kmt21p
#42 [✅] https://www.k-array.com/en/product/thunder-kmt12-i
#43 [✅] https://www.k-array.com/en/product/thunder-ks1p
#44 [✅] https://www.k-array.com/en/product/thunder-ksc18p
#45 [✅] https://www.k-array.com/en/product/thunder-kmt218p
#46 [✅] https://www.k-array.com/en/product/thunder-ksc12p
#47 [✅] https://www.k-array.com/en/product/Thunder-KSC18P

### CATEGORIA: PRODOTTI - LYZARD SERIES
#48 [✅] https://www.k-array.com/en/product/lyzard-kz14I
#49 [✅] https://www.k-array.com/en/product/lyzard-kz14
#50 [✅] https://www.k-array.com/en/product/lyzard-kz14rI
#51 [✅] https://www.k-array.com/en/product/lyzard-kz1I
#52 [✅] https://www.k-array.com/en/product/lyzard-kz1
#53 [✅] https://www.k-array.com/en/product/lyzard-kz1rI
#54 [✅] https://www.k-array.com/en/product/Lyzard-KZ14

### CATEGORIA: PRODOTTI - VYPER SERIES
#55 [✅] https://www.k-array.com/en/product/Vyper-KV25II
#56 [✅] https://www.k-array.com/en/product/vyper-kv25l
#57 [✅] https://www.k-array.com/en/product/vyper-kv52l
#58 [✅] https://www.k-array.com/en/product/Vyper-KV52R%20II
#59 [✅] https://www.k-array.com/en/product/Vyper-KV52F%20II
#60 [✅] https://www.k-array.com/en/product/Vyper-KV102RII
#61 [✅] https://www.k-array.com/en/product/Vyper-KV102II
#62 [✅] https://www.k-array.com/en/product/Vyper-KV52II
#63 [✅] https://www.k-array.com/en/product/vyper-kv25wl
#64 [✅] https://www.k-array.com/en/product/Vyper-KV25R%20II
#65 [✅] https://www.k-array.com/en/product/Vyper-KV52FR%20II
#66 [✅] https://www.k-array.com/en/product/vyper-kv25II

### CATEGORIA: PRODOTTI - AZIMUT SERIES
#67 [✅] https://www.k-array.com/en/product/azimut-kamut2l14II
#68 [✅] https://www.k-array.com/en/product/azimut-kamut2l
#69 [✅] https://www.k-array.com/en/product/azimut-kamut2II
#70 [✅] https://www.k-array.com/en/product/azimut-kamut2v25II
#71 [✅] https://www.k-array.com/en/product/azimut-kamut2l1
#72 [✅] https://www.k-array.com/en/product/azimut-kamut2l1II
#73 [✅] https://www.k-array.com/en/product/azimut-kamut2v25
#74 [✅] https://www.k-array.com/en/product/azimut-kamut2l14

### CATEGORIA: PRODOTTI - RUMBLE SERIES
#75 [✅] https://www.k-array.com/en/product/rumble-ku44
#76 [✅] https://www.k-array.com/en/product/rumble-ku26
#77 [✅] https://www.k-array.com/en/product/rumble-ku210
#78 [✅] https://www.k-array.com/en/product/rumble-ku212
#79 [✅] https://www.k-array.com/en/product/rumble-ku315
#80 [✅] https://www.k-array.com/en/product/Rumble-KU44

### CATEGORIA: PRODOTTI - MUGELLO SERIES
#81 [✅] https://www.k-array.com/en/product/mugello-kh5l
#82 [✅] https://www.k-array.com/en/product/mugello-kh3l
#83 [✅] https://www.k-array.com/en/product/mugello-kh2l
#84 [✅] https://www.k-array.com/en/product/mugello-kh2pl
#85 [✅] https://www.k-array.com/en/product/mugello-kh5pl
#86 [✅] https://www.k-array.com/en/product/mugello-kh3pl
#87 [✅] https://www.k-array.com/en/product/Mugello-KH2-I-SYST12
#88 [✅] https://www.k-array.com/en/product/mugello-kh5
#89 [✅] https://www.k-array.com/en/product/mugello-kh2
#90 [✅] https://www.k-array.com/en/product/mugello-kh3

### CATEGORIA: PRODOTTI - FIRENZE SERIES
#91 [✅] https://www.k-array.com/en/product/firenze-kh7
#92 [✅] https://www.k-array.com/en/product/firenze-ks7
#93 [✅] https://www.k-array.com/en/product/firenze-ks8
#94 [✅] https://www.k-array.com/en/product/firenze-kh7p
#95 [✅] https://www.k-array.com/en/product/firenze-ks7p
#96 [✅] https://www.k-array.com/en/product/firenze-kx12fI
#97 [✅] https://www.k-array.com/en/product/firenze-kh8

### CATEGORIA: PRODOTTI - TRUFFLE SERIES
#98 [✅] https://www.k-array.com/en/product/truffle-ktr26
#99 [✅] https://www.k-array.com/en/product/truffle-ktr24
#100 [✅] https://www.k-array.com/en/product/truffle-ktr25
#101 [✅] https://www.k-array.com/en/product/Truffle-KTR24

### CATEGORIA: PRODOTTI - KAYMAN SERIES
#102 [✅] https://www.k-array.com/en/product/kayman-ky102
#103 [✅] https://www.k-array.com/en/product/kayman-ky52
#104 [✅] https://www.k-array.com/en/product/kayman-ky102-ebs
#105 [⏭️] https://www.k-array.com/en/product/Kayman-KY102

### CATEGORIA: PRODOTTI - TURTLE SERIES
#106 [✅] https://www.k-array.com/en/product/turtle-krm33p
#107 [✅] https://www.k-array.com/en/product/turtle-krm33
#108 [⏭️] https://www.k-array.com/en/product/Turtle-KRM33P

### CATEGORIA: PRODOTTI - ANAKONDA SERIES
#109 [✅] https://www.k-array.com/en/product/anakonda-kan200
#110 [✅] https://www.k-array.com/en/product/anakonda-kan200-plus
#111 [✅] https://www.k-array.com/en/product/anakonda-kan200-plus8

### CATEGORIA: PRODOTTI - DOMINO SERIES
#112 [✅] https://www.k-array.com/en/product/domino-kf26
#113 [✅] https://www.k-array.com/en/product/domino-kf212
#114 [✅] https://www.k-array.com/en/product/domino-kf210
#115 [✅] https://www.k-array.com/en/product/domino-kfc26
#116 [⏭️] https://www.k-array.com/en/product/Domino-KF212

### CATEGORIA: PRODOTTI - DRAGON SERIES
#117 [✅] https://www.k-array.com/en/product/dragon-kx12I
#118 [✅] https://www.k-array.com/en/product/dragon-kxt12p
#119 [✅] https://www.k-array.com/en/product/dragon-kxt18p

### CATEGORIA: PRODOTTI - MASTIFF SERIES
#120 [✅] https://www.k-array.com/en/product/mastiff-km312
#121 [✅] https://www.k-array.com/en/product/mastiff-km112
#122 [✅] https://www.k-array.com/en/product/mastiff-km112p
#123 [✅] https://www.k-array.com/en/product/mastiff-km312p

### CATEGORIA: PRODOTTI - PINNACLE SERIES
#124 [✅] https://www.k-array.com/en/product/pinnacle-kr102-i
#125 [✅] https://www.k-array.com/en/product/pinnacle-kr402-i
#126 [✅] https://www.k-array.com/en/product/pinnacle-kr202-i
#127 [✅] https://www.k-array.com/en/product/Pinnacle-KR802YPII
#128 [✅] https://www.k-array.com/en/product/pinnacle-kr102-ll
#129 [✅] https://www.k-array.com/en/product/Pinnacle-KR202-II
#130 [✅] https://www.k-array.com/en/product/Pinnacle-KR402%20II
#131 [✅] https://www.k-array.com/en/product/pinnacle-kr802
#132 [✅] https://www.k-array.com/en/product/Pinnacle-KR804P%20II
#133 [✅] https://www.k-array.com/en/product/Pinnacle-KR802%20II
#134 [✅] https://www.k-array.com/en/product/Pinnacle-KR404P%20II
#135 [✅] https://www.k-array.com/en/product/Pinnacle-KR402YPII
#136 [✅] https://www.k-array.com/en/product/Pinnacle-K-FoH2

### CATEGORIA: PRODOTTI - DOLOMITE SERIES
#137 [✅] https://www.k-array.com/en/product/dolomite-krd202p

### CATEGORIA: PRODOTTI - PRISMA SERIES
#138 [✅] https://www.k-array.com/en/product/Prisma-KPR00+
#139 [✅] https://www.k-array.com/en/product/Prisma-KPRA14+
#140 [✅] https://www.k-array.com/en/product/Prisma-KPRA34+

### CATEGORIA: PRODOTTI - CAPTURE SERIES
#141 [✅] https://www.k-array.com/en/product/capture-kmc20
#142 [✅] https://www.k-array.com/en/product/capture-kmc20h
#143 [✅] https://www.k-array.com/en/product/capture-kmc20v
#144 [✅] https://www.k-array.com/en/product/capture-kmc50

### CATEGORIA: PRODOTTI - DUETTO SERIES
#145 [✅] https://www.k-array.com/en/product/duetto-kd6t
#146 [✅] https://www.k-array.com/en/product/duetto-kd6b
#147 [✅] https://www.k-array.com/en/product/duetto-kd6bt

### CATEGORIA: PRODOTTI - AXLE SERIES
#148 [✅] https://www.k-array.com/en/product/axle-krx402
#149 [✅] https://www.k-array.com/en/product/axle-krx802

### CATEGORIA: PRODOTTI - EVENT SERIES
#150 [✅] https://www.k-array.com/en/product/event-krev101

### CATEGORIA: PRODOTTI - ALTRI
#151 [✅] https://www.k-array.com/en/product/kk50
#152 [✅] https://www.k-array.com/en/product/kn10s
#153 [✅] https://www.k-array.com/en/product/ktl22-ktl22c
#154 [✅] https://www.k-array.com/en/product/K-RACK-M-208

### CATEGORIA: LINEE PRODOTTI
#155 [✅] https://www.k-array.com/en/products/line/lyzard
#156 [✅] https://www.k-array.com/en/products/line/vyper
#157 [✅] https://www.k-array.com/en/products/line/anakonda
#158 [✅] https://www.k-array.com/en/products/line/tornado
#159 [✅] https://www.k-array.com/en/products/line/kobra
#160 [✅] https://www.k-array.com/en/products/line/python
#161 [✅] https://www.k-array.com/en/products/line/kayman
#162 [✅] https://www.k-array.com/en/products/line/domino
#163 [✅] https://www.k-array.com/en/products/line/dragon
#164 [✅] https://www.k-array.com/en/products/line/mugello
#165 [✅] https://www.k-array.com/en/products/line/firenze
#166 [✅] https://www.k-array.com/en/products/line/rumble
#167 [✅] https://www.k-array.com/en/products/line/truffle
#168 [✅] https://www.k-array.com/en/products/line/thunder
#169 [✅] https://www.k-array.com/en/products/line/azimut
#170 [✅] https://www.k-array.com/en/products/line/Dolomite
#171 [✅] https://www.k-array.com/en/products/line/pinnacle
#172 [✅] https://www.k-array.com/en/products/line/turtle
#173 [✅] https://www.k-array.com/en/products/line/mastiff
#174 [✅] https://www.k-array.com/en/products/line/Prisma
#175 [✅] https://www.k-array.com/en/products/line/kommander
#176 [✅] https://www.k-array.com/en/products/line/capture
#177 [✅] https://www.k-array.com/en/products/line/duetto

### CATEGORIA: APPLICAZIONI
#178 [✅] https://www.k-array.com/en/application/fitness-and-wellness
#179 [✅] https://www.k-array.com/en/application/cafes-and-restaurants
#180 [✅] https://www.k-array.com/en/application/museums-and-exhibitions
#181 [✅] https://www.k-array.com/en/application/large-congregations
#182 [✅] https://www.k-array.com/en/application/theme-parks
#183 [✅] https://www.k-array.com/en/application/houses-of-worship
#184 [✅] https://www.k-array.com/en/application/nightclubs
#185 [✅] https://www.k-array.com/en/application/event-productions
#186 [✅] https://www.k-array.com/en/application/retail
#187 [✅] https://www.k-array.com/en/application/broadcast-and-studios
#188 [✅] https://www.k-array.com/en/application/transportation-facilities
#189 [✅] https://www.k-array.com/en/application/theaters
#190 [✅] https://www.k-array.com/en/application/stadium-and-sport-venues
#191 [✅] https://www.k-array.com/en/application/hotels-and-resorts
#192 [✅] https://www.k-array.com/en/application/concerts-and-live-events
#193 [✅] https://www.k-array.com/en/application/boardrooms
#194 [✅] https://www.k-array.com/en/application/auditoriums-and-concert-halls
#195 [✅] https://www.k-array.com/en/application/residential
#196 [✅] https://www.k-array.com/en/application/Residential-Lighting
#197 [✅] https://www.k-array.com/en/application/Museum%20and%20Ehibitions-Lighting
#198 [✅] https://www.k-array.com/en/application/Hospitality-Lighting
#199 [✅] https://www.k-array.com/en/application/Corporate-Lighting
#200 [✅] https://www.k-array.com/en/application/Retail-Lighting

### CATEGORIA: K-ACADEMY EDUCATIONAL
#520 [ ] https://www.k-array.com/en/k-academy/1
#521 [ ] https://www.k-array.com/en/k-academy/20
#522 [ ] https://www.k-array.com/en/k-academy/19
#523 [ ] https://www.k-array.com/en/k-academy/3
#524 [ ] https://www.k-array.com/en/k-academy/2
#525 [ ] https://www.k-array.com/en/k-academy/13
#526 [ ] https://www.k-array.com/en/k-academy/14
#527 [ ] https://www.k-array.com/en/k-academy/18
#528 [ ] https://www.k-array.com/en/k-academy/17
#529 [ ] https://www.k-array.com/en/k-academy/16
#530 [ ] https://www.k-array.com/en/k-academy/15
#531 [ ] https://www.k-array.com/en/k-academy/5
#532 [ ] https://www.k-array.com/en/k-academy/9
#533 [ ] https://www.k-array.com/en/k-academy/8
#534 [ ] https://www.k-array.com/en/k-academy/10
#535 [ ] https://www.k-array.com/en/k-academy/11
#536 [ ] https://www.k-array.com/en/k-academy/7

### CATEGORIA: ACCESSORI
#537 [ ] https://www.k-array.com/en/accessory/ka1-t2h
#538 [ ] https://www.k-array.com/en/accessory/k-wf26

### CATEGORIA: SOFTWARE
#539 [ ] https://www.k-array.com/en/software

### CATEGORIA: INFORMAZIONI AZIENDALI
#540 [ ] https://www.k-array.com/en/about
#541 [ ] https://www.k-array.com/en/contact/headquarters-people
#542 [ ] https://www.k-array.com/en/distributors
#543 [ ] https://www.k-array.com/en/contact


---

### STRATEGIA DI PROCESSING:
- **ORDINE**: Progressivo (#1 → #2 → #3 → ... → #543)
- **MODALITÀ**: Un URL alla volta con verifica qualitativa completa
- **OUTPUT**: File JSON separati ottimizzati per embedding vettoriale
- **RETRY POLICY**: Timeout + 2 tentativi, poi [❌]

### QUALITÀ REQUIREMENTS PER OGNI URL:
- [ ] Contenuto estratto con prompt multipli specializzati
- [ ] Source attribution completa con citazioni esatte
- [ ] Zero-hallucination verificato manualmente
- [ ] Specifiche tecniche validate e strutturate
- [ ] Metadata e keywords ottimizzate per RAG
- [ ] Formato JSON pronto per embedding

### STRUTTURA OUTPUT JSON OTTIMIZZATA:
```json
{
  "id": "001",
  "url": "https://www.k-array.com/en/product/kommander-ka104",
  "timestamp": "2025-07-12T...",
  "extraction_quality": "verified",
  "metadata": {
    "category": "PRODUCTS",
    "subcategory": "KOMMANDER_SERIES",
    "product_line": "Kommander",
    "model": "KA104",
    "content_type": "product_page"
  },
  "keywords": {
    "primary": ["KA104", "Kommander", "speaker"],
    "technical": ["frequency_response", "power"],
    "applications": ["live_sound", "installation"],
    "unique_identifiers": ["ka104"]
  },
  "content_sections": {...},
  "embedding_optimized": {
    "searchable_text": "...",
    "semantic_chunks": [...],
    "qa_pairs": [...]
  },
  "source_attributions": [...]
}
```

---

## URLS SALTATI (7 totali)

- ⏭️ https://www.k-array.com/en/login (Motivo: Pagina di login/registrazione)
- ⏭️ https://www.k-array.com/en/sign-up (Motivo: Pagina di login/registrazione)
- ⏭️ https://www.k-array.com/en/application/%5Cen (Motivo: URL malformato)
- ⏭️ https://www.k-array.com/en/post/%5Cen (Motivo: URL malformato)


---

## ISTRUZIONI PER L'USO

1. **Processare URLs in ordine progressivo (#1 → #2 → #3...)**
2. **Per ogni URL:**
   - Estrarre contenuto con prompt multipli WebFetch
   - Verifica qualitativa manuale obbligatoria  
   - Generare file JSON ottimizzato per embedding
   - Aggiornare status nel todolist
3. **Marcatura progresso:**
   - [✅] = Completato con successo e verificato qualità
   - [❌] = Fallito dopo timeout + 2 retry
   - [⚠️] = Processato ma qualità da rivedere
4. **Naming convention file output:**
   - `extracted_data_001_kommander_ka104.json`
   - `extracted_data_002_kommander_ka208.json`
   - etc.

**COMANDO PER AGGIORNARE PROGRESSO**:
```bash
# Esempio per URL #1
sed -i 's/#1 \[ \]/#1 [✅]/' K_ARRAY_COMPLETE_TODOLIST.md
```

**ULTIMA MODIFICA**: 2025-07-12 00:47:19
