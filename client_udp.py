import socket
import pygame
import cv2
import numpy as np

SERVER_IP = '192.168.1.100'  # Change this to your server IP
PORT = 33060
CHUNK_SIZE = 60000

def start_udp_client():
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
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return

            try:
                # Receive header
                header, _ = sock.recvfrom(1024)
                total_size, num_chunks = map(int, header.decode().split(','))

                buffer = b''
                for _ in range(num_chunks):
                    chunk, _ = sock.recvfrom(CHUNK_SIZE + 100)
                    buffer += chunk

                if len(buffer) != total_size:
                    print("[CLIENT] Incomplete frame, skipping...")
                    continue

                # Decode image
                np_img = np.frombuffer(buffer, dtype=np.uint8)
                frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (screen_width, screen_height))  # Scale to fullscreen

                # Display
                frame_surface = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")
                screen.blit(frame_surface, (0, 0))
                pygame.display.update()

            except socket.timeout:
                print("[CLIENT] Timeout.")
    except KeyboardInterrupt:
        print("[CLIENT] Stopped.")
    finally:
        sock.close()

if __name__ == "__main__":
    start_udp_client()
