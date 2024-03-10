from State import Ambulance

PC = {"N": 0, "C": 1}
PN = 1


def print_colored(message, color):
    colors = {
        "reset": "\033[0m",
        "green": "\033[32m",
        "red": "\033[31m",
    }
    print(f"{colors[color]}{message}{colors['reset']}")


def run_test(test_function, test_name):
    try:
        test_function()
        print_colored(f"{test_name} passed", "green")
    except AssertionError:
        print_colored(f"{test_name} failed", "red")


def test_case_1():
    # Caso de prueba 1: Agregar un paciente no contagioso
    ambulance1 = Ambulance()
    assert ambulance1.addPassenger("N") == True
    assert ambulance1.PN == PN + 1
    assert ambulance1.PC == PC


def test_case_2():
    # Caso de prueba 2: Intentar agregar un paciente contagioso cuando no hay espacio
    ambulance2 = Ambulance(capacityC=0)
    assert ambulance2.addPassenger("C") == False
    assert ambulance2.PN == PN
    assert ambulance2.PC == PC


def test_case_3():
    # Caso de prueba 3: Agregar un paciente contagioso cuando hay espacio
    ambulance3 = Ambulance(capacityC=5)
    pc = PC.copy()
    pc["C"] += 1
    assert ambulance3.addPassenger("C") == True
    assert ambulance3.PN == PN
    assert ambulance3.PC == pc


def test_case_4():
    # Caso de prueba 4: Intentar agregar un paciente No Contagioso en la zona de Contagiosos cuando está vacía
    ambulance4 = Ambulance(capacityC=2, capacityN=5)
    ambulance4.PN += 1
    assert ambulance4.addPassenger("N") == True
    assert ambulance4.PN == PN + 2
    assert ambulance4.PC == PC


def test_case_5():
    # Caso de prueba 5: Intentar agregar un paciente Contagioso cuando hay un No Contagioso en la zona de Contagiosos
    ambulance5 = Ambulance(capacityC=2, capacityN=0)
    pc = PC.copy()
    pc["C"] += 1
    assert ambulance5.addPassenger("N") == False
    assert ambulance5.addPassenger("C") == True
    assert ambulance5.PN == 1
    assert ambulance5.PC == pc


def test_energy_methods():
    # Caso de prueba 1: Crear una ambulancia y probar enoughEnergy y consumeEnergy
    ambulance = Ambulance()

    # enoughEnergy: La ambulancia tiene 50 de energía, se espera True
    assert ambulance.enoughEnergy(10) == True

    # consumeEnergy: Consumir 10 de energía, se espera True y la energía restante es 40
    assert ambulance.consumeEnergy(10) == True
    assert ambulance.energy == 40

    # enoughEnergy: Intentar consumir más energía de la que hay, se espera False
    assert ambulance.enoughEnergy(50) == False

    # consumeEnergy: Intentar consumir más energía de la que hay, se espera False y la energía sigue siendo 40
    assert ambulance.consumeEnergy(50) == False
    assert ambulance.energy == 40


if __name__ == "__main__":
    run_test(test_case_1, "Test case 1")
    run_test(test_case_2, "Test case 2")
    run_test(test_case_3, "Test case 3")
    run_test(test_case_4, "Test case 4")
    run_test(test_case_5, "Test case 5")
    run_test(test_energy_methods, "Test energy methods")
