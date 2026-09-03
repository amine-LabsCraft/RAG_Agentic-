"""Tool execution dispatcher."""
import json
import logging
from app.services.retrieval_service import search_documents

logger = logging.getLogger(__name__)


async def execute_tool_call(tool_call: dict, user_id: str) -> str:
    """
    Execute a tool call and return the result as a string.

    Args:
        tool_call: Dict with 'name' and 'arguments' keys
        user_id: The user's ID for context

    Returns:
        Tool result as a string (never raises)
    """
    name = tool_call.get("name") if isinstance(tool_call, dict) else None
    raw_args = tool_call.get("arguments", "{}") if isinstance(tool_call, dict) else "{}"
    if not name:
        return "Error: tool call is missing a name."
    try:
        arguments = json.loads(raw_args or "{}")
        if not isinstance(arguments, dict):
            arguments = {}
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning(f"Invalid tool arguments for {name}: {e}")
        return f"Error: invalid arguments for tool '{name}'."

    if name == "search_documents":
        query = arguments.get("query", "")
        results = await search_documents(query, user_id)

        if not results:
            return "No relevant documents found."

        # Format results for LLM context
        formatted = []
        for r in results:
            if not isinstance(r, dict):
                continue
            content = r.get("content", "")
            if not content:
                continue
            try:
                similarity = float(r.get("similarity", 0.0))
            except (TypeError, ValueError):
                similarity = 0.0
            filename = r.get("metadata", {}).get("filename", "unknown") if isinstance(r.get("metadata"), dict) else "unknown"
            formatted.append(
                f"[Source: {filename}] "
                f"(similarity: {similarity:.2f})\n{content}"
            )
        if not formatted:
            return "No relevant documents found."

        return "\n\n---\n\n".join(formatted)

    logger.warning(f"Unknown tool: {name}")
    return f"Error: Unknown tool '{name}'"
