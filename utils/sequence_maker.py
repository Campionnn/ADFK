import tkinter as tk
from tkinter import messagebox, filedialog
import json

class CustomDialog(tk.Toplevel):
    def __init__(self, parent, title, labels, initial_values):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.result = None

        self.title(title)
        self.entries = []

        for i, label in enumerate(labels):
            tk.Label(self, text=label).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            entry = tk.Entry(self)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entry.insert(0, initial_values[i])
            self.entries.append(entry)

        tk.Button(self, text="OK", command=self.on_ok).grid(row=len(labels), column=0, columnspan=2, pady=10)

        self.grid_columnconfigure(1, weight=1)

        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.lift()
        self.focus_set()
        self.wait_window(self)

    def on_ok(self):
        self.result = [entry.get() for entry in self.entries]
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


class Action:
    def __init__(self, action_type, ids, location=None, amount=None):
        self.action_type = action_type
        self.ids = ids
        self.location = location
        self.amount = amount

    def __str__(self):
        if self.action_type == "place":
            return f"Place {self.ids} at {self.location}"
        elif self.action_type == "upgrade":
            return f"Upgrade {self.ids} by {self.amount}"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Custom Placement")
        self.actions = []

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Name").grid(row=0, column=0, sticky="e")
        self.name_entry = tk.Entry(self.root)
        self.name_entry.grid(row=0, column=1, columnspan=3, sticky="ew")

        tk.Label(self.root, text="Description").grid(row=1, column=0, sticky="e")
        self.description_entry = tk.Entry(self.root)
        self.description_entry.grid(row=1, column=1, columnspan=3, sticky="ew")

        tk.Button(self.root, text="Add Place Action", command=self.add_place_action).grid(row=2, column=0, sticky="ew")
        tk.Button(self.root, text="Add Upgrade Action", command=self.add_upgrade_action).grid(row=2, column=1, sticky="ew")
        tk.Button(self.root, text="Save", command=self.save).grid(row=2, column=2, sticky="ew")
        tk.Button(self.root, text="Open", command=self.open_config).grid(row=2, column=3, sticky="ew")

        self.action_listbox = tk.Listbox(self.root, height=10)
        self.action_listbox.grid(row=3, column=0, columnspan=3, pady=10, sticky="nsew")

        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.action_listbox.yview)
        scrollbar.grid(row=3, column=3, sticky="ns")
        self.action_listbox.config(yscrollcommand=scrollbar.set)

        tk.Button(self.root, text="Move Up", command=self.move_up).grid(row=4, column=0, sticky="ew")
        tk.Button(self.root, text="Move Down", command=self.move_down).grid(row=4, column=1, sticky="ew")
        tk.Button(self.root, text="Edit", command=self.edit_action).grid(row=4, column=2, sticky="ew")
        tk.Button(self.root, text="Delete", command=self.delete_action).grid(row=4, column=3, sticky="ew")

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_columnconfigure(3, weight=1)
        self.root.grid_rowconfigure(3, weight=1)

    def ids(self):
        return list(set(id_ for action in self.actions for id_ in action.ids if action.action_type == "place"))

    def add_place_action(self):
        dialog = CustomDialog(self.root, "Place Action", ["Enter tower IDs (ex. 1a 2b)\nPut in multiple ids separated by\nspaces to place multiple at once", "Enter location (center/edge)\nCan also enter 1 for center and 2 for edge"], ["", ""])
        if dialog.result:
            ids_str, location = dialog.result
            ids = ids_str.split()
            if all(id_[0] in ["1", "2", "3", "4", "5", "6"] for id_ in ids) and location in ["center", "edge", "1", "2"]:
                if location in ["1", "2"]:
                    location = "center" if location == "1" else "edge"
                if not self.are_ids_unique(ids):
                    messagebox.showerror("Error", "IDs must be unique")
                    return
                action = Action("place", ids=ids, location=location)
                self.actions.append(action)
                self.update_action_listbox()
            else:
                messagebox.showerror("Error", "Invalid IDs or location")

    def add_upgrade_action(self):
        dialog = CustomDialog(self.root, "Upgrade Action", ["Enter tower IDs (ex. 1a 2b)\nPut in multiple ids separated by spaces\nto cycle through upgrading each", "Enter number of times to upgrade tower\nType in 0 to continuously upgrade until end of game\nNo actions will work after upgrade 0 happens"], ["", ""])
        if dialog.result:
            ids_str, amount_str = dialog.result
            ids_ = ids_str.split()
            try:
                amount = int(amount_str)
                if all(id_ in self.ids() for id_ in ids_) and amount >= 0:
                    action = Action("upgrade", ids=ids_, amount=amount)
                    self.actions.append(action)
                    self.update_action_listbox()
                else:
                    messagebox.showerror("Error", "Invalid IDs or amount")
            except ValueError:
                messagebox.showerror("Error", "Invalid input format")

    def edit_action(self):
        selection = self.action_listbox.curselection()
        if selection:
            index = selection[0]
            action = self.actions[index]
            dialog = None
            if action.action_type == "place":
                dialog = CustomDialog(self.root, "Edit Place Action", ["Enter tower IDs (ex. 1a 2b)\nPut in multiple ids separated by\nspaces to place multiple at once", "Enter location (center/edge)\nCan also enter 1 for center and 2 for edge"], [action.ids, action.location])
            elif action.action_type == "upgrade":
                dialog = CustomDialog(self.root, "Edit Upgrade Action", ["Enter tower IDs (ex. 1a 2b)\nPut in multiple ids separated by spaces\nto cycle through upgrading each", "Enter number of times to upgrade tower\nType in 0 to continuously upgrade until end of game\nNo actions will work after upgrade 0 happens"], [action.ids, str(action.amount)])

            if dialog is not None and dialog.result:
                if action.action_type == "place":
                    ids_str, location = dialog.result
                    ids = ids_str.split()
                    if all(id_[0] in ["1", "2", "3", "4", "5", "6"] for id_ in ids) and location in ["center", "edge", "1", "2"]:
                        if location in ["1", "2"]:
                            location = "center" if location == "1" else "edge"
                        if not self.are_ids_unique(ids, action.ids):
                            messagebox.showerror("Error", "IDs must be unique")
                            return
                        action.ids = ids
                        action.location = location
                elif action.action_type == "upgrade":
                    ids_str, amount_str = dialog.result
                    ids_ = ids_str.split()
                    try:
                        amount = int(amount_str)
                        if all(id_ in self.ids() for id_ in ids_) and amount >= 0:
                            action.ids = ids_
                            action.amount = amount
                    except ValueError:
                        messagebox.showerror("Error", "Invalid input format")
                        return

                if self.is_valid_order():
                    self.update_action_listbox()
                    self.action_listbox.selection_set(index)
                else:
                    messagebox.showerror("Error", "Invalid order: cannot upgrade before placing")

    def are_ids_unique(self, new_ids, current_ids=None):
        if len(new_ids) != len(set(new_ids)):
            return False

        existing_ids = self.ids()
        print(existing_ids)
        if current_ids:
            existing_ids = [id_ for id_ in existing_ids if id_ not in current_ids]
        return all(new_id not in existing_ids for new_id in new_ids)

    def update_action_listbox(self):
        self.action_listbox.delete(0, tk.END)
        for action in self.actions:
            self.action_listbox.insert(tk.END, str(action))

    def move_up(self):
        selection = self.action_listbox.curselection()
        if selection:
            index = selection[0]
            if index > 0:
                self.actions[index], self.actions[index-1] = self.actions[index-1], self.actions[index]
                if self.is_valid_order():
                    self.update_action_listbox()
                    self.action_listbox.selection_set(index-1)
                    self.action_listbox.yview(index-1)
                else:
                    self.actions[index], self.actions[index-1] = self.actions[index-1], self.actions[index]
                    messagebox.showerror("Error", "Invalid order: cannot upgrade before placing")

    def move_down(self):
        selection = self.action_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.actions) - 1:
                self.actions[index], self.actions[index+1] = self.actions[index+1], self.actions[index]
                if self.is_valid_order():
                    self.update_action_listbox()
                    self.action_listbox.selection_set(index+1)
                    self.action_listbox.yview(index+1)
                else:
                    self.actions[index], self.actions[index+1] = self.actions[index+1], self.actions[index]
                    messagebox.showerror("Error", "Invalid order: cannot upgrade before placing")

    def delete_action(self):
        selection = self.action_listbox.curselection()
        if selection:
            index = selection[0]
            deleted_action = self.actions[index]
            del self.actions[index]
            if self.is_valid_order():
                self.update_action_listbox()
            else:
                messagebox.showerror("Error", "Invalid order: cannot upgrade before placing")
                self.actions.insert(index, deleted_action)

    def is_valid_order(self):
        placed_ids = set()
        for action in self.actions:
            if action.action_type == "place":
                placed_ids.update(action.ids)
            elif action.action_type == "upgrade":
                if not all(id_ in placed_ids for id_ in action.ids):
                    return False
        return True

    def save(self):
        name = self.name_entry.get()
        description = self.description_entry.get()
        if not name or not description:
            messagebox.showerror("Error", "Name and description cannot be empty")
            return

        if not self.is_valid_order():
            messagebox.showerror("Error", "Invalid order: cannot upgrade before placing")
            return

        hotkeys = list(set([id_[0] for id_ in self.ids()]))
        hotkeys.sort()

        cost_labels = [f"Cost of tower {hotkey}" for hotkey in hotkeys]
        initial_costs = ["" for _ in hotkeys]

        cost_dialog = CustomDialog(self.root, "Tower Costs", cost_labels, initial_costs)
        if cost_dialog.result:
            costs = {}
            for hotkey, cost in zip(hotkeys, cost_dialog.result):
                try:
                    cost = int(cost)
                    if cost > 0:
                        costs[hotkey] = str(cost)
                    else:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Error", f"Invalid cost for hotkey {hotkey}")
                    return

            data = {
                "name": name,
                "description": description,
                "actions": [{"type": action.action_type, "ids": action.ids, "location": action.location} if action.action_type == "place" else {"type": action.action_type, "ids": action.ids, "amount": action.amount} for action in self.actions],
                "costs": costs
            }

            filename = f"./custom-sequence/{name.replace(' ', '-').lower()}.json"
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)

            messagebox.showinfo("Success", f"Custom placement saved as {filename}")

    def open_config(self):
        filename = filedialog.askopenfilename(initialdir="./custom-sequence/", title="Select file", filetypes=(("JSON files", "*.json"),))
        if filename:
            with open(filename, "r") as f:
                data = json.load(f)

            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, data["name"])

            self.description_entry.delete(0, tk.END)
            self.description_entry.insert(0, data["description"])

            self.actions.clear()
            for action_data in data["actions"]:
                action = None
                if action_data["type"] == "place":
                    action = Action("place", action_data["ids"], location=action_data["location"])
                elif action_data["type"] == "upgrade":
                    action = Action("upgrade", action_data["ids"], amount=action_data["amount"])
                self.actions.append(action)

            self.update_action_listbox()
