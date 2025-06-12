import socket
import pygame
import io
from PIL import Image
import struct

def start_udp_client(server_ip='192.168.63.53', server_port=5005):
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("UDP Screen Mirror Client")

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(2.0)

    # Handshake with server
    udp_socket.sendto(b'hello', (server_ip, server_port))

    try:
        while True:
            try:
                # Receive packet (size + image)
                packet, _ = udp_socket.recvfrom(65536)  # Max UDP size
                if len(packet) < 4:
                    continue
                img_len = struct.unpack('!I', packet[:4])[0]
                img_data = packet[4:]

                # If incomplete image (rarely), skip
                if len(img_data) != img_len:
                    continue

                # Convert to image
                img = Image.open(io.BytesIO(img_data)).convert('RGB')
                img_surface = pygame.image.frombuffer(img.tobytes(), img.size, "RGB")

                # Draw on screen
                screen.blit(img_surface, (0, 0))
                pygame.display.update()

            except socket.timeout:
                print("[CLIENT] Timeout - retrying...")
    except KeyboardInterrupt:
        print("[CLIENT] Interrupted, closing.")
    finally:
        udp_socket.close()

if __name__ == "__main__":
    start_udp_client()
