import ipaddress
import subprocess


BASE_NETWORK = ipaddress.ip_network("10.0.0.0/24")


def generate_private_key() -> str:
    result = subprocess.run(
        ["wg", "genkey"],
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()


def generate_public_key(private_key: str) -> str:
    result = subprocess.run(
        ["wg", "pubkey"],
        input=private_key,
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()


def allocate_client_ip(index: int) -> str:
    host = list(BASE_NETWORK.hosts())[index]

    return f"{host}/32"
