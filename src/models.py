# Object-oriented domain entities [cite: 394]

"""
ZoneType (Enum):
Defines NORMAL, BLOCKED, RESTRICTED, and PRIORITY
with their respective static movement weights.

Zone (Class):
Encapsulates spatial coordinates, metadata, total capacity (max_drones),
and a dynamic reservation registry to track drone presence per simulation turn.

Connection (Class):
Tracks bidirectional links between zones
along with their respective link capacity constraints
(max_link_capacity).

Drone (Class):
Represents individual agents, tracking their current location, state
(e.g., IDLE, MOVING, IN_TRANSIT_TO_RESTRICTED), and planned paths.  """


from enum import Enum
from typing import NamedTuple, Optional, Dict, List

# Defines NORMAL, BLOCKED, RESTRICTED, and PRIORITY
# with their respective static movement weights.


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Coordinates(NamedTuple):
    x: int
    y: int

# Encapsulates spatial coordinates, metadata, total capacity (max_drones),
# and a dynamic reservation registry
# to track drone presence per simulation turn.


class Zone:
    def __init__(
        self,
        name: str,
        prefix: str,
        coords: Coordinates,
        zone_type: ZoneType = ZoneType.NORMAL,
        color: Optional[str] = None,
        max_drones: int = 1
    ):
        self.name: str = name
        self.prefix: str = prefix  # e.g., "start_hub", "end_hub", "hub"
        self.coords: Coordinates = coords
        self.zone_type: ZoneType = zone_type
        self.color: Optional[str] = color
        self.max_drones: int = max_drones

        # We will also need to track how many
        # drones are currently in this zone per turn.
        # We can add that logic later when we build the simulation engine!


class Connection:
    def __init__(
        self,
        zone_a: Zone,
        zone_b: Zone,
        max_link_capacity: int = 1
    ):
        self.zone_a: Zone = zone_a
        self.zone_b: Zone = zone_b
        self.max_link_capacity: int = max_link_capacity

    def get_other_zone(self, current_zone: Zone) -> Zone:
        """
        Helper to get the zone on the other side of this bidirectional link.
        """
        if current_zone == self.zone_a:
            return self.zone_b
        return self.zone_a


# Represents individual agents, tracking their current location,
# state (e.g., IDLE, MOVING, IN_TRANSIT_TO_RESTRICTED), and planned paths.


class Drone:
    pass


class NetworkGraph:
    def __init__(self) -> None:
        self.zones: Dict[str, Zone] = {}
        self.adjacency: Dict[str, List[Connection]] = {}
        self.start_zone: Optional[Zone] = None
        self.end_zone: Optional[Zone] = None
        self.nb_drones: int = 0

    def add_zone(self, zone: Zone) -> None:
        """Stores a zone by its unique name."""
        self.zones[zone.name] = zone
        self.adjacency[zone.name] = []

        # Keep track of unique start and end zones
        if zone.prefix == "start_hub":
            self.start_zone = zone
        elif zone.prefix == "end_hub":
            self.end_zone = zone

    def add_connection(self, connection: Connection) -> None:
        """Registers a connection on both connected zones (bidirectional)."""
        name_a = connection.zone_a.name
        name_b = connection.zone_b.name

        self.adjacency[name_a].append(connection)
        self.adjacency[name_b].append(connection)

    def get_neighbors(self, zone_name: str) -> List[Zone]:
        """Returns all connected target zones from a given zone."""
        connections = self.adjacency.get(zone_name, [])
        current_zone = self.zones[zone_name]
        return [conn.get_other_zone(current_zone) for conn in connections]
