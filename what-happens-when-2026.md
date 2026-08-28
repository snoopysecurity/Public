# What Happens When You Type `google.com` Into Your Browser and Press Enter? — 2026 Edition

*This is a 2026 rewrite of Alex Gaynor's collaborative **“What happens when…”** project, which tried to answer one simple interview question in ridiculous detail: what actually happens when you type `google.com` into a browser and press Enter?*

The short answer is obvious: the browser gets Google's page and shows it.

But that skips basically everything.

Between pressing Enter and seeing the page, your computer may go through keyboard input, the OS, browser processes, URL parsing, caches, DNS, Wi‑Fi or Ethernet, your router, Internet routing, Google's edge network, TLS, HTTP, HTML, CSS, JavaScript, layout, painting, the GPU, and finally the display.

Also, in 2026, a lot of that may not happen from scratch. The browser might already know the DNS answer. It might already have an HTTP/2 or HTTP/3 connection open. It might resume TLS, use something from cache, or let a service worker answer the request.

So there’sn't one exact sequence that happens every single time.

I'm going to start with a mostly **cold navigation**, where we assume the browser has less useful state to reuse. Then I'll point out the places where a **warm navigation** can skip work.

---

## First, the short version

Before going deep, here is the map.

1. You press Enter.
2. The operating system turns the physical input into an event.
3. The browser's UI receives the event and decides that the address bar contents should be navigated to.
4. The browser interprets `google.com` as a hostname and constructs a URL, normally using HTTPS.
5. Browser security and navigation policies are checked.
6. The browser decides whether an existing page, service worker, cache entry, connection, or DNS result can satisfy part of the navigation.
7. If necessary, the hostname is resolved to one or more IP addresses.
8. The operating system determines how packets should leave the machine and which local next hop should receive them.
9. Packets travel over Wi‑Fi, Ethernet, cellular, a VPN, or another network to a router and then across the Internet.
10. The browser establishes or reuses a transport connection—commonly TCP for HTTP/1.1 or HTTP/2, or QUIC over UDP for HTTP/3.
11. For HTTPS, the client and server authenticate and establish encryption using TLS. With HTTP/3, TLS 1.3 is integrated into QUIC's connection establishment.
12. The browser sends an HTTP request.
13. Google's edge infrastructure accepts the request and routes it to the appropriate service.
14. The server returns an HTTP response, usually compressed.
15. The browser begins processing the response before the entire document has necessarily arrived.
16. HTML becomes a DOM tree; CSS becomes style information; scripts execute; other resources are discovered and fetched.
17. The browser calculates styles and geometry, then paints and rasterizes visual content.
18. Composited layers are handed to the GPU and operating system compositor.
19. The display controller scans out the finished frame.
20. Light from the pixels reaches your eyes.

Now let’s go through it properly.

---

# 1. You press Enter

## The key itself

On a physical keyboard, pressing Enter changes the electrical state of a switch. The exact mechanism depends on the keyboard: mechanical switches, membrane switches, optical switches, capacitive sensing, and laptop scissor mechanisms all detect a press differently.

The keyboard's microcontroller scans its keys and turns the change into an input report. Most modern keyboards present themselves to the computer as a **Human Interface Device**, usually over USB or Bluetooth.

A USB keyboard doesn’t simply shout a character such as `"Enter"` directly into your browser. It reports key state according to the USB HID protocol. The host controller and operating system's input drivers interpret that report and translate it into an operating-system input event.

Bluetooth keyboards follow a different transport path, but the result is similar: the OS eventually receives an event describing a key press.

On a phone or tablet, there might be no physical Enter switch at all. A touch controller reports contact coordinates and other touch data. The operating system's input and UI layers determine that you tapped a key on an on-screen keyboard, and the keyboard software emits the corresponding input action.

The main thing to understand is:

```text
physical input
    ↓
device controller
    ↓
OS input subsystem
    ↓
window / UI event system
    ↓
browser
```

The exact route varies by Windows, macOS, Linux, Android, iOS, the desktop environment, and the input device.

## What the browser receives

Eventually the browser learns that the user activated Enter while the address bar—often called the **omnibox**—has focus.

Modern browsers are multi-process applications. The UI containing tabs, menus, and the address bar generally belongs to a privileged **browser process**, while web pages themselves usually run in less-privileged **renderer processes**. Chromium-based browsers also use dedicated services or processes for work such as networking, GPU operations, storage, audio, and other tasks.

That split matters for stability and security. A web page should not get the same access to your computer that the browser's trusted UI has.

So Enter does more than just act like a normal key here. In the context of the omnibox it means something closer to:

> Commit the current text as a navigation.

---

# 2. The browser decides what `google.com` means

An address bar accepts more than URLs. You can type:

```text
google.com
```

or:

```text
best pizza near me
```

or:

```text
https://google.com/search?q=cats
```

The browser has to decide whether the text represents a URL, a search query, a browser command, or something else.

For `google.com`, this one is easy: the browser treats it as a site you want to open.

## Constructing the URL

You didn’t type a scheme such as `https://`. The browser therefore has to choose how to navigate.

In modern browsers, HTTPS is strongly preferred. Several mechanisms can lead the browser directly to HTTPS, including HTTPS-first behavior, remembered security state, and **HSTS** rules for hosts that require secure transport.

So the browser ends up with something like:

```text
https://google.com/
```

A URL can contain several components:

```text
scheme://userinfo@host:port/path?query#fragment
```

For our simple case:

```text
scheme:   https
host:     google.com
port:     443 implicitly
path:     /
```

The fragment isn’t sent to the server as part of an HTTP request. It is interpreted by the client.

## Internationalized hostnames

Domain names aren’t limited to ordinary ASCII letters in what users see. Internationalized domain names can contain Unicode characters, but DNS ultimately uses an ASCII-compatible encoding for those labels, generally via the IDNA rules and Punycode representation where required.

`google.com` doesn’t need that conversion, but a complete URL parser has to handle the possibility.

## The browser also canonicalizes the input

Before a request is sent, the browser parses and canonicalizes the URL. Among other things it must distinguish the scheme, hostname, port, path, query, credentials if present, percent-encoded characters, and invalid or dangerous forms.

