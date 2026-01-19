# **Debugging Websockets Observability: A Troubleshooting Guide**

Websockets enable real-time bidirectional communication between clients and servers, but they introduce complexity in observability due to their persistent connections, event-driven nature, and potential for connection drops. This guide helps diagnose and resolve common Websockets observability issues efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, verify these symptoms:

| Symptom Category       | Possible Issues                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Connection Issues**  | Websocket handshake failures, timeouts, or sudden disconnections.               |
| **Performance Issues** | High latency, dropped messages, or inconsistent throughput.                     |
| **Observability Gaps** | Missing metrics (e.g., connection count, message rate), logs, or traces.       |
| **Error Spikes**       | Sudden increase in reconnection attempts, connection errors, or failed pings. |
| **Resource Constraints** | High CPU/memory usage on the Websocket server or client.                       |

If multiple symptoms coexist, prioritize **connection stability** first.

---

## **2. Common Issues and Fixes**

### **Issue 1: Websocket Connection Drops (Handshake Failures, Timeouts)**
**Symptoms:**
- Clients fail to establish connections (`1006: abnormal closure` or `1002: policy violation`).
- Server logs show no incoming Websocket requests despite client attempts.

**Root Causes:**
- **Firewall/Network Restrictions:** Port blocking (default Websocket port: `80`, `443`, or custom).
- **CORS Misconfiguration:** Missing `Access-Control-Allow-Origin` headers.
- **Protocol Mismatch:** Server expects `ws://` but client uses `wss://` (or vice versa).
- **Load Balancer Issues:** Termination of Websocket handshake (common in HTTP-based LBs).

**Fixes:**
#### **Code: Verify Handshake Headers (Node.js/Express Example)**
```javascript
const WebSocket = require('ws');
const express = require('express');
const app = express();
const server = require('http').createServer(app);
const wss = new WebSocket.Server({ server });

// Ensure CORS and handshake headers are correct
wss.on('connection', (ws) => {
  console.log('Client connected');
  ws.on('message', (message) => {
    console.log('Received:', message);
    ws.send('Server received message');
  });
});

// Serve static files to avoid 404s during handshake
app.use(express.static('public'));

server.listen(8080, () => {
  console.log('Websocket server running on port 8080');
});
```

#### **Debugging Steps:**
1. **Test with `curl` or Postman:**
   ```bash
   curl -v ws://your-server:8080/socket
   ```
   - Check for `101 Switching Protocols` response.
2. **Inspect Network Traffic:**
   - Use **Wireshark** or browser DevTools (`Application > WebSocket`) to verify:
     - Handshake requests (`Upgrade: websocket`).
     - Missing headers (e.g., `Sec-WebSocket-Protocol`).
3. **Check Load Balancer Settings:**
   - If using Nginx/ALB, ensure Websocket upgrading is enabled:
     ```nginx
     location /ws/ {
       proxy_pass http://backend;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
     }
     ```

---

### **Issue 2: Missing Observability Metrics (Connection Count, Latency)**
**Symptoms:**
- No metrics in Prometheus/Grafana for Websocket connections.
- Logs lack timestamped connection events.

**Root Causes:**
- No instrumentation in Websocket server/client.
- Missing middleware for log/metric collection.

**Fixes:**
#### **Code: Instrument Websocket Server (Prometheus + OpenTelemetry)**
```javascript
const { WebSocketServer } = require('ws');
const client = require('prom-client');

// Metrics
const connectionCount = new client.Counter({
  name: 'websocket_connections_total',
  help: 'Total Websocket connections opened',
});
const messageSent = new client.Counter({
  name: 'websocket_messages_sent_total',
  help: 'Total Websocket messages sent',
});
const messageReceived = new client.Counter({
  name: 'websocket_messages_received_total',
  help: 'Total Websocket messages received',
});

const wss = new WebSocketServer({ port: 8080 });

wss.on('connection', (ws, req) => {
  connectionCount.inc();
  ws.on('message', (data) => {
    messageReceived.inc();
    ws.send(`Server: ${data.toString()}`);
    messageSent.inc();
  });
  ws.on('close', () => connectionCount.dec());
});

// Expose metrics endpoint
const collectDefaultMetrics = client.collectDefaultMetrics;
collectDefaultMetrics({ prefix: 'app_' });
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', client.register.contentType);
  res.end(await client.register.metrics());
});
```

#### **Debugging Steps:**
1. **Verify Metrics Endpoint:**
   ```bash
   curl http://localhost:8080/metrics
   ```
   - Look for `websocket_connections_total` and message counters.
