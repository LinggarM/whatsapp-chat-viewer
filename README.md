# WhatsApp Chat Viewer

Aplikasi web berbasis Flask untuk memvisualisasikan ekspor chat WhatsApp dalam tampilan yang menyerupai antarmuka asli WhatsApp.

![Python](https://img.shields.io/badge/Python-3.7+-blue) ![Flask](https://img.shields.io/badge/Flask-2.x-green) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Tampilan

- Dark theme khas WhatsApp (hijau & abu-abu gelap)
- Bubble chat dengan ekor (tail) kiri/kanan
- Avatar inisial warna-warni per pengirim
- Pemisah tanggal otomatis
- Tanda centang biru untuk pesan pengirim

---

## Fitur

- **Upload file `.txt`** — drag & drop atau klik untuk memilih file ekspor WhatsApp
- **Paste teks langsung** — tidak perlu file, cukup paste teks chat ke textarea
- **Parser cerdas** — mendukung format tanggal `DD/MM/YY` dan `DD/MM/YYYY`, pemisah titik maupun titik dua pada waktu
- **Pesan multi-baris** — konten pesan yang panjang dan berbaris banyak tetap terbaca dengan benar
- **Pesan sistem** — info enkripsi, bergabung/keluar grup ditampilkan sebagai label tengah
- **Media placeholder** — `<Media tidak disertakan>` tampil dengan ikon gambar dan teks miring
- **Pesan terhapus** — ditampilkan dengan ikon 🚫 dan gaya italic
- **Link clickable** — URL di dalam pesan otomatis jadi hyperlink
- **Pencarian real-time** — filter pesan dan highlight teks hasil pencarian
- **Pengelompokan pengirim** — avatar hanya muncul sekali di awal rangkaian pesan dari pengirim yang sama
- **Tombol kembali** — upload chat baru tanpa restart server

---

## Instalasi

### Prasyarat

- Python 3.7 atau lebih baru
- pip

### Langkah

```bash
# 1. Clone atau download file app.py ke folder proyek
mkdir wa-chat-viewer
cd wa-chat-viewer

# 2. (Opsional) Buat virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependensi
pip install flask

# 4. Jalankan aplikasi
python app.py
```

Buka browser dan akses **http://localhost:5000**

---

## Cara Mendapatkan File Ekspor WhatsApp

### Di Android

1. Buka chat yang ingin diekspor
2. Ketuk ⋮ (tiga titik) → **Lainnya** → **Ekspor chat**
3. Pilih **Tanpa media**
4. Simpan atau kirim file `.txt` ke komputer

### Di iPhone

1. Buka chat → ketuk nama kontak/grup di bagian atas
2. Scroll ke bawah → **Ekspor Chat**
3. Pilih **Tanpa Media**
4. Simpan file `.txt`

---

## Format yang Didukung

Parser mendukung dua format umum ekspor WhatsApp:

```
DD/MM/YY HH.MM - Nama: Pesan
DD/MM/YYYY HH:MM - Nama: Pesan
```

Contoh:

```
03/06/24 12.46 - Pesan dan panggilan terenkripsi secara end-to-end.
05/06/24 14.47 - Irsal: http://contoh.com
24/06/24 10.08 - Irsal: <Media tidak disertakan>
04/09/24 19.53 - Linggar FTF: Makasih banyak mas 👍🏻
```

---

## Struktur File

```
wa-chat-viewer/
└── app.py          # Aplikasi Flask (semua logika + template HTML dalam satu file)
```

---

## Konfigurasi

Secara default aplikasi berjalan di `host=0.0.0.0` port `5000`. Ubah di bagian bawah `app.py` jika diperlukan:

```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

Untuk production, gunakan WSGI server seperti `gunicorn`:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## Catatan Privasi

Aplikasi ini berjalan **sepenuhnya lokal** di komputer Anda. Tidak ada data chat yang dikirim ke server eksternal manapun. File `.txt` hanya diproses di memori saat request berlangsung dan tidak disimpan ke disk.

---

## Lisensi

MIT License — bebas digunakan dan dimodifikasi.
