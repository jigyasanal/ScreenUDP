import socket
import struct
import time
import io
from PIL import Image
import mss

def capture_screen(resize_to=(800, 600)):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = sct.grab(monitor)
        img = Image.frombytes('RGB', img.size, img.rgb)
        img = img.resize(resize_to)
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=30, optimize=True)
        return buffer.getvalue()

def start_udp_server(host='0.0.0.0', port=33060):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind((host, port))
    print(f"[SERVER] UDP server listening on {host}:{port}")

    # Wait for client to send handshake
    print("[SERVER] Waiting for client connection...")
    data, client_addr = udp_socket.recvfrom(1024)
    print(f"[SERVER] Client connected from {client_addr}")

    try:
        while True:
            screen_data = capture_screen()
            size = struct.pack('!I', len(screen_data))  # 4 bytes, network byte order
            udp_socket.sendto(size + screen_data, client_addr)
            time.sleep(1/30)  # Target ~30 FPS
    except Exception as e:
        print(f"[SERVER ERROR] {e}")

if __name__ == "__main__":
    start_udp_server()