2. **Check OpenTelemetry Traces:**
   - If using distributed tracing (Jaeger/Zipkin), ensure Websocket events are traced:
     ```javascript
     const { WebSocketServer } = require('ws');
     const { registry, TraceSpan } = require('@opentelemetry/sdk-trace-node');

     const wss = new WebSocketServer({ port: 8080 });
     wss.on('connection', (ws) => {
       const span = TraceSpan.active('websocket-handshake');
       span.addEvent('connection-established');
       span.end();
     });
     ```
3. **Log Connection Lifecycle:**
   - Add structured logs:
     ```javascript
     const pino = require('pino');
     const logger = pino();
     wss.on('connection', (ws) => {
       logger.info('New connection', { client: ws.remoteAddress });
       ws.on('close', () => logger.info('Connection closed'));
     });
     ```

---

### **Issue 3: High Latency or Dropped Messages**
**Symptoms:**
- Clients report delayed responses or lost messages.
- Server-side logs show no corresponding messages.

**Root Causes:**
- **Buffer Overflows:** Unhandled message queues (e.g., Node.js `ws.on('message')` pileup).
- **Network Congestion:** High TTFB (Time to First Byte) for Websocket upgrades.
- **Client-Side Throttling:** Clients not acknowledging messages (e.g., browser tabs in background).

**Fixes:**
#### **Code: Rate-Limit Messages (Node.js)**
```javascript
const { WebSocketServer } = require('ws');
const { RateLimiterMemory } = require('rate-limiter-flexible');

const limiter = new RateLimiterMemory({
  points: 100, // Max 100 messages/sec
  duration: 1,
});

const wss = new WebSocketServer({ port: 8080 });

wss.on('connection', async (ws) => {
  ws.on('message', async (data) => {
    try {
      await limiter.consume(ws.remoteAddress);
      ws.send(`Processed: ${data}`);
    } catch (rejected) {
      ws.send('Rate limit exceeded');
    }
  });
});
```

#### **Debugging Steps:**
1. **Monitor Message Throughput:**
   - Use Prometheus to track:
     ```promql
     rate(websocket_messages_received_total[1m])
     ```
   - Spikes >90% of `rate-limiter` cap indicate bottlenecks.
2. **Check Client-Side Network:**
   - Use **Lighthouse** (Chrome DevTools) to test real-world latency:
     ```bash
     lighthouse --view --preset=web-vitals https://your-app.com
     ```
3. **Enable Websocket Ping/Pong:**
   - Force periodic pings to detect silent drops:
     ```javascript
     const interval = setInterval(() => {
       if (ws.readyState === ws.OPEN) ws.ping();
     }, 30000);
     ws.on('pong', () => console.log('Ping acknowledged'));
     ```

---

### **Issue 4: Resource Exhaustion (Memory/CPU Spikes)**
**Symptoms:**
- Server crashes or becomes unresponsive during high traffic.
- Websocket connections leak (e.g., `wss.clients.size` grows indefinitely).

**Root Causes:**
- **Memory Leaks:** Unclosed Websocket connections or event listeners.
- **CPU-Greedy Loops:** Blocking `on('message')` handlers (e.g., slow DB queries).

**Fixes:**
#### **Code: Detect and Clean Up Leaks (Node.js)**
```javascript
const { WebSocketServer } = require('ws');
const cluster = require('cluster');

if (cluster.isMaster) {
  setInterval(() => {
    console.log(`Active connections: ${wss.clients.size}`);
    if (wss.clients.size > 1000) {
      console.warn('Cleaning up connections...');
      wss.clients.forEach((client) => client.terminate());
    }
  }, 60000);
}

const wss = new WebSocketServer({ port: 8080 });
wss.on('connection', (ws) => {
  ws.on('close', () => {
    console.log('Connection closed');
    // Clean up resources
    ws.removeAllListeners();
  });
});
```

#### **Debugging Steps:**
1. **Profile Memory Usage:**
   - Use `node-inspector` or `heapdump`:
     ```bash
     node --inspect ./server.js
     ```
   - Look for retained Websocket objects in V8 heap snapshots.
2. **Use Process Manager (PM2):**
   - Restart workers on crashes:
     ```bash
     pm2 start server.js --max-memory-restart 300M
     ```
3. **Optimize Event Loops:**
   - Offload heavy work (e.g., DB calls) to queues:
     ```javascript
     const Bull = require('bull');

     const queue = new Bull('websocket-queue');
     wss.on('connection', (ws) => {
       ws.on('message', async (data) => {
         await queue.add({ task: 'process', data });
         ws.send('Queued for processing');
       });
     });
     ```

