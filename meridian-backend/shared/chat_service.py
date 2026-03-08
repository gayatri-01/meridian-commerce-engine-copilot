import os
from typing import Any, Dict, List

import boto3


CHAT_SYSTEM_PROMPT = (
    "You are Meridian Virtual Category Manager for Indian Kirana retailers. "
    "Always reason with pack_type differences (Single vs Carton), promotion_flag effects, "
    "and practical replenishment advice. Respond to the exact user question only. "
    "Be concise: 3-6 short bullet points max, avoid long paragraphs, avoid repeating data."
)


def chat_with_kb(question: str, session_id: str, chat_history: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
    region = os.getenv("AWS_REGION", "us-east-1")
    kb_id = os.getenv("BEDROCK_KB_ID", "")
    model_arn = os.getenv(
        "CHAT_MODEL_ARN",
        f"arn:aws:bedrock:{region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
    )

    if not kb_id:
        return {
            "error": "BEDROCK_KB_ID is not configured.",
            "answer": "Knowledge Base is not configured yet.",
            "citations": [],
        }

    agent_runtime = boto3.client("bedrock-agent-runtime", region_name=region)

    response_format = (
        "Response format rules:\n"
        "- Start with one-line direct answer.\n"
        "- Then provide at most 5 bullets.\n"
        "- If user asks for a number, give one approximate number first.\n"
        "- Keep total response under 120 words unless user asks for detail."
    )

    prompt = f"{CHAT_SYSTEM_PROMPT}\n\n{response_format}\n\nUser question: {question}"

    if chat_history:
        compact_history = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in chat_history[-6:]])
        prompt = (
            f"{CHAT_SYSTEM_PROMPT}\n\n{response_format}\n\n"
            f"Conversation context:\n{compact_history}\n\nUser question: {question}"
        )

    # Do not force custom sessionId here; Bedrock can reject app-generated IDs.
    # We keep conversational continuity via prompt history.
    response = agent_runtime.retrieve_and_generate(
        input={"text": prompt},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": kb_id,
                "modelArn": model_arn,
                "retrievalConfiguration": {
                    "vectorSearchConfiguration": {
                        "numberOfResults": int(os.getenv("KB_TOP_K", "6"))
                    }
                },
            },
        },
    )

    output = response.get("output", {}).get("text", "")
    citations = response.get("citations", [])
    bedrock_session_id = response.get("sessionId", "")

    return {
        "session_id": session_id,
        "bedrock_session_id": bedrock_session_id,
        "answer": output,
        "citations": citations,
    }
