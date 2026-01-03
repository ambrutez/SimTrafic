import random
from model import Vehicle, Road

class SimulationController:
    def __init__(self, road_length=2000):
        self.road = Road(road_length, num_lanes=2)
        self.vehicles = []
        self.current_time = 0
        self.next_vehicle_id = 0
        self.target_vehicle_count = 0
        self.base_desired_speed = 30 # m/s

    def set_target_vehicle_count(self, count):
        self.target_vehicle_count = int(count)

    def set_base_desired_speed(self, speed):
        self.base_desired_speed = float(speed)
        for v in self.vehicles:
            v.desired_speed = self.base_desired_speed + random.uniform(-2, 2)

    def update(self, dt):
        self.current_time += dt

        # Spawn/Despawn
        if len(self.vehicles) < self.target_vehicle_count:
            self._spawn_vehicle()
        elif len(self.vehicles) > self.target_vehicle_count:
            self.vehicles.pop()

        # Sort for easy linear neighbor lookup
        self.vehicles.sort(key=lambda v: v.position)

        # Build lane lists for easy lookup
        lanes = [[], []]
        for v in self.vehicles:
            lanes[v.lane].append(v)
            
        # Update each vehicle
        for v in self.vehicles:
            current_lane_cars = lanes[v.lane]
            target_lane_idx = 1 - v.lane
            target_lane_cars = lanes[target_lane_idx]
            
            # Find leader in current lane
            leader = self._find_leader(v, current_lane_cars)
            
            # Find neighbors in target lane for LCD (Lane Change Decision)
            target_leader = self._find_leader(v, target_lane_cars)
            target_follower = self._find_follower(v, target_lane_cars)
            
            neighbors = {
                'target_leader': target_leader,
                'target_follower': target_follower
            }
            
            v.update(dt, leader, self.road, neighbors)

    def _find_leader(self, agent, lane_cars):
        if not lane_cars: return None
        # Since lane_cars is not fully sorted by position (v.lane might change mid-frame in other systems, but here we rebuild logic)
        # Actually we sorted self.vehicles, but lane_cars is subset, still sorted by position.
        
        # Find first car with pos > agent.pos
        # Because it's a loop, if no car > agent.pos, leader is the first car in list (wrapped)
        
        for car in lane_cars:
            if car.position > agent.position:
                return car
        
        # Wrap around
        if lane_cars:
            return lane_cars[0] # Smallest position (just wrapped)
        return None

    def _find_follower(self, agent, lane_cars):
        if not lane_cars: return None
        # Find last car with pos < agent.pos
        
        follower = None
        for car in lane_cars:
            if car.position < agent.position:
                follower = car
            else:
                break # Since sorted, we passed potential followers
                
        if follower is None and lane_cars:
            # Wrap around: largest position car is behind me (across start line)
            return lane_cars[-1]
            
        return follower

    def _spawn_vehicle(self):
        pos = random.uniform(0, self.road.length)
        lane = random.randint(0, 1)
        speed = self.base_desired_speed + random.uniform(-2, 2)
        v = Vehicle(self.next_vehicle_id, pos, lane, speed)
        self.next_vehicle_id += 1
        self.vehicles.append(v)
