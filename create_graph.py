import pandas as pd
import matplotlib.pyplot as plt
from numpy.ma.extras import unique

# data_removed = pd.read_csv('tsv/removed_chip_atlas_experiments_with_keyword.csv')
data_filtered = pd.read_csv('tsv/hg38_native_experiments.tsv')
data_removed = pd.read_csv('tsv/removed_chip_atlas_experiments.csv')
tf_column = data_filtered['Cell type class']
tf_counts = tf_column.value_counts()
tf_counts_top50 = tf_counts.head(50)


# oszlopdiagram

plt.figure(figsize=(16, 9))
bars = plt.bar(tf_counts_top50.index, tf_counts_top50.values)
plt.title('Top 50 "Cell type class" in native-tissue ChIP-Seq experiments with transcription factor targets')
plt.xlabel('Cell type class')
plt.ylabel('SRX ID count')
plt.xticks(rotation=45, ha='right')

# y értékek az oszlopokon
for bar in bars:
    y_val = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, y_val, int(y_val), ha='center', va='bottom')

plt.tight_layout()
plt.show()


# egyéb statisztikák
unique_filtered_tfs = data_filtered['Track type'].nunique()
unique_removed_tfs = data_removed['Track type'].nunique()
with open('tsv/stats.txt', 'w', encoding='utf-8') as f:
    f.write("Egyedi szűrt TF-ek: " + str(unique_filtered_tfs) + "\nEgyedi törölt TF-ek: " + str(unique_removed_tfs))
