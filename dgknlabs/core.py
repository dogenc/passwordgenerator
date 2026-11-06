"""DGKN@Labs PWGen — cryptographic core.

This module contains every security-relevant decision: the character policy,
the generation routine, the exact entropy of the constrained keyspace, the
attacker model and the audit heuristics.  It has no UI imports so it can be
tested and audited headlessly.

Design notes
------------
* Randomness comes from :mod:`secrets` (``SystemRandom`` -> OS CSPRNG).
* ``require_each_class`` uses rejection sampling, which keeps the output
  uniform over the set of passwords that satisfy the policy.  The entropy
  calculation uses inclusion-exclusion over that same set, so the displayed
  bit strength is exact rather than an optimistic upper bound.
* Nothing in this module writes a password to disk, a log or a network
  socket, and there is deliberately no code path that does.
"""

from __future__ import annotations

import math
import re
import secrets
import string
from dataclasses import dataclass
from typing import Sequence

APP_NAME = "PWGen"
APP_VERSION = "2.0.0"
VENDOR = "DGKN@Labs"

MIN_LENGTH = 8
MAX_LENGTH = 256
MAX_BATCH = 5

# Symbols intentionally omit quotes, backslashes and whitespace: they break
# shell, CSV and URL round-trips without contributing meaningful strength.
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?/|~"
AMBIGUOUS = frozenset("O0oIl1|`'\"{}[]()<>/\\")

_LEET = str.maketrans(
    {
        "0": "o",
        "1": "l",
        "2": "z",
        "3": "e",
        "4": "a",
        "5": "s",
        "6": "g",
        "7": "t",
        "8": "b",
        "9": "g",
        "@": "a",
        "$": "s",
        "!": "i",
        "+": "t",
    }
)


class PolicyError(ValueError):
    """Raised when a character policy cannot produce a valid password."""


# --------------------------------------------------------------------------
# Policy
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Policy:
    """A validated description of the password keyspace."""

    length: int = 20
    lowercase: bool = True
    uppercase: bool = True
    digits: bool = True
    symbols: bool = True
    exclude_ambiguous: bool = True
    require_each_class: bool = True

    def validate(self) -> None:
        if not isinstance(self.length, int):
            raise PolicyError("Die Länge muss eine ganze Zahl sein.")
        if not MIN_LENGTH <= self.length <= MAX_LENGTH:
            raise PolicyError(
                f"Die Länge muss zwischen {MIN_LENGTH} und {MAX_LENGTH} Zeichen liegen."
            )
        classes = self.classes()
        if not classes:
            raise PolicyError("Mindestens eine Zeichenklasse muss aktiv sein.")
        for name, chars in classes:
            if not chars:
                raise PolicyError(
                    f"Die Klasse „{name}“ ist nach dem Ausschluss ambiger Zeichen leer."
                )
        if self.require_each_class and self.length < len(classes):
            raise PolicyError(
                "Die Länge ist kürzer als die Anzahl geforderter Zeichenklassen."
            )

    def classes(self) -> tuple[tuple[str, str], ...]:
        """Return (label, characters) pairs in a stable order."""

        candidates: list[tuple[str, str, bool]] = [
            ("Kleinbuchstaben", string.ascii_lowercase, self.lowercase),
            ("Großbuchstaben", string.ascii_uppercase, self.uppercase),
            ("Ziffern", string.digits, self.digits),
            ("Sonderzeichen", SYMBOLS, self.symbols),
        ]
        result: list[tuple[str, str]] = []
        for label, chars, enabled in candidates:
            if not enabled:
                continue
            if self.exclude_ambiguous:
                chars = "".join(c for c in chars if c not in AMBIGUOUS)
            if chars:
                result.append((label, chars))
        return tuple(result)

    def alphabet(self) -> str:
        return "".join(chars for _, chars in self.classes())

    def class_sizes(self) -> tuple[tuple[str, int], ...]:
        return tuple((label, len(chars)) for label, chars in self.classes())

    def with_length(self, length: int) -> "Policy":
        return Policy(
            length=length,
            lowercase=self.lowercase,
            uppercase=self.uppercase,
            digits=self.digits,
            symbols=self.symbols,
            exclude_ambiguous=self.exclude_ambiguous,
            require_each_class=self.require_each_class,
        )


