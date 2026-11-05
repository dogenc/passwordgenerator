"""Unit tests for the cryptographic core (no display required)."""

import math
import unittest

from dgknlabs import core


class PolicyTests(unittest.TestCase):
    def test_default_policy_is_valid(self):
        policy = core.build_policy()
        policy.validate()
        self.assertEqual(policy.length, 20)
        self.assertGreater(len(policy.alphabet()), 70)

    def test_rejects_short_and_long_lengths(self):
        for length in (0, 7, 257):
            with self.assertRaises(core.PolicyError):
                core.build_policy(length=length)

    def test_rejects_empty_class_selection(self):
        with self.assertRaises(core.PolicyError):
            core.build_policy(lowercase=False, uppercase=False, digits=False,
                              symbols=False)

    def test_ambiguous_filter_removes_chars(self):
        policy = core.build_policy(exclude_ambiguous=True)
        self.assertFalse(set(policy.alphabet()) & core.AMBIGUOUS)
        unfiltered = core.build_policy(exclude_ambiguous=False)
        self.assertTrue(set(unfiltered.alphabet()) & core.AMBIGUOUS)

    def test_class_sizes_add_up(self):
        policy = core.build_policy(length=32)
        self.assertEqual(sum(size for _, size in policy.class_sizes()),
                         len(policy.alphabet()))

    def test_minimum_length_with_all_classes_is_valid(self):
        policy = core.build_policy(
            length=8, lowercase=True, uppercase=True, digits=True,
            symbols=True, require_each_class=True,
        )
        password = core.generate(policy)
        self.assertEqual(len(password), 8)
        for _, chars in policy.classes():
            self.assertTrue(any(c in chars for c in password))


class EntropyTests(unittest.TestCase):
    def test_inclusion_exclusion_matches_enumeration(self):
        # 4 characters, 2 classes of 2, length 4 -> 4^4 - 2*2^4 = 224.
        self.assertEqual(core.constrained_keyspace([2, 2], 4), 224)
        self.assertEqual(core.constrained_keyspace([2, 2], 1), 0)
        self.assertEqual(core.constrained_keyspace([5], 3), 125)

    def test_keyspace_matches_policy(self):
        policy = core.build_policy(length=24)
        sizes = [size for _, size in policy.class_sizes()]
        self.assertEqual(core.keyspace(policy),
                         core.constrained_keyspace(sizes, policy.length))

    def test_entropy_below_naive_upper_bound(self):
        policy = core.build_policy(length=16)
        naive = policy.length * math.log2(len(policy.alphabet()))
        self.assertLess(core.entropy_bits(policy), naive)
        self.assertGreater(core.entropy_bits(policy), naive - 2)

    def test_free_keyspace(self):
        policy = core.build_policy(length=10, require_each_class=False)
        expected = 10 * math.log2(len(policy.alphabet()))
        self.assertAlmostEqual(core.entropy_bits(policy), expected, places=6)


class GenerationTests(unittest.TestCase):
    def test_length_and_alphabet(self):
        policy = core.build_policy(length=24, exclude_ambiguous=True)
        for password in core.generate_many(policy, 5):
            self.assertEqual(len(password), 24)
            self.assertLessEqual(set(password), set(policy.alphabet()))

    def test_every_selected_class_present(self):
        policy = core.build_policy(length=12)
        classes = [chars for _, chars in policy.classes()]
        for password in core.generate_many(policy, 5):
            for chars in classes:
                self.assertTrue(any(c in chars for c in password))

    def test_disabled_class_never_appears(self):
        policy = core.build_policy(length=32, digits=False, symbols=False)
        joined = "".join(core.generate_many(policy, 5))
        self.assertFalse(any(c in "0123456789" for c in joined))
        self.assertFalse(set(joined) & set(core.SYMBOLS))

    def test_batch_bounds(self):
        policy = core.build_policy()
        with self.assertRaises(core.PolicyError):
            core.generate_many(policy, 0)
        with self.assertRaises(core.PolicyError):
            core.generate_many(policy, core.MAX_BATCH + 1)

    def test_generated_passwords_are_distinct(self):
        policy = core.build_policy(length=20)
        passwords = core.generate_many(policy, 5)
        self.assertEqual(len(set(passwords)), 5)

    def test_exactly_minimum_length(self):
        # 8 chars and 4 required classes is the tightest valid policy.
        policy = core.build_policy(length=8)
        for password in core.generate_many(policy, 5):
            self.assertEqual(len(password), 8)


