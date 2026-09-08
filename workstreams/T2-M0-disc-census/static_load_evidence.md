# Static load evidence — `TH2.LOW`

Revision: `thor2_ntsc_patched_fe11d2fb`

Status: **HIGH static confidence; dynamic verification pending**.

## Established substrate facts

- `0TH2.BIN` SHA-256: `c1cc4117870bc567386410aa2d4f1b5f03fb98a601be71bb3ae2155de1853c64`
- `0TH2.BIN` size: `0x82C00`
- Saturn header first-read address: `0x06004000`
- `TH2.LOW` SHA-256: `781396898191921b486be751163aea493ef9b1abcb55c0ab8698df9c69211224`
- `TH2.LOW` size: `0x24800`

## Call-site evidence in `0TH2.BIN`

At file offsets `0x0280..0x0288`, a short SH-2 sequence obtains values from the nearby literal pool and performs an indirect call:

- instruction at `0x0280` loads `R5` from literal at file offset `0x035C`; value = `0x002DA000`;
- instruction at `0x0282` loads `R4` from literal at file offset `0x0360`; value = `0x06081C20`;
- instruction at `0x0284` loads `R3` from literal at file offset `0x0364`; value = `0x0600A0F8`;
- instruction at `0x0286` is `JSR @R3`;
- `0x06081C20 - 0x06004000 = 0x7DC20`;
- file offset `0x7DC20` in `0TH2.BIN` contains the NUL-terminated filename `TH2.LOW`.

Therefore, immediately before that call the observed argument state is consistent with:

```text
R4 -> "TH2.LOW"
R5 = 0x002DA000
R3 = 0x0600A0F8
JSR @R3
```

This is strong evidence for a `TH2.LOW` operation targeting Low Work RAM at `0x002DA000`. The exact semantics of routine `0x0600A0F8` are not yet declared `CONFIRMED`; dynamic load/write tracing is the next gate.

## Range consistency

If `TH2.LOW` is placed at `0x002DA000`, its `0x24800` bytes occupy:

`0x002DA000..0x002FE7FF`

Two Low-WRAM addresses reported in prior public Thor 2 research map inside that range:

- `0x002E55A4 -> TH2.LOW + 0xB5A4`
- `0x002E8A38 -> TH2.LOW + 0xEA38`

The current revision contains SH-2-like instruction streams at both corresponding offsets. This supports the executable-candidate classification but does not replace runtime provenance.

## Decision

`TH2.LOW`: `PROBABLE_CODE`, confidence `HIGH`, candidate load address `0x002DA000`.

Next proof: observe the file read/write provenance and later instruction fetch from the mapped range under the dynamic oracle.
