

def main():
    asset = 50
    b_item = 15
    tax = 0.03

    item_cost = b_item * (1 + tax)
    print(asset - item_cost)

    print("// === // === //")
    # Lists
    zoo = ['gibon', 'osprey', 'bear', 'jaguar', 'arapaima']
    print(zoo)
    zoo.remove('jaguar')
    print(zoo)
    print(zoo[0:3])

    print("// === // === //")
    # If else
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
    
    print("// === // === //")
    # Loops
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    x = 0
    while x < 3:
        x += 1
        print("----------")
        for i in days_of_week:
            if i == "Monday":
                continue
            print(f"dia {i}")
    
    
    print("// === // === //")
    # Dicts
    vehicle = {
        "model":"Ford",
        "make":"Explorer",
        "year":2018,
        "mileage":40000
    }
    # 1. for loop to print all
    for k,v in vehicle.items():
        print(f"{k}: {v}")
    # 2. copy dict
    vehicle2 = vehicle.copy()
    # 3. add property to copy
    vehicle2["number_of_tires"] = 4
    # 4. delete property from copy
    vehicle2.pop('mileage')

    print("---- ---- ----")
    for k in vehicle2:
        print(k)

    print("// === // === //")

# functions
def func():
    pass

def data(firstname: str, lastname: str, age:int) :
    dict = {}
    dict['firstName'] = firstname
    dict['lastName'] = lastname
    dict['age'] = age

    return dict

main()
print(data(firstname='Juan Carlos', lastname='Piedrahita',age=40))
