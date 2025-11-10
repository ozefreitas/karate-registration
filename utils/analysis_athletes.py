import matplotlib.pyplot as plt
import os
import django
import pandas as pd

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "karate_registration.settings")
django.setup()

from registration.models import Member

# Fetch data from the model
queryset = Member.objects.all().values("category")  # Get only the category column
df = pd.DataFrame(queryset)

# Count occurrences of each category
category_counts = df["category"].value_counts()

import seaborn as sns

# Plot the bar chart
plt.figure(figsize=(10, 5))
sns.barplot(x=category_counts.index, y=category_counts.values, palette="viridis")

plt.xlabel("Category")
plt.ylabel("Count")
plt.title("Occurrences of Each Category")
plt.xticks(rotation=45)  # Rotate labels if necessary
plt.show()
