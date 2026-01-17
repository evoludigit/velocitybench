# **[Pattern] Memberlist Discovery Integration Reference Guide**

---
## **Overview**
Memberlist discovery is a peer-to-peer (P2P) mechanism used in distributed systems (e.g., databases, caches, or messaging brokers) to dynamically track and communicate the presence of nodes in a cluster. This pattern ensures resilience by enabling nodes to **bootstrap, replicate topology data, and failover** without central coordination.

This reference guide outlines **implementation patterns**, **common configurations**, and **best practices** for integrating memberlist discovery into distributed systems. It covers:
- **Core concepts** (gossip protocols, node states).
- **Supported providers** (gRPC, WebRPC, UDP, TCP).
- **Recipes** for handling node joins, leaves, and failures.
- **Error handling** and **performance tuning**.

---

## **1. Schema Reference**

| **Component**               | **Description**                                                                                     | **Required?** | **Default Value**       | **Notes**                                                                                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `Provider`                  | Discovery mechanism (gRPC, WebRPC, UDP, TCP).                                                     | Yes           | `gRPC`                  | UDP/WebRPC are lightweight but less reliable; gRPC/TCP provide structured RPC.                                                                                     |
| `NetworkInterface`          | IP or hostname for binding the discovery server.                                                   | Yes           | `0.0.0.0`               | For containerized deployments, use `host.docker.internal` or `--network=host`.                                                                                   |
| `Port`                      | Port for discovery traffic.                                                                      | Yes           | `7946`                  | Avoid ports < 1024 (requires root).                                                                                                                             |
| `NodeID`                    | Unique identifier for the node (e.g., `{{.Node.Name}}-{{randSuffix}}`).                          | Yes           | Auto-generated          | Should persist across restarts (e.g., in `/var/lib/cluster/`).                                                                                                |
| `GossipInterval`            | Frequency of gossip messages (in seconds).                                                         | No            | `2`                     | Lower values improve latency but increase network load.                                                                                                     |
| `AliveInterval`             | Time before a node is marked as "alive" (seconds).                                                 | No            | `15`                    | Must be ≤ `gossipInterval` + `deadInterval`.                                                                                                                 |
| `DeadInterval`              | Time after which a missing node is declared dead (seconds).                                       | No            | `30`                    | Adjust based on network latency (e.g., `deadInterval = 3 * gossipInterval`).                                                                                     |
| `MaxNodeCount`              | Maximum nodes in the cluster.                                                                    | No            | `64`                    | Increase for large clusters but monitor memory usage.                                                                                                         |
| `Snitch`                    | Location awareness (e.g., `rack`, `datacenter`).                                                  | No            | `null`                  | Used for preference-based routing (e.g., failover within a rack).                                                                                           |
| `AuthToken`                 | Secure token for mutual TLS or API key authentication.                                            | No            | `null`                  | Recommended for multi-tenant setups.                                                                                                                         |
| `TLSConfig`                 | TLS settings for encrypted communication.                                                          | No            | `null`                  | Includes `CAPath`, `CertPath`, `KeyPath`, and `InsecureSkipVerify`.                                                                                             |
| `BindAddress`               | Comma-separated list of network interfaces to bind to.                                             | No            | `0.0.0.0`               | Useful for multi-homed nodes (e.g., `10.0.0.1,192.168.1.1`).                                                                                                 |
| `HealthCheck`               | Endpoint for node liveness probes.                                                                | No            | `/health`               | Should return `200 OK` if node is healthy.                                                                                                                   |

---

## **2. Query Examples**

### **2.1 Node Join**
Request a node to join the cluster:
```bash
curl -X POST http://localhost:7946/v1/memberlist/nodes \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node-1",
    "address": "10.0.0.1:8000",
    "snitch": { "rack": "rack-01" }
  }'
```
**Response:**
```json
{
  "status": "ok",
  "cluster_nodes": [
    {
      "node_id": "node-1",
      "address": "10.0.0.1:8000",
      "state": "alive",
      "last_seen": "2023-10-01T12:00:00Z"
    }
  ]
}
```

---

### **2.2 List All Nodes**
Fetch current cluster topology:
```bash
curl http://localhost:7946/v1/memberlist/nodes
```
**Response:**
```json
{
  "nodes": [
    {
      "node_id": "node-1",
      "address": "10.0.0.1:8000",
      "state": "alive",
      "snitch": { "rack": "rack-01" }
    },
    {
      "node_id": "node-2",
      "address": "10.0.0.2:8000",
      "state": "suspect",
      "last_seen": "2023-10-01T11:55:00Z"
    }
  ]
}
```

---

### **2.3 Force Leave Node**
Remove a node from the cluster:
```bash
curl -X DELETE http://localhost:7946/v1/memberlist/nodes/node-2
```
**Response:**
```json
{
  "status": "ok",
  "removed_nodes": ["node-2"]
}
```

---

### **2.4 Check Node Health**
Probe a node’s liveness:
```bash
curl http://node-1:8000/health
```
**Expected:**
```json
{ "status": "healthy", "timestamp": "2023-10-01T12:05:00Z" }
```

---

## **3. Implementation Patterns**

### **3.1 Gossip-Based Discovery**
- **How it works**: Nodes exchange **periodic gossip messages** to share node states (alive/dead).
- **Configuration**:
  ```yaml
  gossip_interval: "2s"
  alive_interval: "15s"
  dead_interval: "30s"
  ```
- **Best Practices**:
  - Set `dead_interval = 3 * gossip_interval` to account for network jitter.
  - Use **exponential backoff** for failed gossip attempts.

