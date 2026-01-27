# ACP Message Reference

Complete reference for all ACP JSON-RPC messages.

## Request/Response Methods

### `initialize`

Negotiate protocol version and capabilities.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": 1,
    "clientCapabilities": {
      "filesystem": {
        "read": true,
        "write": true
      },
      "terminal": true
    },
    "clientInfo": {
      "name": "Toad",
      "version": "1.0.0"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": 1,
    "agentCapabilities": {
      "promptTypes": {
        "image": false,
        "audio": false,
        "embeddedContext": true
      },
      "sessionLoad": false,
      "mcp": {
        "http": false,
        "sse": false
      }
    },
    "agentInfo": {
      "name": "my-agent",
      "title": "My Agent",
      "version": "0.1.0"
    },
    "authMethods": []
  }
}
```

### `session/new`

Create a new conversation session.

**Request:**
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

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "sessionId": "sess_abc123def456"
  }
}
```

### `session/load` (optional)

Resume a previous session. Requires `sessionLoad` capability.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "session/load",
  "params": {
    "sessionId": "sess_abc123def456"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "sessionId": "sess_abc123def456"
  }
}
```

### `session/prompt`

Send a user message and receive agent response.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "session/prompt",
  "params": {
    "sessionId": "sess_abc123def456",
    "content": [
      {
        "type": "text",
        "text": "Explain this codebase"
      }
    ]
  }
}
```

**Content block types:**
- `text`: Plain text content
- `image`: Base64-encoded image (if capability enabled)
- `resource`: File reference with URI

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "stopReason": "end_turn"
  }
}
```

**Stop reasons:**
- `end_turn`: Normal completion
- `max_tokens`: Token limit reached
- `cancelled`: User cancelled
- `error`: Error occurred

### `authenticate` (optional)

Authenticate with the agent.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "authenticate",
  "params": {
    "method": "api_key",
    "credentials": {
      "key": "sk-..."
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "success": true
  }
}
```

### `fs/read_text_file` (client capability)

Agent requests to read a file.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "fs/read_text_file",
  "params": {
    "path": "/absolute/path/to/file.py",
    "startLine": 1,
    "endLine": 100
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "content": "file contents here..."
  }
}
```

### `fs/write_text_file` (client capability)

Agent requests to write a file.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "fs/write_text_file",
  "params": {
    "path": "/absolute/path/to/file.py",
    "content": "new file contents..."
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "success": true
  }
}
```

## Notifications (No Response Expected)

### `session/update` (agent → client)

Stream real-time updates during prompt processing.

#### Text Chunk

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "update": {
      "sessionUpdate": "agent_message_chunk",
      "content": {
        "type": "text",
        "text": "Here's what I found..."
      }
    }
  }
}
```

#### Thought Chunk

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "update": {
      "sessionUpdate": "agent_thought_chunk",
      "content": {
        "type": "thinking",
        "text": "Let me analyze this..."
      }
    }
  }
}
```

#### Tool Call Start

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "update": {
      "sessionUpdate": "tool_call",
      "toolCallId": "tc_001",
      "title": "Reading file src/main.py",
      "kind": "fetch",
      "status": "pending"
    }
  }
}
```

#### Tool Call Update

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "update": {
      "sessionUpdate": "tool_call_update",
      "toolCallId": "tc_001",
      "status": "completed",
      "content": [
        {
          "type": "text",
          "text": "File contents retrieved successfully"
        }
      ]
    }
  }
}
```

#### Plan Update

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "update": {
      "sessionUpdate": "plan",
      "entries": [
        {
          "description": "Analyze codebase structure",
          "priority": "high",
          "status": "completed"
        },
        {
          "description": "Identify key components",
          "priority": "medium",
          "status": "in_progress"
        },
        {
          "description": "Generate documentation",
          "priority": "low",
          "status": "pending"
        }
      ]
    }
  }
}
```

### `session/cancel` (client → agent)

Cancel the current operation.

```json
{
  "jsonrpc": "2.0",
  "method": "session/cancel",
  "params": {
    "sessionId": "sess_abc123def456"
  }
}
```

### `session/request_permission` (agent → client)

Request permission before executing a tool.

```json
{
  "jsonrpc": "2.0",
  "method": "session/request_permission",
  "params": {
    "sessionId": "sess_abc123def456",
    "toolCallId": "tc_001",
    "tool": "write_file",
    "description": "Write to /path/to/file.py"
  }
}
```

## Error Codes

Standard JSON-RPC 2.0 error codes:

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Invalid JSON-RPC request |
| -32601 | Method not found | Method does not exist |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Internal server error |

## Capability Reference

### Client Capabilities

```json
{
  "filesystem": {
    "read": true,
    "write": true
  },
  "terminal": true
}
```

### Agent Capabilities

```json
{
  "promptTypes": {
    "image": false,
    "audio": false,
    "embeddedContext": true
  },
  "sessionLoad": false,
  "mcp": {
    "http": false,
    "sse": false
  }
}
```

## Extensibility

### Custom Data (`_meta`)

Any type can include a `_meta` object for custom metadata:

```json
{
  "sessionUpdate": "tool_call",
  "toolCallId": "tc_001",
  "_meta": {
    "customField": "custom value"
  }
}
```

### Custom Methods

Methods prefixed with `_` are reserved for extensions:

```json
{
  "jsonrpc": "2.0",
  "id": 100,
  "method": "_custom/myMethod",
  "params": {}
}
```
