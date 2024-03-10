from queue import PriorityQueue
from Map.Map import *
from State.State import State, Ambulance
import os
import time
import sys
import argparse
import bisect

MEDIUM3_OPTIMAL = 62
MEDIUM2_OPTIMAL = 47
MEDIUM1_OPTIMAL = 33
OUTPUT_PATH = "./ASTAR-test/"


class Node:
    def __init__(self, state: State, father: State = None):
        """
        Initialize the Node
        """
        self.state = state
        self.father = father
        self.pointers = []


class ASTARTraslados:
    def __init__(self, input_file: str, mode: int = 0):
        self.map = Map(input_file, mode)
        self.initial_state = self.map.getInitialState()
        self.final_state = self.map.getFinalState()
        self.map.copyMap(self.initial_state)
        self.verbose_flag = 0
        self.check_flag = 0
        self.check_ad = 0
        self.expanded = 0

    def build_path(self, current_node: Node):
        camino = [current_node.state]
        while current_node.father:
            current_node = current_node.father
            camino.insert(0, current_node.state)
        return camino

    def print_highlighted_positions(self, matrix, highlighted_positions):
        for i, row in enumerate(matrix):
            for j, value in enumerate(row):
                if (i, j) in highlighted_positions:
                    # Print the highlighted cell in green
                    if (i, j) == highlighted_positions[-1]:
                        # Print the last highlighted cell in red
                        print("\033[91m" + str(matrix[i][j]) + "\033[0m", end=" ")
                    else:
                        print("\033[92m" + str(value) + "\033[0m", end=" ")
                else:
                    print(value, end=" ")
            print()

    def search_path(self):
        self.expanded = 0
        # Create the initial Node
        initial_node = Node(self.initial_state)

        # Initialize data structures
        open_set = []
        open_set.append(initial_node)

        closed_set = []
        success = False

        path = []
        # Main loop
        while not len(open_set) == 0 or success:
            # Remove the first node from open_set and add it to closed_set
            current_node = open_set.pop(0)

            if self.check_flag == 1:
                self.check_consistency(current_node)
            if self.check_ad == 1:
                self.check_admissibility(current_node)
            # Verbose consistent
            if self.verbose_flag == 1:
                self.verbose(current_node, path)
            # Expand node
            closed_set.append(current_node)
            if current_node.state.equal_goal(self.final_state):
                success = True
                break

            # Generate successors
            successors = self.map.expand(current_node.state)
            self.expanded += 1
            for successor_state in successors:
                # Create a node for each successor and create a pointer to the current node
                successor_node = Node(successor_state, current_node)

                current_node.pointers.append(successor_node)
                found = False
                # For each successor in open_set, redirect the pointer to current if it has a worse evaluation
                for node in open_set:
                    if node.state == successor_state:
                        found = True
                        if node.state.f > successor_state.f:
                            open_set = sorted(open_set, key=lambda x: x.state.f)
                            node.state.f = successor_state.f
                            node.father = current_node
                        break

                # For each successor in closed_set, redirect the parent pointer to the current node and the pointers of its children to the successor
                for node in closed_set:
                    if node.state == successor_state:
                        found = True
                        if node.state.f > successor_state.f:
                            node.state.f = successor_state.f
                            open_set = sorted(open_set, key=lambda x: x.state.f)
                            # Avoid generating cycles (should not happen if the heuristic is consistent)
                            if current_node.father.state == successor_state:
                                pass
                            else:
                                node.father = current_node
                                for children in node.pointers:
                                    children.father = successor_node
                        break

                # Inserta el sucesor en la posicion correcta para mantener abierta ordenada por el valor de evaluacion
                if not found:
                    bisect.insort(open_set, successor_node, key=lambda x: x.state.f)

        # Build the solution if found
        if success:
            solution = self.build_path(current_node)
            return solution
        else:
            return []

    def verbose(self, current_node: Node, path: List):
        """
        Comprueba la consistencia de la heuristica mediante la formula h(n) <= c(n, m) + h(m)
        """
        # Calcula el nuevo camino

        path = []

        for state in self.build_path(current_node):
            path.append(state.getPosition())

        os.system("clear")
        print("\nCAMINO anterior ->", len(path))
        print("Current -> ", current_node.state)

        # Imprime por pantalla el camino
        self.print_highlighted_positions(current_node.state.map, path)

        """
        time.sleep(1)
        input()
        """

    def check_consistency(self, current_node: Node) -> None:
        """
        Comprueba consistencia h(n) <= c(n, m) +  h(m)
        """
        if current_node.father:
            hn = current_node.father.state.h
            x, y = current_node.state.getPosition()
            cnm = 1
            if str(current_node.state.map[x][y]).isdigit():
                cnm = int(current_node.state.map[x][y])
            cnm *= HEURISTIC_ESCALE
            if hn > cnm + current_node.state.h:
                print(
                    "ERROR: ",
                    f"h(n):\033[91m{round(hn, 2)}\033[0m <= c(n,m):{round(cnm, 2)} + h(m):{current_node.state.h} = \033[91m{round(cnm+current_node.state.h, 2)}\033[0m",
                    "\n\n",
                    "Current ->",
                    current_node.state,
                    "\n",
                    "*" * 200,
                    "\n",
                    "Fahter ->",
                    current_node.father.state,
                )
                sys.exit(1)
            else:
                if self.verbose_flag == 1:
                    print(
                        f"h(n):\033[92m{round(hn, 2)}\033[0m <= c(n,m):{round(cnm, 2)} + h(m):{current_node.state.h} = \033[92m{round(cnm+current_node.state.h, 2)}\033[0m"
                    )

    def check_admissibility(self, current_node: Node) -> None:
        """
        Comprueba admisibilidad h(n) <= coste optimo.
        *Esta pensado para comprobar la heuristica sobre el archivo medium1, el cual es mapa asequible para debuguear la mayoria de heuristicas
        """
        if current_node.father:
            hn = current_node.state.h
            optimal = MEDIUM1_OPTIMAL * HEURISTIC_ESCALE
            if hn > optimal:
                print(
                    "ERROR ADMISIBILITY: ",
                    f"h(n):\033[91m{round(hn, 2)}\033[0m <= optimal: \033[91m{optimal}\033[0m",
                    "\n\n",
                    "Current ->",
                    current_node.state,
                    "\n",
                )
                sys.exit(1)
            else:
                if self.verbose_flag == 1:
                    print(
                        f"h(n):\033[92m{round(hn, 2)}\033[0m <= optimal: \033[92m{optimal}\033[0m",
                    )

    def export_solution(self, path, output_file):
        with open(OUTPUT_PATH + output_file, "w") as archivo:
            for obj in path:
                # Asegúrate de ajustar los nombres de atributos según la estructura de tus objetos
                position = obj.getPosition()
                type = self.map.map[position[0]][position[1]]
                fuel = obj.ambulance.energy

                # Crea una cadena formateada y escríbela en el archivo
                linea = f"({position[0]},{position[1]}):{type}:{fuel}\n"
                archivo.write(linea)

    def export_info(self, output_file, total_time, cost, len_path, nodes):
        with open(OUTPUT_PATH + output_file, "w") as archivo:
            # Asegúrate de ajustar los nombres de atributos según la estructura de tus objetos

            # Crea una cadena formateada y escríbela en el archivo
            linea = f"Tiempo total: {total_time}\nCoste total: {cost}\nLongitud del plan: {len_path}\nNodos expandidos: {nodes}\n"
            archivo.write(linea)


