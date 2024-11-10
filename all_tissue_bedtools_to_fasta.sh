#!/bin/bash

# wget ftp://ftp.ensembl.org/pub/current_fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz

for tissue_dir in "bed"/*/; do
    tissue_name=$(basename "$tissue_dir")
    input_file="$tissue_dir/intersected_${tissue_name}.bed"
    output_file="fasta/bindingSites_${tissue_name}.fasta"
    bedtools getfasta -fi "fasta/Homo_sapiens.GRCh38.dna.primary_assembly.fa" -bed "$input_file" -name -fo "$output_file"
done