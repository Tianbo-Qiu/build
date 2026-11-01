+++
title = 'cgroups'
date = '2026-11-01T03:50:50Z'
+++

A cgroup (control group) is a Linux kernel feature that puts processes in a group and limits how much of a resource, such as CPU time or memory, the group can use.

Processes on one machine share its CPU and memory. Without limits, one process that leaks memory or loops forever can starve the rest, including the system's own processes. A virtual machine prevents this by giving each workload fixed hardware. cgroups get a similar effect from one shared kernel: the kernel already decides which process runs next and who gets memory, so it can enforce a budget each time. Namespaces can't do this, because they control what a process can see, not how much it can use.

cgroups form a tree. In cgroup v2, each process belongs to exactly one cgroup, and a new process starts in its parent's cgroup. A limit on a cgroup also covers every cgroup below it, so a parent can split its budget among its children, but they can't exceed it together. Each kind of resource is managed by a part of the kernel called a controller, such as `cpu`, `memory`, `io` for disk, and `pids` for the number of processes.

Controllers enforce limits differently, because resources differ. CPU time can be delayed, so a group that uses its CPU quota for the current period waits until the next one. This is called throttling: the processes slow down but keep running. Memory can't be delayed. When a group reaches its memory limit, the kernel first tries to free some of the group's memory, such as cached file data. If it can't, the kernel's out-of-memory (OOM) killer ends a process in that group.

For example, suppose a Kubernetes container has a CPU limit of half a core and a memory limit of 256 MiB. The kubelet and the container runtime put the container's processes in their own cgroup and set its limits. Under heavy load, the container gets at most 50 ms of CPU time in every 100 ms period (the default period), so its work slows down. If its memory use grows past 256 MiB and the kernel can't free any, the kernel kills a process in the container. When that's the main process, the container stops and Kubernetes reports the reason as `OOMKilled`. Other containers on the node keep their own budgets throughout.

References: [cgroups(7)](https://man7.org/linux/man-pages/man7/cgroups.7.html), [Control Group v2](https://docs.kernel.org/admin-guide/cgroup-v2.html), [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)