URL parsing sounds boring, but browsers have to make old links, malformed input, Unicode, and security rules all behave consistently. That makes it a lot less simple than it looks.

---

# 3. Navigation begins inside the browser

A modern browser doesn’t immediately open a socket the second you press Enter. First it determines how the navigation should be handled.

Depending on the browser and situation, it may check or coordinate:

- navigation and security policy;
- whether the target should open in the current tab or another browsing context;
- existing renderer processes and site-isolation rules;
- browser extensions that are allowed to observe or modify navigation;
- service workers associated with the origin;
- memory and disk caches;
- cookies and site storage;
- proxy configuration;
- VPN or operating-system network configuration;
- existing connections to the same origin or a compatible server;
- cached DNS results;
- speculative work the browser may already have performed.

Some work may have happened before you pressed Enter. While you were typing, the browser may have predicted the likely destination and performed **DNS prefetching**, **preconnects**, or other speculative loading, depending on settings, browser policy, privacy mode, and confidence.

So sometimes the page feels fast because the browser started useful work before you even pressed Enter.

---

# 4. Before DNS: can the browser avoid the network entirely?

The simplified version of web browsing is:

```text
URL → DNS → connection → HTTP → page
```

Real browsers first check whether they can skip some of that work.

## Browser caches

Browsers maintain several kinds of cached state. A resource may already exist in memory or on disk. HTTP cache metadata can tell the browser whether a cached representation is still fresh or whether it needs validation with the server.

A fresh cached resource may require no network transfer at all.

A stale cached resource might be revalidated using conditional request headers such as:

```http
If-None-Match: "some-etag"
```

or:

```http
If-Modified-Since: ...
```

If the server says the representation hasn’t changed, it can answer with:

```http
304 Not Modified
```

and omit the full response body.

## Service workers

A service worker can sit logically between a web application and the network. If a service worker controls the page, it may receive a `fetch` event for a navigation or subresource and decide how to answer it.

It might:

- return a cached response immediately;
- fetch from the network;
- combine cached and network data;
- provide an offline page;
- implement an application-specific caching strategy.

For a first visit to `google.com`, there might be no controlling service worker for that origin. But for the general question “what happens when you enter a URL?”, service workers are too important to omit.

## Existing connections

The browser may already have a live connection that can be reused.

With HTTP/2 and HTTP/3, many requests can share one connection using independent streams. That means the browser often does **not** need to create a fresh transport connection for every resource.

Connection reuse can remove entire round trips from the critical path.

For the cold-path version, assume none of those shortcuts help us.

Now we actually need an IP address.

---

# 5. DNS: turning `google.com` into an address

We type names like `google.com`, but the network needs IP addresses.

The Domain Name System answers questions such as:

> Which IP addresses can I use to reach `google.com`?

The answer can include IPv4 addresses, IPv6 addresses, aliases, and other DNS records.

## There isn’t just one DNS cache

Before sending a DNS query onto the network, several layers may already know the answer:

1. the browser's own DNS or host cache;
2. an operating-system resolver cache;
3. a local network resolver, such as one on the router;
4. an enterprise resolver;
5. an ISP resolver;
6. a public recursive resolver;
7. an encrypted-DNS provider chosen by the browser or operating system.

The exact ordering varies by platform and browser.

## The hosts file

Operating systems also provide a local hosts file that can map names to IP addresses without ordinary DNS resolution.

For example, a developer might map:

```text
127.0.0.1 example.test
```

The details of how the OS resolver combines local files, caches, mDNS, enterprise policy, and DNS are platform-specific.

## Stub resolver and recursive resolver

If the answer isn’t already known, the client usually sends the question to a **recursive resolver**.

The resolver may be:

- supplied by the local network;
- operated by an ISP;
- operated by an organization;
- a public resolver;
- reached through DNS over HTTPS (DoH), DNS over TLS (DoT), or another encrypted mechanism.

The client generally doesn’t walk the entire DNS hierarchy itself. The recursive resolver does that work if it doesn’t already have a cached answer.

## What the recursive resolver may do

Suppose it needs to resolve `google.com` from scratch.

At a high level it can ask:

```text
root DNS servers
    ↓
.com TLD servers
    ↓
authoritative servers for google.com
    ↓
answer
```

The root server doesn’t need to know Google's final IP address. It can direct the resolver toward the `.com` name servers.

The `.com` servers can direct it toward the authoritative servers for `google.com`.

An authoritative server can then provide the relevant answer or delegation information.

In practice, caching makes a truly from-scratch lookup uncommon. Resolvers cache records according to their TTLs, so many steps can disappear.

## A and AAAA records

The browser may receive both:

- an **A** record for IPv4;
- an **AAAA** record for IPv6.

Modern clients often have logic designed to avoid getting stuck if one address family or one route is slow. Rather than treating IPv4 and IPv6 as completely separate worlds, the client can race or stagger attempts and use the connection that succeeds efficiently.

## DNS isn’t necessarily UDP port 53 anymore

Classic DNS commonly uses UDP port 53, with TCP available when needed. That still exists.

But a 2026 explanation also has to account for encrypted DNS. A browser or OS may send DNS inside HTTPS or TLS rather than exposing a traditional plaintext DNS query directly to the local network.

The important outcome is the same: the browser ends up with candidate network endpoints for the origin.

---

# 6. The operating system decides where packets should go

Suppose DNS gives the browser a usable destination address.

The browser doesn’t itself toggle Wi‑Fi radio waves or Ethernet voltages. It asks the operating system's networking stack to communicate with the destination.

The OS consults its **routing table**.

The routing decision answers a question like:

> For this destination IP address, which network interface and next hop should I use?

The answer may point to:

- Wi‑Fi;
- Ethernet;
- cellular data;
- a VPN tunnel;
- a virtual interface;
- a local route;
- the default gateway.

## The next hop is what matters locally

At the local link layer, your computer usually doesn’t need Google's MAC address. MAC addresses are relevant only on the local link.

If Google is somewhere across the Internet, your machine normally needs the link-layer address of the **next hop**, often your router or another local gateway.

For IPv4, that mapping is commonly learned with **ARP**.

For IPv6, the equivalent job is handled by the **Neighbor Discovery Protocol**, which is part of ICMPv6.

The result is roughly:

