# KubeTriage — Project Guideline

> An AI agent app to detect and assist in debugging incidents in Kubernetes clusters.
> Built with FastAPI, Claude (Anthropic API), Prometheus, and GitHub Actions.

---

## Overview

KubeTriage is a two-phase project. Phase 1 builds and validates the full agent pipeline locally using Docker Desktop Kubernetes. Phase 2 deploys it to EKS with a CI/CD pipeline and automated chaos testing to verify agent accuracy.

```
Alertmanager → FastAPI webhook → AI agent (Claude) → Email notification
                                      ↓
                              k8s read-only tools
                          (describe · events · logs)
```

---

## Phase 1 — Local (Docker Desktop Kubernetes)

### Step 1.1 — Infrastructure setup

**Goal:** Deploy the observability stack and a test workload.

**Tasks:**

- Enable Kubernetes in Docker Desktop settings
- Deploy nginx as a simple target workload:
  ```bash
  kubectl create deployment nginx --image=nginx:latest --replicas=2
  kubectl expose deployment nginx --port=80
  ```
- Install Prometheus + Grafana via Helm:
  ```bash
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm repo update
  helm install monitoring prometheus-community/kube-prometheus-stack \
    --namespace monitoring --create-namespace
  ```
- Verify Prometheus scrapes the nginx deployment and Grafana is accessible at `localhost:3000`

**Deliverables:**

- `monitoring/helm/values.yaml` — custom Prometheus/Grafana values
- Grafana dashboard accessible with nginx request metrics visible

---

### Step 1.2 — Incident simulation & alert rules

**Goal:** Create 4 reproducible test incidents, each with a manifest, a PrometheusRule, and a ground-truth fixture entry.

#### Incident matrix

| Incident           | Simulation method                  | Key Prometheus metric                      |
| ------------------ | ---------------------------------- | ------------------------------------------ |
| `ImagePullBackOff` | Bad image tag in deployment spec   | `kube_pod_container_status_waiting_reason` |
| `OOMKilled`        | `memory: "10Mi"` resource limit    | `container_oom_events_total`               |
| `ConfigError`      | Missing ConfigMap reference in env | `kube_pod_status_phase{phase="Failed"}`    |
| `CrashLoopBackOff` | App exits non-zero on start        | `kube_pod_container_status_restarts_total` |

**Tasks:**

- Create `manifests/incidents/` folder with one YAML per incident:
  - `imagepull.yaml` — deployment with `image: nginx:does-not-exist`
  - `oom.yaml` — deployment with `resources.limits.memory: "10Mi"`
  - `configerror.yaml` — deployment referencing a non-existent ConfigMap
  - `crashloop.yaml` — deployment with `command: ["/bin/sh", "-c", "exit 1"]`
- Create `prometheus/alert-rules.yaml` with one PrometheusRule per incident
- Create `tests/fixtures/incident_fixtures.yaml` mapping each `alertname` to:
  - `expected_category` — exact string (used in phase 2 evaluation)
  - `expected_keywords` — list of strings that must appear in agent remediation output

**Example fixture entry:**

```yaml
- alertname: KubePodCrashLooping
  expected_category: CrashLoopBackOff
  expected_keywords:
    - restart
    - exit code
    - kubectl logs
```

**Alertmanager webhook route config** (add to `alertmanager.yaml`):

```yaml
receivers:
  - name: kubetriage-webhook
    webhook_configs:
      - url: http://kubetriage:8000/webhook/alertmanager
        send_resolved: false
route:
  receiver: kubetriage-webhook
```

**Deliverables:**

- `manifests/incidents/*.yaml` (4 files)
- `prometheus/alert-rules.yaml`
- `tests/fixtures/incident_fixtures.yaml`

---

### Step 1.3 — FastAPI webhook receiver

**Goal:** A thin HTTP listener that validates, deduplicates, and enqueues alerts.

**Project folder layout:**

```
app/
  main.py               # FastAPI app init, router registration
  webhook.py            # POST /webhook/alertmanager
  agent.py              # background agent runner
  k8s_tools.py          # describe_pod, get_pod_events, get_pod_logs
  claude_client.py      # Claude API tool-use loop
  notifier.py           # SMTP email formatter + sender
  dedup.py              # in-memory dedup cache with TTL
  models.py             # Pydantic models for alert payloads
tests/
  test_webhook.py
  test_agent.py
  fixtures/
    incident_fixtures.yaml
manifests/
  incidents/
helm/
prometheus/
```

**Deduplication logic** (`dedup.py`):

- Key: `f"{alertname}:{namespace}:{pod}"`
- TTL: 10 minutes
- Use a simple `dict` with timestamp; for production use Redis

**`POST /webhook/alertmanager` behaviour:**

1. Parse and validate payload with Pydantic `AlertmanagerPayload` model
2. For each alert in `alerts[]` where `status == "firing"`:
   - Compute dedup key
   - If key is in cache and not expired → skip (return 200, log "deduped")
   - Otherwise → add to cache, enqueue `BackgroundTask` to run agent
