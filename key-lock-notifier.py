import sys
import time
import threading
import ctypes
import os
import json
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, Label, Frame, Button, Checkbutton, BooleanVar
import keyboard
import queue
import winreg as reg

# Windows API için gereken sabitler
VK_CAPITAL = 0x14
VK_NUMLOCK = 0x90
VK_SCROLL = 0x91

# Default configuration
DEFAULT_CONFIG = {
    "show_caps_lock": True,
    "show_num_lock": True,
    "show_scroll_lock": True,
    "start_with_windows": False,
    "theme": "blue_dark"
}

# Mevcut resource_path fonksiyonunu kullanın ve tüm dosya yollarında bunu kullanın
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Tuş durumlarını kontrol etmek için Windows API'sini kullanma
def get_key_state(key_code):
    return ctypes.windll.user32.GetKeyState(key_code) & 1 == 1

# Bildirim işlemi için mesaj kuyruğu
notification_queue = queue.Queue()

# Aktif bildirim penceresini takip et
active_notification = None

class ToggleButton(tk.Canvas):
    def __init__(self, parent, width=60, height=30, bg_color="#333333", active_color="#2196F3",
                 inactive_color="#F44336", command=None, initial_state=False):
        super().__init__(parent, width=width, height=height, bg=bg_color, highlightthickness=0)

        self.active_color = active_color
        self.inactive_color = inactive_color
        self.command = command
        self.state = initial_state

        # Create the toggle components with improved appearance
        self.track = self.create_rounded_rect(4, 4, width-4, height-4, 15, fill=inactive_color)

        # Düzeltilmiş başlangıç pozisyonu
        self.knob_offset = 30 if self.state else 0

        # Beyaz top için gölge efekti ekle - Koordinatlar düzeltildi
        self.shadow = self.create_oval(6 + self.knob_offset, 6, 6 + 26 + self.knob_offset, height-6,
                                     fill="#DDDDDD", outline="")

        # Beyaz top - Koordinatlar düzeltildi
        self.knob = self.create_oval(4 + self.knob_offset, 4, 4 + 26 + self.knob_offset, height-4,
                                    fill="#FFFFFF", outline="#EEEEEE", width=1)

        # Bind click events
        self.bind("<Button-1>", self.toggle)

        # Hover efekti ekle
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)

        # Initial rendering
        self.draw()

    def on_hover(self, event=None):
        """Mouse hover effect"""
        self.itemconfig(self.knob, fill="#F8F8F8")

    def on_leave(self, event=None):
        """Mouse leave effect"""
        self.itemconfig(self.knob, fill="#FFFFFF")

    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        # Create a rounded rectangle
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def toggle(self, event=None):
        self.state = not self.state
        self.draw()
        if self.command:
            self.command(self.state)

    def draw(self):
        self.itemconfig(self.track, fill=self.active_color if self.state else self.inactive_color)
        self.knob_offset = 30 if self.state else 0

        # Gölge ve topun konumunu güncelle - Koordinatlar düzeltildi
        self.coords(self.shadow, 6 + self.knob_offset, 6, 6 + 26 + self.knob_offset, self.winfo_height()-6)
        self.coords(self.knob, 4 + self.knob_offset, 4, 4 + 26 + self.knob_offset, self.winfo_height()-4)

    def set_state(self, state):
        if self.state != state:
            self.state = state
            self.draw()

