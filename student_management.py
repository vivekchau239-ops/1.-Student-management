import json
import os

FILE = "students.json"


def load_students():
    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            return json.load(f)
    return {}


def save_students(students):
    with open(FILE, "w") as f:
        json.dump(students, f, indent=4)


def add_student(students):
    roll = input("Enter Roll Number: ")

    if roll in students:
        print("Roll number already exists!")
        return

    name = input("Enter Student Name: ")
    marks = float(input("Enter Marks (0-100): "))

    if not 0 <= marks <= 100:
        print("Marks must be between 0 and 100.")
        return

    students[roll] = {"name": name, "marks": marks}
    save_students(students)
    print("Student added successfully!")


def view_students(students):
    if not students:
        print("No student records found.")
        return

    for roll, info in students.items():
        print(
            f"Roll: {roll} | "
            f"Name: {info['name']} | "
            f"Marks: {info['marks']}"
        )


def search_student(students):
    roll = input("Enter Roll Number to search: ")

    if roll in students:
        print(students[roll])
    else:
        print("Student not found.")


def delete_student(students):
    roll = input("Enter Roll Number to delete: ")

    if roll in students:
        del students[roll]
        save_students(students)
        print("Student deleted successfully!")
    else:
        print("Student not found.")


def main():
    students = load_students()

    while True:
        print("\n--- STUDENT MANAGEMENT SYSTEM ---")
        print("1. Add Student")
        print("2. View Students")
        print("3. Search Student")
        print("4. Delete Student")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            add_student(students)
        elif choice == "2":
            view_students(students)
        elif choice == "3":
            search_student(students)
        elif choice == "4":
            delete_student(students)
        elif choice == "5":
            print("Thank you!")
            break
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()