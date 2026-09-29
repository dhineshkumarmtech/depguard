from app.parser import parse_dependency_file
from app.resolver import resolve_inventory


# Test the parser and dependency resolver together.
def test_resolver():
    packages = parse_dependency_file(
        "samples/package.json"
    )

    inventory = resolve_inventory(packages)

    print()
    print("DEPGUARD INVENTORY")
    print("=" * 60)

    for package in inventory:
        dependency_type = (
            "Direct"
            if package["direct"]
            else "Transitive"
        )

        print(
            f"{package['ecosystem']:6} "
            f"{package['name']:30} "
            f"{str(package['version']):12} "
            f"{dependency_type:10} "
            f"Depth={package['depth']} "
            f"RequiredBy={package['required_by']}"
        )

    print("=" * 60)
    print(f"Total packages: {len(inventory)}")


if __name__ == "__main__":
    test_resolver()
