import pandas as pd
import csv
import re


csv_path = 'sra/liver/SraRunTable - less columns.csv'
data = pd.read_csv(csv_path, sep='\t')

cell_line_list = 'cell_lines/homo_sapiens_cell_line.txt'
chip_atlas_cell_line_list = 'cell_lines/chip_atlas_added_cell_lines.txt'

with open(cell_line_list, 'r') as f:
    cell_lines = [line.strip() for line in f.readlines()]
with open(chip_atlas_cell_line_list, 'r') as f:
    chip_atlas_cell_lines = [line.strip() for line in f.readlines()]

filter_out = (["cancer", "carcinoma", "tumor", "tumour", "infection", "hepatitis", "Embryo", "fetal", "fetus", "organoid", "organoids",
              "knockout", "adenocarcinoma","KO", "overexpression", "H3K4me3", "H3K27me3", "H3K27Ac", "H3K36me3", "H3K4me2", "H3K9ac", "H3K4me1",
              "H3-ChIP", "H3K9me3", "K27ac", "K27me3", "K4me1", "K4me3", 'RNAP2', "PolIII", "polyclonal", 'input', 'input_dna', 'xenograph']
              + cell_lines + chip_atlas_cell_lines)
escaped_filter_out = [r'\b' + re.escape(term) + r'\b' for term in filter_out]

mask = data.apply(lambda row: row.str.contains('|'.join(escaped_filter_out), case=False, na=False).any(), axis=1)

filtered_data = data[~mask]
filtered_output_file = 'sra/liver/filtered_sra_experiments.csv'
filtered_data.to_csv(filtered_output_file, index=False, sep='\t', quoting=csv.QUOTE_NONE, escapechar='\\')

removed_data = data[mask]
removed_output_file = 'sra/liver/removed_sra_experiments.csv'
removed_data.to_csv(removed_output_file, index=False, sep='\t', quoting=csv.QUOTE_NONE, escapechar='\\')
