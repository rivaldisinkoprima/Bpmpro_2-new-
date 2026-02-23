# Dokumentasi Alur Program `new.py` pada BPMPRO_2

File `new.py` adalah skrip yang dirancang untuk membaca, memproses data, serta *mengendalikan* perangkat pengukur tekanan darah (Blood Pressure Monitor) melalui jalur komunikasi Serial (COM Port). Skrip ini memodifikasi versi terdahulunya dengan penambahan fitur interaktif dua-arah (Request-Response).

Berikut adalah penjelasan lengkap mengenai alur kerja dan komponen dari skrip `new.py`.

---

## 1. Konfigurasi Awal (Header)
Bagian ini mengatur spesifikasi koneksi dan identifikasi paket data perangkat:
- **BAUD_RATE**: `19200` – Kecepatan transfer data perangkat.
- **START_BYTE (0x5A)**: Byte penanda awal sebuah paket data yang sah.
- **PARAM_TYPE_BP (0xF2)**: Parameter spesifik yang menunjukkan bahwa paket tersebut adalah data tekanan darah Modul Utama.
- **PACKET_ID_REALTIME (0x28)**: Penanda bahwa paket berisi data tekanan saat ini (sedang memompa).
- **PACKET_ID_RESULT (0x22)**: Penanda bahwa paket berisi hasil akhir pengukuran yang sudah selesai.
- **PACKET_ID_GET_DEVICE_ID (0x0F)** & **SET_DEVICE_ID (0x0E)**: Paket operasional untuk urusan serial number modul.
- **REALTIME_TIMEOUT (5 detik)**: Batas waktu maksimal jika data *realtime* tidak terkirim secara tiba-tiba, maka pembacaan akan diulang (Emergency Stop).

## 2. Deteksi Port Otomatis (`select_port`)
Fungsi `select_port()` bertugas memindai seluruh *COM port* yang aktif di komputer.
1. **Pemindaian**: Skrip mengambil daftar port serial melalui modul `serial.tools.list_ports`.
2. **Penyaringan**: Hanya memilih port serial yang diproduksi oleh **"Silicon Laboratories"** dengan deskripsi periferal USB **"CP210x"**.
3. **Penyematan Identitas**: Untuk setiap port yang sudah disaring, skrip akan menampilkan namanya sebagai **BPMPRO 2**. Jika terdapat perangkat ganda, nama akan ber-inkremen menjadi `BPMPRO 2 (2)`, `BPMPRO 2 (3)`, dan seterusnya.
4. **Interaksi Pengguna**: Setelah mendaftar alat yang berhasil terdeteksi, program meminta user untuk mengetik nomor perangkat yang ingin dihubungkan.

## 3. CRC & Komunikasi (`calc_crc`, dll)
Protokol ini menggunakan sistem **Modbus CRC-16 (Polynomial 0xA001)**.
Setiap paket *command* yang dikirimkan ke mesin melalui perintah `send_..._command(ser)` (seperti *Start*, *Stop*, *Get/Set ID*) disusun dengan struktur:
`[Start Byte] + [Length] + [Command ID] + [Parameter Type] + [Payload Data (Jika Ada)] + [CRC_High] + [CRC_Low]`.
Hasil kalkulasi CRC dirapatkan menggunakan metode **Big Endian**.

## 4. Parsing Payload Data (`parse_packet`)
Fungsi `parse_packet(data_bytes)` bertugas membedah paket byte mentah dari port serial dan mengubahnya menjadi informasi yang bisa dibaca. Penanda paket dibaca dari indeks ke-2 (`packet_id`):
1. **Data Realtime (ID `0x28`)**:
   - Menandai bahwa sistem sedang dalam masa pengukuran (`in_realtime_mode = True`).
   - Ekstrak byte 5 dan 6 sebagai data tekanan *realtime* saat ini. Ditampilkan setiap 0,5 detik sekali.
2. **Device ID (ID `0x0F` & `0x0E`)**:
   - Jika menerima ID `0x0F` *(Get)*, ia akan memenggal 12 byte area data dan menerjemahkannya (*decode*) menjadi huruf ASCII.
   - Jika menerima ID `0x0E` *(Set)*, ia mendekode byte eksekusi respon alat (`0x00` untuk sukses tersimpan, `0x02` untuk sibuk, dst).
3. **Data Hasil Akhir (ID `0x22`)**:
   - Pengukuran selesai (`in_realtime_mode = False`).
   - Ekstrak berbagai nilai pengukuran historis dari struktur byte:
     - Tekanan Sistolik (mmHg)
     - Tekanan Diastolik (mmHg)
     - Mean Arterial Pressure (mmHg)
     - Detak Jantung / *Heart Rate* (bpm)
     - Timestamp / Waktu Pengukuran (Tahun, Bulan, Hari, Jam, Menit).
   - Mengembalikan hasil ekstraksi tersebut dalam bentuk teks *(string)* terformat dengan rapi.

