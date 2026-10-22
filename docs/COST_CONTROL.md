# Cost Control & Budget Guardrails

To prevent infinite recursion, network saturation, and runaway API costs, the engine enforces strict, configurable limits at both the application and investigation level.

## 1. Investigation Budget Parameters
- **Max Recursion Depth (`max_depth`)**: Default `3` (Configurable 1 to 5). Restricts lead expansion hops.
- **Max Total Queries (`max_total_queries`)**: Default `25` (Configurable 5 to 100). Hard cap on outbound searches.
- **Max Execution Time (`max_execution_seconds`)**: Default `600s` (10 minutes). Timed abort if operations stall.
- **Max Download Bytes (`max_download_bytes`)**: Default `50 MB`. Restricts cumulative bandwidth per investigation.
- **Max AI Tokens (`max_ai_tokens`)**: Default `25,000` tokens per investigation.
- **Monthly Spending Threshold (`AI_MONTHLY_SPEND_LIMIT_USD`)**: Application-wide spend cap.

## 2. Diminishing Returns Rule
If `5` consecutive queries return duplicate or zero new findings, the engine automatically halts expansion with the reason:
`"Diminishing returns: 5 consecutive queries returned no new information."`
