#!/bin/bash

for tissue_dir in "../data/processed/bed"/*/; do
    tissue_name=$(basename "$tissue_dir")
    input_file="$tissue_dir/filtered_${tissue_name}.bed"
    output_file="$tissue_dir/intersected_${tissue_name}.bed"
    bedtools intersect -a "$input_file" -b "../data/raw/bed/hg38promoters.bed" -wa -wb > "$output_file"
done
