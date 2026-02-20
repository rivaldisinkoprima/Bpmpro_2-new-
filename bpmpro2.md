# Dokumentasi Alur Program `manual.py` pada BPMPRO_2

File `manual.py` adalah skrip yang dirancang untuk membaca dan memproses data dari perangkat pengukur tekanan darah (Blood Pressure Monitor) melalui koneksi Serial (COM Port). Skrip ini membedakan antara data pengukuran *realtime* (saat manset masih memompa) dan data *hasil akhir*.

Berikut adalah penjelasan lengkap mengenai alur kerja dan komponen dari skrip `manual.py`.

---

## 1. Konfigurasi Awal (Header)
Bagian ini mengatur spesifikasi koneksi dan identifikasi paket data perangkat:
- **BAUD_RATE**: `19200` – Kecepatan transfer data perangkat.
- **START_BYTE (0x5A)**: Byte penanda awal sebuah paket data yang sah.
- **PARAM_TYPE_BP (0xF2)**: Parameter spesifik yang menunjukkan bahwa paket tersebut adalah data tekanan darah.
- **PACKET_ID_REALTIME (0x28)**: Penanda bahwa paket berisi data tekanan saat ini (sedang memompa).
- **PACKET_ID_RESULT (0x22)**: Penanda bahwa paket berisi hasil akhir pengukuran yang sudah selesai.
- **REALTIME_TIMEOUT (5 detik)**: Batas waktu maksimal jika data *realtime* tidak terkirim secara tiba-tiba, maka pembacaan akan diulang (Emergency Stop).

## 2. Deteksi Port Otomatis (`select_port`)
Fungsi `select_port()` bertugas memindai seluruh *COM port* yang aktif di komputer.
1. **Pemindaian**: Skrip mengambil daftar port serial melalui modul `serial.tools.list_ports`.
2. **Penyaringan**: Hanya memilih port serial yang diproduksi oleh **"Silicon Laboratories"** dengan deskripsi periferal USB **"CP210x"**.
3. **Penyematan Identitas**: Untuk setiap port yang sudah disaring, skrip akan menampilkan namanya sebagai **BPMPRO 2**. Jika terdapat perangkat ganda, nama akan ber-inkremen menjadi `BPMPRO 2 (2)`, `BPMPRO 2 (3)`, dan seterusnya.
4. **Interaksi Pengguna**: Setelah mendaftar alat yang berhasil terdeteksi, program meminta user untuk mengetik nomor perangkat yang ingin dihubungkan.

## 3. Parsing Payload Data (`parse_packet`)
Fungsi `parse_packet(data_bytes)` bertugas membedah paket byte mentah dari port serial dan mengubahnya menjadi informasi yang bisa dibaca.
1. **Validasi Paket**: Memeriksa apakah byte pertama adalah `0x5A` (Start Byte) dan Byte ke-4 adalah `0xF2` (Menandakan modul BP).
2. **Data Realtime (ID `0x28`)**:
   - Skrip menandai bahwa sistem sedang dalam masa pengukuran (`in_realtime_mode = True`).
   - Ekstrak byte ke 5 dan 6 sebagai data tekanan *realtime* saat ini.
   - Untuk mencegah spam di terminal, data *realtime* hanya dikembalikan/ditampilkan setiap 0,5 detik sekali.
3. **Data Hasil Akhir (ID `0x22`)**:
   - Pengukuran selesai (`in_realtime_mode = False`).
   - Ekstrak berbagai nilai pengukuran historis dari struktur byte:
     - Tekanan Sistolik (mmHg)
     - Tekanan Diastolik (mmHg)
     - Mean Arterial Pressure (mmHg)
     - Detak Jantung / *Heart Rate* (bpm)
     - Timestamp / Waktu Pengukuran (Tahun, Bulan, Hari, Jam, Menit).
   - Mengembalikan hasil ekstraksi tersebut dalam bentuk teks *(string)* terformat dengan rapi.

## 4. Sistem Pembacaan Serial (`read_serial_loop`)
Ini adalah fungsi utama (loop tak terbatas) yang terus berjalan untuk memantau konektivitas:
1. **Koneksi Port**: Mencoba menghubungkan dengan *Port* yang dipilih sebelumnya. Jika gagal (misalnya alat tiba-tiba dicabut), ia akan memberi peringatan dan mencoba menghubungkan ulang setiap 3 detik.
2. **Timeout Check (`check_realtime_timeout`)**: Saat sedang membaca data *realtime*, jika kabel tiba-tiba terputus atau alat terhenti dan tidak mengirim data selama lebih dari 5 detik, sistem akan memutus siklus dan mencetak pesan **Emergency Stop**, kemudian melakukan restart pembacaan.
3. **Menyusun Packet Byte**: 
   - Fungsi `find_start_byte()` akan membaca byte satu per satu hingga menemukan `0x5A`.
   - Setelah awalan ketemu, ia membaca byte kedua sebagai *panjang paket* (`length`).
   - Sisa byte dibaca sesuai panjang paket tersebut agar dapat disusun menjadi satu array (`full_packet`).
4. **Eksekusi Penampilan Data**: Paket diserahkan ke fungsi `parse_packet()`. 
   - Jika alat mengirimkan laporan *realtime*, angka tekanan langsung di print ke layar terminal.
   - Jika alat mengirimkan teks **"HASIL PENGUKURAN"** (Artinya manset telah kempes dan hasil siap didokumentasikan), komputer akan mencetaknya ke terminal, menunggu jeda istirahat selama 5 detik, kemudian mengulang koneksi (*restart loop*) untuk bersiap membaca pasien pengukuran berikutnya.

## 5. Eksekusi Utama (`__main__`)
Saat skrip dijalankan, ia mencetak pesan *header* ke konsol. Di tahap ini, fungsi deteksi otomatis alat dipanggil dan akan mengeksekusi `read_serial_loop(selected_port)` jika user telah memilih ID port yang valid. Jika pengguna memasukkan input nol atau tidak memilih apa-apa, maka program otomatis dihentikan dengan rapi.

---

## Kesimpulan Alur (Flowchart Singkat)
1. **Scan & Select**: Sistem melacak USB yang memuat nama pabrikan khusus (Silicon Laboratories) dan meminta pengguna memilih perangkat (BPMPRO 2).
2. **Wait/Standby**: Buka `COM Port` yang dipilih, lalu baca satu-persatu byte hingga menemukan header `0x5A`.
2. **Collect**: Baca seluruh panjang paket tersebut, kirim ke `parse_packet`.
3. **Analyze**: 
   - Jika data terdeteksi `0x28` -> Print log tekanan pompa secara *realtime* (Maksimal 2x sedetik).
   - Jika terjadi masalah (Berhenti baca >5 Detik) -> Emergency Stop & Reset.
   - Jika data terdeteksi `0x22` -> Print Hasil Total (Sistolik, Diastolik, Heart Rate), lalu tunggu 5 detik.
4. **Repeat**: Tutup sesi dan kembali ke tahapan nomor 1 untuk sesi berikutnya.
