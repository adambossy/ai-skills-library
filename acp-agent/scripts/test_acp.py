#!/usr/bin/env python3
"""Test an ACP server implementation.

Usage:
    python test_acp.py "uv run my-agent acp"
    python test_acp.py "./my-agent-binary"

This script spawns the agent as a subprocess and runs through the basic
ACP lifecycle: initialize -> session/new -> session/prompt.
"""

import json
import subprocess
import sys
from typing import Any


def send_request(proc: subprocess.Popen, method: str, params: dict, id: int) -> dict:
    """Send a JSON-RPC request and wait for response."""
    request = {
        "jsonrpc": "2.0",
        "id": id,
        "method": method,
        "params": params,
    }
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()

    # Read responses until we get one with matching id
    while True:
        line = proc.stdout.readline()
        if not line:
            raise EOFError("Agent closed connection")
        response = json.loads(line)
        # Skip notifications (no id)
        if "id" in response and response["id"] == id:
            return response
        elif "method" in response:
            print(f"  <- Notification: {response['method']}")
            if response.get("params", {}).get("update", {}).get("sessionUpdate") == "agent_message_chunk":
                text = response["params"]["update"]["content"].get("text", "")
                print(f"     {text[:100]}...")


def test_acp_server(command: str) -> bool:
    """Test an ACP server implementation."""
    print(f"Starting agent: {command}")
    proc = subprocess.Popen(
        command,
        shell=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    try:
        # Test 1: Initialize
        print("\n1. Testing initialize...")
        response = send_request(proc, "initialize", {
            "protocolVersion": 1,
            "clientCapabilities": {
                "filesystem": {"read": True, "write": True},
                "terminal": True,
            },
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        }, id=1)

        if "error" in response:
            print(f"   FAIL: {response['error']}")
            return False

        result = response.get("result", {})
        print(f"   OK: Protocol version {result.get('protocolVersion')}")
        print(f"   Agent: {result.get('agentInfo', {}).get('title', 'Unknown')}")

        # Test 2: Create session
        print("\n2. Testing session/new...")
        response = send_request(proc, "session/new", {
            "cwd": "/tmp",
        }, id=2)

        if "error" in response:
            print(f"   FAIL: {response['error']}")
            return False

        session_id = response.get("result", {}).get("sessionId")
        print(f"   OK: Session ID {session_id}")

        # Test 3: Send prompt
        print("\n3. Testing session/prompt...")
        response = send_request(proc, "session/prompt", {
            "sessionId": session_id,
            "content": [{"type": "text", "text": "Hello, what can you do?"}],
        }, id=3)

        if "error" in response:
            print(f"   FAIL: {response['error']}")
            return False

        stop_reason = response.get("result", {}).get("stopReason")
        print(f"   OK: Stop reason '{stop_reason}'")

        # Test 4: Invalid method
        print("\n4. Testing error handling (invalid method)...")
        response = send_request(proc, "invalid/method", {}, id=4)

        if "error" not in response:
            print("   FAIL: Expected error for invalid method")
            return False

        error_code = response["error"].get("code")
        print(f"   OK: Error code {error_code} (method not found)")

        print("\n" + "=" * 50)
        print("All tests passed!")
        return True

    except Exception as e:
        print(f"\nError: {e}")
        # Print stderr for debugging
        stderr = proc.stderr.read()
        if stderr:
            print(f"\nAgent stderr:\n{stderr}")
        return False

    finally:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_acp.py <agent-command>")
        print("Example: python test_acp.py 'uv run my-agent acp'")
        sys.exit(1)

    command = sys.argv[1]
    success = test_acp_server(command)
    sys.exit(0 if success else 1)
