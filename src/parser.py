# The parser will read line-by-line using a context manager,
# enforcing the specific metadata constraints using strict regex parsing:
# Throws an explicit line-numbered exception
# if multiple start_hub or end_hub declarations are found.
# Validates that zone names do not contain dashes or spaces.
# Ensures connections link only to existing, previously instantiated tokens.

import re
from typing import Set, Tuple, Dict
from models import Zone, ZoneType, Coordinates, Connection, NetworkGraph


class MapParseError(Exception):
    """Custom exception raised when map parsing fails."""
    pass


class ParserEngine:
    @staticmethod
    def parse_file(file_path: str) -> NetworkGraph:
        graph = NetworkGraph()
        seen_connections: Set[Tuple[str, ...]] = set()

        with open(file_path, "r", encoding="utf-8") as file:
            for line_num, raw_line in enumerate(file, start=1):
                # 1. Ignore comments and empty lines
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                # Split line into prefix and payload
                if ":" not in line:
                    raise MapParseError(
                        f"Line {line_num}: Missing ':' in statement.")

                prefix, payload = line.split(":", 1)
                prefix = prefix.strip()
                payload = payload.strip()

                # Handle nb_drones
                if prefix == "nb_drones":
                    try:
                        graph.nb_drones = int(payload)
                        if graph.nb_drones <= 0:
                            raise ValueError
                    except ValueError:
                        raise MapParseError(
                            f"Line {line_num}: "
                            "nb_drones must be a positive integer.")

                # Handle Zones (start_hub, end_hub, hub)
                elif prefix in ("start_hub", "end_hub", "hub"):
                    ParserEngine._parse_zone(graph, prefix, payload, line_num)

                # Handle Connections
                elif prefix == "connection":
                    ParserEngine._parse_connection(
                        graph, payload, seen_connections, line_num)

                else:
                    raise MapParseError(
                        f"Line {line_num}: Unknown prefix '{prefix}'.")

        # Post-parsing validations
        if graph.start_zone is None:
            raise MapParseError("Map definition is missing a 'start_hub'.")
        if graph.end_zone is None:
            raise MapParseError("Map definition is missing an 'end_hub'.")

        return graph

    @staticmethod
    def _extract_metadata(payload: str) -> Tuple[str, Dict[str, str]]:
        """Separates main payload from bracketed metadata."""
        metadata: Dict[str, str] = {}

        # Match content inside brackets [...]
        match = re.search(r'\[(.*?)\]', payload)
        if match:
            meta_str = match.group(1)
            # Remove bracketed part from the main payload string
            payload = payload.replace(match.group(0), "").strip()

            # Parse items like 'zone=priority color=green max_drones=2'
            for item in meta_str.split():
                if '=' in item:
                    k, v = item.split('=', 1)
                    metadata[k] = v
                else:
                    metadata[item] = "true"  # for flags

        return payload.strip(), metadata

    @staticmethod
    def _parse_zone(
                    graph: NetworkGraph,
                    prefix: str,
                    payload: str,
                    line_num: int) -> None:

        # Separate main payload from bracketed metadata
        raw_data, metadata = ParserEngine._extract_metadata(payload)
        tokens = raw_data.split()

        if len(tokens) != 3:
            raise MapParseError(f"Line {line_num}: Expected <name> <x> <y>.")

        name, x_str, y_str = tokens

        # Rule: Zone names cannot contain dashes or spaces
        if "-" in name:
            raise MapParseError(
                f"Line {line_num}: Zone name '{name}' cannot contain dashes.")

        # Parse coordinates
        try:
            x, y = int(x_str), int(y_str)
        except ValueError:
            raise MapParseError(
                f"Line {line_num}: Coordinates must be integers.")

        # Parse metadata
        z_type_str = metadata.get("zone", "normal")
        try:
            z_type = ZoneType(z_type_str)
        except ValueError:
            raise MapParseError(
                f"Line {line_num}: Invalid zone type '{z_type_str}'.")

        color = metadata.get("color")
        max_drones = int(metadata.get("max_drones", "1"))

        # Ensure single start/end hub
        if prefix == "start_hub" and graph.start_zone is not None:
            raise MapParseError(
                f"Line {line_num}: Duplicate start_hub defined.")
        if prefix == "end_hub" and graph.end_zone is not None:
            raise MapParseError(f"Line {line_num}: Duplicate end_hub defined.")

        zone = Zone(
            name=name,
            prefix=prefix,
            coords=Coordinates(x, y),
            zone_type=z_type,
            color=color,
            max_drones=max_drones
        )
        graph.add_zone(zone)

    @staticmethod
    def _parse_connection(
                        graph: NetworkGraph,
                        payload: str,
                        seen: Set[Tuple[str, ...]],
                        line_num: int) -> None:

        raw_data, metadata = ParserEngine._extract_metadata(payload)
        if "-" not in raw_data:
            raise MapParseError(
                f"Line {line_num}: Connection format must be zone1-zone2.")

        zone_a_name, zone_b_name = raw_data.split("-", 1)

        # Check if zones exist
        if zone_a_name not in graph.zones or zone_b_name not in graph.zones:
            raise MapParseError(
                f"Line {line_num}: Connection references undefined zones.")

        # Check duplicate connections
        conn_key = tuple(sorted([zone_a_name, zone_b_name]))
        if conn_key in seen:
            raise MapParseError(
                f"Line {line_num}: "
                f"Duplicate connection '{zone_a_name}-{zone_b_name}'.")
        seen.add(conn_key)

        max_cap = int(metadata.get("max_link_capacity", "1"))
        conn = Connection(
            graph.zones[zone_a_name],
            graph.zones[zone_b_name],
            max_link_capacity=max_cap)
        graph.add_connection(conn)


if __name__ == "__main__":
    parse = ParserEngine.parse_file(
        "/home/mohfalla/Desktop/fly_in/"
        "fly_in-main/maps/medium/01_dead_end_trap.txt")
    print(type(parse))
    print(parse.nb_drones)
    zones = parse.zones
    for z in zones:
        print(z)
