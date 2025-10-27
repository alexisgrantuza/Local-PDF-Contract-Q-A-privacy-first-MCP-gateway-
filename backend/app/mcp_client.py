import os
import requests


MCP_URL = os.environ.get("MCP_API_URL")
MCP_API_KEY = os.environ.get("MCP_API_KEY")


if not MCP_URL:
  raise RuntimeError("MCP_API_URL must be set in environment")


HEADERS = {"Authorization": f"Bearer {MCP_API_KEY}"} if MCP_API_KEY else {}




def mcp_generate(prompt: str, model: str = None, max_tokens: int = 300):
  payload = {
  "input": prompt,
  }
  if model:
    payload["model"] = model
  try:
    r = requests.post(MCP_URL, json=payload, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()
  except Exception as e:
    return {"error": str(e), "text": ""}