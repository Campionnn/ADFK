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
        self.bind("<Return>", self.on_ok)
        self.lift()
        self.focus_set()
        self.wait_window(self)

    def on_ok(self, event=None):
        self.result = [entry.get() for entry in self.entries]
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


class Action:
    def __init__(self, action_type, ids=None, location=None, amount=None):
        self.action_type = action_type
        self.ids = ids
        self.location = location
        self.amount = amount

    def __str__(self):
        if self.action_type == "place":
            return f"Place {self.ids} at {self.location}"
        elif self.action_type == "upgrade":
            return f"Upgrade {self.ids} by {self.amount}"
        elif self.action_type == "auto_use":
            return f"Toggle auto use ability for {self.ids}"
        elif self.action_type == "wait_money":
            return f"Wait for ¥{self.amount}"
        elif self.action_type == "wait_time":
            return f"Wait for {self.amount} seconds"
        elif self.action_type == "wait_wave":
            return f"Wait for wave {self.amount}"
        elif self.action_type == "sell":
            return f"Sell {self.ids}"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Custom Sequence")
        self.actions = []

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Name").grid(row=0, column=0, sticky="e")
        self.name_entry = tk.Entry(self.root)
        self.name_entry.grid(row=0, column=1, columnspan=2, sticky="ew")

        tk.Label(self.root, text="Description").grid(row=1, column=0, sticky="e")
        self.description_entry = tk.Entry(self.root)
        self.description_entry.grid(row=1, column=1, columnspan=2, sticky="ew")

        self.action_type_var = tk.StringVar(self.root)
        self.action_type_var.set("Add Action")
        self.action_type_menu = tk.OptionMenu(self.root, self.action_type_var, "Place", "Upgrade", "Auto Use Ability", "Wait For Money", "Wait For Time", "Wait For Wave", "Sell", command=self.on_action_select)
        self.action_type_menu.grid(row=2, column=0, sticky="ew")

        tk.Button(self.root, text="Save", command=self.save).grid(row=2, column=2, sticky="ew")
        tk.Button(self.root, text="Open", command=self.open_config).grid(row=2, column=3, sticky="ew")

        listbox_frame = tk.Frame(self.root)
        listbox_frame.grid(row=3, column=0, columnspan=4, pady=10, sticky="nsew")

        self.action_listbox = tk.Listbox(listbox_frame, height=10)
        self.action_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", command=self.action_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
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

        self.action_listbox.bind("<Delete>", self.delete_action)
        self.action_listbox.bind("<Double-1>", self.edit_action)

    def ids(self):
        ids = []
        for action in self.actions:
            if action.action_type == "place":
                ids.extend(action.ids)
        return list(set(ids))

    def on_action_select(self, _):
        action_type = self.action_type_var.get()
        if action_type == "Place":
            self.add_place_action()
        elif action_type == "Upgrade":
            self.add_upgrade_action()
        elif action_type == "Auto Use Ability":
            self.add_auto_use_action()
        elif action_type == "Wait For Money":
            self.add_wait_money_action()
        elif action_type == "Wait For Time":
            self.add_wait_time_action()
        elif action_type == "Wait For Wave":
            self.add_wait_wave_action()
        elif action_type == "Sell":
            self.add_sell_action()
        self.action_type_var.set("Add Action")

    def add_place_action(self):
        dialog = CustomDialog(self.root, "Place Action", ["Enter tower IDs (ex. 1a 2b)\nPut in multiple IDs separated by\nspaces to place multiple at once", "Enter location (center/edge)\nCan also enter 1 for center and 2 for edge"], ["", ""])
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
        dialog = CustomDialog(self.root, "Upgrade Action", ["Enter tower IDs (ex. 1a 2b)\nPut in multiple IDs separated by spaces\nto cycle through upgrading each", "Enter number of times to upgrade tower\nType in 0 to continuously upgrade until end of game\nNo actions will work after upgrade 0 happens"], ["", ""])
        if dialog.result:
            ids_str, amount_str = dialog.result
            ids = ids_str.split()
            try:
                amount = int(amount_str)
                if len(ids) > 0 and all(id_ in self.ids() for id_ in ids) and amount >= 0:
                    action = Action("upgrade", ids=ids, amount=amount)
                    self.actions.append(action)
                    self.update_action_listbox()
                else:
                    messagebox.showerror("Error", "Invalid IDs or amount")
            except ValueError:
                messagebox.showerror("Error", "Invalid input format")

    def add_auto_use_action(self):
        dialog = CustomDialog(self.root, "Auto Use Ability Action", ["Enter tower IDs (ex. 1a 2b)\nPut in multiple IDs separated by spaces\nto toggle auto use for each tower"], [""])
        if dialog.result:
            ids_str = dialog.result[0]
            ids = ids_str.split()
            if len(ids) > 0 and all(id_ in self.ids() for id_ in ids):
                action = Action("auto_use", ids=ids)
                self.actions.append(action)
                self.update_action_listbox()
            else:
                messagebox.showerror("Error", "Invalid IDs")

    def add_wait_money_action(self):
        dialog = CustomDialog(self.root, "Wait For Money Action", ["Enter amount of money to wait for"], [""])
        if dialog.result:
            try:
                amount = int(dialog.result[0])
                if amount > 0:
                    action = Action("wait_money", amount=amount)
                    self.actions.append(action)
                    self.update_action_listbox()
                else:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Invalid amount")

    def add_wait_time_action(self):
        dialog = CustomDialog(self.root, "Wait For Time Action", ["Enter amount of time to wait for in seconds"], [""])
        if dialog.result:
            try:
                amount = int(dialog.result[0])
                if amount > 0:
                    action = Action("wait_time", amount=amount)
                    self.actions.append(action)
                    self.update_action_listbox()
                else:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Invalid amount")

    def add_wait_wave_action(self):
        dialog = CustomDialog(self.root, "Wait For Wave Action", ["Enter wave to wait for"], [""])
        if dialog.result:
            try:
                amount = int(dialog.result[0])
                if amount > 0:
                    action = Action("wait_wave", amount=amount)
                    self.actions.append(action)
                    self.update_action_listbox()
                else:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Invalid amount")

    def add_sell_action(self):
        dialog = CustomDialog(self.root, "Sell Action", ["Enter tower IDs (ex. 1a 2b)\nPut in multiple IDs separated by spaces\nto sell multiple at once"], [""])
        if dialog.result:
            ids_str = dialog.result[0]
            ids = ids_str.split()
            if len(ids) > 0 and all(id_ in self.ids() for id_ in ids):
                action = Action("sell", ids=ids)
                self.actions.append(action)
                self.update_action_listbox()
            else:
                messagebox.showerror("Error", "Invalid IDs")

    def edit_action(self, event=None):
        selection = self.action_listbox.curselection()
        if selection:
            index = selection[0]
            action = self.actions[index]
            dialog = None
            if action.action_type == "place":
                dialog = CustomDialog(self.root, "Edit Place Action", ["Enter tower IDs (ex. 1a 2b)\nPut in multiple IDs separated by\nspaces to place multiple at once", "Enter location (center/edge)\nCan also enter 1 for center and 2 for edge"], [action.ids, action.location])
            elif action.action_type == "upgrade":
                dialog = CustomDialog(self.root, "Edit Upgrade Action", ["Enter tower IDs (ex. 1a 2b)\nPut in multiple IDs separated by spaces\nto cycle through upgrading each", "Enter number of times to upgrade tower\nType in 0 to continuously upgrade until end of game\nNo actions will work after upgrade 0 happens"], [action.ids, str(action.amount)])

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

                self.update_action_listbox()
                self.action_listbox.selection_set(index)

    def are_ids_unique(self, new_ids, current_ids=None):
        if len(new_ids) != len(set(new_ids)):
            return False

        existing_ids = self.ids()
        if current_ids:
            existing_ids = [id_ for id_ in existing_ids if id_ not in current_ids]
        return all(new_id not in existing_ids for new_id in new_ids)

    def update_action_listbox(self):
        self.action_listbox.delete(0, tk.END)
        for index, action in enumerate(self.actions):
            self.action_listbox.insert(tk.END, f"{index + 1}: {str(action)}")

    def move_up(self):
        selection = self.action_listbox.curselection()
        if selection:
            index = selection[0]
            if index > 0:
                self.actions[index], self.actions[index-1] = self.actions[index-1], self.actions[index]
                self.update_action_listbox()
                self.action_listbox.selection_set(index-1)
                self.action_listbox.yview(index-1)

    def move_down(self):
        selection = self.action_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.actions) - 1:
                self.actions[index], self.actions[index+1] = self.actions[index+1], self.actions[index]
                self.update_action_listbox()
                self.action_listbox.selection_set(index+1)
                self.action_listbox.yview(index+1)

    def delete_action(self, event=None):
        selection = self.action_listbox.curselection()
        if selection:
            index = selection[0]
            del self.actions[index]
            self.update_action_listbox()

    def is_valid_order(self):
        placed_ids = set()
        for index, action in enumerate(self.actions):
            if action.action_type == "place":
                placed_ids.update(set(action.ids))
            elif action.action_type == "upgrade":
                invalid_ids = [id_ for id_ in action.ids if id_ not in placed_ids]
                if invalid_ids:
                    messagebox.showerror("Invalid Order", f"Upgrade action at step {index + 1} is invalid.\nCannot upgrade tower(s) {', '.join(invalid_ids)} before they are placed or after they are sold.")
                    return False
            elif action.action_type == "auto_use":
                if not all(id_ in placed_ids for id_ in action.ids):
                    messagebox.showerror("Invalid Order", f"Auto use action at step {index + 1} is invalid.\nCannot toggle auto use for tower(s) {', '.join(action.ids)} that are not placed or after they are sold.")
                    return False
            elif action.action_type == "sell":
                if not all(id_ in placed_ids for id_ in action.ids):
                    messagebox.showerror("Invalid Order", f"Sell action at step {index + 1} is invalid.\nCannot sell tower(s) {', '.join(action.ids)} that are not placed.")
                    return False
                placed_ids.difference_update(set(action.ids))
        return True

    def save(self):
        name = self.name_entry.get()
        description = self.description_entry.get()
        if not name or not description:
            messagebox.showerror("Error", "Name and description cannot be empty")
            return

        if not self.is_valid_order():
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
                "actions": [],
                "costs": costs
            }
            for action in self.actions:
                action_data = {
                    "type": action.action_type,
                }
                if action.ids is not None:
                    action_data["ids"] = action.ids
                if action.location is not None:
                    action_data["location"] = action.location
                if action.amount is not None:
                    action_data["amount"] = action.amount
                data["actions"].append(action_data)

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
                    action = Action("place", ids=action_data["ids"], location=action_data["location"])
                elif action_data["type"] == "upgrade":
                    action = Action("upgrade", ids=action_data["ids"], amount=action_data["amount"])
                elif action_data["type"] == "auto_use":
                    action = Action("auto_use", ids=action_data["ids"])
                elif action_data["type"] == "wait_money":
                    action = Action("wait_money", amount=action_data["amount"])
                elif action_data["type"] == "wait_time":
                    action = Action("wait_time", amount=action_data["amount"])
                elif action_data["type"] == "wait_wave":
                    action = Action("wait_wave", amount=action_data["amount"])
                elif action_data["type"] == "sell":
                    action = Action("sell", ids=action_data["ids"])
                self.actions.append(action)

            self.update_action_listbox()
