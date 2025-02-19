# main.py
from models import many_to_one, one_to_many, many_to_many

def main():
    while True:
        print("\n🚀 Multi-threaded Simulator 🚀")
        print("1. Many-to-One Model")
        print("2. One-to-Many Model")
        print("3. Many-to-Many Model")
        print("4. Exit")

        try:
            choice = int(input("Enter your choice (1-4): "))
            
            if choice == 4:
                print("🚪 Exiting program...")
                break  # Exit the loop

            num_threads = int(input("Enter the number of threads: "))

            if num_threads < 1:
                print("⚠️ Please enter a valid number of threads (1 or more).")
                continue

            # Switch-case alternative using if-elif
            if choice == 1:
                many_to_one(num_threads)
            elif choice == 2:
                one_to_many(num_threads)
            elif choice == 3:
                many_to_many(num_threads)
            else:
                print("❌ Invalid choice! Please enter a number between 1 and 4.")

        except ValueError:
            print("⚠️ Invalid input! Please enter a number.")

if __name__ == "__main__":
    main()
