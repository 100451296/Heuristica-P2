from typing import List, Tuple
from State.State import *
import copy
import math

MAP_PATH = "input/map.csv"
ERROR_PATH = "input/error.csv"
DEBUG_PATH = "input/debug.csv"
EASY_PATH = "input/easy.csv"
EASY_PATH2 = "input/easy2.csv"

MAP_HEURISTIC_ESCALE = {"hard": 0.91, "medium3": 0.94, "default": 1, "big": 3}
MAP_COUNT_FACTOR = {"hard": 0.29, "medium3": 0.29, "default": 0.5}
FILE = "default"
NUM_PASSENGER = 0
DEFAULT_COST = 1
HEURISTIC_ESCALE = MAP_HEURISTIC_ESCALE[FILE]
DECREMENT = 0.99999  # Coeficiente que indica el % que representa el peso del siguiente target (Pacientes, CentroC, CentroN, Parking)
MINMAX_N_WEIGHT = 1.25
DEFAULT_WEIGHT = 1


class Map:
    def __init__(self, input_file: str, mode: int = 0) -> None:
        # Posiciones significativas dentro del mapa
        self.posN = []
        self.posC = []
        self.parking = (0, 0)
        self.posCC = (0, 0)
        self.posCN = (0, 0)
        self.escales = {}
        self.heuristic_mode = mode
        # Coeficiente para decidir peso de pacientes restantes. 0 total importancia distancias, 1 total importancia restantes
        self.COUNT_FACTOR = MAP_COUNT_FACTOR[FILE]
        # Matriz de mapa
        self.map = self.readMap(input_file)
        self.rows = len(self.map)
        self.columns = len(self.map[0])
        # Movimiento legales
        self.movements = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
        ]
        self.mean = self.mean_Manhattan()
        self.calculate_escales()
        # Diccionario de funciones heurísticas
        self.heuristic_functions = {
            6: self.heuristic1,
            2: self.heuristic2,
            3: self.heuristic_basic,
            4: self.heuristic_basic_escaled,
            5: self.heuristic_astar,
            1: self.heuristic_astar2,
        }

    def readMap(self, file_path: str) -> list:
        matrix = []
        try:
            with open(file_path, "r") as file:
                for i, line in enumerate(file):
                    row = line.strip().split(";")
                    if i == 0:
                        # Validar que todas las filas tengan la misma longitud
                        if i > 0 and len(row) != len(matrix[0]):
                            raise ValueError(
                                "Las filas del mapa no tienen la misma longitud."
                            )
                    matrix.append(row)

                    for j, element in enumerate(row):
                        # Validar elementos desconocidos
                        if element not in {
                            "N",
                            "C",
                            "P",
                            "CC",
                            "CN",
                            "1",
                            "2",
                            "X",
                        }:
                            raise ValueError(
                                f"Elemento desconocido en la posición ({i}, {j}): {element}"
                            )

                        if element == "N":
                            self.posN.append((i, j))
                        elif element == "C":
                            self.posC.append((i, j))
                        elif element == "P":
                            self.parking = (i, j)
                        elif element == "CC":
                            self.posCC = (i, j)
                        elif element == "CN":
                            self.posCN = (i, j)
        except FileNotFoundError:
            raise FileNotFoundError(f"El archivo '{file_path}' no se encontró.")
        except ValueError as e:
            print(f"Error de formato: {e}")
            exit(1)

        return matrix

    def getInitialState(self) -> State:
        """
        Obtiene el estado inicial para el mapa dado
        """
        ambulance = Ambulance(pos=self.parking)
        initial_state = State(ambulance=ambulance)
        self.copyMap(initial_state)
        initial_state.h = self.heuristic(initial_state)
        return initial_state

    def getFinalState(self) -> State:
        """
        Obtiene el estado final para el mapa dado
        """
        ambulance = Ambulance(pos=self.parking)
        return State(ambulance=ambulance, cc=len(self.posC), cn=len(self.posN))

    def print_map(self) -> None:
        for row in self.map:
            # Convierte cada elemento de la fila a str para imprimirlo
            row_str = " ".join(str(cell) for cell in row)
            print(row_str)

    def is_wall(self, position: Tuple[int, int]) -> bool:
        """
        Comprueba si la posicion pasada por parametro es transitable dentro del mapa
        """
        x, y = position
        return self.map[x][y] == "X"

    def is_valid(self, position: Tuple[int, int]) -> bool:
        """
        Comprueba si la posicion se encuentra dentro de lo limites del mapa
        """
        x, y = position
        return (
            0 <= x < self.rows and 0 <= y < self.columns and not self.is_wall(position)
        )

    def expand(self, state: State) -> List[State]:
        """
        Este metodo genera todos los sucesores validos para un estado dado
        """
        successors = []
        x, y = state.getPosition()

        # Calcula las casillas resultantes tras aplicar los movimientso
        for dx, dy in self.movements:
            new_position = (x + dx, y + dy)

            # Valida las nuevas posiciones
            if self.is_valid(new_position):
                # Crea una copia de estado en el sucesor
                successor = copy.copy(state)
                # Aplica los operadores que sean posibles
                self.applyOperators(successor, state, new_position, successors)
        return successors

    def applyOperators(self, successor, state, new_position, successors):
        """
        Este metodo se encarga de aplicar los operadores indicados según el tipo de casilla
        """
        cell_type = successor.map[new_position[0]][new_position[1]]

        if cell_type == "N":
            self.operatorsN(successor, state, new_position, successors)
        elif cell_type == "C":
            self.operatorsC(successor, state, new_position, successors)
        elif cell_type == "P":
            self.operatorsP(successor, state, new_position, successors)
        elif cell_type == "CC":
            self.operatorsCC(successor, state, new_position, successors)
        elif cell_type == "CN":
            self.operatorsCN(successor, state, new_position, successors)
        else:
            self.operatorsO(successor, state, new_position, successors)

    def operatorsN(self, successor, state, new_position, successors):
        cell_type = successor.map[new_position[0]][new_position[1]]
        # Aplica operador de movimiento y añadir pasajero
        if not successor.move(new_position, DEFAULT_COST):
            return
        successor.addPassenger("N", new_position)

        # Actualiza funcion objetivo
        self.update_f(successor, state, new_position, cell_type)
        successors.append(successor)

    def operatorsC(self, successor, state, new_position, successors) -> bool:
        # Aplica el operador de movimiento si hay energia
        if not successor.move(new_position, DEFAULT_COST):
            return False
        self.addContagious(successor, new_position)

        cell_type = successor.map[new_position[0]][new_position[1]]
        self.update_f(successor, state, new_position, cell_type)
        successors.append(successor)
        return True

    def operatorsP(self, successor, state, new_position, successors) -> bool:
        # Aplica el operador de movimiento si hay energia
        if not successor.move(new_position, DEFAULT_COST):
            return False

        cell_type = successor.map[new_position[0]][new_position[1]]
        successor.ambulance.reloadEnergy()

        self.update_f(successor, state, new_position, cell_type)
        successors.append(successor)
        return True

    def operatorsCC(self, successor, state, new_position, successors) -> bool:
        # Aplica el operadores
        if not successor.move(new_position, DEFAULT_COST):
            return False
        successor.leaveContagious()

        # Actualiza funcion objetivo
        cell_type = successor.map[new_position[0]][new_position[1]]
        self.update_f(successor, state, new_position, cell_type)
        successors.append(successor)
        return True

    def operatorsCN(self, successor, state, new_position, successors) -> bool:
        # Aplica el operadores
        if not successor.move(new_position, DEFAULT_COST):
            return False
        successor.leaveNotContagious()

        # Actualiza la funcion objetivo
        cell_type = successor.map[new_position[0]][new_position[1]]
        self.update_f(successor, state, new_position, cell_type)
        successors.append(successor)
        return True

    def operatorsO(self, successor, state, new_position, successors) -> bool:
        cost = int(successor.map[new_position[0]][new_position[DEFAULT_COST]])
        # Aplica el operador de movimiento si hay energia
        if not successor.move(new_position, cost):
            return False

        # Actualiza funcion objetivo
        cell_type = successor.map[new_position[0]][new_position[1]]
        self.update_f(successor, state, new_position, cell_type)
        successors.append(successor)
        return True

    def addContagious(self, successor: State, new_position) -> None:
        """
        Este operador se encarga de los contagiosos sean los últimos en subir
        """

        # Aun quedan No Contagiosos por recoger
        if len(self.posN) > successor.currentN():
            return

        # Se han recogido a todos los No Contagiosos y si hay hueco intenta subir
        successor.addPassenger("C", new_position)

    def update_f(self, successor, state, new_position, cell_type):
        cost = DEFAULT_COST
        if str(cell_type).isdigit():
            cost = int(cell_type)
        cost *= HEURISTIC_ESCALE
        successor.g = state.g + cost
        successor.h = self.heuristic(successor)
        successor.f = successor.g + successor.h

    def heuristic(self, state: State) -> int:
        """
        Este metodo se encarga de devolver el valor de la heuristica seleccionada
        """
        # Verificar si el modo de heurística es válido
        if self.heuristic_mode in self.heuristic_functions:
            # Llamar a la función correspondiente
            return self.heuristic_functions[self.heuristic_mode](state)
        else:
            return 0

    def heuristic_basic(self, state: State):
        """
        Devuelve los pacientes restantes por recoger
        """
        return (
            len(self.posC) + len(self.posN) - (state.currentN() + state.currentC())
        ) * 1

    def heuristic_basic_escaled(self, state: State) -> int:
        """
        La heuristica penaliza a los estados que tengan pacientes sin recoger o sin dejar en el centro.
        Calcula el numero de pacientes por recoger y los que estan pendientes de dejar en el centro.
        """
        totalP = len(self.posC) + len(self.posN)
        pendingP = totalP - (
            state.currentN() + state.currentC()
        )  # Pacientes pendientes de recoger
        pendingC = totalP - (
            state.CC + state.CN
        )  # Pacientes pendientes de dejar en el centro

        return ((pendingP + pendingC) / 2) * self.escales["COUNT_ESCALE"]

    def calculate_escales(self) -> None:
        """
        Este metodo calcula las escalas a aplicar a las distintas heuristicas para garantizar la consistencia
        """
        passN = len(self.posN)
        # Calcula las escalas
        num_passenger = CAPACITY_N
        if passN <= CAPACITY_N:
            num_passenger = passN

        if self.heuristic_mode in [3, 4]:
            self.COUNT_FACTOR = 1

        # Factor multiplicativo para pacientes restantes por recoger y trasladar al centro
        MAX_COUNT_SCALE = HEURISTIC_ESCALE / (num_passenger / 2)
        COUNT_SCALE = self.COUNT_FACTOR * MAX_COUNT_SCALE

        # Escala para la distancia a pacientes
        MAX_DECREASE = (num_passenger / 2) * COUNT_SCALE
        DIST_FACTOR = (HEURISTIC_ESCALE - MAX_DECREASE) / HEURISTIC_ESCALE
        DIST_ESCALE = HEURISTIC_ESCALE * DIST_FACTOR

        # Escalas para distancias a Centro Contagiosos, Centro No Contagiosos y Parking
        CC_ESCALE = DECREMENT * DIST_ESCALE
        CN_ESCALE = DECREMENT * CC_ESCALE
        PARKING_ESCALE = DECREMENT * CN_ESCALE

        self.escales = {
            "COUNT_ESCALE": COUNT_SCALE,
            "DIST_ESCALE": DIST_ESCALE,
            "CC_ESCALE": CC_ESCALE,
            "CN_ESCALE": CN_ESCALE,
            "PARKING_ESCALE": PARKING_ESCALE,
        }

    def calculate_distP(self, state: State) -> dict:
        # Calcula la distancia a cada paciente sin recoger
        dist_stateN = [
            (self.Manhattan(state.getPosition(), pos), pos)
            for pos in self.posN
            if state.map[pos[0]][pos[1]] == "N"
        ]
        dist_stateNEu = [
            (self.Euclidean(state.getPosition(), pos), pos)
            for pos in self.posN
            if state.map[pos[0]][pos[1]] == "C"
        ]
        dist_stateC = [
            (self.Manhattan(state.getPosition(), pos), pos)
            for pos in self.posC
            if state.map[pos[0]][pos[1]] == "C"
        ]
        dist_stateCEu = [
            (self.Euclidean(state.getPosition(), pos), pos)
            for pos in self.posC
            if state.map[pos[0]][pos[1]] == "C"
        ]

        dist_stateC = sorted(dist_stateC, key=lambda x: x[0])
        dist_stateN = sorted(dist_stateN, key=lambda x: x[0])

        dist_state = dist_stateN + dist_stateC
        dist_stateEu = dist_stateCEu + dist_stateNEu
        dist_state = sorted(dist_state, key=lambda x: x[0])

        # Metricas asociadas a las distancias de los pacientes ( media y distancia paciente mas cercano)
        min_distP = dist_state[0] if dist_state else (0, None)
        max_distP = dist_state[-1] if dist_state else (0, None)
        max_distN = dist_stateN[-1] if dist_stateN else (0, None)

        # SUMATORIOS
        sum_dist = sum(dist[0] for dist in dist_state)
        sum_dist2 = sum(dist[0] for dist in dist_state[: (len(dist_state) // 2)])
        sum_distN = sum(dist[0] for dist in dist_stateN)
        sum_distEu = sum(dist[0] for dist in dist_stateEu)

        # MEDIAS de dist_state y dist_stateN
        mean_distP = sum_dist / len(dist_state) if dist_state else 0
        mean_distN = sum_distN / len(dist_stateN) if dist_stateN else 0

        # Metricas minmax
        minmax_dists = [(min_distP, max_distP)]
        if len(dist_state) > 3:
            neg_index = -1
            for i in range(1, (len(dist_state) // 2) - 1):
                minmax_dists.append((dist_state[i], dist_state[neg_index + (-i)]))

        minmaxW_dists = []
        if len(dist_stateN) >= 2:
            neg_index = -1
            for i in range(1, (len(dist_stateN) // 2) - 1):
                minmaxW_dists.append((dist_stateN[i], dist_stateN[neg_index + (-i)]))

        # Guardaremos de lo siguientes mas cercanos (min y max si solo quedan 2)
        min2_distP, max2_distP = (0, None), (0, None)

        # Logica de asignación de min2 y max2
        if len(dist_state) >= 4:
            min2_distP = dist_state[1]
            max2_distP = dist_state[-2]
        if len(dist_state) == 3:
            min2_distP = max_distP
            max2_distP = dist_state[1]

        return {
            "mean": mean_distP,
            "sum2": sum_dist2,
            "sumN": sum_distN,
            "sumEu": sum_distEu,
            "min": min_distP,
            "min2": min2_distP,
            "max": max_distP,
            "max2": max2_distP,
            "minmax": minmax_dists,
            "minmaxW": minmaxW_dists,
            "meanN": mean_distN,
            "maxN": max_distN,
        }

    def calculate_distCP(self, state) -> dict:
        # Calculo de distancias a puntos relevantes ( CC, CN, P )
        dist_CC = self.Manhattan(state.getPosition(), self.posCC)
        dist_CN = self.Manhattan(state.getPosition(), self.posCN)
        dist_parking = self.Manhattan(state.getPosition(), self.parking)
        mean_distC = (dist_CC + dist_CN) / 2

        return {"CC": dist_CC, "CN": dist_CN, "P": dist_parking, "meanC": mean_distC}

    def heuristic1(self, state: State):
        """
        La heuristica calcula las distancia a cada paciente restante, puntos signicativos del mapa y el valor de la heuristica heuristic_based_escalated.
        Pondera cada una en base a las escalas calculas segun el nunmeros de pacientes y el COUNT FACTOR.

        Esta garantizado que la heuristca disminuye del valor segun te acercas al objetivo, las escalas hacen mas grandes aquellas distancias que deben
        resovlerse primero (Numero de pacientes restantes -> Distancia a CC -> Distancia CN -> Parking). La heuristica solo tiene en cuenta un tipo de distancia a la vez.
        """
        # Calculo metricas necesarias
        distCP_metrics = self.calculate_distCP(state)
        dist_metrics = self.calculate_distP(state)

        # Logica de pesos
        factorP = factorC = factorN = factorParking = 0
        if dist_metrics["max"][0] == 0:  # Todos los pacientes recogidos
            factorP = factorC = 1
        if state.CC == len(self.posC):  # Todos los contagiosos en su centro
            factorC = 0
        if (
            len(self.posN) != state.CN and factorC == 0 and factorP == 1
        ):  # Quedan por llevar No Contagiosos
            factorN = 1
        if factorN == 0 and factorC == 0 and factorP == 1:  # Vuelta al parking
            factorParking = 1

        return (
            dist_metrics["max"][0] * self.escales["DIST_ESCALE"]
            + self.heuristic_basic_escaled(state)
            + distCP_metrics["CC"] * factorP * factorC * self.escales["CC_ESCALE"]
            + distCP_metrics["CN"] * factorN * self.escales["CN_ESCALE"]
            + distCP_metrics["P"] * factorParking * self.escales["PARKING_ESCALE"]
        )

    def heuristic2(self, state: State):
        """
        Devuelve el la distancia al paciente mas lejano mas su distancia a
        """
        dist_metrics = self.calculate_distP(state)
        distCP_metrics = self.calculate_distCP(state)

        dist_PC, dist_minmax = 0, 0

        if dist_metrics["max"][1]:
            # Calculo de la distancia entre el mas cercnao y el mas lejano
            if dist_metrics["min"][1]:
                dist_minmax = self.Manhattan(
                    dist_metrics["max"][1], dist_metrics["min"][1]
                )

            # Calculo de distancia del mas lejano al centro
            x, y = dist_metrics["max"][1]
            center = self.posCN
            if state.map[x][y] == "C":
                center = self.posCC
            dist_PC = self.Manhattan(dist_metrics["max"][1], center)

        return (
            dist_metrics["min"][0] * 1.25
            + dist_minmax * 1.25
            + dist_PC * 1.25
            + distCP_metrics["P"] * 1.25
            + self.heuristic1(state)
        )

    def heuristic_astar(self, state: State):
        """
        Devuelve el la distancia al paciente mas lejano mas su distancia a
        """
        # Obtenemos distancias relevantes ( Pacientes, CN, CC, P )
        dist_metrics = self.calculate_distP(state)
        distCP_metrics = self.calculate_distCP(state)

        dist_PC, dist_minmax = 0, 0

        if dist_metrics["max"][1]:
            if dist_metrics["min"][1]:
                # Calculo de la distancia entre el mas cercano y el mas lejano (min y max) iterativo
                for pair in dist_metrics["minmax"]:
                    dist_minmax += self.Manhattan(pair[0][1], pair[1][1])

                # Calculo de distancia del mas lejano al centro
                x, y = dist_metrics["max"][1]
                center = self.posCN
                if state.map[x][y] == "C":
                    center = self.posCC
                dist_PC = self.Manhattan(dist_metrics["max"][1], center)

        return (
            dist_metrics["min"][0] * DEFAULT_WEIGHT
            + dist_minmax * DEFAULT_WEIGHT
            + dist_PC * DEFAULT_WEIGHT
            + distCP_metrics["P"]
            * DEFAULT_WEIGHT
            * HEURISTIC_ESCALE
            * self.escales["PARKING_ESCALE"]
            + self.heuristic1(state)
        )

    def heuristic_astar2(self, state: State):
        """
        Devuelve el la distancia al paciente mas lejano mas su distancia a
        """
        # Obtenemos distancias relevantes ( Pacientes, CN, CC, P )
        dist_metrics = self.calculate_distP(state)
        distCP_metrics = self.calculate_distCP(state)

        dist_PC, dist_minmax = 0, 0

        if dist_metrics["max"][1]:
            if dist_metrics["min"][1]:
                # Calculo de la distancia entre el mas cercnao y el mas lejano
                if dist_metrics["min"][1]:
                    dist_minmax = self.Manhattan(
                        dist_metrics["max"][1], dist_metrics["min"][1]
                    )
                # Calculo de distancia del mas lejano al centro
                x, y = dist_metrics["max"][1]
                center = self.posCN
                if state.map[x][y] == "C":
                    center = self.posCC
                dist_PC = self.Manhattan(dist_metrics["max"][1], center)

        return (
            dist_metrics["min"][0] * DEFAULT_WEIGHT
            + self.heuristic_basic(state)
            + dist_minmax * DEFAULT_WEIGHT
            + dist_PC * DEFAULT_WEIGHT
            + (  # Heuristica parking y energia
                distCP_metrics["P"]
                * DEFAULT_WEIGHT
                * HEURISTIC_ESCALE
                * self.escales["PARKING_ESCALE"]
            )
            + self.heuristic1(state)
        )

    def Manhattan(self, punto1, punto2):
        # Calcula la distancia euclidiana entre dos puntos
        return math.sqrt((punto1[0] - punto2[0]) ** 2 + (punto1[1] - punto2[1]) ** 2)

    def Euclidean(self, posicion1, posicion2):
        x1, y1 = posicion1
        x2, y2 = posicion2

        # Calcula la diferencia en las coordenadas x e y
        diferencia_x = x2 - x1
        diferencia_y = y2 - y1

        # Calcula la distancia euclidiana
        distancia = math.sqrt(diferencia_x**2 + diferencia_y**2)

        return distancia

    def mean_Manhattan(self):
        # Calcula las distancias y guarda en listas separadas
        distsN = [self.Manhattan(posN, self.posCN) for posN in self.posN]
        distsC = [self.Manhattan(posC, self.posCC) for posC in self.posC]

        # Calcula la media de las distancias
        meanN = sum(distsN) / len(distsN) if distsN else 0
        meanC = sum(distsC) / len(distsC) if distsC else 0

        return (meanC + meanN) / 2

    def copyMap(self, state: State) -> None:
        state.map = self.map.copy()


def main():
    my_map = Map(DEBUG_PATH)
    my_map.print_map()

    print("Rows:", my_map.rows)
    print("Columns:", my_map.columns)
    # Acceder a las posiciones almacenadas
    print("Posiciones de N:", my_map.posN)
    print("Posiciones de C:", my_map.posC)
    print("Posición de parking:", my_map.parking)
    print("Posición de CC:", my_map.posCC)
    print("Posición de CN:", my_map.posCN)

    initial_state = State()

    my_map.expand(initial_state)

    my_map.print_map()


if __name__ == "__main__":
    main()
