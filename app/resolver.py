import re
import xml.etree.ElementTree as ET

import requests
from packaging.requirements import Requirement


MAX_DEPTH = 2
MAX_PACKAGES = 60
REQUEST_TIMEOUT = 5


def safe_get_json(url):
    """
    Safely fetch JSON from a URL.

    A network failure must never crash DepGuard.
    """

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as error:
        print(
            f"[Resolver] Request failed: {url}"
        )
        print(
            f"[Resolver] Reason: {error}"
        )
        return None

    except ValueError:
        print(
            f"[Resolver] Invalid JSON response: {url}"
        )
        return None


def get_npm_latest(name):
    url = f"https://registry.npmjs.org/{name}/latest"

    data = safe_get_json(url)

    if not data:
        return None

    return data.get("version")


def get_pypi_latest(name):
    url = f"https://pypi.org/pypi/{name}/json"

    data = safe_get_json(url)

    if not data:
        return None

    return data.get("info", {}).get("version")


def get_npm_dependencies(name, version):
    url = f"https://registry.npmjs.org/{name}/{version}"

    data = safe_get_json(url)

    if not data:
        return {}

    return data.get("dependencies", {})


def parse_pypi_requirement(requirement_text):
    try:
        requirement = Requirement(
            requirement_text
        )

    except Exception:
        return None

    # Ignore extras.
    if requirement.extras:
        return None

    # Ignore marker-only dependencies.
    if requirement.marker is not None:
        return None

    name = requirement.name

    if not requirement.specifier:
        return name, None

    version = None

    for specifier in requirement.specifier:

        if specifier.operator in (
            "==",
            ">=",
            "~=",
            "<=",
        ):
            version = specifier.version
            break

    return name, version


def get_pypi_dependencies(name, version):
    url = f"https://pypi.org/pypi/{name}/{version}/json"

    data = safe_get_json(url)

    if not data:
        return {}

    requires_dist = (
        data.get("info", {})
        .get("requires_dist")
        or []
    )

    dependencies = {}

    for requirement_text in requires_dist:

        parsed = parse_pypi_requirement(
            requirement_text
        )

        if parsed is None:
            continue

        dependency_name, dependency_version = (
            parsed
        )

        dependencies[
            dependency_name
        ] = dependency_version

    return dependencies


def resolve_maven_property(
    version,
    properties,
):
    if not version:
        return None

    version = version.strip()

    match = re.fullmatch(
        r"\$\{([^}]+)\}",
        version,
    )

    if match:

        property_name = match.group(1)

        return properties.get(
            property_name
        )

    return version


def get_maven_dependencies(
    group_id,
    artifact_id,
    version,
):
    group_path = group_id.replace(
        ".",
        "/",
    )

    url = (
        "https://repo1.maven.org/maven2/"
        f"{group_path}/"
        f"{artifact_id}/"
        f"{version}/"
        f"{artifact_id}-{version}.pom"
    )

    try:

        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException as error:

        print(
            f"[Resolver] Maven request failed: "
            f"{group_id}:{artifact_id}:{version}"
        )

        print(
            f"[Resolver] Reason: {error}"
        )

        return {}

    try:

        root = ET.fromstring(
            response.text
        )

    except ET.ParseError:

        return {}

    namespace = ""

    if root.tag.startswith("{"):
        namespace = (
            root.tag.split("}")[0]
            + "}"
        )

    properties = {}

    properties_element = root.find(
        f"{namespace}properties"
    )

    if properties_element is not None:

        for child in properties_element:

            key = child.tag.replace(
                namespace,
                "",
            )

            properties[key] = (
                child.text or ""
            )

    dependencies = {}

    dependencies_element = root.find(
        f"{namespace}dependencies"
    )

    if dependencies_element is None:
        return dependencies

    for dependency in (
        dependencies_element.findall(
            f"{namespace}dependency"
        )
    ):

        group_element = dependency.find(
            f"{namespace}groupId"
        )

        artifact_element = dependency.find(
            f"{namespace}artifactId"
        )

        version_element = dependency.find(
            f"{namespace}version"
        )

        scope_element = dependency.find(
            f"{namespace}scope"
        )

        optional_element = dependency.find(
            f"{namespace}optional"
        )

        if group_element is None:
            continue

        if artifact_element is None:
            continue

        scope = ""

        if scope_element is not None:

            scope = (
                scope_element.text
                or ""
            ).strip()

        # Skip test dependencies.
        if scope == "test":
            continue

        optional = False

        if optional_element is not None:

            optional = (
                (
                    optional_element.text
                    or ""
                )
                .strip()
                .lower()
                == "true"
            )

        # Skip optional dependencies.
        if optional:
            continue

        group = (
            group_element.text
            or ""
        ).strip()

        artifact = (
            artifact_element.text
            or ""
        ).strip()

        dependency_version = None

        if version_element is not None:

            dependency_version = (
                resolve_maven_property(
                    version_element.text,
                    properties,
                )
            )

        dependency_name = (
            f"{group}:{artifact}"
        )

        dependencies[
            dependency_name
        ] = dependency_version

    return dependencies


