#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Dogukan S.

import math
import secrets
import string
import tkinter as tk
from tkinter import ttk, messagebox


AMBIGUOUS = set("O0oIl1|`'\"{}[]()<>,")
DEFAULT_INCLUDE_AMBIGUOUS = True  # kannst du später im UI als Option erweitern


def strength_label(entropy: float) -> str:
    if entropy < 60:
        return "SCHWACH"
    if entropy < 80:
        return "OK"
    if entropy < 100:
        return "SEHR STARK"
    if entropy < 128:
        return "EXTREM"
    return "OVERKILL"


def seconds_to_human(sec: float) -> str:
    # kompakt, max 2 Einheiten
    units = [
        ("Jahre", 365.25 * 24 * 3600),
        ("Tage", 86400),
        ("Stunden", 3600),
        ("Minuten", 60),
        ("Sekunden", 1),
    ]
    out = []
    for name, size in units:
        if sec >= size:
            v = int(sec // size)
            sec -= v * size
            out.append(f"{v} {name}")
            if len(out) == 2:
                break
    return ", ".join(out) if out else "< 1 Sekunde"


def build_alphabet(include_symbols=True, include_ambiguous=True) -> str:
    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += string.punctuation
    if not include_ambiguous:
        chars = "".join(c for c in chars if c not in AMBIGUOUS)
    return chars


def generate_password(length: int, include_symbols=True, include_ambiguous=True) -> tuple[str, float, int]:
    alphabet = build_alphabet(include_symbols=include_symbols, include_ambiguous=include_ambiguous)
    pw = "".join(secrets.choice(alphabet) for _ in range(length))
    entropy = length * math.log2(len(alphabet))
    return pw, entropy, len(alphabet)


def crack_time_avg(entropy_bits: float, guesses_per_second: float) -> float:
    # average time = 2^(E-1) / rate
    return (2 ** (entropy_bits - 1)) / guesses_per_second


ONLINE_PROFILES = [
    ("Online ohne 2FA (1 Versuch/Sek)", 1.0),
    ("Online ohne 2FA (10 Versuche/Sek)", 10.0),
    ("Online mit Botnetz (10.000 Versuche/Sek)", 1e4),
]

# Moderne Hardware-Werte (Stand 2026, je nach Algorithmus und Optimierung)
OFFLINE_PROFILES = [
    ("Offline Hash (CPU, 2026) 1e9/s", 1e9),
    ("Offline Hash (GPU, 2026) 1e12/s", 1e12),
    ("Offline Hash (ASIC/FPGA) 1e14/s", 1e14),
    ("Offline Hash (Supercomputer) 1e16/s", 1e16),
]


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Password Generator — © Dogukan S.")
        self.geometry("960x660")
        self.minsize(820, 560)

        # Info-Box
        info_frame = ttk.Frame(self, padding=(12, 12, 12, 0))
        info_frame.pack(fill="x")
        info_text = (
            "Knackzeit: Die geschätzte Zeit, die ein Angreifer mit typischer Hardware benötigt, um das Passwort zu erraten. "
            "Online-Angriffe sind langsam, Offline-Angriffe (Hash-Knacken) können extrem schnell sein. "
            "Beispiele zeigen verschiedene Szenarien. Je länger und komplexer das Passwort, desto sicherer!"
        )
        ttk.Label(info_frame, text=info_text, wraplength=900, foreground="#444").pack(anchor="w")

        # Inputs
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="x")

        ttk.Label(frm, text="Passwortlänge:").grid(row=0, column=0, sticky="w")
        self.length_var = tk.StringVar(value="16")
        self.length_entry = ttk.Entry(frm, textvariable=self.length_var, width=10)
        self.length_entry.grid(row=0, column=1, sticky="w", padx=(8, 20))

        ttk.Label(frm, text="Anzahl (1–5):").grid(row=0, column=2, sticky="w")
        self.count_var = tk.StringVar(value="1")
        self.count_combo = ttk.Combobox(frm, textvariable=self.count_var, width=6, values=["1", "2", "3", "4", "5"], state="readonly")
        self.count_combo.grid(row=0, column=3, sticky="w", padx=(8, 20))

        self.symbols_var = tk.BooleanVar(value=True)
        self.symbols_chk = ttk.Checkbutton(frm, text="Sonderzeichen", variable=self.symbols_var)
        self.symbols_chk.grid(row=0, column=4, sticky="w", padx=(0, 16))

        self.ambiguous_var = tk.BooleanVar(value=DEFAULT_INCLUDE_AMBIGUOUS)
        self.amb_chk = ttk.Checkbutton(frm, text="Ambige Zeichen erlauben", variable=self.ambiguous_var)
        self.amb_chk.grid(row=0, column=5, sticky="w")

        self.gen_btn = ttk.Button(frm, text="Generieren", command=self.on_generate)
        self.gen_btn.grid(row=0, column=6, sticky="e", padx=(16, 0))

        frm.columnconfigure(6, weight=1)

        # Output area
        out_frame = ttk.Frame(self, padding=(12, 0, 12, 12))
        out_frame.pack(fill="both", expand=True)

        self.text = tk.Text(out_frame, wrap="word", font=("Consolas", 11))
        self.text.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(out_frame, command=self.text.yview)
        scroll.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scroll.set)

        # Bottom buttons
        bottom = ttk.Frame(self, padding=(12, 0, 12, 12))
        bottom.pack(fill="x")

        self.copy_btn = ttk.Button(bottom, text="Erstes Passwort kopieren", command=self.copy_first_password)
        self.copy_btn.pack(side="left")

        self.clear_btn = ttk.Button(bottom, text="Ausgabe leeren", command=self.clear_output)
        self.clear_btn.pack(side="left", padx=(10, 0))

        # Feld für Passwort-Check (mittig unten)
        check_frame = ttk.Frame(bottom)
        check_frame.pack(side="top", pady=(0, 8))

        ttk.Label(check_frame, text="Passwort prüfen:").pack(side="left")
        self.check_pw_var = tk.StringVar()
        self.check_pw_entry = ttk.Entry(check_frame, textvariable=self.check_pw_var, width=24)
        self.check_pw_entry.pack(side="left", padx=(8, 8))
        self.check_btn = ttk.Button(check_frame, text="Knackzeit berechnen", command=self.on_check_password)
        self.check_btn.pack(side="left")

        self.check_result_label = ttk.Label(check_frame, text="")
        self.check_result_label.pack(side="left", padx=(16, 0))

        # Weltkugel-Icon mit Animation
        globe_frame = ttk.Frame(bottom)
        globe_frame.pack(side="right", padx=(0, 8))

        self.globe_canvas = tk.Canvas(globe_frame, width=28, height=28, highlightthickness=0, bg="#e3f2fd")
        self.globe_canvas.pack(side="left")
        self._globe_angle = 0
        self._last_passwords: list[str] = []
        self._draw_globe()
        self._animate_globe()

        ttk.Label(globe_frame, text="© Dogukan S.").pack(side="left", padx=(4, 0))

        # initial focus
        self.length_entry.focus_set()
        self.length_entry.select_range(0, tk.END)


    def exit_fullscreen(self):
        self.attributes("-fullscreen", False)

    def minimize_window(self):
        self.iconify()

    def close_window(self):
        self.destroy()

        # Style
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 11))
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("Strength.TLabel", font=("Segoe UI", 11, "bold"))

        # Info-Box
        info_frame = ttk.Frame(self, padding=(12, 12, 12, 0))
        info_frame.pack(fill="x")
        info_text = (
            "Knackzeit: Die geschätzte Zeit, die ein Angreifer mit typischer Hardware benötigt, um das Passwort zu erraten. "
            "Online-Angriffe sind langsam, Offline-Angriffe (Hash-Knacken) können extrem schnell sein. "
            "Beispiele zeigen verschiedene Szenarien. Je länger und komplexer das Passwort, desto sicherer!"
        )
        ttk.Label(info_frame, text=info_text, wraplength=900, foreground="#444").pack(anchor="w")

        # Inputs
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="x")

        ttk.Label(frm, text="Passwortlänge:").grid(row=0, column=0, sticky="w")
        self.length_var = tk.StringVar(value="16")
        self.length_entry = ttk.Entry(frm, textvariable=self.length_var, width=10)
        self.length_entry.grid(row=0, column=1, sticky="w", padx=(8, 20))

        ttk.Label(frm, text="Anzahl (1–5):").grid(row=0, column=2, sticky="w")
        self.count_var = tk.StringVar(value="1")
        self.count_combo = ttk.Combobox(frm, textvariable=self.count_var, width=6, values=["1", "2", "3", "4", "5"], state="readonly")
        self.count_combo.grid(row=0, column=3, sticky="w", padx=(8, 20))

        self.symbols_var = tk.BooleanVar(value=True)
        self.symbols_chk = ttk.Checkbutton(frm, text="Sonderzeichen", variable=self.symbols_var)
        self.symbols_chk.grid(row=0, column=4, sticky="w", padx=(0, 16))

        self.ambiguous_var = tk.BooleanVar(value=DEFAULT_INCLUDE_AMBIGUOUS)
        self.amb_chk = ttk.Checkbutton(frm, text="Ambige Zeichen erlauben", variable=self.ambiguous_var)
        self.amb_chk.grid(row=0, column=5, sticky="w")

        self.gen_btn = ttk.Button(frm, text="Generieren", command=self.on_generate)
        self.gen_btn.grid(row=0, column=6, sticky="e", padx=(16, 0))

        frm.columnconfigure(6, weight=1)

        # Output area
        out_frame = ttk.Frame(self, padding=(12, 0, 12, 12))
        out_frame.pack(fill="both", expand=True)

        self.text = tk.Text(out_frame, wrap="word", font=("Consolas", 11))
        self.text.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(out_frame, command=self.text.yview)
        scroll.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scroll.set)

        # Bottom buttons
        bottom = ttk.Frame(self, padding=(12, 0, 12, 12))
        bottom.pack(fill="x")

        self.copy_btn = ttk.Button(bottom, text="Erstes Passwort kopieren", command=self.copy_first_password)
        self.copy_btn.pack(side="left")

        self.clear_btn = ttk.Button(bottom, text="Ausgabe leeren", command=self.clear_output)
        self.clear_btn.pack(side="left", padx=(10, 0))

        # Feld für Passwort-Check (mittig unten)
        check_frame = ttk.Frame(bottom)
        check_frame.pack(side="top", pady=(0, 8))

        ttk.Label(check_frame, text="Passwort prüfen:").pack(side="left")
        self.check_pw_var = tk.StringVar()
        self.check_pw_entry = ttk.Entry(check_frame, textvariable=self.check_pw_var, width=24)
        self.check_pw_entry.pack(side="left", padx=(8, 8))
        self.check_btn = ttk.Button(check_frame, text="Knackzeit berechnen", command=self.on_check_password)
        self.check_btn.pack(side="left")

        self.check_result_label = ttk.Label(check_frame, text="")
        self.check_result_label.pack(side="left", padx=(16, 0))

        # Weltkugel-Icon mit Animation
        globe_frame = ttk.Frame(bottom)
        globe_frame.pack(side="right", padx=(0, 8))

        self.globe_canvas = tk.Canvas(globe_frame, width=28, height=28, highlightthickness=0, bg="#e3f2fd")
        self.globe_canvas.pack(side="left")
        self._globe_angle = 0
        self._last_passwords: list[str] = []
        self._draw_globe()
        self._animate_globe()

        ttk.Label(globe_frame, text="© Dogukan S.").pack(side="left", padx=(4, 0))

        # initial focus
        self.length_entry.focus_set()
        self.length_entry.select_range(0, tk.END)

    def on_check_password(self):
        pw = self.check_pw_var.get()
        if not pw:
            self.check_result_label.config(text="Bitte Passwort eingeben.", foreground="#d32f2f")
            return
        # Alphabet schätzen
        alpha = 0
        if any(c in string.ascii_lowercase for c in pw):
            alpha += 26
        if any(c in string.ascii_uppercase for c in pw):
            alpha += 26
        if any(c in string.digits for c in pw):
            alpha += 10
        if any(c in string.punctuation for c in pw):
            alpha += len(string.punctuation)
        if alpha < 2:
            self.check_result_label.config(text="Zu wenig Zeichenvielfalt.", foreground="#d32f2f")
            return
        entropy = len(pw) * math.log2(alpha)
        result = f"Entropie: {entropy:.1f} Bit\n"
        for name, rate in ONLINE_PROFILES + OFFLINE_PROFILES:
            avg = crack_time_avg(entropy, rate)
            result += f"{name}: {seconds_to_human(avg)}\n"
        self.check_result_label.config(text=result, foreground="#1976d2")

    def _draw_globe(self):
        self.globe_canvas.delete("all")
        r = 12
        cx, cy = 14, 14
        # Kreis
        self.globe_canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#1976d2", width=2, fill="#e3f2fd")
        # Längengrad (drehend)
        angle = self._globe_angle
        for i in range(-1, 2):
            a = math.radians(angle + i * 30)
            x = cx + r * math.sin(a)
            self.globe_canvas.create_line(x, cy - r * 0.8, x, cy + r * 0.8, fill="#1976d2", width=2)
        # Breitengrad
        self.globe_canvas.create_arc(cx - r, cy - r * 0.7, cx + r, cy + r * 0.7, start=0, extent=180, outline="#1976d2", style="arc", width=2)
        self.globe_canvas.create_arc(cx - r, cy - r * 0.7, cx + r, cy + r * 0.7, start=180, extent=180, outline="#1976d2", style="arc", width=2)

    def _animate_globe(self):
        self._globe_angle = (self._globe_angle + 8) % 360
        self._draw_globe()
        self.after(80, self._animate_globe)

    def clear_output(self):
        self.text.delete("1.0", tk.END)
        self._last_passwords = []

    def copy_first_password(self):
        if not self._last_passwords:
            messagebox.showinfo("Hinweis", "Noch nichts generiert.")
            return
        self.clipboard_clear()
        self.clipboard_append(self._last_passwords[0])
        messagebox.showinfo("Kopiert", "Erstes Passwort wurde in die Zwischenablage kopiert.")

    def on_generate(self):
        # Validate input
        try:
            length = int(self.length_var.get().strip())
        except ValueError:
            messagebox.showerror("Fehler", "Passwortlänge muss eine Zahl sein.")
            return

        if length < 8 or length > 256:
            messagebox.showerror("Fehler", "Passwortlänge muss zwischen 8 und 256 liegen.")
            return

        try:
            count = int(self.count_var.get().strip())
        except ValueError:
            messagebox.showerror("Fehler", "Anzahl muss eine Zahl sein.")
            return

        if count < 1 or count > 5:
            messagebox.showerror("Fehler", "Anzahl muss zwischen 1 und 5 liegen.")
            return

        include_symbols = bool(self.symbols_var.get())
        include_ambiguous = bool(self.ambiguous_var.get())

        self.clear_output()

        self.text.insert(tk.END, "Password Generator (GUI)\n")
        self.text.insert(tk.END, "Online-Login ohne 2FA + Offline-Hash Einordnung (Schätzung)\n")
        self.text.insert(tk.END, "-" * 72 + "\n\n")

        passwords = []
        for i in range(count):
            pw, ent, alpha = generate_password(length, include_symbols=include_symbols, include_ambiguous=include_ambiguous)
            passwords.append(pw)

            # Stärke farbig hervorheben
            strength = strength_label(ent)
            color = {
                "SCHWACH": "#d32f2f",
                "OK": "#fbc02d",
                "SEHR STARK": "#388e3c",
                "EXTREM": "#1976d2",
                "OVERKILL": "#6a1b9a"
            }.get(strength, "#333")

            self.text.insert(tk.END, f"[{i+1}] PASSWORT : {pw}\n")
            self.text.insert(tk.END, f"    ENTROPIE : {ent:.1f} Bit\n")
            self.text.insert(tk.END, f"    STÄRKE   : ")
            self.text.insert(tk.END, f"{strength}\n", (strength,))
            self.text.tag_config(strength, foreground=color, font=("Segoe UI", 11, "bold"))

            self.text.insert(tk.END, "    Knackzeit (Ø, grob):\n")
            for name, rate in ONLINE_PROFILES:
                avg = crack_time_avg(ent, rate)
                self.text.insert(tk.END, f"      - {name}: {seconds_to_human(avg)}\n")
            for name, rate in OFFLINE_PROFILES:
                avg = crack_time_avg(ent, rate)
                self.text.insert(tk.END, f"      - {name}: {seconds_to_human(avg)}\n")

            self.text.insert(tk.END, "\n")

        self.text.insert(tk.END, "-" * 72 + "\n")
        self.text.insert(tk.END, "© Dogukan S.\n")

        self._last_passwords = passwords


if __name__ == "__main__":
    app = App()
    app.mainloop()
