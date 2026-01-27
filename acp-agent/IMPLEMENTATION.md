# ACP Implementation Details

Complete Python code examples for implementing an ACP server.

## Transport Layer

Handle JSON-RPC communication over stdin/stdout:

```python
"""JSON-RPC transport over stdin/stdout."""

import asyncio
import json
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class JsonRpcRequest:
    """JSON-RPC 2.0 request message."""
    method: str
    id: int | str | None = None
    params: dict[str, Any] | None = None
    jsonrpc: str = field(default="2.0")


@dataclass(frozen=True)
class JsonRpcResponse:
    """JSON-RPC 2.0 response message."""
    id: int | str | None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    jsonrpc: str = field(default="2.0")


@dataclass(frozen=True)
class JsonRpcNotification:
    """JSON-RPC 2.0 notification (no id, no response expected)."""
    method: str
    params: dict[str, Any] | None = None
    jsonrpc: str = field(default="2.0")


class StdioTransport:
    """Bidirectional JSON-RPC transport via stdin/stdout."""

    async def read_message(self) -> JsonRpcRequest:
        """Read next JSON-RPC request from stdin."""
        loop = asyncio.get_running_loop()
        line: str = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            raise EOFError("stdin closed")
        data: dict[str, Any] = json.loads(line)
        return JsonRpcRequest(
            method=str(data.get("method", "")),
            id=data.get("id"),
            params=data.get("params"),
        )

    async def write_response(self, response: JsonRpcResponse) -> None:
        """Write JSON-RPC response to stdout."""
        payload: dict[str, Any] = {"jsonrpc": response.jsonrpc, "id": response.id}
        if response.result is not None:
            payload["result"] = response.result
        if response.error is not None:
            payload["error"] = response.error
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()

    async def write_notification(self, notification: JsonRpcNotification) -> None:
        """Write JSON-RPC notification to stdout."""
        payload: dict[str, Any] = {
            "jsonrpc": notification.jsonrpc,
            "method": notification.method,
        }
        if notification.params is not None:
            payload["params"] = notification.params
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()
```

## Router

Route JSON-RPC methods to handlers:

```python
"""Route JSON-RPC requests to handlers."""

from collections.abc import Awaitable, Callable
from typing import Any

Handler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class MethodNotFoundError(Exception):
    """Raised when a method is not registered."""
    def __init__(self, method: str) -> None:
        self.method = method
        super().__init__(f"Method not found: {method}")


class RequestRouter:
    """Route JSON-RPC methods to async handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, Handler] = {}

    def register(self, method: str, handler: Handler) -> None:
        """Register handler for a JSON-RPC method."""
        self._handlers[method] = handler

    async def dispatch(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Dispatch request to registered handler."""
        handler = self._handlers.get(method)
        if handler is None:
            raise MethodNotFoundError(method)
        return await handler(params)
```

## Notifier

Send streaming updates to the client:

```python
"""Send session/update notifications."""

from typing import Any, Literal

from .transport import JsonRpcNotification, StdioTransport

ToolCallStatus = Literal["pending", "in_progress", "completed", "failed", "cancelled"]
ToolCallKind = Literal["execute", "fetch", "edit", "other"]


class UpdateNotifier:
    """Send session/update notifications via JSON-RPC."""

    def __init__(self, transport: StdioTransport) -> None:
        self._transport = transport

    async def tool_call(
        self,
        tool_call_id: str,
        title: str,
        kind: ToolCallKind,
        status: ToolCallStatus,
    ) -> None:
        """Notify that a tool call has started."""
        await self._send_update({
            "sessionUpdate": "tool_call",
            "toolCallId": tool_call_id,
            "title": title,
            "kind": kind,
            "status": status,
        })

    async def tool_call_update(
        self,
        tool_call_id: str,
        status: ToolCallStatus,
        content: list[dict[str, Any]] | None = None,
    ) -> None:
        """Update tool call status."""
        update: dict[str, Any] = {
            "sessionUpdate": "tool_call_update",
            "toolCallId": tool_call_id,
            "status": status,
        }
        if content is not None:
            update["content"] = content
        await self._send_update(update)

    async def agent_message_chunk(self, content: dict[str, Any]) -> None:
        """Stream text content to client."""
        await self._send_update({
            "sessionUpdate": "agent_message_chunk",
            "content": content,
        })

    async def agent_thought_chunk(self, content: dict[str, Any]) -> None:
        """Stream thinking/reasoning content."""
        await self._send_update({
            "sessionUpdate": "agent_thought_chunk",
            "content": content,
        })

    async def _send_update(self, update: dict[str, Any]) -> None:
        """Send a session/update notification."""
        notification = JsonRpcNotification(
            method="session/update",
            params={"update": update},
        )
        await self._transport.write_notification(notification)
```

## Handlers

### Initialize Handler

```python
"""Handle initialize request."""

from typing import Any

PROTOCOL_VERSION = 1


async def handle_initialize(params: dict[str, Any]) -> dict[str, Any]:
    """Negotiate capabilities with client."""
    client_version = params.get("protocolVersion", 1)
    negotiated_version = min(client_version, PROTOCOL_VERSION)

    return {
        "protocolVersion": negotiated_version,
        "agentCapabilities": {
            "promptTypes": {
                "image": False,
                "audio": False,
                "embeddedContext": True,
            },
            "mcp": {"http": False, "sse": False},
        },
        "agentInfo": {
            "name": "my-agent",
            "title": "My Agent",
            "version": "0.1.0",
        },
        "authMethods": [],
    }
```

