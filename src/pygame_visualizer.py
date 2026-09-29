import pygame
from typing import Dict, List, Tuple
from models import NetworkGraph, Zone, ZoneType
from engine import PathStep

# --- Configuration & Theme Colors ---
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
FPS = 60

COLOR_BG = (245, 245, 245)       # Light gray background like the subject PDF
COLOR_TEXT = (10, 10, 10)
COLOR_ARROW = (100, 100, 100)

# Colors matching zone categories
COLOR_START = (34, 139, 34)         # Dark Green
COLOR_END = (220, 20, 60)           # Crimson Red
COLOR_NORMAL = (0, 0, 255)          # Blue
COLOR_PRIORITY = (255, 215, 0)      # Gold / Yellow
COLOR_RESTRICTED = (138, 43, 226)   # Violet / Purple
COLOR_BLOCKED = (128, 128, 128)     # Gray
COLOR_DRONE = (255, 69, 0)          # Orange / Red Diamond marker


class PygameVisualizer:
    def __init__(self,
                 graph: NetworkGraph,
                 drone_paths: Dict[int, List[PathStep]]):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Fly-in Drone Routing Visualizer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 14, bold=True)
        self.drone_font = pygame.font.SysFont("Arial", 11, bold=True)

        self.graph = graph
        self.drone_paths = drone_paths

        # Calculate scaled screen positions for graph nodes
        self.node_positions: \
            Dict[str, Tuple[float, float]] = self._calculate_layout()

        # Determine total simulation turns
        self.max_turn = max(
            (step.arrival_turn for path
             in drone_paths.values() for step in path),
            default=0
        )
        self.current_turn = 0
        self.anim_progress = 0.0
        # Interpolation factor from 0.0 to 1.0 between turns
        self.paused = False

    def _calculate_layout(self) -> Dict[str, Tuple[float, float]]:
        """
        Scales map (x, y) integer coordinates
        to fit the Pygame window nicely.
        """
        coords = [z.coords for z in self.graph.zones.values()]
        if not coords:
            return {}

        min_x = min(c.x for c in coords)
        max_x = max(c.x for c in coords)
        min_y = min(c.y for c in coords)
        max_y = max(c.y for c in coords)

        # Padding boundaries
        pad_x, pad_y = 120, 120
        usable_w = WINDOW_WIDTH - 2 * pad_x
        usable_h = WINDOW_HEIGHT - 2 * pad_y

        layout = {}
        for name, zone in self.graph.zones.items():
            # Avoid division by zero for flat maps
            dx = (max_x - min_x) if max_x != min_x else 1
            dy = (max_y - min_y) if max_y != min_y else 1

            screen_x = pad_x + ((zone.coords.x - min_x) / dx) * usable_w
            # Invert Y axis so higher Y coordinates go upward on screen
            screen_y = (WINDOW_HEIGHT - pad_y) - (
                (zone.coords.y - min_y) / dy) * usable_h
            layout[name] = (screen_x, screen_y)

        return layout

    def _get_zone_color(self, zone: Zone) -> Tuple[int, int, int]:
        """Maps zone metadata to visual RGB colors."""
        if zone.prefix == "start_hub":
            return COLOR_START
        if zone.prefix == "end_hub":
            return COLOR_END

        mapping = {
            ZoneType.NORMAL: COLOR_NORMAL,
            ZoneType.PRIORITY: COLOR_PRIORITY,
            ZoneType.RESTRICTED: COLOR_RESTRICTED,
            ZoneType.BLOCKED: COLOR_BLOCKED,
        }
        return mapping.get(zone.zone_type, COLOR_NORMAL)

    def draw_connections(self) -> None:
        """Draws network links between zones with directional arrows."""
        for zone_name, conns in self.graph.adjacency.items():
            start_pos = self.node_positions[zone_name]
            for conn in conns:
                other_zone = conn.get_other_zone(self.graph.zones[zone_name])
                end_pos = self.node_positions[other_zone.name]

                # Draw connection line
                pygame.draw.line(
                    self.screen, COLOR_ARROW, start_pos, end_pos, 2)

    def draw_zones(self) -> None:
        """Draws circular nodes with titles matching PDF formatting."""
        for name, zone in self.graph.zones.items():
            pos = self.node_positions[name]
            color = self._get_zone_color(zone)

            # Node circle
            pygame.draw.circle(
                self.screen, color, (int(pos[0]), int(pos[1])), 28)
            pygame.draw.circle(
                self.screen, COLOR_TEXT, (int(pos[0]), int(pos[1])), 28, 2)

            # Zone label text inside or near circle
            lbl = self.font.render(name, True, (255, 255, 255)
                                   if color != COLOR_PRIORITY else (0, 0, 0))
            lbl_rect = lbl.get_rect(center=(int(pos[0]), int(pos[1])))
            self.screen.blit(lbl, lbl_rect)

    def _get_drone_position_at_turn(self,
                                    path: List[PathStep],
                                    turn: int,
                                    progress: float) -> Tuple[float, float]:
        """Calculates smooth interpolated screen coordinates
        for a drone during transit."""
        # Find path segment corresponding to the current turn window
        prev_step = path[0]
        curr_step = path[0]

        for step in path:
            if step.arrival_turn <= turn:
                prev_step = step
            if step.arrival_turn >= turn:
                curr_step = step
                break

        start_pos = self.node_positions[prev_step.zone.name]
        end_pos = self.node_positions[curr_step.zone.name]

        # Interpolate linear position: P(t) = P1 + (P2 - P1) * progress
        ix = start_pos[0] + (end_pos[0] - start_pos[0]) * progress
        iy = start_pos[1] + (end_pos[1] - start_pos[1]) * progress
        return (ix, iy)

    def draw_drones(self) -> None:
        """Draws diamond-shaped drone markers matching PDF diagrams."""
        for drone_id, path in self.drone_paths.items():
            pos = self._get_drone_position_at_turn(
                path, self.current_turn, self.anim_progress)

            # Draw diamond icon
            x, y = pos
            size = 12
            diamond_pts = [
                (x, y - size), (x + size, y), (x, y + size), (x - size, y)]
            pygame.draw.polygon(self.screen, COLOR_DRONE, diamond_pts)
            pygame.draw.polygon(self.screen, (0, 0, 0), diamond_pts, 1)

            # Label drone ID (e.g., D1, D2)
            tag = self.drone_font.render(f"D{drone_id}", True, (255, 255, 255))
            tag_rect = tag.get_rect(center=(int(x), int(y)))
            self.screen.blit(tag, tag_rect)

    def draw_hud(self) -> None:
        """Displays step controls and status on screen."""
        hud_text = f"Turn: {self.current_turn} / {self.max_turn}  "
        "|  [Space]: Pause/Resume  |  [R]: Reset"
        lbl = self.font.render(hud_text, True, COLOR_TEXT)
        self.screen.blit(lbl, (20, 20))

    def run(self) -> None:
        """Main Pygame render loop."""
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0  # seconds per frame

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r:
                        self.current_turn = 0
                        self.anim_progress = 0.0

            # Advance animation progress
            if not self.paused and self.current_turn < self.max_turn:
                self.anim_progress += dt * 1.5  # Controls animation speed
                if self.anim_progress >= 1.0:
                    self.anim_progress = 0.0
                    self.current_turn += 1

            # Render frame
            self.screen.fill(COLOR_BG)
            self.draw_connections()
            self.draw_zones()
            self.draw_drones()
            self.draw_hud()

            pygame.display.flip()

        pygame.quit()
