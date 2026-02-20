import serial
import serial.tools.list_ports
import time
from datetime import datetime

# ================= KONFIGURASI =================

BAUD_RATE = 19200

START_BYTE = 0x5A
PARAM_TYPE_BP = 0xF2
PACKET_ID_REALTIME = 0x28
PACKET_ID_RESULT = 0x22
PACKET_ID_GET_DEVICE_ID = 0x0F
PACKET_ID_SET_DEVICE_ID = 0x0E

REALTIME_TIMEOUT = 5

# ================= VARIABEL GLOBAL =================

in_realtime_mode = False
last_realtime_data = 0


# ================= CRC & KOMUNIKASI =================

def calc_crc(data_bytes):
    """
    Menghitung CRC16 Modbus (Polynomial 0xA001) untuk verifikasi paket.
    """
    crc = 0xFFFF
    for byte in data_bytes:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    # Mengembalikan dalam byte-order big-endian (High-byte, Low-byte)
    return crc.to_bytes(2, byteorder='big')

def send_start_command(ser):
    """
    Mengirimkan instruksi Start Measurement (ID: 0x21) ke perangkat.
    Pembentukan paket:
    - 0x5A (Start Byte)
    - 0x06 (Packet Length)
    - 0x21 (Packet ID: Start Measurement)
    - 0xF2 (Parameter Type: Complete Machine)
    - CRC16 (2 bytes)
    """
    packet_id = 0x21
    param_type = PARAM_TYPE_BP
    packet_length = 0x06
    
    payload = bytes([START_BYTE, packet_length, packet_id, param_type])
    crc = calc_crc(payload)
    
    full_packet = payload + crc
    ser.write(full_packet)
    print(f"📡 Perintah Start Measurement terkirim! (Paket: {full_packet.hex().upper()})")

def send_stop_command(ser):
    """
    Mengirimkan instruksi Stop Measurement (ID: 0x20) ke perangkat.
    """
    packet_id = 0x20
    param_type = PARAM_TYPE_BP
    packet_length = 0x06
    
    payload = bytes([START_BYTE, packet_length, packet_id, param_type])
    crc = calc_crc(payload)
    
    full_packet = payload + crc
    ser.write(full_packet)
    print(f"\n🛑 Perintah Stop Measurement terkirim! (Paket: {full_packet.hex().upper()})")

def send_get_device_id_command(ser):
    """
    Mengirimkan instruksi Get Device ID (ID: 0x0F) ke perangkat.
    """
    packet_id = PACKET_ID_GET_DEVICE_ID
    param_type = PARAM_TYPE_BP
    packet_length = 0x06
    
    payload = bytes([START_BYTE, packet_length, packet_id, param_type])
    crc = calc_crc(payload)
    
    full_packet = payload + crc
    ser.write(full_packet)
    print(f"\n🔍 Perintah Get Device ID terkirim! (Paket: {full_packet.hex().upper()})")

def send_set_device_id_command(ser, new_id: str):
    """
    Mengirimkan instruksi Set Device ID (ID: 0x0E) ke perangkat.
    Device ID harus terdiri dari maksimal 12 karakter ASCII.
    """
    # Memotong atau mendempul (padding) agar tepat 12 byte
    new_id_bytes = new_id.encode('ascii', errors='ignore')[:12].ljust(12, b'\x00')
    
    packet_id = PACKET_ID_SET_DEVICE_ID
    param_type = PARAM_TYPE_BP
    packet_length = len(new_id_bytes) + 6 # Start(1) + Len(1) + ID(1) + Param(1) + Data(12) + CRC(2)
    
    payload = bytes([START_BYTE, packet_length, packet_id, param_type]) + new_id_bytes
    crc = calc_crc(payload)
    
    full_packet = payload + crc
    ser.write(full_packet)
    print(f"\n✍️ Perintah Set Device ID '{new_id_bytes.decode('ascii').strip(chr(0))}' terkirim! (Paket: {full_packet.hex().upper()})")


# ================= PARSE PAKET =================

