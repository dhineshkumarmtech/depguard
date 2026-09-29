import requests


OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_VULN_URL = "https://api.osv.dev/v1/vulns/"
REQUEST_TIMEOUT = 15


def osv_ecosystem(ecosystem):
    """
    Convert DepGuard ecosystem names to OSV ecosystem names.
    """

    if ecosystem == "npm":
        return "npm"

    if ecosystem == "PyPI":
        return "PyPI"

    if ecosystem == "Maven":
        return "Maven"

    return ecosystem


def osv_package_name(package):
    """
    Return the package name expected by OSV.

    Maven packages already use:
        group:artifact
    """

    return package["name"]


def query_osv_batch(packages):
    """
    Send all packages to OSV using the batch API.

    Returns:
        dict if successful
        None if the request fails
    """

    queries = []

    for package in packages:

        version = package.get("version")

        if not version:
            queries.append({})
            continue

        query = {
            "package": {
                "name": osv_package_name(package),
                "ecosystem": osv_ecosystem(
                    package["ecosystem"]
                ),
            },
            "version": str(version),
        }

        queries.append(query)

    payload = {
        "queries": queries
    }

    try:
        response = requests.post(
            OSV_BATCH_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as error:
        print(
            f"[OSV] Batch request failed: {error}"
        )
        return None

    except ValueError as error:
        print(
            f"[OSV] Invalid JSON response: {error}"
        )
        return None


def get_vulnerability_details(vulnerability_id):
    """
    Retrieve detailed information for one OSV vulnerability.
    """

    url = OSV_VULN_URL + str(vulnerability_id)

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as error:
        print(
            f"[OSV] Detail request failed for "
            f"{vulnerability_id}: {error}"
        )
        return None

    except ValueError:
        print(
            f"[OSV] Invalid JSON for "
            f"{vulnerability_id}"
        )
        return None


def extract_cvss(vulnerability):
    """
    Extract the highest numeric CVSS score.

    If a numeric score is unavailable, use the
    required severity mapping:

        LOW       = 3.0
        MODERATE  = 5.5
        MEDIUM    = 5.5
        HIGH      = 7.5
        CRITICAL  = 9.5
    """

    severities = vulnerability.get(
        "severity"
    ) or []

    numeric_scores = []

    for severity in severities:

        score = severity.get("score")

        if not score:
            continue

        try:

            score_text = str(score)

            # A CVSS vector is not itself a numeric score.
            if score_text.upper().startswith(
                "CVSS:"
            ):
                continue

            numeric_scores.append(
                float(score_text)
            )

        except (
            ValueError,
            TypeError,
        ):
            continue

    if numeric_scores:
        return max(numeric_scores)

    database_specific = (
        vulnerability.get(
            "database_specific"
        )
        or {}
    )

    severity = database_specific.get(
        "severity"
    )

    if severity:

        severity = str(
            severity
        ).upper()

        # Required fallback mapping when
        # OSV does not provide a numeric CVSS.
        mapping = {
            "LOW": 3.0,
            "MODERATE": 5.5,
            "MEDIUM": 5.5,
            "HIGH": 7.5,
            "CRITICAL": 9.5,
        }

        return mapping.get(
            severity,
            0.0,
        )

    return 0.0


def extract_severity(vulnerability):
    """
    Extract human-readable severity.
    """

    database_specific = (
        vulnerability.get(
            "database_specific"
        )
        or {}
    )

    severity = database_specific.get(
        "severity"
    )

    if severity:
        return str(
            severity
        ).upper()

    severities = vulnerability.get(
        "severity"
    ) or []

    if severities:

        for severity_entry in severities:

            score = severity_entry.get(
                "score"
            )

            if score:
                # If no severity label exists,
                # indicate that CVSS exists.
                return "CVSS"

    return "UNKNOWN"


def extract_fixed_versions(vulnerability):
    """
    Extract all fixed versions listed by OSV.
    """

    fixed_versions = []

    affected = vulnerability.get(
        "affected"
    ) or []

    for affected_package in affected:

        ranges = affected_package.get(
            "ranges"
        ) or []

        for version_range in ranges:

            events = version_range.get(
                "events"
            ) or []

            for event in events:

                fixed = event.get(
                    "fixed"
                )

                if (
                    fixed
                    and fixed not in fixed_versions
                ):
                    fixed_versions.append(
                        fixed
                    )

    return fixed_versions


def extract_advisory_url(vulnerability):
    """
    Find the most useful advisory/reference URL.
    """

    references = vulnerability.get(
        "references"
    ) or []

    preferred_types = {
        "ADVISORY",
        "WEB",
        "REPORT",
    }

    for reference in references:

        url = reference.get(
            "url"
        )

        if not url:
            continue

        reference_type = str(
            reference.get(
                "type",
                ""
            )
        ).upper()

        if reference_type in preferred_types:
            return url

    for reference in references:

        url = reference.get(
            "url"
        )

        if url:
            return url

    return None


def extract_cve_id(vulnerability):
    """
    Extract a CVE alias when available.

    Otherwise use the OSV ID.
    """

    aliases = vulnerability.get(
        "aliases"
    ) or []

    for alias in aliases:

        if str(alias).upper().startswith(
            "CVE-"
        ):
            return alias

    return vulnerability.get(
        "id"
    )


def normalize_vulnerability(vulnerability):
    """
    Convert raw OSV data into DepGuard's
    internal vulnerability format.
    """

    return {
        "id": extract_cve_id(
            vulnerability
        ),
        "osv_id": vulnerability.get(
            "id"
        ),
        "summary": vulnerability.get(
            "summary",
            "No summary available."
        ),
        "severity": extract_severity(
            vulnerability
        ),
        "cvss": extract_cvss(
            vulnerability
        ),
        "advisory_url": extract_advisory_url(
            vulnerability
        ),
        "fixed_versions": extract_fixed_versions(
            vulnerability
        ),
    }


def scan_vulnerabilities(inventory):
    """
    Scan the complete inventory using OSV.

    IMPORTANT:
    This function ALWAYS returns the inventory list.
    Even if OSV is unavailable.
    """

    # Handle empty inventory safely.
    if not inventory:
        return []

    # Initialize vulnerability fields first.
    for package in inventory:

        package["vulnerabilities"] = []

        package["max_cvss"] = 0.0

    # Query OSV.
    batch_result = query_osv_batch(
        inventory
    )

    # If OSV is unavailable, return the
    # inventory instead of returning None.
    if not batch_result:

        print(
            "[OSV] Vulnerability service "
            "unavailable. Continuing with "
            "empty vulnerability results."
        )

        return inventory

    results = batch_result.get(
        "results"
    ) or []

    # Process each package result.
    for index, package in enumerate(
        inventory
    ):

        # OSV may return fewer results than
        # the number of queries.
        if index >= len(results):
            continue

        result = results[index]

        vulnerability_entries = (
            result.get(
                "vulns"
            )
            or []
        )

        for vulnerability_summary in (
            vulnerability_entries
        ):

            vulnerability_id = (
                vulnerability_summary.get(
                    "id"
                )
            )

            if not vulnerability_id:
                continue

            # Get complete vulnerability information.
            details = get_vulnerability_details(
                vulnerability_id
            )

            # If detail lookup fails, use
            # the information from batch response.
            if not details:

                details = (
                    vulnerability_summary
                )

            vulnerability = (
                normalize_vulnerability(
                    details
                )
            )

            package[
                "vulnerabilities"
            ].append(
                vulnerability
            )

            cvss = vulnerability.get(
                "cvss",
                0.0
            )

            try:
                cvss = float(cvss)
            except (
                ValueError,
                TypeError,
            ):
                cvss = 0.0

            if cvss > package[
                "max_cvss"
            ]:

                package[
                    "max_cvss"
                ] = cvss

    # CRITICAL:
    # Always return the modified inventory.
    return inventory

