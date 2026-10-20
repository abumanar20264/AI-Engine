import hashlib
import json
import os
import stat
from pathlib import Path


ROOT = Path("/kaggle/working/ai-engine-kaggle-tree-probe")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if ROOT.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {ROOT}")

    deep_dir = ROOT / "nested" / "level-two" / "level-three"
    bin_dir = ROOT / "bin"
    many_dir = ROOT / "many-files"
    deep_dir.mkdir(parents=True)
    bin_dir.mkdir()
    many_dir.mkdir()

    files = {
        ROOT / "root.txt": b"root-file\n",
        deep_dir / "deep.txt": b"deep-file\n",
        bin_dir / "probe.sh": b"#!/bin/sh\nprintf 'tree-probe-ok\\n'\n",
    }
    for path, content in files.items():
        path.write_bytes(content)
    (bin_dir / "probe.sh").chmod(0o755)
    (ROOT / "nested-link.txt").symlink_to("nested/level-two/level-three/deep.txt")
    many_files = []
    for index in range(501):
        path = many_dir / f"file-{index:04d}.txt"
        content = f"fixture-{index:04d}\n".encode("ascii")
        path.write_bytes(content)
        many_files.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )

    manifest = {
        "files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
                "mode": stat.S_IMODE(path.stat().st_mode),
            }
            for path in sorted(files, key=lambda item: item.as_posix())
        ],
        "many_files": many_files,
        "symlinks": [
            {
                "path": "nested-link.txt",
                "target": os.readlink(ROOT / "nested-link.txt"),
            }
        ],
    }
    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
