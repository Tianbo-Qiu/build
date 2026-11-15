+++
title = 'The Kubernetes network model'
date = '2026-11-14T18:36:10Z'
+++

The Kubernetes network model is the set of rules every cluster's network must follow: each {{< term pod >}} gets its own IP address, and every pod can reach every other pod at that address, on any {{< term node >}}, without address translation. Before Kubernetes, a container usually got an address on a private network inside its host, which other hosts couldn't reach. To be reached from another host, a container's port had to be mapped to a port on the host, and two containers couldn't both be published on the host's port 80. Kubernetes drops that: a pod can be treated like a small machine of its own, with its own address and every port free.

The model has these rules:

- One IP per pod: each pod gets a unique address across the whole cluster. The containers in a pod share it, and reach each other over `localhost`.
- Pod to pod: every pod can reach every other pod directly, on the same node or another, with no proxy and no NAT (network address translation). The receiver sees the sender's real pod IP.
- Node to pod: agents on a node, such as the {{< term kubelet >}}, can reach every pod on that node.
- Exceptions only on purpose: the rules hold unless the cluster deliberately segments the network, such as with NetworkPolicy.

![Two nodes. Node kind-worker2, at 172.21.0.2, has the pod range 10.244.1.0/24 and runs pod client at 10.244.1.6. Node kind-worker, at 172.21.0.4, has the pod range 10.244.2.0/24 and runs pod web at 10.244.2.5. The client pod connects to 10.244.2.5 directly, and the packet arrives from 10.244.1.6, with no NAT. The node kind-worker2 also connects to the web pod directly.](model.svg)

## What can reach a pod

The rules say who must reach a pod. Everything else depends on the cluster. On kind, an nginx pod `web` on kind-worker was tested from each kind of source:

![Pod web at 10.244.2.6 in the middle. Above it, the sources that reach it and connect: a container in the same pod, over localhost; a pod on any node, by pod IP with no NAT; the kubelet on web's node, for health checks; and another node, which works on kind but isn't required. Below it, the sources that don't reach it and get no connection: a pod denied by a NetworkPolicy, and a laptop or container outside the cluster, which has no route to the pod range.](reach.svg)

The same tests, drawn where each source really sits in the kind cluster. Every arrow ends at nginx in pod web, and its label is what happened:

![The kind cluster in detail. Outside the cluster, at the top, the Mac running kind and a container on kind's Docker network each try to reach nginx and get no route. Inside the cluster, whose pods use 10.244.0.0/16, node kind-worker2 at 172.21.0.2, with pods in 10.244.1.0/24, holds three sources: the node itself, which reaches nginx on kind; pod client at 10.244.1.6, which reaches it with no NAT; and a pod denied by a NetworkPolicy, which times out. Node kind-worker at 172.21.0.4, with pods in 10.244.2.0/24, holds pod web at 10.244.2.6, which contains nginx on port 80 and a sidecar that reaches nginx over localhost. Below pod web on the same node, the kubelet reaches nginx with its probes, and pod neighbor reaches it too.](scene.svg)

The outside sources show that pod IPs are addresses inside the cluster. A container started with `docker run --network kind`, on the same Docker network as the nodes, couldn't connect to the pod IP, and neither could the Mac running kind. Neither knows that `10.244.0.0/16` lives behind the nodes. Clients outside the cluster reach pods through a [Service]({{< ref "/k8s/service" >}}) instead. For testing, [Reaching a pod while testing]({{< ref "/k8s/reaching-a-pod" >}}) shows three direct routes.

## Four kinds of traffic

The Kubernetes docs split cluster networking into four problems. The network model covers the first two; [Services]({{< ref "/k8s/service" >}}) build on it for the last two:

- Container to container, in one pod: over `localhost`, because the pod's containers share one network namespace. [Sidecar containers]({{< ref "/k8s/sidecar" >}}) rely on this.
- Pod to pod: by pod IP, as the model requires.
- Pod to Service: by a Service's fixed IP or DNS name, which kube-proxy forwards to a pod IP.
- Outside to Service: through a NodePort, a load balancer, Ingress, or Gateway API.

## Who assigns addresses

A cluster uses three ranges of addresses, which must not overlap:

- Pod IPs come from the cluster's pod range. Each node usually gets its own slice of it, its pod CIDR, and the network plugin gives each new pod on that node an address from the slice.
- Service IPs come from a separate range, assigned by the {{< term api-server >}}.
- Node IPs come from the network the machines are on, reported by the kubelet or the {{< term cloud-controller-manager >}}.

On a three-node kind cluster, the pod range is `10.244.0.0/16`, the Service range is `10.96.0.0/16`, and the nodes sit on Docker's network at `172.21.0.x`. Each node's pod CIDR shows with:

{{< parts >}}
kubectl get nodes | List the cluster's nodes.
-o custom-columns=NAME:.metadata.name,PODCIDR:.spec.podCIDR | Print only the name and the node's slice of the pod range.
{{< /parts >}}

It listed `10.244.0.0/24` for the control plane, `10.244.2.0/24` for kind-worker, and `10.244.1.0/24` for kind-worker2. A pod's IP therefore tells which node it's on: `10.244.2.5` is on kind-worker.

## Pod to pod across nodes

Two pods were placed on different nodes: an nginx pod `web` on kind-worker, and a busybox pod `client` on kind-worker2. `kubectl get pods -o wide` showed their IPs, `10.244.2.5` and `10.244.1.6`. The client reached nginx by pod IP alone:

{{< parts >}}
kubectl exec client | Run a command in the client pod.
-- | Ends kubectl's own options; the rest is the command.
wget -qO- http://10.244.2.5 | Fetch nginx's page from the web pod's IP.
{{< /parts >}}

It printed nginx's welcome page. The nginx access log, from `kubectl logs web`, recorded the request as coming from `10.244.1.6`, the client pod's own IP. Nothing on the way rewrote the source address, which is the "no NAT" rule at work.

## How a packet gets there

Each pod has its own network namespace with one interface, `eth0`, holding the pod IP. That interface is one end of a veth pair, a virtual cable whose other end sits in the node's own network namespace. The node then routes the packet like any router. On kind-worker2, `ip route` showed one route per other node's pod CIDR, and one route per local pod:

```text
10.244.0.0/24 via 172.21.0.3 dev eth0
10.244.1.6 dev vethefc3ef1c scope host
10.244.2.0/24 via 172.21.0.4 dev eth0
```

So a packet for `10.244.2.5` goes to kind-worker at `172.21.0.4`. On kind-worker, the route `10.244.2.5 dev veth5f02253a` hands it to the web pod's veth pair.

![The packet path. In node kind-worker2, pod client sends from eth0 at 10.244.1.6 through its veth pair to the node's route table, which says 10.244.2.0/24 goes via 172.21.0.4. The packet crosses the network between nodes. In node kind-worker, the route table says 10.244.2.5 goes to dev veth5f02253a, which leads to the eth0 of pod web at 10.244.2.5.](path.svg)

This is one way to meet the model: plain routes, which work when all nodes share one network, as kind's nodes do. Other network plugins wrap pod packets in packets between node IPs, called an overlay, or program the cloud provider's routes. The model fixes what pods see, not how packets travel.

## Node to pod

The kubelet sends health checks, such as readiness probes, from the node to each of its pods, so the model requires that a node reach its own pods. From kind-worker2's own network namespace, outside any pod, `curl http://10.244.2.5` returned status 200. So did the same request from the control-plane node. The nginx log showed those requests coming from the nodes' IPs, `172.21.0.2` and `172.21.0.3`. On kind every node reaches every pod, but the model only requires a node to reach the pods on itself.

## Who implements it

Kubernetes defines the model, but most of it is built by other software on each node:

- The container runtime, such as containerd, creates each pod's network namespace through the Container Runtime Interface.
- A network plugin connects that namespace to the pod network and gives the pod its IP. Most runtimes call it through the Container Network Interface (CNI), so these are called CNI plugins. kind installs kindnet; Calico, Cilium, and Flannel are common elsewhere.
- kube-proxy, or a network plugin that replaces it, implements Services on top of pod IPs.
- The network plugin also enforces NetworkPolicy. A plugin that doesn't support it accepts NetworkPolicy objects and ignores them.

## Segmenting with NetworkPolicy

By default every pod accepts connections from everywhere. A NetworkPolicy that selects a pod and lists no allowed sources blocks all incoming connections to it:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-deny-all
spec:
  podSelector:
    matchLabels:
      run: web
  policyTypes: [Ingress]
```

With it applied, the client pod's `wget` to `10.244.2.5` timed out, and after deleting it, the request worked again. A request from kind-worker, the node running the web pod, still returned 200 with the policy in place: the docs state that traffic between a pod and the node it runs on is always allowed.

References: [Services, load balancing, and networking (Kubernetes docs)](https://kubernetes.io/docs/concepts/services-networking/), [Cluster networking (Kubernetes docs)](https://kubernetes.io/docs/concepts/cluster-administration/networking/), [Network policies (Kubernetes docs)](https://kubernetes.io/docs/concepts/services-networking/network-policies/), [CNI specification](https://github.com/containernetworking/cni/blob/main/SPEC.md), [kindnet](https://github.com/kubernetes-sigs/kindnet)
