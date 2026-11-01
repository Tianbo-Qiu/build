+++
title = 'Managed Kubernetes clusters'
date = '2026-11-01T19:15:57Z'
+++

A managed Kubernetes cluster is a cluster whose control plane a cloud provider runs for you, as in Google Kubernetes Engine (GKE), Amazon Elastic Kubernetes Service (EKS), or Azure Kubernetes Service (AKS).

The control plane is the hard part to operate. etcd holds the state of the whole cluster, so it needs several copies and backups, and the control plane needs regular upgrades as Kubernetes releases new versions. A managed service takes on that work, and you keep the part your apps run on.

The [architecture]({{< ref "/k8s/architecture" >}}) stays the same: an API server, etcd, a scheduler, controllers, and a {{< term kubelet >}} on each {{< term node >}}. What changes is who runs each part and where. The provider runs the control plane on its own infrastructure, separate from your account, and gives you one address for the API server. The worker nodes are usually virtual machines in your account, and their kubelets reach the API server at that address, the same way {{< term kubectl >}} does. Because components talk only through the API server, the split needs nothing new. It also means your cluster's list of nodes shows only the worker nodes.

Managed clusters also run the {{< term cloud-controller-manager >}}, an optional control plane component that connects Kubernetes to the provider's APIs. When a new virtual machine joins, it adds the machine's cloud details to the node, and it removes nodes whose machine is gone. When you create a {{< term service >}} that asks for a load balancer, it has the cloud create one. A [local cluster]({{< ref "/k8s/local-clusters" >}}) has no cloud behind it, so features like these need workarounds there.

![Three layers. Your computer runs kubectl. The cloud provider's infrastructure runs the API server and, beside it, etcd, the scheduler, the controller manager, and the cloud-controller-manager. Your cloud account runs node VMs, each with a kubelet and pods. kubectl and each kubelet connect to the API server.](managed-clusters.svg)

For example, suppose you create an EKS cluster with a managed node group of three virtual machines, which AWS creates and updates for you. AWS runs at least two API server instances and three etcd instances, spread across three availability zones, which are separate data centers in one region, and it replaces any instance that fails. The three virtual machines start in your account, their kubelets register with the API server, and they become the cluster's nodes. When you add a fourth machine to the group, it joins the same way.

In return, you give up some control. You can't reach etcd or change control plane settings beyond what the provider exposes. Some modes go further and run the nodes for you as well, such as GKE Autopilot and EKS Auto Mode, which leaves you with only your pods.

References: [Cloud controller manager](https://kubernetes.io/docs/concepts/architecture/cloud-controller/), [GKE cluster architecture](https://docs.cloud.google.com/kubernetes-engine/docs/concepts/cluster-architecture), [Amazon EKS architecture](https://docs.aws.amazon.com/eks/latest/userguide/eks-architecture.html)
