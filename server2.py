import socket
import ssl
from datetime import datetime
import threading

server_id = "SRV-002"
data_port = 12347
control_port = 12348
broadcast_ip = '<broadcast>'  # Change this if necessary for actual deployment

# SSL context setup
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile='server_cert.pem', keyfile='server_key.pem')  # Server's SSL cert and key
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE  # Disable certificate verification (for demo)

# Data socket (alerts)
data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
data_socket.bind(('', data_port))
data_socket.listen(5)  # Listen for up to 5 connections

# Control socket (handshake, status, etc.)
control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
control_socket.bind(('', control_port))
control_socket.listen(5)  # Listen for up to 5 connections

topics = ["weather", "finance", "news"]

print(f"✅ Server2 (ID: {server_id}) running with parallel channels (SSL)")
print("Available topics:", topics)
print("Enter alerts as: topic:message")

def handle_data_connection(client_socket):
    while True:
        try:
            raw_input_msg = input("Alert: ")
            topic, msg = raw_input_msg.split(":", 1)
            topic = topic.strip().lower()

            if topic not in topics:
                print("❌ Invalid topic!")
                continue

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alert_message = f"DATA::{server_id}::[{timestamp}] [{topic.upper()}] {msg.strip()}"
            client_socket.sendall(alert_message.encode())
            print("📢 Alert sent!")

        except Exception as e:
            print("Error:", e)
            break

def handle_control_connection(client_socket):
    while True:
        try:
            control_msg = f"CONTROL::{server_id}::Server2 is running and available"
            client_socket.sendall(control_msg.encode())
        except Exception as e:
            print("Control connection error:", e)
            break

while True:
    try:
        # Accept data connections
        data_client_socket, addr = data_socket.accept()
        print(f"🔒 Data connection established with {addr}")
        data_client_socket = context.wrap_socket(data_client_socket, server_side=True)
        threading.Thread(target=handle_data_connection, args=(data_client_socket,), daemon=True).start()

        # Accept control connections
        control_client_socket, addr = control_socket.accept()
        print(f"🔒 Control connection established with {addr}")
        control_client_socket = context.wrap_socket(control_client_socket, server_side=True)
        threading.Thread(target=handle_control_connection, args=(control_client_socket,), daemon=True).start()

    except Exception as e:
        print("Error:", e)
        break