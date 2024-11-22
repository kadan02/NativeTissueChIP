import pandas as pd
import os

# tizedesvesszők eltvávolítása, ha csak 1 db Gene ID tartozik a tf/target génhez
def clean_gene_id(gene_id_str):

    if pd.isna(gene_id_str):
        return ""
    gene_ids = gene_id_str.split(";")
    gene_ids = [gid for gid in gene_ids if gid.strip()]
    return ";".join(gene_ids)


# Gene name alapján csoportosítás, majd reviewed UniProt ID-k priorizálása. Ha nincsen reviewed, akkor az első unreviewed
def get_priority_uniprot_ids(mapping_table):
    reviewed = mapping_table[mapping_table["Reviewed"] == "reviewed"]
    unreviewed = mapping_table[mapping_table["Reviewed"] == "unreviewed"]

    prioritized_uniprot = (
        pd.concat([reviewed, unreviewed])
        .drop_duplicates(subset=["From"], keep="first")
        .reset_index(drop=True)
    )
    return prioritized_uniprot

uniprot_mapping_table = pd.read_csv('mapped_ids.tsv', sep="\t", names=["From", "Entry", "GeneID", "Reviewed"])
input_folder = 'tf_target_lists'
prioritized_mapping = get_priority_uniprot_ids(uniprot_mapping_table)

# tf_target_lists mappában lévő fájlokon iterálás, mapping table-ök szövetenkénti létrehozása
for file_name in os.listdir(input_folder):
    if file_name.endswith(".txt"):
        tissue_name = file_name.replace("tf-target_list_", "").replace(".txt", "")
        interaction_list = pd.read_csv(
            os.path.join(input_folder, file_name),
            sep="\t",
            header=None,
            names=["TF_name", "Target_name"]
        )

    # gén nevek match-elése az ID-kkel
    tf_info = interaction_list.merge(prioritized_mapping, left_on="TF_name", right_on="From", how="left", suffixes=("_TF", "_TG"))
    tg_info = interaction_list.merge(prioritized_mapping, left_on="Target_name", right_on="From", how="left", suffixes=("_TF", "_TG"))

    # Redundáns ; karakterek eltávolítása
    tf_info["GeneID"] = tf_info["GeneID"].apply(clean_gene_id)
    tg_info["GeneID"] = tg_info["GeneID"].apply(clean_gene_id)

    output = pd.DataFrame({
        "UniprotID.TF": tf_info['Entry'],
        "UniprotID.Target": tg_info['Entry'],
        "NCBI.GeneID.TF": tf_info['GeneID'],
        "NCBI.GeneID.Target": tg_info['GeneID'],
        "Name.TF": tf_info['TF_name'],
        "Name.Target": tg_info['Target_name'],
        "Detection.method": "chromatin immunoprecipitation assay",
        "PubmedID": "38749504",
        "Organism": "Homo sapiens",
        "Source.database": "Chip-Atlas",
        "Small-scale.evidence": "-",
        "TF.TFLink.ortho": "-",
        "TF.nonTFLink.ortho": "-",
        "Target.TFLink.ortho": "-",

    })


    # nem fehérjekódoló target géneket (amelyek nem rendelkeznek uniprot ID-kkel) tartalmazó sorok kihagyása
    output = output.dropna(subset=["UniprotID.Target"])

    output_file = 'output_interaction_tables/'f'interaction_table_{tissue_name}.tsv'
    output.to_csv(output_file, sep="\t", index=False)