### Session Handler

```python
"""Manage conversation sessions."""

import secrets
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Session:
    """A conversation session."""
    id: str
    cwd: str
    messages: list[dict[str, Any]] = field(default_factory=list)


class SessionManager:
    """Manage active sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(self, cwd: str) -> Session:
        """Create a new session."""
        session_id = f"sess_{secrets.token_hex(12)}"
        session = Session(id=session_id, cwd=cwd)
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def add_message(self, session_id: str, message: dict[str, Any]) -> None:
        """Add message to session history."""
        if session := self._sessions.get(session_id):
            session.messages.append(message)


async def handle_session_new(
    params: dict[str, Any],
    sessions: SessionManager,
) -> dict[str, Any]:
    """Create a new session."""
    cwd = params.get("cwd", ".")
    session = sessions.create(cwd)
    return {"sessionId": session.id}
```

### Prompt Handler

```python
"""Handle user prompts."""

from typing import Any
import uuid

from .session import SessionManager
from ..notifier import UpdateNotifier


class PromptHandler:
    """Process user prompts and stream responses."""

    def __init__(
        self,
        session_manager: SessionManager,
        notifier: UpdateNotifier,
        # Add your agent/LLM here
    ) -> None:
        self._sessions = session_manager
        self._notifier = notifier

    async def handle_prompt(self, params: dict[str, Any]) -> dict[str, Any]:
        """Process a user prompt."""
        session_id = params.get("sessionId", "")
        content = params.get("content", [])

        # Extract text from content blocks
        user_text = ""
        for block in content:
            if block.get("type") == "text":
                user_text += block.get("text", "")

        # Add to session history
        self._sessions.add_message(session_id, {
            "role": "user",
            "content": content,
        })

        # Process with your agent/LLM here
        # Stream responses via notifier
        await self._process_with_agent(session_id, user_text)

        return {"stopReason": "end_turn"}

    async def _process_with_agent(self, session_id: str, user_text: str) -> None:
        """Process user input with your agent."""
        # Example: Stream a simple response
        await self._notifier.agent_message_chunk({
            "type": "text",
            "text": f"Processing: {user_text}\n",
        })

        # Example: Report a tool call
        tool_id = f"tc_{uuid.uuid4().hex[:8]}"
        await self._notifier.tool_call(
            tool_call_id=tool_id,
            title="Analyzing request",
            kind="other",
            status="pending",
        )

        # ... do actual work ...

        await self._notifier.tool_call_update(
            tool_call_id=tool_id,
            status="completed",
            content=[{"type": "text", "text": "Analysis complete"}],
        )

        await self._notifier.agent_message_chunk({
            "type": "text",
            "text": "Done!",
        })
```

## Main Server

```python
"""ACP server implementation."""

import asyncio
import sys
from typing import Any

# Configure logging to stderr (stdout reserved for JSON-RPC)
import logging
logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from .transport import StdioTransport, JsonRpcResponse
from .router import RequestRouter, MethodNotFoundError
from .notifier import UpdateNotifier
from .handlers.initialize import handle_initialize
from .handlers.session import SessionManager, handle_session_new
from .handlers.prompt import PromptHandler


class ACPServer:
    """ACP server for your agent."""

    def __init__(self) -> None:
        # Initialize transport
        self._transport = StdioTransport()
        self._notifier = UpdateNotifier(self._transport)

        # Initialize session management
        self._sessions = SessionManager()

        # Initialize prompt handler (add your agent here)
        self._prompt_handler = PromptHandler(
            session_manager=self._sessions,
            notifier=self._notifier,
        )

        # Setup router
        self._router = RequestRouter()
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register protocol handlers."""
        self._router.register("initialize", handle_initialize)

        async def session_new(params: dict[str, Any]) -> dict[str, Any]:
            return await handle_session_new(params, self._sessions)

        self._router.register("session/new", session_new)

        async def session_prompt(params: dict[str, Any]) -> dict[str, Any]:
            return await self._prompt_handler.handle_prompt(params)

        self._router.register("session/prompt", session_prompt)

    async def run(self) -> None:
        """Run the main event loop."""
        while True:
            try:
                request = await self._transport.read_message()

                try:
                    params = request.params or {}
                    result = await self._router.dispatch(request.method, params)
                    response = JsonRpcResponse(id=request.id, result=result)

                except MethodNotFoundError as e:
                    response = JsonRpcResponse(
                        id=request.id,
                        error={"code": -32601, "message": f"Method not found: {e.method}"},
                    )

                except Exception as e:
                    response = JsonRpcResponse(
                        id=request.id,
                        error={"code": -32603, "message": f"Internal error: {e}"},
                    )

                await self._transport.write_response(response)

            except EOFError:
                break


async def main() -> None:
    """Entry point."""
    server = ACPServer()
    await server.run()


def run() -> None:
    """Synchronous entry point."""
    asyncio.run(main())
```

## pyproject.toml

```toml
[project]
name = "my-agent"
version = "0.1.0"
requires-python = ">=3.12"

[project.scripts]
my-agent = "my_agent.server:run"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```
