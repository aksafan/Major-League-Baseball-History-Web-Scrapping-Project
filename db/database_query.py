import sqlite3  # For SQL command execution

DB_PATH = "db/baseball_data.sqlite"

conn = sqlite3.connect(DB_PATH, isolation_level='IMMEDIATE')
conn.execute("PRAGMA foreign_keys = 1")

cursor = conn.cursor()

tables = cursor.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY 'name'").fetchall()
print("The tables in this database are:")
for row in tables:
    print(row[0])
print("Enter SQL statements below, ending with a semicolon.  Or, type exit to quit.")


def main():
    command_buffer = []
    print("Welcome to the SQL shell! Type 'exit;' to quit.")

    while True:
        try:
            # Prompt depending on whether we're in the middle of a command
            prompt = "sql> " if not command_buffer else "   -> "
            line = input(prompt)

            # Check for exit command
            if line.strip().lower() == "exit;":
                print("Exiting.")
                break

            # Add line to the command buffer
            command_buffer.append(line)

            # If line ends with a semicolon, it's the end of a command
            if line.strip().endswith(";"):
                # Join all lines in the buffer into a single command
                full_command = " ".join(command_buffer).strip()

                # Clear the buffer
                command_buffer = []

                # Execute the command and handle any SQL exceptions
                try:
                    cursor.execute(full_command)
                    results = cursor.fetchall()
                    for row in results:
                        print(row)
                except sqlite3.Error as e:
                    print(f"SQL Error: {e}")

                # Commit changes if it’s an INSERT, UPDATE, or DELETE
                conn.commit()

        except EOFError:  # Handle Ctrl-D (EOF) gracefully
            print("\n Exiting.")
            break
        except KeyboardInterrupt:  # Handle Ctrl-C (interrupt)
            print("\n Command canceled.")
            command_buffer = []  # Reset the command buffer

    # Clean up the database connection
    conn.close()


main()
