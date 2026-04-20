"""
Levanta el servidor FastAPI con un túnel público usando localhost.run.

No requiere cuenta ni instalación — usa SSH que ya viene en Windows 10/11.

Uso:
    C:/Users/Iyuqui/AppData/Local/Programs/Python/Python313/python.exe -m backend.tunnel
"""

import re
import subprocess
import threading
import uvicorn

PORT = 8000


def start_server():
    uvicorn.run("backend.main:app", host="127.0.0.1", port=PORT, log_level="warning")


if __name__ == "__main__":
    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()

    print("\nAbriendo túnel público (localhost.run)...")
    print("Espera unos segundos...\n")

    proc = subprocess.Popen(
        [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=30",
            "-o", "ServerAliveCountMax=3",
            "-R", f"80:localhost:{PORT}",
            "nokey@localhost.run",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    url_publica = None
    for line in proc.stdout:
        print(line, end="")
        # localhost.run genera URLs con el dominio lhr.life
        match = re.search(r"https://[a-zA-Z0-9\-]+\.lhr\.life", line)
        if match and not url_publica:
            url_publica = match.group(0)
            print("\n" + "═" * 55)
            print("  Túnel activo — comparte esta URL con el frontend")
            print("═" * 55)
            print(f"  URL pública  : {url_publica}")
            print(f"  Endpoint POST: {url_publica}/auth/register")
            print(f"  Documentación: {url_publica}/docs")
            print("═" * 55)
            print("  Presiona Ctrl+C para detener\n")

    proc.wait()
