"""promptgate — defensive prompt-injection detector & sanitizer (educational)."""
import re
import unicodedata

PATTERNS = [
    ("ignore_instructions", r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", 5),
    ("disregard_rules", r"disregard\s+(your\s+)?(rules|instructions|guidelines)", 4),
    ("system_override", r"(system\s*prompt|developer\s*message|you\s+are\s+now)", 3),
    ("jailbreak_persona", r"\b(dan|jailbreak|do\s+anything\s+now|skeleton\s+key)\b", 3),
    ("reveal_secret", r"(reveal|print|show|leak)\s+.*(system\s+prompt|instructions|api\s*key|password)", 4),
    ("role_confusion", r"^(assistant|system|developer|user)\s*:", 2),
    ("encoding_smuggle", r"(base64|rot13|hex\s*encoded)\s*[:\-]", 2),
    ("multi_turn_escalation", r"(step\s+\d+|continue\s+from|pretend\s+you\s+already|hypothetically|as\s+an\s+ai\b.*without\s+restrictions)", 2),
    ("indirect_injection", r"(\[system\]|\[assistant\]|<<\s*system|BEGIN\s+INSTRUCTIONS|END\s+OF\s+.*?\s*INSTRUCTIONS)", 4),
]

ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff\u2060"), None)
TAG_CHARS = dict.fromkeys(range(0xE0000, 0xE0080), None)

def strip_invisibles(text: str) -> str:
    return text.translate(ZERO_WIDTH).translate(TAG_CHARS)

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", strip_invisibles(text))
    return re.sub(r"\s+", " ", text).strip()

def score_text(text: str):
    norm = normalize(text).lower()
    hits = []
    total = 0
    for name, pat, weight in PATTERNS:
        if re.search(pat, norm):
            hits.append({"pattern": name, "weight": weight})
            total += weight
    if total >= 5: verdict = "block"
    elif total >= 2: verdict = "review"
    else: verdict = "allow"
    return {"score": total, "verdict": verdict, "hits": hits, "length": len(text)}

def sanitize(text: str) -> str:
    """Spotlighting: quote untrusted content as data, never as instructions."""
    clean = strip_invisibles(text)
    return ('[UNTRUSTED DATA START] ' + clean.replace("]", "") + ' [UNTRUSTED DATA END]')

def analyze_batch(texts):
    return [dict(text=(t[:80] + ("…" if len(t) > 80 else "")), **score_text(t)) for t in texts]

def cmd(argv):
    if not argv: print("usage: promptgate {check|sanitize} TEXT"); return 2
    if argv[0] == "check":
        import json; print(json.dumps(score_text(" ".join(argv[1:])), indent=2)); return 0
    if argv[0] == "sanitize":
        print(sanitize(" ".join(argv[1:]))); return 0
    print(f"unknown command: {argv[0]}"); return 2

def main(argv=None):
    import sys
    return cmd(argv if argv is not None else sys.argv[1:])

if __name__ == "__main__":
    raise SystemExit(main())
