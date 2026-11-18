+++
title = 'mTLS'
date = '2026-11-18T17:32:58Z'
+++

Mutual TLS (mTLS) is [TLS]({{< ref "/networking/tls" >}}) in which the client also proves its identity with a certificate, not just the server. In ordinary TLS, only the server shows a certificate: the client learns who the server is, but the server learns nothing about the client, which then identifies itself inside the connection with a password, a token, or a cookie. mTLS moves the client's identity into the handshake. A client without a certificate the server trusts can't finish the handshake, so it never sends a request the server would process.

Compared with TLS, mTLS adds:

- A client certificate and private key: the client holds its own key pair and a certificate binding a name, such as `client`, to the public key.
- A trust store on the server for clients: the CA certificates whose clients the server accepts, often a private CA.
- Three handshake messages: the server asks for a certificate, and the client sends its certificate and a signature made with its private key.

![The parts of mTLS. The certificate authority Lab Root CA signs web.crt for server web and client.crt for the client. Server web holds web.crt and web.key, named web, and trusts ca.crt for clients. The client holds client.crt and client.key, named client, and trusts ca.crt for servers.](parts.svg)

The examples here ran in two containers on one Docker network, a server `web` and a client, with OpenSSL 3.5 and curl 8.14, and on a three-node kind cluster running Kubernetes 1.37. The server's key, certificate, and the lab CA are the ones from the TLS page.

## Client certificates

A client certificate is made the same way as a server certificate: the client creates a private key and a certificate signing request, and a CA signs it. Two things differ. The subject names a client, such as a user, a service, or a machine, rather than a host name the client typed. And its extended key usage allows client authentication instead of server authentication:

```text
basicConstraints=CA:FALSE
keyUsage=digitalSignature
extendedKeyUsage=clientAuth
```

{{< parts >}}
openssl x509 -req | Sign a certificate signing request.
-in client.csr | The client's request, with subject O=lab, CN=client.
-CA ca.crt -CAkey ca.key | Sign as Lab Root CA.
-days 90 | Valid for 90 days.
-extfile client.ext | Add the extensions above, which allow client authentication.
-out client.crt | Write the client certificate.
{{< /parts >}}

The server and the client can trust different CAs: a public CA for the server's name, and a private CA that the server's operator runs for its clients. Here the same lab CA signs both.

## Requiring a client certificate

The server asks for client certificates and names the CAs it accepts for them:

{{< parts >}}
openssl s_server -accept 443 | Run a test TLS server on port 443.
-cert web.crt -key web.key | The server's own certificate and key, as in TLS.
-CAfile ca.crt | Trust client certificates signed by ca.crt.
-Verify 1 | Require a client certificate, with a chain at most one CA deep.
-verify_return_error | End the handshake when the check fails.
-www | Answer HTTP requests with a status page.
{{< /parts >}}

Without `-verify_return_error`, `s_server` only logged a failed check and let the client in: a certificate from an untrusted CA got the status page. Servers differ in whether a client certificate is optional, requested, or required, so the setting decides whether mTLS rejects anyone.

The client sends its certificate and key along with the request:

{{< parts >}}
curl https://web/ | Fetch the page over HTTPS.
--cacert ca.crt | Trust server certificates signed by ca.crt.
--cert client.crt | The client certificate to send when the server asks.
--key client.key | The client's private key, which signs the handshake.
{{< /parts >}}

## The handshake

mTLS changes the TLS 1.3 handshake in two places. The server's first flight adds a CertificateRequest. The client's flight, which in TLS holds only Finished, adds its own Certificate and CertificateVerify:

![The mTLS handshake between the client and server web. The client sends ClientHello. The server sends ServerHello, then, encrypted, CertificateRequest, which is new, and its Certificate, CertificateVerify, and Finished. The client sends, encrypted, its Certificate and CertificateVerify, both new, and Finished. The client sends GET / HTTP/1.1. A checked client gets a reply; a rejected client gets an alert.](handshake.svg)

| Message | From | Contents in the capture |
|---|---|---|
| CertificateRequest | server | The signature algorithms the server accepts, such as `ecdsa_secp256r1_sha256`. It may also list the CAs the server trusts; this server's didn't. |
| Certificate | client | `client.crt`, 426 bytes |
| CertificateVerify | client | A signature with `client.key` over every handshake message so far |

The client's flight grew from a 146-byte frame in plain TLS to 1,102 bytes. Like everything after ServerHello, these messages are encrypted, so an observer can't read the client's certificate or its name. mTLS adds no round trip: with 50 ms of delay added by `tc netem`, the handshake finished at 106–109 ms and the first byte of the reply arrived at 161–163 ms, the same as plain TLS 1.3.

## What the server checks

The server checks the client certificate much as a client checks a server's:

- The chain: each signature verifies up to a CA in the server's trust store for clients.
- The dates: the current time falls inside the certificate's validity.
- The usage: the extended key usage allows client authentication.
- Possession: the client's CertificateVerify verifies with the certificate's public key.

There's no name check. A client connects to a name the user typed, so it knows which name to expect; a server doesn't know who is about to connect. The handshake only proves that a client holds a certificate from a trusted CA. Which clients may do what is the program's decision after the handshake, made from the names in the certificate.

In TLS 1.3, the client finishes its side of the handshake first and sends its request at once, before it learns whether the server accepted it. In a capture of a rejected client, the GET left the client, and the server answered with an alert instead of a reply. curl reported each rejection when it read that alert:

| Client sent | Server's alert | curl's error |
|---|---|---|
| No certificate | `certificate_required` | `tlsv13 alert certificate required` |
| A certificate from Other CA, which the server doesn't trust | `unknown_ca` | `tlsv1 alert unknown ca` |
| A certificate from the lab CA that allows only server authentication | `unsupported_certificate` | `ssl/tls alert unsupported certificate` |
| `client.crt` with a key that isn't its own | none | curl didn't connect: `unable to set private key file` |

The server logged the reason for each: `peer did not return a certificate`, `unable to get local issuer certificate`, and `unsuitable certificate purpose`.

## Identity after the handshake

After a successful handshake, the server holds the client's verified certificate. The `s_server` status page printed it: `Subject: O=lab, CN=client` and `Issuer: CN=Lab Root CA`. A program reads the same fields and decides what the client may do. In Kubernetes, the API server turns them into a user.

## In Kubernetes

The Kubernetes control plane uses mTLS for most of its connections, with certificates from the cluster's own CA, named `kubernetes`. The API server's `--client-ca-file` names the CA it trusts for clients, `/etc/kubernetes/pki/ca.crt` on kind. A client certificate signed by it is a user: the subject's CN is the username, and each O is a group.

![Who shows which certificate in a kind cluster. kubectl, with CN=kubernetes-admin and O=kubeadm:cluster-admins, connects to the API server with mTLS. The API server has apiserver.crt and trusts ca.crt for clients. The kubelet on kind-worker connects to the API server with mTLS as CN=system:node:kind-worker. In the other direction, the API server connects to the kubelet with a client certificate, but by default it doesn't check the kubelet's kubelet.crt, which the kubelet made itself, drawn dashed.](k8s.svg)

The kubeconfig that kind wrote holds a client certificate with the subject `O=kubeadm:cluster-admins, CN=kubernetes-admin`, issued by `CN=kubernetes`, allowing client authentication and valid for one year. The API server read it as a user:

{{< parts >}}
kubectl auth whoami | Show the user the API server authenticated this request as.
{{< /parts >}}

It printed the username `kubernetes-admin`, the groups `kubeadm:cluster-admins` and `system:authenticated`, and a credential ID with the certificate's SHA-256 hash. Each kubelet also connects to the API server with a client certificate. On kind-worker, `/var/lib/kubelet/pki/kubelet-client-current.pem` had the subject `O=system:nodes, CN=system:node:kind-worker`, and the kubelet's `rotateCertificates: true` setting has it request a new one before the old one expires.

The API server also connects to each kubelet, for `kubectl logs` and `kubectl exec`, with its own client certificate, `CN=kube-apiserver-kubelet-client`. That connection is only half checked by default. The kubelet's serving certificate on kind-worker was signed by `kind-worker-ca`, a CA the kubelet created for itself, and the API server has no `--kubelet-certificate-authority` set, so it doesn't verify the kubelet's certificate; the Kubernetes docs call this unsafe on untrusted networks. Kubernetes 1.37 also doesn't support revoking certificates: an issued client certificate works until it expires.

## In a service mesh

A {{< term service-mesh "service mesh" >}} uses mTLS between every pair of pods without changing the applications. In Istio, an agent in each pod creates a private key and a certificate signing request and sends it to `istiod`, whose CA signs it, and the agent rotates the certificate before it expires. The pod's [sidecar]({{< ref "/k8s/sidecar" >}}), an Envoy proxy, takes the certificate and key, and the client pod's sidecar runs an mTLS handshake with the server pod's sidecar. The certificate names the pod's service account as a SPIFFE ID, a URI in the Subject Alternative Name such as `spiffe://cluster.local/ns/default/sa/curl`, so policies allow or deny by service account rather than by IP address. Istio's default mode, PERMISSIVE, accepts both mTLS and plain text.

## In a program

In Go, a server sets `ClientAuth: tls.RequireAndVerifyClientCert` in its `tls.Config` and puts the client CA in `ClientCAs`. Other `ClientAuth` values only request a certificate, or accept one without verifying it. A client loads its certificate and key with `tls.LoadX509KeyPair` and puts them in `Certificates`. In an HTTP handler, `r.TLS.PeerCertificates[0]` is the client's verified certificate, and its `Subject` fields carry the identity.

References: [RFC 8446: TLS 1.3, CertificateRequest](https://www.rfc-editor.org/rfc/rfc8446#section-4.3.2), [RFC 5280: X.509 certificates, extended key usage](https://www.rfc-editor.org/rfc/rfc5280#section-4.2.1.12), [Authenticating, X.509 client certificates (Kubernetes docs)](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#x509-client-certificates), [Communication between nodes and the control plane (Kubernetes docs)](https://kubernetes.io/docs/concepts/architecture/control-plane-node-communication/), [Kubelet TLS bootstrapping (Kubernetes docs)](https://kubernetes.io/docs/reference/access-authn-authz/kubelet-tls-bootstrapping/), [Istio security concepts](https://istio.io/latest/docs/concepts/security/), [SPIFFE X.509-SVID](https://github.com/spiffe/spiffe/blob/main/standards/X509-SVID.md), [openssl-s_server](https://docs.openssl.org/3.5/man1/openssl-s_server/), [Go crypto/tls](https://pkg.go.dev/crypto/tls)
