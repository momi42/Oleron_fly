# Terminal ANSI color matrix renderer [cite: 447, 534]

import time
from typing import Dict, List
from models import NetworkGraph, ZoneType
from engine import PathStep


class TerminalVisualizer:
    """Provides visual colored terminal output for the drone simulation."""

    # ANSI Color Palette
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Zone Type Colors
    COLOR_NORMAL = "\033[36m"      # Cyan
    COLOR_PRIORITY = "\033[32m"    # Green
    COLOR_RESTRICTED = "\033[33m"  # Yellow
    COLOR_BLOCKED = "\033[31m"     # Red

    # Target Highlights
    COLOR_START = "\033[42m\033[30m"  # Green Background
    COLOR_END = "\033[41m\033[37m"    # Red Background
    COLOR_DRONE = "\033[35m"          # Magenta

    @classmethod
    def get_zone_color(cls, zone_type: ZoneType, prefix: str) -> str:
        """Returns the appropriate ANSI color code for a given zone."""
        if prefix == "start_hub":
            return cls.COLOR_START
        if prefix == "end_hub":
            return cls.COLOR_END

        mapping = {
            ZoneType.NORMAL: cls.COLOR_NORMAL,
            ZoneType.PRIORITY: cls.COLOR_PRIORITY,
            ZoneType.RESTRICTED: cls.COLOR_RESTRICTED,
            ZoneType.BLOCKED: cls.COLOR_BLOCKED,
        }
        return mapping.get(zone_type, cls.RESET)

    @classmethod
    def display_network_summary(cls, graph: NetworkGraph) -> None:
        """Displays an initial summary view of the parsed network graph."""
        print(f"\n{cls.BOLD}=== Network Graph Infrastructure ==={cls.RESET}")
        print(f"Total Drones: {cls.COLOR_DRONE}{graph.nb_drones}{cls.RESET}")
        print(f"Zones Loaded: {len(graph.zones)}")
        print("-" * 40)

        for name, zone in graph.zones.items():
            color = cls.get_zone_color(zone.zone_type, zone.prefix)
            meta_info = f"[max_drones={zone.max_drones},"
            f"type={zone.zone_type.value}]"
            print(f"  • {color}{name:<12}{cls.RESET} {meta_info}")
        print("-" * 40 + "\n")

    @classmethod
    def render_turn_by_turn(
        cls,
        drone_paths: Dict[int, List[PathStep]],
        delay: float = 0.2
    ) -> None:
        """Renders the step-by-step turn execution with color highlights."""
        # Process movements by turn
        turn_logs: Dict[int, List[str]] = {}

        for drone_id, path in drone_paths.items():
            for i in range(1, len(path)):
                prev_step = path[i - 1]
                curr_step = path[i]

                drone_tag = f"{cls.COLOR_DRONE}D{drone_id}{cls.RESET}"

                # In-flight movement (Restricted zone)
                if curr_step.transit_conn:
                    conn_str = f"{prev_step.zone.name}-{curr_step.zone.name}"
                    move_str = f"{drone_tag}-{cls.COLOR_RESTRICTED}"
                    f"{conn_str}{cls.RESET}"
                    transit_turn = prev_step.arrival_turn + 1
                    turn_logs.setdefault(transit_turn, []).append(move_str)

                    arrival_str = f"{drone_tag}-{cls.COLOR_RESTRICTED}"
                    f"{curr_step.zone.name}{cls.RESET}"
                    turn_logs.setdefault(
                        curr_step.arrival_turn, []).append(arrival_str)

                # Standard movement
                elif curr_step.zone != prev_step.zone:
                    z_color = cls.get_zone_color(
                        curr_step.zone.zone_type, curr_step.zone.prefix)
                    move_str = f"{drone_tag}-{z_color}"
                    f"{curr_step.zone.name}{cls.RESET}"
                    turn_logs.setdefault(
                        curr_step.arrival_turn, []).append(move_str)

        if not turn_logs:
            return

        max_turn = max(turn_logs.keys())
        print(f"{cls.BOLD}=== Simulation Execution Stream ==={cls.RESET}\n")

        for turn in range(1, max_turn + 1):
            moves = turn_logs.get(turn, [])
            if moves:
                turn_header = f"{cls.BOLD}Turn {turn:02d}:{cls.RESET}"
                moves_formatted = "  ".join(moves)
                print(f"{turn_header} {moves_formatted}")

                # Optional small delay for real-time visual streaming effect
                if delay > 0:
                    time.sleep(delay)

        print(
            f"\n{cls.COLOR_START}{cls.BOLD} SIMULATION COMPLETE {cls.RESET}\n")
