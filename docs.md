Tentu, berikut adalah dokumentasi lengkap dan detail dalam format Markdown (`.md`) berdasarkan file yang Anda unggah. Anda dapat langsung menyalinnya ke dalam program agar *agent* dapat memahami protokol komunikasi sistem secara menyeluruh.

---

# Dokumentasi Protokol Komunikasi Desktop Blood Pressure

## 1. Gambaran Umum & Strategi Kontrol

* 
**Tujuan:** Protokol ini dirancang untuk memastikan komunikasi yang andal antara komputer atas (*host/upper computer*) dan komputer bawah (*slave/lower computer*).


* 
**Mekanisme Verifikasi:** Setiap pesan menggunakan verifikasi CRC (*Cyclic Redundancy Check*) untuk memastikan akurasi data.


* 
**Mekanisme Respons & Transmisi Ulang:** Untuk setiap paket perintah kontrol dan kueri yang dikirim oleh *host*, perangkat bawah harus merespons.


* 
**Batas Waktu Transmisi:** Jika *host* tidak menerima respons dalam waktu yang ditentukan, pesan akan dikirim ulang.



## 2. Protokol Lapisan Fisik (Physical Layer)

* 
**Baud rate:** 19200 bps.


* 
**Format Frame:** 1 *start bit*, 8 *data bits*, 1 *stop bit*.


* 
**Parity check:** None (Tidak ada).



## 3. Format Paket Data

Paket data antara *host* dan perangkat bawah mengadopsi format yang seragam. Format tersebut terdiri dari:

* 
**Start of Packet (1 byte):** Selalu bernilai `0x5A`, digunakan untuk menemukan bendera awal paket saat proses *parsing*.


* 
**Packet length (1 byte):** Jumlah byte yang dihitung dari awal paket hingga nilai *checksum*.


* 
**Packet ID (1 byte):** ID yang mengidentifikasi jenis perintah atau paket data.


* 
**Parameter Type (1 byte):** Mengidentifikasi modul parameter yang berbeda. Nilai `0xF1` mendefinisikan Modul Sleeve (*Sleeve module*). Nilai `0xF2` mendefinisikan Mesin Lengkap (*Complete machine*).


* 
**Data segment (Panjang tidak tetap):** Format dan panjang spesifik bergantung pada Packet ID.


* 
**Checksum (2 bytes):** Nilai verifikasi CRC16.



## 4. Parameter Eksekusi Perintah Umum

Untuk perintah kontrol dan kueri secara umum, paket respons akan mengembalikan byte tunggal yang merepresentasikan status eksekusi:

* 
`0x00`: Operasi berhasil dan eksekusi selesai.


* 
`0x01`: Menjalankan perintah (Execute Command).


* 
`0x02`: Operasi sibuk (Operation busy).


* 
`0x03`: Operasi gagal (Operation failed).


* 
`0x04`: Perlindungan Sistem (System Protection).



## 5. Daftar Perintah Komunikasi (Packet ID)

### Manajemen Sistem & Perangkat

* 
**Power-on handshake command (ID: 0x01):** Dikirim oleh *host* untuk memulai komunikasi; perangkat mengembalikan hasil eksekusi umum.


* **Get current version (ID: 0x95):** Mengambil versi perangkat lunak. Perangkat mengembalikan 4 byte yang masing-masing mewakili versi pembaruan perangkat lunak besar, kecil, korektif, dan konstruksi.


* 
**Set device ID (ID: 0x0E):** *Host* mengirimkan 12 byte data untuk mengatur ID perangkat. Perangkat merespons dengan status eksekusi umum.


* 
**Get device ID (ID: 0x0F):** Mengambil ID perangkat. Perangkat mengembalikan 12 byte data ID.


* 
**Ethernet time synchronization (ID: 0x14):** Digunakan untuk sinkronisasi waktu jaringan; mengembalikan status eksekusi umum.


* 
**Reset module (ID: 0x1A):** Mereset modul perangkat; perangkat mengembalikan respons saat memulai dan setelah operasi selesai.


* 
**Sleep module (ID: 0x1B):** Mengalihkan modul ke mode tidur (*hibernation*); mengembalikan status eksekusi.


* 
**Online Upgrade (ID: 0x1F):** *Host* mengirimkan perintah dengan segmen data `0x01` untuk memulai pembaruan modul secara online.


* 
**Start downloading file (ID: 0x61):** Memulai pengunduhan file; mengembalikan hasil eksekusi.


* 
**Language settings (ID: 0x66):** Mengatur bahasa dengan panjang data 1 byte (`0x00` untuk Bahasa Mandarin, `0x01` untuk Bahasa Inggris, `0x02` untuk Bahasa Thailand).


