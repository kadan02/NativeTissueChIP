Ez a repository célja olyan szövet-/szervspecifikus ChIP-Seq kísérletek összegyűjtése és elemzése (work in progress) a TFLink adatbázis bővítéseként, amelyek transzkripciós faktorokat vizsgálnak natív (nem kulturált és betegséggel, vagy egyéb génmanipulációval nem rendelkező) sejtekben.

## 1. Adatgyűjtés
A kísérletek adatai a [ChIP-Atlas-on elérhető metaadat](https://github.com/inutano/chip-atlas/wiki#downloads_doc) táblázatából lettek szűrve. A szűrés a BRENDA Tissue Ontology-n található sejtvonalak segítségével, valamint kulcsszavak manuális megadásával történt. A szűrt sejtvonalak nevei a [cell_lines](https://github.com/kadan02/native_tissue_chip-seq_experiments/tree/master/cell_lines) mappában találhatóak. 

### A csak natív kísérleteket tartalmazó CSV táblázat [itt](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/chip_atlas/native_chip_atlas_experiments.csv) található.

## 2. Feldolgozás
- A ChIP-Atlas-ról elérhető ExperimentList.tab a filter_experimentList.py-al van szűrve a "hg38" és "TF and others" értékekkel rendelkező sorokra. Az output: hg38_TF_filtered_experiments_all_columns.csv
- 
- További szövet-minőség szűrést a filter_chip_atlas_experiment_table.py script végez:
 - A cell_lines mappában lévő cell_line_list_all_no_duplicates.txt tartalmazza a BRENDA Tissue Ontology-n található sejtvonalak neveit, a chip_atlas_added_cell_lines.txt pedig azokat, amelyek manuálisan lettek összegyűjtve az alapján, hogy a cell_line_list_all_no_duplicates.txt-vel történű szűrés után mely sejtvonalak nem voltak szűrve.
 - A sejtvonalakon kívül a további kulcsszavak az alábbiak voltak:
```
'tumor', 'tumors', 'tumours', 'tumour', 'cancer', 'Neoplasm', 'Neoplasms', 'Sarcoma', 'Liposarcoma', 'Fibrosarcoma','leukemia','adenocarcinoma','glioma', 'lymphoma', 'melanoma', 'Rhabdomyosarcoma', 'Polycystic', 'leiomyoma', 'myeloma', 'organoid', 'organoids', 'Unclassified', 'carcinoma', 'Neurofibromatosis', 'Aneurysm','Fetal', 'Fetus', 'Embryo', 'Neural crest','hESC', 'hESCs', 'iPSC', 'iPS', 'xenograft', 'iTreg', 'iSLK','Trophoblast stem cells'
```






## 3. Statisztikák
Az átszűrt adatok:
- Összes SRA Experiment: 3115
- Egyedi TF-ek: 319

A szűrésen nem átjutott adatok:
- Összes SRA Experiment: 29841
- Egyedi TF-ek: 1813

![](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/chip_atlas/figures/figure_tf.png)
![](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/chip_atlas/figures/figure_cell_type_class.png)
![](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/chip_atlas/figures/figure_cell_type.png)
