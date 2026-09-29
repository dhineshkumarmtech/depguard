import json
from pathlib import Path

from app.parser import parse_dependency_file


PACKAGE_FILE = Path("samples/demo-package.json")
ANALYSIS_FILE = Path("app/data/demo_analysis.json")


def load_demo_analysis():
    """
    Load deterministic demo analysis data.
    """

    with ANALYSIS_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def calculate_risk_band(score):
    """
    Convert a numeric risk score into a risk band.
    """

    if score <= 24:
        return "Low"

    if score <= 49:
        return "Medium"

    if score <= 74:
        return "High"

    return "Critical"


def scan_demo():
    """
    Run the deterministic DepGuard demo scan.
    """

    packages = parse_dependency_file(
        str(PACKAGE_FILE)
    )

    demo_data = load_demo_analysis()

    analysis_packages = demo_data.get(
        "packages",
        {}
    )

    results = []

    for package in packages:

        name = package["name"]
        version = package["version"]

        key = f"{name}@{version}"

        analysis = analysis_packages.get(key)

        if analysis is None:
            raise RuntimeError(
                f"No demo analysis found for {key}"
            )

        result = {
            "name": name,
            "version": version,
            "ecosystem": package["ecosystem"],
            "direct": True,
            "depth": 0,
            "required_by": [],
            "vulnerabilities": analysis.get(
                "vulnerabilities",
                []
            ),
            "max_cvss": analysis.get(
                "max_cvss",
                0.0
            ),
            "integrity": analysis.get(
                "integrity",
                {}
            ),
            "suspicious_flags": analysis.get(
                "suspicious_flags",
                []
            ),
            "risk_score": analysis.get(
                "risk_score",
                0
            ),
            "risk_band": analysis.get(
                "risk_band",
                "Low"
            ),
            "fix": analysis.get(
                "fix"
            )
        }

        # Recalculate the risk band from the score.
        result["risk_band"] = calculate_risk_band(
            result["risk_score"]
        )

        results.append(result)

    overall_score = 0

    for result in results:
        if result["risk_score"] > overall_score:
            overall_score = result["risk_score"]

    overall_band = calculate_risk_band(
        overall_score
    )

    return {
        "demo_mode": True,
        "project": "depguard-jury-demo",
        "packages_scanned": len(results),
        "overall_score": overall_score,
        "overall_risk": overall_band,
        "results": results
    }


def print_report(report):
    """
    Print a jury-friendly terminal report.
    """

    print()
    print("=" * 72)
    print("                    DEPGUARD SCAN REPORT")
    print("=" * 72)

    print()
    print(f"Project        : {report['project']}")
    print(f"Packages       : {report['packages_scanned']}")
    print(
        f"Overall Risk   : "
        f"{report['overall_risk'].upper()}"
    )
    print(
        f"Overall Score  : "
        f"{report['overall_score']}/100"
    )

    print()
    print("-" * 72)
    print(
        f"{'Package':30}"
        f"{'Version':12}"
        f"{'Risk':12}"
        f"{'Score':8}"
    )
    print("-" * 72)

    for result in report["results"]:

        package_name = result["name"]

        if len(package_name) > 28:
            package_name = package_name[:28] + ".."

        print(
            f"{package_name:30}"
            f"{result['version']:12}"
            f"{result['risk_band']:12}"
            f"{result['risk_score']:>3}/100"
        )

    print("-" * 72)

    print()
    print("DETAILED FINDINGS")
    print("=" * 72)

    for result in report["results"]:

        print()
        print(
            f"Package: "
            f"{result['name']}@{result['version']}"
        )

        print(
            f"Risk: "
            f"{result['risk_band']} "
            f"({result['risk_score']}/100)"
        )

        vulnerabilities = result[
            "vulnerabilities"
        ]

        if vulnerabilities:

            print("Vulnerabilities:")

            for vulnerability in vulnerabilities:

                print(
                    f"  - {vulnerability['id']} "
                    f"({vulnerability['severity']})"
                )

                print(
                    f"    CVSS: "
                    f"{vulnerability['cvss']}"
                )

                print(
                    f"    {vulnerability['summary']}"
                )

                fixed_versions = vulnerability.get(
                    "fixed_versions",
                    []
                )

                if fixed_versions:
                    print(
                        f"    Fixed in: "
                        f"{', '.join(fixed_versions)}"
                    )

        else:
            print("Vulnerabilities: None detected")

        integrity = result["integrity"]

        print(
            f"Integrity: "
            f"{integrity.get('status', 'Unknown')}"
        )

        flags = result[
            "suspicious_flags"
        ]

        if flags:

            print("Suspicious findings:")

            for flag in flags:
                print(f"  - {flag}")

        else:
            print(
                "Suspicious findings: None"
            )

        if result["fix"]:

            print(
                f"Recommendation: "
                f"{result['fix']}"
            )

    print()
    print("=" * 72)
    print("                  END OF DEPGUARD REPORT")
    print("=" * 72)
    print()


if __name__ == "__main__":

    report = scan_demo()

    print_report(report)
