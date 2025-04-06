import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import sv_ttk
import json
import os
import csv
from datetime import datetime
from collections import defaultdict


class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shared Expense Tracker")

        # Data storage
        self.friends = []
        self.expenses = []
        self.total_paid = {}
        self.total_owed = {}
        self.filtered_expenses = []
        self.selected_expense = None
        self.balances = defaultdict(float)  # To track individual balances

        self.create_widgets()
        self.load_friends()
        self.load_expenses()
        
        self.update_participants_checkboxes()
        self.refresh_totals_display()
        sv_ttk.set_theme("dark")  # Apply dark theme

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Add Friend section
        add_friend_frame = tk.LabelFrame(main_frame, text="Add Friend", font=(16), bd=2)
        add_friend_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.new_friend_var = tk.StringVar()
        ctk.CTkEntry(add_friend_frame, textvariable=self.new_friend_var, border_color="#0390fc").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ctk.CTkButton(add_friend_frame, text="Add Friend", command=self.add_friend,font=("",14,'bold')).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(add_friend_frame, text="Delete Selected", command=self.delete_selected_friends, fg_color="#FF6B6B", text_color="#050505",font=("",14,'bold'),hover_color="#FF4D4D").pack(side=tk.LEFT, padx=5)

        # Expense Input section
        expense_frame = tk.LabelFrame(main_frame, text="Add/Edit Expense", font=("",16), bd=2)
        expense_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(expense_frame, text="Date (YYYY-MM-DD):", font=('Century Gothic', 12)).grid(row=0, column=0, sticky="w")
        self.date_var = tk.StringVar(value=datetime.today().strftime('%Y-%m-%d'))
        ctk.CTkEntry(expense_frame, textvariable=self.date_var, border_color="#0390fc").grid(row=0, column=1, sticky="ew")

        ttk.Label(expense_frame, text="Description:", font=('Century Gothic', 12)).grid(row=1, column=0, sticky="w")
        self.desc_var = tk.StringVar()
        ctk.CTkEntry(expense_frame, textvariable=self.desc_var).grid(row=1, column=1, sticky="ew")

        ttk.Label(expense_frame, text="Amount:", font=('Century Gothic', 12)).grid(row=2, column=0, sticky="w")
        self.amount_var = tk.StringVar()
        self.am = ctk.CTkEntry(expense_frame, textvariable=self.amount_var, bg_color="#1c1c1c", border_color="#0390fc")
        self.am.grid(row=2, column=1, sticky="ew")

        ttk.Label(expense_frame, text="Payer:", font=('Century Gothic', 12)).grid(row=3, column=0, sticky="w")
        self.payer_var = ctk.StringVar()
        self.payer_combobox = ctk.CTkComboBox(expense_frame, values=self.friends, variable=self.payer_var, state="readonly")
        self.payer_combobox.grid(row=3, column=1, sticky="ew")

        ttk.Label(expense_frame, text="Participants:", font=('Century Gothic', 12)).grid(row=4, column=0, sticky="nw")
        self.participants_frame = ttk.Frame(expense_frame)
        self.participants_frame.grid(row=4, column=1, sticky="ew")

        self.edit_btn = ctk.CTkButton(expense_frame, text="Add Expense", command=self.add_update_expense,font=("",14,'bold'))
        self.edit_btn.grid(row=5, column=1, sticky="e", pady=5)

        # Filter section
        filter_frame = ttk.Frame(main_frame)
        filter_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(0,5))

        ttk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT)
        self.filter_var = tk.StringVar()
        self.filter_criteria = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                         values=["All", "Date", "Description", "Payer", "Participant"], 
                                         state="readonly", width=12)
        self.filter_criteria.pack(side=tk.LEFT, padx=5)
        self.filter_criteria.set("All")

        self.filter_value_var = tk.StringVar()
        self.filter_value = ctk.CTkEntry(filter_frame, textvariable=self.filter_value_var, width=150)
        self.filter_value.pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(filter_frame, text="Apply Filter", command=self.apply_filter,font=("",14,'bold')).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(filter_frame, text="Clear Filters", command=self.clear_filters, fg_color="#FF6B6B", text_color="#050505",font=("",14,'bold'), hover_color="#FF4D4D").pack(side=tk.LEFT, padx=5)

        # Expense List with Scrollbar
        list_frame = tk.LabelFrame(main_frame, text="Expenses", font=(16), bd=2)
        list_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)

        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('date', 'description', 'amount', 'payer', 'participants')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='browse')
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
 
        self.tree.heading('date', text='Date')
        self.tree.heading('description', text='Description')
        self.tree.heading('amount', text='Amount')
        self.tree.heading('payer', text='Payer')
        self.tree.heading('participants', text='Participants')

        self.tree.column('date', width=100, anchor="center")
        self.tree.column('description', width=150, anchor="center")
        self.tree.column('amount', width=80, anchor="center")
        self.tree.column('payer', width=100, anchor="center")
        self.tree.column('participants', width=200, anchor="center")

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<<TreeviewSelect>>', self.on_expense_select)

        # Controls
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)

        
        ctk.CTkButton(control_frame, text="Clear Expenses", command=self.clear_selected_expenses, fg_color="#FF6B6B", text_color="#050505",font=("",14,'bold'), hover_color="#FF4D4D").pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(control_frame, text="Clear All", command=self.clear_all_expenses, fg_color="#FF6B6B", text_color="#050505",font=("",14,'bold'), hover_color="#FF4D4D").pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(control_frame, text="Save as CSV", command=self.save_as_csv,font=("",14,'bold')).pack(side=tk.RIGHT, padx=5)

        # Totals Display with Scrollbar
        totals_frame = tk.LabelFrame(main_frame, text="Totals", font=(16), bd=2)
        totals_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)

        totals_tree_frame = ttk.Frame(totals_frame)
        totals_tree_frame.pack(fill=tk.BOTH, expand=True)

        self.totals_tree = ttk.Treeview(
            totals_tree_frame, columns=('friend', 'paid', 'owed', 'balance'), show='headings'
        )
        vsb_totals = ttk.Scrollbar(totals_tree_frame, orient="vertical", command=self.totals_tree.yview)
        self.totals_tree.configure(yscrollcommand=vsb_totals.set)

        self.totals_tree.heading('friend', text='Friend', anchor="center")
        self.totals_tree.column('friend', anchor="center")
        self.totals_tree.heading('paid', text='Total Paid', anchor="center")
        self.totals_tree.column('paid', anchor="center")
        self.totals_tree.heading('owed', text='Total Owed', anchor="center")
        self.totals_tree.column('owed', anchor="center")
        self.totals_tree.heading('balance', text='Balance', anchor="center")
        self.totals_tree.column('balance', anchor="center")

        self.totals_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb_totals.pack(side=tk.RIGHT, fill=tk.Y)

        # Payment Instructions Display
        payments_frame = tk.LabelFrame(main_frame, text="Payment Instructions", font=(16), bd=2)
        payments_frame.grid(row=2, column=1, rowspan=3, sticky="nsew", padx=5, pady=5)

        self.payments_text = tk.Text(payments_frame, wrap=tk.WORD, height=10)
        payments_scroll = ttk.Scrollbar(payments_frame, command=self.payments_text.yview)
        self.payments_text.configure(yscrollcommand=payments_scroll.set, font=("Century Gothic",14))

        payments_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.payments_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

        style = ttk.Style()
        self.root.configure(bg=style.lookup("TLabelFrame", "background"))

    def calculate_payments(self):
        """Calculate who needs to pay whom and display the instructions"""
        # Clear previous instructions
        self.payments_text.delete(1.0, tk.END)
        
        # Calculate net balances for each friend
        balances = defaultdict(float)
        for friend in self.friends:
            balances[friend] = self.total_paid.get(friend, 0) - self.total_owed.get(friend, 0)
        
        # Separate creditors and debtors
        creditors = {k: v for k, v in balances.items() if v > 0}
        debtors = {k: v for k, v in balances.items() if v < 0}
        
        # Sort by amount (highest first for creditors, lowest first for debtors)
        creditors = dict(sorted(creditors.items(), key=lambda item: -item[1]))
        debtors = dict(sorted(debtors.items(), key=lambda item: item[1]))
        
        # Generate payment instructions
        for debtor, debt_amount in debtors.items():
            debt_amount = abs(debt_amount)
            remaining_debt = debt_amount
            
            for creditor, credit_amount in creditors.items():
                if credit_amount == 0:
                    continue
                
                if credit_amount >= remaining_debt:
                    payment = remaining_debt
                    creditors[creditor] -= payment
                    self.payments_text.insert(tk.END, f"{debtor} should pay ₹{payment:.2f} to {creditor}\n")
                    break
                else:
                    payment = credit_amount
                    remaining_debt -= payment
                    creditors[creditor] = 0
                    self.payments_text.insert(tk.END, f"{debtor} should pay ₹{payment:.2f} to {creditor}\n")
        
        # If no payments needed
        if not self.payments_text.get(1.0, tk.END).strip():
            self.payments_text.insert(tk.END, "No payments needed - all balances are settled\n")

    def add_friend(self):
        try:
            new_friend = self.new_friend_var.get().strip()
            if new_friend and new_friend not in self.friends:
                self.friends.append(new_friend)
                self.total_paid[new_friend] = 0.0
                self.total_owed[new_friend] = 0.0
                self.new_friend_var.set('')
                self.update_participants_checkboxes()
                self.payer_combobox.configure(values=self.friends)
                self.save_friends()
                self.refresh_totals_display()
                self.calculate_payments()
            
            if not new_friend:
                messagebox.showerror("Error", "Please Enter Friend Name.")
                return
        except ValueError as ve:
            messagebox.showerror("Error", f"Invalid input: {ve}")

    def delete_selected_friends(self):
        selected_friends = [friend for friend, var in self.participant_vars.items() if var.get()]
        
        if not selected_friends:
            messagebox.showwarning("No Selection", "Please select friends to delete by checking their checkboxes")
            return
            
        if messagebox.askyesno("Confirm", f"Delete selected friends?\nThis will also remove all related expenses."):
            # Remove expenses involving these friends
            self.expenses = [exp for exp in self.expenses 
                           if exp['payer'] not in selected_friends 
                           and not any(p in selected_friends for p in exp['participants'])]
            
            # Remove the friends
            for friend in selected_friends:
                if friend in self.friends:
                    self.friends.remove(friend)
                    if friend in self.total_paid:
                        del self.total_paid[friend]
                    if friend in self.total_owed:
                        del self.total_owed[friend]
            
            # Reset totals
            for friend in self.friends:
                self.total_paid[friend] = 0.0
                self.total_owed[friend] = 0.0
            
            # Recalculate totals from remaining expenses
            for expense in self.expenses:
                payer = expense['payer']
                amount = float(expense['amount'])
                participants = expense['participants']
                
                self.total_paid[payer] += amount
                share = amount / len(participants)
                for participant in participants:
                    self.total_owed[participant] += share
            
            self.update_participants_checkboxes()
            self.payer_combobox['values'] = self.friends
            self.refresh_expense_list()
            self.refresh_totals_display()
            self.save_friends()
            self.save_expenses()
            self.calculate_payments()

    def add_update_expense(self):
        if self.selected_expense is not None:
            self.update_expense()
        else:
            self.add_expense()

    def add_expense(self):
        try:
            date_str = self.date_var.get()
            date = datetime.strptime(date_str, "%Y-%m-%d")
            description = self.desc_var.get().strip()
            amount = float(self.amount_var.get())
            payer = self.payer_var.get()
            participants = [friend for friend, var in self.participant_vars.items() if var.get()]
            
            if not description:
                raise ValueError("Description is required")
            if amount <= 0:
                raise ValueError("Amount must be positive")
            if not payer:
                raise ValueError("Please select a payer")
            if not participants:
                raise ValueError("Please select at least one participant")
            
            # Add expense
            expense = {
                'date': date_str,
                'description': description,
                'amount': amount,
                'payer': payer,
                'participants': participants
            }
            self.expenses.append(expense)
            self.filtered_expenses = self.expenses.copy()
            
            # Update totals
            num_participants = len(participants)
            share = amount / num_participants
            self.total_paid[payer] += amount
            for participant in participants:
                self.total_owed[participant] += share
            
            # Clear inputs
            self.desc_var.set('')
            self.amount_var.set('')
            self.payer_var.set('')
            for var in self.participant_vars.values():
                var.set(False)

            self.refresh_expense_list()
            self.refresh_totals_display()
            self.save_expenses()
            self.calculate_payments()
            
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def update_expense(self):
        try:
            # Remove old expense impact
            old_expense = self.expenses[self.selected_expense]
            old_amount = old_expense['amount']
            old_payer = old_expense['payer']
            old_participants = old_expense['participants']
            old_share = old_amount / len(old_participants)
            
            self.total_paid[old_payer] -= old_amount
            for participant in old_participants:
                self.total_owed[participant] -= old_share

            # Add new expense values
            date_str = self.date_var.get()
            date = datetime.strptime(date_str, "%Y-%m-%d")
            description = self.desc_var.get().strip()
            amount = float(self.amount_var.get())
            payer = self.payer_var.get()
            participants = [friend for friend, var in self.participant_vars.items() if var.get()]
            
            if not description:
                raise ValueError("Description is required")
            if amount <= 0:
                raise ValueError("Amount must be positive")
            if not payer:
                raise ValueError("Please select a payer")
            if not participants:
                raise ValueError("Please select at least one participant")
            
            # Update expense
            new_expense = {
                'date': date_str,
                'description': description,
                'amount': amount,
                'payer': payer,
                'participants': participants
            }
            self.expenses[self.selected_expense] = new_expense
            self.filtered_expenses = self.expenses.copy()
            
            # Update totals with new values
            share = amount / len(participants)
            self.total_paid[payer] += amount
            for participant in participants:
                self.total_owed[participant] += share
            
            # Clear selection and inputs
            self.selected_expense = None
            self.edit_btn.configure(text="Add Expense")
            self.tree.selection_remove(self.tree.selection())
            self.desc_var.set('')
            self.amount_var.set('')
            self.payer_var.set('')
            for var in self.participant_vars.values():
                var.set(False)
            
            self.refresh_expense_list()
            self.refresh_totals_display()
            self.calculate_payments()
            
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def on_expense_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.selected_expense = self.tree.index(selected[0])
            expense = self.expenses[self.selected_expense]
            
            self.date_var.set(expense['date'])
            self.desc_var.set(expense['description'])
            self.amount_var.set(str(expense['amount']))
            self.payer_var.set(expense['payer'])
            
            for friend, var in self.participant_vars.items():
                var.set(friend in expense['participants'])
            
            self.edit_btn.configure(text="Update Expense")

    def update_participants_checkboxes(self):
        for widget in self.participants_frame.winfo_children():
            widget.destroy()

        self.participant_vars = {}
        for friend in self.friends:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(self.participants_frame, text=friend, variable=var)
            cb.pack(anchor="w", side="left", padx=5)
            self.participant_vars[friend] = var

    def refresh_expense_list(self):
        self.tree.delete(*self.tree.get_children())
        for expense in self.filtered_expenses:
            participants = ", ".join(expense['participants'])
            self.tree.insert(
                '',
                'end',
                values=(
                    expense['date'],
                    expense['description'],
                    f"₹{expense['amount']:.2f}",
                    expense['payer'],
                    participants,
                ),
            )

    def refresh_totals_display(self):
        self.totals_tree.delete(*self.totals_tree.get_children())
        for friend in self.friends:
            paid = self.total_paid.get(friend, 0)
            owed = self.total_owed.get(friend, 0)
            balance = paid - owed
            self.totals_tree.insert(
                '',
                'end',
                values=(
                    friend,
                    f"₹{paid:.2f}",
                    f"₹{owed:.2f}",
                    f"₹{balance:.2f}",
                ),
            )

    def apply_filter(self):
        filter_type = self.filter_var.get()
        filter_value = self.filter_value_var.get().lower()
        
        if filter_type == "All":
            self.filtered_expenses = self.expenses.copy()
        else:
            self.filtered_expenses = []
            for expense in self.expenses:
                if filter_type == "Date" and filter_value in expense['date'].lower():
                    self.filtered_expenses.append(expense)
                elif filter_type == "Description" and filter_value in expense['description'].lower():
                    self.filtered_expenses.append(expense)
                elif filter_type == "Payer" and filter_value in expense['payer'].lower():
                    self.filtered_expenses.append(expense)
                elif filter_type == "Participant":
                    participants = [p.lower() for p in expense['participants']]
                    if any(filter_value in p for p in participants):
                        self.filtered_expenses.append(expense)
        
        self.refresh_expense_list()

    def clear_filters(self):
        self.filter_var.set("All")
        self.filter_value_var.set("")
        self.filtered_expenses = self.expenses.copy()
        self.refresh_expense_list()

    def clear_selected_expenses(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select expenses to delete")
            return
            
        if messagebox.askyesno("Confirm", "Delete selected expenses?"):
            # Get indices of selected items (sorted in reverse to avoid index shifting)
            indices = sorted([self.tree.index(item) for item in selected_items], reverse=True)
            
            for idx in indices:
                if idx < len(self.expenses):
                    # Remove expense impact on totals
                    expense = self.expenses[idx]
                    amount = expense['amount']
                    payer = expense['payer']
                    participants = expense['participants']
                    share = amount / len(participants)
                    
                    self.total_paid[payer] -= amount
                    for participant in participants:
                        self.total_owed[participant] -= share
                    
                    # Remove the expense
                    del self.expenses[idx]
            
            self.filtered_expenses = self.expenses.copy()
            self.selected_expense = None
            self.edit_btn.configure(text="Add Expense")
            self.desc_var.set('')
            self.amount_var.set('')
            self.payer_var.set('')
            for var in self.participant_vars.values():
                var.set(False)
            
            self.refresh_expense_list()
            self.refresh_totals_display()
            self.save_expenses()
            self.calculate_payments()

    def clear_all_expenses(self):
        if messagebox.askyesno("Confirm", "Clear all expenses?"):
            self.expenses.clear()
            self.filtered_expenses.clear()
            for friend in self.friends:
                self.total_paid[friend] = 0.0
                self.total_owed[friend] = 0.0
            self.refresh_expense_list()
            self.refresh_totals_display()
            self.save_expenses()
            self.payments_text.delete(1.0, tk.END)

    def save_as_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save expenses as CSV"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Write header
                writer.writerow(['Date', 'Description', 'Amount', 'Payer', 'Participants'])
                
                # Write data
                for expense in self.expenses:
                    participants = ', '.join(expense['participants'])
                    writer.writerow([
                        expense['date'],
                        expense['description'],
                        expense['amount'],
                        expense['payer'],
                        participants
                    ])
                    
            messagebox.showinfo("Success", f"Expenses saved successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV: {str(e)}")

    def save_expenses(self):
        try:
            with open("expenses.json", "w") as f:
                json.dump(self.expenses, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save expenses: {e}")

    def load_expenses(self):
        if os.path.exists("expenses.json"):
            try:
                with open("expenses.json", "r") as f:
                    self.expenses = json.load(f)
            
                self.total_paid = {friend: 0.0 for friend in self.friends}
                self.total_owed = {friend: 0.0 for friend in self.friends}
            
                for expense in self.expenses:
                    payer = expense['payer']
                    amount = float(expense['amount'])
                    participants = expense['participants']
                
                    self.total_paid[payer] += amount
                
                    share = amount / len(participants)
                    for participant in participants:
                        self.total_owed[participant] += share
            
                self.filtered_expenses = self.expenses.copy()
                self.refresh_expense_list()
                self.refresh_totals_display()
                self.calculate_payments()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load expenses: {e}")

    def save_friends(self):
        try:
            with open("friends.json", "w") as f:
                json.dump(self.friends, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save friends: {e}")

    def load_friends(self):
        if os.path.exists("friends.json"):
            try:
                with open("friends.json", "r") as f:
                    self.friends = json.load(f)
            
                for friend in self.friends:
                    self.total_paid[friend] = self.total_paid.get(friend, 0.0)
                    self.total_owed[friend] = self.total_owed.get(friend, 0.0)
            
                self.payer_combobox.configure(values=self.friends)
                self.update_participants_checkboxes()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load friends: {e}")


if __name__ == "__main__":
    root = ctk.CTk()
    app = ExpenseTrackerApp(root)
    root.mainloop()