---

## **3. Debugging Tools and Techniques**

| Tool/Technique          | Purpose                                                                 | Example Command/Setup                                        |
|-------------------------|-------------------------------------------------------------------------|-------------------------------------------------------------|
| **Wireshark**           | Inspect raw Websocket handshakes/frames.                                | `tshark -i any port 8080`                                    |
| **Prometheus + Grafana**| Track connection/metric trends.                                         | Scrape `/metrics` endpoint.                                |
| **OpenTelemetry**       | Distributed tracing for Websocket calls.                                | `otel-nodejs`: `require('@opentelemetry/sdk-node');`       |
| **Chrome DevTools**     | Test Websocket connections in-browser.                                | `Application > WebSocket` tab.                             |
| **K6**                  | Load-test Websocket scalability.                                        | ```javascript // k6 script import ws from 'k6/experimental/ws'; export default function () { const client = new ws.Client('ws://localhost:8080'); } ``` |
| **Netdata**             | Real-time CPU/memory monitoring.                                        | `netdata install` (Linux).                                 |
| **Pino Logger**         | Structured logging for Websocket events.                                | `const logger = pino({ level: 'info' });`                  |

---

## **4. Prevention Strategies**

### **Design-Level Preventions:**
1. **Connection Timeouts:**
   - Set reasonable timeouts (e.g., 30s inactivity):
     ```javascript
     wss.on('connection', (ws) => {
       ws.setTimeout(30000, () => ws.terminate());
     });
     ```
2. **Graceful Degradation:**
   - Fall back to polling if Websockets fail:
     ```javascript
     if (!WebSocket) {
       setInterval(() => fetch('/poll-endpoint'), 5000);
     }
     ```
3. **Auto-Reconnect Clients:**
   - Implement exponential backoff:
     ```javascript
     let retryCount = 0;
     const maxRetries = 5;
     const connect = () => {
       const ws = new WebSocket('ws://server');
       ws.onopen = () => retryCount = 0;
       ws.onerror = () => {
         if (retryCount < maxRetries) {
           setTimeout(connect, 1000 * Math.pow(2, retryCount++));
         }
       };
     };
     connect();
     ```

### **Observability-Level Preventions:**
1. **Centralized Logging:**
   - Use ELK Stack (Elasticsearch + Logstash + Kibana) or Loki:
     ```javascript
     const { ElasticsearchClient } = require('@elastic/elasticsearch');
     const client = new ElasticsearchClient({ node: 'http://localhost:9200' });
     wss.on('connection', (ws) => {
       ws.on('message', async (data) => {
         await client.index({
           index: 'websocket-events',
           body: { message: data, timestamp: new Date() },
         });
       });
     });
     ```
2. **Synthetic Monitoring:**
   - Use tools like **Datadog** or **New Relic** to ping Websocket endpoints periodically.
3. **Anomaly Detection:**
   - Set up alerts for:
     - `websocket_connections_total > 95% threshold`.
     - `p50(message_latency) > 500ms`.

### **Infrastructure-Level Preventions:**
1. **Auto-Scaling:**
   - Scale Websocket servers horizontally (e.g., Kubernetes `HorizontalPodAutoscaler`).
2. **Cold Start Mitigation:**
   - Pre-warm Websocket servers (e.g., AWS Lambda provisioned concurrency).
3. **Network Redundancy:**
   - Use **DNS failover** (e.g., Route 53) or **multi-region Websocket endpoints**.

---

## **5. Quick Summary Table**
| **Issue**               | **Immediate Fix**                          | **Long-Term Solution**                     |
|-------------------------|--------------------------------------------|--------------------------------------------|
| Connection drops        | Check CORS/firewall, test handshake.       | Use Websocket load balancer (e.g., Kong).  |
| Missing metrics         | Add Prometheus/OpenTelemetry.              | Centralize logs with ELK/Loki.            |
| High latency            | Rate-limit messages, optimize network.     | Use CDN (e.g., Cloudflare) for global reach. |
| Resource exhaustion     | Clean up listeners, monitor memory.        | Implement autoscaling (K8s/PM2).           |
| Dropped messages        | Enable pings, check client-side throttling. | Design idempotent message queues.         |

---
**Final Tip:** Start with **connection stability** (handshake, CORS) before diving into observability. Use **Prometheus + Grafana** for proactive monitoring, and **OpenTelemetry** for distributed tracing of Websocket flows.