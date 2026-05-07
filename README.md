# 🎵 This Is Music — Distributed Systems Capstone (IT490 / NJIT)

A fully distributed music web application built across multiple virtualized Ubuntu Server VMs, connected over a private Tailscale mesh network. The system uses a decoupled architecture with RabbitMQ as the message broker, a MySQL InnoDB Cluster for high-availability data storage, Python Flask workers for the backend, and a Python-based frontend served over HTTP with Nginx load balancing.

**Team:** John, Dariel, Meek, Daniel, Jason

---

## Architecture Overview

```
[ Frontend VMs (FE1, FE2) ]
        |
   Nginx Load Balancer (FE1)
     /        \
  FE1:7012   FE2:7012
    (Flask app.py — stateless, cookie auth)
        |
   RabbitMQ Quorum Cluster (3 nodes)
        |
   BE-FE Workers (be_fe.py) — 2 nodes
        |
   RabbitMQ Quorum Cluster
        |
   BE-DB Workers (be_db.py) — 2 nodes
        |
   RabbitMQ Quorum Cluster
        |
   DB Workers (db_worker.py) — 3 nodes
        |
   MySQL Router (port 6446) — 1 per DB node
        |
   MySQL InnoDB Cluster — 3 nodes
   (Single-Primary, auto-failover)
```

All VMs communicate exclusively over a **Tailscale mesh VPN**. No public ports are exposed.

---

## VM Layout

| Role | Nodes | Stack |
|------|-------|-------|
| Frontend | FE1 (Meek), FE2 (Daniel) | Python Flask, Nginx |
| BE-FE Workers | BE-FE1 (Jason), BE-FE2 (Dariel) | Python, pika |
| BE-DB Workers | BE-DB1 (Amaan), BE-DB2 (Jason) | Python, pika |
| RabbitMQ | RMQ1 (Daniel), RMQ2 (Amaan), RMQ3 (Meek) | RabbitMQ quorum cluster |
| Database | DB1 (Dariel), DB2 (Amaan), DB3 (Meek) | MySQL InnoDB Cluster + MySQL Router |
| Composer | DBVM (Amaan) | Bash orchestration scripts |

---

## Key Design Decisions

### RabbitMQ — 3-Node Quorum Cluster
All queues are declared as quorum queues (`x-queue-type: quorum`) for fault tolerance. The cluster tolerates 1 node failure. All worker files use a `RMQ_HOSTS` list with a failover loop — if one node is unreachable the worker automatically tries the next. Heartbeat is set to 300s with blocked connection timeout of 150s.

### MySQL InnoDB Cluster — 3-Node HA
A 3-node InnoDB Cluster provides automatic PRIMARY election on node failure. The cluster tolerates 1 node failure (requires 2/3 for quorum). Each DB node runs its own MySQL Router instance on port `6446`. DB workers connect to a `DB_ROUTER_HOSTS` list — if one Router is down they try the next.

### MySQL Router
Router is not run as a systemd service — it runs from `/tmp/myrouter/` which is wiped on reboot and must be re-bootstrapped. Bootstrap uses a loop that tries all 3 DB nodes in sequence so Router can start even if one node is down. Router reads cluster topology from InnoDB Cluster metadata and automatically reroutes to the new PRIMARY on failover.

### Nginx Load Balancer
Nginx on FE1 load balances between FE1:7012 and FE2:7012. The frontend (`app.py`) is stateless with cookie-based auth and exposes a `/health` endpoint for status checks. If FE1's app.py goes down, Nginx automatically routes all traffic to FE2.

### Composer Orchestration
A custom bash `composer.sh` script on the DBVM orchestrates the entire stack remotely over SSH. It handles ordered startup/shutdown, cluster health checks, and Router bootstrap. Commands: `up`, `down`, `down-safe`, `status`, `logs`.

---

## Message Flow

```
User → Nginx → Flask (app.py)
    → RabbitMQ → be_fe.py
    → RabbitMQ → be_db.py
    → RabbitMQ → db_worker.py
    → MySQL Router (6446)
    → MySQL InnoDB Cluster PRIMARY
```

All inter-service communication uses RabbitMQ RPC pattern with correlation IDs and reply queues. Each layer is independently redundant — multiple instances of each worker share the same queues, and RabbitMQ load balances between them automatically.

---

## Failover Behavior

| Component | Nodes Down | Result |
|-----------|-----------|--------|
| RabbitMQ | 1 of 3 | Fully operational ✅ |
| RabbitMQ | 2 of 3 | Cluster suspended ❌ |
| MySQL Cluster | 1 of 3 | Auto-failover, new PRIMARY elected ✅ |
| MySQL Cluster | 2 of 3 | No quorum, writes fail ❌ |
| Frontend | 1 of 2 | Nginx routes to surviving node ✅ |
| BE-FE / BE-DB / DB Worker | 1 of 2-3 | Other instances absorb load ✅ |

---

## Startup Order

```bash
# 1. RabbitMQ (all 3 nodes)
sudo systemctl start rabbitmq-server

# 2. MySQL (all 3 DB nodes)
sudo systemctl start mysql
# If group replication doesn't auto-start:
mysql -u root -proot123 -h 127.0.0.1 -e "START GROUP_REPLICATION USER='replication_user', PASSWORD='replicapass123';"

# 3. MySQL Router (each DB node, bootstrap from any available node)
for HOST in 100.78.226.13 100.64.56.116 100.124.122.18; do
  echo root123 | sudo mysqlrouter --bootstrap root@$HOST:3306 \
    --directory /tmp/myrouter --user=root --force \
    && sudo chmod 777 /tmp/myrouter && break
done
nohup sudo mysqlrouter --config /tmp/myrouter/mysqlrouter.conf \
  > /tmp/myrouter/router.log 2>&1 &

# 4. DB Workers, BE-DB, BE-FE, Frontend, Nginx
# Or use composer:
./composer.sh up
```

---

## Cluster Recovery

### If metadata is broken (Router shows "No result for metadata query"):
```bash
# From MySQL Shell on any DB node:
mysqlsh root@<any-online-node>:3306
dba.create_cluster('myCluster', {'adoptFromGR': True})
```

### If a node is stuck in RECOVERING:
```bash
# From MySQL Shell on PRIMARY:
cluster = dba.get_cluster()
cluster.remove_instance('root@<stuck-ip>:3306', {'force': True})
cluster.add_instance('root@<stuck-ip>:3306', {'recoveryMethod': 'clone'})
```

### If no quorum:
```bash
# From MySQL Shell on surviving node:
cluster = dba.get_cluster()
cluster.force_quorum_using_partition_of('root@<surviving-ip>:3306')
```

---

## Networking

All inter-VM traffic routes over Tailscale. Key ports:

| Port | Service |
|------|---------|
| 5672 | RabbitMQ AMQP |
| 15672 | RabbitMQ Management UI |
| 3306 | MySQL |
| 33061 | MySQL Group Replication |
| 6446 | MySQL Router (R/W) |
| 6447 | MySQL Router (R/O) |
| 7012 | Frontend Flask app |
| 80 | Nginx load balancer |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Python Flask, HTML/CSS/JS, Nginx |
| Message Broker | RabbitMQ 3-node quorum cluster (pika) |
| Backend Workers | Python 3 (be_fe.py, be_db.py, db_worker.py) |
| Database | MySQL 8.0 InnoDB Cluster + MySQL Router |
| Networking | Tailscale mesh VPN |
| Orchestration | Custom bash composer.sh |
| Virtualization | VirtualBox + Ubuntu Server 24.04 LTS |