```text
destination IP: remote Google endpoint
next-hop IP:    local router
next-hop MAC:   router's interface on this LAN
```

## IPv4 ARP in brief

If the required IPv4 next-hop mapping isn’t cached, the machine can broadcast an ARP request on the local network:

```text
Who has 192.168.1.1?
Tell 192.168.1.42.
```

The router responds with its link-layer address, and the OS caches the mapping for a period of time.

## IPv6 Neighbor Discovery

IPv6 doesn’t use ARP. Neighbor Discovery uses ICMPv6 messages and IPv6 multicast to discover neighbors and routers and to maintain reachability information.

## Wi‑Fi makes this a little messier

On Wi‑Fi, frames must be transmitted over a shared radio medium. The client and access point coordinate according to 802.11 rules. Encryption such as WPA2 or WPA3 protects the local wireless link when configured.

Local Wi‑Fi encryption and HTTPS solve different problems:

- Wi‑Fi encryption protects traffic over the local wireless link.
- TLS protects application traffic end-to-end between the client and the TLS endpoint, even after packets leave your local Wi‑Fi network.

---

# 7. Your router, NAT, firewall, VPN, and ISP may all get involved

A typical home network uses private IPv4 addresses internally. Your laptop might have something like:

```text
192.168.1.42
```

That address isn’t globally routable on the public Internet.

## NAT

The home router may perform **Network Address Translation**. It rewrites the source address—and commonly the source port—so many devices can share one public IPv4 address.

It keeps state so that returning packets can be mapped back to the correct internal device and connection.

IPv6 can reduce the need for this style of address sharing, although firewalls and other policy layers still exist.

## Stateful firewalling

The device itself, the router, a corporate gateway, or a cloud security product may enforce firewall rules. Outbound web traffic is normally allowed, but the network stack still passes through these policy systems.

## VPNs

If you are using a VPN, the apparent route can change dramatically.

Instead of sending a packet toward Google directly through the ordinary route, the OS may first encapsulate it inside an encrypted tunnel to a VPN server:

```text
your device
   ↓ encrypted tunnel
VPN server
   ↓
Internet
   ↓
Google
```

From Google's perspective, the apparent source network might be the VPN provider rather than your home ISP.

## Proxies

Enterprise and managed devices can also use HTTP proxies or security gateways. In those environments, the browser may connect to an intermediary that forwards requests according to policy.

Again: there’s no single universal path.

---

# 8. Packets cross the Internet

Once traffic leaves your local network, it moves through routers operated by Internet service providers, transit networks, Internet exchange participants, content networks, and other autonomous systems.

Routers don’t carry a complete narrative of your browsing session. At the IP layer, their core job is much simpler: inspect the destination address, consult forwarding state, and choose the next hop.

## BGP is how networks decide where traffic goes

Large networks on the Internet are organized into **Autonomous Systems** (ASes). The Border Gateway Protocol, or **BGP**, is used between networks to advertise reachability and select inter-domain routes according to routing policy.

Your packets might therefore travel through multiple networks before reaching Google's infrastructure.

The route can change due to:

- geography;
- peering relationships;
- congestion;
- outages;
- traffic engineering;
- anycast routing;
- network policy.

## Anycast and edge infrastructure

Large Internet services don’t usually mean “one server in one building.” A hostname may lead you toward an edge location selected by DNS, anycast, load balancing, or some combination of techniques.

The machine that first accepts your packets might be a nearby edge system, reverse proxy, or load balancer rather than the application server that ultimately produces the response.

That distinction becomes important when we get to Google's side of the connection.

---

# 9. TCP or QUIC?

Now the browser needs a transport mechanism for HTTP.

In 2026, the important common cases are:

```text
HTTP/1.1 → usually TCP → TLS for HTTPS
HTTP/2   → usually TCP → TLS for HTTPS
HTTP/3   → QUIC over UDP, with TLS 1.3 integrated
```

The browser may already know that the origin supports HTTP/3 from previous interactions or protocol advertisement. Otherwise it may begin with another supported route and learn about HTTP/3 availability.

The exact connection strategy is deliberately implementation-dependent and changes over time.

## If the browser uses TCP

If the browser uses TCP, the operating system creates a TCP connection to the server's IP address and destination port, normally 443 for HTTPS.

A new TCP connection traditionally begins with the three-way handshake:

```text
Client → Server: SYN
Server → Client: SYN + ACK
Client → Server: ACK
```

This establishes sequence-number state and confirms that both endpoints can communicate.

TCP then provides applications with a reliable ordered byte stream. It handles retransmission, acknowledgements, flow control, and congestion control.

## Congestion control

The sender can’t simply blast data onto the Internet as fast as the network card permits. Transport protocols adapt how much data they put in flight based on network conditions.

Modern congestion-control algorithms attempt to use available capacity without causing persistent congestion. The exact algorithm depends on the operating system, server, transport implementation, and network environment.

Packet loss, delay, and acknowledgements influence sending behavior.

## If the browser uses QUIC and HTTP/3

HTTP/3 maps HTTP semantics onto **QUIC**, which runs over UDP.

Calling QUIC “just UDP” is misleading. UDP provides the packet delivery substrate, while QUIC implements features applications previously relied on TCP and TLS to provide, including:

- reliable delivery within streams;
- congestion control;
- flow control;
- connection establishment;
- encryption using TLS 1.3;
- multiplexed streams;
- connection migration capabilities.

One of QUIC's important design benefits is that independent streams don’t suffer from TCP's connection-wide head-of-line blocking when one packet belonging to another stream is lost.

QUIC also allows transport and cryptographic setup to be coordinated tightly, reducing connection-establishment overhead in common cases.

---

# 10. TLS 1.3: proving it’s really the server and encrypting the connection

Typing `https://` doesn’t merely mean “encrypt the bytes somehow.” The browser must establish cryptographic keys and authenticate the server.

Modern HTTPS normally uses **TLS**, with TLS 1.3 being the current protocol generation for modern deployments.

For HTTP/1.1 or HTTP/2 over TCP, TLS sits above TCP.

For HTTP/3, TLS 1.3 is used as part of QUIC's handshake rather than appearing as a separate TLS record layer running over TCP.

## The simplified TLS 1.3 version

A fresh TLS 1.3 handshake looks conceptually like this:

