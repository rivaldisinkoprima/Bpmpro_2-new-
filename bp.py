import serial
import time
from datetime import datetime
import serial.tools.list_ports
import threading
import queue

# ================= KONFIGURASI =================

START_BYTE = 0x5A
PARAM_TYPE_BP = 0xF2
PACKET_ID_REALTIME = 0x28
PACKET_ID_RESULT = 0x22
BAUD_RATE = 19200
REALTIME_TIMEOUT = 5

# ================= VARIABEL GLOBAL =================

port_queue = queue.Queue()
restart_detection = threading.Event()
in_realtime_mode = False
last_realtime_data = 0

# ================= DETEKSI PORT =================

def detect_port(port_name, result_queue, stop_event):
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=1)
        print(f"Mencoba port: {port_name}")
        start_time = time.time()

        while time.time() - start_time < 2 and not stop_event.is_set():
            data = ser.read(1)
            if data and data[0] == START_BYTE:
                print(f"✔ Port valid ditemukan: {port_name}")
                result_queue.put(ser)
                stop_event.set()
                return

        ser.close()
    except serial.SerialException:
        pass


def select_serial_port():
    while True:
        ports = list(serial.tools.list_ports.comports())

        if not ports:
            print("Tidak ada port ditemukan. Coba lagi 1 detik...")
            time.sleep(1)
            continue

        stop_event = threading.Event()

        while not port_queue.empty():
            port_queue.get_nowait()

        threads = []
        for port in ports:
            t = threading.Thread(
                target=detect_port,
                args=(port.device, port_queue, stop_event),
                daemon=True
            )
            threads.append(t)
            t.start()

        start_time = time.time()
        while time.time() - start_time < 3 and not stop_event.is_set():
            time.sleep(0.1)

        stop_event.set()

        try:
            return port_queue.get_nowait()
        except queue.Empty:
            print("Tidak ada port valid. Ulangi deteksi...")
            time.sleep(1)

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

            restart_detection.set()

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

def find_start_byte(ser):
    while True:
        try:
            b = ser.read(1)
            if not b:
                return None
            if b[0] == START_BYTE:
                return b
        except:
            return None


def check_realtime_timeout():
    global in_realtime_mode

    if in_realtime_mode and (time.time() - last_realtime_data > REALTIME_TIMEOUT):
        print("❌ EMERGENCY STOP (5 detik tanpa data)")
        in_realtime_mode = False
        restart_detection.set()
        return True
    return False


def read_serial_data(ser):
    global last_realtime_data

    print(f"\nTerhubung ke {ser.port} ({BAUD_RATE} bps)")
    restart_detection.clear()
    last_realtime_data = time.time()

    while not restart_detection.is_set():

        if check_realtime_timeout():
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

            if restart_detection.is_set():
                print("Menunggu 5 detik sebelum restart...\n")
                time.sleep(5)
                break

    return True

# ================= LOOP UTAMA =================

def main():
    print("=== BP USB MONITOR MODE ===")
    print("Emergency stop jika 5 detik tanpa data realtime\n")

    while True:
        print("\n--- Deteksi Port Serial ---")
        ser = select_serial_port()

        if not ser:
            time.sleep(2)
            continue

        read_serial_data(ser)

        if ser.is_open:
            ser.close()
            print("Port ditutup.")

if __name__ == "__main__":
    main()