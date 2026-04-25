import math

# ==============================
# 📏 HAVERSINE DISTANCE (KM)
# ==============================
def calculate_distance(lat1, lon1, lat2, lon2):

    try:
        R = 6371  # Earth radius in KM

        # convert to float safely
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])

        # convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + \
            math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c

        return round(distance, 3)

    except Exception as e:
        print("Distance Error:", e)
        return float("inf")