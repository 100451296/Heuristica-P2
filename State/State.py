from typing import List, Tuple
import copy

"""
En este archivo se definiran todas las clases necesarias para implementar el estado dentro del problema
"""

# Constantes para debug
CAPACITY_N = 8
CAPACITY_C = 2
MAX_ENERGY = 50
PARKING = (7, 3)
DEFAULT_COST = 1


class Ambulance:
    """Esta clase representa la ambulacancia"""

    def __init__(
        self,
        capacityN: int = CAPACITY_N,
        capacityC: int = CAPACITY_C,
        energy: int = MAX_ENERGY,
        pos: tuple[int, int] = PARKING,
    ) -> None:
        # Numero de plazas para no contagiosos y  cantagiosos
        self.capacityN = capacityN
        self.capacityC = capacityC

        # Asignación de plazas
        self.PN = 0
        self.PC = {"N": 0, "C": 0}

        # Energía y posición
        self.energy = energy
        self.pos = pos

    def __copy__(self):
        new_instance = type(self)(
            capacityN=self.capacityN,
            capacityC=self.capacityC,
            energy=self.energy,
            pos=copy.copy(self.pos),
        )
        new_instance.PN = self.PN
        new_instance.PC = self.PC.copy()

        return new_instance

    def addPassenger(self, type: str) -> bool:
        """Este metodo añade un pasajero tras realizar las validaciones pertinentes. Devuelve True si tiene exito y False en caso contrario"""

        # Contagioso
        if type == "C":
            # Hay hueco en Contagiosos y no hay ningún No Contagioso
            count = sum(self.PC[key] for key in self.PC.keys())
            if count < self.capacityC and self.PC["N"] == 0:
                self.PC[type] += 1
                return True

        # No contagioso
        elif type == "N":
            # Hay hueco en la zona de No Contagiosos
            if self.PN < self.capacityN:
                self.PN += 1
                return True

            # Hay hueco en Contagiosos y no hay ningún Contagioso
            count = sum(self.PC[key] for key in self.PC.keys())
            if count < self.capacityC and self.PC["C"] == 0:
                self.PC[type] += 1
                return True

        return False

    def enoughEnergy(self, cost: int) -> bool:
        """Esta funcion se usará para comprobar si la ambulancia tiene suficiente energía para asumir el coste"""
        return True if self.energy - cost >= 0 else False

    def consumeEnergy(self, cost: int) -> bool:
        """Este método se usará para consumir la energía de la ambulancia"""
        if self.enoughEnergy(cost):
            self.energy -= cost
            return True
        return False

    def reloadEnergy(self) -> None:
        self.energy = MAX_ENERGY

    def updatePosition(self, pos: Tuple[int, int]) -> None:
        self.pos = pos

    def leaveContagious(self) -> None:
        """
        Este metodo devuelve el numero de Contagiados en la ambulancia, si habia alguno lo borra de la zona de contagiados
        """
        count = self.PC["C"]
        if count > 0:
            self.PC["C"] = 0
        return count

    def leaveNotContagious(self) -> None:
        """
        Este metodo devuelve el numero de No Contagiados en la ambulancia, si habia alguno lo borra de la zona de contagiados o zona de no contagiados
        """
        countC = self.PC["N"]
        countN = self.PN
        if countC > 0:
            self.PC["N"] = 0
        if countN > 0:
            self.PN = 0
        return countC + countN

    def bateryLevel(self) -> float:
        return self.energy / MAX_ENERGY


