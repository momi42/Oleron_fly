# Application entry point [cite: 366]

import sys
from typing import Dict, List
from models import NetworkGraph
from parser import ParserEngine, MapParseError
from engine import ReservationTable
from engine import find_path_for_drone, reserve_drone_path, PathStep
from visualizer import TerminalVisualizer
from pygame_visualizer import PygameVisualizer


def generate_simulation_output(drone_paths: Dict[int, List[PathStep]]) -> None:
    """
    Formats and prints the turn-by-turn simulation logs.
    """

    # Organizes movements by turn:
    # turn_logs[turn_number] = ["D1-roof1", "D2-corridorA"]
    turn_logs: Dict[int, List[str]] = {}

    for drone_id, path in drone_paths.items():
        for i in range(1, len(path)):
            prev_step = path[i - 1]
            curr_step = path[i]

            # Case 1: In-flight toward a restricted zone
            # (e.g., D1-corridorA-tunnelB)
            if curr_step.transit_conn:
                conn_name = f"{prev_step.zone.name}-{curr_step.zone.name}"
                move_str = f"D{drone_id}-{conn_name}"
                transit_turn = prev_step.arrival_turn + 1
                turn_logs.setdefault(transit_turn, []).append(move_str)

                # Arrival at restricted zone on turn T+2
                arrival_str = f"D{drone_id}-{curr_step.zone.name}"
                turn_logs.setdefault(
                    curr_step.arrival_turn, []).append(arrival_str)

            # Case 2: Standard move (or arrival from non-restricted)
            else:
                # Omit "moves" where the drone simply waited in place
                if curr_step.zone != prev_step.zone:
                    move_str = f"D{drone_id}-{curr_step.zone.name}"
                    turn_logs.setdefault(
                        curr_step.arrival_turn, []).append(move_str)

    # Print output line-by-line for each turn sequentially
    if not turn_logs:
        return

    max_turn = max(turn_logs.keys())
    for turn in range(1, max_turn + 1):
        moves = turn_logs.get(turn, [])
        if moves:
            print(" ".join(moves))


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_map_file> [--visual | --gui]")
        sys.exit(1)

    map_path = sys.argv[1]
    gui_mode = "--gui" in sys.argv
    visual_mode = "--visual" in sys.argv

    try:
        graph: NetworkGraph = ParserEngine.parse_file(map_path)
        reservations = ReservationTable()
        drone_paths = {}

        for drone_id in range(1, graph.nb_drones + 1):
            path = find_path_for_drone(graph, reservations, start_turn=0)
            if not path:
                print(
                    f"Error: Pathfinding failed for Drone D{drone_id}",
                    file=sys.stderr)
                sys.exit(1)

            reserve_drone_path(path, reservations)
            drone_paths[drone_id] = path

        if gui_mode:
            # Launch Pygame Graphical Window
            gui = PygameVisualizer(graph, drone_paths)
            gui.run()
        else:
            # Output terminal text stream
            TerminalVisualizer.render_turn_by_turn(
                drone_paths, delay=0.15 if visual_mode else 0.0)

    except MapParseError as e:
        print(f"Parsing Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
