+++
title = 'Distributed systems'
date = '2026-11-08T05:59:50Z'
+++

A distributed system is a set of programs on different machines that work together over a network as one system. Systems are split this way to serve more load than one machine can, to keep running when one machine fails, and to let separate teams own separate parts. The cost is that every call between the parts crosses a network, and a network call behaves differently from a call inside one program.

## What changes across a network

A 1994 paper from Sun Microsystems, "A Note on Distributed Computing", names four differences between a remote call and a local one:

- Latency: a network call takes far longer than a function call, and the time varies.
- Memory access: the two sides don't share memory, so data has to be copied into messages.
- Partial failure: one side can fail while the other keeps running, and the caller can't always tell what happened.
- Concurrency: the parts run at the same time, with no single order of events.

![Two scopes. In one process, as in a monolith or hexagonal architecture, one module calls another by a function call, which is fast and can't half-fail. In many processes, as in SOA or microservices, service A calls service B by a network call, which is slow and can fail or time out.](scope.svg)

## Partial failure

When a call times out, the caller doesn't know whether the other side did the work. The request may have been lost, the other side may have crashed, or the work may be done and only the reply lost. Retrying is the usual answer, so the receiver must handle the same request twice safely. One way is an idempotency key: the caller sends a unique key with the request, and the receiver does the work only once per key.

![A sequence diagram between an orders service and a payments service. Orders asks payments to charge 20 dollars. Payments does the charge, but its reply is lost, drawn dashed. Orders times out without knowing whether the charge happened, so it retries with the idempotency key 7f3. Payments answers that the charge is already done for key 7f3, and charges nothing more.](failure.svg)

## Where the styles sit

- [Microservices]({{< ref "/architecture/microservices" >}}) and [SOA]({{< ref "/architecture/styles" >}}) are distributed: each service is its own program, and services call each other over the network.
- A monolith, and [hexagonal architecture]({{< ref "/architecture/styles" >}}) inside one service, are not. Hexagonal architecture keeps network calls in adapters at the edge of the program.

## Key terms

- Node: one machine or process in the system.
- Timeout: how long a caller waits before treating a call as failed.
- Retry: sending a failed call again.
- Idempotent: safe to do more than once with the same result as doing it once.
- Replication: keeping copies of the same data on several nodes, so it survives a node failing.
- Eventual consistency: copies may disagree for a while, but agree once all updates arrive.

References: [A Note on Distributed Computing (Waldo, Wyant, Wollrath, and Kendall, 1994)](https://waldo.scholars.harvard.edu/publications/note-distributed-computing)
