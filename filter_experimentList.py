with open('chip_atlas/metadataExperimentList.tab', 'r', encoding='utf-8') as infile, open('chip_atlas/hg38_TF_filtered_experiments_all_columns.csv', 'w', encoding='utf-8') as outfile:
    for line in infile:
        columns = line.strip().split('\t')
        genome_assembly = columns[1]
        track_type = columns[2]

        if genome_assembly == 'hg38' and track_type == 'TFs and others':
            outfile.write(','.join(columns) + '\n')
