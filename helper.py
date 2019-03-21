import random
def genRandLocation():
    lat = random.randrange(-90, 90)
    lon = random.randrange(-180, 180)
    return (lat, lon)