3. Return `{"status": "accepted"}` immediately (never block on agent)

**Add a results endpoint for phase 2 testing:**

```python
GET /results/{dedup_key}
# Returns the last agent report for that key, or 404 if not yet available
```

Store agent results in a simple in-memory dict keyed by dedup key.

**Test the webhook manually:**

```bash
curl -X POST http://localhost:8000/webhook/alertmanager \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/sample_alert.json
```

**Deliverables:**

- `app/webhook.py`, `app/dedup.py`, `app/models.py`
- `tests/test_webhook.py` with at least: valid payload accepted, duplicate rejected, malformed payload returns 422

---

### Step 1.4 — AI agent with Claude tool-use

**Goal:** A background worker that collects Kubernetes context and calls Claude to produce a structured triage report.

#### Kubernetes RBAC setup

```yaml
# k8s/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kubetriage
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kubetriage-readonly
rules:
  - apiGroups: [""]
    resources: ["pods", "events", "namespaces"]
    verbs: ["get", "list"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kubetriage-readonly-binding
subjects:
  - kind: ServiceAccount
    name: kubetriage
    namespace: default
roleRef:
  kind: ClusterRole
  name: kubetriage-readonly
  apiGroup: rbac.authorization.k8s.io
```

#### Tool schema (define in `claude_client.py`)

```python
TOOLS = [
    {
        "name": "get_pod_info",
        "description": "Returns kubectl describe output for a specific pod.",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "pod_name": {"type": "string"}
            },
            "required": ["namespace", "pod_name"]
        }
    },
    {
        "name": "get_pod_events",
        "description": "Returns recent Kubernetes events for a pod.",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "pod_name": {"type": "string"}
            },
            "required": ["namespace", "pod_name"]
        }
    },
    {
        "name": "get_pod_logs",
        "description": "Returns the last N lines of logs from a pod container.",
        "input_schema": {
            "type": "object",
            "properties": {
                "namespace": {"type": "string"},
                "pod_name": {"type": "string"},
                "tail": {"type": "integer", "default": 50}
            },
            "required": ["namespace", "pod_name"]
        }
    }
]
```

#### System prompt (in `claude_client.py`)

```
You are KubeTriage, an SRE assistant that diagnoses Kubernetes pod incidents.

When given an alert, you must:
1. Always call get_pod_info and get_pod_events before concluding.
2. Call get_pod_logs only if the above tools suggest an application error.
3. Classify the incident into exactly one category:
   ImagePullBackOff | OOMKilled | ConfigError | CrashLoopBackOff | Unknown
4. Respond in this exact structure:

CATEGORY: <one of the above>
ROOT_CAUSE: <one sentence>
REMEDIATION:
- <step 1>
- <step 2>
KUBECTL_COMMAND: <the single most useful kubectl command for the engineer>
ESCALATE: yes | no
```

#### Agent loop constraints

- Maximum tool iterations: **5**
- `max_tokens` on final response: **1500**
- Model: `claude-sonnet-4-6`
- API key: read from `ANTHROPIC_API_KEY` environment variable (mounted from k8s Secret — never hardcoded)

#### Kubernetes Secret for API key

```bash
kubectl create secret generic kubetriage-secrets \
  --from-literal=ANTHROPIC_API_KEY=sk-ant-...
```

Reference in deployment:

```yaml
env:
  - name: ANTHROPIC_API_KEY
    valueFrom:
      secretKeyRef:
        name: kubetriage-secrets
        key: ANTHROPIC_API_KEY
```

**Deliverables:**

- `app/k8s_tools.py`, `app/claude_client.py`, `app/agent.py`
- `k8s/serviceaccount.yaml`, `k8s/clusterrole.yaml`, `k8s/clusterrolebinding.yaml`
- `tests/test_agent.py` — unit tests with mocked tool responses

---

### Step 1.5 — Email notification

**Goal:** Format the Claude response into a readable engineer notification.

**Email structure:**

```
Subject: [KubeTriage] <CATEGORY> — <namespace>/<pod>

Incident:   <alertname>
Namespace:  <namespace>
Pod:        <pod>
Detected:   <timestamp>

Category:     <CATEGORY>
Root cause:   <ROOT_CAUSE>

Remediation:
  1. <step>
  2. <step>

Suggested command:
  $ <KUBECTL_COMMAND>

Escalate: <yes/no>
```