```text
Client                               Server
  |                                    |
  | ---- ClientHello ----------------> |
  |                                    |
  | <--- ServerHello ----------------- |
  | <--- encrypted handshake data ---- |
  | <--- certificate/authentication -- |
  | <--- Finished -------------------- |
  |                                    |
  | ---- Finished -------------------> |
  |                                    |
  | ===== encrypted application ====== |
```

The details are more complicated, but several important things happen.

## ClientHello

The browser sends a `ClientHello` containing cryptographic capabilities and parameters needed to establish the connection. This can include supported TLS versions, cipher suites, key-share information, protocol negotiation information such as ALPN, and other extensions.

## ServerHello and key agreement

The server selects compatible parameters and sends its response. Modern TLS 1.3 normally uses ephemeral Diffie–Hellman-style key agreement, commonly based on elliptic curves.

The client and server derive shared secrets without sending the final symmetric traffic keys across the network.

That is an important improvement over old explanations of TLS that describe the browser generating a random symmetric key and encrypting it directly with the server's RSA public key. That model describes older TLS handshakes, not the normal TLS 1.3 story.

## The certificate

The server provides certificate information allowing the browser to authenticate the server's identity.

The browser checks things such as:

- whether the certificate is valid for the requested hostname;
- whether the validity period is acceptable;
- whether the signature chain leads to a trusted certificate authority;
- whether relevant certificate and security policies are satisfied.

Certificate verification is its own deep subject. Browsers and operating systems maintain trust stores and apply additional policy around certificate validity and revocation information.

## Symmetric encryption

Public-key cryptography is useful for authentication and key agreement, but bulk web traffic is protected using efficient symmetric authenticated encryption.

Once the handshake keys are established, HTTP data can be encrypted and integrity-protected.

Someone observing the network can still learn some metadata—such as IP addresses and traffic timing—but they should not be able to simply read the HTTP page contents protected inside the TLS connection.

## Session resumption

On a later visit, the browser might be able to resume previous TLS state rather than repeating the entire cost of a completely fresh handshake.

That is another reason a warm navigation can look very different from the cold path described here.

---

# 11. The browser decides which HTTP version to use

During connection setup, client and server can negotiate an application protocol.

For HTTPS over TCP, ALPN can allow them to agree on a protocol such as HTTP/2 or HTTP/1.1.

HTTP/3 runs over QUIC and is negotiated in that context.

The main point is that **HTTP isn’t synonymous with one wire format**.

The semantics—methods, headers, status codes, requests, responses, caching rules—are shared across modern HTTP versions, while their framing and transport behavior differ.

---

# 12. The HTTP request is sent

Conceptually, the browser wants to say:

> Give me the resource at `/` for `google.com`, using the context and capabilities represented by these request headers.

An HTTP/1.1 request is human-readable enough to illustrate:

```http
GET / HTTP/1.1
Host: google.com
User-Agent: ...
Accept: ...
Accept-Encoding: gzip, br, zstd, ...
Accept-Language: ...
Cookie: ...
...
```

Actual headers depend on browser, privacy settings, current standards, site state, and request context. Modern browsers also try to reduce unnecessary identifying information compared with older user-agent behavior.

HTTP/2 and HTTP/3 don’t send the request using exactly that textual representation, but the logical request has similar semantics.

## Cookies

If cookies applicable to the request exist and policy permits them to be sent, they can accompany the request.

Cookie inclusion depends on attributes and browser rules involving domain, path, security, same-site context, partitioning, expiration, and privacy policy.

Cookies aren’t automatically “all cookies for every site.” The browser carefully selects which stored values are relevant and permitted.

## Request headers

Headers can communicate things such as:

- acceptable content types;
- preferred language;
- supported compression;
- cache validators;
- referrer information when applicable;
- fetch metadata;
- cookies;
- client hints when allowed;
- range requests;
- authentication credentials in relevant cases.

The request is then encoded according to the selected HTTP version and carried over the established transport.

---

# 13. What Google does with the request

A common old explanation says something like:

> Apache or nginx receives the request, finds the index file, maybe executes PHP, and returns the HTML.

That can describe a small traditional website, but it’sn’t a useful model for a service the size of Google.

At Internet scale, think in layers.

A simplified path might look like:

```text
Internet
   ↓
Google edge / frontend
   ↓
TLS / QUIC termination and traffic management
   ↓
request routing / load balancing
   ↓
application services
   ↓
caches, indexes, storage, internal services
   ↓
response generation
```

The exact internal design is proprietary, changes over time, and is far more complex than this article can observe from the outside. The important architectural point is that the public endpoint isn’t necessarily the program that constructs every byte of the page.

## Edge infrastructure

Large providers operate globally distributed infrastructure. The edge can:

- terminate client connections;
- enforce security policy;
- mitigate attacks;
- route requests;
- serve cached or static content;
- forward application requests to internal systems;
- compress responses;
- manage connection reuse.

## Load balancing

The visible hostname represents a service, not one permanent machine.

Traffic can be distributed based on health, capacity, geography, latency, shard ownership, deployment state, and many other signals.

If one machine fails, the service should continue functioning without requiring users to learn a different URL.

## Application logic

For the Google homepage, backend systems decide what response should be generated for the request. The exact result can depend on many legitimate inputs, such as language, region, authentication state, experiments, device capabilities, and account settings.

The response might be assembled from templates, static resources, cached fragments, service calls, configuration, and user-specific state.

The main point is that the neat boundary called “the server” often hides a large distributed system.

---

# 14. The server sends an HTTP response

An HTTP response contains a status plus headers and, often, a body.

In HTTP/1.1-style notation, it might resemble:

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Encoding: br
Cache-Control: ...
Set-Cookie: ...
Content-Security-Policy: ...
...

