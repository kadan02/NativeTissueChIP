Ez a repository célja olyan szövet-/szervspecifikus ChIP-Seq kísérletek összegyűjtése és elemzése (work in progress) a TFLink adatbázis bővítéseként, amelyek transzkripciós faktorokat vizsgálnak natív (nem kulturált és betegséggel, vagy egyéb génmanipulációval nem rendelkező) sejtekben.

## 1. Adatgyűjtés
A kísérletek adatai a [ChIP-Atlas-on elérhető metaadat](https://github.com/inutano/chip-atlas/wiki#downloads_doc) táblázatából lettek szűrve. A szűrés a BRENDA Tissue Ontology-n található sejtvonalak segítségével, valamint kulcsszavak manuális megadásával történt. A szűrt sejtvonalak nevei a [cell_lines](https://github.com/kadan02/native_tissue_chip-seq_experiments/tree/master/cell_lines) mappában találhatóak. 

### A csak natív kísérleteket tartalmazó CSV táblázat [itt](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/chip_atlas/native_chip_atlas_experiments.csv) található.

## 2. Feldolgozás


## Statisztikák
Az átszűrt adatok:
- Összes SRA Experiment: 3115
- Egyedi TF-ek: 319

A szűrésen nem átjutott adatok:
- Összes SRA Experiment: 29841
- Egyedi TF-ek: 1813

![](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/chip_atlas/figures/figure_tf.png)
![](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/chip_atlas/figures/figure_cell_type_class.png)
![](https://github.com/kadan02/native_tissue_chip-seq_experiments/blob/master/chip_atlas/figures/figure_cell_type.png)
