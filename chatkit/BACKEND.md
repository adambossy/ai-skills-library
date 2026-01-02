# ChatKit Backend Integration

Detailed guide for setting up ChatKit Python backends with FastAPI.

## FastAPI Server Setup

### Basic Structure with Hot Reloading

Use a **factory function** pattern to enable hot reloading during development:

```python
"""ChatKit server with FastAPI and hot reloading."""
from chatkit.server import ChatKitServer, StreamingResult
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse


def create_app():
    """Factory function that creates and returns the FastAPI app."""
    server = MyChatKitServer()
    app = FastAPI()

    # CORS middleware (required for browser clients)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/chatkit")
    async def chatkit_endpoint(req: Request):
        body = await req.body()
        if not body:
            return Response(
                content='{"error": "No request body"}',
                media_type="application/json",
                status_code=400,
            )

        result = await server.process(body, context={})
        if isinstance(result, StreamingResult):
            return StreamingResponse(result, media_type="text/event-stream")
        return Response(content=result.json, media_type="application/json")

    return app


def main() -> None:
    """Entry point with hot reloading enabled."""
    import uvicorn

    uvicorn.run(
        "mymodule.server:create_app",  # String path to factory
        host="0.0.0.0",
        port=8000,
        reload=True,      # Enable hot reloading
        factory=True,     # create_app is a factory function
    )
```

**Key points:**
- `create_app()` returns the FastAPI app (factory pattern)
- Pass string path `"module:create_app"` instead of app object
- `factory=True` tells uvicorn to call the function to get the app
- `reload=True` watches for file changes and restarts

**Without factory pattern**, hot reloading won't work because uvicorn needs to reimport the module on each reload.

## Common Issues

### Issue: 422 Unprocessable Entity

**Error message:**
```json
{"detail":[{"type":"missing","loc":["query","request"],"msg":"Field required"}]}
```

**Root cause:** `from __future__ import annotations` at the top of the file.

This import makes all type annotations lazy (string literals). FastAPI uses type annotations to determine parameter sources. When it sees `req: Request` as a string instead of the actual `Request` class, it can't recognize it as the special Starlette Request type and treats `request` as a required query parameter.

**Solution:** Remove `from __future__ import annotations` from FastAPI endpoint files.

**Alternative:** If you need postponed annotations for other code, move FastAPI endpoints to a separate module without the import.

### Issue: CORS Errors

**Symptoms:**
- `OPTIONS /chatkit HTTP/1.1 405 Method Not Allowed`
- `Access-Control-Allow-Origin` header missing
- Browser console shows CORS policy blocked

**Solution:** Add CORSMiddleware before defining routes:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",  # Include both!
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Note:** Browsers treat `localhost` and `127.0.0.1` as different origins. Include both.

### Issue: Server Changes Not Taking Effect

**Symptom:** Code changes don't appear after editing

**Solution:** Restart the server. Use `uvicorn` with `--reload` for development:

```bash
uvicorn mymodule:app --reload --host 0.0.0.0 --port 8000
```

## Store Implementation

ChatKit requires a store for thread and item persistence. Here's a minimal in-memory implementation:

```python
"""Simple in-memory store for ChatKit."""
from typing import Any, Literal
import uuid

from chatkit.store import Store
from chatkit.types import Page, ThreadItem, ThreadMetadata


class SimpleInMemoryStore(Store[Any]):
    def __init__(self) -> None:
        self._threads: dict[str, ThreadMetadata] = {}
        self._items: dict[str, dict[str, ThreadItem]] = {}

    def generate_thread_id(self, context: Any) -> str:
        return str(uuid.uuid4())

    def generate_item_id(
        self,
        item_type: Literal[
            "thread", "message", "tool_call", "task",
            "workflow", "attachment", "sdk_hidden_context"
        ],
        thread: ThreadMetadata,
        context: Any,
    ) -> str:
        return f"{item_type}_{uuid.uuid4()}"

    async def save_thread(self, thread: ThreadMetadata, context: Any) -> None:
        self._threads[thread.id] = thread
        if thread.id not in self._items:
            self._items[thread.id] = {}

    async def load_thread(self, thread_id: str, context: Any) -> ThreadMetadata:
        if thread_id not in self._threads:
            raise ValueError(f"Thread {thread_id} not found")
        return self._threads[thread_id]

    async def load_threads(
        self, limit: int, after: str | None, order: str, context: Any
    ) -> Page[ThreadMetadata]:
        threads = list(self._threads.values())
        start_idx = 0
        if after:
            start_idx = next(
                (i for i, t in enumerate(threads) if t.id == after), 0
            ) + 1
        page_threads = threads[start_idx : start_idx + limit]
        return Page(data=page_threads, has_more=start_idx + limit < len(threads))

    async def delete_thread(self, thread_id: str, context: Any) -> None:
        self._threads.pop(thread_id, None)
        self._items.pop(thread_id, None)

    async def save_item(self, thread_id: str, item: ThreadItem, context: Any) -> None:
        if thread_id not in self._items:
            self._items[thread_id] = {}
        self._items[thread_id][item.id] = item

    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: Any
    ) -> None:
        await self.save_item(thread_id, item, context)

    async def load_item(
        self, thread_id: str, item_id: str, context: Any
    ) -> ThreadItem:
        if thread_id not in self._items or item_id not in self._items[thread_id]:
            raise ValueError(f"Item {item_id} not found")
        return self._items[thread_id][item_id]

    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: Any,
    ) -> Page[ThreadItem]:
        if thread_id not in self._items:
            return Page(data=[], has_more=False)

        items = list(self._items[thread_id].values())
        start_idx = 0
        if after:
            start_idx = next(
                (i for i, item in enumerate(items) if item.id == after), 0
            ) + 1

        page_items = items[start_idx : start_idx + limit]
        return Page(data=page_items, has_more=start_idx + limit < len(items))

    async def delete_thread_item(
        self, thread_id: str, item_id: str, context: Any
    ) -> None:
        if thread_id in self._items:
            self._items[thread_id].pop(item_id, None)
```

## Debugging Tips

### Enable Request Logging

```python
@app.post("/chatkit")
async def chatkit_endpoint(req: Request):
    body = await req.body()
    print(f"Method: {req.method}")
    print(f"Headers: {dict(req.headers)}")
    print(f"Body: {body[:500] if body else b'empty'}")
    # ... rest of handler
```

### Debug Routes

```python
@app.get("/debug")
async def debug_routes() -> dict[str, list[str]]:
    return {"routes": [r.path for r in app.routes]}
```

### Check Server Startup

Verify the server starts without import errors:

```bash
uv run python -c "from mymodule import MyChatKitServer; print('OK')"
```
