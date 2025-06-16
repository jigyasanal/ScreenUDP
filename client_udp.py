# client_udp.py

import socket
import pygame
import cv2
import numpy as np
import time

SERVER_IP = '192.168.1.100'  # Change to your server IP
PORT = 33060
CHUNK_SIZE = 60000

running = False  # Global control flag

def mirror_once():
    global running
    running = True

    while running:  # Outer loop to allow reconnection
        # Initialize PyGame and socket inside the loop
        pygame.init()
        info = pygame.display.Info()
        screen_width, screen_height = info.current_w, info.current_h

        screen = pygame.display.set_mode(
            (screen_width, screen_height),
            pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
        )
        pygame.display.set_caption("Screen Mirror")
        pygame.mouse.set_visible(False)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
        sock.sendto(b'hello', (SERVER_IP, PORT))

        try:
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        break
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        running = False
                        break

                if not running:
                    break

                try:
                    header, _ = sock.recvfrom(65535)
                    header_str = header.decode('latin-1')  # More reliable decoding
                    total_size, num_chunks = map(int, header_str.split(','))

                    buffer = b''
                    for _ in range(num_chunks):
                        chunk, _ = sock.recvfrom(CHUNK_SIZE + 100)
                        buffer += chunk

                    if len(buffer) != total_size:
                        continue

                    np_img = np.frombuffer(buffer, dtype=np.uint8)
                    frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
                    if frame is None:
                        continue

                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (screen_width, screen_height))

                    frame_surface = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")
                    screen.blit(frame_surface, (0, 0))
                    pygame.display.update()

                except socket.timeout:
                    print("[CLIENT] Timeout. Reconnecting...")
                    break  # Exit inner loop to reconnect
                except Exception as e:
                    print(f"[CLIENT] Error: {e}. Reconnecting...")
                    break  # Exit inner loop to reconnect

        finally:
            if 'sock' in locals(): 
                sock.shutdown(socket.SHUT_RDWR)  # Force socket closure
                sock.close()
            pygame.quit()
            pygame.display.quit()  # Extra cleanup
            time.sleep(1)  # Critical delay

def start_udp_client():
    mirror_once()

def stop_udp_client():
    global running
    running = False