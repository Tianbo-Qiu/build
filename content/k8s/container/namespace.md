+++
title = 'Namespaces'
date = '2026-10-31T21:05:01Z'
+++

A namespace is a Linux kernel feature that gives a group of processes their own instance of one system resource, such as process IDs, network interfaces, or the hostname.

Namespaces let programs on the same machine run without seeing or interfering with each other. A virtual machine does this too, but it runs a separate operating system for each program. Namespaces get much of the same isolation from one shared kernel, so they start faster and use less memory. The trade-off is a weaker boundary: a flaw in the shared kernel can affect every program on it.

A process learns about the system only by asking the kernel. The kernel tracks which namespaces each process belongs to and answers within them. For example, in a new PID namespace, process IDs start again at 1, and processes inside can't see processes outside. The parent namespace still sees each of them, under a different ID.

Linux has eight namespace types: PID, network, mount, UTS (hostname), user, IPC, time, and cgroup. Each process belongs to exactly one namespace of each type, so two processes can share some namespaces and not others. For example, the containers in a Kubernetes pod share a network namespace, so they can reach each other on `localhost`, but each has its own mount namespace and so its own view of the filesystem.

A container is one or more processes running in their own set of namespaces on the host's kernel. Container runtimes such as Docker ask the kernel to create the namespaces, and the kernel does the isolation.

For example, suppose you start two nginx web server containers on the same host. By default, Docker puts each one in new namespaces of most types, including PID, network, and mount. Inside each container, the main nginx process is process 1, it sees only its own network interfaces and IP address, and the files from its image make up its whole filesystem. Both containers can listen on port 80 at the same time, because each port belongs to a different network namespace. On the host, they're just two more nginx processes with ordinary process IDs.

Namespaces don't limit how much CPU or memory processes use. That's a separate kernel feature, [cgroups]({{< ref "cgroups" >}}).

References: [namespaces(7)](https://man7.org/linux/man-pages/man7/namespaces.7.html), [cgroups(7)](https://man7.org/linux/man-pages/man7/cgroups.7.html)
