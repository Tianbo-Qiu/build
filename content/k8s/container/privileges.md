+++
title = 'Container privileges'
date = '2026-11-01T04:27:59Z'
+++

A container's privileges are the operations the kernel lets its processes perform, such as changing the system clock or loading code into the kernel.

A process does almost everything through system calls, which are requests to the kernel. Processes in a container make these calls to the host's kernel, the same kernel every other container uses. Namespaces change what a call sees, and cgroups limit how much it uses, but neither stops a call that changes something all containers share. In a virtual machine, such a call reaches only the guest's own kernel. So {{< term container-runtime "container runtimes" >}} also limit which calls a container's processes can make.

Traditionally, Linux has two kinds of processes. A process running as root (user ID 0) skips the kernel's permission checks, and every other process is checked. Capabilities split root's power into about 40 separate units, such as `CAP_SYS_TIME` for setting the clock and `CAP_NET_BIND_SERVICE` for using ports below 1024. A process can use only the capabilities it holds, even when it runs as root. By default, Docker keeps 14 capabilities that typical applications need and drops the rest.

Seccomp (secure computing mode) filters the system calls themselves. Before running a call, the kernel checks it against a list of allowed calls, called a profile. Docker's default profile blocks about 44 of more than 300 system calls. In Kubernetes, containers run without a seccomp profile by default, unless the {{< term pod >}} or the {{< term kubelet >}} asks for the runtime's default profile. {{< term apparmor >}} and {{< term selinux >}} add one more layer: kernel policies that decide which files and other resources a process may access, even as root.

For example, suppose a process running as root in a Docker container tries to set the clock. The clock isn't namespaced, so the change would affect every process on the host. Docker's default seccomp profile blocks the call, and the container doesn't hold `CAP_SYS_TIME` either, so the kernel refuses it with a permission error. A privileged container, started with Docker's `--privileged` option, gets all capabilities and, unless one is set explicitly, no seccomp profile. There, the same call succeeds and changes the host's clock.

References: [capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html), [seccomp(2)](https://man7.org/linux/man-pages/man2/seccomp.2.html), [Docker seccomp profiles](https://docs.docker.com/engine/security/seccomp/), [Docker runtime privilege and capabilities](https://docs.docker.com/engine/containers/run/), [Kubernetes seccomp](https://kubernetes.io/docs/tutorials/security/seccomp/)