def parseArgs():
    parser = argparse.ArgumentParser(description="Descripción del script")
    # Si no se proporcionan banderas, asume el modo de archivo
    if len(sys.argv) == 3:
        parser.file = sys.argv[1]
        parser.mode = sys.argv[2]
        parser.verbose = None
        parser.admissibility = None
        parser.check = None
        parser.result = None
        return parser

    # Si se proporcionan banderas, utiliza argparse para analizar los argumentos

    parser.add_argument("--file", "-f", type=str, help="Archivo de entrada")
    parser.add_argument("--mode", "-m", type=str, help="Modo de algoritmo")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verbose")
    parser.add_argument(
        "--check",
        "-c",
        action="store_true",
        help="Checkea consistencia de la heuristica",
    )
    parser.add_argument(
        "--admissibility",
        "-a",
        action="store_true",
        help="Checkea admisibilidad de la heuristica",
    )
    parser.add_argument(
        "--result",
        "-r",
        action="store_true",
        help="Reconstruye el camino si encuentra solucion",
    )

    return parser.parse_args()


def printResults(
    resultado: list, total_time: float, astar_traslados: ASTARTraslados, args
) -> None:
    if resultado:
        path = []
        for node in resultado:
            path.append(node.getPosition())

        # Muestra nodo por nodo el recorrido
        if args.result:
            input("Aqui esta la solución...")
            for i in range(1, len(path) + 1):
                os.system("clear")
                astar_traslados.print_highlighted_positions(
                    astar_traslados.map.map, path[:i]
                )
                print(resultado[i - 1 : i][0])
                time.sleep(0.75)

        for node in resultado:
            print(node, "->")

        print(f"TIEMPO ALGORITMO -> {round(total_time, 2)} segundos")
        print(f"NODOS EXPANDIDOS -> {astar_traslados.expanded}")
        print(
            f"PARAMETROS:\n-> HEURISTIC ESCALE: {HEURISTIC_ESCALE}\n-> COUNT_FACTOR: {astar_traslados.map.COUNT_FACTOR}"
        )


