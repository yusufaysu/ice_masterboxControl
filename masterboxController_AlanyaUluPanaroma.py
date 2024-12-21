##############################################################
# Author   : Yusuf AYSU
# E-mail   : yusuf.aaysu@gmail.com
# Company  : iCe Akıllı Ev ve Ofis Sistemleri
# Project  : Alanya Kontrol Paneli
# File     : Alanya_guvenlik.py
# Created  : 24.11.2024
# Updated  : 14.12.2024
##############################################################

import customtkinter as ctk
import paho.mqtt.client as mqtt
import json
import time
import csv
import threading
import numpy as np
import time

# MQTT Sunucu Ayarları
MQTT_HOST = "icemqtt.com.tr"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 5

import os
import sys

def resource_path(relative_path):
    """
    Yazılımı Windowsa portlamak için pyinstallerın ve exe dosyasının dosya yolu,
    linux ve macos dan farklı olduğu için işletim sisteminden direk belirtilen
    dosyanın absolute pathini döndüren bir fonksyon.
    İlgili link -> https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
    """
    try:
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# CSV Dosya Yolu
CSV_FILE_PATH = "./Table.csv"

import sounddevice as sd
import numpy as np

def play_alarm_sound(duration=1.0, freq=440, sample_rate=44100):
    """
    duration (float): Alarmın süresi (saniye cinsinden). Varsayılan: 1.0
    freq (float): Alarm frekansı (Hz cinsinden). Varsayılan: 440 Hz (A4 notası)
    sample_rate (int): Örnekleme hızı. Varsayılan: 44100
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio_signal = np.sin(2 * np.pi * freq * t)

    sd.play(audio_signal, sample_rate)
    sd.wait()  # Sesin bitmesini bekle

def read_licenses_as_3d_array(filename):
    """
    CSV dosyasından daire, lisans ve TİP bilgilerini dön.
    """
    daires = []
    licenses = []
    types = []
    
    with open(filename, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            daires.append(row["Daire"])
            licenses.append(row["Lisans"])
            types.append(row["TİP"])
    
    return [daires, licenses, types]

def getLisansFromTopic(topic):
    """
    Gelen MQTT topic'inden lisansı dön.
    Örnek:
    Input: "/02.02.660D87B9.605F/devSender"
    Output: "02.02.660D87B9.605F"
    """
    try:
        # Topic'i '/' ile ayır
        parts = topic.split('/')
        
        # Lisans bilgisi ikinci sırada
        if len(parts) > 1:
            return parts[1]
        else:
            raise ValueError("Geçersiz topic formatı!")
    except Exception:
        return None

class Client:
    """
    Client object
    """
    def __init__(self, app, host=MQTT_HOST, port=MQTT_PORT, keepalive=MQTT_KEEPALIVE):
        self.app = app
        self.host = host
        self.port = port
        self.keepalive = keepalive
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._disconnected_logged = False

        # MQTT olay işleyicilerini tanımla
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def connect(self):
        try:
            self.client.connect(self.host, self.port, self.keepalive)
            self.client.loop_start()
            self.app.show_log("Sunucuya bağlanıyor...", "#2e526b")
        except Exception as e:
            self.app.show_log(f"Sunucu bağlantı hatası: {e}", "grey")
            self.app.toggle_status_light(1)

    def disconnect(self):
        if self.client.is_connected():
            self.client.loop_stop()
            self.client.disconnect()

    def on_connect(self, client, userdata, flags, rc, atribiutes):
        if rc == 0:
            self.app.show_log("Sunucu bağlantısı başarılı!", "#2e526b")
            self.app.toggle_status_light(0)
            self._disconnected_logged = False
        else:
            self.app.show_log(f"Sunucu bağlantısı başarısız, Kod: {rc}", "grey")
            self.app.toggle_status_light(1)

    def on_disconnect(self, client, userdata, rc, flags, attributes):
        if not self._disconnected_logged:
            if rc == 0:
                self.app.show_log("Sunucu bağlantısı düzgün şekilde kapatıldı.", "grey")
            else:
                self.app.show_log(f"Sunucu bağlantısı beklenmedik şekilde kesildi (Kod: {rc}).", "grey")
            self.app.toggle_status_light(1)
            self._disconnected_logged = True

    def on_message(self, client, userdata, message):
        try:
            topic = message.topic
            payload = message.payload.decode('utf-8')
            data = json.loads(payload)

            if "durum" in data and 'irval' in data["durum"]:
                if data["durum"]["irval"] == "alarm":
                    app.open_toplevel(app.get_daire_no_from_licanse(getLisansFromTopic(topic)), data["durum"]["ircom"])

        except UnicodeDecodeError as e:
            self.app.show_log(f"Veri decode hatası: {e}. Payload: {payload[:100]}...", "orange")
        except json.JSONDecodeError as e:
            self.app.show_log(f"Geçersiz JSON formatı! Hata: {e}", "orange")
        except Exception as e:
            pass

    def subscribe_to_all_topics(self):
        """
        csv dosyası içerisindeki lisansların devSender kanalına abone olur
        """
        for license_id in self.app.licenses_daire_no[1]:
            topic = f"/{license_id}/devSender"
            try:
                self.client.subscribe(topic)
            except Exception as e:
                self.app.show_log(f"Kanal aboneliği sırasında hata oluştu -> {topic}, Hata: {e}", "red")

class App(ctk.CTk):
    """
    UI object
    """
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title("iCe Duyuru Paneli")
        self.client = Client(app=self)
        self.licenses_daire_no = read_licenses_as_3d_array(CSV_FILE_PATH)
        self.toplevel_window = None
        self.setup_ui()
        self.client.connect()
        self.client.subscribe_to_all_topics()

    def setup_ui(self):
        window_width, window_height = 800, 520
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (screen_width - window_width) // 2, (screen_height - window_height) // 2
        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

        frame = ctk.CTkFrame(master=self)
        frame.pack(pady=0, padx=0, fill="both", expand=True)

        self.status_light = ctk.CTkLabel(master=frame, width=2, height=20, corner_radius=10)
        self.status_light.place(x=20, y=25)

        label = ctk.CTkLabel(master=frame, text="iCe Kontrol Paneli", font=("Roboto Mono", 24))
        label.pack(pady=24, padx=10)

        self.option_menu = ctk.CTkOptionMenu(
            master=frame, 
            values=self.licenses_daire_no[0], 
            width=300,
            fg_color="grey",
            dropdown_hover_color="grey",
            dropdown_text_color="grey"
        )
        self.option_menu.pack(pady=24, padx=10)

        button_frame = ctk.CTkFrame(master=frame)
        button_frame.pack(pady=24, padx=10)

        self.su_ac_button = ctk.CTkButton(master=button_frame, text="Suyu Aç", height=32, command=lambda: self.on_button_click(1))
        self.su_ac_button.grid(row=0, column=0, padx=10, pady=10)

        self.su_kapat_button = ctk.CTkButton(master=button_frame, text="Suyu Kapat", fg_color="grey", height=32, command=lambda:self.on_button_click(2))
        self.su_kapat_button.grid(row=0, column=1, padx=10, pady=10)

        self.elektrik_ac_button = ctk.CTkButton(master=button_frame, text="Elektrik Aç", height=32, command=lambda:self.on_button_click(3))
        self.elektrik_ac_button.grid(row=0, column=2, padx=10, pady=10)

        self.elektrik_kapat_button = ctk.CTkButton(master=button_frame, text="Elektrik Kapat", fg_color="grey", height=32, command=lambda:self.on_button_click(4))
        self.elektrik_kapat_button.grid(row=0, column=3, padx=10, pady=10)

        self.log_frame = ctk.CTkFrame(master=frame)
        self.log_frame.pack(pady=12, padx=10, fill="both", expand=True)

        self.log_text = ctk.CTkTextbox(master=self.log_frame, font=("Roboto Mono", 12), wrap="word", state="disabled")
        self.log_text.pack(side="left", fill="both", expand=True)

    def show_log(self, log_message, color):
        log_message_with_time = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {log_message}"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", log_message_with_time + "\n", color)
        self.log_text.configure(state="disabled")
        self.log_text.see("end")
        self.log_text.tag_config(color, foreground=color)

    def get_licanse_from_daire_no(self, daire_no):
        return self.licenses_daire_no[1][self.licenses_daire_no[0].index(daire_no)]
    
    def get_daire_no_from_licanse(self, licanse):
        return self.licenses_daire_no[0][self.licenses_daire_no[1].index(licanse)]

    def get_type_from_daire_no(self, daire_no):
        return self.licenses_daire_no[2][self.licenses_daire_no[0].index(daire_no)]

    def toggle_status_light(self, connection_status):
        if connection_status == 0:
            self.status_light.configure(fg_color="#2e526b")
            self.status_light.configure(text="Online")
        else:
            self.status_light.configure(fg_color="grey")
            self.status_light.configure(text="Offline")

    def disable_buttons_temporarily(self, buttons, duration_ms):
        """
        Gelen butonları disable et.
        """
        for button in buttons:
            button.configure(state="disabled")
        self.after(duration_ms, lambda: [button.configure(state="normal") for button in buttons])
    
    def open_toplevel(self, daire_no, ircom):
        """
        Dinamik olarak bir ToplevelWindow oluşturur ve açık olduğu sürece alarm çalar.
        """
        alarm_event = threading.Event()

        def play_alarm():
            """Alarm sesini çalmak için bir döngü."""
            while not alarm_event.is_set():
                play_alarm_sound(duration=0.3, freq=5000)
                time.sleep(0.1)

        def stop_alarm():
            """Alarmı durdurur ve thread'i sonlandırır."""
            alarm_event.set()

        app.show_log(f"Daire no -> {daire_no} | Alarm!!! | Alarm sebebi -> {ircom}", "red")
        
        toplevel_window = ctk.CTkToplevel(self)
        toplevel_window.geometry("400x200")
        toplevel_window.title(f"Alarm!!!")

        # Alarmı başlatmak için bir thread
        alarm_thread = threading.Thread(target=play_alarm, daemon=True)
        alarm_thread.start()

        label = ctk.CTkLabel(toplevel_window, text=f"Daire: {daire_no}\nAlarm sebebi: {ircom}", font=("Roboto Mono", 16))
        label.pack(padx=20, pady=20)

        close_button = ctk.CTkButton(
            toplevel_window, 
            text="Kapat", 
            command=lambda: (stop_alarm(), toplevel_window.destroy())  # Alarmı durdur ve pencereyi kapat
        )
        close_button.pack(pady=20)
        
        # Toplevel OS in kendi penceresinden kapatılırsa
        toplevel_window.protocol("WM_DELETE_WINDOW", lambda: (stop_alarm(), toplevel_window.destroy()))

    def publish_message(self, daire_no, com_id, stat_value):
        topic = f"/{daire_no}/devListener"
        payload = f"""{{"com":"event","id":{com_id},"durum":{{"stat":{stat_value}}}}}"""
        result = self.client.client.publish(topic, payload)
        return result

    def on_button_click(self, button_type):
        if button_type == 1:  # Su Aç
            self.show_log(f"Daire -> {self.option_menu.get()} Lisans -> {self.get_licanse_from_daire_no(self.option_menu.get())} | Su Açıldı.", "#2e526b")
            #anakutu ise
            if self.get_type_from_daire_no(self.option_menu.get()) == "1":
                result = self.publish_message(self.get_licanse_from_daire_no(self.option_menu.get()), 6, "false")
            #ekkutu ise
            else:
                result = self.publish_message(self.get_licanse_from_daire_no(self.option_menu.get()), 15, "false")

        elif button_type == 2:  # Su Kapat
            self.show_log(f"Daire -> {self.option_menu.get()} Lisans -> {self.get_licanse_from_daire_no(self.option_menu.get())} | Su Kapatıldı.", "grey")
            #anakutu ise
            if self.get_type_from_daire_no(self.option_menu.get()) == "1":
                result = self.publish_message(self.get_licanse_from_daire_no(self.option_menu.get()), 6, "true")
            #ekkutu ise
            else:
                result = self.publish_message(self.get_licanse_from_daire_no(self.option_menu.get()), 15, "true")
        
        elif button_type == 3:
            self.show_log(f"Daire -> {self.option_menu.get()} Lisans -> {self.get_licanse_from_daire_no(self.option_menu.get())} | Elektrik Açıldı.", "#2e526b")
            #anakutu ise
            if self.get_type_from_daire_no(self.option_menu.get()) == "1":
                result = self.publish_message(self.get_licanse_from_daire_no(self.option_menu.get()), 7, "false")
            #ekkutu ise
            else:
                result = self.publish_message(self.get_licanse_from_daire_no(self.option_menu.get()), 16, "false")

        elif button_type == 4:
            self.show_log(f"Daire -> {self.option_menu.get()} Lisans -> {self.get_licanse_from_daire_no(self.option_menu.get())} | Elektrik Kapatıldı.", "grey")
            #anakutu ise
            if self.get_type_from_daire_no(self.option_menu.get()) == "1":
                result = self.publish_message(self.get_licanse_from_daire_no(self.option_menu.get()), 7, "true")
            #ekkutu ise
            else:
                result = self.publish_message(self.get_licanse_from_daire_no(self.option_menu.get()), 16, "true")
        
        if result[0] != 0:
            self.show_log(f"Server Publish failed with code: {result[0]}", "red")

        if button_type == 1 or button_type == 2:
            self.disable_buttons_temporarily([self.su_ac_button, self.su_kapat_button], 30000)
        elif button_type == 3 or button_type == 4:
            self.disable_buttons_temporarily([self.elektrik_ac_button, self.elektrik_kapat_button], 2000)

if __name__ == "__main__":
    app = App()
    app.mainloop()
