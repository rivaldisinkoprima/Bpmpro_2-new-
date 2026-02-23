# Panduan Kalibrasi Tekanan via Software (`new.py`)

Dokumen ini menguraikan prosedur langkah demi langkah untuk melakukan instruksi kalibrasi tekanan pada perangkat pengukur tekanan darah murni melalui skrip antarmuka `new.py`.

Kalibrasi dilakukan dengan menembakkan urutan perintah (*Command ID*) spesifik ke mikrokontroler perangkat agar angka pembacaan sensor sinkron dengan tekanan nyata (aktual).

---

## Tahapan Eksekusi Kalibrasi

Saat Anda menjalankan program `new.py` dan telah terhubung ke port perangkat (BPM PRO 2), ikuti urutan eksekusi menu berikut:

### Langkah 1: Memulai Pompa Kalibrasi (ID: `0x35`)
Pilih menu angka **`[5]`** (Start Kalibrasi) pada terminal Anda. 
- Komputer akan meminta Anda memasukkan **Target Tekanan Pompa Awal (Pre-fill)** dalam satuan `mmHg`.
- Ketik angka target (contoh: `100` atau `150`) lalu tekan *Enter*.
- Skrip akan menerjemahkan angka ini ke dalam byte hex dan menembakkannya bersama **Packet ID `0x35`**.
- Mesin BPM akan merespons instruksi ini dengan menyalakan pompa udara hingga pembacaan sensor internalnya mencapai nilai yang Anda minta, setelah itu ia akan menahan tekanan tersebut.
- Tunggu hingga terminal Python mencetak balasan **Status: ✅ Operasi Berhasil Diselesaikan! (`0x00`)** dari alat.

### Langkah 2: Menetapkan Nilai Koreksi Aktual (ID: `0x36`)
Setelah kondisi tekanan udara ditahan oleh alat, Anda harus memberitahu alat berapa tekanan nyata/aktual saat ini (biasanya dilihat melalui manometer referensi eksternal).
- Pilih menu angka **`[6]`** (Set Tkn Aktual) pada terminal.
- Program akan meminta Anda memasukkan **Tekanan Aktual (Nyata)**.
- Ketik angka tekanan sebenarnya yang diukur (contoh: jika target `150` tapi nyatanya `147`, ketik `147`) lalu tekan *Enter*.
- Skrip akan menyusun perintah offset ini bersama **Packet ID `0x36`** dan mengirimkannya ke perangkat.
- Papan mikrokontroler BPM akan mencatat selisih tersebut ke dalam memorinya sebagai faktor kalibrasi sensor.
- Terminal akan kembali memunculkan **Status: ✅ Operasi Berhasil Diselesaikan! (`0x00`)** jika nilai referensi kalibrasi sukses disimpan.

*(Catatan: Langkah 1 dan 2 dapat diulang di beberapa titik tekanan yang berbeda — misalnya di 50, 100, 150, 200, dan 250 mmHg — untuk kalibrasi multi-titik yang lebih akurat sesuai desain mesin).*

### Langkah 3: Mengakhiri Mode Kalibrasi (ID: `0x37`)
Setelah seluruh titik tekanan berhasil dikalibrasi (atau jika Anda ingin membatalkan proses di tengah jalan), perangkat harus dipaksa keluar dari mode pemeliharaan/kalibrasi.
- Pilih menu angka **`[7]`** (Cancel Kalibrasi) pada terminal.
- Skrip akan menembakkan instruksi darurat secara langsung menggunakan **Packet ID `0x37`** tanpa memerlukan parameter nilai tambahan.
- Katup buang (exhaust valve) pada mesin BPM akan terbuka secara otomatis, mengosongkan seluruh udara yang tersisa di sistem.
- Mode kalibrasi pada perangkat telah sepenuhnya dibatalkan/diakhiri.

Setelah proses `[7]` selesai, instrumen Anda telah kembali ke mode *Standby* normal dan siap digunakan untuk membaca tekanan darah biasa menggunakan menu *Start Measurement* `[1]`.
