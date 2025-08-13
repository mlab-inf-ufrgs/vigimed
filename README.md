# 💊 VigiMed
This project aims to centralize the ingestion, processing, compression, and visualization of [VigiMed](https://dados.anvisa.gov.br/dados/) data in Brazil.

The VigiMed datasets are updated once a week and avaible in csv format.
- `VigiMed_Notificacoes.csv`
- `VigiMed_Medicamentos.csv`
- `VigiMed_Reacoes.csv`

 
# 🌳  Project Folder Overview

```bash
dengue/
├── config/                    # Configuration files (e.g., parameters, paths, credentials)
├── dashboard/powerbi/         # Power BI dashboards and reports
├── data/                      # Data storage, organized by processing layer
│   └── staging/               # Temporary zone for data loading and testing
│   ├── bronze/                # Raw data as collected from external sources
│   ├── silver/                # Cleaned and transformed data
│   ├── gold/                  # Aggregated and enriched data for analytics
├── docs/                      # Project documentation
├── root/                      # Root-level utilities for project setup or orchestration
│   └── requirements.txt       # Python dependencies required for the project
├── src/                       # Source code for data ingestion, processing, and helpers
│   ├── cnes/                  # Scripts to process CNES (National Registry of Health Facilities) data
│   ├── vigimed/               # Scripts to process Vigimed (Notifiable Diseases) data
│   └── utils/                 # Utility functions and tools
│       └── compression_for_parquet.py  # Function to split large Parquet files into chunks
├── tests/                     # Unit and integration tests
```
