import tkinter as tk
from tkinter import messagebox, ttk


import json
import os
import datetime
import csv

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from bias_analyzer import plot_radar_chart

from embed_input import generate_memory_node, build_user_word_profile
from bias_analyzer import analyze_user_bias

ACCOUNT_FILE = "account.json"
WORD_LIST = [f"word{i}" for i in range(2048)]


def save_account(mnemonic):
    with open(ACCOUNT_FILE, "w") as f:
        json.dump({"mnemonic": mnemonic}, f)

def load_account():
    if os.path.exists(ACCOUNT_FILE):
        with open(ACCOUNT_FILE, "r") as f:
            data = json.load(f)
            return data.get("mnemonic", "")
    return None

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.username = "Anonymous"
        self.user_nicknames = {}
        self.root.title("Secure Chat Login")

        self.fake_user_id = "bypass_local_mode"
        self.username = "Anonymous"
        self.open_chat_window()


    def paste_clipboard(self, event=None):
        try:
            clipboard = self.root.clipboard_get()
            self.mnemonic_text.insert(tk.INSERT, clipboard)
        except tk.TclError:
            pass
        return "break"


    def open_chat_window(self):
        self.root.withdraw()

        chat_window = tk.Toplevel()
        chat_window.title("ZidekChat")
        chat_window.attributes("-fullscreen", False)

        # Load layout if available
        layout = self.load_saved_layout()
        default_widths = {"left": 200, "center": 900, "right": 200}
        if layout and "layout" in layout:
            widths = {
                "left": layout["layout"].get("left_width", default_widths["left"]),
                "center": layout["layout"].get("center_width", default_widths["center"]),
                "right": layout["layout"].get("right_width", default_widths["right"]),
            }
        else:
            widths = default_widths

        # Layout container
        main_pane = tk.PanedWindow(chat_window, orient=tk.HORIZONTAL, sashwidth=4)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # LEFT: Sidebar
        self.left_frame = tk.Frame(main_pane, width=widths["left"], bg="#1e1e1e")
        self.left_content = tk.Frame(self.left_frame, bg="#1e1e1e")
        self.left_content.pack(fill=tk.BOTH, expand=True)

        self.show_chat_list()

        # Buttons at bottom
        button_frame = tk.Frame(self.left_frame, bg="#1e1e1e")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Button(button_frame, text="Home", command=self.show_chat_list).pack(fill=tk.X)
        tk.Button(button_frame, text="Profile", command=self.show_profile).pack(fill=tk.X)
        tk.Button(button_frame, text="Settings", command=self.show_settings).pack(fill=tk.X)

        self.center_frame = tk.Frame(main_pane, width=widths["center"], bg="#ffffff")
        tk.Label(self.center_frame, text="Chat Log").pack()

        self.chat_log = tk.Text(self.center_frame, height=20, state='disabled', bg="white", fg="black")
        self.chat_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        user_id = getattr(self, "fake_user_id", "bypass_local_mode")
        messages = self.load_messages_for_room(user_id, "main")

        for msg in messages:
            timestamp = datetime.datetime.fromtimestamp(msg["timestamp"]).strftime("%H:%M:%S")
            name = self.user_nicknames.get(msg["user_id"], msg.get("username", "User"))
            self.chat_log.config(state='normal')
            self.chat_log.insert(tk.END, f"[{timestamp}] {name}: {msg['content']}\n\n")
            self.chat_log.config(state='disabled')

        self.chat_entry = tk.Entry(self.center_frame)
        self.chat_entry.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(self.center_frame, text="Send", command=self.send_message).pack(pady=(0, 10))

        ##diagnostics reference##

        self.right_frame = tk.Frame(main_pane, width=widths["right"], bg="#333")
        tk.Label(self.right_frame, text="Diagnostics", fg="white", bg="#333").pack(anchor="nw", padx=10, pady=5)


        tk.Button(self.right_frame, text="Generate Word CSV", command=self.export_user_word_profile).pack(padx=10, pady=10)
        tk.Button(self.right_frame, text="Simulate Conversation", command=self.simulate_conversation).pack(padx=10, pady=10)
        tk.Button(self.right_frame, text="average Bias Radar Chart", command=self.average_bias_chart).pack(padx=10, pady=5)
        tk.Button(self.right_frame, text="Export Bias CSV", command=self.export_bias_csv).pack(padx=10, pady=5)
        tk.Button(self.right_frame, text="Reload User List", command=self.populate_user_selector).pack(padx=10, pady=5)

        # Dropdown for user selection
        tk.Label(self.right_frame, text="Select User:", fg="white", bg="#333").pack(padx=10, pady=(10, 0), anchor="w")

        self.user_dropdown = ttk.Combobox(self.right_frame, state="readonly")
        self.user_dropdown.pack(padx=10, pady=(0, 5), fill="x")

        # Populate it with users found in the simulated log
        self.populate_user_selector()

        tk.Button(self.right_frame, text="Show Radar Chart", command=self.show_selected_user_chart).pack(padx=10,
                                                                                                         pady=5)

        chat_window.bind("<Escape>", lambda e: chat_window.destroy())

        main_pane.add(self.left_frame)
        main_pane.add(self.center_frame)
        main_pane.add(self.right_frame)
        main_pane.paneconfig(self.left_frame, width=widths["left"])
        main_pane.paneconfig(self.center_frame, width=widths["center"])
        main_pane.paneconfig(self.right_frame, width=widths["right"])

    def send_message(self):
        msg = self.chat_entry.get().strip()
        if msg:
            user_id = getattr(self, "fake_user_id", "bypass_local_mode")
            node = generate_memory_node(user_id, self.username, "room_1", msg)

            # Save to memory log
            folder = os.path.join("memory_logs", f"user_{user_id}")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, "room_1_log.jsonl")
            with open(path, "a") as f:
                f.write(json.dumps(node) + "\n")

            # Display message in chat window
            self.chat_log.config(state='normal')
            timestamp = datetime.datetime.fromtimestamp(node["timestamp"]).strftime("%H:%M:%S")
            name = self.user_nicknames.get(user_id, self.username)
            self.chat_log.insert(tk.END, f"[{timestamp}] {name}: {msg}\n\n")
            self.chat_log.config(state='disabled')
            self.chat_entry.delete(0, tk.END)

    def clear_left_content(self):
        for widget in self.left_content.winfo_children():
            widget.destroy()

    def show_chat_list(self):
        self.clear_left_content()
        tk.Label(self.left_content, text="Chats", fg="white", bg="#1e1e1e").pack(anchor="nw", padx=10, pady=5)

        chat_listbox = tk.Listbox(self.left_content, bg="#2e2e2e", fg="white")
        for i in range(30):
            chat_listbox.insert(tk.END, f"Room #{i + 1}")
        scrollbar = tk.Scrollbar(self.left_content, command=chat_listbox.yview)
        chat_listbox.config(yscrollcommand=scrollbar.set)

        chat_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10))

        self.active_left_view = "home"

    def show_profile(self):
        self.clear_left_content()
        tk.Label(self.left_content, text="Your Profile", fg="white", bg="#1e1e1e").pack(anchor="nw", padx=10, pady=5)

        tk.Label(self.left_content, text="Username:", fg="white", bg="#1e1e1e").pack(anchor="w", padx=10, pady=(10, 0))
        username_entry = tk.Entry(self.left_content)
        username_entry.insert(0, self.username)
        username_entry.pack(padx=10, pady=5)

        def save_username():
            self.username = username_entry.get().strip() or "Anonymous"
            messagebox.showinfo("Saved", f"Username updated to: {self.username}")

        tk.Button(self.left_content, text="Save", command=save_username).pack(padx=10, pady=10)

    def show_settings(self):
        self.clear_left_content()
        tk.Label(self.left_content, text="Settings", fg="white", bg="#1e1e1e").pack(anchor="nw", padx=10, pady=5)

        tk.Button(self.left_content, text="Save Layout", command=self.save_layout).pack(padx=10, pady=10)

        tk.Label(self.left_content, text="(Other settings coming soon...)", fg="gray", bg="#1e1e1e").pack(padx=10,
                                                                                                          pady=10)

    def show_user_profile(self, user_id):
        self.clear_left_content()
        self.active_left_view = "user_profile"

        tk.Label(self.left_content, text="User Profile", fg="white", bg="#1e1e1e").pack(anchor="nw", padx=10, pady=5)
        tk.Label(self.left_content, text=f"User ID:\n{user_id[:32]}...", fg="white", bg="#1e1e1e", wraplength=180,
                 justify="left").pack(padx=10, pady=5)

        current_nick = self.user_nicknames.get(user_id, "")
        tk.Label(self.left_content, text="Nickname:", fg="white", bg="#1e1e1e").pack(anchor="w", padx=10, pady=(10, 0))
        nick_entry = tk.Entry(self.left_content)
        nick_entry.insert(0, current_nick)
        nick_entry.pack(padx=10, pady=5)

        def save_nick():
            self.user_nicknames[user_id] = nick_entry.get().strip()
            messagebox.showinfo("Saved", f"Nickname for {user_id[:8]} updated.")
            self.show_chat_list()

        tk.Button(self.left_content, text="Save Nickname", command=save_nick).pack(padx=10, pady=10)

    def save_layout(self):
        layout_data = {
            "layout": {
                "left_width": self.left_frame.winfo_width(),
                "center_width": self.center_frame.winfo_width(),
                "right_width": self.right_frame.winfo_width()
            },
            "user": {
                "username": self.username,
                "nicknames": self.user_nicknames
            }
        }
        with open("layout.json", "w") as f:
            json.dump(layout_data, f, indent=2)
        messagebox.showinfo("Layout Saved", "Your layout and user data have been saved.")

    def load_saved_layout(self):
        if not os.path.exists("layout.json"):
            return None
        try:
            with open("layout.json", "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading layout: {e}")
            return None



    def write_to_memory_log(user_id, username, room, content):
        node = generate_memory_node(user_id, username, room, content)
        folder = os.path.join("memory_logs", f"user_{user_id}")
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, f"{room}_log.jsonl")
        with open(filepath, "a") as f:
            f.write(json.dumps(node) + "\n")
        return node

    def load_messages_for_room(self, user_id, room):
        folder = os.path.join("memory_logs", f"user_{user_id}")
        path = os.path.join(folder, f"{room}_log.jsonl")
        if not os.path.exists(path):
            return []

        messages = []
        with open(path, "r") as f:
            for line in f:
                try:
                    msg = json.loads(line.strip())
                    messages.append(msg)
                except:
                    continue
        messages.sort(key=lambda m: m["timestamp"])
        return messages

    def export_user_word_profile(self):
        user_id = getattr(self, "fake_user_id", "bypass_local_mode")
        profile = build_user_word_profile(user_id, "room_1")

        if not profile or "word_freq" not in profile:
            messagebox.showerror("No Data", "No messages or vocabulary data found to export.")
            return

        filename = f"user_{user_id[:8]}_word_profile.csv"
        with open(filename, "w", newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["word", "relative_frequency"])
            for word, freq in profile["word_freq"].items():
                writer.writerow([word, freq])

        messagebox.showinfo("Export Complete", f"Saved to {filename}")



