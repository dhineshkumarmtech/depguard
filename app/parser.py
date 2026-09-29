import json
import re
import xml.etree.ElementTree as ET


# Read a package.json file and return its dependencies.
def parse_package_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    packages = []

    dependencies = data.get("dependencies", {})
    dev_dependencies = data.get("devDependencies", {})

    for name, version in dependencies.items():
        packages.append(
            {
                "ecosystem": "npm",
                "name": name,
                "version": normalize_version(version),
            }
        )

    for name, version in dev_dependencies.items():
        packages.append(
            {
                "ecosystem": "npm",
                "name": name,
                "version": normalize_version(version),
            }
        )

    return packages


# Read a requirements.txt file and return its dependencies.
def parse_requirements(file_path):
    packages = []

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            line = line.split("#", 1)[0].strip()

            if not line:
                continue

            match = re.match(
                r"^([A-Za-z0-9_.-]+)\s*(==|>=|~=|<=)?\s*(.*)$",
                line,
            )

            if not match:
                continue

            name = match.group(1)
            operator = match.group(2)
            version = match.group(3).strip()

            if operator and version:
                version = normalize_version(version)
            else:
                version = None

            packages.append(
                {
                    "ecosystem": "PyPI",
                    "name": name,
                    "version": version,
                }
            )

    return packages


# Read a Maven pom.xml file and return its non-test dependencies.
def parse_pom(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    namespace = ""

    if root.tag.startswith("{"):
        namespace = root.tag.split("}")[0] + "}"

    properties = {}

    properties_element = root.find(f"{namespace}properties")

    if properties_element is not None:
        for child in properties_element:
            key = child.tag.replace(namespace, "")
            properties[key] = child.text or ""

    packages = []

    dependencies_element = root.find(f"{namespace}dependencies")

    if dependencies_element is None:
        return packages

    for dependency in dependencies_element.findall(
        f"{namespace}dependency"
    ):
        group_element = dependency.find(f"{namespace}groupId")
        artifact_element = dependency.find(f"{namespace}artifactId")
        version_element = dependency.find(f"{namespace}version")
        scope_element = dependency.find(f"{namespace}scope")

        if group_element is None or artifact_element is None:
            continue

        scope = ""

        if scope_element is not None and scope_element.text:
            scope = scope_element.text.strip()

        if scope == "test":
            continue

        group_id = group_element.text.strip()
        artifact_id = artifact_element.text.strip()

        version = None

        if version_element is not None and version_element.text:
            version = version_element.text.strip()
            version = resolve_property(version, properties)
            version = normalize_version(version)

        packages.append(
            {
                "ecosystem": "Maven",
                "name": f"{group_id}:{artifact_id}",
                "version": version,
            }
        )

    return packages


# Convert common version ranges into their base version.
def normalize_version(version):
    if version is None:
        return None

    version = str(version).strip()

    if not version:
        return None

    version = re.sub(r"^[\^~]", "", version)

    match = re.search(
        r"(\d+(?:\.\d+){0,3})",
        version,
    )

    if match:
        return match.group(1)

    return version


# Replace a simple Maven ${property} value.
def resolve_property(version, properties):
    match = re.fullmatch(r"\$\{([^}]+)\}", version)

    if match:
        property_name = match.group(1)
        return properties.get(property_name, version)

    return version


# Detect the dependency file type and call the correct parser.
def parse_dependency_file(file_path):
    file_name = file_path.lower()

    if file_name.endswith(".json"):
        return parse_package_json(file_path)

    if file_name.endswith(".txt"):
        return parse_requirements(file_path)

    if file_name.endswith(".xml"):
        return parse_pom(file_path)

    raise ValueError(
        "Unsupported dependency file. Use package.json, "
        "requirements.txt, or pom.xml."
    )
