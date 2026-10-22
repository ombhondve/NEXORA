# Source Connectors & Integration Guide

The engine employs a pluggable connector architecture (`backend/src/recursive_osint/connectors/base.py`).

## 1. Implemented Free & Open Source Connectors

| Connector | Source Name | Auth Required? | Capabilities & Data Coverage |
| :--- | :--- | :--- | :--- |
| **Wikipedia Open Knowledge** | `wikipedia` | **None** | Global encyclopedic articles, biographical data, public corporate filings, history. |
| **Internet Archive CDX** | `internet_archive` | **None** | Millions of historical web captures, public texts, whitepapers, datasets. |
| **CrossRef Open Datasets** | `open_datasets` | **None** | Public scientific literature, DOI registrations, researcher names, technical affiliations. |
| **Mock Demo Source** | `mock_demo` | **None** | Deterministic simulated records for hermetic offline tests and zero-credential demos. |

## 2. Commercial Adapters (Optional)
The connector interface also supports commercial search engines when API keys are configured in `.env`:
- `TavilySearchConnector` (`TAVILY_API_KEY`)
- `SerperSearchConnector` (`SERPER_API_KEY`)
- `BraveSearchConnector` (`BRAVE_SEARCH_API_KEY`)

If API keys are omitted, the application operates smoothly with the free public connectors and clearly labels connector statuses in the dashboard.