def parse_packet(data_bytes):
    global in_realtime_mode, last_realtime_data

    try:
        if data_bytes[0] != START_BYTE:
            return None

        length = data_bytes[1]
        packet_id = data_bytes[2]
        param_type = data_bytes[3]

        if param_type != PARAM_TYPE_BP:
            return None

        # ===== REALTIME =====
        if packet_id == PACKET_ID_REALTIME and length >= 0x08:
            in_realtime_mode = True
            
            # Debug Hex
            print(f"[DEBUG REALTIME] {data_bytes.hex().upper()}")

            pressure = int.from_bytes(data_bytes[4:6], 'big')

            now = time.time()
            if now - last_realtime_data >= 0.5:
                last_realtime_data = now
                return f"Realtime Pressure: {pressure} mmHg"

        # ===== GET DEVICE ID =====
        elif packet_id == PACKET_ID_GET_DEVICE_ID:
            in_realtime_mode = False
            print(f"\n[DEBUG GET ID] {data_bytes.hex().upper()}")
            device_id_bytes = data_bytes[4:-2]
            try:
                device_id_str = device_id_bytes.decode('ascii', errors='replace').strip('\x00')
            except:
                device_id_str = "Error Decoding"
                
            return (
                "\n=== GET DEVICE ID ===\n"
                f"Raw Hex : {device_id_bytes.hex().upper()}\n"
                f"ASCII   : {device_id_str}\n"
                "=====================\n"
            )
            
        # ===== SET DEVICE ID (EXECUTION RESULT) =====
        elif packet_id == PACKET_ID_SET_DEVICE_ID:
            in_realtime_mode = False
            print(f"\n[DEBUG SET ID] {data_bytes.hex().upper()}")
            
            # Segmen data eksekusi umum (1 byte setelah param_type)
            exec_status = data_bytes[4] if len(data_bytes) > 6 else 0xFF
            
            status_map = {
                0x00: "✅ Berhasil Disimpan!",
                0x01: "Memproses Command...",
                0x02: "Perangkat Sibuk",
                0x03: "❌ Gagal Menyimpan",
                0x04: "System Protection",
            }
            status_text = status_map.get(exec_status, f"Kode Tak Dikenal: {exec_status}")
            
            return (
                "\n=== HASIL SET DEVICE ID ===\n"
                f"Status: {status_text}\n"
                "===========================\n"
            )

        # ===== RESULT =====
        elif packet_id == PACKET_ID_RESULT and length >= 0x14:
            in_realtime_mode = False
            
            # Debug Hex
            print(f"\n[DEBUG RESULT] {data_bytes.hex().upper()}")

            systolic = int.from_bytes(data_bytes[4:6], 'big')
            diastolic = int.from_bytes(data_bytes[6:8], 'big')
            mean = int.from_bytes(data_bytes[8:10], 'big')
            heart_rate = int.from_bytes(data_bytes[10:12], 'big')

            year = int.from_bytes(data_bytes[12:14], 'big')
            month = data_bytes[14]
            day = data_bytes[15]
            hour = data_bytes[16]
            minute = data_bytes[17]

            try:
                measurement_time = datetime(year, month, day, hour, minute)
            except:
                measurement_time = datetime.now()

            return (
                "\n=== HASIL PENGUKURAN ===\n"
                f"Sistolik     : {systolic} mmHg\n"
                f"Diastolik    : {diastolic} mmHg\n"
                f"Mean         : {mean} mmHg\n"
                f"Heart Rate   : {heart_rate} bpm\n"
                f"Waktu        : {measurement_time}\n"
                "=========================\n"
            )

    except Exception as e:
        print("Error parsing:", e)

    return None


# ================= SERIAL READER =================