### **3.2 Push/Pull Model**
- **Push**: Nodes actively **notify** others of their state (e.g., on startup).
- **Pull**: Nodes **poll** a centralized registry (e.g., Consul, etcd) for updates.
- **Example (Push)**:
  ```go
  // Pseudocode: Node joins cluster
  node := &Node{
      ID:      "node-1",
      Address: "10.0.0.1:8000",
  }
  if err := memberlist.Join(node); err != nil {
      log.Fatalf("Join failed: %v", err)
  }
  ```

### **3.3 Hybrid Mode (Gossip + Central Registry)**
Combine P2P gossip with a **centralized registry** (e.g., etcd) for:
- **Initial bootstrapping**.
- **High-availability failover**.

**Workflow**:
1. Node queries etcd for initial peers.
2. Gossip protocol maintains real-time updates.

---

## **4. Error Handling & Debugging**

| **Error**                     | **Cause**                                                                 | **Solution**                                                                 |
|-------------------------------|----------------------------------------------------------------------------|------------------------------------------------------------------------------|
| `ErrNodeNotFound`             | Node ID does not exist in cluster.                                        | Verify `NodeID` matches across pods/containers.                                |
| `ErrTimeout`                  | Gossip messages timed out.                                                | Increase `gossip_interval` or check network latency.                           |
| `ErrInvalidState`             | Node reported an invalid state (e.g., "dead" when alive).                 | Fix the node’s health check or adjust `alive_interval`.                       |
| `ErrTLSHandshakeFailed`       | TLS configuration mismatch.                                               | Verify `CertPath`, `KeyPath`, and `CAPath`.                                   |
| `ErrMaxNodesExceeded`         | Cluster size exceeds `MaxNodeCount`.                                       | Scale horizontally or increase `MaxNodeCount`.                               |
| `ErrSnitchMisconfigured`      | Invalid `snitch` configuration.                                           | Validate `rack`/`datacenter` values.                                         |

**Debugging Commands**:
```bash
# Check gossip logs
journalctl -u memberlist-service -f

# Monitor network traffic
tcpdump -i eth0 port 7946 -A
```

---

## **5. Performance Tuning**

| **Parameter**               | **Impact**                                                                 | **Recommendation**                                                                 |
|------------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| `gossip_interval`            | Lower = faster convergence but higher network load.                        | Start with `2s`; adjust based on cluster size.                                     |
| `MaxNodeCount`               | Higher = more memory usage for node tracking.                             | Benchmark with `32` nodes before scaling.                                           |
| `BindAddress`                | Multi-homed nodes improve reliability but add complexity.                 | Use `0.0.0.0` for simplicity unless multi-interface is critical.                    |
| `TLS`                        | Encryption adds latency (~10-50ms).                                       | Enable TLS only if security is critical; use `InsecureSkipVerify` for testing.    |

---

## **6. Related Patterns**

| **Pattern**                  | **Description**                                                                 | **When to Use**                                                                   |
|------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **[Ring Population](https://docs.hashicorp.com/consul/api-docs/ring-population)** | Distributes nodes in a consistent hash ring.                                  | For latency-sensitive read/write operations (e.g., databases).                     |
| **[Anti-Affinity](https://kubernetes.io/docs/tasks/configure-pod-container/assign-pods-node/#inter-pod-affinity-and-anti-affinity)** | Ensures nodes are scheduled across availability zones.                         | High-availability clusters with multi-region deployments.                          |
| **[Leader Election](https://pkg.go.dev/github.com/hashicorp/raft#LeaderElection)** | Elects a primary node for centralized coordination.                          | For stateful services requiring strong consistency (e.g., databases).              |
| **[Rate Limiting](https://pkg.go.dev/golang.org/x/time/rate)** | Throttles gossip traffic to avoid flooding.                                  | During cluster storms (e.g., rapid node joins/leaves).                            |
| **[Service Mesh Integration](https://istio.io/latest/docs/concepts/traffic-management/)** | Integrates with Istio/Linkerd for mTLS and observability.                    | Production deployments requiring fine-grained traffic control.                   |

---

## **7. Example: Full Configuration (YAML)**
```yaml
# memberlist.config.yaml
provider: "gRPC"
network_interface: "0.0.0.0"
port: 7946
node_id: "{{.Node.Name}}-{{randSuffix 8}}"
gossip_interval: "2s"
alive_interval: "15s"
dead_interval: "30s"
max_node_count: 64
snitch:
  rack: "{{.Node.Rack}}"
  datacenter: "{{.Node.Datacenter}}"
health_check:
  endpoint: "/health"
  interval: "10s"
tls:
  ca_path: "/etc/ssl/ca.pem"
  cert_path: "/etc/ssl/node-cert.pem"
  key_path: "/etc/ssl/node-key.pem"
```

---
## **8. Troubleshooting Checklist**
1. **Network Connectivity**:
   - Verify nodes can ping each other (`ping 10.0.0.1`).
   - Check firewall rules (`sudo iptables -L`).
2. **Configuration Validity**:
   - Validate YAML/JSON configs with `yq` or `jq`.
3. **Logs**:
   - Look for `ERR` or `WARN` in `journalctl`/`stdout`.
4. **Topology**:
   - Run `curl localhost:7946/v1/memberlist/nodes` to audit node states.
5. **Dependencies**:
   - Ensure `consul`, `etcd`, or `gRPC` dependencies are running.

---
## **9. References**
- [HashiCorp Memberlist Go Doc](https://pkg.go.dev/github.com/hashicorp/memberlist)
- [Raft Consensus Algorithm](https://raft.github.io/)
- [Kubernetes Node Affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)

---
**Last Updated**: `2023-10-01`
**Version**: `1.2.0`