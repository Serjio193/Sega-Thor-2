# Revision metadata

Each researched game revision gets one legal-safe metadata file after T2-M0 confirms it.

Recommended schema:

```yaml
id: thor2_<region_or_patch>_<short_hash>
status: confirmed

disc:
  format: MODE1/2352
  cue_sha256: <hash>
  data_track_sha256: <hash>

saturn_header:
  product_code: <value>
  version: <value>
  date: <value>
  title: <value>
  first_read_address: 0x........

files:
  manifest: ../../workstreams/T2-M0-disc-census/disc_manifest.tsv

notes:
  - No commercial bytes are stored in this repository.
```

Do not create a `confirmed` revision record from preliminary observations. T2-M0 must first pass reproducibility.
