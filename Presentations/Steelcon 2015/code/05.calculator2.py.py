
def addition(num1,num2): 
    answer = num1 + num2
    return answer

def subtraction(num1,num2): 
    answer = num1 - num2
    return answer

def division(num1,num2): 
    answer = num1 / num2
    return answer

def multiplication(num1,num2): 
    answer = num1 / num2
    return answer



print('1 = Addition')
print('2 = Subtraction')
print('3 = Division')
print('4 = Multiplication')

choice = int(raw_input('Pick Your  choice'))
num1 = int(raw_input('What is your first number'))
num2 = int(raw_input('What is your second number'))

if choice == 1:
    answer = addition(num1,num2)
    print 'The result is ', answer
elif choice ==2:
    answer =  subtraction(num1,num2)
    print 'The result is ', answer
elif choice ==3:
    multiplication(num1,num2)
    print 'The result is ', answer
elif choice ==4:
    answer = division(num1,num2)
    print 'The result is ', answer
      







