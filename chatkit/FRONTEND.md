# ChatKit Frontend Integration

Guide for setting up React/Next.js frontends with the ChatKit client SDK.

## Setup with Next.js

### Package Installation

```bash
npm install @openai/chatkit-react next react react-dom
```

### package.json

```json
{
  "name": "chatkit-demo",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "@openai/chatkit-react": "^1.4.0",
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.0.0"
  }
}
```

### Layout (app/layout.tsx)

```tsx
import type { Metadata } from "next";
import Script from "next/script";

export const metadata: Metadata = {
  title: "ChatKit Demo",
  description: "ChatKit integration demo",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <Script
          src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
          strategy="beforeInteractive"
        />
      </head>
      <body style={{ margin: 0, padding: 0, height: "100vh" }}>
        {children}
      </body>
    </html>
  );
}
```

### Main Page (app/page.tsx)

```tsx
"use client";

import { ChatKit, useChatKit } from "@openai/chatkit-react";

export default function Home() {
  const chatkit = useChatKit({
    api: {
      url: "http://localhost:8000/chatkit",
      domainKey: "local-dev",
    },
    theme: "dark",
    composer: {
      placeholder: "Ask a question...",
    },
    startScreen: {
      greeting: "How can I help you today?",
      prompts: [
        { label: "Example 1", prompt: "What can you help me with?" },
        { label: "Example 2", prompt: "Show me an example" },
      ],
    },
  });

  return (
    <main style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <header style={{ padding: "1rem", borderBottom: "1px solid #333" }}>
        <h1 style={{ margin: 0 }}>My ChatKit App</h1>
      </header>
      <div style={{ flex: 1, display: "flex" }}>
        <ChatKit control={chatkit.control} style={{ flex: 1 }} />
      </div>
    </main>
  );
}
```

## useChatKit Configuration

### Critical Configuration Points

**API Configuration (required):**
```tsx
const chatkit = useChatKit({
  api: {
    url: "http://localhost:8000/chatkit",  // Full URL to backend
    domainKey: "local-dev",                 // Required identifier
  },
  // ...
});
```

**Common mistakes:**
```tsx
// WRONG - apiUrl is not a valid option
useChatKit({ apiUrl: "..." })

// WRONG - missing domainKey
useChatKit({ api: { url: "..." } })

// CORRECT
useChatKit({ api: { url: "...", domainKey: "..." } })
```

### Using the Control Prop

```tsx
// WRONG - chatkit is the full return object
<ChatKit control={chatkit} />

// CORRECT - use chatkit.control
<ChatKit control={chatkit.control} />
```

### Prompt Configuration

```tsx
// WRONG - text is not a valid field
startScreen: {
  prompts: [{ text: "Example prompt" }]
}

// CORRECT - use label and prompt
startScreen: {
  prompts: [
    { label: "Short label", prompt: "Full prompt text sent to agent" }
  ]
}
```

## Common Issues

### Issue: `control.setInstance is not a function`

**Cause:** Passing `chatkit` directly instead of `chatkit.control`

**Fix:**
```tsx
// Change this:
<ChatKit control={chatkit} />

// To this:
<ChatKit control={chatkit.control} />
```

### Issue: `Unrecognized key: "text"`

**Cause:** Wrong prompt structure

**Fix:**
```tsx
// Change this:
prompts: [{ text: "Example" }]

// To this:
prompts: [{ label: "Example", prompt: "Full prompt text" }]
```

### Issue: `Invalid input at api`

**Cause:** Missing `domainKey` in api configuration

**Fix:**
```tsx
api: {
  url: "http://localhost:8000/chatkit",
  domainKey: "local-dev",  // Add this
}
```

### Issue: Network Error / CORS

**Symptoms:**
- `net::ERR_FAILED`
- CORS policy blocked
- 405 Method Not Allowed on OPTIONS

**Fix:** Ensure backend has CORS middleware configured for the frontend origin:
```python
# Backend must include your frontend origin
allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

### Issue: SSE Stream Not Working

**Symptom:** Request succeeds but no streaming response

**Check:**
1. Backend returns `StreamingResponse` with `media_type="text/event-stream"`
2. Frontend sends `Accept: text/event-stream` header (ChatKit does this automatically)

## TypeScript Configuration

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

### next.config.js

```js
/** @type {import('next').NextConfig} */
const nextConfig = {};

module.exports = nextConfig;
```

## Running the Frontend

```bash
cd web
npm install
npm run dev
```

Access at `http://localhost:3000` (or `http://127.0.0.1:3000`)
