# agent/kubetriage.py
import os
import logging
import time
import anthropic
import subprocess
from ..models import AlertInfo

logger = logging.getLogger(__name__)

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


def run_triage(alertInfo: AlertInfo) -> None:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # context
    context = []
    context.append(
        {
            "role": "user",
            "content": f"""
                Alert: {alertInfo.alertname}\n 
                Namespace: {alertInfo.namespace}\n 
                Pod: {alertInfo.pod}\n 
                Description: {alertInfo.description}\n\n 
                Please triage this incident.
            """
        }
    )

    logger.info(f"---------- AI agent: Start ----------")
    max_iterations = 20
    for _ in range(max_iterations):
        response = client.messages.create(
            model=os.environ["ANTHROPIC_MODEL"],
            max_tokens=1024,
            system=SYSTEM_PROMPT,  # add system prompt
            messages=context
        )
        
        time.sleep(10)
        
        logger.info(f"Content: {response.content}")
        # append assistant response to history
        context.append({"role": "assistant", "content": response.content})
        # get output
        llm_output = response.content[0].text.strip()

        # if complete: break loop
        if llm_output.startswith("complete:"):
            logger.info(f"---------- LLM: complete ----------")
            break

        # if command: execute command
        if llm_output.startswith("command:"):
            # get command
            command = llm_output.split("command:", 1)[1].strip()
            logger.info(f"---------- LLM: {command} ----------")
            # Exectute command
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True)
            command_result = result.stdout + result.stderr
            exec_output = f"Execution completed: {command_result}"
            logger.info(f"---------- Agent: {exec_output} ----------")

            # append the cli output for next loop
            context.append(
                {"role": "user", "content": f"command execution: {exec_output}"})  # must be user role
        
        # guard
        else:
            context.append(
                {"role": "user", "content": "Please follow the output format."})
            continue
