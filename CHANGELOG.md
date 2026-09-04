# Changelog

## Unreleased (Flutter-first fork)

- Duplicate-info: referensi triase duplikasi + deteksi string-copy ganda
  di scanner + wiring di SKILL.md.
- Label echo: detektor judul-diulang-subteks (guard dialog `?` + elaborasi)
  + dokumentasi batasannya.

- Anti-slop: referensi `references/ai-slop.md` (7+ tells adaptasi Flutter +
  catatan Indonesia) + gate pre-ship di SKILL.md + 2 pola scanner
  (hue default Material, typeface generik).

- Scanner otomatis Flutter-first: pola Compose/Views/SwiftUI di-skip bila
  terdeteksi `pubspec.yaml` (tanpa React Native); override via `--stack all`.
- `IconButton` hanya dilaporkan bila tak ada `tooltip:` dalam 10 baris.
- Cek safe-area/inset native di-skip dalam mode Flutter-first.
- Hasil di app Flutter nyata: P1 64 → 4, P2 39 → 20.

## Unreleased

- Add structured JSON output for automated audit pipelines.
- Flag disabled font scaling, risky single-line labels, constrained Dynamic Type, and autoplay-style React Native video configuration.
- Require media lifecycle, single-caption, interruption, offline, resume, phone, tablet, foldable, and large-text verification where applicable.

## 0.2.0 - 2026-07-15

- Require explicit install modes in noninteractive environments.
- Reject malformed or unknown CLI arguments and invalid global targets.
- Preserve shared agent instruction files through deterministic managed blocks.
- Reject destination symlinks, junctions, reparse-point escapes, and malformed markers.
- Keep the static scanner inside its selected root by skipping linked paths.
- Add built-in tests, package-content checks, CI, security guidance, and release gates.
- Support the maintained Node.js 22, 24, and 26 release lines.

## 0.1.0 - 2026-06-27

- Initial public skill, static scanner, plugin manifests, and interactive installer.
