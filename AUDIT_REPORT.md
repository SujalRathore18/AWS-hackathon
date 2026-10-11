# Climate Compass / HeatShield AI Audit Report

Audit date: 2026-10-11  
Repository: `SujalRathore18/AWS-hackathon`  
Scope: frontend, local API, Lambda handlers, risk engine, SAM template, tests, documentation, and GitHub Pages behavior.

## Executive summary

The repository contains a coherent Python risk engine, local live-weather demo, AWS SAM template, Lambda handlers, automated risk tests, and a deployed static frontend. The main risks are product honesty and state handling rather than a broken core calculation: the dashboard contains representative city metrics that look live, the static-hosting fallback uses a single fixed extreme result, and the UI does not model live, demo, loading, error, or stale states explicitly.

The AWS deployment is not verified in the current account. Previous deployment attempts were blocked by an AWS Organizations Service Control Policy denying `cloudformation:CreateChangeSet`. This is an account-policy limitation and must not be bypassed.

## Findings

| ID | Severity | Area | Finding | Evidence / reproduction | Practical fix |
|---|---|---|---|---|---|
| F-01 | High | Frontend data honesty | The dashboard displays fixed Dubai/New York temperatures, variance, and “Live model” copy without a source, observation timestamp, or data-state label. | Open `frontend/index.html`; the comparison and chart values are literal markup and the globe header says “Live model”. | Label the visualization as illustrative/sample data, or wire it to a validated comparison API. Show source and timestamp for measured values. |
| F-02 | High | Demo behavior | GitHub Pages uses a single deterministic representative result, including a fixed extreme heat index, which can look like a current observation. | Open the public site, run the safety check, and inspect the “52.1°C” result. | Add explicit DEMO state and selectable lower/moderate/high/extreme sample scenarios. Never call sample values live. |
| F-03 | High | Error handling | A failed live request does not have a distinct user-facing ERROR state or retry action. | Stop `local_server.py` or make `/risk` unavailable and run the safety check. | Add explicit `LIVE`, `DEMO`, `LOADING`, `ERROR`, and `STALE` state handling with safe retry and recovery messaging. |
| F-04 | Medium | Risk model | The Rothfusz heat-index calculation is used without an explicit valid operating range or limitation in the response. | `src/risk.py:heat_index_c` always evaluates the formula; no range metadata is returned. | Document the approximation and return a calculation note when temperature/humidity are outside the supported range. Keep the result conservative and clearly heuristic. |
| F-05 | Medium | User guidance | `safe_minutes` is presented as a safe exposure budget, which can imply a guarantee despite being a heuristic. | `src/risk.py:BASE_MINUTES` and the frontend result text use “Suggested safe time”. | Rename to “conservative planning limit” or “consider limiting exposure to,” and show the model disclaimer next to it. |
| F-06 | Medium | Time handling | The local server evaluates current activity hour with `datetime.now().hour`, while Indore data is Asia/Kolkata. This can differ on machines configured for another timezone. | `local_server.py` passes `datetime.now().hour` to `risk.assess`. | Use an explicit Asia/Kolkata timezone for local calculations and use the weather observation timezone consistently. |
| F-07 | Medium | API reliability | The local server returns the raw exception string to the browser. This can expose implementation details and produces no structured error state. | `local_server.py` catches `Exception` and serializes `exc` into the response body. | Log a safe server-side diagnostic and return a generic error plus a stable error code. |
| F-08 | Medium | API contract | The Lambda silently changes unknown activities to `commute` and malformed minutes to `60`, making invalid input appear successful. | `src/get_risk.py:activity` and minutes parsing. | Validate input and return HTTP 400 with allowed values and bounds; keep defaults only when parameters are absent. |
| F-09 | Medium | Security | API Gateway and handler CORS allow every origin, and the API has no throttling or request validation. | `template.yaml` and `src/get_risk.py:HEADERS`. | Keep permissive CORS only for the public prototype if required, but document it; add bounded input validation and consider an API-specific allowed-origin parameter before production. |
| F-10 | Low | Accessibility | The dashboard uses decorative visualizations and buttons but has limited semantic status markup and no explicit reduced-motion rule. | `frontend/index.html` contains CSS globe/chart decoration and result updates without `aria-live`. | Add labels, live status announcements, keyboard-visible focus, and `prefers-reduced-motion`. |
| F-11 | Low | Documentation consistency | Documentation mixes HeatShield AI and Climate Compass naming and includes old generic repository instructions. | `README.md` and `HACKATHON_SUBMISSION.md`. | Use “Climate Compass — HeatShield AI” consistently and link the actual repository/live site. |
| F-12 | Informational | Deployment | The SAM template is present and previously validated/built, but deployment is not verified in the active AWS account. | AWS returned an explicit Organizations SCP deny for `cloudformation:CreateChangeSet`. | Keep the blocker visible, validate/build locally, and deploy only from an approved account with owner approval. |

## Confirmed architecture

- `template.yaml` defines DynamoDB, two Lambda functions, an HTTP API, an EventBridge schedule, CloudWatch alarm, and X-Ray tracing.
- `src/fetch_weather.py` writes the `Indore` weather item.
- `src/get_risk.py` reads the `Indore` item and optional `IMD_Indore` alert item.
- `local_server.py` fetches Open-Meteo directly and uses the same risk engine.
- The current static site is served by GitHub Pages; it cannot host `/risk`, so it requires an explicit demo mode unless an API URL is configured.

## Validation performed before changes

- Existing risk tests: 6 passed.
- Local dashboard flow: modal opens and local `/risk` returns a rendered result.
- GitHub Pages workflow for commit `6c49601`: successful.
- AWS deployment: not successful; blocked by the account Organizations policy described above.

## Prioritized implementation plan

1. Correct data-state and demo labeling in the frontend; remove “live” claims for illustrative metrics.
2. Add explicit sample scenarios and robust live-request error/stale handling.
3. Improve risk-model limitations and replace guaranteed-sounding exposure language.
4. Tighten local/Lambda input validation and safe error responses.
5. Fix explicit timezone use and add focused tests for new contracts.
6. Update documentation and run the targeted test, SAM, and browser validation commands available in the environment.

## Post-fix verification

The prioritized fixes were implemented in commit `e00706d`:

- Frontend sample cards and visualizations are labelled illustrative.
- GitHub Pages exposes four selectable DEMO scenarios and does not call demo values live.
- Local API responses show LIVE state, retrieval time, and model limitations; invalid input returns HTTP 400.
- Live request failures render an ERROR state instead of silently substituting sample data.
- Risk output calls the exposure number a conservative planning limit.
- Local calculations use the explicit Asia/Kolkata timezone.
- Status updates use screen-reader-friendly live regions and reduced-motion CSS.

Verification completed:

- `python -m pytest tests -q`: 8 passed.
- `python -m py_compile src\risk.py src\get_risk.py src\fetch_weather.py local_server.py`: passed.
- Local browser flow on port 8081: LIVE API response rendered with timestamp and model note.
- Invalid local request: `/risk?activity=bad&minutes=60` returned HTTP 400.
- Public GitHub Pages flow: Cool sample rendered as `DEMO · sample data` and explicitly stated that it was not a current observation.
- GitHub Pages workflow run for `e00706d`: successful.
- `sam validate --lint`: unavailable in the final shell because `sam` was not on PATH; prior repository validation/build remains documented, and AWS deployment remains blocked by the Organizations policy.
