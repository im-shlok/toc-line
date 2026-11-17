import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from ui import theme as t


class ActivityPanel(ctk.CTkFrame):
    def __init__(self, parent, export_command):
        super().__init__(parent, fg_color=t.SURFACE, corner_radius=12)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(12, 8))
        self.title = t.label(header, "Activity log", 18, True)
        self.title.pack(side="left")
        t.button(header, "Export CSV", export_command, width=110, height=32, anchor="center").pack(side="right")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Metro.Treeview", background=t.SURFACE, foreground=t.INK,
                        fieldbackground=t.SURFACE, borderwidth=0, rowheight=34, font=(t.FONT, 10))
        style.configure("Metro.Treeview.Heading", background=t.SOFT, foreground=t.MUTED,
                        font=(t.FONT, 10, "bold"), relief="flat", padding=(8, 6))
        style.map("Metro.Treeview", background=[("selected", t.PRIMARY)], foreground=[("selected", t.SURFACE)])
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.tree = ttk.Treeview(body, columns=("time", "mode", "action", "transition", "output"),
                                 show="headings", height=4, style="Metro.Treeview")
        for name, text, width in (("time", "Time", 76), ("mode", "Mode", 64),
                                   ("action", "Input / event", 160), ("transition", "Transition", 160),
                                   ("output", "FSM output", 335)):
            self.tree.heading(name, text=text, anchor="w")
            self.tree.column(name, width=width, minwidth=width, stretch=name == "output")
        vertical = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.tree.yview)
        horizontal = ttk.Scrollbar(body, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self.tree.tag_configure("alarm", foreground=t.RED)
        self.tree.tag_configure("entry", foreground=t.GREEN)
        self.count = 0

    def sync(self, session):
        for index, event in enumerate(session.events[self.count:], self.count):
            transition = f"{event['previous_state']} -> {event['next_state']}" if event["input"] else event["next_state"]
            action = event["input"] or event["event"]
            tag = "alarm" if event["next_state"] == "ALARM" else "entry" if event["next_state"] == "UNLOCKED" else ""
            self.tree.insert("", "end", iid=str(index), values=(event["timestamp"][11:19], event["mode"],
                              action, transition, event["output"] or event["event"]), tags=(tag,))
        self.count = len(session.events)
        # Keep the visible widget bounded, but preserve the entire session for CSV.
        children = self.tree.get_children()
        for item in children[:-300]:
            self.tree.delete(item)
        if self.tree.get_children():
            self.tree.see(self.tree.get_children()[-1])
        self.title.configure(text=f"Activity log   ({len(session.history)} inputs)")
