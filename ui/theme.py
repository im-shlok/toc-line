"""Shared visual tokens and keyboard-friendly controls."""
import tkinter as tk

import customtkinter as ctk

BG = "#F1F5F6"
SURFACE = "#FFFFFF"
INK = "#19343D"
MUTED = "#526A73"
BORDER = "#DCE5E8"
PRIMARY = "#12695D"
PRIMARY_HOVER = "#0C554B"
NAV = "#16343D"
NAV_TEXT = "#C3D4D9"
SOFT = "#EAF1F3"
GREEN = "#08745B"
GREEN_SOFT = "#E4F3ED"
RED = "#B12D3D"
RED_SOFT = "#FBECEF"
AMBER = "#8A5713"
AMBER_SOFT = "#FFF3DD"
FONT = "Segoe UI"
MONO = "Consolas"


def font(size=14, weight="normal"):
    return ctk.CTkFont(family=FONT, size=size, weight=weight)


def label(parent, text="", size=14, bold=False, color=INK, **kwargs):
    return ctk.CTkLabel(parent, text=text, font=font(size, "bold" if bold else "normal"),
                        text_color=color, anchor="w", **kwargs)


def button(parent, text, command, primary=False, **kwargs):
    options = dict(height=42, corner_radius=8, border_width=0,
                   fg_color=PRIMARY if primary else SOFT,
                   hover_color=PRIMARY_HOVER if primary else BORDER,
                   text_color=SURFACE if primary else INK,
                   text_color_disabled=MUTED, font=font(14, "bold"),
                   anchor="w")
    options.update(kwargs)
    widget = ctk.CTkButton(parent, text=text, command=command, **options)
    # CTkButton is canvas-based: explicitly provide Tab, Enter, Space and focus.
    widget._canvas.configure(takefocus=1)
    normal_border = options["border_width"]
    normal_color = options.get("border_color", BORDER)
    focus_color = AMBER_SOFT if primary else NAV_TEXT if options["text_color"] == NAV_TEXT else INK
    widget.bind("<FocusIn>", lambda _: widget.configure(border_width=2, border_color=focus_color))
    widget.bind("<FocusOut>", lambda _: widget.configure(border_width=normal_border,
                                                        border_color=normal_color))
    widget.bind("<Return>", lambda _: widget.invoke())
    widget.bind("<space>", lambda _: widget.invoke())
    return widget


def canvas(parent, height, background=SURFACE):
    return tk.Canvas(parent, height=height, background=background,
                     borderwidth=0, highlightthickness=0)
