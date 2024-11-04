Ez a repository célja olyan szövet-/szervspecifikus ChIP-Seq kísérletek összegyűjtése és elemzése (work in progress) a TFLink adatbázis bővítéseként, amelyek transzkripciós faktorokat vizsgálnak natív (nem kulturált és betegséggel, vagy egyéb génmanipulációval nem rendelkező) sejtekben. Egyelőre csak humán adatok állnak rendelkezésre.

## 1. Adatgyűjtés
A kísérletek adatai a [ChIP-Atlas-on elérhető metaadat](https://github.com/inutano/chip-atlas/wiki#tables-summarizing-metadata-and-files) táblázatából lettek szűrve. A szűrés a BRENDA Tissue Ontology-n található sejtvonalak segítségével, valamint kulcsszavak manuális megadásával történt. A szűrt sejtvonalak nevei a [cell_lines](https://github.com/kadan02/native_tissue_chip-seq_experiments/tree/master/cell_lines) mappában találhatóak. 

## 2. Feldolgozás
1. A ChIP-Atlas-ról elérhető ExperimentList.tab a [filter_experimentList.py](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/filter_experimentList.py)-al van szűrve a "hg38" és "TF and others" értékekkel rendelkező sorokra. Az output: [hg38_TF_filtered_experiments_relevant_columns.tsv](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/tsv/hg38_TF_filtered_experiments_relevant_columns.tsv)
 
2. A további szövet-minőség szűrést a [filter_native_tissues.py script](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/filter_native_tissues.py) végzi:
   - A [cell_lines](https://github.com/kadan02/native_tissue_chip-seq_experiments/tree/master/cell_lines) mappában lévő cell_line_list_all_no_duplicates.txt tartalmazza a [BRENDA Tissue Ontology-n](https://www.ebi.ac.uk/ols4/ontologies/bto) található sejtvonalak neveit, a chip_atlas_added_cell_lines.txt pedig azokat, amelyek manuálisan lettek összegyűjtve az alapján, hogy a cell_line_list_all_no_duplicates.txt-vel történő szűrés után mely sejtvonalak nem voltak szűrve. 
   - A kulturált sejtvonalak nevein kívül a további kulcsszavak a [keywords.txt](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/cell_lines/keywords.txt) fájlban találhatóak.
  
   Lényegében a következő [oszlopokra](https://github.com/inutano/chip-atlas/wiki#tables-summarizing-metadata-and-files) történt a szűrés:
    - Cell type (embrionális, betegséggel rendelkező és valamilyen mesterséges sejtvonal névvel ellátott sorok)
    - Track type (GFP, Epitope tags)
    - Cell type class (Placenta, Gonad, Embryo, Pluripotent stem cell, No description)

- A sejt/szövet-minőségi szűrés eredményei a [hg38_native_experiments.tsv](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/tsv/hg38_native_experiments.tsv) fájlban találhatóak.

4. A "Cell type class"-onkénti nagyobb (minden TF-et és Cell type-ot tartalmazó) BED fájlok a [ChIP-Atlas Peak Browser](https://chip-atlas.org/peak_browser)-en keresztül lettek letöltve. A [filter_bed.py](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/filter_bed.py) script szűri ki azokat az Experiment ID-vel rendelkező sorokat, amelyek a [hg38_native_experiments.tsv](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/tsv/hg38_native_experiments.tsv)-ben megtalálhatóak.

5. A csak natív-sejtekre szűrt BED fájlok és a hg38 genom promóterjeit tartalmazó hg38promoters.bed fájl a BEDTools csomag segítségével van feldolgozva.
  - A tüdő példájával:
```
bedtools intersect -a hg38promoters.bed -b Lng/filtered_Lng.bed -wa -wb > Lng/intersected_Lng.bed
```
Az intersect_beds.sh minden bed/ alatt található almappába elhelyezett filtered_${tissue_name}.bed (filter_bed.py-al létrehozott) fájlt feldolgoz ilyen módon automatikusan.

A feldolgozott BED fájlok a [releases](https://github.com/kadan02/native_tissue_chip-seq_experiments/releases) linkről tölthetőek le.

## 3. Statisztikák
Az átszűrt adatok:
- Összes SRA Experiment: 3090
- Egyedi TF-ek: 317
- Különböző sejtcsoport kategóriák: 190

A szűrésen nem átjutott adatok:
- Összes SRA Experiment: 30076
- Egyedi TF-ek: 1819
- Különböző sejtcsoport kategóriák: 1034


![](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/figures/figure_tf.png)
![](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/figures/figure_cell_type_class.png)
![](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/figures/figure_cell_type.png)
