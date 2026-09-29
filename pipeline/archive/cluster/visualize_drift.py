import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the theme intensity metrics
metrics_df = pd.read_csv("./data/theme_intensity/INTC/risk_factors/metrics_2.csv")

# Convert year to integer for proper sorting
metrics_df['year'] = metrics_df['year'].astype(int) 

'''
# Plot Mean Top 3 Scores over Years
plt.figure(figsize=(10, 6))
sns.lineplot(data=metrics_df, x='year', y='mean_top3', marker='o')
plt.title('Mean Top 3 Theme Intensity Scores Over Years')
plt.xlabel('Year')
plt.ylabel('Mean Top 3 Scores')
plt.grid(True)
plt.savefig('./data/theme_intensity/INTC/risk_factors/mean_top3_scores.png')
plt.show()
'''

#plot number above threshold over years
plt.figure(figsize=(10, 6))
sns.lineplot(data=metrics_df, x='year', y='count_above_0.40', marker='o', color='orange')
plt.title('Count of Chunks Above Theme Score Threshold Over Years')
plt.xlabel('Year')
plt.ylabel('Count Above 0.40')
plt.grid(True)
plt.savefig('./data/theme_intensity/INTC/risk_factors/count_above_0.40.png')
plt.show()