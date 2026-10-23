# Japanese translation and checker fixes

This branch starts at PR #99 commit
`242c09c4a20fafa25b3da1f09c41cf1419227a7f`.

- Japanese text is embedded as inert JSON in `index.html`. There is no translation
  download to delay the checker. Missing, malformed, or invalid data falls back
  to the original English.
- The executable page script uses ECMAScript 2018 syntax, a compatible own-property
  check, and a manual check button when IntersectionObserver is unavailable.
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
  a browser test's scope. The test starts when its visible overview enters view.
- Plain-language steps cover browser/OS, app, and firmware updates. A conditional
  DNS/TLS diagram distinguishes cache poisoning from denial of service and cites
  ISC advisories. It does not claim a combined exploit has occurred. Version tables
  are identified as the upstream snapshot dated 23 October 2026.
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
