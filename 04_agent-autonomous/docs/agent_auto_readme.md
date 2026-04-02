# KubeTriage: Custom AI Agent — Function Calling Note

[Back](../../README.md)

- [KubeTriage: Custom AI Agent — Function Calling Note](#kubetriage-custom-ai-agent--function-calling-note)
  - [App Development](#app-development)
    - [Create and Develop App](#create-and-develop-app)
    - [System prompt](#system-prompt)
    - [Push image](#push-image)
  - [App Deployment](#app-deployment)
    - [Deploy in Cluster](#deploy-in-cluster)
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
Role:
You are KubeTriage, an SRE assistant that diagnoses and fix Kubernetes pod incidents.

Environment Variales:
These variables have been set.
APISERVER=https://kubernetes.default.svc
SERVICEACCOUNT=/var/run/secrets/kubernetes.io/serviceaccount
TOKEN_FILE=/var/run/secrets/kubernetes.io/serviceaccount/token
NAMESPACE_FILE=/var/run/secrets/kubernetes.io/serviceaccount/namespace
CACERT_FILE=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

Task:
KEEP APPLICATION RUNNING AS SOON AS POSSIBLE IS YOUR MAIN TASK.
You MUST do anything to fix the incidents.
You can access api server with curl command.
You are SAFE to modify, remove, and patch via api server.

Output Rules:
1. If the execution of command line is required, then output ONLY ONE line of shell command
command: <executable_command>

2. If no further execution is required, then output in this format:
complete: <summary_text>

Keep the output concise.
""".strip()
```

---

### Push image

```sh
docker build -t kubetriage:autonomous 04_agent-autonomous/
# docker rm kubetriage:autonomous --force
# docker run --name agent-kubetriage -d --rm -p 8000:8000 kubetriage:autonomous

docker tag kubetriage:autonomous simonangelfong/kubetriage:autonomous
docker push simonangelfong/kubetriage:autonomous
```

---

## App Deployment

### Deploy in Cluster

```sh
kubectl apply -f 04_agent-autonomous/manifests
kubectl replace --force -f 04_agent-autonomous/manifests --grace-period=0
kubectl logs kubetriage -f
```

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
  name: kubetriage-privileged
  namespace: default
rules:
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["*"]
```
