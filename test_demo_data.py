import json
from pathlib import Path

from app.parser import parse_dependency_file


sample = Path("samples/demo-package.json")

demo_data = json.loads(
    Path("app/data/demo_analysis.json").read_text()
)

packages = parse_dependency_file(str(sample))

print()
print("DEPGUARD DEMO DATA TEST")
print("=" * 50)

print(f"Parsed packages: {len(packages)}")
print()

for package in packages:
    key = f"{package['name']}@{package['version']}"

    if key not in demo_data["packages"]:
        raise RuntimeError(
            f"Missing demo analysis for {key}"
        )

    print(f"[OK] {key}")

print()
print("=" * 50)

if len(packages) != 3:
    raise RuntimeError(
        f"Expected 3 packages, got {len(packages)}"
    )

print("Demo Phase 1 PASS")