**Configuration** (environment variables):

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=<app password>
NOTIFY_TO=engineer@yourteam.com
```

Mount SMTP credentials from a k8s Secret (same pattern as API key above).

**Deliverables:**

- `app/notifier.py`
- Integration test: agent result → formatted email string (no live SMTP needed)

---

## Phase 2 — EKS

### Step 2.1 — CI/CD pipeline with GitHub Actions

**Goal:** Automate build, push to ECR, and deploy to EKS on every push to `main`.

#### Required GitHub Secrets

| Secret             | Purpose                                          |
| ------------------ | ------------------------------------------------ |
| `AWS_ROLE_ARN`     | IRSA role ARN for OIDC authentication            |
| `ECR_REGISTRY`     | e.g. `123456789.dkr.ecr.us-east-1.amazonaws.com` |
| `EKS_CLUSTER_NAME` | EKS cluster name                                 |
| `EKS_REGION`       | AWS region                                       |

> Use IRSA (IAM Roles for Service Accounts) with OIDC — avoid static `AWS_ACCESS_KEY_ID` credentials entirely.

#### Workflow: `deploy.yml`

Triggered on: `push` to `main`

```
job: test
  → pytest, lint (ruff), type check (mypy)

job: build-push  (needs: test)
  → docker build
  → push to ECR, tag with git SHA

job: deploy-eks  (needs: build-push)
  → aws-actions/configure-aws-credentials (OIDC)
  → update kubeconfig
  → helm upgrade --install kubetriage ./helm \
      --set image.tag=${{ github.sha }} \
      --namespace kubetriage --create-namespace
```

**Helm chart structure (`helm/`):**

```
Chart.yaml
values.yaml
templates/
  deployment.yaml
  service.yaml
  serviceaccount.yaml   # annotated with IRSA role ARN
  secret.yaml           # ANTHROPIC_API_KEY + SMTP creds
  prometheusrule.yaml   # alert rules
```

**Deliverables:**

- `.github/workflows/deploy.yml`
- `helm/` chart with all templates
- IAM role + IRSA annotation on ServiceAccount

---

### Step 2.2 — Chaos testing & agent evaluation

**Goal:** Automatically inject random incidents into EKS and verify the agent categorises and advises correctly.

#### Workflow: `chaos-test.yml`

Triggered on: `workflow_dispatch` (manual) or `schedule` (e.g. weekly)

```
job: inject-incident
  → randomly pick one file from manifests/incidents/
  → kubectl apply -f <chosen manifest>
  → output the chosen incident name as a step output

job: wait-for-agent  (needs: inject-incident)
  → poll GET /results/<dedup_key> every 15s
  → timeout after 3 minutes
  → save agent JSON response as artifact

job: evaluate  (needs: wait-for-agent)
  → python tests/evaluate.py \
      --incident ${{ needs.inject-incident.outputs.incident_name }} \
      --result agent_result.json
  → exit 0 = pass, exit 1 = fail (fails the workflow)

job: cleanup  (always runs)
  → kubectl delete -f <chosen manifest>
```

#### Evaluation script (`tests/evaluate.py`)

```python
# Loads incident_fixtures.yaml
# Checks:
#   1. result["category"] == fixture["expected_category"]   (exact match)
#   2. All fixture["expected_keywords"] appear in result["remediation"]
# Prints pass/fail summary
# sys.exit(1) on any failure
```

**Deliverables:**

- `.github/workflows/chaos-test.yml`
- `tests/evaluate.py`
- Passing chaos test run for all 4 incident types

---

## Key decisions reference

| Decision             | Choice                                   | Reason                          |
| -------------------- | ---------------------------------------- | ------------------------------- |
| LLM                  | Claude (`claude-sonnet-4-6`)             | Tool-use API, structured output |
| CI/CD                | GitHub Actions only                      | Simple, no extra tooling        |
| AWS auth             | IRSA + OIDC                              | No long-lived credentials       |
| Alert dedup          | In-memory dict (TTL 10 min)              | Sufficient for single-instance  |
| Agent max iterations | 5                                        | Prevents runaway tool loops     |
| Secrets at runtime   | k8s Secret + External Secrets            | Never in CI env vars            |
| Evaluation           | `incident_fixtures.yaml` + `evaluate.py` | Scriptable pass/fail            |

---

## Incident fixture schema reference

```yaml
# tests/fixtures/incident_fixtures.yaml
incidents:
  - alertname: KubePodImagePullBackOff
    expected_category: ImagePullBackOff
    expected_keywords: [image, pull, registry, tag]

  - alertname: KubePodOOMKilled
    expected_category: OOMKilled
    expected_keywords: [memory, limit, OOM, increase]

  - alertname: KubePodConfigError
    expected_category: ConfigError
    expected_keywords: [configmap, env, missing, mount]

  - alertname: KubePodCrashLooping
    expected_category: CrashLoopBackOff
    expected_keywords: [restart, exit code, kubectl logs]
```

---

## Suggested build order

1. `manifests/incidents/` + `incident_fixtures.yaml`
2. `app/models.py` + `app/dedup.py`
3. `app/webhook.py` + `app/main.py` (test with curl)
4. `k8s/` RBAC manifests + `app/k8s_tools.py`
5. `app/claude_client.py` (test with a single manual alert)
6. `app/agent.py` wiring webhook → agent → result store
7. `app/notifier.py` + SMTP config
8. Full local end-to-end test (apply bad manifest → email received)
9. `helm/` chart
10. `.github/workflows/deploy.yml`
11. `.github/workflows/chaos-test.yml` + `tests/evaluate.py`
