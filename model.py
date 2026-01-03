import math
import random

class Road:
    def __init__(self, length, num_lanes=2):
        self.length = length
        self.num_lanes = num_lanes
        # List of tuples: (start_pos, end_pos, limit)
        # We assume limits apply to all lanes for simplicity in this version
        self.speed_limit_zones = []

    def add_speed_limit_zone(self, start, end, limit):
        # Remove existing zone overlapping or just append?
        # Simple append, logic will take the lowest limit if multiple overlap
        self.speed_limit_zones.append({'start': start, 'end': end, 'limit': limit})
    
    def clear_zones(self):
        self.speed_limit_zones = []

    def get_speed_limit_at(self, position):
        min_limit = float('inf')
        for zone in self.speed_limit_zones:
            # Handle wrapping zones if needed (not implemented yet for simplicity)
            if zone['start'] <= position <= zone['end']:
                if zone['limit'] < min_limit:
                    min_limit = zone['limit']
        return min_limit

class Vehicle:
    def __init__(self, id, position, lane, desired_speed):
        self.id = id
        self.position = position
        self.lane = lane
        self.velocity = desired_speed * 0.5
        self.desired_speed = desired_speed
        self.acceleration = 0
        self.length = 5
        self.width = 2
        
        # IDM Parameters
        self.max_acceleration = 1.0 # a
        self.comfortable_deceleration = 1.5 # b
        self.min_gap = 2.0 # s0
        self.time_headway = 1.5 # T
        
        # Lane Change Parameters
        self.cooldown = 0
        
        self.color = (0, 0, 255)

    def update(self, dt, lead_vehicle, road, neighbors):
        # Neighbors is a dict: {'left_lead', 'left_floll', 'right_lead', 'right_foll'}
        
        if self.cooldown > 0:
            self.cooldown -= dt

        # 1. Update Position
        self.position += self.velocity * dt
        if self.position > road.length:
            self.position -= road.length

        # 2. Lane Change Logic (Simple)
        # If stuck behind slow car, and other lane is faster/free
        self._try_lane_change(lead_vehicle, neighbors, road)

        # 3. IDM Acceleration (Longitudinal)
        limit = road.get_speed_limit_at(self.position)
        effective_desired = min(self.desired_speed, limit)
        
        self.acceleration = self._calculate_idm_accel(self.velocity, effective_desired, lead_vehicle, road.length)

        # 4. Update Velocity
        self.velocity += self.acceleration * dt
        if self.velocity < 0: self.velocity = 0
        
        # Color Update
        self._update_color(effective_desired)

    def _calculate_idm_accel(self, v, v0, leader, road_len):
        delta_v = 0
        s = float('inf')
        
        if leader:
            s = leader.position - self.position
            if s < 0: s += road_len
            s -= self.length
            delta_v = v - leader.velocity
        
        # Safety clamp for s
        if s <= 0.1: s = 0.1

        s_star = (self.min_gap + 
                  (v * self.time_headway) + 
                  (v * delta_v) / (2 * math.sqrt(self.max_acceleration * self.comfortable_deceleration)))

        term1 = (v / v0) ** 4 if v0 > 0 else 0
        term2 = (s_star / s) ** 2
        
        return self.max_acceleration * (1 - term1 - term2)

    def _try_lane_change(self, lead, neighbors, road):
        if self.cooldown > 0: return

        # Only consider changing if speed is inhibited
        # or if random probability (politeness factor?)
        
        current_acc = self.acceleration
        
        # Check lanes
        # Assume 2 lanes: 0 and 1.
        target_lane = 1 - self.lane
        
        # Get neighbors in target lane
        # We need to know who would be my leader and follower in target lane
        # "neighbors" arg passed from simulation should have this info for the target lane
        
        # Simplified: Simulation passes us the object candidates
        # simulation.py will have to find:
        # target_leader = closest vehicle ahead in target lane
        # target_follower = closest vehicle behind in target lane
        
        target_leader = neighbors['target_leader']
        target_follower = neighbors['target_follower']

        # Safety Criterion: Would I crash into target_leader? Would target_follower crash into me?
        # Check simple gaps
        safe_gap_front = 10 # meters, simplified
        safe_gap_back = 10
        
        gap_front = float('inf')
        if target_leader:
            dist = target_leader.position - self.position
            if dist < 0: dist += road.length
            gap_front = dist - target_leader.length
            
        gap_back = float('inf')
        if target_follower:
            dist = self.position - target_follower.position
            if dist < 0: dist += road.length
            gap_back = dist - self.length

        if gap_front < safe_gap_front or gap_back < safe_gap_back:
            return # Unsafe

        # Incentive Criterion:
        # Gain in acceleration? 
        # Calculate accel if I stay related to 'lead'
        # Calculate accel if I move related to 'target_leader'
        
        limit = road.get_speed_limit_at(self.position)
        eff_speed = min(self.desired_speed, limit)

        acc_stay = self._calculate_idm_accel(self.velocity, eff_speed, lead, road.length)
        acc_move = self._calculate_idm_accel(self.velocity, eff_speed, target_leader, road.length)
        
        # Hysteresis threshold
        if acc_move > acc_stay + 0.5: # significant gain needed
            self.lane = target_lane
            self.cooldown = 2.0 # Wait 2 seconds before changing again

    def _update_color(self, limit):
        if self.velocity < 2:
            self.color = (255, 0, 0)
        elif self.velocity < limit * 0.6:
            self.color = (255, 165, 0)
        else:
            self.color = (0, 255, 0)
