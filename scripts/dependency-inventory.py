"""Record installed Python and npm-lock metadata; not a legal compliance verdict."""
import importlib.metadata
import json
from datetime import date
from pathlib import Path

root = Path(__file__).resolve().parents[1]
python_packages = []
for distribution in importlib.metadata.distributions():
    metadata = distribution.metadata
    license_name = metadata.get("License-Expression")
    if not license_name:
        license_name = next((value.rsplit("::", 1)[-1].strip()
                             for value in metadata.get_all("Classifier", [])
                             if value.startswith("License ::")), None)
    if not license_name:
        raw = metadata.get("License", "")
        license_name = raw if raw and len(raw) < 100 else "Review bundled license files"
    python_packages.append({"name": metadata["Name"], "version": distribution.version,
                            "license_metadata": license_name})
lock = json.loads((root / "frontend/package-lock.json").read_text(encoding="utf-8"))
npm_packages = [{"path": path, "version": info.get("version"),
                 "license_metadata": info.get("license", "Review package license files"),
                 "optional": info.get("optional", False)}
                for path, info in lock["packages"].items() if path]
report = {
    "review_date": date.today().isoformat(),
    "scope": "Installed Windows Python environment and complete npm lock graph including optional platform packages. Metadata is evidence for review, not FOSS-policy approval. Container/bundled native library notices require separate review.",
    "python": sorted(python_packages, key=lambda p: p["name"].lower()),
    "npm_lock": npm_packages,
}
(root / "docs/dependency-inventory.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(f"Recorded {len(python_packages)} Python distributions and {len(npm_packages)} npm lock entries.")
