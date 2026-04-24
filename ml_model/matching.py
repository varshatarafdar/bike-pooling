from utils.distance import calculate_distance

def find_best_matches(user_ride, rides):
    matches = []

    for ride in rides:
        dist = calculate_distance(
            user_ride['start_lat'],
            user_ride['start_lng'],
            ride['start_lat'],
            ride['start_lng']
        )

        time_diff = abs(int(user_ride['time']) - int(ride['time']))

        if dist < 3 and time_diff < 10:  # threshold
            matches.append({
                "ride": ride,
                "distance": dist,
                "time_diff": time_diff
            })

    matches = sorted(matches, key=lambda x: (x['distance'], x['time_diff']))

    return matches[:5]  # top 5 matches