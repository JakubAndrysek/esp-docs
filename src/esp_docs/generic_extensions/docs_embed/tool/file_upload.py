import os
from pathlib import Path
import hashlib
from typing import Optional
import click
import requests


class FileWithProgressAndHash:
    """File-like object that updates a progress bar and computes SHA-256 hash while reading."""
    def __init__(self, path: Path, bar: click.progressbar, chunk_size: int = 1024 * 1024):
        self.path = path
        self.f = open(path, "rb")
        self.total = self.path.stat().st_size
        self.hash = hashlib.sha256()
        self.bar = bar
        self.chunk_size = chunk_size

    def __len__(self):
        return self.total

    def read(self, n: Optional[int] = None):
        n = n or self.chunk_size
        chunk = self.f.read(n)
        if chunk:
            self.hash.update(chunk)
            self.bar.update(len(chunk))
        return chunk

    def hexdigest(self) -> str:
        return self.hash.hexdigest()

    def close(self):
        try:
            self.f.close()
        except Exception:
            pass


class FileUploader:
    def __init__(self, path: str):
        self.base_path = Path(path)
        self.gen_path = self.base_path / ".gen"
        self.gen_path.mkdir(exist_ok=True)

        self.storage_url_prefix = os.getenv("STORAGE_URL_PREFIX").strip("/")
        self.storage_url = os.getenv("STORAGE_URL")
        self.storage_token = os.getenv("STORAGE_TOKEN")
        self.dest_root = os.getenv("STORAGE_DEST_ROOT", "gen").strip("/")

        verify_env = os.getenv("STORAGE_VERIFY_SSL", "1")
        self.verify_ssl = False if verify_env.strip() in ("0", "false", "False", "no") else True

        if not self.storage_url or not self.storage_token:
            raise RuntimeError(
                "Environment variables STORAGE_URL and STORAGE_TOKEN must be set"
            )

    def upload_file_with_progress(self, src: Path, dest_rel: str):
        """Upload a single file to the storage server with progress and hash verification."""
        headers = {"Authorization": f"Bearer {self.storage_token}"}
        params = {"dest": dest_rel}  # storage.php očekává ?dest=...

        with click.progressbar(length=src.stat().st_size, label=f"Uploading {src.name}") as bar:
            streamer = FileWithProgressAndHash(src, bar)
            try:
                resp = requests.put(
                    self.storage_url,
                    params=params,
                    headers=headers,
                    data=streamer,
                    timeout=(10, 600),
                    verify=self.verify_ssl,
                )
            finally:
                streamer.close()

        if resp.status_code != 200:
            raise RuntimeError(f"Upload failed ({resp.status_code}): {resp.text}")

        try:
            info = resp.json()
        except Exception as e:
            raise RuntimeError(f"Invalid JSON response from server: {e}")

        if not info.get("ok"):
            raise RuntimeError(f"Server reported error: {info}")

        server_hash = info.get("sha256")
        local_hash = streamer.hexdigest()
        if server_hash and server_hash != local_hash:
            raise RuntimeError(
                f"Hash mismatch for {src.name}: local={local_hash} server={server_hash}"
            )

        click.echo(f"✔ {src} → {dest_rel} ({info.get('bytes', '?')} B)")

    def upload_generated_files(self) -> None:
        """Upload generated firmware images and config files to storage."""
        if not self.gen_path.exists() or not self.gen_path.is_dir():
            raise FileNotFoundError(f"Directory not found: {self.gen_path}")

        files = [p for p in self.gen_path.rglob("*") if p.is_file()]
        if not files:
            raise RuntimeError(f"No files to upload in {self.gen_path}")

        click.echo(f"Found {len(files)} file(s) in {self.gen_path} to upload.")

        for src in files:
            dest_rel = f"{self.storage_url_prefix}/{src}"
            print(f"- Uploading {src.name} to {dest_rel}")
            # self.upload_file_with_progress(src, dest_rel)
