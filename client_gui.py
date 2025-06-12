import tkinter as tk
from tkinter import ttk
import threading
import client_udp  # Your client logic file

class ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Screen Mirror - Client")

        ttk.Label(root, text="Server IP:").pack()
        self.ip_entry = ttk.Entry(root)
        self.ip_entry.insert(0, "192.168.1.100")
        self.ip_entry.pack()

        self.connect_button = ttk.Button(root, text="Connect", command=self.connect_to_server)
        self.connect_button.pack(pady=10)

        self.status_label = ttk.Label(root, text="Status: Not connected")
        self.status_label.pack(pady=10)

    def connect_to_server(self):
        ip = self.ip_entry.get()
        self.status_label.config(text="Status: Connecting...")
        threading.Thread(target=client_udp.start_udp_client,
                         args=(ip,),
                         daemon=True).start()
        self.status_label.config(text="Status: Connected")

if __name__ == "__main__":
    root = tk.Tk()
    gui = ClientGUI(root)
    root.mainloop()
