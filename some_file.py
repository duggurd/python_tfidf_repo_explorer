import os


def main():
    a = os.listdir(".")

    print(a)

    print("this is a AST test")

    if a is not None:
        k = 1 + 1 
        k = k*2
    
    return True