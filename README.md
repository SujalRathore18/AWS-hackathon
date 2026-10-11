# Climate Compass

Climate Compass is a human-friendly heat intelligence dashboard for students, commuters, outdoor workers, and sports participants. Its HeatShield safety check turns weather, activity, and outdoor duration into a clear risk level, practical actions, and a suggested safe-time budget.

## Fast local demo

Run the live local demo (it fetches current weather from Open-Meteo):

```powershell
python local_server.py
```

Open http://localhost:8080. Explore the dashboard, then select **Open heat safety check** and try different activities and durations. Stop the server with `Ctrl+C`.

## AWS implementation

The intended serverless deployment is defined in `template.yaml` using AWS SAM:

`EventBridge -> Lambda -> DynamoDB <- Lambda <- API Gateway`

The risk engine is in `src/risk.py`, weather ingestion is in `src/fetch_weather.py`, and the API handler is in `src/get_risk.py`.

Build and validate:

```powershell
sam validate --lint
sam build
python -m pytest tests -v
```

## Project structure

```text
src/risk.py            Shared explainable risk engine
src/fetch_weather.py   Scheduled Lambda weather ingestion
src/get_risk.py        API Gateway Lambda risk endpoint
local_server.py        Live local demo using the same risk engine
frontend/index.html    Climate Compass dashboard and HeatShield safety check
template.yaml          AWS SAM infrastructure
tests/                 Automated tests
```

Deployment may require an AWS Organization administrator to allow CloudFormation change sets. The current account has an explicit Service Control Policy deny, so the local demo is the working fallback.

## Limits

This is a transparent, rule-based awareness prototype using the NWS heat-index formula. It is not clinically validated, not medical advice, and does not replace official IMD warnings. No health information is stored.
