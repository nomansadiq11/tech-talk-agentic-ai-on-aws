# 🧠 Tech Talk: Agentic AI for DevOps in Kubernetes

This project demonstrates an autonomous agent deployed inside a Kubernetes cluster that monitors pod health, detects issues such as `CrashLoopBackOff` and `ImagePullBackOff`, and interacts with a local LLM (Ollama) to determine and apply corrective actions.

## 🚀 What It Does

- Watches Kubernetes pod events using the Kubernetes Python client.
- Detects crash loops and image pull errors in real time.
- Collects logs and pod descriptions.
- Sends diagnostic prompts to a locally hosted Ollama LLM.
- Applies the LLM-suggested fix (e.g., deleting the pod).

## 📦 Components

### 1. `agent_loop.py`
A Python script running inside a Kubernetes pod that:
- Uses `watch` to stream pod events.
- Sends crash details to the LLM.
- Applies automated fixes.

### 2. Dockerfile
Builds the agent container with the necessary Python dependencies.

### 3. Kubernetes Manifests
- **Agent Deployment**: Runs the agent inside the cluster.
- **Ollama Deployment**: Optional local LLM running in the same cluster.
- **Service for Ollama**: Enables internal HTTP access for the agent to call the LLM.

## 🧠 How It Works

```
[Pod Events] --> [Agent Loop] --> [LLM (Ollama)] --> [Diagnosis + Fix] --> [K8s API]
```

## 🛠️ Local Setup Instructions

### 1. Build and Load Docker Image (if using KIND)

```bash
docker build -t agent-loop:latest .
kind load docker-image agent-loop:latest --name <your-kind-cluster-name>
```

### 2. Deploy the Agent and Ollama

```bash
kubectl apply -f manifests/ollama-deployment.yaml
kubectl apply -f manifests/agent-loop-deployment.yaml
```

> ⚠️ The agent assumes Ollama is available at `http://ollama.default.svc.cluster.local:11434`.

### 3. Load a Model into Ollama

```bash
kubectl exec -it deploy/ollama -- bash
ollama run llama3
```

### 4. View Logs

```bash
kubectl logs -f deploy/agent-loop
```

## 🧪 Example

If a pod goes into `CrashLoopBackOff`, the agent will:

- Fetch its logs
- Describe the pod
- Send the context to Ollama with a prompt like:
  ```
  Logs:
  <tail logs>

  Describe:
  <pod spec>
  ```
- Get a response like:
  ```
  Diagnosis: missing env var
  Action: delete the pod
  ```
- Automatically delete the pod

## 🔒 Secure & Air-Gapped Ready

- Ollama runs in-cluster with no internet dependency.
- No cloud API calls needed.
- Ideal for private and secure DevOps environments.

## 📚 Tech Stack

- Python 3.9
- Kubernetes Python Client
- Ollama (LLM runtime for `llama3`, `mistral`, etc.)
- KIND (optional for local clusters)

## 📎 Use Cases

- Automated incident response in dev/test clusters
- Air-gapped AI assistant for platform teams
- Demonstrations of Model Context Protocol (MCP) concepts

## 📢 Talk: Autonomous DevOps with Agentic AI on AWS

This repository is part of the [Agent Con Talk](https://agentcon.io) demonstrating how intelligent, goal-driven agents can operate inside Kubernetes using local AI models and infrastructure APIs.

## 🤝 Contributions

Feel free to fork and adapt! You can add:
- Slack/email alerting
- Patch-based fixes (env updates, restarts)
- Multi-model LLM routing

## 🧑‍💻 Author

**Noman Sadiq**
Senior DevOps Engineer, passionate about AI in infrastructure
Follow me on [LinkedIn](https://linkedin.com/in/nomansadiq)

---

> 🤖 Built with love for Agentic DevOps and cloud-native AI.