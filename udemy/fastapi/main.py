

def main():
    asset = 50
    b_item = 15
    tax = 0.03

    item_cost = b_item * (1 + tax)
    print(asset - item_cost)

    zoo = ['gibon', 'osprey', 'bear', 'jaguar', 'arapaima']
    print(zoo)
    zoo.remove('jaguar')
    print(zoo)
    print(zoo[0:3])

    grade = 200

    if grade <= 59:
        print("F")
    elif grade <= 69:
        print("D")
    elif grade <= 79:
        print("C")
    elif grade <= 89:
        print("B")
    elif grade <= 100:
        print("A")
    else:
        print("Not valid grade")



main()