<!doctype html>
<html>...</html>
```

The exact Google response varies and should not be treated as fixed.

## Status codes

`200 OK` is only one possibility.

The server could also return or trigger behavior involving:

- `301` or `308` permanent redirects;
- `302`, `303`, or `307` redirects;
- `304 Not Modified` for cache validation;
- `401` or `403` authorization-related responses;
- `404 Not Found`;
- `429 Too Many Requests`;
- `5xx` server errors.

For our simple successful navigation, assume a `200` response containing HTML.

## Compression

Textual web resources compress extremely well. The browser advertises supported content encodings, and the server may compress HTML, CSS, JavaScript, JSON, and other suitable content.

The browser decompresses the bytes before the higher-level parser consumes them.

Compression saves bandwidth but costs CPU time, so servers and clients balance size and processing cost.

## Streaming matters

The browser doesn’t necessarily wait for the final byte of the HTML document before doing anything.

As response bytes arrive, the networking stack can feed them toward the renderer. Parsing and resource discovery can overlap with continued network transfer.

This overlap is one of the central reasons the modern browser loading pipeline should not be imagined as a strict sequence of:

```text
download everything
then parse everything
then load CSS
then load JavaScript
then draw
```

Many stages run concurrently.

---

# 15. The response moves through the browser

In a multi-process browser, the network-facing code and the code responsible for executing a web page don’t necessarily live in the same process.

In Chromium's architecture, for example, renderer processes are sandboxed and network access is mediated by more privileged browser/network components.

Conceptually:

```text
network
   ↓
network service / browser-controlled networking
   ↓
validated response stream
   ↓
renderer process for the site
```

This separation makes it harder for a compromised web renderer to directly use arbitrary operating-system resources.

The browser must also decide which renderer process should host the new document. Site isolation can place documents from different sites into different renderer processes, including cross-site frames embedded inside a page.

---

# 16. The browser turns bytes into text

The HTML parser can’t operate on arbitrary compressed network bytes.

Before parsing, the browser works through layers such as:

```text
transport packets
    ↓
encrypted protocol data
    ↓
TLS/QUIC decryption
    ↓
HTTP framing
    ↓
content decompression
    ↓
byte stream
    ↓
character decoding
    ↓
HTML tokenizer/parser
```

The response's declared encoding, HTTP headers, BOMs where applicable, HTML rules, and browser behavior determine how bytes become text.

For modern HTML, UTF‑8 is overwhelmingly the expected encoding, but browsers still contain compatibility logic for the wider web.

---

# 17. HTML gets turned into the DOM

The browser's HTML parser processes the incoming character stream.

At a simplified level:

```text
characters
   ↓
tokenization
   ↓
tree construction
   ↓
DOM
```

The **Document Object Model**, or DOM, is the browser's in-memory representation of the document's node structure.

Given:

```html
<body>
  <h1>Hello</h1>
</body>
```

the browser creates nodes representing the document, `html`, `body`, `h1`, and the text `Hello`.

## HTML is deliberately forgiving

Web browsers don’t parse HTML the same way a strict compiler parses a programming language.

Real web pages contain malformed nesting, omitted tags, historic quirks, and patterns that browsers have supported for decades. The HTML parsing algorithm defines how browsers recover from many forms of invalid markup so that pages still produce a DOM.

This error recovery is standardized behavior, not simply a browser deciding to “do its best” at random.

---

# 18. The browser starts finding other files early

If the main HTML parser were the only component discovering subresources, loading would be unnecessarily slow.

Modern browsers can scan ahead through incoming markup and identify resources that are likely to be needed, such as:

```html
<link rel="stylesheet" href="/styles.css">
<script src="/app.js"></script>
<img src="/logo.webp">
<link rel="preload" href="/font.woff2" as="font">
```

This allows network requests to begin while the main HTML parser is still working.

That is why a more accurate mental model is:

```text
HTML arrives ────────────────►
   │
   ├─ parser builds DOM ─────►
   │
   ├─ scanner discovers CSS ─► network
   ├─ scanner discovers JS ──► network
   ├─ scanner discovers img ─► network
   └─ scanner discovers font ► network
```

The browser is a pipeline, not a checklist.

---

# 19. CSS gets downloaded and parsed

CSS resources are downloaded, decoded, and parsed into internal structures representing stylesheets and rules.

For example:

```css
button.primary {
  font-weight: 600;
  padding: 0.75rem 1rem;
}
```

is turned into data the style engine can efficiently match against DOM elements.

The browser combines rules from several sources, including:

- user-agent stylesheets;
- author stylesheets;
- `<style>` blocks;
- inline `style` attributes;
- inherited properties;
- cascade layers and specificity;
- media queries;
- user preferences and accessibility settings.

The end result isn’t simply “the CSSOM plus DOM equals pixels.” The style system must determine the **computed style** applicable to each relevant element under the cascade.

## CSS can block rendering

Stylesheets are often render-blocking because drawing the page before required CSS is available could create a flash of incorrect layout and styling.

Browsers aggressively optimize this process, but CSS on the critical rendering path can still affect how soon meaningful content appears.

---

# 20. JavaScript can interrupt all of this

JavaScript isn’t just another static resource.

A script can:

- inspect or modify the DOM;
- change styles;
- register event handlers;
- start network requests;
- create workers;
- read or write storage where permitted;
- schedule timers;
- trigger animations;
- cause new layout or paint work;
- import additional modules;
- interact with browser APIs.

## Parser-blocking scripts

A classic script such as:

```html
<script src="app.js"></script>
```

can block the HTML parser while the script is fetched and executed, because the script may call APIs such as `document.write()` or otherwise depend on the exact parser state.

## `defer`

A deferred script can be fetched while HTML parsing continues and is executed after the document has been parsed, with ordering semantics defined for deferred scripts.

```html
<script defer src="app.js"></script>
```

## `async`

An async script downloads independently and executes when ready, without preserving normal parser ordering relative to other async scripts.

```html
<script async src="analytics.js"></script>
```

## JavaScript modules

ES modules add their own loading graph and execution rules:

```html
<script type="module" src="main.js"></script>
```

`main.js` can import additional modules, which creates a dependency graph that the browser resolves and fetches.

---

# 21. Now a lot more requests start happening

The original HTML is often only the beginning.

A modern page may request:

- CSS;
- JavaScript;
- fonts;
- images;
- icons;
- video;
- API data;
- analytics endpoints;
- ads;
- maps;
- embedded frames;
- module dependencies.

Each resource has its own URL and caching rules.

Resources hosted on a different origin may require additional DNS resolution, a new connection, another TLS context, CORS processing, or different credentials.

Resources on the same origin can often reuse an HTTP/2 or HTTP/3 connection.

## Priorities

Not all resources matter equally to the first visible frame.

Browsers assign and adjust priorities so that critical resources—such as the main document, render-blocking CSS, and important fonts or images—can compete differently from less urgent work.

Servers and protocols can also participate in scheduling, though the exact algorithms vary between browser versions.

---

# 22. Security checks keep happening while the page loads

Modern browsers enforce many security boundaries while loading a page.

These can include:

- Same-Origin Policy;
- CORS;
- Content Security Policy;
- mixed-content restrictions;
- cookie security rules;
- permissions policy;
- sandboxed iframe restrictions;
- cross-origin isolation mechanisms;
- download and navigation protections;
- certificate policy;
- malware/phishing defenses depending on browser configuration.

These aren’t one single “security check” performed at the beginning. Security policy is woven throughout the navigation, networking, parsing, scripting, and process-isolation architecture.

---

# 23. The browser figures out the final styles

Once the browser has DOM nodes and applicable style information, it determines the computed styles required for rendering.

Conceptually:

```text
DOM + CSS rules + environment
             ↓
      computed styles
