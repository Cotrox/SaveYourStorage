<div align="center">
  <img src="assets/cotrox-avatar.png" alt="Avatar di Giuseppe Antonino Cotroneo" width="128" height="128">
  <h1>🚀 SaveYourStorage</h1>
  <p>Media Optimizer & Video Trimmer Desktop (WinUI 3)</p>
  <p>
    <a href="https://ko-fi.com/cotrox">
      <img src="https://img.shields.io/badge/Ko--fi-Supporta%20il%20progetto-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white" alt="Supporta su Ko-fi">
    </a>
    <a href="https://www.paypal.com/paypalme/graficarulez">
      <img src="https://img.shields.io/badge/PayPal-Supporta%20il%20progetto-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="Supporta su PayPal">
    </a>
  </p>
</div>

Un software desktop moderno, minimale e ad alte prestazioni per Windows con estetica **WinUI 3 / Fluent Design**. Progettato da **Giuseppe Antonino Cotroneo** per ottimizzare, velocizzare, tagliare e convertire video e immagini in sicurezza, riducendo drasticamente lo spazio occupato su disco senza perdite qualitative percettibili (*visually lossless*).

---

## ☕ Supporta il Progetto

Se trovi **SaveYourStorage** utile per il tuo lavoro quotidiano o per liberare preziosi gigabyte di spazio sui tuoi dischi, puoi supportare direttamente lo sviluppo offrendo un caffè:

