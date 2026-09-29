from app.parser import parse_dependency_file


# Test parsing a dependency file and print the results.
def test_parser():
    files = [
        "samples/package.json",
        "samples/requirements.txt",
        "samples/pom.xml",
    ]

    for file_path in files:
        print()
        print(f"Testing: {file_path}")

        packages = parse_dependency_file(file_path)

        for package in packages:
            print(package)


if __name__ == "__main__":
    test_parser()
