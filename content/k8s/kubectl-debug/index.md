+++
title = 'Ephemeral containers and kubectl debug'
date = '2026-11-14T20:51:01Z'
+++

An ephemeral container is a container added to a {{< term pod >}} that is already running, to inspect it by hand. A pod's containers are fixed when it's created, and `kubectl exec` can only run programs that already exist in a container's image. Many production images have no shell or tools at all: a distroless image holds just the application and its libraries, so `kubectl exec app -- sh` fails with `executable file not found`. The alternative is rebuilding the image with tools and redeploying, which restarts the very pod that showed the problem. An ephemeral container brings its own image, with its own tools, into the pod as it is.

`kubectl debug` creates debugging containers in three ways:

- Ephemeral container: adds a container to the running pod. It shares the pod's network, and with `--target`, the processes of one container.
- Copy of the pod: creates a new pod from the old one's spec with changes, such as another command or image.
- Node debugging: creates a pod on a {{< term node >}} that runs in the node's own namespaces, with the node's root filesystem mounted.

![Three panels. 1, ephemeral container, added to the running pod: in pod app, a debugger container from busybox sits beside the app container, which has no shell; with --target, the debugger sees the app's processes. 2, copy, a new pod to change: pod crash, which keeps crashing, is copied with --copy-to to pod crash-debug, which has a new command and no labels. 3, node, a pod in the node's namespaces: on node kind-worker, pod node-debugger uses the host network, PID, and IPC namespaces, and mounts the node's root filesystem at /host.](modes.svg)

## Ephemeral containers

An ephemeral container is declared like an ordinary container but with fewer guarantees. It is never restarted. It can't have ports, so it can't have probes either, and it can't set resources, because a pod's resource allocations can't change this way. Once added, it can't be changed or removed; it stays in the pod's spec until the pod is deleted. Ephemeral containers are stable since Kubernetes 1.25, and static pods don't support them.

They are added through their own API endpoint, the pod's `ephemeralcontainers` subresource, not by editing the pod's spec. Permission to update a pod doesn't include it, and the default `admin` and `edit` roles leave it out, so adding one needs an explicit grant on `pods/ephemeralcontainers`.

## Adding one to a pod

A pod `app` ran the `pause` image, which holds one binary and no shell, so `kubectl exec app -- sh` failed. An ephemeral container brought busybox into it:

{{< parts >}}
kubectl debug app | Add a debugging container to pod app.
-it | Attach to the new container with input and a terminal, for an interactive shell.
--image=busybox:1.36 | The debugging container's image, which has a shell and tools.
--target=app | Join the process namespace of container app.
+ --profile=general | The security settings to apply. general is the default in recent kubectl.
{{< /parts >}}

The new container shares the pod's network namespace, like every container in a pod: `ip addr` showed the pod's IP, `10.244.2.10`, and `hostname` printed `app`. Processes are separate by default. Without `--target`, `ps` listed only the debugging shell. With it, `ps` listed `/pause` as process 1, running as user 65535. The target's filesystem shows through that process: `ls /proc/1/root` listed the app's own files, including the `pause` binary. The `general` profile gave this targeted container the `SYS_PTRACE` capability, which lets tools such as `strace` trace other processes. The container runtime must support `--target`; without it, the container may not start, or may start with its own process namespace.

After the shell exits, the container stays in the pod with state `Terminated`. `kubectl get pod app` still showed `1/1` ready and no restarts: ephemeral containers don't count toward readiness, and adding one doesn't restart the pod. A second `kubectl debug` with the same container name failed: `existing ephemeral containers "dbg4" may not be changed`. Each session adds a new one.

## Copying a pod

Some changes can't be made to a running pod, such as replacing a crashing container's command. A pod `crash` printed `config missing` and exited with code 1 on each start, so it kept restarting. A copy kept the same image and replaced its command with a shell that stays up:

{{< parts >}}
kubectl debug crash | Debug pod crash.
--copy-to=crash-debug | Create a new pod named crash-debug from crash's spec, and leave crash as it is.
--container=crash | Change this container. Without it, kubectl adds a new container instead.
-- | Ends kubectl's options; the rest is the new command.
sh -c 'sleep 3600' | The new command, which keeps the container running to inspect it.
{{< /parts >}}

The copy ran on the same image and started cleanly. A copy differs from the original in a few ways:

- It has none of the original's labels, so a Service or ReplicaSet that selects the original doesn't pick it up. `--keep-labels` keeps them.
- Its liveness, readiness, and startup probes are removed, so a failing probe doesn't kill it. `--keep-liveness` and the matching flags keep them.
- Its containers share one process namespace, unless `--share-processes=false`.
- `--set-image=crash=busybox:1.37` swaps a container's image, and `*=` swaps all of them.
- `--same-node` places the copy on the original's node.

The copy is an ordinary pod that nothing manages, so it stays until it's deleted.

## Debugging a node

`kubectl debug` can also target a node instead of a pod:

{{< parts >}}
kubectl debug node/kind-worker | Create a debugging pod on node kind-worker.
-it | Attach with input and a terminal.
--image=busybox:1.36 | The image the debugging pod runs.
{{< /parts >}}

It created pod `node-debugger-kind-worker-t5b55`, pinned to that node, with `hostNetwork`, `hostPID`, and `hostIPC` set. The node's root filesystem is mounted at `/host`, through a hostPath volume. Inside it, `ip addr` showed the node's address, `172.21.0.4`, and `ps` showed the node's processes, including the {{< term kubelet >}}. `/host/etc/os-release` named the node's own system, Debian 13. The pod isn't privileged by default, so reading some process information or running `chroot /host` may fail; `--profile=sysadmin` makes it privileged. After the shell exits, the pod stays as `Completed` until it's deleted.

## Profiles

A profile sets the debugging container's security settings, so it fits the pod security level of its namespace or gets the privileges a task needs:

- `general`: a reasonable set for each kind of debugging, such as `SYS_PTRACE` when targeting a container. The default in recent kubectl.
- `baseline` and `restricted`: settings that pass the Pod Security Standards' baseline and restricted policies.
- `netadmin`: adds network administrator privileges.
- `sysadmin`: a privileged container, with system administrator (root) privileges.
- `legacy`: the behavior of kubectl 1.22, which older versions used by default.

`--custom` takes a file with a partial container spec, such as extra environment variables or a security context, and applies it on top of the profile.

Each mode reaches further than the one before: an ephemeral container sees one pod, a copy runs a changed pod, and a node pod sees everything on the node. [Reaching a pod while testing]({{< ref "/k8s/reaching-a-pod" >}}) covers connecting to a pod from outside it.

References: [Ephemeral containers (Kubernetes docs)](https://kubernetes.io/docs/concepts/workloads/pods/ephemeral-containers/), [Debug running pods (Kubernetes docs)](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/), [kubectl debug (Kubernetes docs)](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_debug/), [Share process namespace between containers in a pod (Kubernetes docs)](https://kubernetes.io/docs/tasks/configure-pod-container/share-process-namespace/), [distroless](https://github.com/GoogleContainerTools/distroless)