def build_policy(**kwargs: object) -> Policy:
    """Build and validate a policy in one step."""

    policy = Policy(**kwargs)  # type: ignore[arg-type]
    policy.validate()
    return policy


# --------------------------------------------------------------------------
# Keyspace and entropy
# --------------------------------------------------------------------------


def constrained_keyspace(class_sizes: Sequence[int], length: int) -> int:
    """Number of length-``length`` strings containing every class at least once.

    Inclusion-exclusion over the classes:
    ``sum_S (-1)^|S| * (N - sum_{i in S} n_i) ** length``.
    Exact integer arithmetic, no floating point involved.
    """

    sizes = [n for n in class_sizes if n > 0]
    total = sum(sizes)
    count = 0
    for mask in range(1 << len(sizes)):
        omitted = 0
        bits = 0
        for index, size in enumerate(sizes):
            if mask & (1 << index):
                omitted += size
                bits += 1
        remaining = total - omitted
        if remaining <= 0:
            continue
        term = remaining**length
        count += -term if bits % 2 else term
    return max(count, 0)


def keyspace(policy: Policy) -> int:
    policy.validate()
    length = policy.length
    class_sizes = [len(chars) for _, chars in policy.classes()]
    if policy.require_each_class:
        return constrained_keyspace(class_sizes, length)
    return sum(class_sizes) ** length


def entropy_bits(policy: Policy) -> float:
    space = keyspace(policy)
    return math.log2(space) if space > 1 else 0.0


# --------------------------------------------------------------------------
# Generation
# --------------------------------------------------------------------------


def generate(policy: Policy, rng: secrets.SystemRandom | None = None) -> str:
    """Generate one password that satisfies ``policy``.

    With ``require_each_class`` the sampler rejects candidates that miss a
    class, which yields a uniform distribution over the constrained keyspace.
    The constructive fallback only triggers for pathological policies where
    rejection would take impractically long; it is still cryptographically
    strong, just not perfectly uniform.
    """

    policy.validate()
    random = rng or secrets.SystemRandom()
    alphabet = policy.alphabet()
    classes = [chars for _, chars in policy.classes()]
    if not policy.require_each_class:
        return "".join(random.choice(alphabet) for _ in range(policy.length))

    required = set("".join(classes))
    for _ in range(4096):
        candidate = "".join(random.choice(alphabet) for _ in range(policy.length))
        if required <= set(candidate):
            return candidate

    # Fallback: one guaranteed character per class, the rest drawn freely.
    chars = [random.choice(chars) for chars in classes]
    chars.extend(random.choice(alphabet) for _ in range(policy.length - len(chars)))
    random.shuffle(chars)
    return "".join(chars)


def generate_many(
    policy: Policy, count: int, rng: secrets.SystemRandom | None = None
) -> list[str]:
    if not 1 <= count <= MAX_BATCH:
        raise PolicyError(f"Die Anzahl muss zwischen 1 und {MAX_BATCH} liegen.")
    results: list[str] = []
    seen: set[str] = set()
    attempts = 0
    while len(results) < count and attempts < count * 64:
        attempts += 1
        candidate = generate(policy, rng)
        if candidate not in seen:
            seen.add(candidate)
            results.append(candidate)
    if len(results) < count:  # practically unreachable, but never return short
        raise RuntimeError("Es konnten nicht genügend eindeutige Passwörter erzeugt werden.")
    return results


# --------------------------------------------------------------------------
# Ratings and attacker model
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Rating:
    label: str
    tone: str
    min_bits: float


RATINGS: tuple[Rating, ...] = (
    Rating("MAXIMAL", "accent", 130.0),
    Rating("EXZELLENT", "accent", 110.0),
    Rating("STARK", "ok", 90.0),
    Rating("SOLIDE", "info", 70.0),
    Rating("SCHWACH", "warn", 50.0),
    Rating("KRITISCH", "danger", 0.0),
)


