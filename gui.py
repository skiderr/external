"""Tkinter aim-trainer GUI. Everything here is a self-contained simulation."""
from __future__ import annotations

import math
import time
import tkinter as tk
from tkinter import ttk

from config import AimConfig, AimMode, NEAREST
from targeting import AimController, AimResult
from targets import TargetField
from vector_math import Vector2

W, H = 900, 580
BG = "#14161b"
PANEL = "#1c1f26"
FG = "#d7dae0"
ACCENT = "#4aa3ff"


class AimTrainerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Aim Trainer (simulation)")
        root.configure(bg=PANEL)
        root.resizable(False, False)

        self.config = AimConfig()
        self.field = TargetField(W, H, count=6)
        self.controller = AimController(self.config)

        self.mouse = Vector2(W / 2, H / 2)
        self.offset = Vector2()
        self.hits = 0
        self.shots = 0

        self._build_ui()
        self._last = time.perf_counter()
        self._tick()

    # ------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.canvas = tk.Canvas(self.root, width=W, height=H, bg=BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0)
        try:
            self.canvas.configure(cursor="none")
        except tk.TclError:
            self.canvas.configure(cursor="crosshair")
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Button-2>", lambda e: self.controller.selector.release())
        self.canvas.bind("<Button-3>", lambda e: self.controller.selector.release())
        self.root.bind("<r>", lambda e: self.controller.selector.release())

        panel = tk.Frame(self.root, bg=PANEL, padx=14, pady=14)
        panel.grid(row=0, column=1, sticky="ns")

        def label(text: str) -> tk.Label:
            return tk.Label(panel, text=text, bg=PANEL, fg=FG, anchor="w")

        # Enable / FOV visibility
        self.enabled_var = tk.BooleanVar(value=self.config.enabled)
        self.show_fov_var = tk.BooleanVar(value=self.config.show_fov)
        for text, var, key in (
            ("Enabled", self.enabled_var, "enabled"),
            ("Show FOV circle", self.show_fov_var, "show_fov"),
        ):
            tk.Checkbutton(
                panel, text=text, variable=var, bg=PANEL, fg=FG, selectcolor=BG,
                activebackground=PANEL, activeforeground=FG,
                command=lambda v=var, k=key: self.config.update(**{k: v.get()}),
            ).pack(anchor="w")

        # FOV slider
        label("FOV radius").pack(anchor="w", pady=(12, 0))
        self.fov_scale = tk.Scale(
            panel, from_=int(AimConfig.FOV_MIN), to=int(AimConfig.FOV_MAX),
            orient="horizontal", length=220, bg=PANEL, fg=FG, troughcolor=BG,
            highlightthickness=0,
            command=lambda v: self.config.update(fov_radius=float(v)),
        )
        self.fov_scale.set(self.config.fov_radius)
        self.fov_scale.pack(anchor="w")

        # Smoothing slider
        label("Smoothing (0 = instant)").pack(anchor="w", pady=(8, 0))
        self.smooth_scale = tk.Scale(
            panel, from_=int(AimConfig.SMOOTH_MIN), to=int(AimConfig.SMOOTH_MAX),
            orient="horizontal", length=220, bg=PANEL, fg=FG, troughcolor=BG,
            highlightthickness=0,
            command=lambda v: self.config.update(smoothing=float(v)),
        )
        self.smooth_scale.set(self.config.smoothing)
        self.smooth_scale.pack(anchor="w")

        # Mode
        label("Mode").pack(anchor="w", pady=(10, 0))
        self.mode_var = tk.StringVar(value=self.config.mode.value)
        for mode in AimMode:
            tk.Radiobutton(
                panel, text=mode.value, value=mode.value, variable=self.mode_var,
                bg=PANEL, fg=FG, selectcolor=BG, activebackground=PANEL, activeforeground=FG,
                command=lambda: self.config.update(mode=self.mode_var.get()),
            ).pack(anchor="w")

        # Target dropdown
        label("Target").pack(anchor="w", pady=(10, 0))
        self.target_var = tk.StringVar(value=self.config.target_choice)
        combo = ttk.Combobox(
            panel, textvariable=self.target_var, state="readonly", width=24,
            values=[NEAREST] + self.field.names,
        )
        combo.pack(anchor="w")
        combo.bind("<<ComboboxSelected>>",
                   lambda e: self.config.update(target_choice=self.target_var.get()))

        ttk.Button(panel, text="Release lock (R / right-click)",
                   command=self.controller.selector.release).pack(anchor="w", pady=(10, 0))
        ttk.Button(panel, text="Reset stats", command=self._reset_stats).pack(anchor="w", pady=(4, 0))

        self.stats_var = tk.StringVar()
        tk.Label(panel, textvariable=self.stats_var, bg=PANEL, fg=ACCENT,
                 justify="left", anchor="w").pack(anchor="w", pady=(14, 0))

        tk.Label(panel, text="Move mouse over the arena.\nLeft-click to shoot.",
                 bg=PANEL, fg="#8a8f99", justify="left").pack(anchor="w", pady=(10, 0))

    # ------------------------------------------------------------ input
    def _on_motion(self, e: tk.Event) -> None:
        self.mouse = Vector2(e.x, e.y)

    def _crosshair(self) -> Vector2:
        return (self.mouse + self.offset).clamped(0, 0, W, H)

    def _on_click(self, _e: tk.Event) -> None:
        cross = self._crosshair()
        self.shots += 1
        best, best_d = None, 1e9
        for t in self.field.alive_targets():
            d = cross.distance_to(t.pos)
            if d <= t.radius and d < best_d:
                best, best_d = t, d
        if best is not None:
            self.hits += 1
            self.field.kill(best)

    def _reset_stats(self) -> None:
        self.hits = self.shots = 0

    # ------------------------------------------------------------ loop
    def _tick(self) -> None:
        now = time.perf_counter()
        dt = min(now - self._last, 0.05)
        self._last = now

        self.field.update(dt)
        cross = self._crosshair()
        result = self.controller.step(cross, self.field.targets, dt)

        if result.target is not None:
            self.offset = self.offset + result.delta
        else:
            self.offset = self.offset * math.exp(-4.0 * dt)  # ease assist back out
        self.offset = self._crosshair() - self.mouse           # keep inside arena

        self._draw(self._crosshair(), result)
        self.root.after(16, self._tick)

    # ------------------------------------------------------------ drawing
    def _draw(self, cross: Vector2, res: AimResult) -> None:
        c = self.canvas
        cfg = self.config
        c.delete("all")

        for t in self.field.alive_targets():
            c.create_oval(t.pos.X - t.radius, t.pos.Y - t.radius,
                          t.pos.X + t.radius, t.pos.Y + t.radius,
                          fill="#c94f4f", outline="#ff8a8a", width=2)
            c.create_text(t.pos.X, t.pos.Y - t.radius - 10, text=t.name,
                          fill="#8a8f99", font=("Segoe UI", 8))

        if cfg.show_fov:
            r = cfg.fov_radius
            c.create_oval(cross.X - r, cross.Y - r, cross.X + r, cross.Y + r,
                          outline=ACCENT if cfg.enabled else "#555a63", dash=(4, 4))

        if res.target is not None:
            tp = res.target.pos
            ring = "#ffb347" if res.locked else "#5fd38d"
            c.create_line(cross.X, cross.Y, tp.X, tp.Y, fill=ring, dash=(2, 3))
            rr = res.target.radius + 6
            c.create_oval(tp.X - rr, tp.Y - rr, tp.X + rr, tp.Y + rr, outline=ring, width=2)

        s = 10
        c.create_line(cross.X - s, cross.Y, cross.X + s, cross.Y, fill="white")
        c.create_line(cross.X, cross.Y - s, cross.X, cross.Y + s, fill="white")

        if not cfg.enabled:
            status = "Assist: OFF"
        elif res.target is None:
            status = f"{cfg.mode.value}: no target in FOV"
        else:
            tag = "LOCKED" if res.locked else "Tracking"
            status = f"{cfg.mode.value}: {tag} {res.target.name}"
        c.create_text(10, 10, anchor="nw", text=status, fill=FG, font=("Segoe UI", 10, "bold"))

        acc = (100.0 * self.hits / self.shots) if self.shots else 0.0
        self.stats_var.set(f"Hits: {self.hits}\nShots: {self.shots}\nAccuracy: {acc:.0f}%")


def run() -> None:
    root = tk.Tk()
    AimTrainerApp(root)
    root.mainloop()
