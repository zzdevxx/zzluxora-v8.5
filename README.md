# 🎛️ zzluxora v8.5.0 (AppContext & .zlx Edition)

> **Native PySide6 (Qt6) + Art-Net DMX512 Lighting Control with Dependency-Injected Architecture & Custom Project File Support.**  
> Edisi rilis v8.5 dengan arsitektur modern `AppContext` Service Registry (ADR-2), format penyimpanan proyek kustom **`.zlx`**, thread pekerja audio Librosa (`QThread`), dan kelulusan pengujian unit test **42/42 Tests Passed (100%)**.

---

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt6-41CD52?style=flat-square&logo=qt&logoColor=white)
![Architecture](https://img.shields.io/badge/Architecture-AppContext_DI_(ADR--2)-purple?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-42%2F42_Passed_(100%25)-brightgreen?style=flat-square)
![Project Format](https://img.shields.io/badge/Project_File-.zlx_(JSON_Schema)-orange?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows_10%2F11-0078D6?style=flat-square&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

---

## 📑 Daftar Isi
1. [Gambaran Umum Proyek](#-1-gambaran-umum-proyek)
2. [Inovasi & Fitur Unggulan v8.5.0](#-2-inovasi--fitur-unggulan-v850)
3. [Arsitektur AppContext & Dependency Injection](#-3-arsitektur-appcontext--dependency-injection)
4. [Format Penyimpanan Proyek (.zlx)](#-4-format-penyimpanan-proyek-zlx)
5. [Katalog Direktori Proyek](#-5-katalog-direktori-proyek)
6. [Panduan Instalasi & Eksekusi](#-6-panduan-instalasi--eksekusi)
7. [Hasil Pengujian Unit Test (42 Tests)](#-7-hasil-pengujian-unit-test-42-tests)
8. [Lisensi & Hak Cipta](#-8-lisensi--hak-cipta)

---

## 📖 1. Gambaran Umum Proyek

**zzluxora v8.5.0** menandai lonjakan arsitektural penting dalam evolusi perangkat lunak pengendali pencahayaan panggung cerdas berbasis Windows. Versi ini menuntaskan masalah ketergantungan singleton global dari versi terdahulu dengan memperkenalkan pola **Service Registry (AppContext)**, format proyek terstruktur **`.zlx`**, serta isolasi komputasi berat analisis musik menggunakan **Worker Threads (QThread)**.

Aplikasi ini mengekstrak parameter akustikal musik menggunakan **Librosa**, memetakan suasana lagu rohani ke ruang emosi afektif **Valence-Arousal (Russell Circumplex Model)**, mengonversi koordinat emosi ke ruang warna fisik **HSV ➔ RGB ➔ Physical 4-Channel RGBW**, dan mentransmisikan paket frame DMX512 via **Art-Net UDP Broadcast (Port 6454)** secara *real-time* ke mikrokontroler **ESP32**.

---

## ✨ 2. Inovasi & Fitur Unggulan v8.5.0

- 🧩 **AppContext Dependency Injection (ADR-2):** Seluruh panel UI kini menerima instance `ctx: AppContext` yang menyatukan manajemen `Config`, `FixtureManager`, `SongStore`, dan `ArtNetController` secara modular.
- 💾 **Custom Project File Format (`.zlx`):** Format file proyek berbasis JSON dengan validasi skema ketat untuk menyimpan patch fixture, cue scenes, chase sequences, dan metadata lagu.
- 🧵 **Non-Blocking Background Workers (`workers/audio_worker.py`):** Ekstraksi fitur audio Librosa yang membutuhkan komputasi berat dieksekusi pada thread latar belakang (`QThread`), menjaga UI tetap responsif pada 60 FPS tanpa *freezing*.
- 🗄️ **SongStore Data Registry:** Pusat penyimpanan lagu yang mengelola cache fitur akustik musik yang telah dianalisis untuk pemuatan instan.
- 🎚️ **Expanded DMX Channel Mixer:** Kontrol fader 513 kanal (512 Channel DMX + Master Dimmer Blackout Safety).
- 🧪 **Full Mathematical Unit Test Suite:** 42 unit test terintegrasi yang memverifikasi model matematika, normalisasi Min-Max, pemetaan kuadran emosi, I/O proyek `.zlx`, dan transmisi Art-Net.

---

## 🏗️ 3. Arsitektur AppContext & Dependency Injection

```text
+-----------------------------------------------------------------------------------------+
|                                ARSITEKTUR ZZLUXORA v8.5                                 |
+-----------------------------------------------------------------------------------------+
                          ┌──────────────────────────────┐
                          │   AppContext (Service Hub)   │
                          ├──────────────────────────────┤
                          │ • cfg      : AppConfig       │
                          │ • fixtures : FixtureManager  │
                          │ • songs    : SongStore       │
                          │ • artnet   : ArtNetController│
                          │ • project  : .zlx File State │
                          └──────────────┬───────────────┘
                                         │ Injected into
          ┌──────────────────────────────┴──────────────────────────────┐
          ▼                                                             ▼
  [UI PANELS & TABS]                                            [BACKGROUND WORKERS]
  • AddressTab (512 DMX Cells Patching)                         • audio_worker.py (QThread)
  • AudioTab (Spectrogram & Waveform)                           • Librosa MIR Extraction
  • ScenesTab & ChaseTab (Cue Management)
  • MixerTab (513 Faders: 512 DMX + Master)
  • PageTab (Live Button Pad Triggers)
  • PreviewTab (2D Stage Visualization)
          │
          ▼
  [NETWORK BROADCAST]
  • ArtNetController ➔ UDP Socket (Port 6454) ➔ ESP32 Receiver Node + MAX485
+-----------------------------------------------------------------------------------------+
```

---

## 💾 4. Format Penyimpanan Proyek (`.zlx`)

Format file `.zlx` menyimpan konfigurasi sistem pencahayaan dalam struktur JSON yang teratur:

```json
{
  "schema_version": "1.0",
  "project_name": "Ibadah_Raya_Minggu.zlx",
  "created_at": "2026-08-20T18:00:00Z",
  "artnet": {
    "target_ip": "255.255.255.255",
    "universe": 0,
    "fps": 40
  },
  "fixtures": [
    {
      "id": "par_01",
      "name": "Front PAR RGBW",
      "profile": "Generic PAR RGBW 8ch",
      "start_address": 1
    }
  ],
  "scenes": [],
  "chases": []
}
```

---

## 📁 5. Katalog Direktori Proyek

```text
zzluxora_v8.5/
├── main.py                  <- Entry point aplikasi (Inisialisasi AppContext & SplashScreen)
├── app.py                   <- Registry Service AppContext (ADR-2 Dependency Injection)
├── main_window.py           <- Jendela utama multi-panel
├── config.py / config.ini   <- Manajemen konfigurasi sistem
├── styles.py                <- Desain stylesheet QSS tema Gold Accent (#FFD700)
├── requirements.txt         <- Daftar dependensi Python
├── Untitled.zlx             <- Contoh template berkas proyek .zlx
│
├── 📂 core/                 <- Core business logic & data models:
│   ├── fixture_manager.py   <- Manajemen database lampu & DMX address map
│   ├── paths.py             <- Resolver direktori data & log
│   ├── project_io.py        <- Serializer & deserializer berkas .zlx
│   └── song_store.py        <- Manajemen memori lagu & fitur akustik
│
├── 📂 engines/              <- Computational engines:
│   ├── analyze_pipeline.py  <- Pipeline komputasi fitur audio
│   ├── artnet_sender.py     <- Socket Art-Net UDP 6454 broadcaster
│   ├── audio_engine.py      <- Ekstraksi fitur Librosa & tempo tracking
│   ├── chase.py             <- Algoritma sekuens chase ritmis
│   ├── color_mapping.py     <- Transformasi ruang warna HSV ke Physical RGBW
│   ├── color_mixer.py       <- Utilitas palet warna & Curve LUT
│   ├── fixture_types.py     <- Definisi profil kanal lampu DMX
│   ├── mood_engine.py       <- Classifier emosi musik Valence-Arousal
│   ├── scene_generator.py   <- Pembangkit cue pencahayaan otomatis
│   └── va_presets.py        <- Preset kuadran afektif Russell
│
├── 📂 workers/              <- Thread latar belakang:
│   └── audio_worker.py      <- QThread worker untuk pemrosesan Librosa non-blocking
│
├── 📂 panels/               <- Panel antarmuka pengguna:
│   ├── address_tab.py       <- Grid 512 alamat DMX (24 kolom)
│   ├── audio_tab.py         <- Visualizer waveform, RMS chart, & spektrum
│   ├── chase_tab.py         <- Editor sekuens chase lampu
│   ├── color_mixer_tab.py   <- Color picker manual
│   ├── mixer_tab.py         <- Fader 513 kanal DMX
│   ├── output_tab.py        <- Live Art-Net packet monitor
│   ├── page_tab.py          <- Grid tombol live show trigger
│   ├── preview_tab.py       <- Canvas panggung 2D
│   ├── program_panel.py     <- Multi-tab host container
│   ├── settings_panel.py    <- Pengaturan interface & IP Art-Net
│   └── about_panel.py       <- Metadata akademik & hak cipta
│
├── 📂 widgets/              <- Komponen UI kustom (Fader, Pill, Splash, Toast)
├── 📂 fixtures/             <- Profil lampu JSON (PAR LED, Moving Head)
└── 📂 tests/                <- 42 unit tests (Art-Net, Math Model, Tabs, Project I/O)
```

---

## 🚀 6. Panduan Instalasi & Eksekusi

### Persyaratan Sistem:
- **Sistem Operasi:** Windows 10 / 11 (64-bit)
- **Python:** Versi 3.10 atau lebih baru

### Langkah Menjalankan:
1. **Clone Repositori:**
   ```powershell
   git clone https://gitlab.com/zzdevxx/zzluxora_v8.5.git
   cd zzluxora-v8.5
   ```

2. **Install Dependensi:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Jalankan Aplikasi:**
   ```powershell
   python main.py
   ```

---

## 🧪 7. Hasil Pengujian Unit Test (42 Tests)

Seluruh 42 unit test lulus 100% tanpa kegagalan:

```text
============================= test session starts =============================
platform win32 -- Python 3.14+ -- pytest-9.1+
collected 42 items

tests/test_art_net.py (5 tests)         : PASSED [100%]
tests/test_math_model.py (26 tests)     : PASSED [100%]
tests/test_program_tabs.py (5 tests)    : PASSED [100%]
tests/test_project_io.py (6 tests)      : PASSED [100%]

============================= 42 passed in 3.27s ==============================
```

Untuk menjalankan pengujian secara mandiri:
```powershell
pytest tests/ -v
```

---

## 📜 8. Lisensi & Hak Cipta

Proyek ini dilisensikan di bawah **MIT License**.  
Hak Cipta (c) 2026 **Andreas Restuawanta Christwara ([@zzdevxx](https://github.com/zzdevxx))** — Universitas Negeri Semarang.
