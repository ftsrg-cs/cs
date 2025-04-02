param map = localPath('../Scenic/assets/maps/CARLA/Town01.xodr') # adjust path if necessary
param carla_map = 'Town01'
model scenic.simulators.newtonian.driving_model

MAX_BREAK_THRESHOLD = 1
SAFETY_DISTANCE = 8
PARKING_SIDEWALK_OFFSET_RANGE = 2
CUT_IN_TRIGGER_DISTANCE = Range(10, 12)
EGO_SPEED = 8
PARKEDCAR_SPEED = 7

behavior CutInBehavior(laneToFollow, target_speed):
    while (distance from self to ego) >  CUT_IN_TRIGGER_DISTANCE:
        wait

    do FollowLaneBehavior(laneToFollow = laneToFollow, target_speed=target_speed)

behavior CollisionAvoidance():
    while withinDistanceToAnyObjs(self, SAFETY_DISTANCE):
        take SetBrakeAction(MAX_BREAK_THRESHOLD)


behavior EgoBehavior(target_speed):
    try: 
        do FollowLaneBehavior(target_speed=target_speed)

    interrupt when withinDistanceToAnyObjs(self, SAFETY_DISTANCE):
        do CollisionAvoidance()


roads = network.roads
select_road = Uniform(*roads)
ego_lane = select_road.lanes[0]

ego = new Car on ego_lane.centerline,
    with behavior EgoBehavior(target_speed=EGO_SPEED)

rightCurb = ego.laneGroup.curb
leftCurb = ego.oppositeLaneGroup.curb
spot = new OrientedPoint on visible rightCurb
parkedHeadingAngle = Uniform(-1,1)*Range(10,20) deg

other = new Car left of (spot offset by PARKING_SIDEWALK_OFFSET_RANGE @ 0), 
        facing parkedHeadingAngle relative to ego.heading,
        with behavior CutInBehavior(ego_lane, target_speed=PARKEDCAR_SPEED),
        with regionContainedIn None

require (angle from ego to other) - ego.heading < 0 deg
require 10 < (distance from ego to other) < 20

monitor StopAfterInteraction():
    for i in range(50):
        wait
    while ego.speed > 2:
        wait
    for i in range(50):
        wait
    terminate
require monitor StopAfterInteraction()
terminate after 15 seconds   # in case ego never breaks