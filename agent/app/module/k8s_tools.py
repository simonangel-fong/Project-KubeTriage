from kubernetes import client, config


def _load_config():
    try:
        config.load_incluster_config()   # running inside k8s pod
    except Exception:
        config.load_kube_config()        # local dev fallback


def get_pod_info(namespace: str, pod_name: str) -> str:
    _load_config()
    v1 = client.CoreV1Api()
    try:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        lines = [
            f"Name: {pod.metadata.name}",
            f"Namespace: {pod.metadata.namespace}",
            f"Node: {pod.spec.node_name}",
            f"Phase: {pod.status.phase}",
        ]
        for cs in (pod.status.container_statuses or []):
            lines.append(f"Container: {cs.name}")
            lines.append(f"  Ready: {cs.ready}")
            lines.append(f"  Restart count: {cs.restart_count}")
            if cs.state.waiting:
                lines.append(f"  Waiting reason: {cs.state.waiting.reason}")
                lines.append(f"  Waiting message: {cs.state.waiting.message}")
            if cs.state.terminated:
                lines.append(f"  Terminated reason: {cs.state.terminated.reason}")
                lines.append(f"  Exit code: {cs.state.terminated.exit_code}")
            if cs.last_state.terminated:
                lines.append(f"  Last terminated reason: {cs.last_state.terminated.reason}")
                lines.append(f"  Last exit code: {cs.last_state.terminated.exit_code}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching pod info: {e}"


def get_pod_events(namespace: str, pod_name: str) -> str:
    _load_config()
    v1 = client.CoreV1Api()
    try:
        events = v1.list_namespaced_event(
            namespace=namespace,
            field_selector=f"involvedObject.name={pod_name}"
        )
        if not events.items:
            return "No events found for this pod."
        lines = []
        for e in sorted(events.items, key=lambda x: x.last_timestamp or x.event_time):
            lines.append(
                f"[{e.type}] {e.reason}: {e.message} "
                f"(count: {e.count}, last: {e.last_timestamp})"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error fetching events: {e}"


def get_pod_logs(namespace: str, pod_name: str, tail: int = 50) -> str:
    _load_config()
    v1 = client.CoreV1Api()
    try:
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail,
            previous=False
        )
        return logs if logs else "No logs available."
    except Exception as e:
        # try previous container logs (e.g. after OOMKill or crash)
        try:
            logs = v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail,
                previous=True
            )
            return f"[previous container logs]\n{logs}"
        except Exception:
            return f"Error fetching logs: {e}"