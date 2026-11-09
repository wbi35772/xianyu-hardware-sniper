import asyncio
import ipaddress
import logging
import subprocess
import sys
from pathlib import Path

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8086
TARGET_PORT = 8086
DISTRO = "Ubuntu-24.04"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "windows_wsl_proxy.log"

_target_ip = None


def resolve_wsl_ip():
    commands = [
        ["wsl.exe", "--", "hostname", "-I"],
        ["wsl.exe", "-d", DISTRO, "--", "hostname", "-I"],
    ]
    for command in commands:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                timeout=15,
                check=False,
            )
        except Exception:
            continue
        if result.returncode != 0:
            continue
        text = result.stdout.decode("utf-8", errors="ignore")
        for token in text.split():
            try:
                address = ipaddress.ip_address(token)
            except ValueError:
                continue
            if address.version == 4 and not address.is_loopback:
                return str(address)
    return None


async def refresh_target():
    global _target_ip
    address = await asyncio.to_thread(resolve_wsl_ip)
    if address:
        if address != _target_ip:
            logging.info("WSL target changed to %s:%s", address, TARGET_PORT)
        _target_ip = address
    return _target_ip


async def refresh_loop():
    while True:
        await refresh_target()
        await asyncio.sleep(30)


async def pipe(reader, writer):
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (ConnectionError, asyncio.CancelledError):
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def handle_client(client_reader, client_writer):
    target_ip = _target_ip or await refresh_target()
    remote_writer = None
    remote_reader = None
    if target_ip:
        for attempt in range(2):
            try:
                remote_reader, remote_writer = await asyncio.wait_for(
                    asyncio.open_connection(target_ip, TARGET_PORT),
                    timeout=10,
                )
                break
            except Exception:
                if attempt == 0:
                    target_ip = await refresh_target()
        if remote_reader is None:
            logging.warning("Cannot connect to WSL target %s:%s", target_ip, TARGET_PORT)
    if remote_reader is None:
        try:
            client_writer.close()
        except Exception:
            pass
        return
    await asyncio.gather(
        pipe(client_reader, remote_writer),
        pipe(remote_reader, client_writer),
    )


async def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(LOG_FILE),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )
    await refresh_target()
    asyncio.create_task(refresh_loop())
    try:
        server = await asyncio.start_server(handle_client, LISTEN_HOST, LISTEN_PORT)
    except OSError as exc:
        logging.error("Cannot listen on %s:%s: %s", LISTEN_HOST, LISTEN_PORT, exc)
        return 1
    logging.info("Listening on http://%s:%s -> WSL:%s", LISTEN_HOST, LISTEN_PORT, TARGET_PORT)
    async with server:
        await server.serve_forever()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        sys.exit(0)