## 5. Sistem Pembacaan Serial (`read_serial_loop`)
Ini adalah fungsi utama (loop tak terbatas) yang terus berjalan untuk memantau konektivitas:
1. **Koneksi Port**: Mancoba menghubungkan dengan *Port* yang dipilih sebelumnya.
2. **Kendali Antarmuka**: Program meminta pengguna untuk memilih menu eksekusi:
   - `[1]` untuk mengirim *Start Measurement*
   - `[2]` untuk mengirim *Stop Measurement*
   - `[3]` untuk meminta info *Get Device ID*
   - `[4]` untuk mengatur *Set Device ID*
   Setelah opsi dipilih, port dieksekusi dan program lanjut membuka gerbang *Listener*.
3. **Timeout Check (`check_realtime_timeout`)**: Saat sedang membaca data *realtime*, jika terhenti >5 detik, sistem melakukan **Emergency Stop**.
3. **Menyusun Packet Byte**: 
   - Fungsi `find_start_byte()` akan membaca byte satu per satu hingga menemukan header `0x5A`.
   - Modul membaca *panjang paket* (`length`) di byte selanjutnya, lalu merangkai sisanya (`full_packet`).
5. **Eksekusi Penampilan Data**: Paket diserahkan ke fungsi `parse_packet()`. 
   - Komputer akan mencetaknya ke terminal. Apabila responnya adalah seputar status **"DEVICE ID"**, terminal hanya beristirahat 1 detik lalu kembali ke opsi Antarmuka. Namun, jika ia adalah **"HASIL PENGUKURAN"** (pengukuran selesai / lengan kempes), terminal mengambil jeda agak panjang (5 detik) untuk mode istirahat pasien.

## 6. Eksekusi Utama (`__main__`)
Saat skrip dijalankan, ia mencetak pesan *header* ke konsol. Di tahap ini, fungsi deteksi otomatis alat dipanggil dan akan mengeksekusi `read_serial_loop(selected_port)` jika user telah memilih ID port yang valid. Jika pengguna memasukkan input nol atau tidak memilih apa-apa, maka program otomatis dihentikan dengan rapi.

---

Metode standar CRC-16 pada sistem BPM ini (Modbus 0xA001) ditransmisikan dua arah, baik untuk pembacaan maupun penulisan, tetapi harus ekstra waspada terhadap urutan **Endianness**. Respons alat pada *Realtime* / *Result* biasanya dapat dievaluasi menggunakan *Little Endian*, sementara pengiriman utusan *Command* ke Mikrokontroler (mis. Start Measurement ID `0x21`) terkonfirmasi wajib menggunakan rentetan **Big Endian**.

Contoh Struktur Payload Realtime (`5A0828F200306745`):
- `5A` ➔ Start Byte
- `08` ➔ Packet Length (Panjang paket total adalah 8 byte)
- `28` ➔ Packet ID (Upload real-time cuff pressure)
- `F2` ➔ Parameter Modul Utama
- `00 30` ➔ Payload Data (Tekanan 48 mmHg dalam hexadecimal `0x0030`)
- `67 45` ➔ Ekstensi CRC-16.

## Kesimpulan Alur (Flowchart Singkat)
1. **Scan & Select**: Sistem melacak USB yang memuat nama pabrikan khusus (Silicon Laboratories) dan meminta pengguna memilih perangkat (BPMPRO 2).
2. **Action Prompt**: Terminal menyajikan antarmuka *Input Menu* [1-4] untuk mengatur atau memulai interaksi dengan mesin pengukur. Komputer mentransmisikan bit-bit yang ditentukan.
3. **Wait/Standby**: Buka *Listening stream* COM Port, lalu baca satu-persatu respon alat memburu header kompas `0x5A`.
4. **Collect**: Baca seluruh panjang paket tersebut, pastikan integritasnya (opsional), buang ke *parser*.
5. **Analyze**: 
   - Jika data terdeteksi `0x28` -> Print log ketegangan pompa *realtime*.
   - Jika data masuk jenis info/pengaturan (`0x0E`/`0x0F`) -> Tampilkan -> Kembali cepat ke Start.
   - Jika terjadi masalah (Berhenti baca >5 Detik) -> Emergency Stop & Reset.
   - Jika data terdeteksi `0x22` -> Print Hasil Total (Sistolik, Diastolik, Heart Rate), lalu tunggu 5 detik.
6. **Repeat**: Tutup sesi dan kembali ke tahapan nomor 2 untuk pasien / pengujian berikutnya.
