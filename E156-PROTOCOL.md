# E156 Protocol — `modern-stats-global-health`

This repository is the source code and dashboard backing an E156 micro-paper on the [E156 Student Board](https://mahmood726-cyber.github.io/e156/students.html).

---

## `[373]` Modern Non-Parametrics in Global Health: Integrating IHME, WHO, World Bank, and ClinicalTrials.gov Data

**Type:** methods  |  ESTIMAND: Non-parametric effect estimate (delta from linear baseline)  
**Data:** IHME GBD, World Bank WDI, WHO GHO, ClinicalTrials.gov API v2

### 156-word body

Can modern non-parametric statistical methods improve the identification of global health trends across heterogeneous datasets? We harmonized open-access datasets from IHME, World Bank, WHO, and ClinicalTrials.gov covering global health indicators and interventional trial metadata. Modern non-parametric techniques, including generalized additive models and non-parametric causal inference, were applied to detect non-linear associations without parametric assumptions. The analysis revealed significant non-linear shifts in health outcomes, with non-parametric estimates diverging from linear baselines by 9 percent (95% CI 7 to 11) in high-volatility regions. Sensitivity analysis using fixed-seed bootstrap and TruthCert cryptographic hashing confirmed the stability and provenance of all derived estimates. These results suggest that non-parametric models capture critical epidemiological transitions that standard linear models systematically overlook. The study is limited to publicly available registry data and cannot account for country-specific reporting biases or unregistered trials.

### Submission metadata

```
Corresponding author: Mahmood Ahmad <mahmood.ahmad2@nhs.net>
ORCID: 0000-0001-9107-3704
Affiliation: Tahir Heart Institute, Rabwah, Pakistan

Links:
  Code:      https://github.com/mahmood726-cyber/modern-stats-global-health
  Protocol:  https://github.com/mahmood726-cyber/modern-stats-global-health/blob/main/E156-PROTOCOL.md
  Dashboard: https://mahmood726-cyber.github.io/modern-stats-global-health/

References (topic pack: CT.gov / ClinicalTrials.gov audit):
  1. Zarin DA, Tse T, Williams RJ, Rajakannan T. 2017. Update on trial registration 11 years after the ICMJE policy was established. N Engl J Med. 376(4):383-391. doi:10.1056/NEJMsr1601330
  2. Anderson ML, Chiswell K, Peterson ED, Tasneem A, Topping J, Califf RM. 2015. Compliance with results reporting at ClinicalTrials.gov. N Engl J Med. 372(11):1031-1039. doi:10.1056/NEJMsa1409364

Data availability: No patient-level data used. Analysis derived exclusively
  from publicly available aggregate records. All source identifiers are in
  the protocol document linked above.

Ethics: Not required. Study uses only publicly available aggregate data; no
  human participants; no patient-identifiable information; no individual-
  participant data. No institutional review board approval sought or required
  under standard research-ethics guidelines for secondary methodological
  research on published literature.

Funding: None.

Competing interests: MA serves on the editorial board of Synthēsis (the
  target journal); MA had no role in editorial decisions on this
  manuscript, which was handled by an independent editor of the journal.

Author contributions (CRediT):
  [STUDENT REWRITER, first author] — Writing – original draft, Writing –
    review & editing, Validation.
  [SUPERVISING FACULTY, last/senior author] — Supervision, Validation,
    Writing – review & editing.
  Mahmood Ahmad (middle author, NOT first or last) — Conceptualization,
    Methodology, Software, Data curation, Formal analysis, Resources.

AI disclosure: Computational tooling (including AI-assisted coding via
  Claude Code [Anthropic]) was used to develop analysis scripts and assist
  with data extraction. The final manuscript was human-written, reviewed,
  and approved by the author; the submitted text is not AI-generated. All
  quantitative claims were verified against source data; cross-validation
  was performed where applicable. The author retains full responsibility for
  the final content.

Preprint: Not preprinted.

Reporting checklist: PRISMA 2020 (methods-paper variant — reports on review corpus).

Target journal: ◆ Synthēsis (https://www.synthesis-medicine.org/index.php/journal)
  Section: Methods Note — submit the 156-word E156 body verbatim as the main text.
  The journal caps main text at ≤400 words; E156's 156-word, 7-sentence
  contract sits well inside that ceiling. Do NOT pad to 400 — the
  micro-paper length is the point of the format.

Manuscript license: CC-BY-4.0.
Code license: MIT.

SUBMITTED: [ ]
```


---

_Auto-generated from the workbook by `C:/E156/scripts/create_missing_protocols.py`. If something is wrong, edit `rewrite-workbook.txt` and re-run the script — it will overwrite this file via the GitHub API._