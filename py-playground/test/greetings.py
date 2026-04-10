# module1.py
def greet(name):
    return f"Hello, {name}!"

if __name__ == "__main__":
    # This will only run when module1.py is executed directly
    print("Module1 is executed directly")
    print(greet(input("Please enter your name")))````