def rating_for(bits: float) -> Rating:
    for rating in RATINGS:
        if bits >= rating.min_bits:
            return rating
    return RATINGS[-1]


@dataclass(frozen=True)
class AttackerProfile:
    key: str
    label: str
    rate: float
    note: str


# Guesses per second, average-case model: 2**(H-1) / rate.
# Deliberately conservative: a fast hash on a GPU cluster is assumed for the
# "offline" rows so the tool never overstates protection.
PROFILES: tuple[AttackerProfile, ...] = (
    AttackerProfile(
        "online-limited",
        "Online · Rate-Limit",
        10.0,
        "Login mit Sperre, 10 Versuche/s",
    ),
    AttackerProfile(
        "online-open",
        "Online · ungedrosselt",
        1e3,
        "API ohne Sperre, 1 000 Versuche/s",
    ),
    AttackerProfile(
        "kdf",
        "Offline · KDF-Hash",
        1e4,
        "Argon2id/bcrypt, 10 000 Versuche/s",
    ),
    AttackerProfile(
        "gpu",
        "Offline · GPU-Cluster",
        1e12,
        "schneller Hash, 10¹² Versuche/s",
    ),
    AttackerProfile(
        "cluster",
        "Offline · Rechenzentrum",
        1e15,
        "schneller Hash, 10¹⁵ Versuche/s",
    ),
)

_SECONDS_PER_YEAR = 365.25 * 24 * 3600


def crack_time_log10_seconds(bits: float, rate: float) -> float:
    """log10 of the average time to guess, without float overflow."""

    if bits <= 0:
        return float("-inf")
    return (bits - 1) * math.log10(2) - math.log10(rate)


