import ipaddress
import json
import subprocess
from pathlib import Path
from typing import Any

from app.config import settings


class WireGuardError(RuntimeError):
    pass


def _run(command: list[str], *, input_text: str | None = None) -> str:
    try:
        result = subprocess.run(
            command,
            input=input_text,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise WireGuardError(f"Command not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        stdout = (exc.stdout or "").strip()
        details = stderr or stdout or f"exit code {exc.returncode}"
        raise WireGuardError(f"Command failed: {' '.join(command)}: {details}") from exc

    return result.stdout.strip()


def generate_private_key() -> str:
    return _run(["wg", "genkey"])


def generate_public_key(private_key: str) -> str:
    return _run(["wg", "pubkey"], input_text=private_key)


def _peer_state_dir() -> Path:
    path = Path(settings.wg_state_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _peer_state_path(peer_id: str) -> Path:
    return _peer_state_dir() / f"{peer_id}.json"


def _load_peer_state(peer_id: str) -> dict[str, Any] | None:
    path = _peer_state_path(peer_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save_peer_state(peer_id: str, data: dict[str, Any]) -> None:
    _peer_state_path(peer_id).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _delete_peer_state(peer_id: str) -> None:
    _peer_state_path(peer_id).unlink(missing_ok=True)


def _used_ips_from_state() -> set[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    used: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
    for path in _peer_state_dir().glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            used.add(ipaddress.ip_interface(data["client_ip"]).ip)
        except Exception:
            continue
    return used


def _used_ips_from_wireguard() -> set[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    used: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()
    output = _run(["wg", "show", settings.wg_interface, "allowed-ips"])

    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue

        for allowed_ip in parts[1].split(","):
            try:
                used.add(ipaddress.ip_interface(allowed_ip).ip)
            except ValueError:
                continue

    return used


# def allocate_client_ip() -> str:
#     network = ipaddress.ip_network(settings.wg_network, strict=False)
#     used = _used_ips_from_state() | _used_ips_from_wireguard()

#     hosts = list(network.hosts())

#     for host in hosts[19:]:
#         if host not in used:
#             return f"{host}/32"

#     raise WireGuardError(f"No free client IPs in {settings.wg_network}")

def allocate_client_ip() -> str:
    network = ipaddress.ip_network(settings.wg_network, strict=False)
    used = _used_ips_from_state()

    if settings.wg_apply_changes:
        used |= _used_ips_from_wireguard()

    hosts = list(network.hosts())

    # reserve .1-.19
    for host in hosts[19:]:
        if host not in used:
            return f"{host}/32"

    raise WireGuardError(f"No free client IPs in {settings.wg_network}")


def add_peer(peer_id: str, public_key: str, client_ip: str) -> None:
    if settings.wg_apply_changes:
        _run([
            "wg",
            "set",
            settings.wg_interface,
            "peer",
            public_key,
            "allowed-ips",
            client_ip,
        ])

    _save_peer_state(peer_id, {
        "public_key": public_key,
        "client_ip": client_ip,
    })


def remove_peer(peer_id: str) -> bool:
    state = _load_peer_state(peer_id)
    if state is None:
        return False

    if settings.wg_apply_changes:
        _run([
            "wg",
            "set",
            settings.wg_interface,
            "peer",
            state["public_key"],
            "remove",
        ])

    _delete_peer_state(peer_id)
    return True