class NotificationWindow:
    def __init__(self, root, image_path, text, duration=0.2, theme="blue_dark"):
        self.root = root
        self.duration = duration
        self.theme = theme

        # Define colors based on theme - Sabit tema
        bg_color = "#282828"  # Dark blue
        text_color = "#FFFFFF"  # White

        # Ekranın boyutlarını al
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        # Pencere özellikleri
        self.root.overrideredirect(True)  # Pencere kenarlarını kaldır
        self.root.attributes('-topmost', True)  # Her zaman üstte
        self.root.attributes('-alpha', 0.0)  # Başlangıçta tamamen şeffaf

        # Windows'ta arkaplanı şeffaf yapma
        self.root.configure(bg=bg_color)

        # Pencere boyutları (daha küçük boyut)
        window_width = 200
        window_height = 200

        # Pencereyi ekranın ortasında konumlandır
        x_position = (screen_width - window_width) // 2
        y_position = screen_height - 250  # Ekranın alt kısmında

        # Pencere konumunu ayarla
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        # Ana frame
        self.main_frame = Frame(root, bg=bg_color, padx=15, pady=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Görsel ekle (varsa)
        if image_path and os.path.exists(image_path):
            try:
                # PIL ile görüntüyü aç ve boyutu küçült
                pil_image = Image.open(image_path)
                pil_image = pil_image.resize((120, 120), Image.LANCZOS)

                # Tkinter'da kullanılabilir hale getir
                self.tk_image = ImageTk.PhotoImage(pil_image)

                # Görseli ekle
                self.image_label = Label(self.main_frame, image=self.tk_image, bg=bg_color)
                self.image_label.pack(pady=(0, 10))
            except Exception as e:
                print(f"Görsel yükleme hatası: {e}")
                self.create_default_image(text, bg_color)
        else:
            self.create_default_image(text, bg_color)

        # Durum metni - Daha büyük ve kalın
        status_text = "ON" if "ON" in text else "OFF"
        status_color = "#2196F3" if "ON" in text else "#F44336"  # Mavi veya Kırmızı

        self.status_label = Label(self.main_frame, text=status_text,
                             font=("Arial", 22, "bold"), fg=status_color, bg=bg_color)
        self.status_label.pack(pady=(0, 5))

        # Açıklama metni - tuş adı - Daha büyük ve kalın
        self.label = Label(self.main_frame, text=text.split(":")[0],
                      font=("Arial", 16, "bold"), fg=text_color, bg=bg_color)
        self.label.pack()

        # Animasyon için alpha değerini yavaşça artır (fade-in)
        self.fade_in()

    def create_default_image(self, text, bg_color):
        # Varsayılan görsel - yazı olarak göster
        key_text = {
            "Caps Lock": "CAPS",
            "Num Lock": "NUM",
            "Scroll Lock": "SCROLL"
        }.get(text.split(":")[0], "KEY")

        status_color = "#2196F3" if "ON" in text else "#F44336"  # Mavi veya Kırmızı

        self.default_img = Label(self.main_frame, text=key_text,
                             font=("Arial", 32, "bold"),
                             fg=status_color, bg=bg_color)
        self.default_img.pack(pady=(10, 15))

    def fade_in(self):
        """Pencereyi yavaşça görünür yap"""
        alpha = self.root.attributes('-alpha')
        if alpha < 0.9:
            alpha += 0.1
            self.root.attributes('-alpha', alpha)
            self.root.after(30, self.fade_in)
        else:
            # Fade-in tamamlandığında fade-out için zamanlayıcı başlat
            self.root.after(int(self.duration * 1000), self.fade_out)

    def fade_out(self):
        """Pencereyi yavaşça kaybet"""
        alpha = self.root.attributes('-alpha')
        if alpha > 0.1:
            alpha -= 0.1
            self.root.attributes('-alpha', alpha)
            self.root.after(30, self.fade_out)
        else:
            self.root.destroy()
            # Bildirimi işledikten sonra global değişkeni None olarak ayarla
            global active_notification
            active_notification = None

class SettingsWindow:
    def __init__(self, parent, config, save_callback):
        self.parent = parent
        self.config = config
        self.save_callback = save_callback

        # Create a new top-level window
        self.window = tk.Toplevel(parent)
        self.window.title("Key Lock Notifier Settings")
        self.window.geometry("500x600")  # Increased height to accommodate logo
        self.window.resizable(False, False)
        # Pencereyi ekranın ortasına yerleştir
        self.center_window(self.window)
        # Set theme colors - Sabit tema (blue_dark)
        self.bg_color = "#282828"  # Dark blue
        self.text_color = "#FFFFFF"  # White
        self.accent_color = "#2196F3"  # Lighter blue
        self.button_hover_color = "#1976D2"  # Darker blue for hover

        # Configure window style
        self.window.configure(background=self.bg_color)

        # Center the window on screen
        self.center_window(self.window)

        # Create a frame for settings
        self.frame = Frame(self.window, bg=self.bg_color, padx=20, pady=20)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Add app logo
        logo_path = resource_path(os.path.join("images", "app_logo.png"))
        if os.path.exists(logo_path):
            try:
                # Open and resize logo image
                logo_image = Image.open(logo_path)
                logo_image = logo_image.resize((300, 125), Image.LANCZOS)

                # Convert to Tkinter compatible image
                self.logo_tk = ImageTk.PhotoImage(logo_image)

                # Create label and display logo
                logo_label = Label(self.frame, image=self.logo_tk, bg=self.bg_color)
                logo_label.pack(pady=(0, 15))
            except Exception as e:
                print(f"Logo loading error: {e}")
        else:
            print(f"Logo file not found: {logo_path}")

        # Title label - Daha büyük ve kalın
        Label(self.frame, text="Key Lock Notifier Settings",
              font=("Arial", 18, "bold"), fg=self.text_color, bg=self.bg_color).pack(pady=(0, 20))

        # Create a frame for the notification options
        notification_frame = Frame(self.frame, bg=self.bg_color)
        notification_frame.pack(fill=tk.X, pady=10)

        # Label for notifications - Daha büyük ve kalın
        Label(notification_frame, text="Notifications to be displayed:",
              font=("Arial", 14, "bold"), fg=self.text_color, bg=self.bg_color,
              anchor="w").pack(fill=tk.X, pady=(0, 10))

        # Toggle buttons for different key notifications
        toggle_frame = Frame(self.frame, bg=self.bg_color)
        toggle_frame.pack(fill=tk.X, pady=5)

        # Caps Lock - Daha büyük yazı
        caps_frame = Frame(toggle_frame, bg=self.bg_color)
        caps_frame.pack(fill=tk.X, pady=5)
        Label(caps_frame, text="Caps Lock", font=("Arial", 13, "bold"), fg=self.text_color,
              bg=self.bg_color, width=15, anchor="w").pack(side=tk.LEFT, padx=(0, 10))
        self.caps_toggle = ToggleButton(caps_frame, initial_state=self.config.get("show_caps_lock", True),
                                       command=lambda x: self.update_config("show_caps_lock", x))
        self.caps_toggle.pack(side=tk.RIGHT)

        # Num Lock - Daha büyük yazı
        num_frame = Frame(toggle_frame, bg=self.bg_color)
        num_frame.pack(fill=tk.X, pady=5)
        Label(num_frame, text="Num Lock", font=("Arial", 13, "bold"), fg=self.text_color,
              bg=self.bg_color, width=15, anchor="w").pack(side=tk.LEFT, padx=(0, 10))
        self.num_toggle = ToggleButton(num_frame, initial_state=self.config.get("show_num_lock", True),
                                     command=lambda x: self.update_config("show_num_lock", x))
        self.num_toggle.pack(side=tk.RIGHT)

        # Scroll Lock - Daha büyük yazı
        scroll_frame = Frame(toggle_frame, bg=self.bg_color)
        scroll_frame.pack(fill=tk.X, pady=5)
        Label(scroll_frame, text="Scroll Lock", font=("Arial", 13, "bold"), fg=self.text_color,
              bg=self.bg_color, width=15, anchor="w").pack(side=tk.LEFT, padx=(0, 10))
        self.scroll_toggle = ToggleButton(scroll_frame, initial_state=self.config.get("show_scroll_lock", True),
                                        command=lambda x: self.update_config("show_scroll_lock", x))
        self.scroll_toggle.pack(side=tk.RIGHT)

        # Separator
        separator_frame = Frame(self.frame, height=1, bg="#555555")
        separator_frame.pack(fill=tk.X, pady=15)

        # Startup option - Daha büyük yazı ve genişletilmiş alan
        startup_frame = Frame(self.frame, bg=self.bg_color)
        startup_frame.pack(fill=tk.X, pady=20)

        # Windows ile Başlat yazısı için daha geniş alan
        Label(startup_frame, text="Start with Windows",
              font=("Arial", 13, "bold"),
              fg=self.text_color,
              bg=self.bg_color,
              width=25,  # Genişliği daha da artır (20'den 25'e)
              anchor="w").pack(side=tk.LEFT, padx=(0, 10))

        self.startup_toggle = ToggleButton(startup_frame,
                                          initial_state=self.config.get("start_with_windows", False),
                                          command=lambda x: self.update_config("start_with_windows", x))
        self.startup_toggle.pack(side=tk.RIGHT)

        # Tema seçimi kaldırıldı

        # Save button
        button_frame = Frame(self.frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        # Yapımcı bilgisi - Kaydet butonunun soluna taşındı
        creator_label = Label(
            button_frame,
            text="Coder: captainmgc",
            font=("Arial", 14, "bold"),  # Yazı boyutu büyütüldü ve kalınlaştırıldı
            fg="#4CAF50",  # Yeşil renk
            bg=self.bg_color,
            cursor="hand2"
        )
        creator_label.pack(side=tk.LEFT, padx=5)  # Sol tarafa hizalandı

        # GitHub bağlantısı için tıklama olayı
        def open_github(event):
            import webbrowser
            webbrowser.open("https://github.com/captainmgc")

        creator_label.bind("<Button-1>", open_github)

        # Modern save button with hover effect - Daha büyük yazı
        self.save_button = self.create_button(
            button_frame,
            "Save and Close",
            self.save_settings
        )
        self.save_button.pack(side=tk.RIGHT, padx=5)

        # Apply button - Daha büyük yazı
        self.apply_button = self.create_button(
            button_frame,
            "Apply",
            lambda: self.save_callback(self.config)
        )
        self.apply_button.pack(side=tk.RIGHT, padx=5)
    def create_button(self, parent, text, command):
        """Modern buton oluştur - improved appearance"""
        # Create a frame for the button to add shadow effect
        btn_frame = Frame(parent, bg=self.bg_color)

        # Main button with improved styling - Daha büyük yazı
        button = tk.Button(
            btn_frame,
            text=text,
            font=("Arial", 13, "bold"),  # Daha büyük ve kalın yazı
            bg=self.accent_color,
            fg="white",
            padx=15,
            pady=8,
            bd=0,
            relief=tk.FLAT,
            activebackground=self.button_hover_color,
            activeforeground="white",
            cursor="hand2",
            command=command
        )
        button.pack(padx=1, pady=1)

        # Add rounded corners effect with border radius
        button.config(highlightbackground=self.accent_color,
                     highlightthickness=1,
                     borderwidth=0)

        # Enhanced hover effects
        def on_enter(e):
            button.config(bg=self.button_hover_color)

        def on_leave(e):
            button.config(bg=self.accent_color)

        def on_press(e):
            # Pressed effect
            button.config(relief=tk.SUNKEN)
            button.after(100, lambda: button.config(relief=tk.FLAT))

        # Bind enhanced events
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.bind("<Button-1>", on_press)

        return btn_frame

    def center_window(self, window):
        """Pencereyi ekranın ortasına konumlandır"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def update_config(self, key, value):
        self.config[key] = value

    def save_settings(self):
        self.save_callback(self.config)
        self.window.destroy()

class SystemTrayApp:
    def __init__(self, root, key_notifier):
        self.root = root
        self.key_notifier = key_notifier

        try:
            import pystray
            from PIL import Image

            # Create a system tray icon with correct path
            # Yeni kod
            icon_path = resource_path(os.path.join("images", "tray_icon.png"))

            if not os.path.exists(icon_path):
                # Create a simple icon if the file doesn't exist
                img = Image.new('RGB', (64, 64), color="#1E2736")
                img.save(icon_path)

            icon_image = Image.open(icon_path)

            menu = (
                pystray.MenuItem('Settings', self.show_settings),
                pystray.MenuItem('Exit', self.quit_app)
            )

            self.icon = pystray.Icon("KeyLockNotifier", icon_image, "Key Lock Notifier Settings", menu)

            # Run the icon in a separate thread
            threading.Thread(target=self.icon.run, daemon=True).start()

        except ImportError:
            print("pystray modülü bulunamadı, sistem tepsisi simgesi oluşturulamadı.")
            self.icon = None

    def show_settings(self):
        # Ensure the settings window appears
        self.key_notifier.show_settings()

    def quit_app(self):
        # Shutdown the application
        if self.icon:
            self.icon.stop()
        self.key_notifier.running = False
        self.root.quit()

class KeyLockNotifier:
    def __init__(self):
        self.running = True
        self.caps_lock_state = get_key_state(VK_CAPITAL)
        self.num_lock_state = get_key_state(VK_NUMLOCK)
        self.scroll_lock_state = get_key_state(VK_SCROLL)

        # Config file path
        self.config_file = os.path.join(os.path.expanduser("~"), "key_lock_notifier_config.json")

        # Load configuration
        self.config = self.load_config()

        # Tema sabit olarak ayarla
        self.config["theme"] = "blue_dark"

        # Görsel dosyalarının yolu - Updated to correct path
        self.image_folder = resource_path("images")

        # Use absolute paths for all image files
        self.caps_on_img = resource_path(os.path.join("images", "caps_on.png"))
        self.caps_off_img = resource_path(os.path.join("images", "caps_off.png"))
        self.num_on_img = resource_path(os.path.join("images", "num_on.png"))
        self.num_off_img = resource_path(os.path.join("images", "num_off.png"))
        self.scroll_on_img = resource_path(os.path.join("images", "scroll_on.png"))
        self.scroll_off_img = resource_path(os.path.join("images", "scroll_off.png"))

        # Ana GUI thread için tkinter root
        self.root = None
        self.settings_window = None

        # Görsel klasörünü oluştur (yoksa) - Development mode için
        if not os.path.exists(self.image_folder):
            try:
                os.makedirs(self.image_folder)
                print(f"'{self.image_folder}' klasörü oluşturuldu. Lütfen görsel dosyalarınızı buraya ekleyin.")
            except Exception as e:
                print(f"Klasör oluşturma hatası: {e}")

        # Apply startup settings
        self.apply_startup_settings()

    def load_config(self):
        """Yapılandırma dosyasını yükle veya yeni oluştur"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Verify all required keys exist
                    for key, value in DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
            except:
                return DEFAULT_CONFIG
        return DEFAULT_CONFIG

    def save_config(self, config=None):
        """Yapılandırmayı kaydet"""
        if config:
            self.config = config

        # Update startup registry if necessary
        self.apply_startup_settings()

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            print("The configuration has been saved.")
        except Exception as e:
            print(f"Configuration registry error: {e}")

    def apply_startup_settings(self):
        """Windows startup registry ayarlarını uygula"""
        app_name = "KeyLockNotifier"
        exe_path = os.path.abspath(sys.argv[0])

        # Fix path for PyInstaller
        if exe_path.endswith('.py'):
            exe_path = f'pythonw "{exe_path}"'

        try:
            # Open registry key
            registry_key = reg.OpenKey(reg.HKEY_CURRENT_USER,
                                     r"Software\Microsoft\Windows\CurrentVersion\Run",
                                     0, reg.KEY_SET_VALUE | reg.KEY_QUERY_VALUE)

            if self.config.get("start_with_windows", False):
                # Add to startup
                reg.SetValueEx(registry_key, app_name, 0, reg.REG_SZ, exe_path)
                print(f"Program Windows ile başlatılacak şekilde ayarlandı: {exe_path}")
            else:
                # Remove from startup if exists
                try:
                    reg.DeleteValue(registry_key, app_name)
                    print("Program Windows ile başlatılmayacak şekilde ayarlandı.")
                except:
                    # Key doesn't exist, which is fine
                    pass

            reg.CloseKey(registry_key)
        except Exception as e:
            print(f"Windows başlangıç ayarı hatası: {e}")

    def show_settings(self):
        """Ayarlar penceresini göster"""
        # Ana pencereyi gösterme, sadece ayarlar penceresini aç
        if self.settings_window is None or not tk.Toplevel.winfo_exists(self.settings_window.window):
            self.settings_window = SettingsWindow(self.root, self.config, self.save_config)
            self.settings_window.window.lift()
            self.settings_window.window.focus_force()
        else:
            # Eğer pencere zaten açıksa, sadece öne getir
            self.settings_window.window.lift()
            self.settings_window.window.focus_force()

    def process_notification_queue(self):
        """Kuyruktan bildirimleri işle"""
        try:
            # Global değişkene erişim
            global active_notification

            # Kuyruktaki bir bildirimi al (beklemeden)
            if not notification_queue.empty() and active_notification is None:
                key_name, state = notification_queue.get_nowait()

                # Yapılandırmayı kontrol et - bu tuş için bildirim gösterilmeli mi?
                show_notification = False
                if key_name == "Caps Lock" and self.config.get("show_caps_lock", True):
                    show_notification = True
                    image_path = self.caps_on_img if state else self.caps_off_img
                elif key_name == "Num Lock" and self.config.get("show_num_lock", True):
                    show_notification = True
                    image_path = self.num_on_img if state else self.num_off_img
                elif key_name == "Scroll Lock" and self.config.get("show_scroll_lock", True):
                    show_notification = True
                    image_path = self.scroll_on_img if state else self.scroll_off_img

                if show_notification:
                    # Dosya var mı kontrol et
                    if not os.path.exists(image_path):
                        print(f"Uyarı: {image_path} bulunamadı. Varsayılan metin gösterimi kullanılacak.")
                        image_path = None

                    # Duruma göre metin
                    state_text = "ON" if state else "OFF"
                    notification_text = f"{key_name}: {state_text}"

                    # Yeni bildirimi göster (Ayrı bir pencere olarak)
                    notification_root = tk.Toplevel(self.root)
                    active_notification = NotificationWindow(
                        notification_root,
                        image_path,
                        notification_text,
                        theme=self.config.get("theme", "blue_dark")
                    )
        except queue.Empty:
            pass
        finally:
            # Periyodik olarak kuyruğu kontrol et
            if self.running:
                self.root.after(100, self.process_notification_queue)

    def check_key_states(self):
        """Tuş durumlarını sürekli kontrol et"""
        while self.running:
            new_caps_state = get_key_state(VK_CAPITAL)
            new_num_state = get_key_state(VK_NUMLOCK)
            new_scroll_state = get_key_state(VK_SCROLL)

            # Durum değişikliği kontrolü
            if new_caps_state != self.caps_lock_state:
                self.caps_lock_state = new_caps_state
                notification_queue.put(("Caps Lock", self.caps_lock_state))

            if new_num_state != self.num_lock_state:
                self.num_lock_state = new_num_state
                notification_queue.put(("Num Lock", self.num_lock_state))

            if new_scroll_state != self.scroll_lock_state:
                self.scroll_lock_state = new_scroll_state
                notification_queue.put(("Scroll Lock", self.scroll_lock_state))

            # Kısa bir süre bekle (CPU kullanımını azaltmak için)
            time.sleep(0.1)

    def setup_key_hooks(self):
        """Tuş olaylarını dinle"""
        keyboard.on_press_key("caps lock", lambda _: None)
        keyboard.on_press_key("num lock", lambda _: None)
        keyboard.on_press_key("scroll lock", lambda _: None)

    def run(self):
        print("Key Lock Notifier Starting...")

        # Main tkinter window - Arka planda çalışacak ve görünmeyecek
        self.root = tk.Tk()
        self.root.title("Key Lock Notifier Settings")
        self.root.withdraw()  # Ana pencereyi gizle

        # Initialize UI with blue-black theme
        self.root.configure(bg="#282828")

        # Set window size and position
        window_width = 400
        window_height = 400
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        self.root.resizable(False, False)

        # Doğrudan ayarlar penceresini gösterme kısmını kaldırın
        # self.show_settings()

        # Create system tray
        self.system_tray = SystemTrayApp(self.root, self)

        # Key states checking thread
        thread = threading.Thread(target=self.check_key_states, daemon=True)
        thread.start()

        # Process notification queue
        self.process_notification_queue()

        # Key hooks
        self.setup_key_hooks()

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.root.withdraw())

        # Start main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.running = False
        print("Uygulama kapatılıyor...")
        sys.exit(0)


if __name__ == "__main__":
    app = KeyLockNotifier()
    app.run()  # Girinti hatası düzeltildi





