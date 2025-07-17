import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit,
    QPushButton, QMessageBox, QLabel, QCheckBox, QSpinBox
)
from PyQt5.QtCore import Qt
import json
import subprocess
import socket
import os

CONFIG_FILE = "config.json"

class PhoneController(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📱 Multi-Phone ADB Controller + Embedded Screens")
        self.setGeometry(200, 100, 900, 650)
        self.devices = self.load_devices()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        ip_layout = QHBoxLayout()
        self.ip_entry = QLineEdit()
        self.ip_entry.setPlaceholderText("Enter IP:Port or Device Serial")
        ip_layout.addWidget(self.ip_entry)

        self.add_btn = QPushButton("➕ Add")
        self.auto_ip_btn = QPushButton("🔍 Auto Detect IP")
        ip_layout.addWidget(self.add_btn)
        ip_layout.addWidget(self.auto_ip_btn)

        layout.addLayout(ip_layout)

        self.device_list = QListWidget()
        layout.addWidget(self.device_list)

        self.fullscreen_checkbox = QCheckBox("🖥️ Embed in screen (no popup)")
        layout.addWidget(self.fullscreen_checkbox)

        self.scale_label = QLabel("Scale (%):")
        self.scale_spinbox = QSpinBox()
        self.scale_spinbox.setRange(10, 200)
        self.scale_spinbox.setValue(100)
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(self.scale_label)
        scale_layout.addWidget(self.scale_spinbox)
        layout.addLayout(scale_layout)

        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("🔗 Connect All")
        self.disconnect_btn = QPushButton("❌ Disconnect All")
        self.launch_btn = QPushButton("📺 Launch Screens")
        self.refresh_btn = QPushButton("🔄 Refresh Devices")
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        btn_layout.addWidget(self.launch_btn)
        btn_layout.addWidget(self.refresh_btn)

        layout.addLayout(btn_layout)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.update_list()

        self.add_btn.clicked.connect(self.add_ip)
        self.auto_ip_btn.clicked.connect(self.auto_detect_ip)
        self.connect_btn.clicked.connect(self.connect_all)
        self.disconnect_btn.clicked.connect(self.disconnect_all)
        self.launch_btn.clicked.connect(self.launch_all)
        self.refresh_btn.clicked.connect(self.refresh_connected_devices)

    def load_devices(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)["devices"]
        except:
            return []

    def save_devices(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"devices": self.devices}, f, indent=4)

    def update_list(self):
        self.device_list.clear()
        for idx, device in enumerate(self.devices, 1):
            self.device_list.addItem(f"{idx}. {device}")

    def is_valid_ip(self, ip_port):
        try:
            ip = ip_port.split(":")[0]
            socket.gethostbyname(ip)
            return True
        except socket.error:
            return False

    def add_ip(self):
        ip = self.ip_entry.text().strip()
        if not ip:
            return
        if self.is_valid_ip(ip):
            self.devices.append(ip)
            self.save_devices()
            self.update_list()
            self.status_label.setText(f"✅ Added {ip}")
        else:
            self.status_label.setText(f"❌ Invalid IP or Host: {ip}")
        self.ip_entry.clear()

    def auto_detect_ip(self):
        try:
            subprocess.call("adb tcpip 5555", shell=True)
            result = subprocess.check_output("adb shell ip route", shell=True, universal_newlines=True)
            parts = result.strip().split()
            if parts:
                ip = parts[2].strip()
                full_ip = f"{ip}:5555"
                if full_ip not in self.devices:
                    self.devices.append(full_ip)
                    self.save_devices()
                    self.update_list()
                    self.status_label.setText(f"✅ Auto-detected and saved: {full_ip}")
                else:
                    self.status_label.setText(f"ℹ️ Already exists: {full_ip}")
            else:
                self.status_label.setText("❌ Could not parse IP route.")
        except Exception as e:
            self.status_label.setText(f"❌ ADB or IP fetch error: {e}")

    def connect_all(self):
        errors = []
        for ip in self.devices:
            if self.is_valid_ip(ip):
                result = os.popen(f"adb connect {ip}").read()
                if "connected" in result or "already connected" in result:
                    continue
                else:
                    errors.append(f"{ip}: {result.strip()}")
            else:
                errors.append(f"Invalid: {ip}")
        if errors:
            self.status_label.setText("⚠️ Some connections failed.")
            QMessageBox.warning(self, "Connection Errors", "\n".join(errors))
        else:
            self.status_label.setText("✅ All devices connected.")

    def disconnect_all(self):
        os.popen("adb disconnect").read()
        self.status_label.setText("🔌 Disconnected all devices.")

    def launch_all(self):
        scale = self.scale_spinbox.value()
        embed = self.fullscreen_checkbox.isChecked()

        for idx, ip in enumerate(self.devices, 1):
            title = f"Phone {idx} - {ip}"
            cmd = f'start scrcpy -s {ip} --window-title "{title}" --turn-screen-on --stay-awake --max-size {scale*10}'
            if embed:
                cmd += " --window-borderless"
            os.system(cmd)

        self.status_label.setText("📺 Launched all devices.")

    def refresh_connected_devices(self):
        try:
            output = subprocess.check_output("adb devices", shell=True, universal_newlines=True)
            lines = output.strip().split("\n")[1:]
            connected = [line.split()[0] for line in lines if "device" in line and not "offline" in line]
            self.status_label.setText(f"🔄 Connected: {', '.join(connected) if connected else 'None'}")
            QMessageBox.information(self, "Connected Devices", "\n".join(connected) if connected else "No connected devices.")
        except Exception as e:
            self.status_label.setText(f"❌ Refresh failed: {e}")

# Run App
app = QApplication(sys.argv)
window = PhoneController()
window.show()
sys.exit(app.exec_())
