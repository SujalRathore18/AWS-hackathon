# Climate Compass - Hackathon Submission

## One-line summary

Climate Compass presents global heat patterns and includes a HeatShield safety check that turns Indore weather into an explainable outdoor-safety decision for students, commuters, and outdoor workers.

## Environmental problem and beneficiaries

Extreme heat can make a normal commute or outdoor task unsafe, but weather apps usually show only temperature. HeatShield AI combines temperature, humidity, activity, planned duration, time of day, and an optional heat-sensitivity setting to explain the risk and suggest safer actions.

The primary beneficiaries are:

- Students commuting across Indore
- Outdoor and delivery workers
- Sports participants
- Older adults and people who are more heat-sensitive

The app does not store health information and does not replace official IMD warnings.

## Working feature

The user selects an activity and time outdoors. The application returns:

- Low, Moderate, High, or Extreme risk
- A plain-language explanation
- Recommended protective actions
- Suggested safe outdoor minutes
- Best hours in the next 12 hours
- Current weather source and update timestamp

The local demonstration uses live Open-Meteo weather through `local_server.py`. The same risk engine is used by the AWS Lambda API implementation.

## AWS usage

The project uses AWS SAM, an AWS open-source infrastructure and deployment tool. The deployable architecture in `template.yaml` contains:

```text
EventBridge schedule
        -> fetch_weather Lambda
        -> DynamoDB WeatherCache

Browser
        -> API Gateway HTTP API
        -> get_risk Lambda
        -> DynamoDB WeatherCache

CloudWatch alarm + X-Ray tracing
```

The deployment account currently has an AWS Organizations Service Control Policy that explicitly denies `cloudformation:CreateChangeSet`. Therefore deployment cannot be completed from this account without an organization administrator. This is an account-policy limitation, not an application build failure. The SAM template validates and builds successfully.

## Evidence of execution

Run:

```powershell
python -m pytest tests -v
```

Expected:

```text
6 passed
```

Run the working demo:

```powershell
python local_server.py
```

Open http://localhost:8080.

Validate and build the AWS implementation:

```powershell
sam validate --lint
sam build --build-dir ".aws-sam\final-build"
```

## Three-minute demo script

### 0:00-0:30 - Problem and users

“Heat affects everyday decisions in Indore. A weather app may show 38 degrees, but it does not explain whether a student's commute or an outdoor worker's three-hour task is risky. HeatShield AI is designed for students, commuters, and outdoor workers.”

### 0:30-1:20 - Working application

Open the app at http://localhost:8080 or use the public dashboard at https://sujalrathore18.github.io/AWS-hackathon/.

1. Select **Open heat safety check**.
2. Select **Commute**, 60 minutes, and click **Check my risk**.
3. Select **Outdoor work**, 180 minutes, and click again.
4. Select **Sports** and compare the result.

Say:

“The dashboard makes the climate context easy to scan, then the connected safety check explains why the level changed, gives practical actions, estimates a safe-time budget, and identifies better hours. The user gets a decision, not just a weather number.”

### 1:20-1:50 - Safety and transparency

Show the source, timestamp, IMD reminder, and disclaimer.

Say:

“The model is a transparent awareness heuristic. It is not medical advice and does not replace official IMD warnings. The sensitivity option is used only for the current calculation.”

### 1:50-2:30 - AWS implementation

Open `template.yaml` and show the Lambda, DynamoDB, API Gateway, EventBridge, CloudWatch, and X-Ray resources. On GitHub Pages, the safety check uses a clearly labeled representative demo reading because static hosting cannot provide the `/risk` API.

Say:

“The production path is packaged with AWS SAM. EventBridge refreshes weather, Lambda computes the risk, DynamoDB caches the data, and API Gateway serves the browser.”

### 2:30-2:50 - Testing

Show the terminal output:

```text
6 passed
SAM template valid
SAM build succeeded
```

### 2:50-3:00 - Honest deployment note

“This account is managed by an AWS Organization whose Service Control Policy blocks CloudFormation change sets. The application and SAM package are complete; an organization administrator can deploy the same template in an approved account. The public GitHub Pages dashboard is live for review.”

## Source code

Publish this project folder to a GitHub repository:

```powershell
cd "C:\Users\Asus\OneDrive\Desktop\AWS"
git add .
git commit -m "Build HeatShield AI hackathon application"
git remote add origin https://github.com/YOUR_USERNAME/heatshield-ai.git
git push -u origin master
```

Replace the repository URL with the actual empty GitHub repository URL. Never publish `.aws` credentials, access keys, secret keys, or OTPs.

## Limitations and future work

- The risk model is rule-based and not clinically validated.
- The MVP does not automatically ingest IMD alerts.
- Open-Meteo attribution is required.
- Future versions can add Hindi labels, offline support, automated official alerts, and opt-in notifications.
