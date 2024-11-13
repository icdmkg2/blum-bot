import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from pyautogui import screenshot
import pygetwindow as gw
import time
import random
import json
import os
from pynput.mouse import Button, Controller
import keyboard
import threading
import sv_ttk  # Import sv-ttk for theming
import pywinstyles, sys  # Import necessary for title bar theming
import darkdetect  # Import darkdetect for system theme detection

mouse = Controller()

def click(x, y):
    mouse.position = (x, y + random.randint(1, 3))
    mouse.press(Button.left)
    mouse.release(Button.left)

def apply_theme_to_titlebar(root):
    version = sys.getwindowsversion()

    if version.major == 10 and version.build >= 22000:
        # Set the title bar color to the background color on Windows 11 for better appearance
        pywinstyles.change_header_color(root, "#1c1c1c" if sv_ttk.get_theme() == "dark" else "#fafafa")
    elif version.major == 10:
        pywinstyles.apply_style(root, "dark" if sv_ttk.get_theme() == "dark" else "normal")

        # A hacky way to update the title bar's color on Windows 10 (it doesn't update instantly like on Windows 11)
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)

class BotGUI:
    SETTINGS_FILE = "settings.json"

    def __init__(self, root):
        self.root = root
        self.root.title("Blum Bot")
        self.paused = False
        self.bot_running = False
        self.setting_hotkey = False
        self.hotkey = "k"  # Default hotkey
        self.window_choice = "TelegramDesktop"  # Default window choice

        # Load saved settings if they exist
        self.load_settings()

        # Window selection (Use ttk widget for dropdown)
        self.window_var = tk.StringVar(value=self.window_choice)
        window_menu = ttk.OptionMenu(root, self.window_var, "TelegramDesktop", "KotatogramDesktop")
        window_menu.grid(row=0, column=0, padx=10, pady=10)

        # Hotkey entry
        ttk.Label(root, text="Pause/Resume Hotkey:").grid(row=1, column=0, padx=10, pady=10)
        self.hotkey_label = ttk.Label(root, text=self.hotkey, width=10, relief="sunken")
        self.hotkey_label.grid(row=1, column=1, padx=10, pady=10)

        # Set hotkey button (Use ttk button for styling)
        hotkey_button = ttk.Button(root, text="Set Hotkey", command=self.set_hotkey)
        hotkey_button.grid(row=1, column=2, padx=10, pady=10)

        # Start button
        start_button = ttk.Button(root, text="Start Bot", command=self.start_bot)
        start_button.grid(row=0, column=1, padx=10, pady=10)

        # Status label
        self.status_label = ttk.Label(root, text="Status: Idle")
        self.status_label.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

        # Apply the sv-ttk theme AFTER the Tk() window is created using darkdetect
        sv_ttk.set_theme(darkdetect.theme())  # Automatically sets the theme based on system preference

        # Apply theme to titlebar after setting the theme
        apply_theme_to_titlebar(root)

    def set_hotkey(self):
        self.setting_hotkey = True
        self.hotkey_label.config(text="Press a key...")
        self.status_label["text"] = "Status: Waiting for hotkey press"
        
        threading.Thread(target=self.capture_hotkey, daemon=True).start()

    def capture_hotkey(self):
        while self.setting_hotkey:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                self.hotkey = event.name
                self.hotkey_label.config(text=self.hotkey)
                self.setting_hotkey = False
                self.status_label["text"] = f"Status: Hotkey set to '{self.hotkey}'"
                self.save_settings()

    def start_bot(self):
        window_name = self.window_var.get()
        if window_name not in ["TelegramDesktop", "KotatogramDesktop"]:
            messagebox.showerror("Error", "Please select a valid window.")
            return

        check = gw.getWindowsWithTitle(window_name)
        if not check:
            messagebox.showerror("Error", f"Window '{window_name}' not found! Make sure it's open and visible.")
            return

        self.window_choice = window_name
        self.save_settings()

        self.telegram_window = check[0]
        self.status_label["text"] = f"Status: Running on {window_name}"
        self.bot_running = True
        self.paused = False

        threading.Thread(target=self.run_bot, daemon=True).start()

    def run_bot(self):
        while self.bot_running:
            if keyboard.is_pressed(self.hotkey):
                self.paused = not self.paused
                status = "Paused" if self.paused else "Running"
                self.status_label["text"] = f"Status: {status}"
                time.sleep(0.3)

            if self.paused:
                time.sleep(0.1)
                continue

            try:
                self.telegram_window.activate()
            except:
                self.telegram_window.minimize()
                self.telegram_window.restore()

            window_rect = (
                self.telegram_window.left, self.telegram_window.top,
                self.telegram_window.width, self.telegram_window.height
            )

            scrn = screenshot(region=(window_rect[0], window_rect[1], window_rect[2], window_rect[3]))

            width, height = scrn.size
            pixel_found = False

            for x in range(0, width, 20):
                for y in range(0, height, 20):
                    r, g, b = scrn.getpixel((x, y))
                    if (b in range(20, 125)) and (r in range(102, 220)) and (g in range(200, 255)):
                        screen_x = window_rect[0] + x
                        screen_y = window_rect[1] + y
                        click(screen_x + 4, screen_y)
                        time.sleep(0.020)
                        pixel_found = True
                        break
                if pixel_found:
                    break

    def load_settings(self):
        if os.path.exists(self.SETTINGS_FILE):
            try:
                with open(self.SETTINGS_FILE, "r") as file:
                    settings = json.load(file)
                    self.hotkey = settings.get("hotkey", self.hotkey)
                    self.window_choice = settings.get("window_choice", self.window_choice)
            except (json.JSONDecodeError, FileNotFoundError):
                pass

    def save_settings(self):
        settings = {
            "hotkey": self.hotkey,
            "window_choice": self.window_var.get()
        }
        with open(self.SETTINGS_FILE, "w") as file:
            json.dump(settings, file)

    def on_closing(self):
        self.bot_running = False
        self.root.destroy()

# Create the root window
root = tk.Tk()

# Create and run the GUI application
app = BotGUI(root)
root.protocol("WM_DELETE_WINDOW", app.on_closing)
root.mainloop()
