import tkinter as tk
from tkinter import ttk
import threading
import client_udp  # Your client logic file


class ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Screen Mirror - Client")
        self.client_thread = None

        ttk.Label(root, text="Server IP:").pack()
        self.ip_entry = ttk.Entry(root)
        self.ip_entry.insert(0, "192.168.1.100")
        self.ip_entry.pack()

        self.connect_button = ttk.Button(root, text="Connect", command=self.connect)
        self.connect_button.pack(pady=5)

        self.disconnect_button = ttk.Button(root, text="Disconnect", command=self.disconnect)
        self.disconnect_button.pack(pady=5)

        self.status_label = ttk.Label(root, text="Status: Not connected")
        self.status_label.pack(pady=10)

    def connect(self):
        self.status_label.config(text="Status: Connecting...")
        client_udp.stop_flag = False  # Reset stop flag before reconnect
        self.client_thread = threading.Thread(target=client_udp.start_udp_client, daemon=True)
        self.client_thread.start()
        self.status_label.config(text="Status: Connected")

    def disconnect(self):
        client_udp.stop_flag = True
        self.status_label.config(text="Status: Disconnected")


if __name__ == "__main__":
    root = tk.Tk()
    gui = ClientGUI(root)
    root.mainloop()
