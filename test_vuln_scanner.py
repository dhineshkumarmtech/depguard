from app.parser import parse_dependency_file
from app.resolver import resolve_inventory
from app.vuln_scanner import scan_vulnerabilities


def test_vulnerability_scanner():

    print()
    print("STEP 1: Parsing dependency file")

    packages = parse_dependency_file(
        "samples/package.json"
    )

    print(
        f"Parsed packages: {len(packages)}"
    )

    print()
    print("STEP 2: Resolving inventory")

    inventory = resolve_inventory(
        packages
    )

    print(
        f"Inventory packages: {len(inventory)}"
    )

    print()
    print("STEP 3: Running OSV vulnerability scan")

    scanned_inventory = scan_vulnerabilities(
        inventory
    )

    # Safety check so we immediately know
    # if the scanner returned the wrong type.
    if scanned_inventory is None:
        raise RuntimeError(
            "scan_vulnerabilities() returned None"
        )

    inventory = scanned_inventory

    print()
    print("DEPGUARD VULNERABILITY SCAN")
    print("=" * 75)

    total_vulnerabilities = 0

    for package in inventory:

        vulnerabilities = package.get(
            "vulnerabilities",
            []
        )

        total_vulnerabilities += len(
            vulnerabilities
        )

        print(
            f"{package['ecosystem']:6} "
            f"{package['name']:30} "
            f"Version={str(package['version']):12} "
            f"CVSS={package.get('max_cvss', 0.0):4.1f} "
            f"Vulnerabilities={len(vulnerabilities)}"
        )

        for vulnerability in vulnerabilities:

            print(
                f"    -> ID: "
                f"{vulnerability.get('id')}"
            )

            print(
                f"       Severity: "
                f"{vulnerability.get('severity')}"
            )

            print(
                f"       CVSS: "
                f"{vulnerability.get('cvss')}"
            )

            print(
                f"       Fixed versions: "
                f"{vulnerability.get('fixed_versions')}"
            )

            print(
                f"       Advisory: "
                f"{vulnerability.get('advisory_url')}"
            )

    print("=" * 75)

    print(
        f"Total packages scanned: "
        f"{len(inventory)}"
    )

    print(
        f"Total vulnerabilities found: "
        f"{total_vulnerabilities}"
    )


if __name__ == "__main__":
    test_vulnerability_scanner()

