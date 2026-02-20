# ==========================================
# CRC16 MODBUS VALIDATOR (AUTO ENDIAN CHECK)
# ==========================================

def crc16_modbus(data: bytes):
    """
    CRC-16 MODBUS
    Polynomial : 0xA001
    Init value : 0xFFFF
    """
    crc = 0xFFFF

    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1

    return crc & 0xFFFF


def validate_crc(hex_string: str):
    try:
        # Bersihkan input
        hex_string = hex_string.replace(" ", "").strip()

        # Validasi panjang
        if len(hex_string) < 6:
            print("❌ Data terlalu pendek")
            return

        # Konversi HEX ke bytes
        packet = bytes.fromhex(hex_string)

        if len(packet) < 3:
            print("❌ Paket tidak valid")
            return

        # Pisahkan data & CRC
        data = packet[:-2]
        crc_bytes = packet[-2:]

        # Interpretasi CRC diterima
        received_little = int.from_bytes(crc_bytes, byteorder="little")
        received_big = int.from_bytes(crc_bytes, byteorder="big")

        # Hitung CRC
        calculated_crc = crc16_modbus(data)

        print("\n========== HASIL VALIDASI ==========")
        print("HEX Input        :", hex_string.upper())
        print("Data tanpa CRC   :", data.hex().upper())
        print("CRC dihitung     :", format(calculated_crc, "04X"))
        print("CRC diterima LE  :", format(received_little, "04X"))
        print("CRC diterima BE  :", format(received_big, "04X"))

        if calculated_crc == received_little:
            print("✅ CRC VALID (Little Endian)")
        elif calculated_crc == received_big:
            print("✅ CRC VALID (Big Endian)")
        else:
            print("❌ CRC TIDAK VALID")

        print("====================================\n")

    except ValueError:
        print("❌ Format HEX tidak valid (pastikan hanya karakter 0-9 A-F)")


if __name__ == "__main__":
    print("=== CRC16 MODBUS VALIDATOR ===")
    print("Masukkan HEX lengkap (termasuk 2 byte CRC di belakang)")
    print("Contoh: 5A0828F200695D85")
    print("Ketik 'exit' untuk keluar\n")

    while True:
        user_input = input("Input HEX : ")

        if user_input.lower() == "exit":
            print("Program selesai.")
            break

        validate_crc(user_input)