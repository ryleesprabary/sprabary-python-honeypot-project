!/usr/bin/env python3
# src/listener.py  -- Mock SSH banner listener with JSONL logging
import socket, time, json, pathlib, signal, sys
from datetime import datetime

# CONFIG - change PORT below or via env var HP_PORT
HOST = "0.0.0.0"
PORT = int(__import__('os').environ.get("HP_PORT", "2222"))  # default 2222 (sa>
BANNER = b"SSH-2.0-OpenSSH_8.9p1 Ubuntu-3\r\n"
LOG_FILE = pathlib.Path("logs/connections.jsonl")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

ACCEPT_TIMEOUT = 1.0
CONN_TIMEOUT = 5.0
MAX_RECV_BYTES = 1024

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def log_connection(addr, banner_sent, client_banner=None):
    entry = {
        "ts": now_iso(),
        "src_ip": addr[0],
        "src_port": addr[1],
        "banner_sent": banner_sent.decode(errors="ignore").strip(),
        "client_banner": client_banner.decode(errors="ignore").strip() if clien>
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def handle_client(conn, addr):
    try:
        conn.settimeout(CONN_TIMEOUT)
        conn.sendall(BANNER)
        try:
            data = conn.recv(MAX_RECV_BYTES)
            client_banner = data or None
      except socket.timeout:
            client_banner = None
        log_connection(addr, BANNER, client_banner)
    except Exception as e:
        print(f"[!] Error handling {addr}: {e}")
    finally:
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        conn.close()

def run(host=HOST, port=PORT):
    print(f"[+] Starting mock SSH listener on {host}:{port} (banner: {BANNER.de>
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(50)
        s.settimeout(ACCEPT_TIMEOUT)
        try:
            while True:
                try:
                    conn, addr = s.accept()
                except socket.timeout:
                    continue
                print(f"[+] Connection from {addr[0]}:{addr[1]}")
                handle_client(conn, addr)
        except KeyboardInterrupt:
            print("\n[+] Shutting down listener.")
        except Exception as e:
            print(f"[!] Listener error: {e}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s,f: sys.exit(0))
    run()
