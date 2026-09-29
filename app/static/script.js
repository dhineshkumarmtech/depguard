const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const scanButton = document.getElementById("scanButton");
const statusBox = document.getElementById("status");

const results = document.getElementById("results");
const overallRisk = document.getElementById("overallRisk");
const overallScore = document.getElementById("overallScore");
const projectName = document.getElementById("projectName");

const packageCount = document.getElementById("packageCount");
const criticalCount = document.getElementById("criticalCount");
const mediumCount = document.getElementById("mediumCount");
const cleanCount = document.getElementById("cleanCount");

const packageTable = document.getElementById("packageTable");
const findings = document.getElementById("findings");


fileInput.addEventListener("change", () => {

    if (fileInput.files.length > 0) {
        fileName.textContent = fileInput.files[0].name;
        statusBox.textContent = "";
    } else {
        fileName.textContent = "No file selected";
    }

});


scanButton.addEventListener("click", async () => {

    if (fileInput.files.length === 0) {
        statusBox.textContent = "Please select a dependency file first.";
        return;
    }

    const file = fileInput.files[0];

    const formData = new FormData();
    formData.append("file", file);

    scanButton.disabled = true;
    scanButton.textContent = "Scanning...";
    statusBox.textContent = "Analyzing dependencies...";
    results.classList.add("hidden");

    try {

        const response = await fetch("/api/scan", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Scan failed.");
        }

        renderReport(data);

        statusBox.textContent = "Scan completed successfully.";
        results.classList.remove("hidden");

    } catch (error) {

        statusBox.textContent = `Error: ${error.message}`;

    } finally {

        scanButton.disabled = false;
        scanButton.textContent = "🔍 Scan Dependencies";

    }

});


function renderReport(report) {

    overallRisk.textContent = report.overall_risk.toUpperCase();
    overallScore.textContent = report.overall_score;
    projectName.textContent = report.project;

    packageCount.textContent = report.packages_scanned;

    const critical = report.results.filter(
        item => item.risk_band === "Critical"
    ).length;

    const medium = report.results.filter(
        item => item.risk_band === "Medium"
    ).length;

    const clean = report.results.filter(
        item => item.risk_band === "Low"
    ).length;

    criticalCount.textContent = critical;
    mediumCount.textContent = medium;
    cleanCount.textContent = clean;

    renderPackageTable(report.results);
    renderFindings(report.results);
}


function renderPackageTable(packages) {

    packageTable.innerHTML = "";

    packages.forEach(item => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td><strong>${escapeHtml(item.name)}</strong></td>
            <td>${escapeHtml(item.version)}</td>
            <td>
                <span class="risk-badge risk-${item.risk_band.toLowerCase()}">
                    ${escapeHtml(item.risk_band)}
                </span>
            </td>
            <td>${item.risk_score}/100</td>
            <td>${escapeHtml(item.integrity.status)}</td>
        `;

        packageTable.appendChild(row);
    });
}


function renderFindings(packages) {

    findings.innerHTML = "";

    packages.forEach(item => {

        const finding = document.createElement("div");
        finding.className = "finding";

        let content = `
            <div class="finding-title">
                ${escapeHtml(item.name)}@${escapeHtml(item.version)}
            </div>

            <p>
                Risk:
                <strong>
                    ${escapeHtml(item.risk_band)}
                    (${item.risk_score}/100)
                </strong>
            </p>

            <p>
                Integrity:
                <strong>${escapeHtml(item.integrity.status)}</strong>
            </p>
        `;

        if (item.vulnerabilities.length > 0) {

            item.vulnerabilities.forEach(vulnerability => {

                content += `
                    <div class="recommendation">
                        <strong>
                            🔴 ${escapeHtml(vulnerability.id)}
                        </strong>

                        <p>
                            Severity:
                            ${escapeHtml(vulnerability.severity)}
                        </p>

                        <p>
                            CVSS:
                            ${escapeHtml(String(vulnerability.cvss))}
                        </p>

                        <p>
                            ${escapeHtml(vulnerability.summary)}
                        </p>

                        <p>
                            Fixed in:
                            ${escapeHtml(
                                vulnerability.fixed_versions.join(", ")
                            )}
                        </p>
                    </div>
                `;
            });
        }

        if (item.suspicious_flags.length > 0) {

            content += `
                <div class="recommendation">
                    <strong>⚠ Suspicious Findings</strong>
            `;

            item.suspicious_flags.forEach(flag => {

                content += `
                    <p>• ${escapeHtml(flag)}</p>
                `;

            });

            content += `</div>`;
        }

        if (item.fix) {

            content += `
                <div class="recommendation">
                    <strong>Recommendation</strong>
                    <p>${escapeHtml(item.fix)}</p>
                </div>
            `;
        }

        finding.innerHTML = content;
        findings.appendChild(finding);
    });
}


function escapeHtml(value) {

    const div = document.createElement("div");
    div.textContent = value;
    return div.innerHTML;
}
