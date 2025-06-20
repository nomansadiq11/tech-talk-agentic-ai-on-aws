import time
import json
from datetime import datetime
from kubernetes import client, config, watch
import requests

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

def get_pod_logs(v1, namespace, name):
    try:
        return v1.read_namespaced_pod_log(name=name, namespace=namespace, tail_lines=50)
    except Exception as e:
        print(f"[ERROR] Failed to get logs for pod {name} in {namespace}: {e}")
        return f"Error reading logs: {e}"

def describe_pod(v1, namespace, name):
    try:
        pod = v1.read_namespaced_pod(name=name, namespace=namespace)
        return json.dumps(pod.to_dict(), indent=2, cls=DateTimeEncoder)
    except Exception as e:
        print(f"[ERROR] Failed to describe pod {name} in {namespace}: {e}")
        return f"Error describing pod: {e}"

def ask_llm(prompt):
    try:
        if "CrashLoopBackOff" in prompt:
            return (
                "Pod is crashing due to a misconfigured env var or missing dependency.",
                "kubectl delete pod"
            )
        elif "ImagePullBackOff" in prompt:
            return (
                "The image may be misnamed or the registry is not accessible. Check image name or credentials.",
                "check image name or secret"
            )
        return ("Unknown issue", "")
    except Exception as e:
        print(f"[ERROR] LLM prompt failed: {e}")
        return ("LLM error", "")

# def ask_llm(prompt):
#     try:
#         response = requests.post(
#             "http://ollama:11434/api/generate",
#             json={"model": "llama3", "prompt": prompt}
#         )

#         result = response.json()

#         print(f"[LLM RESPONSE] {result}")

#         output = result.get("response", "")

#         print(f"[LLM OUTPUT] {output}")
#         # Basic logic to determine fix from LLM response
#         if "delete the pod" in output.lower():
#             return output, "kubectl delete pod"
#         elif "check image" in output.lower():
#             return output, "check image"
#         else:
#             return output, ""
#     except Exception as e:
#         print(f"[ERROR] LLM request failed: {e}")
#         return "LLM error", ""

def apply_fix(namespace, name, fix, v1):
    try:
        if "delete pod" in fix:
            v1.delete_namespaced_pod(name=name, namespace=namespace)
            return f"Deleted pod {name} in namespace {namespace}"
        elif "check image" in fix:
            return "No automated fix applied. Requires manual image/registry check."
        else:
            return "No fix rule matched."
    except Exception as e:
        print(f"[ERROR] Failed to apply fix to pod {name} in {namespace}: {e}")
        return f"Fix error: {e}"

def process_pod_event(pod, v1):
    try:
        if not pod.status.container_statuses:
            return

        state = pod.status.container_statuses[0].state
        reason = state.waiting.reason if state and state.waiting else None

        if reason in ["CrashLoopBackOff", "ImagePullBackOff"]:
            name = pod.metadata.name
            namespace = pod.metadata.namespace
            print(f"[{reason}] Detected on pod {name} in {namespace}")

            logs = get_pod_logs(v1, namespace, name)
            desc = describe_pod(v1, namespace, name)

            prompt = f"Logs:\n{logs}\n\nDescribe:\n{desc}"
            diagnosis, fix = ask_llm(prompt)

            print(f"[DIAGNOSIS] {diagnosis}")
            if fix:
                result = apply_fix(namespace, name, fix, v1)
                print(f"[FIX APPLIED] {result}")

    except Exception as e:
        print(f"[ERROR] Exception while processing pod event: {e}")

def main():
    try:
        try:
            config.load_incluster_config()
        except config.ConfigException:
            print("Loading local kube config...")
            config.load_kube_config()

        v1 = client.CoreV1Api()
        w = watch.Watch()

        while True:
            try:
                for event in w.stream(v1.list_pod_for_all_namespaces, timeout_seconds=60):
                    pod = event['object']
                    print(f"[EVENT] {event['type']} on pod {pod.metadata.name} in namespace {pod.metadata.namespace}")
                    process_pod_event(pod, v1)
                    print("[INFO] Waiting for next event...")
            except Exception as e:
                print(f"[ERROR] Watch loop error: {e}")
                time.sleep(5)  # backoff before reconnect

    except Exception as e:
        print(f"[FATAL ERROR] Agent crashed: {e}")
        # Never exit — keep retrying
        time.sleep(10)
        main()  # restart loop

if __name__ == '__main__':
    main()
