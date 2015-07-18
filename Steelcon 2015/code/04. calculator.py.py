#My first program in Python. Im still learning this programing language.

running = True 

while running:
    print("1 = Addition")
    print("2 = Subtraction")
    print("3 = Multiplication")
    print("4 = Division")
    print("5 = Exit program")
    cmd = int(input("Enter number : "))
    if cmd == 1:
        print("Addition")
        first = int(input("Enter first number :"))
        secund = int(input("Enter secund number :"))
        result = first + secund
        print(first ,'+' ,secund ,'=' , result)
    elif cmd == 2:
        print("Subtraction")
        first = int(input("Enter first number :"))
        secund = int(input("Enter secund number :"))
        result = first - secund
        print(first ,"-" ,secund ,"=" , result)
    elif cmd == 3:
        print("Mmltiplication")
        first = int(input("Enter first number :"))
        secund = int(input("Enter secund number :"))
        result = first * secund
        print(first ,"*" ,secund ,"=" , result)
    elif cmd == 4:
        print("Division")
        first = int(input("Enter first number :"))
        secund = int(input("Enter secund number :"))
        result = first / secund
        print(first ,"/" ,secund ,"=" , result)
    elif cmd == 5:
        print("Quit!")
        running = False