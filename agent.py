import os
from groq import Groq
from dotenv import load_dotenv
from memory_store import recall_incidents

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Models available on this Groq account in priority order
MODELS = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b"]

def triage_incident(service: str, error_logs: str, use_memory: bool = True) -> tuple[str, list]:
    """Triages production incidents using Groq LLM with optional Hindsight persistent memory."""
    if use_memory:
        memories = recall_incidents(service, error_logs)
        if memories:
            memory_summary = "\n".join([f"- Previous Incident: {m.get('content', str(m))}" for m in memories])
        else:
            memory_summary = "No prior incidents matching this exact symptom pattern found in memory."
    else:
        memories = []
        memory_summary = "MEMORY LAYER DISABLED (Simulating Stateless LLM without Hindsight)."

    if use_memory:
        system_prompt = """You are ResolveIQ, an autonomous Site Reliability Engineering (SRE) agent.
Your objective: Diagnose production incidents by synthesizing incoming alerts with past institutional memory.

Rules:
1. If Hindsight memory reveals a past incident with matching root causes, highlight that exact past fix immediately.
2. Structure your response clearly:
   - 🚨 Incident Summary
   - 🧠 Historical Memory Match (Cite past incident if present)
   - 🔍 Probable Root Cause
   - 🛠️ Recommended Action / Runbook Step
"""
    else:
        system_prompt = """You are a generic AI troubleshooting assistant without access to past institutional memory or post-mortems.
Provide general, standard troubleshooting steps for this incident without citing any specific past organizational incidents.
Structure your response clearly:
   - 🚨 Incident Summary
   - 🔍 General Possibilities
   - 🛠️ Standard Troubleshooting Steps
"""

    user_prompt = f"""
Current Outage:
- Microservice: {service}
- Error Logs / Symptoms: {error_logs}

Retrieved Organizational Memory (Hindsight):
{memory_summary}
"""

    last_error = None
    for model_name in MODELS:
        try:
            response = groq_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            content = response.choices[0].message.content
            if content:
                return content, memories
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise last_error

    return "No diagnosis generated.", memories
