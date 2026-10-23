# 🛡️ DepGuard – Dependency Supply Chain Analyzer

**Secure your software supply chain, one dependency at a time.**

DepGuard is a Python-based dependency supply-chain security analyzer designed to help developers identify potential security threats and reliability issues in third-party packages. It analyzes dependency metadata to detect known vulnerabilities, integrity problems, suspicious package characteristics, and potential risks without installing or executing packages.

The project aims to improve software supply-chain security by providing dependency analysis, risk assessment, Software Bill of Materials (SBOM) generation, and security reports through a web-based dashboard.

## 🚀 Key Features

- **Vulnerability Detection** – Analyze dependencies for known security vulnerabilities.
- **Integrity Analysis** – Identify potential package integrity issues and suspicious version changes.
- **Suspicious Package Detection** – Flag potentially risky package characteristics for further investigation.
- **Risk Scoring** – Assign risk scores to dependencies to help prioritize security reviews.
- **Dependency Analysis** – Parse supported dependency files and inspect declared packages.
- **SBOM Generation** – Generate a Software Bill of Materials to document project dependencies.
- **Security Reports** – Produce downloadable reports summarizing dependency findings.
- **Dependency History** – Use SQLite to maintain analysis history and support comparisons.
- **Web Dashboard** – Provide a FastAPI-powered interface for submitting projects and reviewing results.
- **Safe Analysis by Design** – Never install or execute the packages being analyzed.

## 📂 Supported Dependency Files

| File format | Ecosystem |
|---|---|
| `package.json` | Node.js / JavaScript |
| `requirements.txt` | Python |
| `pom.xml` | Java / Maven |

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Backend:** FastAPI
- **ASGI Server:** Uvicorn
- **Database:** SQLite
- **HTTP Requests:** Requests
- **Package Version Handling:** Packaging
- **Report Generation:** ReportLab
- **Frontend:** HTML, CSS, JavaScript

## 🏗️ Development Roadmap

DepGuard is organized into the following development phases:

1. **Project Setup and Parser** – Establish the project structure and parse supported dependency files.
2. **Dependency Resolver** – Resolve and normalize dependency metadata and version information.
3. **Vulnerability Scanner** – Check dependencies against available vulnerability information.
4. **Integrity Analysis and Database History** – Track package metadata and historical changes.
5. **Suspicious Package Detection** – Identify potentially suspicious package characteristics.
6. **Risk Scoring** – Calculate risk scores based on identified security indicators.
7. **SBOM Generation** – Generate a Software Bill of Materials for analyzed projects.
8. **Report Generation** – Create security reports containing findings and risk summaries.
9. **FastAPI and Dashboard** – Integrate the analysis pipeline with a web API and dashboard.

## 🔒 Security Philosophy

DepGuard follows a metadata-first analysis approach. It does not install or execute third-party packages during analysis, reducing the risk associated with inspecting potentially malicious dependencies.

**Important:** DepGuard is intended to assist security reviews. Its findings depend on the metadata, vulnerability sources, and detection rules available to the analyzer. It should complement—not replace—other software security practices.

## 🎯 Project Goals

- Improve visibility into third-party software dependencies.
- Help developers identify potentially vulnerable or suspicious packages.
- Support software supply-chain risk assessment.
- Improve dependency traceability through SBOM generation.
- Provide understandable security reports for development and security teams.

## 👨‍💻 Intended Audience

- Software developers
- Cybersecurity students and researchers
- Application security engineers
- DevSecOps teams
- Software supply-chain security enthusiasts

## 📌 Project Status

**Development in progress.** Features are being implemented incrementally according to the development roadmap.

## 🔗 Repository

Explore the source code, follow development progress, and contribute:

[DepGuard on GitHub](https://github.com/dhineshkumarmtech/depguard)

## ⚖️ Disclaimer

DepGuard provides automated security analysis to support informed decision-making. A clean report does not guarantee that a dependency or software project is completely secure.
