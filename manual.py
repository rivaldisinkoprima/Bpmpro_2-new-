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

REALTIME_TIMEOUT = 5

# ================= VARIABEL GLOBAL =================

in_realtime_mode = False
last_realtime_data = 0


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

            pressure = int.from_bytes(data_bytes[4:6], 'big')

            now = time.time()
            if now - last_realtime_data >= 0.5:
                last_realtime_data = now
                return f"Realtime Pressure: {pressure} mmHg"

        # ===== RESULT =====
        elif packet_id == PACKET_ID_RESULT and length >= 0x14:
            in_realtime_mode = False

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