def select_port():
    print("Mencari perangkat Silicon Labs CP210x...")
    ports = serial.tools.list_ports.comports()
    valid_ports = []
    
    for p in ports:
        manufacturer = p.manufacturer if p.manufacturer else ""
        description = p.description if p.description else ""
        
        if "Silicon Laboratories" in manufacturer and "CP210x" in description:
            valid_ports.append(p)
            
    if not valid_ports:
        print("❌ Tidak ada perangkat yang cocok (Silicon Labs CP210x) ditemukan.")
        return None
        
    print("\nPerangkat ditemukan:")
    for idx, p in enumerate(valid_ports):
        alias_name = "BPMPRO 2" if idx == 0 else f"BPMPRO 2 ({idx + 1})"
        print(f"[{idx + 1}] {p.device} - {alias_name}")
        
    while True:
        try:
            choice = input("\nPilih nomor perangkat (atau 0 untuk keluar): ")
            choice_idx = int(choice)
            if choice_idx == 0:
                return None
            if 1 <= choice_idx <= len(valid_ports):
                return valid_ports[choice_idx - 1].device
            else:
                print("⚠️ Pilihan tidak valid.")
        except ValueError:
            print("⚠️ Masukkan angka yang valid.")


def find_start_byte(ser):
    while True:
        byte = ser.read(1)
        if not byte:
            return None
        if byte[0] == START_BYTE:
            return byte


def check_realtime_timeout():
    global in_realtime_mode

    if in_realtime_mode and (time.time() - last_realtime_data > REALTIME_TIMEOUT):
        print("❌ EMERGENCY STOP (5 detik tanpa data)")
        in_realtime_mode = False
        return True
    return False


def read_serial_loop(port_name):
    global last_realtime_data

    while True:
        try:
            print(f"\nMencoba koneksi ke {port_name}...")
            ser = serial.Serial(port_name, BAUD_RATE, timeout=1)
            print(f"✔ Terhubung ke {port_name}")

            # Fitur memicu perintah secara manual
            while True:
                user_input = input('\nMenu: [1] Start, [2] Stop, [3] Get ID, [4] Set ID.\nPilih Angka: ')
                if user_input.strip() == '1':
                    ser.reset_input_buffer()
                    send_start_command(ser)
                    break
                elif user_input.strip() == '2':
                    ser.reset_input_buffer()
                    send_stop_command(ser)
                    break
                elif user_input.strip() == '3':
                    ser.reset_input_buffer()
                    send_get_device_id_command(ser)
                    break
                elif user_input.strip() == '4':
                    new_id = input("Masukkan ID baru (maks 12 karakter): ")
                    ser.reset_input_buffer()
                    send_set_device_id_command(ser, new_id)
                    break
                else:
                    print("⚠️ Input tidak sesuai.")

            last_realtime_data = time.time()

            while True:

                if check_realtime_timeout():
                    print("Restarting pembacaan...\n")
                    break

                start = find_start_byte(ser)
                if not start:
                    continue

                length_byte = ser.read(1)
                if not length_byte:
                    continue

                length = length_byte[0]
                remaining = ser.read(length - 2)

                if len(remaining) != length - 2:
                    continue

                full_packet = start + length_byte + remaining
                result = parse_packet(full_packet)

                if result:
                    print(result)

                    # Jika hasil final → tunggu 5 detik lalu restart loop
                    if "HASIL PENGUKURAN" in result:
                        print("Menunggu 5 detik sebelum pengukuran berikutnya...\n")
                        time.sleep(5)
                        break
                        
                    # Jika itu seputar urusan Device ID → tunggu sebentar lalu langsung ke menu awal
                    if "DEVICE ID" in result:
                        time.sleep(1)
                        break

            ser.close()
            print("Port ditutup.")

        except serial.SerialException:
            print(f"❌ Gagal membuka {port_name}. Pastikan alat terhubung.")
            time.sleep(3)

        except KeyboardInterrupt:
            print("\nProgram dihentikan oleh user.")
            break


# ================= MAIN =================

if __name__ == "__main__":
    print("=== BP MONITOR ===")
    print("Emergency stop jika 5 detik tanpa data realtime\n")
    
    selected_port = select_port()
    if selected_port:
        read_serial_loop(selected_port)
    else:
        print("Program dihentikan.")