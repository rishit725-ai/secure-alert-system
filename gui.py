import sys
import socket
import ssl
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
    QVBoxLayout, QPushButton, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

DATA_PORT = 12345
CONTROL_PORT = 12346
SERVER_IP = '127.0.0.1'  # Change this to server's IP on demo
CERT_FILE = 'server_cert.pem'  # Use server's certificate to validate

class SecureAlertClient(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Secure Alert Client (SSL)")
        self.setFixedSize(650, 500)
        self.setStyleSheet("background-color: #f2f2f2;")

        self.topics = []
        self.running = False

        self.title = QLabel("🔒 Secure Alert Client (SSL)")
        self.title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)

        self.topic_label = QLabel("Subscribe to Topics (comma-separated):")
        self.topic_label.setFont(QFont("Segoe UI", 11))

        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("e.g. weather, finance")
        self.topic_input.setFont(QFont("Segoe UI", 10))
        self.topic_input.setStyleSheet("padding: 8px;")

        self.subscribe_button = QPushButton("Subscribe")
        self.subscribe_button.setFont(QFont("Segoe UI", 10))
        self.subscribe_button.setStyleSheet(
            "padding: 8px; background-color: #007ACC; color: white; border-radius: 4px;"
        )
        self.subscribe_button.clicked.connect(self.subscribe)

        self.alert_box = QTextEdit()
        self.alert_box.setReadOnly(True)
        self.alert_box.setFont(QFont("Consolas", 10))
        self.alert_box.setStyleSheet("background-color: white; padding: 10px;")

        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addSpacing(10)
        layout.addWidget(self.topic_label)
        layout.addWidget(self.topic_input)
        layout.addWidget(self.subscribe_button)
        layout.addSpacing(10)
        layout.addWidget(self.alert_box)

        self.setLayout(layout)

        self.data_socket = None
        self.control_socket = None

    def subscribe(self):
        user_input = self.topic_input.text()
        if not user_input.strip():
            QMessageBox.warning(self, "Input Required", "Please enter at least one topic.")
            return

        self.topics = [t.strip().lower() for t in user_input.split(',')]
        self.alert_box.append(f"✅ Subscribed to: {', '.join(self.topics)}\n")
        self.subscribe_button.setEnabled(False)
        self.topic_input.setEnabled(False)

        # Setup secure sockets
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # For demo purposes

        # Connect data socket
        raw_data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_data_socket.connect((SERVER_IP, DATA_PORT))
        self.data_socket = context.wrap_socket(raw_data_socket, server_hostname=SERVER_IP)

        # Connect control socket
        raw_control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_control_socket.connect((SERVER_IP, CONTROL_PORT))
        self.control_socket = context.wrap_socket(raw_control_socket, server_hostname=SERVER_IP)

        self.running = True

        threading.Thread(target=self.listen_data_channel, daemon=True).start()
        threading.Thread(target=self.listen_control_channel, daemon=True).start()

    def listen_data_channel(self):
        while self.running:
            try:
                data = self.data_socket.recv(2048).decode()
                if any(f"[{topic.upper()}]" in data for topic in self.topics):
                    self.display_alert(data)
                    self.log_alert(data)
            except Exception as e:
                print("Data channel error:", e)
                break

    def listen_control_channel(self):
        while self.running:
            try:
                msg = self.control_socket.recv(1024).decode()
                self.alert_box.append(f"ℹ {msg}")
            except Exception as e:
                print("Control channel error:", e)
                break

    def display_alert(self, message):
        self.alert_box.append(f"{message}")

    def log_alert(self, message):
        with open("secure_alerts_log.txt", "a") as f:
            f.write(message + "\n")

    def closeEvent(self, event):
        self.running = False
        try:
            if self.data_socket:
                self.data_socket.close()
            if self.control_socket:
                self.control_socket.close()
        except:
            pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SecureAlertClient()
    window.show()
    sys.exit(app.exec_())
 