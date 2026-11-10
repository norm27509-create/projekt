"""ROB RUN Settings Tuner - display gamma profiles plus a settings checklist.

Only changes the Windows display gamma ramp (like a GPU control panel).
It does not read, modify, or inject into the game.
"""

import json
import os
import queue
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from . import display as display_mod
from .ramp import PRESETS, Profile, build_ramp

CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "RobRunTuner"
CONFIG_FILE = CONFIG_DIR / "profiles.json"

CHECKLIST = [
    "FPS drops only while moving the mouse? Set mouse polling rate to 1000 Hz (or 500 Hz) in your mouse software.",
    "Update your GPU driver, then restart Steam and the game.",
    "Disable overlays you don't need (Discord, GeForce/Radeon, recording tools).",
    "Steam > ROB RUN > Properties > Installed Files > Verify integrity if the game crashes or freezes.",
    "Use Fullscreen display mode and set the refresh rate to your monitor's native value.",
    "Lower shadows and post-processing first; keep texture quality if you have enough VRAM.",
    "Turn off motion blur and heavy film effects for a clearer image.",
    "Use the in-game brightness slider first, then this tuner for dark scenes.",
    "Headphones + slightly louder effects volume make footsteps easier to hear.",
    "High ping or rubber-banding is a server/network issue, not a graphics one.",
]


def load_profiles() -> dict[str, Profile]:
    profiles = dict(PRESETS)
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        for name, values in data.get("custom", {}).items():
            profiles[name] = Profile.from_dict(values)
    except (OSError, ValueError, TypeError):
        pass
    return profiles


def save_profiles(profiles: dict[str, Profile]):
    custom = {n: p.to_dict() for n, p in profiles.items() if n not in PRESETS}
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"custom": custom}, indent=2), encoding="utf-8")


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.display = display_mod.Display()
        self.profiles = load_profiles()
        self.active = False
        self.events: "queue.Queue[str]" = queue.Queue()

        root.title("ROB RUN Settings Tuner")
        root.resizable(False, False)
        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        nb.add(self._build_display_tab(nb), text="Display")
        nb.add(self._build_checklist_tab(nb), text="Settings checklist")

        self.status = tk.StringVar()
        ttk.Label(root, textvariable=self.status, foreground="#555").pack(anchor="w", padx=10, pady=(0, 8))

        if display_mod.IS_WINDOWS:
            from . import hotkeys
            hotkeys.start(self.events)
            self.status.set("Ready. F9 = toggle profile, F10 = reset to normal.")
        else:
            self.status.set("Preview mode: display changes only work on Windows.")

        root.protocol("WM_DELETE_WINDOW", self.quit)
        root.after(100, self._poll_events)

    # ---- UI ----
    def _build_display_tab(self, parent):
        f = ttk.Frame(parent, padding=10)
        ttk.Label(f, text="Profile").grid(row=0, column=0, sticky="w")
        self.profile_var = tk.StringVar(value="Default")
        self.combo = ttk.Combobox(f, textvariable=self.profile_var, state="readonly", width=28,
                                  values=list(self.profiles))
        self.combo.grid(row=0, column=1, columnspan=2, sticky="we", pady=4)
        self.combo.bind("<<ComboboxSelected>>", lambda e: self._load_selected())

        self.vars = {}
        specs = [("gamma", "Gamma (shadows)", 0.5, 2.5), ("brightness", "Brightness", -0.3, 0.3),
                 ("contrast", "Contrast", 0.5, 1.5)]
        for row, (key, label, lo, hi) in enumerate(specs, start=1):
            ttk.Label(f, text=label).grid(row=row, column=0, sticky="w")
            var = tk.DoubleVar()
            ttk.Scale(f, from_=lo, to=hi, variable=var, length=220,
                      command=lambda _v: self._on_slider()).grid(row=row, column=1, pady=4)
            val_lbl = ttk.Label(f, width=6)
            val_lbl.grid(row=row, column=2)
            var.trace_add("write", lambda *_a, v=var, l=val_lbl: l.config(text=f"{v.get():.2f}"))
            self.vars[key] = var

        btns = ttk.Frame(f)
        btns.grid(row=4, column=0, columnspan=3, pady=(10, 0), sticky="we")
        self.apply_btn = ttk.Button(btns, text="Apply (F9)", command=self.toggle)
        self.apply_btn.pack(side="left")
        ttk.Button(btns, text="Reset (F10)", command=self.reset).pack(side="left", padx=4)
        ttk.Button(btns, text="Save as…", command=self.save_as).pack(side="left")
        ttk.Button(btns, text="Delete", command=self.delete).pack(side="left", padx=4)

        self._load_selected()
        return f

    def _build_checklist_tab(self, parent):
        f = ttk.Frame(parent, padding=10)
        for tip in CHECKLIST:
            # tk (not ttk) Checkbutton supports wraplength.
            tk.Checkbutton(f, text=tip, wraplength=380, justify="left",
                           variable=tk.BooleanVar(f)).pack(anchor="w", pady=2)
        return f

    # ---- logic ----
    def current_profile(self) -> Profile:
        return Profile(**{k: v.get() for k, v in self.vars.items()})

    def _load_selected(self):
        p = self.profiles[self.profile_var.get()]
        for k, v in p.to_dict().items():
            self.vars[k].set(v)
        if self.active:
            self._apply()

    def _on_slider(self):
        if self.active:
            self._apply()

    def _apply(self):
        if self.display.apply(build_ramp(self.current_profile())):
            self.status.set(f"Applied '{self.profile_var.get()}'. F9 to toggle off.")
        elif display_mod.IS_WINDOWS:
            self.status.set("Windows rejected this ramp. Try milder values (see README: GdiICMGammaRange).")

    def toggle(self):
        if self.active:
            self.reset()
        else:
            self.active = True
            self.apply_btn.config(text="Turn off (F9)")
            self._apply()

    def reset(self):
        self.active = False
        self.apply_btn.config(text="Apply (F9)")
        self.display.restore()
        self.status.set("Display restored to normal.")

    def save_as(self):
        name = simpledialog.askstring("Save profile", "Profile name:", parent=self.root)
        if not name:
            return
        if name in PRESETS:
            messagebox.showerror("Save profile", "That name is a built-in preset.")
            return
        self.profiles[name] = self.current_profile()
        save_profiles(self.profiles)
        self.combo.config(values=list(self.profiles))
        self.profile_var.set(name)

    def delete(self):
        name = self.profile_var.get()
        if name in PRESETS:
            messagebox.showinfo("Delete", "Built-in presets can't be deleted.")
            return
        del self.profiles[name]
        save_profiles(self.profiles)
        self.combo.config(values=list(self.profiles))
        self.profile_var.set("Default")
        self._load_selected()

    def _poll_events(self):
        while not self.events.empty():
            ev = self.events.get()
            if ev == "toggle":
                self.toggle()
            elif ev == "reset":
                self.reset()
            elif ev.startswith("error:"):
                self.status.set(ev[6:])
        self.root.after(100, self._poll_events)

    def quit(self):
        self.display.restore()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = App(root)
    try:
        root.mainloop()
    finally:
        app.display.restore()


if __name__ == "__main__":
    main()
