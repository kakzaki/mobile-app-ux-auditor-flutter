#!/usr/bin/env python3
"""Static mobile UX signal scanner.

This script detects review signals in Flutter, React Native, Swift/iOS, and
Android projects. It is evidence gathering, not a full accessibility audit.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "Pods",
    "DerivedData",
    ".gradle",
    "build",
    ".dart_tool",
    ".expo",
    "coverage",
    "ios/Pods",
    "android/build",
}

EXTENSIONS = {
    ".dart",
    ".jsx",
    ".tsx",
    ".js",
    ".ts",
    ".swift",
    ".kt",
    ".kts",
    ".java",
    ".xml",
}

# When a Flutter app is detected, native UI patterns (Compose/Views/SwiftUI)
# only produce noise: a Flutter project's android/ and ios/ folders hold engine
# glue, not app UI, and Dart widgets like Icon( / TextField( textually match
# native regexes. Flutter-first filtering keeps only Flutter + stack-agnostic
# patterns unless the user explicitly asks for everything (--stack all).
FLUTTER_FIRST_PLATFORMS = {"Flutter", "All"}

# Multiline guards: {finding title: (required token regex, lines to look ahead)}.
# Single-line regexes cannot see constructor arguments on following lines, so
# without this every IconButton is flagged even when it has a tooltip.
MULTILINE_GUARDS = {
    "IconButton likely missing tooltip": (r"tooltip\s*:", 10),
}


@dataclass
class Finding:
    severity: str
    platform: str
    category: str
    title: str
    path: str
    line: int
    evidence: str
    fix: str


PATTERNS = [
    (
        "P1",
        "React Native",
        "Accessibility",
        "Touchable/Pressable likely missing role or label",
        re.compile(r"<(?:Pressable|TouchableOpacity|TouchableHighlight|TouchableWithoutFeedback)\b(?![^>\n]*accessibility(?:Role|Label))", re.I),
        "Add accessibilityRole, accessibilityLabel, accessibilityState, and keyboard/screen-reader behavior.",
    ),
    (
        "P2",
        "React Native",
        "Forms",
        "TextInput placeholder-label risk",
        re.compile(r"<TextInput\b[^>\n]*placeholder\s*=", re.I),
        "Verify a persistent visible label and accessibilityLabel are present.",
    ),
    (
        "P1",
        "React Native",
        "Images",
        "Image likely missing accessibility label",
        re.compile(r"<Image\b(?![^>\n]*(?:accessibilityLabel|alt)\s*=)", re.I),
        "Add accessibilityLabel for meaningful images or mark decorative images inaccessible.",
    ),
    (
        "P2",
        "Flutter",
        "Accessibility",
        "IconButton likely missing tooltip",
        re.compile(r"\bIconButton\s*\(", re.I),
        "Verify tooltip/semanticLabel exists so screen readers and long-press hints are useful.",
    ),
    (
        "P1",
        "Flutter",
        "Images",
        "Image likely missing semantic label",
        re.compile(r"\bImage\.(?:asset|network|file|memory)\s*\((?![^;\n]*semanticLabel\s*:)", re.I),
        "Add semanticLabel for meaningful images or exclude decorative images from semantics.",
    ),
    (
        "P3",
        "Flutter",
        "Anti-slop",
        "Default Material hue without brand reason",
        re.compile(r"\bColors\.(?:blue|indigo|purple|lightBlue)\b", re.I),
        "Replace with a named brand hex from the project brief; default hues read as AI-generated.",
    ),
    (
        "P3",
        "Flutter",
        "Anti-slop",
        "Generic default typeface",
        re.compile(r"GoogleFonts\.(?:inter|roboto)\b|fontFamily:\s*['\"]?(?:Roboto|Inter)['\"]?", re.I),
        "Use a deliberate display/body pairing from the project brief instead of the statistical default.",
    ),
    (
        "P2",
        "Flutter",
        "Forms",
        "Text field needs persistent labeling",
        re.compile(r"\bText(?:Form)?Field\s*\(", re.I),
        "Verify InputDecoration has labelText/semantic labeling, helper/error text, and keyboard/autofill hints.",
    ),
    (
        "P1",
        "Swift/iOS",
        "Accessibility",
        "Image likely missing accessibility label",
        re.compile(r"\bImage\s*\([^)]+\)(?![^\n]*accessibilityLabel)", re.I),
        "Add accessibilityLabel for meaningful images or mark decorative images hidden.",
    ),
    (
        "P2",
        "Swift/iOS",
        "Layout",
        "Broad ignoresSafeArea risk",
        re.compile(r"\.ignoresSafeArea\s*\(\s*\)", re.I),
        "Constrain ignored safe areas to intentional background layers, not interactive content.",
    ),
    (
        "P2",
        "Swift/iOS",
        "Permissions",
        "Permission request needs value-first timing",
        re.compile(r"requestAuthorization|requestWhenInUseAuthorization|requestAlwaysAuthorization", re.I),
        "Verify permission is requested at the moment of user intent and has a clear rationale.",
    ),
    (
        "P1",
        "Android Compose",
        "Accessibility",
        "Icon likely missing contentDescription",
        re.compile(r"\bIcon\s*\((?![^)\n]*contentDescription\s*=)", re.I),
        "Set contentDescription for meaningful icons or null for decorative icons.",
    ),
    (
        "P1",
        "Android Compose",
        "Accessibility",
        "Clickable modifier may need role/state semantics",
        re.compile(r"\.clickable\s*\(", re.I),
        "Verify role, stateDescription, custom actions, and target size for custom clickable UI.",
    ),
    (
        "P2",
        "Android Compose",
        "Forms",
        "TextField needs explicit label/error support",
        re.compile(r"\b(?:OutlinedTextField|TextField)\s*\(", re.I),
        "Verify label, supportingText/error state, keyboardOptions, and autofill behavior.",
    ),
    (
        "P1",
        "Android Views",
        "Accessibility",
        "ImageView likely missing contentDescription",
        re.compile(r"<ImageView\b(?![^>\n]*android:contentDescription\s*=)", re.I),
        "Add android:contentDescription for meaningful images or @null for decorative images.",
    ),
    (
        "P2",
        "Android Views",
        "Forms",
        "EditText likely missing hint/label relationship",
        re.compile(r"<EditText\b(?![^>\n]*android:hint\s*=)", re.I),
        "Use hint/labelFor or Material TextInputLayout with clear errors and keyboard input type.",
    ),
    (
        "P2",
        "All",
        "Retention",
        "Notification or permission ask found",
        re.compile(r"requestPermissions?|POST_NOTIFICATIONS|UNUserNotificationCenter|notifications?\b", re.I),
        "Check this is value-timed, optional when possible, and paired with granular settings.",
    ),
]


def contained_path(root: Path, candidate: Path) -> Path | None:
    """Resolve a non-linked path only when it remains under the scan root."""
    try:
        if candidate.is_symlink():
            return None
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        return resolved
    except (OSError, RuntimeError, ValueError):
        return None


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        resolved = contained_path(root, path)
        if resolved is None or not resolved.is_file():
            continue
        relative = resolved.relative_to(root)
        if any(part in EXCLUDE_DIRS for part in relative.parts):
            continue
        if resolved.suffix.lower() not in EXTENSIONS:
            continue
        if resolved.stat().st_size > 1_000_000:
            continue
        yield resolved


def detect_stack(root: Path, files: list[Path]) -> list[str]:
    stack: list[str] = []
    if contained_path(root, root / "pubspec.yaml") is not None:
        stack.append("Flutter")
    package_json = root / "package.json"
    safe_package_json = contained_path(root, package_json)
    if safe_package_json is not None and safe_package_json.is_file():
        try:
            data = json.loads(safe_package_json.read_text(encoding="utf-8"))
            deps = " ".join(
                list((data.get("dependencies") or {}).keys())
                + list((data.get("devDependencies") or {}).keys())
            )
            if "react-native" in deps:
                stack.append("React Native")
            if "expo" in deps:
                stack.append("Expo")
        except Exception:
            stack.append("package.json present, unreadable")
    if any(path.suffix.lower() == ".swift" for path in files):
        stack.append("Swift/iOS")
    if any(path.suffix.lower() in {".kt", ".java"} for path in files):
        stack.append("Android Kotlin/Java")
    if (safe_android := contained_path(root, root / "android")) is not None and safe_android.is_dir():
        stack.append("Android project")
    if (safe_ios := contained_path(root, root / "ios")) is not None and safe_ios.is_dir():
        stack.append("iOS project")
    return sorted(set(stack)) or ["Unknown mobile stack"]


def global_findings(
    root: Path, stack: list[str], all_text: str, flutter_first: bool
) -> list[Finding]:
    findings: list[Finding] = []
    if "Flutter" in stack and "SafeArea" not in all_text:
        findings.append(
            Finding("P2", "Flutter", "Layout", "SafeArea not found", ".", 0, "No SafeArea token found", "Verify content avoids notches, system bars, keyboards, and gesture areas.")
        )
    if flutter_first:
        # Native safe-area/inset checks do not apply to the Flutter layer.
        return findings
    if "React Native" in stack and "SafeAreaView" not in all_text and "useSafeAreaInsets" not in all_text:
        findings.append(
            Finding("P2", "React Native", "Layout", "Safe-area handling not found", ".", 0, "No SafeAreaView/useSafeAreaInsets token found", "Verify content avoids notches, system bars, and gesture areas.")
        )
    if ("Android Kotlin/Java" in stack or "Android project" in stack) and "WindowInsets" not in all_text and "safeDrawing" not in all_text:
        findings.append(
            Finding("P2", "Android", "Adaptive layout", "Inset handling not found", ".", 0, "No WindowInsets/safeDrawing token found", "Verify edge-to-edge layouts account for system bars and IME.")
        )
    return findings


def scan(
    root: Path, stack_override: str = "auto"
) -> tuple[list[str], list[Finding], int, bool]:
    findings: list[Finding] = []
    files = list(iter_files(root))
    stack = detect_stack(root, files)
    flutter_first = stack_override == "flutter" or (
        stack_override == "auto"
        and "Flutter" in stack
        and "React Native" not in stack
    )
    active_platforms: set[str] | None = (
        FLUTTER_FIRST_PLATFORMS if flutter_first else None
    )
    snippets: list[str] = []
    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        try:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        snippets.extend(lines[:2000])
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            for severity, platform, category, title, pattern, fix in PATTERNS:
                if active_platforms is not None and platform not in active_platforms:
                    continue
                if not pattern.search(stripped):
                    continue
                guard = MULTILINE_GUARDS.get(title)
                if guard is not None:
                    token, lookahead = guard
                    block = "\n".join(lines[idx - 1 : idx + lookahead])
                    if re.search(token, block):
                        continue
                findings.append(
                    Finding(
                        severity=severity,
                        platform=platform,
                        category=category,
                        title=title,
                        path=rel,
                        line=idx,
                        evidence=stripped[:180],
                        fix=fix,
                    )
                )
    findings = (
        global_findings(root, stack, "\n".join(snippets), flutter_first)
        + findings
    )
    findings = duplicate_copy_findings(root, files) + findings
    findings = label_echo_findings(root, files) + findings
    findings = emoji_density_findings(root, files) + findings
    return stack, findings, len(files), flutter_first


EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]"
)
EMOJI_DENSITY_THRESHOLD = 12


def emoji_density_findings(root: Path, files: list[Path]) -> list[Finding]:
    """Report UI files with high emoji density.

    Emoji as the sole affordance is an AI-slop tell; opensource icons and
    Lottie should carry function and decoration. Files above the threshold
    are triage candidates, NOT verdicts — a brief-declared warm identity
    (e.g. maternal apps) may justify them. Confirm each emoji is paired
    with a text label or Material icon before changing anything.
    """
    out: list[Finding] = []
    for file_path in files:
        if file_path.suffix.lower() != ".dart":
            continue
        rel = file_path.relative_to(root).as_posix()
        if not (rel.startswith("lib/screens/") or rel.startswith("lib/widgets/")):
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        hits = EMOJI_RE.findall(text)
        if len(hits) <= EMOJI_DENSITY_THRESHOLD:
            continue
        top = ", ".join(
            f"{e}×{c}" for e, c in collections.Counter(hits).most_common(5)
        )
        out.append(
            Finding(
                "P3",
                "Flutter",
                "Anti-slop",
                "High emoji density — verify deliberate",
                rel,
                1,
                f"{len(hits)} emoji: {top[:100]}",
                "Keep only brief-declared emoji paired with labels; "
                "use Material icons for affordances, Lottie for decoration. "
                "See references/ai-slop.md.",
            )
        )
    return out


def duplicate_copy_findings(root: Path, files: list[Path]) -> list[Finding]:
    """Flag long string literals repeated across files.

    Same copy in 2+ places rots independently — single-source it or make
    the repetition an intentional, canonical reinforcement.
    """
    seen: dict[str, list[tuple[str, int]]] = {}
    for file_path in files:
        if file_path.suffix.lower() not in {".dart", ".tsx", ".jsx", ".swift", ".kt"}:
            continue
        rel = file_path.relative_to(root).as_posix()
        try:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("import ") or len(stripped) < 60:
                continue
            for match in re.finditer(r"'([^'\n]{50,160})'", line):
                text = " ".join(match.group(1).split())
                seen.setdefault(text, []).append((rel, idx))
    out: list[Finding] = []
    for text, locs in seen.items():
        hit_files = {loc[0] for loc in locs}
        if len(hit_files) < 2:
            continue
        first, rest = locs[0], locs[1:4]
        others = ", ".join(f"{p}:{n}" for p, n in rest)
        platform = "Flutter" if first[0].endswith(".dart") else "All"
        out.append(
            Finding(
                "P3",
                platform,
                "Duplication",
                "Same copy in multiple files",
                first[0],
                first[1],
                text[:100],
                f"Single-source this copy; also found in {others}. "
                "See references/duplicate-info.md.",
            )
        )
    return out


ECHO_STOPWORDS = {
    "yang", "dan", "dari", "untuk", "dengan", "dalam", "pada", "ini",
    "itu", "adalah", "atau", "juga", "bisa", "agar", "bila", "saat",
    "anda", "kamu", "kita", "bunda", "the", "and", "for", "with",
    "your", "this", "that",
}


def label_echo_findings(root: Path, files: list[Path]) -> list[Finding]:
    """Flag heading text echoed by nearby subtext.

    A title followed within a few lines by a description sharing most of
    its content words ("Tekanan Darah" / "Catat tekanan darah di sini")
    wastes vertical space and reads as filler. Descriptions must ADD
    information (action, scope, state) instead of restating the title.
    """
    out: list[Finding] = []
    for file_path in files:
        if file_path.suffix.lower() != ".dart":
            continue
        rel = file_path.relative_to(root).as_posix()
        try:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        lits: list[tuple[int, str]] = []
        for idx, line in enumerate(lines):
            for match in re.finditer(r"'([^'\n]{4,120})'", line):
                text = " ".join(match.group(1).split())
                if text.startswith("package:") or text.startswith("http"):
                    continue
                lits.append((idx, text))
        for (i1, t1), (i2, t2) in zip(lits, lits[1:]):
            if i2 - i1 > 6 or t1 == t2:
                continue

            def words(t: str) -> set[str]:
                return {
                    w.lower().strip(".,!?():")
                    for w in t.split()
                    if len(w) > 3
                } - ECHO_STOPWORDS

            w1, w2 = words(t1), words(t2)
            if len(w1) < 2 or len(w2) < 2:
                continue
            # Dialog titles intentionally mirror their button labels.
            if "?" in t1 or "?" in t2:
                continue
            # Elaboration is not echo: a subtext that contains the whole
            # title plus new information is doing its job.
            if w1 <= w2 or w2 <= w1:
                continue
            overlap = w1 & w2
            if len(overlap) >= 2 and len(overlap) / min(len(w1), len(w2)) >= 0.5:
                out.append(
                    Finding(
                        "P3",
                        "Flutter",
                        "Duplication",
                        "Heading echo in nearby subtext",
                        rel,
                        i1 + 1,
                        f"'{t1[:80]}' // '{t2[:80]}'",
                        "Merge the echo or make the subtext add action/scope/state. "
                        "See references/duplicate-info.md.",
                    )
                )
    return out


def render_markdown(
    root: Path,
    stack: list[str],
    findings: list[Finding],
    file_count: int,
    flutter_first: bool,
) -> str:
    counts = {key: sum(1 for item in findings if item.severity == key) for key in ("P0", "P1", "P2", "P3")}
    out = [
        "# Mobile UX Static Scan",
        "",
        f"Root: `{root}`",
        f"Files scanned: `{file_count}`",
        f"Detected stack: {', '.join(stack)}",
        f"Findings: P0={counts['P0']} P1={counts['P1']} P2={counts['P2']} P3={counts['P3']}",
        "",
        "> Static scan output is a triage signal. Confirm every finding in the app or code before changing behavior.",
        "",
    ]
    if flutter_first:
        out.append(
            "> Flutter-first mode: native (Compose/Views/SwiftUI) patterns skipped. "
            "Re-run with `--stack all` to include them."
        )
        out.append("")
    if not findings:
        out.append("No matching static UX signals found.")
        return "\n".join(out)

    out.extend(["| Severity | Platform | Category | Location | Signal | Evidence | Fix |", "| --- | --- | --- | --- | --- | --- | --- |"])
    for item in findings[:140]:
        location = item.path if item.line == 0 else f"{item.path}:{item.line}"
        evidence = item.evidence.replace("|", "\\|")
        out.append(
            f"| {item.severity} | {item.platform} | {item.category} | `{location}` | {item.title} | `{evidence}` | {item.fix} |"
        )
    if len(findings) > 140:
        out.append(f"\nTruncated to 140 findings out of {len(findings)}. Narrow the scan path for more detail.")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a mobile app for static UX review signals.")
    parser.add_argument("root", nargs="?", default=".", help="Project root or subdirectory to scan")
    parser.add_argument(
        "--stack",
        choices=("auto", "flutter", "all"),
        default="auto",
        help="Pattern set: auto detects Flutter-first, flutter forces it, all disables filtering",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        raise SystemExit(f"Path does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Path is not a directory: {root}")
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    stack, findings, file_count, flutter_first = scan(root, args.stack)
    print(render_markdown(root, stack, findings, file_count, flutter_first))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
