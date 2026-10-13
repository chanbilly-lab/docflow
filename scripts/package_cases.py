"""Build a deterministic Lambda ZIP with the pinned pure-Python SDK dependencies."""

from importlib.metadata import distribution
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    files: dict[str, bytes] = {}
    for line in (ROOT / "backend/requirements-runtime.txt").read_text().splitlines():
        name, version = line.split("==")
        package = distribution(name)
        if package.version != version:
            raise RuntimeError(f"Install pinned runtime dependency: {name}=={version}")
        for entry in package.files or []:
            path = str(entry).replace("\\", "/")
            if ".." in entry.parts or "__pycache__" in entry.parts or path.endswith(".pyc"):
                continue
            if ".dist-info/" in path and not path.endswith(
                ("METADATA", "WHEEL", "LICENSE", "LICENSE.txt")
            ):
                continue
            files[path] = package.locate_file(entry).read_bytes()
    for folder in (
        "case_api",
        "common",
        "document_api",
        "document_processor",
        "outbox_publisher",
        "workflow_validate_case",
        "workflow_finalize_case",
        "workflow_failure_handler",
        "workflow_create_review_task",
        "review_api",
        "notification_worker",
        "operations_monitor",
    ):
        for source in (ROOT / "backend/src" / folder).rglob("*"):
            if source.is_file() and (source.suffix == ".py" or source.name == "py.typed"):
                files[source.relative_to(ROOT / "backend/src").as_posix()] = source.read_bytes()
    output = ROOT / "build/cases.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w") as archive:
        for name, content in sorted(files.items()):
            info = ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, content)
    print("PASS: built build/cases.zip")


if __name__ == "__main__":
    main()
