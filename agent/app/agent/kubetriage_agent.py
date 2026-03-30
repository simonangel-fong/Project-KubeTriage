import os
import logging
import anthropic
from .k8s_tools import get_pod_info, get_pod_events, get_pod_logs
from ..models.models import TriageReport

logger = logging.getLogger(__name__)

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

SYSTEM_PROMPT = """You are KubeTriage, an SRE assistant that diagnoses Kubernetes pod incidents.

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


def _execute_tool(name: str, inputs: dict) -> str:
    if name == "get_pod_info":
        return get_pod_info(inputs["namespace"], inputs["pod_name"])
    elif name == "get_pod_events":
        return get_pod_events(inputs["namespace"], inputs["pod_name"])
    elif name == "get_pod_logs":
        return get_pod_logs(inputs["namespace"], inputs["pod_name"], inputs.get("tail", 50))
    return f"Unknown tool: {name}"


def _parse_report(text: str) -> TriageReport:
    lines = text.strip().splitlines()
    data = {
        "category": "Unknown",
        "root_cause": "",
        "remediation": [],
        "kubectl_command": "",
        "escalate": False
    }
    in_remediation = False
    for line in lines:
        line = line.strip()
        if line.startswith("CATEGORY:"):
            data["category"] = line.split(":", 1)[1].strip()
            in_remediation = False
        elif line.startswith("ROOT_CAUSE:"):
            data["root_cause"] = line.split(":", 1)[1].strip()
            in_remediation = False
        elif line.startswith("REMEDIATION:"):
            in_remediation = True
        elif line.startswith("KUBECTL_COMMAND:"):
            data["kubectl_command"] = line.split(":", 1)[1].strip()
            in_remediation = False
        elif line.startswith("ESCALATE:"):
            data["escalate"] = line.split(":", 1)[1].strip().lower() == "yes"
            in_remediation = False
        elif in_remediation and line.startswith("-"):
            data["remediation"].append(line[1:].strip())
    return TriageReport(**data)


def run_triage(alertname: str, namespace: str, pod: str, description: str) -> TriageReport:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = []
    messages.append(
        {
            "role": "user",
            "content": f"""
                Alert: {alertname}\n 
                Namespace: {namespace}\n 
                Pod: {pod}\n 
                Description: {description}\n\n 
                Please triage this incident.
            """
        }
    )

    logger.info(f"========== AI agent: Start ==========")
    max_iterations = 5
    for _ in range(max_iterations):
        response = client.messages.create(
            model=os.environ["ANTHROPIC_MODEL"],
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        # append assistant response to history
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            logger.info(f"========== AI agent: Completed ==========")
            # extract final text block
            for block in response.content:
                if block.type == "text":
                    return _parse_report(block.text)
            break

        if response.stop_reason == "tool_use":
            logger.info(f"========== AI agent: use tool ==========")
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = _execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            messages.append({"role": "user", "content": tool_results})

    return TriageReport(
        category="Unknown",
        root_cause="Agent did not produce a structured response.",
        remediation=[
            "Review pod manually with kubectl describe and kubectl logs."],
        kubectl_command=f"kubectl describe pod {pod} -n {namespace}",
        escalate=True
    )
