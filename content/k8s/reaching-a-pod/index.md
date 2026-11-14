+++
title = 'Reaching a pod while testing'
date = '2026-11-14T19:07:17Z'
+++

A pod's IP address works only inside the cluster, as the [network model]({{< ref "/k8s/network-model" >}}) describes, so a laptop can't open it directly. Before a pod has a [Service]({{< ref "/k8s/service" >}}), or when a Service doesn't work, there are three ways to talk to it straight away:

- From a node: open a shell on a node and connect to the pod IP. The model requires that a node reach its own pods, so from the pod's own node this has the fewest hops.
- From another pod: start a temporary pod with a client tool and connect to the pod IP over the pod network.
- With port forwarding: `kubectl port-forward` listens on a local port on the laptop and carries each connection through the Kubernetes API to the pod.

![Three routes to nginx in pod web at 10.244.2.9 on node kind-worker. Route 1, from the node: a shell on kind-worker runs curl 10.244.2.9, and nginx sees the client as 10.244.2.1. Route 2, from a pod: a temporary pod tmp at 10.244.1.7 on kind-worker2 connects, and nginx sees 10.244.1.7. Route 3, port forwarding: on the laptop, curl localhost:8080 goes to kubectl port-forward pod/web 8080:80, which streams over the Kubernetes API to the API server, then to the kubelet on kind-worker, which connects inside the pod to localhost:80, and nginx sees 127.0.0.1.](routes.svg)

Each route passes through more parts than the one before. When a connection fails, trying the shortest route first shows whether the pod itself answers, before the pod network or the API is involved.

## From a node

How to get a shell on a node depends on the cluster: kind nodes are Docker containers, minikube has `minikube ssh`, and cloud nodes take SSH.

{{< parts >}}
docker exec | Run a command in a running container, here a kind node.
-it | Keep input open and give it a terminal, for an interactive shell.
kind-worker | The node that runs pod web.
bash | The command: a shell.
{{< /parts >}}

From that shell, `curl 10.244.2.9` returned nginx's page. nginx logged the client as `10.244.2.1`, not the node's address `172.21.0.4`: the node reaches its pods through their veth pairs, and gives each veth on its side the address `10.244.2.1`.

## From another pod

A pod that runs one command and is deleted afterwards tests the pod network the way other pods use it:

{{< parts >}}
kubectl run tmp | Create a pod named tmp.
--rm | Delete it when the command ends.
-i | Keep input open and show the output.
--restart=Never | Create a plain pod that isn't restarted.
--image=curlimages/curl:8.11.1 | An image with curl in it.
-- | Ends kubectl's options; the rest is the command.
curl http://10.244.2.9 | The command the pod runs.
{{< /parts >}}

The pod landed on kind-worker2, and nginx logged the client as `10.244.1.7`, the temporary pod's own IP.

## With port forwarding

Port forwarding needs no pod IP, only the pod's name and port, and works from any machine where kubectl can reach the API server:

{{< parts >}}
kubectl port-forward | Listen on a local port and forward connections to a pod.
pod/web | The pod. A Deployment or Service name also works; kubectl then picks one of its pods.
8080:80 | Local port 8080 to the pod's port 80. With one number, both ports are the same.
{{< /parts >}}

It printed `Forwarding from 127.0.0.1:8080 -> 80` and the same for `[::1]`, and stays in the foreground until stopped. In a second terminal, `curl localhost:8080` returned nginx's page. The connection travels as a stream from kubectl to the {{< term api-server >}}, which passes it to the {{< term kubelet >}} on the pod's node; the API server's connections to kubelets exist for logs, attaching, and port forwarding. The connection to the pod is opened inside the pod's own network namespace, so nginx logged the client as `127.0.0.1`.

- It forwards TCP only.
- It needs permission to create `pods/portforward`. It reaches the pod without crossing the pod network, and the docs warn that it may bypass network-level controls.
- It's for testing: one kubectl process, one laptop, and it stops when kubectl stops.

References: [Use port forwarding to access applications in a cluster (Kubernetes docs)](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/), [Communication between nodes and the control plane (Kubernetes docs)](https://kubernetes.io/docs/concepts/architecture/control-plane-node-communication/), [kubectl run (Kubernetes docs)](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_run/)
