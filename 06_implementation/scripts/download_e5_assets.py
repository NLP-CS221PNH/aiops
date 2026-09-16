"""Download pinned model assets for intfloat/e5-small-v2.

Revision: ffb93f3bd4047442299a41ebb6fa998a38507c52
Saves config.json and model.safetensors into vendor/e5-small-v2/
"""
import hashlib
import json
from pathlib import Path
import urllib.request
import sys


REVISION = "ffb93f3bd4047442299a41ebb6fa998a38507c52"
BASE_URL = f"https://huggingface.co/intfloat/e5-small-v2/resolve/{REVISION}/"
FILES = ["config.json", "model.safetensors"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_assets(target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest = {}
    
    for filename in FILES:
        url = BASE_URL + filename
        dest = target_dir / filename
        if dest.exists():
            print(f"{filename} already exists at {dest}. Checking hash...")
            h = sha256_file(dest)
            manifest[filename] = h
            print(f"  SHA-256: {h}")
            continue
            
        print(f"Downloading {filename} from {url}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CS221-Research-Pack/1.0"})
            with urllib.request.urlopen(req, timeout=60) as response, open(dest, "wb") as out:
                total = int(response.headers.get("content-length", 0))
                downloaded = 0
                while True:
                    buffer = response.read(1024 * 1024)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    out.write(buffer)
                    if total > 0:
                        pct = (downloaded / total) * 100
                        sys.stdout.write(f"\r  Progress: {pct:.1f}% ({downloaded / 1024 / 1024:.1f} MB)")
                        sys.stdout.flush()
            print()
            h = sha256_file(dest)
            manifest[filename] = h
            print(f"Downloaded {filename}, SHA-256: {h}")
        except Exception as e:
            print(f"Failed to download {filename}: {e}")
            if dest.exists():
                dest.unlink()
            raise e
            
    return manifest


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[1]
    vendor_dir = base / "vendor" / "e5-small-v2"
    print(f"Target directory: {vendor_dir}")
    manifest = download_assets(vendor_dir)
    print("Downloaded assets summary:")
    print(json.dumps(manifest, indent=2))
