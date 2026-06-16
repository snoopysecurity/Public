# Scoring & Prioritization

`repo-intel` calculates an **Audit Priority** score (0-100) for every finding to help you decide where to start your review.

The goal is to bubble up **high-confidence, high-value** signals while suppressing noise.

---

## 1. The Priority Formula

The engine calculates priority using a balanced formula:

```python
Priority = Confidence * (Research Value + Impact) / 2
```

*The result is scaled to a 0-100 integer.*

### The Components (0.0 - 1.0)

| Component | Question it answers | Examples |
| :--- | :--- | :--- |
| **Confidence** | *How likely is this signal real?* | High for SAST/CVEs. Lower for keyword matches. |
| **Research Value** | *Is this code interesting to a human?* | High for Auth/Crypto. Low for documentation. |
| **Impact** | *How bad is it if exploited?* | High for RCE/SQLi. Low for informational findings. |

---

## 2. Module Scoring Defaults

Each module defines its own base scores (1-10), which are normalized to 0.0-1.0.

| Module Source | Typical Scores | Reasoning |
| :--- | :--- | :--- |
| **Semgrep / SAST** | **9** (High) | Code patterns are specific and reliable. |
| **Exploits / CVEs** | **8-10** (High) | Verified vulnerabilities or known exploits. |
| **GitHub Issues** | **4 - 8** (Variable) | "High Precision" keywords (e.g., "RCE") get 8s.<br>Generic keywords get 4s. |
| **Commits / PRs** | **5** (Medium) | Contextual signals that need verification. |

---

## 3. Cross-Signal Reinforcement (The "Boost")

The system rewards **converging evidence**.

*   **Rule:** If a file contains findings from **2 or more different modules** (e.g., a Semgrep match AND a suspicious Commit), it gets a **+20 Point Boost**.
*   **Effect:** A medium-priority file can jump to high-priority if multiple tools agree it's interesting.
*   **Indicator:** You will see `[🔥 Cross-Signal Boost]` in the priority reason.

---

## 4. Noise Reduction (Blacklists)

To prevent wasting time on tests or docs, the system applies strict penalties **before** calculating priority.

### A. Filepath Blacklist
*   **Target:** `test/`, `spec/`, `mock/`, `docs/`, `fixtures/`, etc.
*   **Effect:** 
    *   **Research Value & Impact** reduced to **0.1** (Near zero).
    *   **Severity** forced to **Info**.
    *   **Confidence** capped.

### B. Content Blacklist
*   **Target:** Common false positive terms in titles/descriptions.
*   **Effect:** Same penalties as above (Impact/Research -> 0.1).

---

## 5. Hotspots

The dashboard groups findings into **Hotspots** based on these scores:

1.  **CVE Hotspots:** Grouped by CVE ID. Sorted by max priority.
2.  **File Hotspots:** Grouped by File Path. The file's score is the **highest priority score** of any finding within it.
