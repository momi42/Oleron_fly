# Core simulation runner [cite: 533]

from typing import Dict, Tuple, Set, List, Optional, NamedTuple
from models import Zone, Connection, NetworkGraph, ZoneType
from collections import deque


class ReservationTable:
    def __init__(self) -> None:
        # Maps (zone_name, turn) -> count of drones occupying it
        self.zone_occupancy: Dict[Tuple[str, int], int] = {}
        # Maps (canonical_connection_key,turn) -> count of drones traversing it
        self.link_occupancy: Dict[Tuple[Tuple[str, str], int], int] = {}

    def is_zone_available(self, zone: Zone, turn: int) -> bool:
        # Start and End zones have unlimited capacity
        if zone.prefix in ("start_hub", "end_hub"):
            return True
        current_count = self.zone_occupancy.get((zone.name, turn), 0)
        return (True if (current_count) < (zone.max_drones) else False)

    def is_link_available(self, conn: Connection, turn: int) -> bool:
        key = tuple(sorted([conn.zone_a.name, conn.zone_b.name]))
        current_count = self.link_occupancy.get((key, turn), 0)
        return (True if (current_count) < (conn.max_link_capacity) else False)

    def reserve_zone(self, zone: Zone, turn: int) -> None:
        if zone.prefix not in ("start_hub", "end_hub"):
            key = (zone.name, turn)
            self.zone_occupancy[key] = self.zone_occupancy.get(key, 0) + 1

    def reserve_link(self, conn: Connection, turn: int) -> None:
        key = (tuple(sorted([conn.zone_a.name, conn.zone_b.name])), turn)
        self.link_occupancy[key] = self.link_occupancy.get(key, 0) + 1


class PathStep(NamedTuple):
    zone: Zone
    arrival_turn: int
    transit_conn: Optional[Connection] = None


def find_path_for_drone(
    graph: NetworkGraph,
    reservations: ReservationTable,
    start_turn: int = 0
) -> Optional[List[PathStep]]:
    """Finds the fastest valid spatio-temporal route for one drone."""

    start = graph.start_zone
    end = graph.end_zone
    if not start or not end:
        return None

    # Queue items: (current_zone, current_turn, path_history)
    queue = deque([(start, start_turn, [PathStep(start, start_turn)])])

    # Track visited states to prevent infinite loops: (zone_name, turn)
    visited: Set[Tuple[str, int]] = set([(start.name, start_turn)])

    while queue:
        curr_zone, curr_turn, path = queue.popleft()

        # Destination reached!
        if curr_zone == end:
            return path

        # --- Option 1: Stay in place (Wait 1 turn) ---
        wait_turn = curr_turn + 1
        if (curr_zone.name, wait_turn) not in visited:
            if reservations.is_zone_available(curr_zone, wait_turn):
                visited.add((curr_zone.name, wait_turn))
                new_path = path + [PathStep(curr_zone, wait_turn)]
                queue.append((curr_zone, wait_turn, new_path))

        # --- Option 2: Move to adjacent zones ---
        connections = graph.adjacency.get(curr_zone.name, [])
        for conn in connections:
            neighbor = conn.get_other_zone(curr_zone)

            # Cannot enter blocked zones
            if neighbor.zone_type == ZoneType.BLOCKED:
                continue

            # Determine turn cost and movement mechanic
            if neighbor.zone_type == ZoneType.RESTRICTED:
                # Takes 2 turns: occupied link during turn T, arrival at T+2
                arrival_turn = curr_turn + 2

                # Verify link capacity on turn T and destination space at T+2
                if (reservations.is_link_available(conn, curr_turn) and
                   reservations.is_zone_available(neighbor, arrival_turn)):

                    state_key = (neighbor.name, arrival_turn)
                    if state_key not in visited:
                        visited.add(state_key)
                        step = PathStep(
                            neighbor, arrival_turn, transit_conn=conn)
                        queue.append((neighbor, arrival_turn, path + [step]))

            else:
                # Normal/Priority zone: 1 turn
                arrival_turn = curr_turn + 1

                if (reservations.is_link_available(conn, curr_turn) and
                   reservations.is_zone_available(neighbor, arrival_turn)):

                    state_key = (neighbor.name, arrival_turn)
                    if state_key not in visited:
                        visited.add(state_key)
                        step = PathStep(neighbor, arrival_turn)
                        queue.append((neighbor, arrival_turn, path + [step]))

    return None  # No valid path found


def reserve_drone_path(path: List[PathStep],
                       reservations: ReservationTable) -> None:
    for i in range(1, len(path)):
        prev_step = path[i - 1]
        curr_step = path[i]

        # Reserve link at departure turn
        if curr_step.transit_conn:
            reservations.reserve_link(
                curr_step.transit_conn, prev_step.arrival_turn)

        # Reserve destination zone at arrival turn
        reservations.reserve_zone(curr_step.zone, curr_step.arrival_turn)
