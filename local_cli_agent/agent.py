from local_cli_agent.constants import RESET, BOLD, YELLOW
from local_cli_agent.api import call_api
from local_cli_agent.executor import execute_tool


def agent_loop(messages, thinking=True, max_tokens=16384):
    """Run the agent loop: call API, execute tools, feed results back, repeat."""
    max_iterations = 25
    for i in range(max_iterations):
        content, tool_calls = call_api(messages, thinking=thinking, max_tokens=max_tokens)
        if content is None and tool_calls is None:
            return

        assistant_msg = {"role": "assistant"}
        if content:
            assistant_msg["content"] = content
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)

        if not tool_calls:
            return

        print(f"\n{YELLOW}{BOLD} [{len(tool_calls)} tool call(s)]{RESET}")
        for tc in tool_calls:
            result = execute_tool(tc["function"]["name"], tc["function"]["arguments"])
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    print(f"\n{YELLOW}Max iterations reached ({max_iterations}).{RESET}")
