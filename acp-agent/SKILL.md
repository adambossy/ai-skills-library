---
name: acp-agent
description: Implement an Agent Client Protocol (ACP) server to integrate AI agents with the Toad terminal UI and other ACP-compatible editors. Use when building agents that need to communicate with IDEs, creating coding assistants, or implementing the ACP standard.
---

# Agent Client Protocol (ACP) Implementation Guide

Build ACP-compatible agents that work with Toad, Zed, JetBrains, and other ACP clients.

## Overview

The Agent Client Protocol (ACP) is a standardized JSON-RPC 2.0 protocol enabling communication between AI coding agents and editor clients. It's similar to LSP but for AI agents.

**Key concepts:**
- **Transport**: JSON-RPC over stdin/stdout (local) or HTTP/WebSocket (remote)
- **Session lifecycle**: `initialize` → `session/new` → `session/prompt` loop
- **Streaming updates**: Real-time notifications for tool calls, text chunks, and thoughts
- **Permission flow**: Agents request permission before executing tools

## Quick Start

### 1. Project Structure

```
my-agent/
├── src/my_agent/
│   ├── __init__.py
│   ├── server.py          # Main ACP server
│   ├── router.py          # JSON-RPC method routing
│   ├── transport.py       # stdin/stdout communication
│   ├── notifier.py        # Streaming notifications
│   └── handlers/
│       ├── __init__.py
│       ├── initialize.py  # Capability negotiation
│       ├── session.py     # Session management
│       └── prompt.py      # User prompt handling
└── pyproject.toml
```

### 2. Core Components

See [IMPLEMENTATION.md](IMPLEMENTATION.md) for complete code examples.

## Protocol Lifecycle

### Phase 1: Initialization

Client sends `initialize` to negotiate capabilities:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": 1,
    "clientCapabilities": {
      "filesystem": { "read": true, "write": true },
      "terminal": true
    },
    "clientInfo": { "name": "Toad", "version": "1.0.0" }
  }
}
```

Agent responds with its capabilities:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": 1,
    "agentCapabilities": {
      "promptTypes": { "image": false, "audio": false, "embeddedContext": true },
      "mcp": { "http": false, "sse": false }
    },
    "agentInfo": { "name": "my-agent", "title": "My Agent", "version": "0.1.0" },
    "authMethods": []
  }
}
```

### Phase 2: Session Creation

Client creates a session with `session/new`:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "session/new",
  "params": {
    "cwd": "/path/to/project",
    "mcpServers": []
  }
}
```

Agent returns a session ID:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": { "sessionId": "sess_abc123def456" }
}
```

### Phase 3: Prompt Turn (Core Loop)

Client sends user messages with `session/prompt`:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "session/prompt",
  "params": {
    "sessionId": "sess_abc123def456",
    "content": [{ "type": "text", "text": "Explain this codebase" }]
  }
}
```

Agent streams updates via `session/update` notifications, then responds:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": { "stopReason": "end_turn" }
}
```

## Streaming Notifications

Send real-time updates via `session/update` notifications (no `id` field):

### Text Chunks

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "update": {
      "sessionUpdate": "agent_message_chunk",
      "content": { "type": "text", "text": "Here's what I found..." }
    }
  }
}
```

### Tool Calls

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "update": {
      "sessionUpdate": "tool_call",
      "toolCallId": "tc_001",
      "title": "Reading file",
      "kind": "fetch",
      "status": "pending"
    }
  }
}
```

Update tool status as it progresses:

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "update": {
      "sessionUpdate": "tool_call_update",
      "toolCallId": "tc_001",
      "status": "completed",
      "content": [{ "type": "text", "text": "File contents..." }]
    }
  }
}
```

### Tool Status Values

- `pending`: Tool call initiated
- `in_progress`: Execution started
- `completed`: Successfully finished
- `failed`: Error occurred
- `cancelled`: User cancelled

### Tool Kind Values

- `fetch`: Reading data (files, APIs)
- `execute`: Running commands
- `edit`: Modifying files
- `other`: General operations

## Testing with Toad

Toad is a terminal UI for ACP agents. Launch your agent:

```bash
toad acp "uv run my-agent acp 2>/tmp/my-agent.log" -t "My Agent"
```

**Important**: Redirect stderr to a file since stdout is reserved for JSON-RPC.

## Reference Implementation

The [transactoid](https://github.com/adambossy/transactoid) project provides a complete Python ACP implementation. Study its `src/transactoid/ui/acp/` directory for patterns.

## Additional Resources

- [ACP Specification](https://agentclientprotocol.com)
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Complete code examples
- [MESSAGES.md](MESSAGES.md) - Full message reference
