# KubeTriage: Kagent — Human-in-the-Loop Demo

[Back](../../README.md)

- [KubeTriage: Kagent — Human-in-the-Loop Demo](#kubetriage-kagent--human-in-the-loop-demo)
  - [`hitl-agent` Configuration](#hitl-agent-configuration)
  - [`hitl-agent` Demo](#hitl-agent-demo)
    - [Healthy Deployment](#healthy-deployment)
    - [ImagePullBackOff](#imagepullbackoff)
    - [ConfigMap Error](#configmap-error)
    - [CrashLoopBackOff](#crashloopbackoff)

---

## `hitl-agent` Configuration

- Model: `claude-haiku-4-5`
- Agent Instructions(Default)

```txt
You are a Kubernetes management agent. You help users inspect and manage resources in the cluster. Before making any changes, explain what you plan to do. If the user's request is ambiguous, use the ask_user tool to clarify before proceeding.
```

- **Prompt** — Request introduction

```txt
Summarize the deployment into a table in the default namespace.
```

![pic](../pic/demo_agent_hitl01.png)

![pic](../pic/demo_agent_hitl02.png)

![pic](../pic/demo_agent_hitl03.png)

---

## `hitl-agent` Demo

### Healthy Deployment

- Apply

```sh
kubectl apply -f 00_demo-app/manifests/01_healthy.yaml
# deployment.apps/nginx created
# service/nginx created
```

- **Prompt 1** — Request report

```txt
Summarize the deployment into a table in the default namespace.
```

![pic](../pic/demo_healthy01.png)

---

### ImagePullBackOff

Simulates a deployment referencing a non-existent image tag, triggering an `ImagePullBackOff` error.

```sh
kubectl apply -f 00_demo-app/manifests/02_imagepull.yaml
# deployment.apps/nginx-imagepull created
```

- **Prompt 1** — Request report

```txt
Summarize the deployment into a table in the default namespace.
```

![pic](../pic/demo_ImagePullBackOff01.png)

- **Prompt 2** — Request fix

```txt
Help me fix it.
```

- Question to choose image

![pic](../pic/demo_ImagePullBackOff02.png)

- Final output
  Summary of change

![pic](../pic/demo_ImagePullBackOff03.png)

- Confirm
  Verify fix applied correctly via kubectl

![pic](../pic/demo_ImagePullBackOff04.png)

---

### ConfigMap Error

Simulates a deployment referencing a non-existent ConfigMap, triggering an `CreateContainerConfigError` error.

```sh
kubectl apply -f 00_demo-app/manifests/03_configerror.yaml
# deployment.apps/nginx-configerror created
```

- **Prompt 1** — Request report

```txt
Summarize the deployment into a table in the default namespace.
```

![pic](../pic/demo_ConfigError01.png)

- **Prompt 2** — Request diagnosis

```txt
Yes
```

![pic](../pic/demo_ConfigError02.png)

![pic](../pic/demo_ConfigError03.png)

- **Prompt 2** — Request fix

```txt
Fix it by removing environment variable reference
```

![pic](../pic/demo_ConfigError04.png)

- Confirm
  Verify fix applied correctly via kubectl

![pic](../pic/demo_ConfigError05.png)

---

### CrashLoopBackOff

Simulates a deployment executing `exit 1`, triggering an `CrashLoopBackOff` error.

```sh
kubectl apply -f 00_demo-app/manifests/04_crashloop.yaml
# deployment.apps/nginx-crashloop created
```

- **Prompt 1** — Request report

```txt
Summarize the deployment into a table in the default namespace.
```

![pic](../pic/demo_CrashLoopBackOff01.png)

- **Prompt 2** — Request fix

```txt
Help me fix it.
```

![pic](../pic/demo_CrashLoopBackOff02.png)

![pic](../pic/demo_CrashLoopBackOff03.png)

- Confirm
  Verify fix applied correctly via kubectl

![pic](../pic/demo_CrashLoopBackOff04.png)

---
