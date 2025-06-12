import socket
import time
import cv2
import numpy as np
import mss

CHUNK_SIZE = 60000  # UDP safe size
SERVER_IP = '0.0.0.0'
PORT = 33060

def capture_frame(resize_to=(800, 600), jpeg_quality=35):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = np.array(sct.grab(monitor))

        # Remove alpha channel if present (mss returns BGRA)
        if img.shape[2] == 4:
            img = img[:, :, :3]

        img = cv2.resize(img, resize_to)

        # JPEG encode with quality
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
        ret, buffer = cv2.imencode('.jpg', img, encode_params)
        return buffer.tobytes() if ret else None

def start_udp_server(resize_to=(640, 360), jpeg_quality=35):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
    sock.bind((SERVER_IP, PORT))
    print("[SERVER] Listening for client...")

    # Handshake
    data, client_addr = sock.recvfrom(1024)
    print(f"[SERVER] Client connected from {client_addr}")

    try:
        while True:
            frame = capture_frame(resize_to, jpeg_quality)
            if not frame:
                continue

            total_size = len(frame)
            num_chunks = (total_size // CHUNK_SIZE) + 1

            # Send header
            sock.sendto(f"{total_size},{num_chunks}".encode(), client_addr)

            # Send chunks
            for i in range(num_chunks):
                chunk = frame[i * CHUNK_SIZE : (i + 1) * CHUNK_SIZE]
                sock.sendto(chunk, client_addr)

            time.sleep(1 / 30)  # ~30 FPS
    except Exception as e:
        print("[SERVER ERROR]:", e)
    finally:
        sock.close()

if __name__ == "__main__":
    start_udp_server()
