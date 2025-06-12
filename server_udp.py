import socket
import time
import cv2
import numpy as np
import mss

CHUNK_SIZE = 60000  # UDP safe size
SERVER_IP = '0.0.0.0'
PORT = 33060

def capture_frame(resize_to=(800, 600)):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        img = np.array(sct.grab(monitor))
        img = cv2.resize(img, resize_to)
        ret, buffer = cv2.imencode  ('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 25, int(cv2.IMWRITE_JPEG_OPTIMIZE),1])
        return buffer.tobytes() if ret else None

def start_udp_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
    sock.bind((SERVER_IP, PORT))
    print("[SERVER] Listening for client...")
    
    # Handshake
    data, client_addr = sock.recvfrom(1024)
    print(f"[SERVER] Client connected from {client_addr}")

    try:
        while True:
            frame = capture_frame()
            if not frame:
                continue

            total_size = len(frame)
            num_chunks = (total_size // CHUNK_SIZE) + 1

            # Send header: total_size and chunk count
            sock.sendto(f"{total_size},{num_chunks}".encode(), client_addr)

            # Send chunks
            for i in range(num_chunks):
                chunk = frame[i*CHUNK_SIZE : (i+1)*CHUNK_SIZE]
                sock.sendto(chunk, client_addr)

            time.sleep(1/25)
    except Exception as e:
        print("[SERVER ERROR]:", e)
    finally:
        sock.close()

if __name__ == "__main__":
    start_udp_server()
