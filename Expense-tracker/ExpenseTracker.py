"""
Dominick Jean

Python expense tracker
"""
import matplotlib.pyplot as plt
import numpy as np


# class that holds values for each expense
class Expense:
    def __init__(self, info, cycle, amount):
        self.info = info
        self.cycle = cycle
        self.amount = amount


# class that holds each expense and can be edited
class ExpenseTracker:
    def __init__(self):
        self.expenses = []          # holds expenses
        self.pay = 0.00             # holds pay
        self.isSaving = False       # are they saving?
        self.saveType = None        # how are they saving?
        self.saveAmount = 0.00      # how much they plan to save
        self.savings = 0.00         # how much they've saved
        self.goal = 0.00            # save goal

    # add pay
    def set_pay(self, pay):
        self.pay = pay

    # sets if they're saving
    def is_saving(self, isSaving, saveType, saveAmount):
        self.isSaving = isSaving
        self.saveType = saveType
        self.saveAmount = saveAmount

    # add expense to the list
    def add_expense(self, expense):
        self.expenses.append(expense)

    # delete expense from list while checking if index is true
    def remove_expense(self, index):
        if 0 <= index < len(self.expenses):
            del self.expenses[index]
            print("Expense removed.")
        else:
            print("Invalid index.")

    # show expenses
    def view_expenses(self):
        if len(self.expenses) == 0:                     # Check if empty
            print("There are currently no expenses.")
        else:                                           # Goes through the list and print
            print("Expense list:")
            for i, expense in enumerate(self.expenses, start=1):
                print(f"{i}. Info: {expense.info}, Cycle: {expense.cycle}, Amount: ${expense.amount:.2f}")

    # adds everything together
    def total_expenses(self):
        total = sum(expense.amount for expense in self.expenses)
        print(f"Total Expenses: ${total:.2f}")

    def yearly_balance(self):
        # if there are expenses, calculate the monthly, yearly, and total
        if len(self.expenses) != 0:
            monthly_expenses = sum(expense.amount for expense in self.expenses if expense.cycle == 'monthly')
            yearly_expenses = sum(expense.amount for expense in self.expenses if expense.cycle == 'yearly')
            total_expenses = (monthly_expenses * 12) + yearly_expenses

        # if saving, calculate the save amount
        if self.isSaving:
            if self.saveType == "fixed":                            # If having a fixed save amount
                total = self.pay - self.saveAmount                  # get balance minus what's saved
                total *= 12
                self.savings = self.saveAmount                      # get save total
                saveTotal = self.savings * 12
                if self.goal > 0.00:                                # find time until save goal reached
                    goalReachTime = self.goal / self.saveAmount
            else:                                                   # If having a percent save amount
                self.savings = self.pay * (self.saveAmount / 100)   # get monthly save
                total = self.pay - self.savings                     # get balance minus what's saved
                total *= 12
                saveTotal = self.savings * 12                       # get save total
                if self.goal > 0.00:                                # find time until save goal reached
                    goalReachTime = self.goal / self.savings
        else:
            total = self.pay * 12                                   # get balance without any in savings

        if len(self.expenses) != 0:
            total -= total_expenses

        # prints out everything
        print(f"Yearly pay: ${(self.pay * 12):.2f}")
        if len(self.expenses) != 0:
            print(f"Total monthly expenses: -${monthly_expenses:.2f}")
            print(f"Total yearly expenses: -${yearly_expenses:.2f}")
            print(f"Total expenses: -${total_expenses:.2f}")
        print(f"Yearly Balance: ${total:.2f}")
        print(f"Savings for the entire year: ${saveTotal:.2f}")
        if self.goal > 0.00:
            print(f"Time until save goal reached: {goalReachTime:.1f} Months")

    # set the save goal
    def set_save_goal(self, goal):
        self.goal = goal

    # prints the balance chart
    def show_chart(self):
        months = np.arange(1, 13)
        monthly_savings = np.full((12,), self.savings if self.isSaving else 0)
        monthly_expenses = np.array(
            [sum(expense.amount for expense in self.expenses if expense.cycle == 'monthly')] * 12)
        monthly_pay = np.full((12,), self.pay)

        # Calculate the cumulative sum for savings and expenses
        cumulative_savings = np.cumsum(monthly_savings)
        cumulative_expenses = np.cumsum(monthly_expenses)

        # Balance is pay minus expenses plus savings
        cumulative_balance = (monthly_pay * months) - cumulative_expenses + cumulative_savings

        plt.figure(figsize=(10, 5))
        plt.plot(months, cumulative_savings, label='Savings', color='blue', marker='o')
        plt.plot(months, cumulative_expenses, label='Expenses', color='red', marker='o')
        plt.plot(months, cumulative_balance, label='Balance', color='purple', marker='o')

        plt.title('Financial Overview Through the Year')
        plt.xlabel('Month')
        plt.ylabel('Cumulative Amount ($)')
        plt.legend()
        plt.grid(True)
        plt.xticks(months)
        plt.tight_layout()
        plt.show()


