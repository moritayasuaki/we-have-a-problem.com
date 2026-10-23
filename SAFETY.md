# Japanese translation and checker fixes

This branch starts at PR #99 commit
`242c09c4a20fafa25b3da1f09c41cf1419227a7f`.

- Japanese text is embedded as inert JSON in `index.html`. There is no translation
  download to delay the checker. Missing, malformed, or invalid data falls back
  to the original English.
- The executable page script uses ECMAScript 2018 syntax, a compatible own-property
  check, and a manual retry button. Automatic checks start on page load without
  relying on IntersectionObserver or scrolling.
- Certificate and network errors retain the original `blocked` classification
  and green result color. Text describes the observation: the expected test
  response was not received. A visible note explains that this does not prove
  certificate revocation or distrust. Successful test responses are red and
  recommend checking updates; timeouts and unexpected responses remain gray.
- Unexpected checker failures show an inconclusive notice and leave retry enabled.
- The overview is red if any expected test response is received, gray if the
  remaining result is incomplete, and green only if every probe returned the
  existing `blocked` result. Green describes missing responses, not verified
  distrust. Apps, command-line installations, and devices are explicitly outside
  a browser test's scope. A fixed result bar remains visible while scrolling.
  The first expected test response immediately triggers the red bar and an
  accessible alert, without waiting for other probes. Rechecks retain a previous
  positive result with an explicit historical label until they complete.
  Incomplete rechecks cannot erase a positive result. A full all-blocked result
  clears it. The bar makes no claim that an attack occurred.
- Plain-language steps cover browser/OS, app, and firmware updates. A conditional
  DNS/TLS diagram distinguishes cache poisoning from denial of service and cites
  ISC advisories. It does not claim a combined exploit has occurred. Version tables
  are identified as the upstream snapshot dated 23 October 2026.
- The first screen gives three update actions. A device diagram explains PHP,
  TLS libraries, and certificate lists using linked vendor and PHP documentation.
  PHP vulnerabilities and certificate trust are distinct issues; PHP presence
  does not prove eMudhra exposure and a PHP patch alone does not prove trust is
  fixed. Products and versions vary; follow manufacturer instructions.
- Related updates are dated 23 October 2026 and cite PHP, ISC, Cloudflare,
  Homebrew, Electron, Mozilla, Google and the DoH RFC. PHP RCE, conditional BIND
  RCE/cache poisoning, and DNS denial of service are distinguished. Combined
  exploitation is described as conditional reasoning, not observed exploitation.
  cloudflared/WARP updates are vendor-confirmed; specific Slack/Teams exposure
  is not inferred from their framework. Neither 8.8.8.8 route control nor past
  download tampering is implied by possession of compromised certificate keys.
- Router examples distinguish vendor-firmware remote access (Zbtlink), attacker-added
  backdoors (Quad7), and end-of-life devices (KV Botnet). Dates and sampling limits
  accompany counts. A separate Archer AX21 CVE is not assigned as Quad7’s entry
  flaw. The examples do not establish PHP causation, malicious vendor intent, or
  combined eMudhra exploitation. Product-specific remediation takes precedence
  over brand/country generalizations.
- All 14 connection rows and their existing explanation are visible directly below
  the browser verdict, without opening a disclosure. Table wording is preserved.
- The default view prioritizes short update actions. Exact observations, network
  and proxy limitations, and detailed related-issue guidance are in closed native
  disclosures. Green recommends continued automatic updates; it is not relabeled
  as certificate revocation or a complete device assessment. Deep links open the
  relevant disclosures, and the red update notice remains visible while scrolling.
- Detailed evidence and administrator workarounds remain available in disclosure
  sections. Deep links open all enclosing disclosures, including nested ones.
- The static Open Graph and X card tags point to the public 1200×630 PNG, so social
  crawlers do not need JavaScript. The editable SVG is its source. No social SDK,
  analytics script, external font, or third-party image request was added.
- English fragments still have to match exactly before translation. Links, inline
  commands, templates, and the signed proof text are preserved.

Run the dependency-free tests with:

```sh
node --test tests/*.test.cjs
```

CI runs these tests on the exact pushed commit, without third-party actions,
credentials, or write permissions. Browser tests should additionally cover
English/Japanese, missing APIs/data, and mocked success, rejection, timeout, and
unexpected-response states. A successful mocked test does not establish the
certificate behavior of a particular browser or network.

The upstream hosts, certificate material, proof archives, and remediation scripts
are unchanged. This independently branded guide identifies its sources and uses
its own canonical URL at emudhra.hamazon.is. Deployment backups and configuration
must stay outside its public directory. Open Graph image URLs must be updated if
the guide is hosted at another origin. Card metadata and image availability can
be tested locally; a platform's cached preview is controlled by that platform.

## Apple / OCSP diagnostics (23 October 2026)

- Apple guidance distinguishes distributed revocation data, online checks, and best-attempt versus response-required policy. The page does not attribute a past red result to an outage or infer intermediate acceptance from root-store presence.
- The browser's 14-host checker and classification are unchanged. An always-visible short Apple note links directly to a single optional detail section.
- `check-ocsp.py` is an explicitly downloaded, read-only local diagnostic, not website JavaScript or a server proxy. It sends one bounded POST for each of three fixed public certificate paths, with no redirects, automatic retries, or trust-store changes. curl config loading is disabled; environment proxy routing can still apply and is disclosed.
- OCSP response signatures, target matching and freshness must verify before a signed status is reported. HTTP success alone is never protection or revocation success. Embedded public issuers apply only to this diagnostic process. No response verification bypass flags are used.
- Offline tests use temporary test keys and cover good/revoked/unknown, invalid signatures, malformed bodies, stale/future timestamps, wrong certificate and HTTP errors/timeouts. Verification passed using OpenSSL 4 and macOS LibreSSL 3.3.6; the CI also runs these tests.
- Three live sample queries yielded HTTP 403/unconfirmed for the two emSign paths and a verified revoked response for the AAA cross-sign. This is a time-and-network-specific observation, not an outage diagnosis.
