with open('tsv/ExperimentList.tab', 'r', encoding='utf-8') as infile, open(
        'tsv/hg38_TF_filtered_experiments_relevant_columns.tsv', 'w', encoding='utf-8') as outfile:
    for line in infile:
        columns = line.strip().split('\t')
        genome_assembly = columns[1]
        track_type = columns[2]

        if genome_assembly == 'hg38' and track_type == 'TFs and others':
            # a szűrésen végigment 2 oszlopot nem írjuk az output-ba
            filtered_columns = [columns[i] for i in range(len(columns)) if i not in (1, 2)]
            outfile.write('\t'.join(filtered_columns) + '\n')