def writeResults(
    file_name: str, astar_traslados: ASTARTraslados, resultado, total_time: float
):
    # Utiliza la función os.path.basename para extraer el nombre del archivo de la ruta completa
    file_name_only = os.path.basename(file_name)

    # Encuentra la última aparición del punto para manejar casos donde el nombre del archivo contiene puntos adicionales
    last_dot_index = file_name_only.rfind(".")

    if last_dot_index != -1:
        # Construye el nuevo nombre de archivo reemplazando la extensión por ".output"
        output_file = (
            file_name_only[:last_dot_index]
            + f"-{astar_traslados.map.heuristic_mode}"
            + ".output"
        )
        info_file = (
            file_name_only[:last_dot_index]
            + f"-{astar_traslados.map.heuristic_mode}"
            + ".stat"
        )
    else:
        # Si no se encuentra ningún punto, simplemente agrega ".output" al final del nombre del archivo
        output_file = (
            file_name_only + f"-{astar_traslados.map.heuristic_mode}" + ".output"
        )
        info_file = file_name_only + f"-{astar_traslados.map.heuristic_mode}" + ".stat"

    # Escribe solucion en archivo .output
    astar_traslados.export_solution(resultado, output_file)
    astar_traslados.export_info(
        info_file, total_time, resultado[-1].g, len(resultado), astar_traslados.expanded
    )


def main():
    file_name = EASY_PATH
    mode = 0

    # Parsear los argumentos
    args = parseArgs()

    # Acceder a los valores de los argumentos
    if args.file:
        file_name = args.file
    if args.mode:
        mode = int(args.mode)

    # Configura ASTARTraslados segun las flags
    astar_traslados = ASTARTraslados(file_name, mode)
    if args.verbose:
        astar_traslados.verbose_flag = 1
    if args.check:
        astar_traslados.check_flag = 1
    if args.admissibility:
        astar_traslados.check_ad = 1

    # Busqueda del mejor cmaino
    resultado = []
    inicio_tiempo = time.time()
    resultado = astar_traslados.search_path()
    fin_tiempo = time.time()
    total_time = fin_tiempo - inicio_tiempo

    # Reescala los costes
    for node in resultado:
        node.g = node.g / HEURISTIC_ESCALE

    if args.verbose or args.result:
        # Muestra los resultados por consola
        printResults(resultado, total_time, astar_traslados, args)

    # Genera archivos de salida
    writeResults(file_name, astar_traslados, resultado, total_time)


if __name__ == "__main__":
    main()