def normalize_npm_version(version):
    """
    Convert a simple npm version range into
    its base version.

    Examples:

        ^1.2.3   -> 1.2.3
        ~1.2.3   -> 1.2.3
        >=1.2.3  -> 1.2.3
        <=1.2.3  -> 1.2.3
        1.2.3    -> 1.2.3
    """

    if not version:
        return None

    version = str(version).strip()

    # Remove common npm range operators.
    version = re.sub(
        r"^[\^~<>=\s]+",
        "",
        version,
    )

    # Handle simple OR ranges such as:
    # >=1.0.0 <2.0.0
    version = version.split(
        " ",
        1,
    )[0]

    # Extract the numeric base version.
    match = re.search(
        r"\d+(?:\.\d+){0,2}",
        version,
    )

    if match:
        return match.group(0)

    return version


def resolve_missing_version(
    package,
):
    """
    Resolve a package version.

    For npm:
    - normalize ranges
    - query latest only when no version exists
    """

    version = package.get(
        "version"
    )

    ecosystem = package[
        "ecosystem"
    ]

    name = package[
        "name"
    ]

    if ecosystem == "npm":

        if version:
            return normalize_npm_version(
                version
            )

        return get_npm_latest(
            name
        )

    if ecosystem == "PyPI":

        if version:
            return version

        return get_pypi_latest(
            name
        )

    # Maven needs an explicit version
    # from the POM.
    return version
    if package.get("version"):
        return package["version"]

    ecosystem = package[
        "ecosystem"
    ]

    name = package[
        "name"
    ]

    if ecosystem == "npm":
        return get_npm_latest(
            name
        )

    if ecosystem == "PyPI":
        return get_pypi_latest(
            name
        )

    return None


def get_dependencies(
    package,
):
    ecosystem = package[
        "ecosystem"
    ]

    name = package[
        "name"
    ]

    version = package.get(
        "version"
    )

    if not version:
        return {}

    if ecosystem == "npm":

        return get_npm_dependencies(
            name,
            version,
        )

    if ecosystem == "PyPI":

        return get_pypi_dependencies(
            name,
            version,
        )

    if ecosystem == "Maven":

        if ":" not in name:
            return {}

        group_id, artifact_id = (
            name.split(
                ":",
                1,
            )
        )

        return get_maven_dependencies(
            group_id,
            artifact_id,
            version,
        )

    return {}


def package_key(
    package,
):
    return (
        package["ecosystem"],
        package["name"].lower(),
        package.get("version"),
    )


def add_package(
    inventory,
    package,
):
    key = package_key(
        package
    )

    for existing in inventory:

        if package_key(
            existing
        ) == key:

            return existing

    if len(inventory) >= MAX_PACKAGES:
        return None

    inventory.append(
        package
    )

    return package


def add_required_by(
    child,
    parent,
):
    parent_name = parent[
        "name"
    ]

    if parent_name not in child[
        "required_by"
    ]:

        child[
            "required_by"
        ].append(
            parent_name
        )


def resolve_inventory(
    parsed_packages,
):
    """
    Build the dependency inventory.

    Uses an iterative queue instead of recursive
    resolution so packages are not repeatedly
    resolved.
    """

    inventory = []

    # Packages waiting to be processed.
    queue = []

    # Add direct dependencies.
    for parsed in parsed_packages:

        package = {
            "ecosystem": parsed[
                "ecosystem"
            ],
            "name": parsed[
                "name"
            ],
            "version": parsed.get(
                "version"
            ),
            "direct": True,
            "depth": 0,
            "required_by": [],
        }

        package[
            "version"
        ] = resolve_missing_version(
            package
        )

        existing = add_package(
            inventory,
            package,
        )

        if existing is not None:

            queue.append(
                existing
            )

        if len(inventory) >= MAX_PACKAGES:
            break

    # Keep track of packages whose dependencies
    # have already been requested.
    processed = set()

    while queue:

        package = queue.pop(0)

        key = package_key(
            package
        )

        if key in processed:
            continue

        processed.add(key)

        depth = package[
            "depth"
        ]

        # Do not resolve beyond MAX_DEPTH.
        if depth >= MAX_DEPTH:
            continue

        dependencies = get_dependencies(
            package
        )

        for name, version in (
            dependencies.items()
        ):

            if len(inventory) >= MAX_PACKAGES:
                break

            child = {
                "ecosystem": package[
                    "ecosystem"
                ],
                "name": name,
                "version": version,
                "direct": False,
                "depth": depth + 1,
                "required_by": [],
            }

            child[
                "version"
            ] = resolve_missing_version(
                child
            )

            existing = add_package(
                inventory,
                child,
            )

            if existing is None:
                break

            add_required_by(
                existing,
                package,
            )

            existing_key = package_key(
                existing
            )

            if existing_key not in processed:

                queue.append(
                    existing
                )

    return inventory
