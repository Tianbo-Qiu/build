+++
title = 'Kubernetes architecture'
date = '2026-11-01T18:41:56Z'
+++

Kubernetes architecture is the way Kubernetes splits its work between a control plane, which decides what should run, and nodes, the machines that run it.

Running containers on one machine is easy. Running them across many machines that can fail is hard: something has to pick a machine for each container, restart containers that crash, and move them when a machine dies. Kubernetes does this for you. You describe the state you want, such as three instances of a web server, and Kubernetes keeps working to make the actual state match it. Like a thermostat, it doesn't act once and stop. It keeps checking.

The control plane has four main components. The API server is the front door: people, tools such as {{< term kubectl >}}, and every other component read and change the cluster's state only through it. It stores that state in etcd, a key-value database. The scheduler picks a node for each new {{< term pod >}}. The controller manager runs controllers, which are loops that each watch one kind of object and act to move the actual state toward the desired state.

Each node runs a kubelet. It watches the API server for pods assigned to its node, asks the {{< term container-runtime >}} to start their containers, and reports their status back. Most clusters also run kube-proxy on each node. It sets up network rules so that traffic sent to a {{< term service >}} reaches one of its pods.

The components don't give each other orders. Each one watches the API server for the objects it cares about, does its own job, and writes the result back. Only the API server talks to etcd.

![The control plane holds the scheduler, the controller manager, the API server, and etcd. Each node holds the kubelet, kube-proxy, the container runtime, and pods. kubectl, the scheduler, the controller manager, the kubelet, and kube-proxy all connect to the API server, and only the API server connects to etcd.](architecture.svg)

For example, suppose you use kubectl to create a {{< term deployment >}} that asks for three nginx pods. The API server stores it in etcd. The Deployment controller notices it and creates a {{< term replicaset >}}, and the ReplicaSet controller creates three pods. The pods have no node yet, so the scheduler assigns one to each. The kubelet on each chosen node sees its new pod, has the container runtime start nginx, and reports that the pod is running. If a node fails, the control plane deletes that node's pods after a timeout, and the ReplicaSet controller sees too few pods and creates a replacement.

References: [Kubernetes components](https://kubernetes.io/docs/concepts/overview/components/), [Controllers](https://kubernetes.io/docs/concepts/architecture/controller/), [Cluster architecture](https://kubernetes.io/docs/concepts/architecture/)
