import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit,
    QPushButton, QMessageBox, QInputDialog, QLabel, QMenu
)
from PyQt5.QtCore import Qt
import json
import subprocess

CONFIG_FILE = "config.json"
SCRCPY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scrcpy")
ADB_PATH = os.path.join(SCRCPY_DIR, "adb.exe")
SCRCPY_PATH = os.path.join(SCRCPY_DIR, "scrcpy.exe")

class PhoneController(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📱 Multi-Phone ADB Controller")
        self.setGeometry(200, 100, 850, 600)
        self.devices = self.load_devices()
        self.init_ui()
        self.update_list()
        # Start ADB server
        try:
            subprocess.run([ADB_PATH, "start-server"], check=True)
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, "ADB Error", f"Failed to start ADB server: {e}")

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Top layout for adding devices ---
        ip_layout = QHBoxLayout()
        self.ip_entry = QLineEdit()
        self.ip_entry.setPlaceholderText("Enter IP:Port or Device Serial")
        ip_layout.addWidget(self.ip_entry)

        self.add_btn = QPushButton("➕ Add")
        self.auto_ip_btn = QPushButton("🔍 Auto Detect IP")
        ip_layout.addWidget(self.add_btn)
        ip_layout.addWidget(self.auto_ip_btn)
        layout.addLayout(ip_layout)

        # --- Device list ---
        self.device_list = QListWidget()
        self.device_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.device_list.customContextMenuRequested.connect(self.show_device_context_menu)
        layout.addWidget(self.device_list)

        # --- Main action buttons ---
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("🔗 Connect All")
        self.disconnect_btn = QPushButton("❌ Disconnect All")
        self.launch_btn = QPushButton("📺 Launch All Screens")
        self.refresh_btn = QPushButton("🔄 Refresh List")
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        btn_layout.addWidget(self.launch_btn)
        btn_layout.addWidget(self.refresh_btn)
        layout.addLayout(btn_layout)

        # --- Status label ---
        self.status_label = QLabel("Welcome!")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # --- Connect signals ---
        self.add_btn.clicked.connect(self.add_device)
        self.ip_entry.returnPressed.connect(self.add_device)
        self.auto_ip_btn.clicked.connect(self.auto_detect_ip)
        self.connect_btn.clicked.connect(self.connect_all)
        self.disconnect_btn.clicked.connect(self.disconnect_all)
        self.launch_btn.clicked.connect(self.launch_all)
        self.refresh_btn.clicked.connect(self.update_list)

    def load_devices(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f).get("devices", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_devices(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"devices": self.devices}, f, indent=4)

    def get_connected_devices(self):
        try:
            output = subprocess.check_output([ADB_PATH, "devices"], universal_newlines=True, stderr=subprocess.PIPE)
            lines = output.strip().split("\n")[1:]
            return [line.split()[0] for line in lines if "device" in line.split()]
        except subprocess.CalledProcessError as e:
            self.status_label.setText(f"❌ ADB error: {e.stderr.strip()}")
            return []
        except Exception:
            return []

    def update_list(self):
        self.device_list.clear()
        connected_devices = self.get_connected_devices()
        for idx, device in enumerate(self.devices, 1):
            status = "✅" if device in connected_devices else "❌"
            self.device_list.addItem(f"{idx}. {device}  {status}")

    def add_device(self):
        device_id = self.ip_entry.text().strip()
        if not device_id:
            return
        if device_id not in self.devices:
            self.devices.append(device_id)
            self.save_devices()
            self.update_list()
            self.status_label.setText(f"✅ Added {device_id}")
        else:
            self.status_label.setText(f"ℹ️ Already exists: {device_id}")
        self.ip_entry.clear()

    def auto_detect_ip(self):
        self.status_label.setText("🔍 Detecting USB device...")
        QApplication.processEvents() 
        try:
            output = subprocess.check_output([ADB_PATH, "devices"], universal_newlines=True)
            lines = output.strip().split("\n")[1:]
            usb_devices = [line.split()[0] for line in lines if "device" in line and ":" not in line.split()[0]]

            if not usb_devices:
                self.status_label.setText("❌ No USB device detected.")
                return
            if len(usb_devices) > 1:
                self.status_label.setText("❌ Multiple USB devices. Please connect only one.")
                return
            
            serial = usb_devices[0]
            self.status_label.setText(f"Found {serial}. Setting to TCP/IP mode...")
            QApplication.processEvents()
            
            subprocess.run([ADB_PATH, "-s", serial, "tcpip", "5555"], check=True)
            
            self.status_label.setText(f"Fetching IP address for {serial}...")
            QApplication.processEvents()

            result = subprocess.check_output([ADB_PATH, "-s", serial, "shell", "ip", "addr", "show", "wlan0"], universal_newlines=True)
            ip_address = None
            for line in result.splitlines():
                if "inet" in line:
                    parts = line.strip().split()
                    if len(parts) > 1:
                        ip_address = parts[1].split('/')[0]
                        break
            
            if ip_address:
                full_ip = f"{ip_address}:5555"
                if full_ip not in self.devices:
                    self.devices.append(full_ip)
                    self.save_devices()
                    self.update_list()
                    self.status_label.setText(f"✅ Auto-detected and saved: {full_ip}")
                else:
                    self.status_label.setText(f"ℹ️ Already exists: {full_ip}")
            else:
                self.status_label.setText("❌ Could not determine IP address.")
        except subprocess.CalledProcessError as e:
            self.status_label.setText(f"❌ ADB command failed: {e}")
        except Exception as e:
            self.status_label.setText(f"❌ Error: {e}")

    def connect_all(self):
        errors = []
        for ip in self.devices:
            try:
                proc = subprocess.run([ADB_PATH, "connect", ip], capture_output=True, text=True, timeout=5)
                output = proc.stdout.strip()
                if "connected to" in output or "already connected" in output:
                    continue
                else:
                    errors.append(f"{ip}: {output or proc.stderr.strip()}")
            except subprocess.TimeoutExpired:
                errors.append(f"{ip}: Connection timed out")
        
        self.update_list()
        if errors:
            self.status_label.setText("⚠️ Some connections failed.")
            QMessageBox.warning(self, "Connection Errors", "\n".join(errors))
        else:
            self.status_label.setText("✅ All devices connected successfully.")

    def disconnect_all(self):
        subprocess.run([ADB_PATH, "disconnect"], capture_output=True)
        self.update_list()
        self.status_label.setText("🔌 Disconnected all devices.")

    def launch_all(self):
        for idx, ip in enumerate(self.devices, 1):
            self.launch_device(ip, idx)
        self.status_label.setText("📺 Launched screens for all devices.")

    # --- Context Menu and Single Device Actions ---

    def show_device_context_menu(self, position):
        item = self.device_list.itemAt(position)
        if not item:
            return
        
        device_id = item.text().split(' ')[1]

        menu = QMenu()
        connect_action = menu.addAction("🔗 Connect")
        disconnect_action = menu.addAction("❌ Disconnect")
        launch_action = menu.addAction("📺 Launch Screen")
        menu.addSeparator()
        remove_action = menu.addAction("🗑️ Remove")
        
        action = menu.exec_(self.device_list.mapToGlobal(position))

        if action == connect_action:
            self.connect_device(device_id)
        elif action == disconnect_action:
            self.disconnect_device(device_id)
        elif action == launch_action:
            self.launch_device(device_id)
        elif action == remove_action:
            self.remove_device(device_id)

    def connect_device(self, device):
        try:
            proc = subprocess.run([ADB_PATH, "connect", device], capture_output=True, text=True, timeout=5)
            output = proc.stdout.strip()
            if "connected to" in output or "already connected" in output:
                self.status_label.setText(f"✅ Connected to {device}")
            else:
                 self.status_label.setText(f"❌ Failed to connect: {output or proc.stderr.strip()}")
        except subprocess.TimeoutExpired:
            self.status_label.setText(f"❌ Connection to {device} timed out.")
        self.update_list()

    def disconnect_device(self, device):
        subprocess.run([ADB_PATH, "disconnect", device], capture_output=True)
        self.status_label.setText(f"🔌 Disconnected {device}")
        self.update_list()

    def launch_device(self, device, index=None):
        if index is None:
            try:
                index = self.devices.index(device) + 1
            except ValueError:
                self.status_label.setText(f"❌ Device {device} not in list.")
                return
        title = f"Phone {index} - {device}"
        command = [SCRCPY_PATH, "-s", device, "--window-title", title]
        subprocess.Popen(command)
        self.status_label.setText(f"📺 Launched screen for {device}")

    def remove_device(self, device):
        reply = QMessageBox.question(self, 'Remove Device', f"Are you sure you want to remove {device}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if device in self.devices:
                self.devices.remove(device)
                self.save_devices()
                self.update_list()
                self.status_label.setText(f"🗑️ Removed {device}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhoneController()
    window.show()
    sys.exit(app.exec_())

