# =================================================
# capstone_agents.py
# Multi-Agent Task Manager (Supervisor + Worker)
# =================================================

# -------------------------
# Memory Class
# -------------------------
class Memory:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value

# -------------------------
# Base Tool Class
# -------------------------
class Tool:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def run(self, **kwargs):
        raise NotImplementedError("Tool.run() must be implemented by subclasses")

# Example Tool: Echo
class EchoTool(Tool):
    def __init__(self):
        super().__init__("echo_tool", "Repeats input text")

    def run(self, text: str):
        return {"echo": text}

# -------------------------
# Base Agent Class
# -------------------------
class Agent:
    def __init__(self, name):
        self.name = name
        self.memory = Memory()
        self.tools = {}

    def add_tool(self, tool):
        self.tools[tool.name] = tool

    def run(self, message: str):
        # Tool execution format: tool:tool_name {"param": "value"}
        if message.startswith("tool:"):
            try:
                tool_name, payload = message[5:].split(" ", 1)
                import json
                payload = json.loads(payload)
                if tool_name not in self.tools:
                    return {"error": f"Tool '{tool_name}' not found"}
                result = self.tools[tool_name].run(**payload)
                return {"from": self.name, "tool": tool_name, "result": result}
            except Exception as e:
                return {"error": f"Tool execution failed: {str(e)}"}
        # Default response
        return {"from": self.name, "response": f"Received message: {message}"}

# -------------------------
# Worker Agent
# -------------------------
class WorkerAgent(Agent):
    def __init__(self):
        super().__init__("worker")
        self.add_tool(EchoTool())  # Add echo tool by default

# -------------------------
# Supervisor Agent
# -------------------------
class SupervisorAgent(Agent):
    def __init__(self, worker_agent):
        super().__init__("supervisor")
        self.worker = worker_agent
        self.add_tool(EchoTool())  # Optional supervisor tools

    def run(self, message: str):
        # If message contains "delegate", forward to worker
        if "delegate" in message.lower():
            task = message.replace("delegate", "").strip()
            return self.worker.run(task)
        # Otherwise, default behavior
        return super().run(message)

# -------------------------
# Session Class (manages agents)
# -------------------------
class Session:
    def __init__(self):
        self.worker = WorkerAgent()
        self.supervisor = SupervisorAgent(self.worker)
        self.agents = {
            "supervisor": self.supervisor,
            "worker": self.worker
        }

    def send(self, agent_name: str, message: str):
        agent = self.agents.get(agent_name)
        if not agent:
            return {"error": f"Agent '{agent_name}' not found. Available: {list(self.agents.keys())}"}
        try:
            return agent.run(message)
        except Exception as e:
            return {"error": f"Agent.run() failed: {str(e)}"}
