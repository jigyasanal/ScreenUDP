import tkinter as tk
from tkinter import ttk
import threading
import server_udp  # Your server logic file

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Screen Mirror - Server")

        self.status_label = ttk.Label(root, text="Status: Idle", font=("Arial", 12))
        self.status_label.pack(pady=10)

        ttk.Label(root, text="Resolution:").pack()
        self.resolution = ttk.Combobox(root, values=["640x360", "800x600", "1024x768"])
        self.resolution.set("640x360")
        self.resolution.pack()

        ttk.Label(root, text="JPEG Quality:").pack()
        self.quality = ttk.Scale(root, from_=10, to=100, orient=tk.HORIZONTAL)
        self.quality.set(35)
        self.quality.pack()

        self.start_button = ttk.Button(root, text="Start Server", command=self.start_server)
        self.start_button.pack(pady=10)

    def start_server(self):
        res = self.resolution.get().split('x')
        resize = (int(res[0]), int(res[1]))
        quality = int(self.quality.get())
        self.status_label.config(text="Status: Running...")

        threading.Thread(target=server_udp.start_udp_server,
                         args=(resize, quality),
                         daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    gui = ServerGUI(root)
    root.mainloop()