* 
**Switching protocol (ID: 0xFE):** Beralih protokol komunikasi; mengembalikan hasil eksekusi.


* **Disable/enable start button (ID: 0x26):** Menutup atau membuka fungsi tombol perangkat. Segmen data: `0x00` (Buka tombol), `0x01` (Blokir tombol).



### Kontrol Pengukuran Tekanan Darah

* 
**Start measurement (ID: 0x21):** Memulai pengukuran tekanan darah; mengembalikan parameter hasil eksekusi umum.


* 
**Stop measurement (ID: 0x20):** Menghentikan pengukuran secara manual; mengembalikan hasil eksekusi dan parameter penanda deflasi.


* 
**Upload real-time cuff pressure (ID: 0x28):** Perangkat otomatis mengunggah 2 byte data tekanan manset secara *real-time* selama proses pengukuran, dengan *high bit* di depan.


* 
**Turn off/on cuff pressure output (ID: 0x29):** Data segmen `0x00` untuk membuka penerimaan, `0x01` untuk menutup; mengembalikan hasil eksekusi.


* 
**Upload measurement results (ID: 0x22):** Otomatis dikirim setelah pengukuran. Berisi 14 byte: Tekanan Sistolik (2 byte), Diastolik (2 byte), Tekanan rata-rata (2 byte), Denyut Jantung (2 byte), Tahun (2 byte), Bulan (1 byte), Hari (1 byte), Jam (1 byte), Menit (1 byte).



### Penyimpanan & Riwayat Data

* 
**Get measurement count (ID: 0x23):** Meminta jumlah pengukuran; mengembalikan 4 byte nilai hitungan pengukuran (*high bit* pertama).


* 
**Clear measurement count (ID: 0x24):** Menghapus jumlah pengukuran. Perangkat merespons "Execute command", lalu merespons kembali dengan hasil saat operasi selesai.


* 
**Get storage data quantity (ID: 0x2B):** Meminta jumlah data yang tersimpan; mengembalikan 2 byte nilai jumlah memori (*high byte* pertama).


* 
**Get stored data (ID: 0x2C):** Mengambil data riwayat yang tersimpan; mengembalikan format 14 byte yang identik dengan hasil unggahan pengukuran otomatis.


* 
**Clear measurement records (ID: 0x2A):** Menghapus seluruh riwayat pengukuran. Beroperasi asinkron dengan respons awal dan respons final setelah selesai.



### Pengaturan Parameter & Proteksi

* 
**Set/Get cuff protection parameters (ID: 0x59 / 0x5A):** Mengatur dan mengambil parameter perlindungan manset. Data terdiri dari 4 byte: Batas perlindungan tekanan (2 byte) dan batas perlindungan arus (2 byte).


* 
**Set/Get sleeve inflation and deflation parameters (ID: 0x5B / 0x5C):** Mengatur/mengambil parameter manset. Data terdiri dari 4 byte: Batas perlindungan *timeout* inflasi (2 byte) dan deflasi (2 byte).


* 
**Set/Get motor protection parameters (ID: 0x5D / 0x5E):** Batas operasi motor. Data terdiri dari 2 byte yang merepresentasikan batas *timeout* operasi motor.



### Mode Pemeliharaan (Maintenance) & Kalibrasi

* 
**Pump and valve maintenance mode (ID: 0x31):** Memasuki atau keluar mode pemeliharaan; data `0x00` (keluar), `0x01` (masuk).


* 
**Pump and Valve Maintenance (ID: 0x32):** Mengontrol pompa dan katup secara spesifik. Bit 0-6 mendefinisikan saluran (pompa/katup 1 atau 2), bit 7 mendefinisikan status hidup/mati. Contoh nilai: `0x01` (Matikan pompa 1), `0x81` (Nyalakan pompa 1).


* 
**Motor Maintenance (ID: 0x33):** Mengontrol motor; data `0x00` (Lepaskan manset), `0x01` (Tarik manset).


* **Sleeve self-test (ID: 0x34):** Pengujian mandiri manset; `0x00` (Batal), `0x01` (Mulai).


* 
**Start calibration mode (ID: 0x35):** Memulai kalibrasi tekanan dengan mengirimkan 2 byte data tekanan pra-pengisian.


* 
**Set calibration pressure (ID: 0x36):** Mengatur tekanan nyata untuk kalibrasi dengan 2 byte data tekanan.


* 
**Cancel pressure calibration (ID: 0x37):** Membatalkan proses kalibrasi tekanan secara manual.


