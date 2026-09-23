"""LFSR Simulator - a simple desktop GUI for a Fibonacci Linear Feedback Shift Register.

Run directly with:
    python3 lfsr_gui.py

Package as a standalone executable with PyInstaller (run ON the target OS,
PyInstaller does not cross-compile):
    pip install pyinstaller
    pyinstaller --onefile --windowed --name LFSR_Simulator lfsr_gui.py
The executable will be in the generated dist/ folder.
"""

import tkinter as tk
from tkinter import ttk, messagebox

BG = "#0f172a"
PANEL = "#1e293b"
BORDER = "#334155"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
ONE_BIT = "#0369a1"
OUTPUT_COLOR = "#4ade80"

DEFAULT_TAPS = {
    4: [4, 3],
    8: [8, 6, 5, 4],
    16: [16, 15, 13, 4],
    32: [32, 22, 2, 1],
}

MAX_OUTPUT_CHARS = 2048


class LFSRApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LFSR Simulator")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.length = tk.IntVar(value=8)
        self.seed_var = tk.StringVar()
        self.speed_var = tk.IntVar(value=250)
        self.tap_vars = {}

        self.register = []
        self.step_count = 0
        self.output_bits = ""
        self.running = False
        self._run_job = None

        self._build_ui()
        self._setup(8)

    # ---------- UI construction ----------

    def _build_ui(self):
        pad = {"padx": 16, "pady": 8}

        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=20, pady=(20, 0))
        tk.Label(header, text="LFSR Simulator", font=("Segoe UI", 18, "bold"),
                  bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(header, text="A simple Fibonacci Linear Feedback Shift Register",
                  font=("Segoe UI", 10), bg=BG, fg=MUTED).pack(anchor="w")

        controls = tk.Frame(self, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        controls.pack(fill="x", padx=20, pady=12)

        row1 = tk.Frame(controls, bg=PANEL)
        row1.pack(fill="x", **pad)

        tk.Label(row1, text="Register length", bg=PANEL, fg=MUTED,
                  font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        length_menu = ttk.Combobox(row1, values=[4, 8, 16, 32], state="readonly",
                                    textvariable=self.length, width=8)
        length_menu.grid(row=1, column=0, sticky="w", padx=(0, 24))
        length_menu.bind("<<ComboboxSelected>>", lambda e: self._on_length_change())

        tk.Label(row1, text="Seed (binary)", bg=PANEL, fg=MUTED,
                  font=("Segoe UI", 9)).grid(row=0, column=1, sticky="w")
        seed_entry = tk.Entry(row1, textvariable=self.seed_var, width=36,
                               bg=BG, fg=TEXT, insertbackground=TEXT,
                               relief="flat", font=("Consolas", 10))
        seed_entry.grid(row=1, column=1, sticky="w")
        seed_entry.bind("<Return>", lambda e: self._on_seed_change())
        seed_entry.bind("<FocusOut>", lambda e: self._on_seed_change())

        tk.Label(controls, text="Tap positions (feedback polynomial)", bg=PANEL,
                  fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=16)
        self.taps_frame = tk.Frame(controls, bg=PANEL)
        self.taps_frame.pack(fill="x", padx=16, pady=(4, 12))

        row3 = tk.Frame(controls, bg=PANEL)
        row3.pack(fill="x", padx=16, pady=(0, 16))

        self.step_btn = tk.Button(row3, text="Step", command=self._on_step,
                                   bg=BORDER, fg=TEXT, relief="flat", padx=12, pady=4)
        self.step_btn.pack(side="left", padx=(0, 8))

        self.run_btn = tk.Button(row3, text="Run", command=self._on_toggle_run,
                                  bg=BORDER, fg=TEXT, relief="flat", padx=12, pady=4)
        self.run_btn.pack(side="left", padx=(0, 8))

        self.reset_btn = tk.Button(row3, text="Reset", command=self._on_reset,
                                    bg=BORDER, fg=TEXT, relief="flat", padx=12, pady=4)
        self.reset_btn.pack(side="left", padx=(0, 8))

        tk.Label(row3, text="Speed", bg=PANEL, fg=MUTED,
                  font=("Segoe UI", 9)).pack(side="left", padx=(24, 4))
        tk.Scale(row3, from_=30, to=1000, orient="horizontal", variable=self.speed_var,
                 bg=PANEL, fg=MUTED, troughcolor=BG, highlightthickness=0,
                 showvalue=False, length=140).pack(side="left")

        display = tk.Frame(self, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        display.pack(fill="x", padx=20, pady=(0, 20))

        tk.Label(display, text="REGISTER", bg=PANEL, fg=MUTED,
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(12, 4))
        self.register_frame = tk.Frame(display, bg=PANEL)
        self.register_frame.pack(anchor="w", padx=16, pady=(0, 12))

        stats = tk.Frame(display, bg=PANEL)
        stats.pack(fill="x", padx=16, pady=(0, 12))
        self.step_label = self._stat(stats, "STEP", "0", 0)
        self.output_bit_label = self._stat(stats, "OUTPUT BIT", "-", 1)
        self.feedback_bit_label = self._stat(stats, "FEEDBACK BIT", "-", 2)

        tk.Label(display, text="OUTPUT STREAM", bg=PANEL, fg=MUTED,
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(0, 4))
        self.output_text = tk.Text(display, height=4, width=60, bg=BG, fg=OUTPUT_COLOR,
                                    relief="flat", font=("Consolas", 10), wrap="char")
        self.output_text.pack(fill="x", padx=16, pady=(0, 16))
        self.output_text.configure(state="disabled")

    def _stat(self, parent, label, value, col):
        frame = tk.Frame(parent, bg=PANEL)
        frame.grid(row=0, column=col, sticky="w", padx=(0, 32))
        tk.Label(frame, text=label, bg=PANEL, fg=MUTED,
                  font=("Segoe UI", 8)).pack(anchor="w")
        value_label = tk.Label(frame, text=value, bg=PANEL, fg=TEXT,
                                 font=("Consolas", 13, "bold"))
        value_label.pack(anchor="w")
        return value_label

    # ---------- LFSR logic ----------

    def _default_seed(self, n):
        return "0" * (n - 1) + "1"

    def _setup(self, n):
        self.length.set(n)
        self._rebuild_taps(n, DEFAULT_TAPS.get(n, [n, 1]))
        self.seed_var.set(self._default_seed(n))
        self._load_seed()

    def _rebuild_taps(self, n, selected):
        for widget in self.taps_frame.winfo_children():
            widget.destroy()
        self.tap_vars = {}
        for pos in range(1, n + 1):
            var = tk.IntVar(value=1 if pos in selected else 0)
            cb = tk.Checkbutton(self.taps_frame, text=str(pos), variable=var,
                                 bg=PANEL, fg=TEXT, selectcolor=BG,
                                 activebackground=PANEL, activeforeground=TEXT,
                                 command=self._render_register)
            cb.pack(side="left", padx=4)
            self.tap_vars[pos] = var

    def _get_taps(self):
        return [pos for pos, var in self.tap_vars.items() if var.get()]

    def _load_seed(self):
        n = self.length.get()
        seed = self.seed_var.get().strip()
        if len(seed) != n or any(c not in "01" for c in seed):
            seed = self._default_seed(n)
            self.seed_var.set(seed)
        if set(seed) == {"0"}:
            seed = seed[:-1] + "1"
            self.seed_var.set(seed)

        self.register = [int(c) for c in seed]
        self.step_count = 0
        self.output_bits = ""
        self.output_bit_label.config(text="-")
        self.feedback_bit_label.config(text="-")
        self._render_register()
        self._render_stats()

    def _render_register(self, pulse_index=None):
        for widget in self.register_frame.winfo_children():
            widget.destroy()
        taps = self._get_taps()
        for i, bit in enumerate(self.register):
            is_tapped = (i + 1) in taps
            fg = TEXT
            bg = ONE_BIT if bit else BG
            border = ACCENT if is_tapped else BORDER
            box = tk.Label(self.register_frame, text=str(bit), width=3, height=1,
                            bg=bg, fg=fg, font=("Consolas", 12, "bold"),
                            relief="solid", bd=1, highlightbackground=border,
                            highlightthickness=1)
            box.pack(side="left", padx=3)

    def _render_stats(self):
        self.step_label.config(text=str(self.step_count))
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        text = self.output_bits
        if len(text) > MAX_OUTPUT_CHARS:
            text = "..." + text[-MAX_OUTPUT_CHARS:]
        self.output_text.insert("1.0", text)
        self.output_text.configure(state="disabled")

    def _step(self):
        taps = self._get_taps()
        if not taps:
            self._stop_run()
            messagebox.showwarning("No taps selected",
                                    "Select at least one tap position for feedback.")
            return
        feedback = 0
        for pos in taps:
            feedback ^= self.register[pos - 1]
        output = self.register[-1]

        self.register = [feedback] + self.register[:-1]
        self.step_count += 1
        self.output_bits += str(output)

        self.output_bit_label.config(text=str(output))
        self.feedback_bit_label.config(text=str(feedback))
        self._render_register()
        self._render_stats()

    # ---------- Event handlers ----------

    def _on_length_change(self):
        self._stop_run()
        self._setup(self.length.get())

    def _on_seed_change(self):
        self._stop_run()
        self._load_seed()

    def _on_step(self):
        self._stop_run()
        self._step()

    def _on_reset(self):
        self._stop_run()
        self._load_seed()

    def _on_toggle_run(self):
        if self.running:
            self._stop_run()
        else:
            self._start_run()

    def _start_run(self):
        self.running = True
        self.run_btn.config(text="Stop", bg="#b91c1c")
        self._run_tick()

    def _stop_run(self):
        self.running = False
        self.run_btn.config(text="Run", bg=BORDER)
        if self._run_job is not None:
            self.after_cancel(self._run_job)
            self._run_job = None

    def _run_tick(self):
        if not self.running:
            return
        self._step()
        self._run_job = self.after(self.speed_var.get(), self._run_tick)


if __name__ == "__main__":
    app = LFSRApp()
    app.mainloop()
