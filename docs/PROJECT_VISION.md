# Project vision

## Goal

Produce a portable native implementation of **The Story of Thor 2 / The Legend of Oasis** while preserving original behavior through evidence-driven reverse engineering and differential verification.

## Non-goals

- Build a general-purpose Sega Saturn emulator as the final product.
- Produce clean-looking source by guessing intent.
- Depend permanently on the original executable if verified native replacements can remove that dependency.
- Assume every Saturn subsystem is needed before Thor 2 demonstrates it.

## Strategy

1. Establish immutable/canonical input identity.
2. Observe what the game actually executes and loads.
3. Build exact machine-level representations.
4. Mechanically translate bounded execution units.
5. Differentially verify them against an authoritative execution path.
6. Promote verified blocks/functions incrementally.
7. Recover structure and semantics only after correctness is protected.
8. Replace Saturn-facing subsystems only with proof-gated native contracts.
9. Move toward a standalone runtime progressively.

## Success criterion

The project succeeds when the minimum necessary chain of individually proven components reproduces the game's agreed observable behavior and no longer requires unnecessary guest CPU/hardware emulation in production.
