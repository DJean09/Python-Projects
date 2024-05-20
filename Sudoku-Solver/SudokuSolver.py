"""
Dominick Jean

Sudoku Solver
"""
def get_number():
    while True:
        num = input("Enter a number (0-9): ")
        if num.isdigit() and 0 <= int(num) <= 9:
            return int(num)
        else:
            print("Invalid input. Please enter a number between 0 and 9.")


def fill_board(board_size):
    board = []  # Initialize the empty board
    for row in range(board_size):
        current_row = []
        if row == 3 or row == 7:
            print(end="")
        elif row >= 7:
            print(f"Enter numbers for row {row - 1}:")
        elif row >= 4:
            print(f"Enter numbers for row {row}:")
        else:
            print(f"Enter numbers for row {row + 1}:")
        for col in range(board_size):
            if (row == 3 or row == 7) and (col == 3 or col == 7):
                num = ""
            elif row == 3 or row == 7:
                num = ""
            elif col == 3 or col == 7:
                num = ""
            else:
                num = get_number()
            current_row.append(num)
        board.append(current_row)
    return board


def change_row(board):
    while True:
        row = get_int("Please enter the row number (1-9): ", "Invalid input.")

        if 0 < row < 10:
            if row > 6:
                row += 2
            elif row > 3:
                row += 1

            break
        else:
            print("Not within the number range (1-9)")

    for col in range(11):
        if (row == 3 or row == 7) and (col == 3 or col == 7):
            num = ""
        elif row == 3 or row == 7:
            num = ""
        elif col == 3 or col == 7:
            num = ""
        else:
            num = get_number()
        board[row][col] = num


def move_check(board, row, col, num):
    # check if number is not in the box
    section_row = row - row % 4
    section_col = col - col % 4
    for i in range(3):
        for j in range(3):
            if board[i + section_row][j + section_col] == num:
                return False

    # check if number is not in the row
    for x in range(11):
        if board[x][col] == num:
            return False

    # check if number is not in the column
    for y in range(11):
        if board[row][y] == num:
            return False

    return True


def find_next(board):
    for i in range(11):
        for j in range(11):
            if board[i][j] == 0:
                return (i, j)

    return None


def solve(board):
    next = find_next(board)
    if not next:
        return True
    row, col = next

    for num in range(1, 10):
        if move_check(board, row, col, num):
            board[row][col] = num

            if solve(board):
                return True

            # Resets to 0 for backtracking
            board[row][col] = 0

    # start backtracking
    return False


temp_sudoku_board = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9]
]

# Print the filled board
def print_board(board):
    for row in board:
        print(" ".join(str(num) if num != 0 else '.' for num in row))


def get_int(msg, errorMsg):
    while True:
        try:
            number = int(input(msg))
        except ValueError:
            print(errorMsg)
        else:
            print()
            break
    return number


def main():
    print("Welcome to the sudoku puzzle solver!")
    print("Please type in your board in the order they appear by row.")
    sudoku_board = fill_board(11)

    while True:
        print_board(sudoku_board)
        print("This is the current board you have given.")
        print("1. Solve")
        print("2. Change a row")
        print("3. New Board")
        print("4. Exit")

        response = get_int("Select (1-4): ", "Invalid Input.")

        if response == 1:
            if solve(sudoku_board):
                for row in sudoku_board:
                    print(" ".join(str(num) if num != 0 else '.' for num in row))
            else:
                print("No solution.")
        elif response == 2:
            print("Change a row?")
            print("1. Yes")
            print("2. No")
            while True:
                response = get_int("Select (1-2): ", "Invalid Input.")

                if response == 1:
                    change_row(sudoku_board)
                    break
                elif response == 2:
                    print("OK.")
                    break
                else:
                    print("Not within the number range (1-2)")
        elif response == 3:
            print("Create a new board?")
            print("1. Yes")
            print("2. No")
            while True:
                response = get_int("Select (1-2): ", "Invalid Input.")

                if response == 1:
                    sudoku_board = fill_board(11)
                    break
                elif response == 2:
                    print("OK.")
                    break
                else:
                    print("Not within the number range (1-2)")
        elif response == 4:
            break
        else:
            print("Please enter between 1 and 4.")


main()