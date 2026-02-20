import serial.tools.list_ports

def scan_ports():
    ports = list(serial.tools.list_ports.comports())

    if not ports:
        print("Tidak ada COM port yang terdeteksi.")
        return None

    print("\nDaftar COM Port Terdeteksi:")
    print("-" * 40)

    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")

    return ports


def show_port_detail(port):
    print("\nDetail Port:")
    print("-" * 40)
    print(f"Device        : {port.device}")
    print(f"Name          : {port.name}")
    print(f"Description   : {port.description}")
    print(f"HWID          : {port.hwid}")
    print(f"VID           : {hex(port.vid) if port.vid else 'N/A'}")
    print(f"PID           : {hex(port.pid) if port.pid else 'N/A'}")
    print(f"Serial Number : {port.serial_number}")
    print(f"Manufacturer  : {port.manufacturer}")
    print(f"Product       : {port.product}")
    print(f"Interface     : {port.interface}")


def main():
    ports = scan_ports()

    if not ports:
        return

    try:
        choice = int(input("\nPilih nomor port yang ingin dicek: "))
        if 1 <= choice <= len(ports):
            selected_port = ports[choice - 1]
            show_port_detail(selected_port)
        else:
            print("Nomor tidak valid.")
    except ValueError:
        print("Input harus berupa angka.")


if __name__ == "__main__":
    main()