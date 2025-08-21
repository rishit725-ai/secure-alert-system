# server1.py (Secure TCP with parallel SSL channels)
import socket
import ssl
import threading
from datetime import datetime

server_id = "SRV-001"
data_port = 12345
control_port = 12346
host = '0.0.0.0'  # Listen on all interfaces

# SSL certificate and key paths
CERT_FILE = "server_cert.pem"
KEY_FILE = "server_key.pem"

topics = ["weather", "finance", "news"]

def handle_data_connection(connstream, addr):
    print(f"📡 Data connection from {addr}")
    while True:
        try:
            raw_input_msg = input("Alert: ")
            topic, msg = raw_input_msg.split(":", 1)
            topic = topic.strip().lower()

            if topic not in topics:
                print("❌ Invalid topic!")
                continue

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            final_message = f"DATA::{server_id}::[{timestamp}] [{topic.upper()}] {msg.strip()}"
            connstream.sendall(final_message.encode())
            print("📢 Alert sent!")

            # Notify control channel
            for ctrl in control_connections:
                try:
                    ctrl.sendall(
                        f"CONTROL::{server_id}::Alert on topic '{topic}' sent at {timestamp}".encode()
                    )
                except:
                    pass

        except Exception as e:
            print("Error:", e)
            break
    connstream.close()

def handle_control_connection(connstream, addr):
    print(f"⚙  Control connection from {addr}")
    control_connections.append(connstream)

# Create SSL context
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

# TCP sockets (one for data, one for control)
data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
data_sock.bind((host, data_port))
data_sock.listen(5)

control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
control_sock.bind((host, control_port))
control_sock.listen(5)

control_connections = []

print(f"✅ Secure Server1 (ID: {server_id}) running with parallel SSL channels")
print("Available topics:", topics)
print(f"Data Port: {data_port}, Control Port: {control_port}")

while True:
    data_conn, data_addr = data_sock.accept()
    data_stream = context.wrap_socket(data_conn, server_side=True)
    threading.Thread(target=handle_data_connection, args=(data_stream, data_addr), daemon=True).start()

    ctrl_conn, ctrl_addr = control_sock.accept()
    ctrl_stream = context.wrap_socket(ctrl_conn, server_side=True)
    threading.Thread(target=handle_control_connection, args=(ctrl_stream, ctrl_addr), daemon=True).start()