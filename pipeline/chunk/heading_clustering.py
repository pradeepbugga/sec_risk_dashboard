import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from chunk.color_utils import color_distance
from chunk.capital_feature_utils import is_title_case

def cluster_heading_styles(headings, body_color):

    features = []
    for h in headings:
        features.append([
            h["font_size"] or 0,
            h["font_weight"] or 400,
            int(h.get("italic", False)),
            int(h.get("underline", False)),
            int(h.get("is_all_caps", False)), 
            int(is_title_case(h.get("text", ""))),
            color_distance(h["font_color"], body_color) if h.get("font_color") else 0
        ])

    X = np.array(features)
    X_scaled = StandardScaler().fit_transform(X)

    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=1.5,
        linkage='ward'
    )

    labels = clustering.fit_predict(X_scaled)

    for label in np.unique(labels):
        cluster = X[labels == label]
        print("Cluster", label)
        print("Mean font size:", cluster[:,0].mean())
        print("Mean font weight:", cluster[:,1].mean())
        print("Mean italic:", cluster[:,2].mean())
        print("Mean underline:", cluster[:,3].mean())
        print("Mean all caps:", cluster[:,4].mean())
        print("Mean title case:", cluster[:,5].mean())
        print("Mean color distance:", cluster[:,6].mean())
        print()

    return labels