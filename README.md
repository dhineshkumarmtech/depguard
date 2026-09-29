# DepGuard – Supply Chain Analyzer

DepGuard is a dependency supply-chain analyzer.

It reads dependency metadata and analyzes packages for:

- Vulnerabilities
- Integrity problems
- Suspicious traits
- Risk
- Software Bill of Materials (SBOM)

DepGuard never installs or executes packages.

## Tech Stack

- Python 3.10+
- FastAPI
- Uvicorn
- SQLite
- Requests
- Packaging
- ReportLab
- HTML
- CSS
- JavaScript

## Supported Dependency Files

- package.json
- requirements.txt
- pom.xml

## Development Phases

1. Project setup + parser
2. Dependency resolver
3. Vulnerability scanner
4. Integrity + database history
5. Suspicious detection
6. Risk scoring
7. SBOM
8. Reports
9. FastAPI + dashboard
