import csv
import os


def preprocess_bed(input_file, output_file):
    """
     Probléma: A promóteres bed fájlból származóan a target gén oszlopban néhány helyen több génnév is
     van, vagy csak ENSG ID van, de génnév nincsen hozzá. Ilyenkor pl így néz ki a target gén oszlopban az érték: ,IPO13
     Ezzel a scripttel csak azokat az értékeket hagyom meg, amelyeknél rendes génnevek is vannak (tehát a fenti pl csak IPO13 lesz)
     és ilyen esetben külön sorba írom őket.

     Tehát pl AIRIM,CDCA8 esetén így fog kinézni az output:
     CTCF	AIRIM
     CTCF	CDCA8
     """

    unique_interactions = set()     # csak az egyedi tf-tg interakciók lesznek tárolva

    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter='\t')

        for row in csv.reader(infile, delimiter='\t'):
            tf = row[4]
            target_genes = row[8]
            target_genes = target_genes.strip(',')

            # Vessző szerint split és ha ven üres string akkor azt töröljük
            target_genes_list = [target_gene.strip() for target_gene in target_genes.split(',') if target_gene.strip()]

            for target_gene in target_genes_list:
                interaction = (tf, target_gene)
                unique_interactions.add(interaction)

        for tf, target_gene in unique_interactions:
            writer.writerow([tf, target_gene])


def combine_unique_gene_names(output_dir, combined_file):
    """
    A generált interakciós listákból csinál egy csak csak egyedi génneveketem tartalmazó fájlt
    Ok: a UniProt toollal való használatra https://www.uniprot.org/id-mapping
    """
    unique_genes = set()

    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.startswith("tf-target_list_") and file.endswith(".txt"):
                interaction_file = os.path.join(root, file)
                with open(interaction_file, 'r') as infile:
                    for line in infile:
                        print(line)
                        tf_gene, target_gene = line.strip().split('\t')
                        unique_genes.add(tf_gene)
                        unique_genes.add(target_gene)

    with open(combined_file, 'w') as outfile:
        outfile.write('\n'.join(sorted(unique_genes)))


def process_all_beds(input_dir, output_dir, combined_file):

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Bed fájlok processzálása
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.startswith('intersected_') and file.endswith('.bed'):
                tissue_name = file.replace('intersected_', '').replace('.bed', '')
                input_file = os.path.join(root, file)
                output_file = os.path.join(output_dir, f"tf-target_list_{tissue_name}.txt")

                print(f"Processing {input_file} -> {output_file}")
                preprocess_bed(input_file, output_file)

    combine_unique_gene_names(output_dir, combined_file)


input_bed_folder = "bed"
output_interactions_folder = "interactions/tf_target_lists"
combined_genes_file = "interactions/combined_gene_names.txt"
process_all_beds(input_bed_folder, output_interactions_folder, combined_genes_file)