```

The environment includes things such as viewport dimensions, device pixel ratio, user settings, media queries, font availability, color scheme, and more.

A change to a class name, viewport size, stylesheet, or inherited property can require style recalculation for some portion of the document.

Browsers therefore maintain dependency information and caches so they don’t recompute the entire world after every minor change.

---

# 24. Layout: figuring out where everything goes

Knowing that a paragraph has `font-size: 16px` isn’t enough to draw it.

The browser has to determine geometry:

- width;
- height;
- x/y position;
- line breaks;
- scrollable overflow;
- table sizing;
- grid and flex layout;
- absolute and fixed positioning;
- transformed coordinate systems;
- intrinsic image dimensions;
- font metrics.

This stage is generally called **layout**.

For a block of text, layout depends on the selected font, glyph metrics, available width, word-breaking rules, line height, and neighboring content.

A tiny change can sometimes affect a large region. For example, changing the width of a container can change line wrapping, which changes the container's height, which moves everything below it.

Browsers work hard to limit layout recalculation to the regions that actually need it.

---

# 25. Fonts are another thing the browser has to wait on

Text can’t be laid out perfectly without knowing font metrics.

If the page references a web font, the browser may initially have to choose between waiting, drawing with a fallback font, or following behavior specified through mechanisms such as `font-display`.

When the desired font arrives, text can change width and height, causing additional layout.

This is one source of **layout shift**—content visibly moving after the page first appears.

Performance-minded sites try to minimize unnecessary shifts because they are distracting and make interfaces harder to use.

---

# 26. Paint: turning the page into drawing instructions

After layout establishes geometry, the browser determines what needs to be painted.

Painting doesn’t yet necessarily mean “set this physical pixel to blue.” It means generating drawing operations for visual effects such as:

- backgrounds;
- borders;
- text;
- shadows;
- images;
- gradients;
- outlines;
- clipping.

The browser also has to respect stacking order, transparency, clipping, transforms, and effects.

Conceptually:

```text
layout objects
    ↓
paint records / display items
```

The exact internal representation differs by rendering engine.

---

# 27. Layers and compositing

Some parts of a page are useful to treat as independent composited surfaces.

For example, elements involved in transforms, video, scrolling, certain animations, or other effects might be placed into compositing layers according to the browser's heuristics and rendering architecture.

Layering can make some updates cheaper. If an element moves using a compositor-friendly transform, the browser might be able to reposition an existing rasterized layer rather than repainting a large part of the page.

But “more layers” isn’t automatically better. Layers consume memory and management overhead, so the engine decides when they are worthwhile.

---

# 28. Rasterization: drawing into pixels

Paint instructions eventually have to become pixel data.

This process is **rasterization**.

Modern browsers often divide content into tiles and rasterize the pieces needed for the current and near-future viewport. Raster work can use CPU resources and GPU acceleration depending on the platform, content, and rendering path.

The browser doesn’t necessarily rasterize every pixel of a 50,000-pixel-tall page immediately. Doing so would waste time and memory for content the user may never scroll to.

Instead, engines prioritize visible and soon-to-be-visible content.

---

# 29. The GPU and compositor put the frame together

Modern browsers use a GPU-related process or service to help rasterize and composite visual content while maintaining security isolation between untrusted page code and privileged graphics interfaces.

The compositor combines the relevant page surfaces, browser UI, embedded content, scrolling state, and effects into a frame.

Very roughly:

```text
DOM / CSS / JS
      ↓
style
      ↓
layout
      ↓
paint
      ↓
raster
      ↓
composite
      ↓
GPU / display system
```

This diagram is useful, but real rendering is incremental. A page doesn’t run through the whole pipeline once and stop. Scrolling, animations, network responses, user input, JavaScript, images decoding, fonts arriving, and DOM mutations can trigger portions of the pipeline repeatedly.

---

# 30. The OS compositor puts the browser window on screen

The browser isn’t the only thing drawing on your screen.

Your operating system has a window compositor that combines visible application surfaces—the browser, desktop, taskbar or dock, notifications, other windows, cursor, and system UI—into the final desktop image.

Depending on the platform, technologies such as DirectComposition/Direct3D, Core Animation/Metal, Wayland compositors, or other graphics stacks may participate.

The exact implementation changes by OS and hardware.

The browser ultimately hands off surfaces or buffers through platform graphics APIs, and the operating system coordinates their presentation.

---

# 31. The display finally shows the frame

At some point, the final frame exists in a buffer suitable for presentation.

The display controller reads pixel data and sends it to the physical display according to the display link and refresh timing.

On an LCD or OLED panel, the electronics drive individual pixels or subpixels to emit or modulate light.

At 60 Hz, a display refreshes roughly every 16.7 milliseconds. At 120 Hz, the interval is roughly 8.3 milliseconds. Variable-refresh-rate displays can alter timing within supported ranges.

If a newly rendered frame misses the appropriate presentation deadline, the old frame may remain visible for another refresh interval, which the user can perceive as jank or stutter.

And after all of the software, cryptography, distributed systems, radio communication, routing, parsing, layout, and graphics work, the final step is almost embarrassingly physical:

**photons leave the display and enter your eyes.**

---

# 32. But the page still isn’t really “finished”

The moment the first useful frame appears isn’t the end of the story.

JavaScript may continue running. Images may still decode. Fonts may arrive. API requests may return. Analytics may fire. Ads or embedded widgets may load. Service workers may update caches. Animations may run. The user may scroll or type.

A web page is better thought of as a live program than a static document download.

## `DOMContentLoaded`

The browser fires `DOMContentLoaded` after the initial HTML document has been completely parsed and deferred/module script conditions have been satisfied according to the platform rules.

That does **not** mean every image or other subresource has necessarily finished loading.

## `load`

The window's `load` event occurs later, after the document and its dependent resources covered by the event's rules have loaded.

Even then, the application may immediately start more work.

## The event loop keeps going

The renderer continues processing tasks, microtasks, rendering updates, network callbacks, timers, input, and other events.

The page remains alive until it’s closed, navigated away from, frozen, discarded, crashed, or otherwise terminated.

---

# 33. What gets skipped on a warm navigation?

Everything above sounds expensive because we deliberately described a mostly cold path.

On a repeat visit, the browser may skip or shorten much of it.

A warm navigation might look more like:

```text
Enter
  ↓