# reusable function for getting float input
def GetFloat(msg, errorMsg):
    while True:
        try:
            amount = float(input(msg))
        except ValueError:
            print(errorMsg)
            continue
        else:
            print()
            break

    return amount


# reusable function for getting int input
def GetInt(msg, errorMsg):
    while True:
        try:
            amount = int(input(msg))
        except ValueError:
            print(errorMsg)
            continue
        else:
            print()
            break

    return amount


# prompts the user for their pay
def GetPay():
    print("How often are you paid?")
    while True:
        cycle = GetInt("Weekly(1), Bi-Weekly(2), or Monthly(3): ", "Invalid response.")

        if cycle == 1:
            pay = GetFloat("Enter weekly pay: ", "Invalid response. Please try again.")
            pay *= 4
            print(f"Possible monthly pay: ${pay:.2f}")
            break
        elif cycle == 2:
            pay = GetFloat("Enter bi-weekly pay: ", "Invalid response. Please try again.")
            pay *= 2
            print(f"Possible monthly pay: ${pay:.2f}")
            break
        elif cycle == 3:
            pay = GetFloat("Enter monthly pay: ", "Invalid response. Please try again.")
            print(f"Monthly pay: ${pay:.2f}")
            break
        else:
            print("Invalid response. Please select (1-3)")

    return pay


# main function
def main():
    tracker = ExpenseTracker()  # sets the expenseTracker
    tracker.set_pay(GetPay())   # sets the pay
    print("\n----------------------------------")
    while True:                 # asks if the user is saving
        print("Are you saving?")
        print("1. Yes")
        print("2. No")
        response = GetInt("Please select (1-2): ", "Sorry, I didn't get that.")     # reusable response variable

        if response == 1:       # asks how they plan to save
            print("Savings option:")
            print("1. Fixed")
            print("2. Percentage")
            while True:
                saveType = GetInt("Please select (1-2): ", "Sorry, I didn't get that.")

                if saveType == 1:   # fixed savings
                    tracker.is_saving(True, "fixed", GetFloat("Enter amount saved per month: $", "Invalid input"))
                    break
                elif saveType == 2: # percent savings
                    tracker.is_saving(True, "percentage", GetFloat("Enter percentage saved per month: ", "Invalid input"))
                    break
                else:
                    print("Invalid input.")

            break
        elif response == 2:
            break
        else:
            print("Invalid input.")

    if response == 1:
        while True:             # asks for save goal
            print("Do you have a save goal?")
            print("1. Yes")
            print("2. No")
            response = GetInt("Please select (1-2): ", "Sorry, I didn't get that.")

            if response == 1:   # enter save goal
                tracker.set_save_goal(GetFloat("Enter goal amount: $", "Invalid response"))
                break
            elif response == 2:
                break
            else:
                print("Invalid input.")


    # main menu
    while True:
        print("\n----------------------------------")
        print("Expense Tracker Menu")
        print("1. Add Expense")
        print("2. Remove Expense")
        print("3. View Expense")
        print("4. Total Expense")
        print("5. Yearly Balance")
        print("6. Exit")

        select = GetInt("Please select (1-6): ", "Sorry, I didn't get that.")

        if select == 1:                             # Add Expense
            info = input("Enter the description: ") # expense description
            while True:                             # checks for monthly or yearly expense
                print("Enter Monthly or Yearly?")
                print("1. Monthly")
                print("2. Yearly")
                response = GetInt("Please select (1-2): ", "Sorry, I didn't get that.")
                if response == 1:
                    cycle = "monthly"
                    break
                elif response == 2:
                    cycle = "yearly"
                    break
                else:
                    print("Invalid input.")

            amount = GetFloat("Enter the amount: ", "Invalid input.")   # expense cost
            expense = Expense(info, cycle, amount)                      # set variable with expense class
            tracker.add_expense(expense)                                # add to tracker list
            print("Expense added successfully.")
        elif select == 2:                             # Remove Expense
            index = GetInt("Enter expense index to remove: ", "Invalid input.")
            tracker.remove_expense(index - 1)
        elif select == 3:                             # View Expense
            tracker.view_expenses()
        elif select == 4:                             # Total Expense
            tracker.total_expenses()
        elif select == 5:                             # Yearly Balance
            tracker.yearly_balance()
            tracker.show_chart()
        elif select == 6:                             # Exit
            print("Goodbye")
            break
        else:                                         # Invalid input
            print("Invalid response. Try again.")


main()