# Project KubeTriage

> Automated Kubernetes incident triage using ArgoCD notifications and n8n workflows.

- [Project KubeTriage](#project-kubetriage)
  - [How it works](#how-it-works)
    - [🟢T0: Healthy Deployment](#t0-healthy-deployment)
    - [🟡T1: Sync for Update](#t1-sync-for-update)
    - [🔴T2: Degraded Deployment and Triage Notification](#t2-degraded-deployment-and-triage-notification)
    - [🟢T3: Bugfix and Recovery](#t3-bugfix-and-recovery)
  - [n8n Workflow](#n8n-workflow)

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
