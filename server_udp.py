import socket
import time
import cv2
import numpy as np
import mss

CHUNK_SIZE = 60000
SERVER_IP = '0.0.0.0'
PORT = 33060

server_running = False  # Global flag

def capture_frame(resize_to=(800, 600), jpeg_quality=35):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = np.array(sct.grab(monitor))
        img = cv2.resize(img, resize_to)
        ret, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
        return buffer.tobytes() if ret else None

def start_udp_server(resize_to=(800, 600), jpeg_quality=35):
    global server_running
    server_running = True

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
    sock.bind((SERVER_IP, PORT))
    print("[SERVER] Listening for client...")

    try:
        data, client_addr = sock.recvfrom(1024)
        print(f"[SERVER] Client connected from {client_addr}")

        while server_running:
            frame = capture_frame(resize_to, jpeg_quality)
            if not frame:
                continue

            total_size = len(frame)
            num_chunks = (total_size // CHUNK_SIZE) + 1
            sock.sendto(f"{total_size},{num_chunks}".encode(), client_addr)

            for i in range(num_chunks):
                chunk = frame[i * CHUNK_SIZE : (i + 1) * CHUNK_SIZE]
                sock.sendto(chunk, client_addr)

            time.sleep(1 / 30)

    except Exception as e:
        print(f"[SERVER ERROR]: {e}")
    finally:
        sock.close()
        print("[SERVER] Disconnected")

def stop_udp_server():
    global server_running
    server_running = False
