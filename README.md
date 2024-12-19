Ez a repository célja olyan szövet-/szervspecifikus ChIP-Seq adatok gyűjtése és elemzése a [TFLink](https://tflink.net/) adatbázis bővítéseként, amelyek transzkripciós faktorokat és target géneket vizsgálnak a normál élettani körülményekhez leginkább közeli ("natív") szövetekben.

## 1. Adatgyűjtés
A ChIP-Seq kísérletek kiindulópontja a [ChIP-Atlas-on elérhető metaadat](https://github.com/inutano/chip-atlas/wiki#tables-summarizing-metadata-and-files) táblázata. A szűrés a BRENDA Tissue Ontology és Cellosaurus adatbázisokban található sejtvonalak segítségével, valamint kulcsszavak manuális megadásával történt. A szűrt sejtvonalak nevei és egyéb kulcsszavak a [cell_lines](https://github.com/kadan02/native_tissue_chip-seq_experiments/tree/master/cell_lines) mappában találhatóak. 

## 2. Feldolgozás

### 2.1 Kezdeti szűrés

A ChIP-Atlas experiment listájából a releváns sorok kiválasztása (hg38 genom, TF kategória).

A ChIP-Atlas-on elérhető ExperimentList.tab sorai a "hg38" és "TF and others" értékekkel rendelkező sorokra vannak szűrve ([filter_experimentList.py](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/filter_experimentList.py)) Az output: [hg38_TF_filtered_experiments_relevant_columns.tsv](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/tsv/hg38_TF_filtered_experiments_relevant_columns.tsv)

### 2.2 Szövet minőség szűrés

A nagy kihívás a betegség, génmanipuláció, gyógyszeres vagy egyéb kezeléssel végrehajtott kísérletek/sequenceing run-ok kiszűrése és a "natív" szövetkeben végrehajtottak megtartása.

 A kezdeti szövet-minőség szűrést a [filter_native_tissues.py script](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/filter_native_tissues.py) végzi:
   - A [cell_lines](https://github.com/kadan02/native_tissue_chip-seq_experiments/tree/master/cell_lines) mappában lévő fájlok tartalmazzák azokat a kulcsszavakat, amelyek ki vannak szűrve az adott oszlopokból. A sejtvonalak nevei a [BRENDA Tissue Ontology](https://www.ebi.ac.uk/ols4/ontologies/bto)-ról és a https://www.cellosaurus.org -ról származnak. A hg38_added_cell_lines.txt és mm10_added_cell_lines.txt fájlokban található sejtvonalak manuálisan lettek összegyűjtve az alapján, hogy a kezdeti szűrés után mely sejtvonalak nem voltak szűrve. 
   - A kulturált sejtvonalak nevein kívül a további kulcsszavak a [keywords.txt](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/cell_lines/keywords.txt) fájlban találhatóak.
  
Lényegében a következő [oszlopokra](https://github.com/inutano/chip-atlas/wiki#tables-summarizing-metadata-and-files) történt a szűrés:
- Track type
    - Szűrve: "GFP", "Epitope tags"
- Cell type class
    - Szűrve: "Placenta", "Embryo", "Pluripotent stem cell", "No description"
- Cell type 
    - Szűrve: embrionális, beteg és kulturált sejtvonalak nevei. Lásd cell_lines mappát.

A sejt/szövet-minőségi szűrés eredményei a [hg38_native_experiments.tsv](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/tsv/hg38_native_experiments.tsv) fájlban találhatóak.

### 2.3 BED fájlok

A "Cell type class"-onkénti nagyobb (minden TF-et és Cell type-ot tartalmazó) BED fájlok a [ChIP-Atlas Peak Browser](https://chip-atlas.org/peak_browser)-en felületén keresztül lettek letöltve. A cél csak azoknak a kísérleteknek a kiválasztása, amelyek megfelelnek a natív szűrés kritériumainak a [hg38_native_experiments.tsv](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/tsv/hg38_native_experiments.tsv) alapján. A [filter_bed_single_run.py](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/filter_bed_single_run.py) szűri ki azokat az Experiment ID-vel rendelkező sorokat ebből a bed fájlból, amelyek a [hg38_native_experiments.tsv](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/tsv/hg38_native_experiments.tsv)-ben megtalálhatóak. Egy könyvtárrendszert hoz létre a szövet kategóriáknak (Cell type class) megfelelően, és a filtered_SZÖVETNÉV_.bed fájlokba kerül az output.

### 2.4 Peak - promoter overlapping
A csak natív-szövetekre szűrt BED fájlok és a hg38 genom promóterjeit tartalmazó hg38promoters.bed fájl a BEDTools csomag segítségével van feldolgozva.
A tüdő példájával:
```
bedtools intersect -a hg38promoters.bed -b Lng/filtered_Lng.bed -wa -wb > Lng/intersected_Lng.bed
```
Az [intersect_beds.sh](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/intersect_beds.sh) minden bed/ alatt található almappába elhelyezett filtered_${tissue_name}.bed (filter_bed.py-al létrehozott) fájlt feldolgoz ilyen módon automatikusan.

A feldolgozott BED fájlok a [releases](https://github.com/kadan02/native_tissue_chip-seq_experiments/releases) linkről tölthetőek le.

### 2.5 Kötőhely szekvenciák

[all_tissue_bedtools_to_fasta.sh](https://github.com/kadan02/NativeTissueChIP/blob/master/all_tissue_bedtools_to_fasta.sh) - Szintén minden bed/ alatt található almappába elhelyezett intersected_${tissue_name}.bed fájl koordinátáiból előállítja a transzkripciós faktor kötőhely szekvenciáit a fasta mappába.

### 2.6 ID Mapping
 Az [extract_gene_names.py](https://github.com/kadan02/NativeTissueChIP/blob/master/extract_gene_names.py) az intersected_TISSUE_NAME.bed fájlokból előállít szövetenként egy .txt fájlt, amelyek csak a Transzkripciós faktor - Target gén interakciók génneveit tartalmazzák. Készít egy [másik txt fájlt](https://github.com/kadan02/NativeTissueChIP/blob/master/interactions/combined_gene_names.txt) is, amely minden egyedi génnevet tartalmaz az összes bed fájlból. 

Az ID mappelés a [Uniprot 'ID Mapping' tool-jával]((https://www.uniprot.org/id-mapping)) történt. A bemeneti adatok a [combined_gene_names.txt](https://github.com/kadan02/NativeTissueChIP/blob/master/interactions/combined_gene_names.txt) sorai, az alábbi beállításokkal:

Bemeneti beállítások:
   - From database: Gene Name 
   - To database: UniProtKB 
   - Restrict by organism: Homo sapiens, etc.

Letöltés beállítások:
   - Format: TSV
   - Columns: GeneID, Reviewed

### 2.7 Interakciós table előállítása
[create_interaction_table.py](https://github.com/kadan02/NativeTissueChIP/blob/master/interactions/create_interaction_table.py) - Minden egyedi transzkripciós faktor - target gén interakció megfelelő adatait az [interactions/output_interaction_tables](https://github.com/kadan02/NativeTissueChIP/tree/master/interactions/output_interaction_tables) tsv fájljaiba írja szövetenként.

## 3. Statisztikák
Az átszűrt humán adatok:
- Összes SRA Experiment: 3090
- Egyedi TF-ek: 317
- Különböző sejtcsoport kategóriák: 190

A szűrésen nem humán átjutott adatok:
- Összes SRA Experiment: 30076
- Egyedi TF-ek: 1819
- Különböző sejtcsoport kategóriák: 1034


![](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/figures/figure_tf.png)
![](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/figures/figure_cell_type_class.png)
![](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/figures/figure_cell_type.png)

## 4. Credits
This project was made possible using data from [ChIP-Atlas](https://chip-atlas.org).

1. Zou, Z., Ohta, T., Oki, S. ChIP-Atlas 3.0: a data-mining suite to explore chromosome architecture together with large-scale regulome data. Nucleic Acids Res. 52(W1), W45-W53, 2024. [http://dx.doi.org/10.1093/nar/gkae358](http://dx.doi.org/10.1093/nar/gkae358)
2. Zou, Z., Ohta, T., Miura, F., Oki, S. ChIP-Atlas 2021 update: a data-mining suite for exploring epigenomic landscapes by fully integrating ChIP-seq, ATAC-seq and Bisulfite-seq data. Nucleic Acids Res. 50(W1), W175-W182, 2022. [http://dx.doi.org/10.1093/nar/gkac199](http://dx.doi.org/10.1093/nar/gkac199)
3. Oki, S., Ohta, T., Shioi, G., Hatanaka, H., Ogasawara, O., Okuda, Y., Kawaji, H., Nakaki, R., Sese, J., Meno, C. ChIP-Atlas: a data-mining suite powered by full integration of public ChIP-seq data. EMBO Rep. 19(12), e46255, 2018. [http://dx.doi.org/10.15252/embr.201846255](http://dx.doi.org/10.15252/embr.201846255)
4. Web Tool: Oki, S; Ohta, T (2015): ChIP-Atlas. [https://chip-atlas.org](https://chip-atlas.org)
