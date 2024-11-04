import pandas as pd
import matplotlib.pyplot as plt
from numpy.ma.extras import unique

data_filtered = pd.read_csv('tsv/hg38_native_experiments.tsv', sep='\t')
data_removed = pd.read_csv('tsv/hg38_removed_experiments.tsv', sep='\t')
generate = input(' TF: 1\nCell type class: 2 \nCell type: 3\n')
column = data_filtered[generate]
counts = column.value_counts()
counts_top50 = counts.head(50)

s = ''
if generate == '1':
    s = 'Transcription factor'
elif generate == '2':
    s = 'Cell type class'
elif generate == '3':
    s = 'Cell type'

# 3. TF oszlopdiagram
plt.figure(figsize=(16, 9))
bars = plt.bar(counts_top50.index, counts_top50.values)
plt.title('Top 50 ' + s + ' in native-tissue ChIP-Seq experiments with transcription factor targets')
plt.xlabel('Transcription factor')
plt.ylabel('SRX ID count')
plt.xticks(rotation=45, ha='right')

# y értékek az oszlopokon
for bar in bars:
    y_val = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, y_val, int(y_val), ha='center', va='bottom')

plt.tight_layout()
plt.show()

# egyéb statisztikák
unique_filtered_tfs = data_filtered['1'].nunique()
unique_removed_tfs = data_removed['1'].nunique()
unique_filtered_cell_types = data_filtered['3'].nunique()
unique_removed_cell_types = data_removed['3'].nunique()
with open('figures/stats.txt', 'w', encoding='utf-8') as f:
    f.write("Egyedi szűrt TF-ek: " + str(unique_filtered_tfs) + "\nEgyedi törölt TF-ek: " + str(unique_removed_tfs) +
            "\nKülönböző sejtcsoport kategóriák: " + str(unique_filtered_cell_types) +
            "\nTörölt különböző sejtcsoport kategóriák:" + str(unique_removed_cell_types))
