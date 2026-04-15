import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import webbrowser
import threading
import time
import json
import os

# ================= CONFIG =================
NODE_URL = "https://europe3.signum.network"
#EXPLORER_URL = "https://explorer.signum.network/?action=address&address="
EXPLORER_URL = "https://explorer.signum.network/at/"
CANCEL_MESSAGE = "b00e004992c79bd8000000000000000000000000000000000000000000000000"
AMOUNT_SIGNA = 0.2
FEE_SIGNA = 0.03

# =========================================

class SignumApp:
    HISTORY_FILE = "signum_history.json"

    def __init__(self, root):
        self.root = root
        self.root.title("Signum Contract Manager")
        self.root.geometry("620x360")

        self.history = []

        style = ttk.Style()
        style.configure("Treeview", rowheight=18, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

        self.create_ui()
        self.load_history()

    def create_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=6, pady=3)

        tk.Label(top, text="Wallet:", font=("Segoe UI", 9)).pack(side="left")

        self.addr_var = tk.StringVar()
        self.combo = ttk.Combobox(top, textvariable=self.addr_var, height=5)
        self.combo.pack(side="left", fill="x", expand=True, padx=4)
        self.combo.bind("<Return>", lambda event: self.load_contracts())
        self.root.bind("<Return>", lambda event: self.load_contracts())

        tk.Button(top, text="Load", width=7, command=self.load_contracts).pack(side="left")
        tk.Button(top, text="Exit", width=7, command=self.root.quit).pack(side="left", padx=4)

        self.loading = tk.Label(self.root, text="", fg="blue", font=("Segoe UI", 9))
        self.loading.pack(anchor="w", padx=6)

        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=4, pady=3)

        self.tree = ttk.Treeview(
            frame,
            columns=("Address", "Balance (SIGNA)"),
            show="headings"
        )

        self.tree.heading("Address", text="Contract Address", command=lambda: self.sort_col("Address", False))
        self.tree.heading("Balance (SIGNA)", text="Balance (SIGNA)", command=lambda: self.sort_col("Balance (SIGNA)", False))

        self.tree.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(frame, command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

        # Styles
        self.tree.tag_configure("clickable", foreground="#0066cc")
        self.tree.tag_configure("zero", foreground="#888888")
        self.tree.tag_configure("nonzero", foreground="#008800")

        self.tree.bind("<ButtonRelease-1>", self.on_click)

    # ================= LOADING =================
    def animate_loading(self):
        dots = 0
        while self.is_loading:
            self.loading.config(text="Loading" + "." * dots)
            dots = (dots + 1) % 4
            time.sleep(0.4)

    def load_contracts(self):
        addr = self.addr_var.get().strip()
        if not addr:
            return

        self.save_history(addr)
        self.tree.delete(*self.tree.get_children())

        self.is_loading = True
        threading.Thread(target=self.animate_loading, daemon=True).start()
        threading.Thread(target=self.fetch, args=(addr,), daemon=True).start()

    # ================= FETCH =================
    def fetch(self, addr):
        try:
            url = f"{NODE_URL}/burst?requestType=getAccountATs&account={addr}"
            data = requests.get(url).json()

            max_addr_len = len("Contract Address")
            max_bal_len = len("Balance (SIGNA)")

            rows = []

            for at in data.get("ats", []):
                address = at.get("atRS")
                bal = int(at.get("balanceNQT", 0)) / 1e8

                bal_str = f"{bal:.4f}"

                max_addr_len = max(max_addr_len, len(address))
                max_bal_len = max(max_bal_len, len(bal_str))

                rows.append((address, bal_str, bal))

            # Insert rows
            for address, bal_str, bal in rows:
                tag = "nonzero" if bal > 0 else "zero"
                self.tree.insert("", "end", values=(address, bal_str), tags=("clickable", tag))

            # Auto column sizing
            self.tree.column("Address", width=max_addr_len * 7)
            self.tree.column("Balance (SIGNA)", width=max_bal_len * 7, anchor="w")

        except Exception as e:
            messagebox.showerror("Error", str(e))

        self.is_loading = False
        self.loading.config(text="")

    # ================= ADDRESS → NUMERIC =================
    def get_numeric_id(self, rs_address):
        try:
            url = f"{NODE_URL}/burst?requestType=getAccount&account={rs_address}"
            data = requests.get(url).json()
            return data.get("account")
        except:
            return None

    # ================= CLICK =================
    def on_click(self, event):
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)

        if not item:
            return

        addr, bal = self.tree.item(item, "values")
        bal = float(bal)

        if col == "#1":
            numeric = self.get_numeric_id(addr)
            if numeric:
                webbrowser.open(EXPLORER_URL + numeric)
            else:
                messagebox.showerror("Error", "Could not resolve numeric address.")

        elif col == "#2":
            if bal == 0:
                messagebox.showwarning("Zero Balance", "This contract has zero balance and does not require cancellation.")
            else:
                self.cancel(addr)

    # ================= CANCEL =================
    def cancel(self, contract):
        phrase = simpledialog.askstring("Passphrase", "Enter secret passphrase:", show="*")
        if not phrase:
            return

        try:
            params = {
                "requestType": "sendMoney",
                "recipient": contract,
                "amountNQT": int(AMOUNT_SIGNA * 1e8),
                "feeNQT": int(FEE_SIGNA * 1e8),
                "deadline": 60,
                "secretPhrase": phrase,
                "message": CANCEL_MESSAGE,
                "messageIsText": "false"
            }

            r = requests.post(f"{NODE_URL}/burst", data=params).json()

            if "errorDescription" in r:
                messagebox.showerror("Error", r["errorDescription"])
            else:
                messagebox.showinfo("Success", "Cancel transaction sent.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= SORT =================
    def sort_col(self, col, rev):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]

        try:
            data.sort(key=lambda x: float(x[0]), reverse=rev)
        except:
            data.sort(reverse=rev)

        for i, (_, k) in enumerate(data):
            self.tree.move(k, "", i)

        self.tree.heading(col, command=lambda: self.sort_col(col, not rev))

    # ================= HISTORY =================
    def save_history(self, addr):
        if addr in self.history:
            if addr in self.history:
                self.history.remove(addr)

        self.history.insert(0, addr)
        self.history = self.history[:5]

        self.combo["values"] = self.history

        # persist to disk
        self.save_history_file()
        def save_history(self, addr):
            if addr in self.history:
                self.history.remove(addr)
            self.history.insert(0, addr)
            self.history = self.history[:5]
            self.combo["values"] = self.history

    def load_history(self):
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, "r") as f:
                    self.history = json.load(f)
                    self.combo["values"] = self.history
            except:
                self.history = []

    def save_history_file(self):
        try:
            with open(self.HISTORY_FILE, "w") as f:
                json.dump(self.history, f)
        except:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    SignumApp(root)
    root.mainloop()
