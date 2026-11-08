+++
title = 'SOA and hexagonal architecture'
date = '2026-11-08T06:05:18Z'
+++

Two older styles come up next to [microservices]({{< ref "/architecture/microservices" >}}). Service-oriented architecture (SOA) came before them and splits a system into services across the network, so it's [distributed]({{< ref "/architecture/distributed-systems" >}}). Hexagonal architecture organizes the inside of one program, so it isn't distributed, and each microservice can be built that way.

## Service-oriented architecture

SOA builds large systems from services: separate programs that each offer one business capability, such as checking a customer's credit, through a published contract that others call over the network. The OASIS reference model of 2006 defines it as "a paradigm for organizing and utilizing distributed capabilities that may be under the control of different ownership domains". It grew in large companies in the early 2000s, to replace custom point-to-point links between many separate systems. Services described their operations in WSDL and exchanged XML messages in SOAP envelopes, both W3C notes from 2000 and 2001, and usually talked through an enterprise service bus (ESB): central middleware that routed and transformed messages and often held business rules.

![On the left, point-to-point integration: CRM, billing, orders, and warehouse systems each connected directly to several others, six links in all. On the right, SOA with an enterprise service bus: CRM and billing services send to the bus, which handles routing, transformation, and rules, and delivers to the orders and warehouse services.](esb.svg)

What worked, and carried over into microservices: services built around business capabilities, explicit contracts, and calls across languages and vendors through standard formats.

What went wrong:

- The pipes got smart. The ESB collected routing and business rules in one central product, so many changes waited on the team that ran it.
- The standards grew heavy. The WS-* family of web service standards reached, in James Lewis and Martin Fowler's words, "a complexity that is, frankly, breathtaking".
- Governance slowed change, with central reviews and shared data models for every service.
- The network was hidden. Tools made remote calls look like local ones, which made systems fragile.

In 2009, analyst Anne Thomas Manes wrote that "SOA met its demise on January 1, 2009", calling it "a great failed experiment" for most organizations, though the need for services lived on. Microservices, described in 2014, keep SOA's services and drop the central bus: logic lives in the services, and the network only carries messages.

## Hexagonal architecture

Hexagonal architecture, also called ports and adapters, keeps a program's business logic free of outside technology. Alistair Cockburn described it in 2005. The core defines interfaces, called ports, for everything it needs from the outside, such as "save an order", and small adapters connect each port to a real technology, such as a SQL database or an HTTP framework. The core depends on nothing outside itself, so it can be tested with an in-memory adapter instead of a real database, and the database can be replaced without changing the logic.

![An orders application drawn as a hexagon, the application core, holding the ordering rules and its ports PlaceOrder, OrderStore, and Payments. On the left, an HTTP controller and a test harness, drawn dashed, call PlaceOrder. On the right, the core calls OrderStore, implemented by a SQL adapter that talks to a database or by an in-memory fake, drawn dashed, and Payments, implemented by a payments API client that makes a network call to the payments service.](hexagon.svg)

Driving adapters, on the left, call into the core; driven adapters, on the right, are called by it. In a microservice built this way, the network shows up only in driven adapters that call other services. They handle timeouts and retries, and the business rules don't change if a dependency moves from the same process to another service. The six sides mean nothing: Cockburn drew a hexagon to leave room for several ports.

References: [OASIS Reference Model for SOA 1.0](https://docs.oasis-open.org/soa-rm/v1.0/soa-rm.html), [SOAP 1.1](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/), [WSDL 1.1](https://www.w3.org/TR/wsdl.html), [R.I.P. SOA, InfoWorld, quoting Anne Thomas Manes](https://www.infoworld.com/article/2177696/r-i-p-soa.html), [Microservices, by James Lewis and Martin Fowler](https://martinfowler.com/articles/microservices.html), [Hexagonal architecture, by Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