* 
**Control/Get aging switch & records (ID: 0x62 / 0x63):** Kontrol program menuakan perangkat (aging) dan mengambil data riwayat aging (4 byte nilai).



### Kontrol Modul Printer & Suara

* 
**Voice switch control (ID: 0x11):** Data `0x00` (Matikan suara), `0x01` (Nyalakan suara).


* 
**Printer power control (ID: 0x12):** Data `0x00` (Matikan printer), `0x01` (Buka/Nyalakan printer).


* 
**Print out paper (ID: 0x38):** Memerintahkan printer mengeluarkan kertas; parameter 4 byte menunjukkan langkah pergerakan motor.


* 
**Print paper feed (ID: 0x39):** Memberi makan kertas printer dengan 4 byte parameter motor.


* 
**Print and Cut Paper (ID: 0x3A):** Mencetak dan memotong kertas dengan parameter langkah motor 4 byte.


* 
**Get paper out signal (ID: 0x3B):** Mengecek status kertas; mengembalikan 1 byte (`0x00` = ada kertas, `0x01` = tidak ada kertas).


* 
**Get head-up signal (ID: 0x3C):** Mengecek status kepala printer; mengembalikan 1 byte (`0x00` = tertutup, `0x01` = dinaikkan).


* 
**Test fixed print content (ID: 0x3D):** Menguji cetak dengan konten tetap yang tertanam dalam memori.


* 
**Test print logo image (ID: 0x3F):** Menguji proses pencetakan gambar logo pada struk/kertas.



### Kontrol Waktu Perangkat

* 
**Set Date (ID: 0x51):** Mengatur penanggalan perangkat dengan mengirimkan 7 byte data (Tahun, Bulan, Hari, Jam, Menit, Detik).


* 
**Get Date (ID: 0x52):** Mengambil waktu internal perangkat; mengembalikan 7 byte data (Tahun 2 byte, kemudian masing-masing 1 byte untuk Bulan, Hari, Jam, Menit, dan Detik).



## 6. Kode Kesalahan (Upload Measurement Error Code - ID: 0x25)

Jika terjadi kegagalan pengukuran, perangkat akan secara otomatis mengirimkan pesan ID `0x25` dengan payload data 1 byte yang berisi kode kesalahan spesifik berikut:

* 
`0x00`: Hasil normal.


* 
`0x01`: Manset terlalu longgar atau tidak terhubung.


* 
`0x02`: Terjadi kebocoran pada sirkuit udara atau katup.


* 
`0x03`: Kesalahan tekanan udara, kemungkinan katup tidak terbuka normal.


* 
`0x04`: Sinyal lemah (denyut nadi terlalu lemah atau manset terlalu longgar).


* 
`0x05`: Nilai tekanan darah objek berada di luar jangkauan pengukuran.


* 
`0x06`: Gerakan berlebihan selama pengukuran.


* 
`0x07`: Pengukuran tekanan berlebih (>290 mmHg untuk dewasa, >247 mmHg untuk pediatrik, >145 mmHg untuk neonatal).


* 
`0x08`: Saturasi sinyal, amplitudo terlalu besar karena gerakan.


* 
`0x09`: Waktu pengukuran berakhir (*timeout* melebihi 120s/90s).


* 
`0x0A`: Dihentikan secara manual.


* 
`0x0B`: Kesalahan sistem.


* 
`0x0C`: Kesalahan saat membaca informasi kalibrasi.


* 
`0x0D`: Tidak ada sinyal yang terdeteksi.


* 
`0x0E`: Gelombang denyut nadi tidak teratur.


* 
`0x10`: Perlindungan tekanan berlebih aktif (>290 mmHg).


* 
`0x11`: Kegagalan pada sleeve, kegagalan operasi motor.


* 
`0x12`: Pengukuran gagal dilakukan.


* 
`0x13`: Postur lengan salah atau sakelar siku tidak ditekan.


* 
`0x20`: Komunikasi *handshake* gagal.


* 
`0x23`: Pengukuran tidak dapat dimulai, tidak ada respons saat diinstruksikan.


* 
`0x24`: Tidak bisa mendapatkan hasil pengukuran.


* 
`0x25`: Batas waktu keseluruhan melebihi 180 detik.


* 
`0x26`: Komunikasi awal (*Handshake*) gagal dilakukan secara spesifik.


* 
`0x40`: Kertas pada printer habis.


* 
`0x41`: Penutup *printer* tidak ditutup dengan rapat.


* 
`0x42`: Penutup luar *printer* terbuka.


* 
`0x60`: Saat ini tidak ada rekaman/riwayat pengukuran sama sekali.


* 
`0x64`: Tombol berhenti darurat (*emergency stop*) ditekan.



---
