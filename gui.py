import sys
import platform
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from src.processing import process_run_history
from src.resource_path import get_resource_path


def get_default_data_dir():
    if platform.system() == "Windows":
        appdata = Path.home() / "AppData" / "LocalLow" / "MegaCrit" / "SlayTheSpire2"
        if appdata.exists():
            return str(appdata)
    else:
        linux_path = Path.home() / ".local" / "share" / "SlayTheSpire2"
        if linux_path.exists():
            return str(linux_path)
    return ""


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Slay the Spire 2 — Data Summary")
        self.geometry("620x480")
        self.minsize(520, 420)

        self.grid_columnconfigure(1, weight=1)

        row = 0

        # Data directory
        ctk.CTkLabel(self, text="SlayTheSpire2 Data Directory:").grid(
            row=row, column=0, columnspan=3, sticky="w", padx=12, pady=(16, 2))
        row += 1

        self.data_dir_var = ctk.StringVar(value=get_default_data_dir())
        ctk.CTkEntry(self, textvariable=self.data_dir_var).grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=(12, 4), pady=2)
        ctk.CTkButton(self, text="Browse", width=80, command=self._browse_data_dir).grid(
            row=row, column=2, padx=(0, 12), pady=2)
        row += 1

        # Steam ID
        ctk.CTkLabel(self, text="Steam ID:").grid(
            row=row, column=0, columnspan=3, sticky="w", padx=12, pady=(12, 2))
        row += 1

        self.steam_id_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.steam_id_var).grid(
            row=row, column=0, columnspan=3, sticky="ew", padx=12, pady=2)
        row += 1

        # Output directory
        ctk.CTkLabel(self, text="Output Directory:").grid(
            row=row, column=0, columnspan=3, sticky="w", padx=12, pady=(12, 2))
        row += 1

        self.output_dir_var = ctk.StringVar(value=str(Path.home()))
        ctk.CTkEntry(self, textvariable=self.output_dir_var).grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=(12, 4), pady=2)
        ctk.CTkButton(self, text="Browse", width=80, command=self._browse_output_dir).grid(
            row=row, column=2, padx=(0, 12), pady=2)
        row += 1

        # Run button
        self.run_button = ctk.CTkButton(self, text="Run Processing", command=self._run)
        self.run_button.grid(row=row, column=0, columnspan=3, padx=12, pady=(20, 8))
        row += 1

        # Status area
        ctk.CTkLabel(self, text="Status:").grid(
            row=row, column=0, columnspan=3, sticky="w", padx=12, pady=(8, 2))
        row += 1

        self.status_box = ctk.CTkTextbox(self, height=140, state="disabled")
        self.status_box.grid(row=row, column=0, columnspan=3, sticky="nsew", padx=12, pady=(0, 12))
        self.grid_rowconfigure(row, weight=1)

    def _browse_data_dir(self):
        path = filedialog.askdirectory(title="Select SlayTheSpire2 Data Directory")
        if path:
            self.data_dir_var.set(path)

    def _browse_output_dir(self):
        path = filedialog.askdirectory(title="Select Output Directory")
        if path:
            self.output_dir_var.set(path)

    def _log(self, message):
        self.status_box.configure(state="normal")
        self.status_box.insert("end", message + "\n")
        self.status_box.see("end")
        self.status_box.configure(state="disabled")

    def _run(self):
        data_dir = self.data_dir_var.get().strip()
        steam_id = self.steam_id_var.get().strip()
        output_dir = self.output_dir_var.get().strip()

        if not data_dir:
            self._log("Error: Please select a data directory.")
            return
        if not steam_id:
            steam_dir = Path(data_dir) / "steam"
            if steam_dir.is_dir():
                ids = [d.name for d in steam_dir.iterdir() if d.is_dir()]
                if ids:
                    steam_id = ids[0]
                    self.steam_id_var.set(steam_id)
                    self._log(f"No Steam ID provided, using: {steam_id}")
            if not steam_id:
                self._log("Error: No Steam ID provided and none found in data directory.")
                return
        if not output_dir:
            self._log("Error: Please select an output directory.")
            return

        history_path = Path(data_dir) / "steam" / steam_id / "profile1" / "saves" / "history"
        cards_json_path = get_resource_path("data/cards/cards.json")
        output_path = Path(output_dir)

        self.run_button.configure(state="disabled")
        self._log(f"History path: {history_path}")

        def do_processing():
            try:
                def status_callback(msg):
                    self.after(0, self._log, msg)

                run_df, card_df = process_run_history(history_path, cards_json_path, status_callback)

                run_csv = output_path / "run_history.csv"
                card_csv = output_path / "card_choices.csv"
                run_df.to_csv(run_csv)
                card_df.to_csv(card_csv)

                self.after(0, self._log, f"Saved run history to {run_csv}")
                self.after(0, self._log, f"Saved card choices to {card_csv}")
            except Exception as e:
                self.after(0, self._log, f"Error: {e}")
            finally:
                self.after(0, lambda: self.run_button.configure(state="normal"))

        threading.Thread(target=do_processing, daemon=True).start()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = App()
    app.mainloop()
