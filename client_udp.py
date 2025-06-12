import socket
import pygame
import cv2
import numpy as np

SERVER_IP = '192.168.1.100'  # Change this to your server IP
PORT = 33060
CHUNK_SIZE = 60000

running = False  # Global state toggle

def start_udp_client(fullscreen=True):
    global running
    running = True

    pygame.init()
    info = pygame.display.Info()
    screen_width, screen_height = info.current_w, info.current_h

    flags = pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE if fullscreen else 0
    screen = pygame.display.set_mode((screen_width, screen_height), flags)
    pygame.display.set_caption("Screen Mirror")
    pygame.mouse.set_visible(False)

    while running:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)

        try:
            sock.sendto(b'hello', (SERVER_IP, PORT))
            print("[CLIENT] Connected to server")

            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        running = False

                try:
                    header, _ = sock.recvfrom(1024)
                    total_size, num_chunks = map(int, header.decode().split(','))

                    buffer = b''
                    for _ in range(num_chunks):
                        chunk, _ = sock.recvfrom(CHUNK_SIZE + 100)
                        buffer += chunk

                    if len(buffer) != total_size:
                        print("[CLIENT] Incomplete frame, skipping...")
                        continue

                    np_img = np.frombuffer(buffer, dtype=np.uint8)
                    frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (screen_width, screen_height))

                    frame_surface = pygame.image.frombuffer(frame.tobytes(), (screen_width, screen_height), "RGB")
                    screen.blit(frame_surface, (0, 0))
                    pygame.display.update()

                except socket.timeout:
                    print("[CLIENT] Timeout.")
        except Exception as e:
            print(f"[CLIENT ERROR]: {e}")
        finally:
            sock.close()

    pygame.quit()
    print("[CLIENT] Disconnected")

def stop_udp_client():
    global running
    running = False