def _de_int(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def _unit(value: int, singular: str, plural: str) -> str:
    return f"{_de_int(value)} {singular if value == 1 else plural}"


def format_log10_duration(log10_seconds: float) -> str:
    """Human readable German duration from a log10 seconds value."""

    if log10_seconds == float("-inf"):
        return "sofort"
    if log10_seconds < 0:
        return "< 1 Sekunde"
    if log10_seconds < math.log10(60):
        return _unit(round(10**log10_seconds), "Sekunde", "Sekunden")
    if log10_seconds < math.log10(3600):
        return _unit(round(10**log10_seconds / 60), "Minute", "Minuten")
    if log10_seconds < math.log10(86400):
        return _unit(round(10**log10_seconds / 3600), "Stunde", "Stunden")
    if log10_seconds < math.log10(365.25 * 86400):
        return _unit(round(10**log10_seconds / 86400), "Tag", "Tage")

    log10_years = log10_seconds - math.log10(_SECONDS_PER_YEAR)
    if log10_years < 3:
        return _unit(round(10**log10_years), "Jahr", "Jahre")
    if log10_years < 6:
        return f"{10 ** (log10_years - 3):.1f} Tsd. Jahre".replace(".", ",")
    if log10_years < 9:
        return f"{10 ** (log10_years - 6):.1f} Mio. Jahre".replace(".", ",")
    if log10_years < 12:
        return f"{10 ** (log10_years - 9):.1f} Mrd. Jahre".replace(".", ",")
    if log10_years < 15:
        return f"{10 ** (log10_years - 12):.1f} Bio. Jahre".replace(".", ",")
    return f"10^{log10_years:.0f} Jahre"


def format_crack_time(bits: float, rate: float) -> str:
    return format_log10_duration(crack_time_log10_seconds(bits, rate))


def format_bits(bits: float) -> str:
    return f"{bits:.1f} Bit".replace(".", ",")


# --------------------------------------------------------------------------
# Audit of user-supplied passwords
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    text: str
    severity: str  # "danger" | "warn" | "info"
    penalty: float = 0.0


@dataclass(frozen=True)
class Requirement:
    key: str
    label: str
    passed: bool


@dataclass(frozen=True)
class AuditReport:
    length: int
    pool: int
    raw_bits: float
    effective_bits: float
    findings: tuple[Finding, ...]
    requirements: tuple[Requirement, ...]
    rating: Rating

    @property
    def dictionary_hit(self) -> bool:
        return any(f.text == DICTIONARY_FINDING for f in self.findings)


DICTIONARY_FINDING = "Bekanntes Passwort oder Wörterbuchbegriff erkannt"

_KEYBOARD_ROWS = (
    "qwertzuiop",
    "asdfghjkl",
    "yxcvbnm",
    "1234567890",
    "!@#$%^&*()",
)


def class_count(password: str) -> int:
    """Number of distinct character classes present in a password."""

    return sum(
        (
            any(c.islower() and c.isascii() for c in password),
            any(c.isupper() and c.isascii() for c in password),
            any(c.isdigit() and c.isascii() for c in password),
            any((not c.isalnum()) and (not c.isspace()) for c in password),
        )
    )


def _pool_size(password: str) -> int:
    pool = 0
    if any(c in string.ascii_lowercase for c in password):
        pool += 26
    if any(c in string.ascii_uppercase for c in password):
        pool += 26
    if any(c in string.digits for c in password):
        pool += 10
    if any(c in SYMBOLS + string.punctuation for c in password):
        pool += len(SYMBOLS)
    if " " in password:
        pool += 1
    if any(ord(c) > 127 for c in password):
        pool += 100
    return pool


def _normalise(password: str) -> str:
    folded = password.lower().translate(_LEET)
    return "".join(c for c in folded if c.isalpha())


def _has_run(password: str, length: int) -> bool:
    lowered = password.lower()
    for start in range(len(lowered) - length + 1):
        chunk = [ord(c) for c in lowered[start : start + length]]
        if all(b - a == 1 for a, b in zip(chunk, chunk[1:])):
            return True
        if all(a - b == 1 for a, b in zip(chunk, chunk[1:])):
            return True
    return False


def _has_repeat(password: str) -> bool:
    return any(password[index] == password[index + 1] == password[index + 2]
               for index in range(len(password) - 2))


def _has_keyboard_run(password: str) -> bool:
    lowered = password.lower()
    for row in _KEYBOARD_ROWS:
        for start in range(len(row) - 3):
            block = row[start : start + 4]
            if block in lowered or block[::-1] in lowered:
                return True
    return False


def _is_known(password: str) -> bool:
    from .wordlist import COMMON_PASSWORDS

    if password.lower() in COMMON_PASSWORDS:
        return True
    normalised = _normalise(password)
    if normalised in COMMON_PASSWORDS:
        return True
    if 4 <= len(normalised) <= 32:
        return any(len(word) >= 6 and word in normalised for word in COMMON_PASSWORDS)
    return False


def audit_password(password: str) -> AuditReport:
    """Heuristic strength audit for an existing password.

    The result is intentionally labelled as an upper bound in the UI: it
    estimates the keyspace implied by the observed character pool and then
    subtracts for structural patterns.  It cannot see breaches, reuse or
    phishing, and it is not a substitute for a full estimator.
    """

    length = len(password)
    pool = _pool_size(password)
    raw_bits = length * math.log2(pool) if pool >= 2 and length else 0.0

    findings: list[Finding] = []
    penalty = 0.0

    if length == 0:
        findings.append(Finding("Kein Passwort eingegeben", "danger"))
    else:
        if length < 8:
            findings.append(Finding("Sehr kurz — unter 8 Zeichen", "danger", 20.0))
            penalty += 20.0
        elif length < 12:
            findings.append(Finding("Kurz — unter 12 Zeichen", "warn", 8.0))
            penalty += 8.0

        classes = class_count(password)
        if classes < 3:
            findings.append(
                Finding(f"Nur {classes} Zeichenklasse(n) verwendet", "warn", 8.0)
            )
            penalty += 8.0

        if len(set(password)) <= max(1, length // 2) and length > 4:
            findings.append(Finding("Geringe Zeichenvielfalt", "warn", 6.0))
            penalty += 6.0

        if _has_repeat(password):
            findings.append(Finding("Zeichenwiederholungen (z. B. „aaa“)", "warn", 8.0))
            penalty += 8.0

        if _has_run(password, 4):
            findings.append(Finding("Sequenzielle Zeichenfolge erkannt", "warn", 10.0))
            penalty += 10.0

        if _has_keyboard_run(password):
            findings.append(Finding("Tastaturmuster erkannt", "warn", 10.0))
            penalty += 10.0

        if re.search(r"(19|20)\d{2}", password):
            findings.append(Finding("Jahreszahl enthalten", "warn", 6.0))
            penalty += 6.0

        if _is_known(password):
            findings.append(Finding(DICTIONARY_FINDING, "danger", 0.0))

    effective = raw_bits
    if any(f.text == DICTIONARY_FINDING for f in findings):
        effective = min(effective, 12.0)
    effective = max(0.0, effective - penalty)

    if not findings and length:
        findings.append(Finding("Keine strukturellen Schwächen erkannt", "info"))

    requirements = (
        Requirement("length", "Mindestens 12 Zeichen", length >= 12),
        Requirement("classes", "Mindestens 3 Zeichenklassen", class_count(password) >= 3),
        Requirement("distinct", "Mindestens 8 verschiedene Zeichen", len(set(password)) >= 8),
        Requirement("known", "Nicht in Standardlisten enthalten", not _is_known(password) if password else False),
        Requirement("sequence", "Keine langen Zeichenfolgen", not _has_run(password, 4) if password else False),
    )

    return AuditReport(
        length=length,
        pool=pool,
        raw_bits=raw_bits,
        effective_bits=effective,
        findings=tuple(findings),
        requirements=requirements,
        rating=rating_for(effective),
    )


def masked(password: str, visible: int = 4) -> str:
    """Mask a password for shoulder-surfing protection."""

    if len(password) <= visible + 2:
        return "•" * len(password)
    return f"{password[:visible]}{'•' * (len(password) - visible - 2)}{password[-2:]}"


# --------------------------------------------------------------------------
# Headless self-test (used by the executable smoke test and CI)
# --------------------------------------------------------------------------


def self_test() -> tuple[bool, list[str]]:
    messages: list[str] = []

    def check(name: str, condition: bool) -> None:
        messages.append(("PASS  " if condition else "FAIL  ") + name)

    # Exact enumeration check on a synthetic keyspace: 2 + 2 characters,
    # length 4, both classes required -> 4^4 - 2*2^4 = 224.
    check("Inklusion-Exklusion (2+2 Zeichen, Länge 4)", constrained_keyspace([2, 2], 4) == 224)
    check("Inklusion-Exklusion (eine Klasse)", constrained_keyspace([5], 3) == 125)
    check("Leerer Schlüsselraum wird erkannt", constrained_keyspace([2, 2], 1) == 0)

    policy = build_policy(length=16)
    sizes = [len(chars) for _, chars in policy.classes()]
    check("Policy-Schlüsselraum konsistent", keyspace(policy) == constrained_keyspace(sizes, 16))

    sample = generate_many(policy, 5)
    check("Batch-Länge", len(sample) == 5)
    check("Eindeutigkeit", len(set(sample)) == 5)
    check("Zeichen im Alphabet", all(set(pw) <= set(policy.alphabet()) for pw in sample))
    classes = [chars for _, chars in policy.classes()]
    check(
        "Alle Zeichenklassen abgedeckt",
        all(all(any(c in chars for c in pw) for chars in classes) for pw in sample),
    )
    check("Exakte Entropie positiv", entropy_bits(policy) > 90)

    strict = build_policy(length=24, exclude_ambiguous=True)
    check("Keine ambigen Zeichen", not (set("".join(generate_many(strict, 5))) & AMBIGUOUS))

    report = audit_password("Passwort123!")
    check("Audit erkennt Standardpasswort", report.dictionary_hit)
    check("Audit bewertet Kurzpasswort kritisch", audit_password("Ab1!").rating.label == "KRITISCH")
    check("Maskierung verbirgt Inhalt", "•" in masked("S3hrGeheim!"))

    ok = all(line.startswith("PASS") for line in messages)
    return ok, messages
