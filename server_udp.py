import socket
import time
import cv2
import numpy as np
import mss
import threading
import zlib

class UDPServer:
    def __init__(self):
        self.running = False
        self.sock = None
        self.client_addr = None
        self.seq_num = 0
        self.MAX_PACKET_SIZE = 1400  # Optimal for most networks
        self.TARGET_FPS = 30
        self.frame_stats = {'sent': 0, 'dropped': 0, 'bytes_sent': 0}

    def start_server(self, resize_to=(1280, 720), jpeg_quality=60, fps=30):
        self.TARGET_FPS = fps
        self.running = True

        # Socket setup with larger buffers
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 16 * 1024 * 1024)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.sock.bind(('0.0.0.0', 33060))
        except socket.error as e:
            print(f"[SERVER] Bind failed: {e}")
            return False

        print(f"[SERVER] Ready at 0.0.0.0:33060 | {resize_to[0]}x{resize_to[1]} | {fps}FPS | Q:{jpeg_quality}")

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            frame_interval = 1.0 / fps

            while self.running:
                self.client_addr = None
                self.seq_num = 0
                print("[SERVER] Waiting for client connection...")
                try:
                    self.sock.settimeout(1.0)
                    while self.running and self.client_addr is None:
                        try:
                            data, addr = self.sock.recvfrom(1024)
                            if data == b'connect':
                                self.client_addr = addr
                        except socket.timeout:
                            continue
                    if not self.running:
                        break
                    print(f"[SERVER] Client connected: {self.client_addr}")
                    # Send config
                    config = f"{resize_to[0]},{resize_to[1]},{fps},{jpeg_quality}"
                    self.sock.sendto(config.encode(), self.client_addr)
                except socket.error as e:
                    print(f"[SERVER] Connection error: {e}")
                    continue

                # Main capture loop for this client
                while self.running and self.client_addr is not None:
                    frame_start = time.time()
                    try:
                        # Non-blocking check for new connect messages
                        self.sock.settimeout(0.01)
                        try:
                            data, addr = self.sock.recvfrom(1024)
                            if data == b'connect' and addr != self.client_addr:
                                print(f"[SERVER] New client {addr} requested connection. Switching.")
                                break  # Break to outer loop to accept new client
                        except socket.timeout:
                            pass
                        # 1. Capture
                        img = np.array(sct.grab(monitor))
                        # 2. Process
                        img = cv2.resize(img, resize_to)
                        ret, buffer = cv2.imencode('.jpg', img, [
                            int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality
                        ])
                        if not ret:
                            continue
                        # 3. Compress
                        compressed = zlib.compress(buffer.tobytes(), level=1)
                        # 4. Send
                        self._send_frame(compressed)
                        self.frame_stats['sent'] += 1
                        self.frame_stats['bytes_sent'] += len(compressed)
                        # 5. Maintain FPS
                        elapsed = time.time() - frame_start
                        sleep_time = max(0, frame_interval - elapsed)
                        if sleep_time < 0:
                            self.frame_stats['dropped'] += 1
                            if self.frame_stats['dropped'] % 10 == 0:
                                print(f"[SERVER] Can't keep up! Dropped {self.frame_stats['dropped']} frames")
                        else:
                            time.sleep(sleep_time)
                    except Exception as e:
                        print(f"[SERVER] Frame error or client disconnected: {str(e)}")
                        # On error, break to wait for new client
                        break

        return True

    def _send_frame(self, frame_data):
        try:
            # 1. Create header
            header = (
                self.seq_num.to_bytes(4, 'big') +
                len(frame_data).to_bytes(4, 'big') +
                zlib.crc32(frame_data).to_bytes(4, 'big')
            )
            self.seq_num += 1
            
            # 2. Split into chunks
            chunks = []
            for i in range(0, len(frame_data), self.MAX_PACKET_SIZE):
                chunk = frame_data[i:i + self.MAX_PACKET_SIZE]
                chunks.append(chunk)

            # 3. Send metadata
            metadata = header + len(chunks).to_bytes(2, 'big')
            self.sock.sendto(metadata, self.client_addr)
            
            # 4. Send chunks
            for chunk in chunks:
                self.sock.sendto(chunk, self.client_addr)
                time.sleep(0.0005)

        except socket.error as e:
            if e.errno == 10040:  # WSAEMSGSIZE
                self.MAX_PACKET_SIZE = max(508, self.MAX_PACKET_SIZE - 100)
                print(f"[SERVER] Reduced packet size to {self.MAX_PACKET_SIZE}")
            else:
                print(f"[SERVER] Send error: {e}")

    def stop_server(self):
        self.running = False
        if self.sock:
            try:
                if self.client_addr:
                    self.sock.sendto(b'TERMINATE', self.client_addr)
            finally:
                self.sock.close()
                print(f"[SERVER] Stopped. Stats: {self.frame_stats}")

# Wrapper functions for GUI compatibility
_server_instance = None

def start_udp_server(resize_to=(1280, 720), jpeg_quality=60, fps=25):
    global _server_instance
    _server_instance = UDPServer()
    server_thread = threading.Thread(
        target=_server_instance.start_server,
        kwargs={
            'resize_to': resize_to,
            'jpeg_quality': jpeg_quality,
            'fps': fps
        },
        daemon=True
    )
    server_thread.start()
    return True

def stop_udp_server():
    global _server_instance
    if _server_instance:
        _server_instance.stop_server()
        _server_instance = None
    return True