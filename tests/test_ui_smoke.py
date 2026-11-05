"""GUI smoke tests. They are skipped automatically without a display."""

from __future__ import annotations

import tkinter as tk
import unittest

from dgknlabs import core
from dgknlabs.app import App


class UiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            probe = tk.Tk()
            probe.destroy()
        except Exception as error:  # pragma: no cover - depends on environment
            raise unittest.SkipTest(f"Keine grafische Oberfläche verfügbar: {error}")

    def setUp(self) -> None:
        self.app = App()
        self.app.geometry("1200x880+0+0")
        self.app.update_idletasks()
        self.app.update()

    def tearDown(self) -> None:
        try:
            self.app.destroy()
        except tk.TclError:
            pass

    def test_generate_renders_cards_and_copies(self) -> None:
        self.app._count_segment.set_value("3")
        self.app._on_count_change("3")
        self.app.generate()
        self.app.update_idletasks()
        self.app.update()

        self.assertEqual(len(self.app._passwords), 3)
        self.assertEqual(len(self.app._cards), 3)
        self.assertTrue(all(len(pw) == 20 for pw in self.app._passwords))

        self.app._copy_index(0)
        self.assertEqual(self.app.clipboard_get(), self.app._passwords[0])

    def test_mask_toggle_hides_password(self) -> None:
        self.app.generate()
        self.app._mask_toggle.set_value(True, notify=True)
        self.app.update_idletasks()
        self.app.update()
        label = self.app._cards[0]._password_label.cget("text")
        self.assertIn("•", label)
        self.assertNotEqual(label, self.app._passwords[0])

    def test_audit_view_reports_common_password(self) -> None:
        self.app._show_view("audit")
        self.app._audit_entry.set("Passwort123!")
        self.app._refresh_audit()
        self.app.update_idletasks()
        self.assertEqual(self.app._audit_rating.cget("text"), "KRITISCH")

    def test_policy_rejects_empty_class_selection(self) -> None:
        for key in ("lower", "upper", "digits", "symbols"):
            self.app._toggles[key].set_value(False, notify=False)
        self.app._refresh_policy()
        self.assertIn("Zeichenklasse", self.app._summary_label.cget("text"))

    def test_entropy_matches_core(self) -> None:
        self.app.generate()
        expected = core.format_bits(core.entropy_bits(self.app.policy))
        self.assertIn(expected, self.app._summary_label.cget("text"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
