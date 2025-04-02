param map = localPath('../Scenic/assets/maps/CARLA/Town01.xodr') # adjust path if necessary
model scenic.domains.driving.model

ego = new Car with color (1.0, 0.0, 0.0, 1.0)
blue = new Car with color (0.0, 0.0, 1.0, 1.0)
green = new Car with color (0.0, 1.0, 0.0, 1.0)