class RatingAndTimeTests(unittest.TestCase):
    def test_rating_bands_are_ordered(self):
        ratings = core.RATINGS
        for current, previous in zip(ratings, ratings[1:]):
            self.assertGreater(current.min_bits, previous.min_bits)
        self.assertEqual(core.rating_for(0).label, "KRITISCH")
        self.assertEqual(core.rating_for(500).label, "MAXIMAL")

    def test_time_formatting_is_monotonic(self):
        short = core.format_crack_time(40, 1e12)
        long = core.format_crack_time(140, 1e12)
        self.assertNotEqual(short, long)
        self.assertIn("sofort", core.format_crack_time(0, 1e12))

    def test_time_does_not_overflow(self):
        text = core.format_crack_time(1000, 1e15)
        self.assertIn("Jahre", text)
        self.assertIn("10^", text)

    def test_human_units(self):
        self.assertEqual(core.format_log10_duration(math.log10(30)), "30 Sekunden")
        self.assertEqual(core.format_log10_duration(math.log10(3600)), "1 Stunde")
        self.assertEqual(core.format_log10_duration(math.log10(120)), "2 Minuten")
        self.assertEqual(core.format_log10_duration(math.log10(86400)), "1 Tag")
        self.assertEqual(core.format_log10_duration(math.log10(2 * 86400)), "2 Tage")


class AuditTests(unittest.TestCase):
    def test_common_password_is_flagged(self):
        self.assertTrue(core.audit_password("Passwort123!").dictionary_hit)
        self.assertTrue(core.audit_password("qwertz").dictionary_hit)

    def test_strong_random_password_passes_requirements(self):
        password = core.generate(core.build_policy(length=24))
        report = core.audit_password(password)
        self.assertTrue(all(item.passed for item in report.requirements))

    def test_sequences_and_repeats_are_detected(self):
        self.assertTrue(any("Sequenz" in f.text
                            for f in core.audit_password("Xy7!abcdZ2#q").findings))
        self.assertTrue(any("wiederholung" in f.text.lower()
                            for f in core.audit_password("Xy7!aaabZ2#q").findings))

    def test_short_password_is_critical(self):
        self.assertEqual(core.audit_password("Ab1!").rating.label, "KRITISCH")

    def test_empty_password_is_safe(self):
        report = core.audit_password("")
        self.assertEqual(report.effective_bits, 0)
        self.assertEqual(report.rating.label, "KRITISCH")

    def test_effective_bits_never_exceed_raw(self):
        for password in ("Sommer2024!", "aB3$xyzQ", "aaaaaaaa", "P@ssw0rd!"):
            report = core.audit_password(password)
            self.assertLessEqual(report.effective_bits, report.raw_bits + 1e-9)


class MaskingAndSelfTest(unittest.TestCase):
    def test_masking_keeps_length(self):
        password = "S3hrGeheim!2026"
        hidden = core.masked(password)
        self.assertEqual(len(hidden), len(password))
        self.assertNotIn("Geheim", hidden)

    def test_short_input_is_fully_masked(self):
        self.assertEqual(core.masked("abc"), "•••")

    def test_self_test_passes(self):
        ok, lines = core.self_test()
        self.assertTrue(ok, "\n".join(lines))


if __name__ == "__main__":
    unittest.main(verbosity=2)
