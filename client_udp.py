import socket
import pygame
import cv2
import numpy as np
import time
import threading
import zlib
from datetime import datetime

class UDPClient:
    def __init__(self):
        self.running = False
        self.sock = None
        self.last_frame = None
        self.frame_lock = threading.Lock()
        self.stats = {
            'received': 0,
            'dropped': 0,
            'last_seq': -1,
            'fps': 0,
            'data_received': 0,
            'config_received': False
        }
        self.MAX_PACKET_SIZE = 1400
        self.BUFFER_SIZE = 16 * 1024 * 1024
        self.screen_width = 1280
        self.screen_height = 720
        self.font = None
        self.last_frames = []

    def start_client(self, server_ip='192.168.1.100'):
        self.running = True
        pygame.init()
        
        # Socket setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFFER_SIZE)
        self.sock.settimeout(5.0)
        
        # Connect to server
        print("[CLIENT] Connecting to server...")
        self.sock.sendto(b'connect', (server_ip, 33060))
        
        # Get configuration with retries
        config = None
        for _ in range(10):  # Try 10 times to get config
            try:
                config, _ = self.sock.recvfrom(1024)
                break
            except socket.timeout:
                print("[CLIENT] Waiting for config...")
                continue
        
        if not config:
            print("[CLIENT] Failed to receive configuration")
            self.running = False
            return
            
        try:
            width, height, fps, quality = map(int, config.decode().split(','))
            self.screen_width, self.screen_height = width, height
            self.stats['config_received'] = True
            print(f"[CLIENT] Config received: {width}x{height}@{fps}fps")
        except:
            print("[CLIENT] Invalid config received")
            self.running = False
            return

        # Setup display
        self.screen = pygame.display.set_mode((width, height), 
            pygame.DOUBLEBUF | pygame.HWSURFACE)
        pygame.display.set_caption(f"Screen Mirror | {width}x{height} | {fps}FPS")
        self.font = pygame.font.SysFont('Arial', 24)
        
        # Start network thread
        threading.Thread(target=self._receive_loop, daemon=True).start()
        
        # Main display loop
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.running = False
            
            with self.frame_lock:
                if self.last_frame:
                    self.screen.blit(self.last_frame, (0, 0))
                    self._display_stats()
                    pygame.display.flip()
            
            # Calculate FPS
            self.last_frames.append(time.time())
            self.last_frames = [t for t in self.last_frames if t > time.time() - 1]
            self.stats['fps'] = len(self.last_frames)
            
            clock.tick(fps)

    def _display_stats(self):
        """Display statistics overlay"""
        stats_text = [
            f"FPS: {self.stats['fps']}",
            f"Received: {self.stats['received']}",
            f"Dropped: {self.stats['dropped']}",
            f"Loss: {self._calculate_loss_rate():.1f}%",
            f"Data: {self.stats['data_received']/1024/1024:.2f} MB"
        ]
        
        y_offset = 10
        for text in stats_text:
            text_surface = self.font.render(text, True, (255, 255, 255), (0, 0, 0))
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 30

    def _calculate_loss_rate(self):
        total = self.stats['received'] + self.stats['dropped']
        return (self.stats['dropped'] / total * 100) if total > 0 else 0

    def _receive_loop(self):
        while self.running:
            try:
                # Receive metadata
                metadata, _ = self.sock.recvfrom(18)
                if len(metadata) < 14:
                    continue
                    
                # Parse header
                seq_num = int.from_bytes(metadata[:4], 'big')
                total_size = int.from_bytes(metadata[4:8], 'big')
                checksum = int.from_bytes(metadata[8:12], 'big')
                total_chunks = int.from_bytes(metadata[12:14], 'big')
                
                # Receive chunks
                chunks = {}
                for _ in range(total_chunks):
                    try:
                        chunk, _ = self.sock.recvfrom(self.MAX_PACKET_SIZE + 100)
                        chunks[len(chunks)] = chunk
                    except socket.timeout:
                        break
                
                # Reassemble frame
                if len(chunks) == total_chunks:
                    frame_data = b''.join(chunks.values())
                    self.stats['data_received'] += len(frame_data)
                    
                    if zlib.crc32(frame_data) == checksum:
                        self._process_frame(frame_data)
                        self.stats['received'] += 1
                        
                        # Check for dropped frames
                        if self.stats['last_seq'] != -1 and seq_num > self.stats['last_seq'] + 1:
                            self.stats['dropped'] += seq_num - (self.stats['last_seq'] + 1)
                        self.stats['last_seq'] = seq_num
                    else:
                        self.stats['dropped'] += 1
                else:
                    self.stats['dropped'] += 1
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[CLIENT] Error: {str(e)}")
                time.sleep(0.1)

    def _process_frame(self, frame_data):
        try:
            # Decompress and decode
            decompressed = zlib.decompress(frame_data)
            np_img = np.frombuffer(decompressed, dtype=np.uint8)
            frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            if frame is None:
                return
                
            # Convert to pygame surface
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_surface = pygame.image.frombuffer(
                frame.tobytes(), frame.shape[1::-1], "RGB")
            
            with self.frame_lock:
                self.last_frame = frame_surface
                
        except Exception as e:
            print(f"[CLIENT] Frame error: {str(e)}")

    def stop_client(self):
        self.running = False
        if self.sock:
            self.sock.close()
        pygame.quit()
        print(f"[CLIENT] Stopped. Final stats: {self.stats}")

# Wrapper functions
_client_instance = None

def start_udp_client(server_ip='192.168.1.100'):
    global _client_instance
    _client_instance = UDPClient()
    client_thread = threading.Thread(
        target=_client_instance.start_client,
        kwargs={'server_ip': server_ip},
        daemon=True
    )
    client_thread.start()
    return True

def stop_udp_client():
    global _client_instance
    if _client_instance:
        _client_instance.stop_client()
        _client_instance = None
    return True