URL recognized
  ↓
DNS answer already cached
  ↓
HTTP/3 connection still alive
  ↓
TLS/QUIC state already established
  ↓
request sent immediately on new stream
  ↓
HTML validated or returned
  ↓
CSS / JS / images served partly from cache
  ↓
render
```

Or a service worker might satisfy important resources without going to the network at all.

Or the browser might have speculatively connected before you pressed Enter.

That’s why network waterfalls and performance traces are more informative than memorizing one rigid sequence.

---

# 34. What if something fails?

The “happy path” is only one possibility.

## DNS failure

If name resolution fails, the browser can’t reach an endpoint by the requested hostname and shows an error page.

## No route or connectivity

The machine may have Wi‑Fi but no working Internet route, a captive portal, a broken VPN, or a firewall blocking traffic.

## Connection failure

TCP or QUIC establishment can fail because of packet loss, filtering, server availability, path problems, or timeouts.

The browser may retry another IP address, another protocol, or another network path depending on implementation.

## TLS failure

If the server certificate is invalid, the hostname doesn’t match, cryptographic negotiation fails, or policy rejects the connection, the browser can block the navigation and display a security warning or error.

## HTTP redirect

The server may respond with a redirect, sending the browser through another navigation cycle to a new URL.

## Server error

The service may respond with an HTTP error status or fail to respond in time.

## Renderer crash

The network may succeed but the renderer process can still crash due to a bug, resource exhaustion, or another failure. Multi-process architecture limits the blast radius so one tab doesn’t necessarily destroy the entire browser.

---

# 35. Where privacy features come into it

A 2026 browser also makes privacy decisions throughout the path.

Depending on browser, settings, jurisdiction, enterprise policy, and user choices, features may affect:

- third-party cookies;
- storage partitioning;
- referrer information;
- tracking protection;
- fingerprinting surfaces;
- DNS behavior;
- preloading and speculation;
- IP-address exposure in some APIs;
- permission prompts;
- extension access.

Private or incognito browsing also changes what is persisted and reused, although it doesn’t make the user anonymous to websites, networks, employers, schools, ISPs, or VPN providers.

Privacy is therefore another cross-cutting concern, like security—not a single isolated step.

---

# 36. The whole thing, as a 2026 mental model

If you remember only one thing from this article, remember that modern navigation is **concurrent, cached, speculative, encrypted, multi-process, and distributed**.

The old classroom story is:

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
HTTP
 ↓
HTML
 ↓
CSS
 ↓
JavaScript
 ↓
render
```

That sequence is useful as a first approximation, but it’s too linear.

A better picture looks like this:

```text
                         ┌──────── browser cache ────────┐
                         │                               │
user input → navigation ─┼→ service worker? ────────────┼────┐
                         │                               │    │
                         ├→ DNS/cache/speculation ──────┤    │
                         │                               │    │
                         └→ connection pool ─────────────┘    │
                                                             ▼
                         TCP + TLS ─┐                    HTTP request
                                     ├→ HTTP/1.1 or 2 ────┤
                         QUIC + TLS ─┘                    │
                              └────────→ HTTP/3 ──────────┘
                                                             │
                                                             ▼
                                                    edge / backend
                                                             │
                                                             ▼
                                                     HTTP response
                                                             │
                       ┌─────────────────────────────────────┼────────────┐
                       ▼                                     ▼            ▼
                  HTML parser                         preload scanner   cache
                       │                                     │
                       ▼                                     ├→ CSS
                      DOM                                    ├→ JS
                       │                                     ├→ fonts
                       │                                     └→ images
                       │
                  style calculation
                       │
                     layout
                       │
                     paint
                       │
                    raster
                       │
                   composite
                       │
                      GPU
                       │
                  OS compositor
                       │
                     display
```

And all the while, JavaScript, networking, user input, timers, workers, and rendering can continue to influence one another.

---

# 37. The version I’d give in an interview

If someone asked me this in an interview, I wouldn’t start talking about USB packets or BGP straight away. I’d give the shape of the answer first:

> You press Enter, the browser parses the URL and checks whether it can reuse anything from cache, DNS, a service worker, or an existing connection. If it needs the network, it resolves the hostname, connects using TCP or QUIC, establishes TLS for HTTPS, sends an HTTP request, and gets a response. The browser parses the HTML, fetches the CSS, JavaScript, images, fonts, and other resources it needs, then calculates styles and layout, paints the page, rasterizes it, composites the final frame, and sends it to the display. Modern browsers do a lot of this in parallel and can skip a bunch of steps when state is already cached or a connection is reusable.

Then I’d go deeper depending on what the interviewer actually cares about. If they’re asking a networking question, talk about DNS, routing, TCP/QUIC, TLS, and HTTP. If it’s a browser question, go into processes, parsing, JavaScript, layout, paint, and compositing.

The point isn’t to memorize one giant sequence. It’s to understand the layers well enough that you can zoom in when someone asks.

---

# 38. The deeper checklist

For anyone using this topic to study systems, here is the full chain grouped by discipline.

## Input and operating systems

- keyboard matrix or touch sensor;
- USB HID or Bluetooth HID;
- device driver;
- kernel input subsystem;
- window system;
- browser UI event handling.

