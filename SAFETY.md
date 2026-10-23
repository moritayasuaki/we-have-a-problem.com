# Japanese translation and checker fixes

This branch starts at PR #99 commit
`242c09c4a20fafa25b3da1f09c41cf1419227a7f`.

- Japanese text is embedded as inert JSON in `index.html`. There is no translation
  download to delay the checker. Missing, malformed, or invalid data falls back
  to the original English.
- The executable page script uses ECMAScript 2018 syntax, a compatible own-property
  check, and a manual check button when IntersectionObserver is unavailable.
- Certificate and network errors retain the original `blocked` classification
  and "Did not connect" display. The summary explains that failed connections
  do not prove certificate distrust. Timeouts and unexpected responses remain
  inconclusive.
- Unexpected checker failures show an inconclusive notice and leave retry enabled.
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
are unchanged. A mirror should identify itself as an unofficial snapshot and keep
deployment backups and configuration outside its public directory.
