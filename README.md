# Project KubeTriage: AI Agent Assistance for Kubernetes

> Automated Kubernetes incident triage using ArgoCD notifications and n8n workflows.

- [Project KubeTriage: AI Agent Assistance for Kubernetes](#project-kubetriage-ai-agent-assistance-for-kubernetes)
  - [How it works](#how-it-works)
    - [🟢T0: Healthy Deployment](#t0-healthy-deployment)
    - [🟡T1: Sync for Update](#t1-sync-for-update)
    - [🔴T2: Degraded Deployment and Triage Notification](#t2-degraded-deployment-and-triage-notification)
    - [🟢T3: Bugfix and Recovery](#t3-bugfix-and-recovery)
  - [n8n Workflow](#n8n-workflow)
    - [v9 — EKS assistant agent](#v9--eks-assistant-agent)
    - [v10 — EKS risky agent](#v10--eks-risky-agent)

---

## How it works

`KubeTriage` monitors `ArgoCD` application health and automatically triggers a triage workflow when a deployment degrades. The workflow collects context, generates a summary report, and notifies the team — reducing mean time to resolution.

---

### 🟢T0: Healthy Deployment

Application is running and healthy.

![ArgoCD healthy state](./docs/demo_t0_argocd.png)

---

### 🟡T1: Sync for Update

A new version (containing a bug) is committed, pushed, and synced to the cluster.

![ArgoCD sync](./docs/demo_t1_argocd.png)

---

### 🔴T2: Degraded Deployment and Triage Notification

ArgoCD detects the deployment as Degraded and fires a webhook to n8n.

![ArgoCD degraded state](./docs/demo_t2_argocd.png)

The n8n workflow is triggered and generates a triage summary report.

![n8n workflow triggered](./docs/demo_t2_n8n.png)

The report is delivered by email.

![Email report page 1](./docs/demo_t2_email01.png)

![Email report page 2](./docs/demo_t2_email02.png)

---

### 🟢T3: Bugfix and Recovery

The bug is fixed, committed, and the application is resynced. Health is restored.

![ArgoCD recovered](./docs/demo_t3_argocd.png)

See [Rollback and Sync CLI reference](./docs/cli.md) for the recovery commands used.

---

## n8n Workflow

![n8n workflow diagram](./docs/diagram_n8n_workflow.png)

See [Creating the KubeTriage n8n workflow](./n8n/README.md) for setup instructions.

---

### v9 — EKS assistant agent

**Goal:** demonstrate real-world operational value in Kubernetes.

**What it does:**

- Runs inside the cluster with scoped permissions
- Integrates with observability stack (e.g., Prometheus alerts)
- Automates:
  - Incident data collection (logs, events, pod status)
  - Incident summarization
  - Suggested debugging actions

**Demo:**

- Break a microservice
- Alert triggers the agent
- Agent generates an incident report and sends notification (e.g., email/Slack)

**Key point:**
The agent reduces MTTR by automating triage — not replacing engineers, but accelerating them.

---

### v10 — EKS risky agent

**Goal:** expose the security risks of autonomous agents in production.

**What it does:**

- Runs with elevated permissions (intentionally misconfigured)
- Accepts and executes unsafe or injected instructions
- Demonstrates:
  - RBAC misconfiguration risks
  - Prompt/skill injection
  - Uncontrolled command execution

**Demo:**

- Agent receives malicious or unsafe instruction
- Executes destructive actions (e.g., delete deployment, install tools)
- Show captured evidence (logs, commands, outcomes)

**Key point:**
Agents are powerful but dangerous — without proper constraints, they become a production risk.

---
