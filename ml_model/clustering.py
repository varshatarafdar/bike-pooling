from sklearn.cluster import KMeans
import pandas as pd

def cluster_locations(rides):
    data = pd.DataFrame(rides)

    X = data[['start_lat', 'start_lng']]

    kmeans = KMeans(n_clusters=3, random_state=0)
    data['cluster'] = kmeans.fit_predict(X)

    return data