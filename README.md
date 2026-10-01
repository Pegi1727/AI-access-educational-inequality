# Decoupling Education from Geopolitics: AI Accessibility, Educational Inequality, and Educational Resilience in Sanctioned Environments

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23075043.svg)](https://doi.org/10.5281/zenodo.23075043)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![R 4.0+](https://img.shields.io/badge/R-4.0+-blue.svg)](https://www.r-project.org/)
[![Reproducibility](https://img.shields.io/badge/Reproducibility-Verified-success.svg)]()

---

## 📌 Overview

This repository provides open research materials, reproducible statistical analysis pipelines, and supplementary datasets for the study:

> **Merrikhi, P.** (2026). *Decoupling Education from Geopolitics: AI Accessibility, Educational Inequality, and Educational Resilience in Sanctioned Environments*. 

The research investigates the structural disparities arising from unequal access to state-of-the-art Generative AI tools (Premium vs. Free tiers) in geopolitical sanctioned contexts, framing the findings within **UN Sustainable Development Goal 4 (Quality Education)**.

---

## 📂 Repository Structure
```text
AI-access-educational-inequality/
│
├── data/
│   ├── SDG4_Quant_Data.csv             # Quantitative outcome measures (n = 60)
│   ├── SDG4_Codebook.csv               # Variable definitions and scale metadata
│   ├── SDG4_Qual_Codes.csv             # Qualitative thematic codebook
│   └── qualitative_transcripts/        # Synthetic transcript exemplars (SYN-FREE / SYN-PREMIUM)
│
├── notebooks/
│   ├── analysis_sdg4.ipynb             # Executed Python Jupyter Notebook
│   └── analysis_sdg4_R.ipynb           # R Jupyter Notebook
│
├── scripts/
│   ├── analysis_sdg4.py                # Standalone Python replication script
│   └── analysis_sdg4.R                 # Standalone R replication script
│
├── Figures/
│   ├── graphical_abstract.png          # Visual abstract of the conceptual framework
│   ├── group_means_95ci.png            # Main statistical comparison plot
│   └── sdg1.jpg - sdg4.jpg             # Contextual SDG target figures
│
├── supplementary/
│   ├── Appendices.docx
│   └── Supplementary_Materials_Final.docx
│
├── LICENSE
└── README.md