👉 **[Supporta Giuseppe Antonino Cotroneo su Ko-fi](https://ko-fi.com/cotrox)**

Oppure fai una donazione tramite **[PayPal.Me](https://www.paypal.com/paypalme/graficarulez)**.

Il tuo supporto consente di mantenere il software costantemente aggiornato, gratuito e senza pubblicità!

---

## 🌟 Caratteristiche Principali

- 🛡️ **Sicurezza Totale e Output Separato**: I file di origine rimangono sempre intatti e al loro posto. Nessun file originale viene mai sovrascritto. La cartella di destinazione è personalizzabile a piacere.
- 🔄 **Conversione Formato Flessibile**:
  - **Video**: `.MP4` (H.264 o H.265 ad altissima efficienza), `.MOV`, `.MKV`, `.WebM` (VP9/AV1), `.AVI`, `.GIF` animata.
  - **Foto**: `.WebP` (risparmio fino all'80% di spazio), `.JPG`, `.PNG`, `.AVIF`.
- ⚡ **Velocizzazione Video e Audio**:
  - Moltiplicatori rapidi: **1.25x**, **1.5x**, **2x**, **3x**, **5x**, **8x** (con concatenazione di filtri `atempo` per correzione pitch e sincronia perfetta).
  - Modalità **Video Muto**: rimuove completamente l'audio (`-an`) per ridurre ulteriormente il peso dei file nei video accelerati o b-roll.
- 📉 **Compressione Intelligente & Upscaling HQ**:
  - Profili: *Visually Lossless* (CRF 20), *Bilanciato* (CRF 26 H.265 con risparmio dal 50% al 70%), *Compressione Massima* (CRF 32) o *Lossless Puro* (CRF 0).
  - Ridimensionamento intelligente: Rileva automaticamente video verticali e orizzontali preservando le proporzioni native (720p, 1080p Full HD, scala 25%, scala 50%, scala 75%).
  - **✨ Upscaling 2x**: Algoritmo di super-interpolazione **Lanczos** ad alta precisione con filtro nitidezza (*unsharp mask*).
- 📐 **Orientamento, Formati Social & Ritaglio Inquadratura (Zero Bande Nere)**:
  - Scelta proporzioni: **Verticale 9:16** (TikTok, Reels, Shorts), **Orizzontale 16:9** (YouTube, Desktop), **Quadrato 1:1**, **Verticale 4:5** o **Ritaglio Libero (Custom Crop)**.
  - Modalità **Riempi Schermo (Crop & Fill)**: elimina totalmente le bande nere ritagliando l'inquadratura al formato desiderato.
  - **Riposizionamento Inquadratura**: cursore da 0% a 100% (o preset *Inizio*, *Centro*, *Fine*) per centrare o spostare l'inquadratura esattamente sul soggetto.
  - **Ritaglio Libero**: imposta coordinate X/Y e dimensioni % per ritagliare qualsiasi area specifica del video.
- ✂️ **Video Trimming Interattivo con Anteprima**:
  - Quando carichi un **singolo video**, l'interfaccia attiva automaticamente il player video e il modulo di trimming.
  - Cursori visivi per impostare inizio e fine, pulsanti di avanzamento millimetrico (`-1s`, `-0.1s`, `+0.1s`, `+1s`), scorciatoie da tastiera (**Spazio**, **I**, **O**, **←/→**) e calcolo in tempo reale della durata finale e della percentuale tagliata.
  - Se carichi una cartella intera o più file, l'app passa automaticamente alla modalità **Elaborazione Batch** con coda completa e statistiche di risparmio per ciascun file.
- ⏱️ **Velocità temporale selettiva**: aggiungi più intervalli della timeline da
  mantenere a velocità normale; il resto del video e dell'audio viene
  velocizzato mantenendo la sincronizzazione.

---

## 📂 Struttura del Progetto

```text
SaveYourStorage/
├── bin/
│   ├── ffmpeg.exe         # Binario locale, scaricato durante la build/release
│   └── ffprobe.exe        # Binario locale per l'ispezione dei metadati multimediali
├── web/
│   ├── index.html         # Interfaccia grafica Fluent Design / WinUI 3
│   ├── style.css          # Tema scuro Acrylic / Mica con palette moderna
│   └── app.js             # Gestione interattiva player, slider, trimming e polling
├── scripts/
│   └── ensure_ffmpeg.py   # Verificatore e downloader di emergenza FFmpeg
├── engine.py              # Motore FFmpeg multithreading, filtri velocità, upscale e codec
├── scanner.py             # Analizzatore metadati (risoluzione, durata, bitrate, codec)
├── server.py              # Backend locale HTTP con dialog nativi Windows e streaming Range
├── start.bat              # Avvio 1-click in modalità Desktop WinUI (Edge App Mode)
├── start_silent.vbs       # Avvio silenzioso senza finestra terminale DOS
├── build_exe.bat          # Script per compilare l'app in un unico .EXE (PyInstaller)
├── packaging/             # Manifest e script per il pacchetto MSIX
├── .github/workflows/     # Build automatica delle release Windows
├── LICENSE                # Licenza MIT del codice del progetto
├── THIRD-PARTY-NOTICES    # Note sulle licenze di FFmpeg
├── requirements.txt       # Dipendenze opzionali
└── README.md              # Documentazione
```

---

## 🚀 Come Avviare l'Applicazione

### ⚙️ Gestione Componenti FFmpeg & FFprobe (Onboarding & Impostazioni)
- **Eseguibile portabile (.exe)**: L'eseguibile portabile contiene già FFmpeg e FFprobe inclusi. Chi scarica ed esegue `SaveYourStorage.exe` può usarlo immediatamente senza alcuna configurazione manuale.
- **Wizard di Onboarding con richiesta di consenso**: Se l'app viene avviata in un ambiente in cui i componenti non sono presenti (o se sono stati disinstallati), compare un wizard di primo avvio che spiega in modo chiaro perché FFmpeg e FFprobe siano fondamentali e richiede il consenso esplicito dell'utente prima di scaricarli e configurarli automaticamente in locale.
- **Pannello Impostazioni (icona ⚙️)**: Accessibile in qualsiasi momento dalla barra superiore (in alto a destra, accanto al pulsante Ko-Fi), mostra lo stato di FFmpeg e FFprobe con la relativa provenienza, permette di reinstallarli/aggiornarli con barra di avanzamento del download in tempo reale, oppure di disinstallarli.
- **Segnalazione e Notifica all'avvio**: Se i componenti sono disinstallati, sotto ciascuno di essi compare l'avviso che la reinstallazione è necessaria per il corretto funzionamento. Qualsiasi tentativo di avviare il processo di ottimizzazione notificherà all'utente l'assenza dei componenti con un dialog di avviso e il pulsante per installarli all'istante.

### Metodo 1: Avvio Rapido (.bat) — Consigliato
Fai doppio click su:
```bat
start.bat
```
*(Oppure su `start_silent.vbs` per aprirlo senza mostrare la finestra nera del prompt dei comandi).*

Il programma si aprirà istantaneamente in una **finestra desktop nativa** senza barra degli indirizzi o tab del browser (utilizzando la modalità *Edge App Mode* integrata in Windows).

### Metodo 2: Compilazione in file `.exe` autonomo
Se desideri creare un file eseguibile `.exe` distribuibile:
1. Fai doppio click su `build_exe.bat`.
2. Troverai l'eseguibile compilato all'interno della cartella `dist\SaveYourStorage\`.

---

## 🛠️ Come Funziona

1. **Carica il file o la cartella**:
   - Clicca su **"Carica Singolo File"** per un video o un'immagine specifica (attiverà il trimmer interattivo se video).
   - Oppure clicca su **"Carica Intera Cartella"** per elaborare centinaia di file contemporaneamente in batch.
2. **Personalizza le impostazioni**:
   - Scegli la cartella di destinazione (*predefinita: `NomeCartella_Output`*).
   - Seleziona il formato finale (es. converti da `.MOV` a `.MP4` con H.265).
   - Seleziona la velocità (1x, 1.25x, 1.5x, 2x, 3x, 5x, 8x) e decidi se mantenere o rimuovere l'audio.
   - Scegli il preset di compressione o attiva l'Upscaling 2x.
   - *(Opzionale per video singoli)* Imposta i punti di inizio e fine per ritagliare le parti non desiderate con precisione al frame.
3. **Avvia l'Ottimizzazione**:
   - Premi **"Avvia Ottimizzazione"**. La barra di avanzamento mostrerà in tempo reale la percentuale completata e lo spazio risparmiato (MB e percentuale).
   - Al termine, un pulsante ti consentirà di aprire direttamente la cartella di destinazione in Esplora Risorse.

---

## 📦 Distribuzione

Il progetto è predisposto per essere pubblicato su GitHub. Creando un tag
`v1.0.0`, GitHub Actions costruirà automaticamente l'archivio portabile e il
pacchetto MSIX.

Per una build locale:

```powershell
.\build_exe.bat
.\packaging\build_msix.ps1 -Version 1.0.0
```

Il pacchetto MSIX non firmato è adatto ai test locali. Per Microsoft Store è
necessario usare il publisher e il certificato associati al proprio account
Partner Center:

```powershell
.\packaging\build_msix.ps1 -Version 1.0.0 `
  -Publisher "CN=Publisher del Partner Center" `
  -Certificate .\certs\store-signing.pfx
```

Prima dell'invio allo Store occorre completare la scheda Partner Center,
verificare la firma e caricare le informazioni sulla privacy e sulla licenza di
FFmpeg riportate in `THIRD-PARTY-NOTICES`.

## 📚 Contribuire e licenza

- **`CONTRIBUTING.md`** è la guida per chi vuole contribuire al progetto:
  descrive come preparare l'ambiente, avviare l'app e verificare una modifica
  creando la build.
- **`LICENSE`** contiene i termini legali con cui il codice può essere usato,
  copiato, modificato e distribuito. Il codice del progetto è rilasciato con
  licenza MIT; le dipendenze esterne, come FFmpeg, mantengono le proprie
  licenze riportate in `THIRD-PARTY-NOTICES`.

## 👨‍💻 Autore & Crediti

- **Autore**: **Giuseppe Antonino Cotroneo** (`@Cotrox`)
- **Supporto**: [Ko-fi](https://ko-fi.com/cotrox) · [PayPal.Me](https://www.paypal.com/paypalme/graficarulez)
- **Licenza**: MIT per il codice del progetto; FFmpeg è distribuito secondo la licenza indicata in `THIRD-PARTY-NOTICES`.