class State:
    def __init__(
        self,
        evaluation: int = 0,
        ambulance: Ambulance = Ambulance(),
        cc: int = 0,
        cn: int = 0,
        map: List[List[int]] = [],
    ):
        self.ambulance = ambulance
        self.CC = cc
        self.CN = cn
        self.f = evaluation
        self.g = 0
        self.h = 0

        self.map = map

    def __eq__(self, __value: "State") -> bool:
        """Comprueba que dos estados sean iguales haciendo uso del operador =="""

        # La ambulancia no se encuentra en en el mismo lugar
        if self.ambulance.pos != __value.ambulance.pos:
            return False

        # La ambulancia no tiene la misma energia
        if self.ambulance.energy != __value.ambulance.energy:
            return False

        # Tienen distinto número de plazas asignadas en No Cantagiosos
        if self.ambulance.PN != __value.ambulance.PN:
            return False

        # Tienen distinta asignacion de la zona de Cantiogiosos
        if (
            self.ambulance.PC["N"] != __value.ambulance.PC["N"]
            or self.ambulance.PC["C"] != __value.ambulance.PC["C"]
        ):
            return False

        # No han llevado a los centros al mismo numero de pacientes
        if self.CC != __value.CC or self.CN != __value.CN:
            return False

        if self.map != __value.map:
            return False

        return True

    def __copy__(self):
        new_instance = type(self)(
            evaluation=self.f,
            ambulance=copy.copy(self.ambulance),
            cc=self.CC,
            cn=self.CN,
            map=copy.deepcopy(self.map),
        )
        return new_instance

    def __str__(self):
        state_str = f"\033[95mState\033[0m"
        evaluation_str = f"\033[91mevaluation=\033[97m{round(self.f, 2)}\033[0m"  # Rojo
        cost_str = f"\033[91mcost=\033[97m{round(self.g, 2)}\033[0m"  # Rojo
        heur_str = f"\033[91mheur=\033[97m{round(self.h, 2)}\033[0m"  # Rojo
        ambulance_pos_str = (
            f"\033[91mambulancePos=\033[97m{self.ambulance.pos}\033[0m"  # Rojo
        )
        ambulance_pn_str = (
            f"\033[91mambulancePN=\033[97m{self.ambulance.PN}\033[0m"  # Rojo
        )
        ambulance_pc_str = (
            f"\033[91mambulancePC=\033[97m{self.ambulance.PC}\033[0m"  # Rojo
        )
        ambulance_fuel_str = (
            f"\033[91mambulanceFuel=\033[97m{self.ambulance.energy}\033[0m"  # Rojo
        )
        cc_str = f"\033[91mCC=\033[97m{self.CC}\033[0m"  # Rojo
        cn_str = f"\033[91mCN=\033[97m{self.CN}\033[0m"  # Rojo

        return f"{state_str}({evaluation_str}, {cost_str}, {heur_str}, {ambulance_pos_str}, {ambulance_pn_str}, {ambulance_pc_str}, {ambulance_fuel_str}, {cc_str}, {cn_str})"

    def getPosition(self):
        return self.ambulance.pos

    def move(self, pos, cost):
        """
        Operador de movimiento. Precondiciones: pos posicion valida y tener energia
        """
        if self.ambulance.enoughEnergy(cost):
            self.ambulance.consumeEnergy(cost)
            self.ambulance.updatePosition(pos)
            return True
        return False

    def currentN(self) -> int:
        """
        Devuelve el numero de pacientes No Contagiosos que ya han sido recogidos
        """
        numN = self.ambulance.PC["N"]
        # Pacientes NC en el centro + Pacientes NC subidos en la ambulancia en zona NC + Pacientes NC subidos en zona C
        return self.CN + self.ambulance.PN + numN

    def currentC(self) -> int:
        """
        Devuelve el numero de pacientes Contagiosos que ya han sido recogidos
        """
        # Pacientes CC en el centro + Pacientes C subidos en zona C
        return self.CC + self.ambulance.PC["C"]

    def leaveContagious(self) -> None:
        """
        Este metodo traslada los pacientes Contagiados de la ambulancia al Centro de Contagiados
        """
        count = self.ambulance.leaveContagious()
        self.CC += count

    def leaveNotContagious(self) -> None:
        """
        Este metodo traslada los pacientes NO Contagiados de la ambulancia al Centro de NO Contagiados
        """
        # Si no hay ningun contagiado subido ejecuta el operador, en caso contrario debe darles prioridad
        if self.ambulance.PC["C"] == 0:
            count = self.ambulance.leaveNotContagious()
            self.CN += count

    def equal_goal(self, __value: "State") -> bool:
        """Comprueba que dos estados sean iguales", sin tener en cuenta la energia"""
        # La ambulancia no se encuentra en en el mismo lugar
        if self.ambulance.pos != __value.ambulance.pos:
            return False

        # Tienen distinto número de plazas asignadas en No Cantagiosos
        if self.ambulance.PN != __value.ambulance.PN:
            return False

        # Tienen distinta asignacion de la zona de Cantiogiosos
        if (
            self.ambulance.PC["N"] != __value.ambulance.PC["N"]
            or self.ambulance.PC["C"] != __value.ambulance.PC["C"]
        ):
            return False

        # No han llevado a los centros al mismo numero de pacientes
        if self.CC != __value.CC or self.CN != __value.CN:
            return False

        return True

    def addPassenger(self, type: str, position: Tuple[int, int]) -> None:
        """
        Añade el pasajero a la ambulancia si es posible y actualiza el mapa en caso afirmativo
        """
        if self.ambulance.addPassenger(type) == True:
            self.map[position[0]][position[1]] = DEFAULT_COST

    def bateryLevel(self) -> float:
        return self.ambulance.bateryLevel()


if __name__ == "__main__":
    state1, state2 = State(), State()

    if state1 == state2:
        print("Estados iguales")
    else:
        print("Estados diferentes")