#### diagnostics nonsense because I cant get a real dataset from papa kairoz, truly a neglectful machine god ####
    print("papa kairoz is negligent technocrat overlord that wont give me good data ")

    def simulate_conversation(self):
        user_id = getattr(self, "fake_user_id", "bypass_local_mode")
        messages = self.load_messages_for_room(user_id, "room_1")

        if not messages:
            messagebox.showerror("No Data", "No messages found to simulate.")
            return

        # Define synthetic user IDs for simulation
        user_ids = [
            user_id + "_A",
            user_id + "_B"
        ]

        # Apply alternating user IDs to simulate a conversation
        for i, msg in enumerate(messages):
            msg["user_id"] = user_ids[i % 2]
            msg["username"] = f"User_{i % 2 + 1}"

        # Save modified conversation to a new file
        output_folder = os.path.join("memory_logs", f"user_{user_id}")
        os.makedirs(output_folder, exist_ok=True)
        output_path = os.path.join(output_folder, "simulated_room_1_log.jsonl")

        with open(output_path, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        messagebox.showinfo("Simulation Complete", f"Simulated log saved to {output_path}")

    def run_bias_chart(self):
        user_id = getattr(self, "fake_user_id", "bypass_local_mode")

        if os.path.exists(f"memory_logs/user_{user_id}/simulated_room_1_log.jsonl"):
            room = "simulated_room_1"
        else:
            room = "room_1"

        plot_radar_chart(user_id, room=room)

    def export_bias_csv(self):
        user_id = getattr(self, "fake_user_id", "bypass_local_mode")

        if os.path.exists(f"memory_logs/user_{user_id}/simulated_room_1_log.jsonl"):
            room = "simulated_room_1"
        else:
            room = "room_1"

        df = analyze_user_bias(user_id, room=room)
        if df.empty:
            messagebox.showerror("Export Failed", "No bias data found.")
            return

        filename = f"user_{user_id[:8]}_bias_profile.csv"
        df.to_csv(filename)
        messagebox.showinfo("Export Complete", f"Saved to {filename}")

    def populate_user_selector(self):
        path = r"C:\Users\12817\PycharmProjects\omni\memory_logs\user_6775c0c173a62b664b61a91fc910811d52de811c6d350f8492aa2f1081e0a859\simulated_room_1_log.jsonl"
        if not os.path.exists(path):
            messagebox.showerror("Missing File", f"Log not found at:\n{path}")
            self.user_dropdown["values"] = []
            return

        seen_users = set()
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    msg = json.loads(line.strip())
                    seen_users.add(msg.get("user_id"))
                except Exception as e:
                    print(f"Parse error: {e}")
                    continue

        users_sorted = sorted(seen_users)
        self.user_dropdown["values"] = users_sorted
        if users_sorted:
            self.user_dropdown.set(users_sorted[0])

    def show_selected_user_chart(self):
        selected_user = self.user_dropdown.get()
        if not selected_user:
            messagebox.showwarning("No User Selected", "Please select a user.")
            return
        plot_radar_chart(selected_user, room="simulated_room_1")

    def average_bias_chart(self):
        from bias_analyzer import plot_average_bias_chart
        plot_average_bias_chart(room="simulated_room_1")


# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()