## Browser navigation

- omnibox interpretation;
- URL parsing and canonicalization;
- HTTPS/HSTS/security policy;
- browsing context selection;
- site isolation;
- extension hooks;
- service worker checks;
- HTTP cache;
- speculative loading.

## Naming

- browser host cache;
- OS resolver;
- hosts file and local naming rules;
- recursive DNS resolver;
- DoH/DoT or traditional DNS;
- root/TLD/authoritative DNS on cache misses;
- A and AAAA results.

## Local networking

- routing table;
- interface selection;
- ARP for IPv4;
- Neighbor Discovery for IPv6;
- Wi‑Fi/Ethernet/cellular framing;
- local firewall;
- NAT where applicable;
- VPN or proxy where applicable.

## Internet routing

- ISP access network;
- autonomous systems;
- BGP;
- peering/transit;
- anycast;
- edge routing.

## Transport and cryptography

- TCP handshake or QUIC connection setup;
- congestion control;
- packet loss recovery;
- TLS 1.3;
- certificate validation;
- key agreement;
- session resumption;
- ALPN/protocol negotiation.

## HTTP

- HTTP/1.1, HTTP/2, or HTTP/3;
- request method;
- request headers;
- cookies;
- content negotiation;
- caching;
- redirects;
- compression;
- response status and headers;
- streaming body.

## Server-side systems

- edge frontend;
- DDoS/security controls;
- connection termination;
- reverse proxy;
- load balancing;
- application services;
- caches;
- storage/indexes;
- response generation.

## Browser loading

- decompression;
- character decoding;
- HTML tokenization/tree construction;
- DOM;
- preload scanning;
- stylesheet loading;
- JavaScript/module loading;
- images and fonts;
- CORS and security policy;
- browser cache updates.

## Rendering

- computed style;
- layout;
- paint;
- layerization;
- rasterization;
- compositing;
- GPU process/service;
- OS compositor;
- display scanout.

## Runtime after load

- event loop;
- tasks and microtasks;
- user input;
- timers;
- animation frames;
- workers;
- fetch/XHR;
- DOM mutation;
- incremental style/layout/paint;
- background and lifecycle management.

---

# 39. Things older versions of this explanation get wrong

This question has circulated for decades, so many versions on the Internet preserve details that were once reasonable but are now misleading.

## “The browser sends HTTP/1.1 unless it upgrades to SPDY”

No longer a useful modern description. SPDY was an important predecessor to HTTP/2, but today's relevant protocol family is HTTP/1.1, HTTP/2, and HTTP/3.

## “HTTPS means TCP, then TLS, then HTTP”

That still describes HTTPS over HTTP/1.1 and HTTP/2, but not HTTP/3. HTTP/3 runs over QUIC, which uses UDP as its substrate and integrates TLS 1.3 into connection establishment.

## “TLS encrypts a random secret with the server's RSA public key”

That describes an older handshake model. TLS 1.3 normally establishes ephemeral shared secrets using modern key agreement and derives traffic keys from them.

## “DNS means UDP port 53 to your router”

Sometimes, but not universally. DNS can be cached at multiple layers, and browsers or operating systems may use encrypted DNS transports.

## “ARP finds the MAC address of the web server”

Not across the public Internet. ARP is local-link IPv4 machinery. Your machine generally needs the MAC address of its local next hop. IPv6 uses Neighbor Discovery instead.

## “The browser downloads the HTML, then downloads the CSS, then downloads the JavaScript”

Too sequential. Resource discovery and fetching overlap with HTML parsing, and multiple resources are fetched concurrently over multiplexed connections.

## “The server finds `index.php` and runs it”

That is one possible architecture for a conventional site, not a universal web-server model and not a good model for hyperscale services.

## “The page is finished when the load event fires”

Modern web applications can continue network, JavaScript, animation, worker, and rendering activity indefinitely.

---

# 40. Why this is still a good question

I like this question because it looks simple and then keeps opening into another layer.

Pressing one key gets you into operating systems. Resolving one hostname gets you into DNS. Reaching one server gets you into routing, transport protocols, encryption, CDNs, and distributed systems. Showing one page gets you into parsers, JavaScript runtimes, layout engines, graphics, GPUs, and displays.

You don’t need to know every detail here to be useful. Nobody keeps the entire stack in their head at once. What matters is knowing roughly where the boundaries are and being able to follow a problem down through them.

And the exact path keeps changing. A version of this article from years ago could reasonably talk mostly about TCP, old TLS handshakes, HTTP/1.1, SPDY, Xorg, or Flash. In 2026, that would give you the wrong mental model in a bunch of places. HTTP/2 and HTTP/3 matter. QUIC matters. TLS 1.3 matters. Encrypted DNS is normal enough that you have to account for it. Browsers are aggressively multi-process. Service workers and modern caching can intercept requests. Rendering is heavily parallelized and GPU-assisted.

So this article shouldn’t be treated like a fixed script. It’s a snapshot of how the stack fits together now.

The next time you type `google.com` and press Enter, the page might appear almost instantly. Underneath that, a ridiculous amount of engineering just agreed on what you meant and got the result onto the screen.

---

# References and further reading

The original inspiration for this rewrite is the collaborative **“What happens when…”** project by Alex Gaynor and contributors.

For the modern protocol and browser architecture discussed here, useful primary or near-primary references include:

- [RFC 9114 — HTTP/3](https://www.rfc-editor.org/rfc/rfc9114)
- [RFC 9000 — QUIC: A UDP-Based Multiplexed and Secure Transport](https://www.rfc-editor.org/rfc/rfc9000)
- [RFC 8446 — TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446)
- [RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)
- [RFC 9112 — HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112)
- [RFC 9113 — HTTP/2](https://www.rfc-editor.org/rfc/rfc9113)
- [WHATWG HTML Living Standard](https://html.spec.whatwg.org/)
- [WHATWG URL Standard](https://url.spec.whatwg.org/)
- [Chromium: Multi-process Architecture](https://www.chromium.org/developers/design-documents/multi-process-architecture/)
- [Chrome for Developers: RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture)
- [MDN Web Docs: Service Worker API](https://developer.mozilla.org/docs/Web/API/Service_Worker_API)

