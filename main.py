import pygame
import sys
import math
from simulation import SimulationController

# Configuration
WIDTH, HEIGHT = 1200, 700 # Bigger for oval
FPS = 60

# Oval Geometry
OVAL_RADIUS = 150
STRAIGHT_LENGTH = 800
# Total logical length
ROAD_LENGTH = 2 * (STRAIGHT_LENGTH + math.pi * OVAL_RADIUS) 

# Colors
WHITE = (255, 255, 255)
BG_COLOR = (34, 139, 34) # Grass Green
ROAD_COLOR = (50, 50, 50)
MARKER_COLOR = (255, 255, 255)
ZONE_COLOR = (255, 100, 100) # Light red overlay

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Simulación de Tráfico V2 - Circuito Ovalado")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 14)
        self.title_font = pygame.font.SysFont("Arial", 20, bold=True)

        self.sim = SimulationController(road_length=ROAD_LENGTH)
        self.sim.set_target_vehicle_count(40)
        self.sim.set_base_desired_speed(120 / 3.6) # 120 km/h default

        # Zones: 2 configurable zones
        # Init zones: Zone 1 at top straight, Zone 2 at bottom straight
        # Start vals: Max speed (no limit)
        self.zone1_limit_kmh = 120
        self.zone2_limit_kmh = 120
        
        # Zone 1: 200m to 600m (Top straight)
        self.zone1_range = (200, 600)
        # Zone 2: 1500m to 1900m (Bottom straight approx) 
        # Road structure: Top Straight -> Right Curve -> Bottom Straight -> Left Curve
        # Top Straight: 0 to 800
        # Right Curve: 800 to 800 + pi*R (~1271)
        # Bottom Straight: 1271 to 2071
        self.zone2_range = (1400, 1800)
        
        self.update_zones()

        # UI
        self.dragging_slider = None
        # Helper config for sliders
        self.sliders = [
            {'name': 'Cant. Vehículos', 'min': 0, 'max': 150, 'val': 40, 'y': 50, 'action': self.update_count_ui},
            {'name': 'Vel. Global (km/h)', 'min': 30, 'max': 180, 'val': 120, 'y': 90, 'action': self.update_speed_ui},
            {'name': 'Límite Zona 1 (km/h)', 'min': 10, 'max': 150, 'val': 120, 'y': 130, 'action': self.update_z1},
            {'name': 'Límite Zona 2 (km/h)', 'min': 10, 'max': 150, 'val': 120, 'y': 170, 'action': self.update_z2}
        ]
        
        self.center_x = WIDTH // 2
        self.center_y = HEIGHT // 2

    def update_zones(self):
        self.sim.road.clear_zones()
        self.sim.road.add_speed_limit_zone(self.zone1_range[0], self.zone1_range[1], self.zone1_limit_kmh / 3.6)
        self.sim.road.add_speed_limit_zone(self.zone2_range[0], self.zone2_range[1], self.zone2_limit_kmh / 3.6)

    def update_count_ui(self, val):
        self.sim.set_target_vehicle_count(val)

    def update_speed_ui(self, val):
        self.sim.set_base_desired_speed(val / 3.6)

    def update_z1(self, val):
        self.zone1_limit_kmh = val
        self.update_zones()

    def update_z2(self, val):
        self.zone2_limit_kmh = val
        self.update_zones()

    def get_pos_on_oval(self, linear_pos, lane_offset):
        # Map linear pos (0 to ROAD_LENGTH) to (x, y)
        # 0 starts at left-top of straight: (-S/2, -R) ? No, let's center it.
        # Let's say loop starts at Top-Left of straight section, moving Right.
        
        # Geometry:
        # Top Straight: from x = -S/2 to S/2 at y = -R
        # Right Arc: from angle -90 to 90 (or 270 to 90)
        # Bottom Straight: from S/2 to -S/2 at y = R
        # Left Arc: from 90 to 270
        
        # Lane offset: outer lane is larger radius?
        # Standard track: lane 0 inner, lane 1 outer?
        # Logic is simpler if lane 0 is r, lane 1 is r + lane_width
        
        base_r = OVAL_RADIUS
        # Visual lane width approx 15px
        r = base_r + (lane_offset * 15) 
         
        s_len = STRAIGHT_LENGTH
        curve_len = math.pi * r # Approximate curve length for specific lane?
        # Note: logic road length is fixed (centerline approximation). 
        # Visually we might speed up/slow down cars on curves if we map strictly 1:1, but acceptable for demo.
        
        # Mapping based on Centerline definition:
        # Top Straight: [0, S]
        # Right Curve: [S, S + pi*R_center]
        # Bot Straight: [S + pi*R, 2S + pi*R]
        # Left Curve: [2S + pi*R, 2S + 2pi*R]
        
        arc_len = math.pi * OVAL_RADIUS
        
        p = linear_pos
        
        # Adjust coordinate system origin to center of screen
        cx, cy = self.center_x, self.center_y
        
        if p < s_len:
            # Top Straight (Left to Right)
            # x goes from -S/2 to S/2
            # y = -r
            pct = p / s_len
            x = -s_len/2 + pct * s_len
            y = -r
            return cx + x, cy + y
            
        p -= s_len
        if p < arc_len:
            # Right Curve
            # Angle goes from -pi/2 (top) to +pi/2 (bottom) clockwise
            pct = p / arc_len
            angle = -math.pi/2 + pct * math.pi
            x = s_len/2 + math.cos(angle) * r
            y = math.sin(angle) * r
            return cx + x, cy + y
            
        p -= arc_len
        if p < s_len:
            # Bottom Straight (Right to Left)
            pct = p / s_len
            x = s_len/2 - pct * s_len
            y = r
            return cx + x, cy + y
            
        p -= s_len
        # Left Curve
        # Angle goes from pi/2 to 3pi/2 (top)
        pct = p / arc_len # Remain 
        angle = math.pi/2 + pct * math.pi
        x = -s_len/2 + math.cos(angle) * r
        y = math.sin(angle) * r
        return cx + x, cy + y

    def draw_road(self):
        # Draw Grass
        self.screen.fill(BG_COLOR)
        
        # Draw Layout (thick gray line)
        # We need to draw 2 ovals: inner edge and outer edge?
        # Or just one thick line
        
        # For zone highlighting, it's tricky on oval. We can iterate small steps?
        # Or just draw zones first if we can map them.
        
        # Simplest: Draw Asphalt
        # Inner loop
        # Rects for straights
        rect_h = 40 # 2 lanes * 20
        # Top Straight
        top_rect = pygame.Rect(self.center_x - STRAIGHT_LENGTH//2, self.center_y - OVAL_RADIUS - 10, STRAIGHT_LENGTH, 35) # 10 is lane offset visual
        bot_rect = pygame.Rect(self.center_x - STRAIGHT_LENGTH//2, self.center_y + OVAL_RADIUS - 10, STRAIGHT_LENGTH, 35)
        
        pygame.draw.rect(self.screen, ROAD_COLOR, top_rect)
        pygame.draw.rect(self.screen, ROAD_COLOR, bot_rect)
        
        # Arcs
        # Pygame arc is not filled properly for roads easily.
        # Draw circles.
        # Right Circle
        right_center = (int(self.center_x + STRAIGHT_LENGTH//2), self.center_y)
        pygame.draw.circle(self.screen, ROAD_COLOR, right_center, OVAL_RADIUS + 25)
        pygame.draw.circle(self.screen, BG_COLOR, right_center, OVAL_RADIUS - 10)
        # Box clear left side of circle to make it semi?
        # Not needed if we layer right.
        # Cover left half of right circle with BG? No, straights connect.
        
        # Left Circle
        left_center = (int(self.center_x - STRAIGHT_LENGTH//2), self.center_y)
        pygame.draw.circle(self.screen, ROAD_COLOR, left_center, OVAL_RADIUS + 25)
        pygame.draw.circle(self.screen, BG_COLOR, left_center, OVAL_RADIUS - 10)
        
        # Redraw Center grass to clean up overlaps
        center_rect = pygame.Rect(self.center_x - STRAIGHT_LENGTH//2, self.center_y - OVAL_RADIUS + 10, STRAIGHT_LENGTH, (OVAL_RADIUS - 10)*2)
        pygame.draw.rect(self.screen, BG_COLOR, center_rect)

        # Draw Zone Markers (Visual approx)
        # Zone 1 (Top Straight part)
        z1_start_x = self.center_x - STRAIGHT_LENGTH//2 + 200
        z1_width = 400
        pygame.draw.rect(self.screen, ZONE_COLOR, (z1_start_x, self.center_y - OVAL_RADIUS - 15, z1_width, 5))
        
        # Zone 2 (Bottom Straight part)
        # 1400 linear starts at 1400 - (800 + 471) = ~129 into bottom straight? 
        # Approx visual: just draw where we logically put it
        z2_start_x = self.center_x + STRAIGHT_LENGTH//2 - (1400 - (STRAIGHT_LENGTH + math.pi*OVAL_RADIUS)) # Approx math
        # Actually logic is: Bottom straight starts at Right side. Moving Left.
        # Linear 1400 is relative to 000.
        # Start of Bot Straight is S + pi*R = 800 + 471 = 1271.
        # 1400 is 129m into straight.
        # Since it goes Right to Left, x = RightEdge - 129.
        if z2_start_x:
            pass # calculated in paint logic above is better?
             
        # Simple Labels for zones
        l1 = self.font.render("ZONA 1", True, WHITE)
        self.screen.blit(l1, (self.center_x, self.center_y - OVAL_RADIUS - 40))
        l2 = self.font.render("ZONA 2", True, WHITE)
        self.screen.blit(l2, (self.center_x, self.center_y + OVAL_RADIUS + 30))


    def draw_ui(self):
        # Panel
        panel_rect = pygame.Rect(20, 20, 260, 200)
        s = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180)) # Semi-transparent black
        self.screen.blit(s, (panel_rect.x, panel_rect.y))
        
        for sl in self.sliders:
            # Label
            val_txt = f"{int(sl['val'])}"
            lbl = self.font.render(f"{sl['name']}: {val_txt}", True, WHITE)
            self.screen.blit(lbl, (panel_rect.x + 10, sl['y'] - 15))
            
            # Bar
            bar_rect = pygame.Rect(panel_rect.x + 10, sl['y'], 200, 10)
            pygame.draw.rect(self.screen, (100, 100, 100), bar_rect)
            
            # Knob
            rng = sl['max'] - sl['min']
            pct = (sl['val'] - sl['min']) / rng
            kx = bar_rect.x + pct * bar_rect.width
            pygame.draw.circle(self.screen, WHITE, (int(kx), bar_rect.centery), 8)
            
            # Store rect for input
            sl['rect'] = bar_rect

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for s in self.sliders:
                    if 'rect' in s and s['rect'].inflate(10, 10).collidepoint(mx, my):
                        self.dragging_slider = s
                        # Immediate update on click
                        self.update_slider_val(s, mx)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging_slider = None
                
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_slider:
                    mx, _ = pygame.mouse.get_pos()
                    self.update_slider_val(self.dragging_slider, mx)
        return True

    def update_slider_val(self, s, mx):
        rect = s['rect']
        rel = mx - rect.x
        pct = max(0, min(1, rel / rect.width))
        new_val = s['min'] + pct * (s['max'] - s['min'])
        s['val'] = new_val
        s['action'](new_val)

    def run(self):
        running = True
        while running:
            running = self.handle_input()
            dt = self.clock.tick(FPS) / 1000.0
            
            self.sim.update(dt)
            
            self.draw_road()
            
            # Draw Vehicles
            for v in self.sim.vehicles:
                # Determine visual lane offset
                # Lane 0: Inner, Lane 1: Outer
                lane_off = 0 if v.lane == 0 else 1
                
                x, y = self.get_pos_on_oval(v.position, lane_off)
                
                # Draw
                pygame.draw.circle(self.screen, v.color, (int(x), int(y)), 5)
            
            self.draw_ui()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    App().run()
