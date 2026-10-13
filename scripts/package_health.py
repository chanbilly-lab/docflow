"""Build a deterministic, dependency-free Lambda archive before Terraform checks."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    destination = ROOT / "build" / "health.zip"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w") as archive:
        for name in ("__init__.py", "health.py"):
            source = ROOT / "backend" / "src" / "case_api" / name
            info = ZipInfo(f"case_api/{source.name}", date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
    print("PASS: built build/health.zip")


if __name__ == "__main__":
    main()
