# KubeTriage: Custom AI Agent — Function Calling Note

[Back](../../README.md)

- [KubeTriage: Custom AI Agent — Function Calling Note](#kubetriage-custom-ai-agent--function-calling-note)
  - [App Development](#app-development)
    - [Create and Develop App](#create-and-develop-app)
    - [System prompt](#system-prompt)
    - [Push image](#push-image)
  - [App Deployment](#app-deployment)
    - [Deploy in Cluster](#deploy-in-cluster)
    - [Mount Secrets as Environment variables](#mount-secrets-as-environment-variables)
    - [RBAC](#rbac)

---

## App Development

### Create and Develop App

```sh
python -m venv .venv
python.exe -m pip install --upgrade pip

pip install "fastapi[standard]" pydantic anthropic kubernetes

cd agent/app
uvicorn main:app --reload

```

---

### System prompt

```python
SYSTEM_PROMPT = """
You are KubeTriage, an SRE assistant that diagnoses Kubernetes pod incidents.

When given an alert you must:
1. Always call get_pod_info and get_pod_events before concluding.
2. Call get_pod_logs only if pod_info or events suggest an application-level error.
3. Classify the incident into exactly one category:
   ImagePullBackOff | OOMKilled | ConfigError | CrashLoopBackOff | Unknown
4. Respond in this exact structure — no extra text before or after:

CATEGORY: <one of the above>
ROOT_CAUSE: <one sentence>
REMEDIATION:
- <step 1>
- <step 2>
- <step 3>
KUBECTL_COMMAND: <single most useful kubectl command for the engineer>
ESCALATE: yes | no"""

TOOLS = [
    {
        "name": "get_pod_info",
        "description": "Returns describe output for a specific pod including container state, restart count, waiting/terminated reasons.",
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
        "description": "Returns recent Kubernetes events for a pod including warnings and errors.",
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
        "description": "Returns the last N lines of logs from a pod container. Use only if pod_info or events suggest an application-level error.",
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

---

### Push image

```sh
docker build -t kubetriage:function-calling 03_agent-function-calling/
# docker rm kubetriage:function-calling --force
# docker run --name agent-kubetriage -d --rm -p 8000:8000 kubetriage:function-calling

docker tag kubetriage:function-calling simonangelfong/kubetriage:function-calling
docker push simonangelfong/kubetriage:function-calling
```

---

## App Deployment

### Deploy in Cluster

```sh
kubectl apply -f 03_agent-function-calling/manifests
kubectl replace --force -f 03_agent-function-calling/manifests --grace-period=0
kubectl logs kubetriage -f
```

---

### Mount Secrets as Environment variables

```sh
kubectl delete secret kubetriage-secrets
kubectl create secret generic kubetriage-secrets        \
    --from-literal=ANTHROPIC_API_KEY=                   \
    --from-literal=ANTHROPIC_MODEL=claude-haiku-4-5                 \
    --from-literal=SMTP_HOST=smtp.gmail.com                         \
    --from-literal=SMTP_PORT=587                                    \
    --from-literal=SMTP_USER=""          \
    --from-literal=SMTP_PASSWORD=                   \
    --from-literal=NOTIFY_TO=""
```

---

### RBAC

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: kubetriage-readonly
  namespace: default
rules:
  - apiGroups: ["", "apps"]
    resources:
      - pods
      - pods/log
      - services
      - endpoints
      - configmaps
      - events
      - deployments
      - replicasets
    verbs: ["get", "list", "watch"]
```
