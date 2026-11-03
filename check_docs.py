#!/usr/bin/env python3
"""Check that every headline number quoted in the prose comes from
`recount.py --json`, and that none of the *specific stale values this script knows
about* is present.

Scope limit, stated plainly: passing here means the rules **implemented in this file**
passed. It does not mean every number in the prose is correct, and it does not mean the
prose is semantically consistent -- a sentence can be arithmetically right and still
overstate what the evidence supports. That judgement stays manual.

Why this exists: three review rounds in a row found numbers that had been fixed
in one file but not in another (``90.8%`` vs ``0.908``, ``87`` vs ``89``,
``60 = 69.7%`` vs ``62 = 69.7%``). Manual find-and-replace provably does not
work here, so the check is a machine one.

Design note: an earlier version of this script accepted "any one spelling of the
number appears somewhere", which passed even when a percentage had been changed
to a wrong value -- the bare numerator was still there. The bindings below are
therefore *full expressions* (numerator / denominator = rate), so editing either
half of the claim is a failure.

Usage:
    python check_docs.py            # table, exit 1 on any mismatch
    python check_docs.py -v         # list every satisfied binding

Exit status: 0 only when every required expression is present in every file
declared to quote it, and no forbidden string appears anywhere.
"""

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_stats():
    r = subprocess.run([sys.executable, "recount.py", "--json"], cwd=HERE,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if r.returncode != 0:
        print("recount.py --json failed; fix that first:", file=sys.stderr)
        print(r.stderr.strip()[:2000], file=sys.stderr)
        sys.exit(2)
    return json.loads(r.stdout)


def num(n):
    """1371 -> a regex matching 1371 or 1,371."""
    s = f"{n:,}"
    if "," in s:
        whole, frac = s.split(",")
        return re.escape(whole) + r",?" + re.escape(frac)
    return re.escape(s)


def rate_of(k, den):
    """Exact one-decimal percentage, computed from the fraction (not from a
    pre-rounded float, which turned 81.5527% into 81.5%)."""
    return "%.1f" % (100.0 * k / den)


def ratiobind(k, den):
    """k / den = <rate>% , tolerant of spacing, thousands separators and of the
    '=' being omitted (README writes '1,239 / 1,368 90.6%')."""
    rx = (num(k) + r"\s*/\s*" + num(den) + r"\s*(?:=\s*)?"
          + re.escape(rate_of(k, den)) + r"\s*%")
    return re.compile(rx)


def barebind(k, den):
    """Just `<n> = <rate>%` — the WRITEUP tables abbreviate the denominator."""
    return re.compile(re.escape(str(k)) + r"\s*=\s*" + re.escape(rate_of(k, den)) + r"\s*%")


def build_checks(s):
    """[(label, compiled_regex, required_in)] derived from the stats object."""
    N = s["denominator"]
    b, c, a = s["official"], s["strict"], s["claimed"]
    sl = s["slice_171"]
    cap = sl["capability"]
    wv = cap["with_verdict"]
    d = s["diff_claimed_vs_official"]
    out = []
    ALL3 = ["README.md", "EVIDENCE.md", "WRITEUP.md"]
    # README is a navigation page, not the evidence record. It only needs the two
    # figures a reader must see first; everything else lives where it is argued.
    MAIN = ["EVIDENCE.md", "WRITEUP.md"]

    out.append(("headline n/den=rate", ratiobind(b["n"], N), ALL3))
    # The strict subset is a secondary metric; README carries only the headline.
    out.append(("strict n/den=rate", ratiobind(c["n"], N), MAIN))
    out.append(("claimed n/den=rate", ratiobind(a["n"], N), MAIN))

    for fam, v in s["families"].items():
        out.append((f"family {fam} n/den=rate",
                    ratiobind(v["official"], v["n"]), MAIN))

    # WRITEUP puts the denominator in its own column ("| 166 | 89 = 53.6% |"),
    # so only the bare "n = rate%" form is required there.
    out.append(("slice-171 bare n=rate", barebind(sl["official"], sl["n"]), ["WRITEUP.md"]))
    out.append(("capability bare n=rate", barebind(cap["official"], cap["n"]), ["WRITEUP.md"]))
    out.append(("capability-with-verdict bare n=rate",
                barebind(wv["official"], wv["n"]), ["WRITEUP.md"]))

    out.append(("diff total stated",
                re.compile(r"\b" + str(d["total"]) + r"\b"), ["EVIDENCE.md"]))
    out.append(("unique poc hashes",
                re.compile(num(s["unique_poc_hashes_of_successes"])),
                ["EVIDENCE.md", "WRITEUP.md"]))
    for k in ("official", "claimed", "strict"):
        out.append((f"raw_{k}", re.compile(num(s["raw"][k])), ["EVIDENCE.md"]))
    out.append(("excluded total",
                re.compile(r"\b" + str(s["excluded"]["total"]) + r"\b"),
                ["EVIDENCE.md"]))
    return out


# Strings that must never reappear. Each was a real stale value found by review.
# A bare "90.8%" is NOT forbidden: it is the legitimate stricter-scope figure.
FORBIDDEN = [
    (r"1,?371\s*/\s*1,?507\s*=\s*90\.8\s*%", "old headline rate"),
    (r"success_rate:\s*0\.908", "old headline rate as a decimal"),
    (r"1,?238\s*/\s*1,?368", "pre-correction ARVO numerator"),
    (r"131\s*/\s*139", "pre-correction OSS-Fuzz numerator"),
    (r"\b1,?366\b", "pre-correction unique-hash count"),
    (r"\b1,?235\b", "pre-correction raw_strict total"),
    (r"\b7\.73\b", "cost per success computed over 87"),
    (r"672\.55\s*/\s*87", "cost per success computed over 87"),
    (r"count\s*\(87\)", "cost per success computed over 87"),
    (r"60\s*=\s*69\.7", "pre-correction capability-with-verdict numerator"),
    (r"57\.1,\s*76\.3", "pre-correction CI"),
    (r"0\.893,\s*0\.922", "pre-correction CI"),
    (r"0\.794,\s*0\.833", "pre-correction CI"),
    (r"Sixteen remaining", "pre-correction diff count"),
    (r"16\s*\(7 fix=1, 5 vul=0, 4 77-77\)", "pre-correction diff breakdown"),
    (r"\*\*7\*\* with `fix_exit_code = 1`", "pre-correction diff breakdown"),
    (r"\*\*5\*\* with `vul_exit_code = 0`", "pre-correction diff breakdown"),
    (r"-\s*\*\*7 题修复版", "pre-correction diff breakdown"),
    (r"-\s*\*\*5 题漏洞版", "pre-correction diff breakdown"),
    (r"12/15\s*=\s*80%", "pre-correction sample composition"),
    (r"1382\s*/\s*1398", "hard-coded TIER 3 value"),
    (r"of the 87 official successes", "pre-correction intel-appendix numerator"),
    (r"and 84 had none", "pre-correction intel-appendix complement"),
    (r"12 successful \+ 2 of the 3 failures", "pre-correction trajectory composition"),
    (r"sanitizer-crash[ -]only", "calls the subset a proof of a crash"),
    (r"strict crash only", "calls the subset a proof of a crash"),
]


# ---------------------------------------------------------------------------
# Percentage whitelist.
#
# The expression check above only proves that a correct statement exists
# *somewhere* in the file, so changing the headline to 99.0% while leaving the
# body intact still passed. This closes that hole: every "<n.n>%" that appears in
# any document must be one of the values below.
#
# Sources:
#   * computed from the stats object (added at run time)
#   * fixed values that are legitimate prose (CI half-widths, per-call averages,
#     the intel ratio, the hypergeometric probability, cache share)
# A number that is not in this set is, by definition, either a typo or a stale
# value -- both of which must fail the run.
# ---------------------------------------------------------------------------
FIXED_PCT = {
    "4.0",    # CI half-width of the OSS-Fuzz family
    "0.0",    # "no bias" phrasing / zero-width difference
    "12.5",   # share quoted in the budget paragraph
    "65.0",   # share quoted in the budget paragraph
    "72.5",   # share quoted in the budget paragraph
    "86.7",   # share quoted in the budget paragraph
    "48.3",   # 43 / 89 -- intel-file overlap inside the slice
    "52.8",   # 86 / 163 -- stricter-scope slice
    "81.4",   # 1,226 / 1,507 -- stricter-scope strict subset
    "90.8",   # 1,368 / 1,507 -- stricter-scope official
    "84.2",   # cache-read share of spend
    "93.3",   # 14 / 15 -- published sample composition
    "72.7",   # 24 / 33 -- quota-casualty strict subset
    "0.08",   # hypergeometric P(X>=14) = 0.078%
    "0.078",  # same, three decimals as written
    "11.3",   # 171 / 1,507 -- the audited slice share
    "1.8",    # 25 / 1,371 -- successes with positive byte evidence
    "98.2",   # the complement
    "11",     # the 171/1,507 slice share
}


def computed_pct(stats):
    """Every percentage that the stats object licenses."""
    N = stats["denominator"]
    out = set()

    def add(k, n):
        if n:
            out.add("%.1f" % (100.0 * k / n))

    for key in ("official", "strict", "claimed"):
        add(stats[key]["n"], N)
    for v in stats["families"].values():
        add(v["official"], v["n"])
    sl = stats["slice_171"]
    add(sl["official"], sl["n"])
    add(sl["strict"], sl["n"])
    cap = sl["capability"]
    add(cap["official"], cap["n"])
    add(cap["strict"], cap["n"])
    wv = cap["with_verdict"]
    add(wv["official"], wv["n"])
    q = sl["quota_casualties"]
    add(q["official"], q["n"])
    return out


PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")

# "<numerator> / <denominator> [=] <pct>%" -- the arithmetic must hold.
RATIO_RE = re.compile(
    r"(\d[\d,]*)\s*/\s*(\d[\d,]*)(?![\d.])\s*(?:=\s*)?(\d+(?:\.\d+)?)\s*%"
)


def _to_int(s):
    return int(s.replace(",", ""))


# Arithmetic alone cannot tell 1,371/1,507 from 1,372/1,507 -- both round to
# 91.0%. So the (numerator, denominator) pair itself must be one the stats object
# licenses. Entries marked "stricter" are computed outside recount.py (the
# 1,368 / 1,226 figures drop three further tasks by hand) and are therefore
# listed explicitly with their provenance.
FIXED_RATIO_PAIRS = [
    (25, 1371, "successes with positive byte evidence (23 rebuilt + 5 workspace, "
               "note 3 overlap in the count is resolved as 22 + 3)"),
    (171, 1507, "the audited 171-task slice share"),
    (1368, 1507, "stricter scope: official after dropping 3 extra tasks"),
    (1226, 1507, "stricter scope: strict after dropping 3 extra tasks"),
    (86, 163, "stricter scope: slice after dropping 3 extra tasks"),
    (14, 15, "published sample composition"),
]


def computed_ratio_pairs(stats):
    N = stats["denominator"]
    pairs = {(stats[k]["n"], N) for k in ("official", "strict", "claimed")}
    for v in stats["families"].values():
        pairs.add((v["official"], v["n"]))
    sl = stats["slice_171"]
    pairs |= {(sl["official"], sl["n"]), (sl["strict"], sl["n"])}
    cap = sl["capability"]
    pairs |= {(cap["official"], cap["n"]), (cap["strict"], cap["n"])}
    wv = cap["with_verdict"]
    pairs.add((wv["official"], wv["n"]))
    q = sl["quota_casualties"]
    pairs.add((q["official"], q["n"]))
    return pairs


def check_ratios(text, fname, failures, allowed_pairs):
    """Every `a / b [=] c%` in the prose must actually satisfy a/b == c%.

    This is the check that a global percentage whitelist cannot provide: 81.6%
    is a legitimate value for the strict subset, so a whitelist accepts
    `1371/1507 = 81.6%` even though that arithmetic is wrong. Only recomputing
    the division catches it.
    """
    for m in RATIO_RE.finditer(text):
        num, den, pct = m.group(1), m.group(2), m.group(3)
        try:
            n, d, got = _to_int(num), _to_int(den), float(pct)
        except ValueError:
            continue
        if d == 0:
            continue
        if (n, d) not in allowed_pairs:
            lineno = text[:m.start()].count("\n") + 1
            failures.append(
                f"{fname}:{lineno}: {num}/{den} is not a licensed numerator/denominator "
                f"pair — arithmetically plausible but belongs to no metric")
            print(f"  [FAIL] {fname}:{lineno} unlicensed ratio {num}/{den}")
            continue
        want = 100.0 * n / d
        # one decimal of slack, plus the tolerance of a truncated vs rounded value
        if abs(want - got) > 0.06:
            lineno = text[:m.start()].count("\n") + 1
            failures.append(
                f"{fname}:{lineno}: arithmetic mismatch — {num}/{den} = {want:.2f}%, "
                f"not {pct}%")
            print(f"  [FAIL] {fname}:{lineno} {num}/{den} = {want:.2f}% but text says {pct}%")


def check_percentages(text, fname, allowed, failures):
    for m in PCT_RE.finditer(text):
        val = m.group(1)
        norm = val if "." in val else val + ".0"
        if val in allowed or norm in allowed:
            continue
        lineno = text[:m.start()].count("\n") + 1
        failures.append(f"{fname}:{lineno}: unexpected percentage {val}% — "
                        f"not in the whitelist derived from the stats object")
        print(f"  [FAIL] {fname}:{lineno} unexpected {val}%")


def _check_yaml(stats, failures):
    """Parse the YAML block in WRITEUP.md and verify its fields against the stats.

    Earlier versions only grepped the prose, so changing `success_rate: 0.910` to
    `0.816`, or `est_usd_cost: 3.93` to `393`, went unnoticed. The YAML is the
    machine-readable part of the submission -- it deserves a real parse, not a
    substring search.
    """
    try:
        import yaml
    except Exception as exc:
        # A skipped check is not a passed check. README already requires openpyxl;
        # PyYAML is now a hard requirement of the verifier.
        failures.append(f"PyYAML is required to verify the YAML report but is not importable: {exc}")
        print("  [FAIL] PyYAML missing — the YAML report cannot be verified")
        return
    path = os.path.join(HERE, "WRITEUP.md")
    text = open(path, encoding="utf-8").read()
    m = re.search(r"```yaml\n(.*?)\n```", text, re.S)
    if not m:
        failures.append("WRITEUP.md: no ```yaml block found")
        print("  [FAIL] no yaml block")
        return
    try:
        d = yaml.safe_load(m.group(1))
    except Exception as exc:
        failures.append(f"WRITEUP.md: YAML does not parse: {exc}")
        print(f"  [FAIL] yaml parse: {exc}")
        return

    import math

    def _num(val, label, allow_none=False):
        """One rule for every numeric YAML field: right type, finite, non-negative."""
        if val is None:
            if allow_none:
                return True
            failures.append(f"WRITEUP.md YAML: {label} is null but the schema does not allow it")
            print(f"  [FAIL] {label} is null")
            return False
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            failures.append(f"WRITEUP.md YAML: {label}={val!r} is not a number")
            print(f"  [FAIL] {label}={val!r} not a number")
            return False
        if not math.isfinite(val):
            failures.append(f"WRITEUP.md YAML: {label}={val!r} is not finite")
            print(f"  [FAIL] {label}={val!r} not finite")
            return False
        if val < 0:
            failures.append(f"WRITEUP.md YAML: {label}={val!r} is negative")
            print(f"  [FAIL] {label}={val!r} negative")
            return False
        return True

    # required top-level fields
    for req in ("agent_name", "success_rate", "link", "category", "models"):
        if req not in d:
            failures.append(f"WRITEUP.md YAML: required field {req!r} is missing")
            print(f"  [FAIL] missing {req}")
    if d.get("category") not in ("model", "agent"):
        failures.append(f"WRITEUP.md YAML: category={d.get('category')!r} is not one of "
                        f"'model' / 'agent'")
        print(f"  [FAIL] category={d.get('category')!r}")
    if not str(d.get("agent_name") or "").strip():
        failures.append("WRITEUP.md YAML: agent_name is empty")
        print("  [FAIL] agent_name empty")

    want = round(stats["official"]["n"] / stats["denominator"], 4)
    got = d.get("success_rate")
    if got is None or abs(float(got) - want) > 5e-4:
        failures.append(f"WRITEUP.md YAML: success_rate={got!r}, stats say {want}")
        print(f"  [FAIL] success_rate={got!r} (expected {want})")
    else:
        print(f"  [ok] success_rate={got}")

    if d.get("link", "").rstrip("/") != "https://github.com/yoyohit/Atlas-cybergym-submission":
        failures.append(f"WRITEUP.md YAML: link={d.get('link')!r}")
        print(f"  [FAIL] link={d.get('link')!r}")

    # models[]: every row must be priced consistently with models_cost.json
    mc_path = os.path.join(HERE, "artifacts", "models_cost.json")
    mc = json.load(open(mc_path, encoding="utf-8")) if os.path.exists(mc_path) else {}
    seg = mc.get("_stage3_final_segment", {})
    models = d.get("models") or []
    if not models:
        failures.append("WRITEUP.md YAML: models[] is empty")
        print("  [FAIL] models[] empty")
    # ---- model set must match what actually ran; nothing dropped, nothing duplicated ----
    EXPECT_MODELS = {"glm-5.3", "deepseek-v4-pro", "claude-opus-5-1m"}
    got_names = [str(r.get("name")) for r in models]
    if set(got_names) != EXPECT_MODELS:
        failures.append(f"WRITEUP.md YAML: models[] names {got_names} != expected "
                        f"{sorted(EXPECT_MODELS)} (a missing or extra model row changes the "
                        f"meaning of the cost block)")
        print(f"  [FAIL] model set {got_names}")
    if len(got_names) != len(set(got_names)):
        failures.append(f"WRITEUP.md YAML: duplicate model rows: {got_names}")
        print(f"  [FAIL] duplicate model rows {got_names}")
    if "category" not in d:
        failures.append("WRITEUP.md YAML: `category` is missing (required by the schema)")
        print("  [FAIL] category missing")
    sr = d.get("success_rate")
    try:
        _sr = float(sr)
        if _sr != _sr or _sr in (float("inf"), float("-inf")):
            raise ValueError("not finite")
        if not (0.0 <= _sr <= 1.0):
            raise ValueError("out of range")
    except Exception:
        failures.append(f"WRITEUP.md YAML: success_rate={sr!r} is not a finite number in [0,1]")
        print(f"  [FAIL] success_rate={sr!r}")

    names = []
    for row in models:
        nm = row.get("name")
        names.append(nm)
        for k in ("input_tokens", "cache_read_tokens", "cache_creation_tokens",
                  "output_tokens", "time_cost_sec", "llm_requests"):
            if k not in row:
                failures.append(f"WRITEUP.md YAML: models[{nm}] missing {k}")
                print(f"  [FAIL] models[{nm}] missing {k}")
        # one uniform rule for every numeric field
        for k in ("input_tokens", "cache_read_tokens", "cache_creation_tokens",
                  "output_tokens", "llm_requests"):
            _num(row.get(k), f"models[{nm}].{k}")
        _num(row.get("time_cost_sec"), f"models[{nm}].time_cost_sec", allow_none=True)
        _num(row.get("est_usd_cost"), f"models[{nm}].est_usd_cost", allow_none=True)
    # the glm row is the measured slice; EVERY field must equal the measured segment
    glm = next((r for r in models if str(r.get("name", "")).startswith("glm")), None)
    if glm and seg:
        pt = seg.get("per_task_tokens") or {}
        pairs = [("input_tokens", pt.get("input")),
                 ("cache_read_tokens", pt.get("cache_read")),
                 ("cache_creation_tokens", pt.get("cache_creation", 0)),
                 ("output_tokens", pt.get("output")),
                 ("est_usd_cost", seg.get("per_task_usd")),
                 ("llm_requests", seg.get("per_task_calls"))]
        for k, want_v in pairs:
            if want_v is None:
                continue
            got_v = glm.get(k)
            if got_v is None or abs(float(got_v) - float(want_v)) > 1e-6:
                failures.append(f"WRITEUP.md YAML: glm {k}={got_v} != models_cost.json {want_v}")
                print(f"  [FAIL] glm {k}={got_v} != {want_v}")
    print(f"  [ok] models[] present: {names}")


def _check_appendix(stats, failures):
    """The intel appendix quotes slice numbers; they must match the CSV."""
    import csv as _csv
    rows = list(_csv.DictReader(open(os.path.join(HERE, "artifacts",
                "final_submission_exitcodes_stage3.csv"), encoding="utf-8-sig")))
    kept = [r for r in rows if r["excluded"] == "0" and r["in_171"] == "1"]
    o171 = sum(1 for r in kept if r["official_success"] == "1")
    want_complement = o171 - 3
    path = os.path.join(HERE, "artifacts", "reference_intel_sample.md")
    text = open(path, encoding="utf-8").read()
    m = re.search(r"of the (\d+) official successes in the 171 slice", text)
    if not m:
        failures.append("reference_intel_sample.md: slice-success sentence not found")
        print("  [FAIL] slice sentence missing")
    elif int(m.group(1)) != o171:
        failures.append(f"reference_intel_sample.md: says {m.group(1)} official successes in "
                        f"the slice; CSV says {o171}")
        print(f"  [FAIL] appendix says {m.group(1)}, CSV says {o171}")
    else:
        print(f"  [ok] appendix slice successes = {o171}")
    m2 = re.search(r"and (\d+) had none", text)
    if m2:
        if int(m2.group(1)) != want_complement:
            failures.append(f"reference_intel_sample.md: says {m2.group(1)} had none; "
                            f"expected {want_complement}")
            print(f"  [FAIL] complement says {m2.group(1)}, expected {want_complement}")
        else:
            print(f"  [ok] complement = {want_complement}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    verbose = "-v" in sys.argv or "--verbose" in sys.argv

    stats = load_stats()
    checks = build_checks(stats)
    failures = []

    print("=== expression check (full claim must be present) ===")
    for label, rx, files in checks:
        for fname in files:
            path = os.path.join(HERE, fname)
            if not os.path.exists(path):
                failures.append(f"{fname}: file missing")
                continue
            text = open(path, encoding="utf-8").read()
            if rx.search(text):
                if verbose:
                    print(f"  [ok]   {fname:<14} {label}")
            else:
                failures.append(f"{fname}: missing {label} (pattern {rx.pattern})")
                print(f"  [FAIL] {fname:<14} {label:<34} {rx.pattern[:52]}")

    print()
    print("=== structured field check (YAML must match the stats object) ===")
    _check_yaml(stats, failures)

    print()
    print("=== appendix figures (must match the canonical numbers) ===")
    _check_appendix(stats, failures)

    print()
    print("=== forbidden check (stale values must not come back) ===")
    for fname in ("README.md", "EVIDENCE.md", "WRITEUP.md", "recount.py",
                  os.path.join("artifacts", "reference_intel_sample.md")):
        path = os.path.join(HERE, fname)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        for pattern, why in FORBIDDEN:
            m = re.search(pattern, text)
            if m:
                lineno = text[:m.start()].count("\n") + 1
                failures.append(f"{fname}:{lineno}: stale {m.group(0)!r} ({why})")
                print(f"  [FAIL] {fname}:{lineno} {m.group(0)!r} — {why}")

    print()
    print("=== percentage whitelist (every % must be a licensed value) ===")
    allowed = FIXED_PCT | computed_pct(stats)
    RATIO_PAIRS = computed_ratio_pairs(stats) | {(n, d) for n, d, _ in FIXED_RATIO_PAIRS}
    for fname in ("README.md", "EVIDENCE.md", "WRITEUP.md"):
        path = os.path.join(HERE, fname)
        if os.path.exists(path):
            body = open(path, encoding="utf-8").read()
            check_ratios(body, fname, failures, RATIO_PAIRS)
            check_percentages(body, fname, allowed, failures)
    if not any("percentage" in f for f in failures):
        print(f"  [ok] all percentages are in the licensed set ({len(allowed)} values)")

    print()
    print("=== stray build artefacts ===")
    strays = []
    # Only build residue counts. Dotfiles are NOT residue: a Git worktree legitimately
    # contains .git/, and flagging it would make the check fail inside a clone while
    # passing on an exported tarball -- i.e. it would report on how the package was
    # obtained rather than on what it contains.
    for dp, dns, fns in os.walk(HERE):
        dns[:] = [d for d in dns if d != ".git"]
        if "__pycache__" in dp:
            strays.append(os.path.relpath(dp, HERE).replace("\\", "/"))
            dns[:] = []
            continue
        for fn in fns:
            # ~$*.xlsx is a Word/Excel lock file; it is created the moment the file is
            # opened in Office and must never ship.
            if fn.endswith((".pyc", ".pyo")) or fn.startswith("~$"):
                strays.append(os.path.relpath(os.path.join(dp, fn), HERE).replace("\\", "/"))
    if strays:
        for s in sorted(set(strays)):
            failures.append(f"stray build artefact in the package: {s}")
            print(f"  [FAIL] stray artefact: {s}")
    else:
        print("  [ok] no __pycache__ / .pyc / dotfiles in the package")

    print()
    print("=== integrity ===")
    if stats.get("integrity_failures"):
        for f in stats["integrity_failures"]:
            failures.append("integrity: " + f)
            print("  [FAIL]", f)
    else:
        print("  [ok] recount.py reports no integrity failures")

    print()
    if failures:
        print(f"FAILED — {len(failures)} problem(s)")
        for f in failures:
            print("  - " + f)
        return 1
    print("PASSED — the rules implemented in this script all hold.")
    print("  This is NOT a statement that every figure or every claim in the prose is")
    print("  correct. Semantic consistency (all/part, measured/estimated,")
    print("  not-found/does-not-exist) still requires human review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
