### A táblázatok értékei
A fájlokban minden sor 1-1 szekvenálás adatait tartalmazza. Kísérletenként lehet több szekvenálás is.

[Az oszlopok részletes leírása](https://github.com/inutano/chip-atlas/wiki#tables-summarizing-metadata-and-files). Az eredeti táblázatból a 2. és 3. oszlopok törölve vannak a kisebb méret érdekében. 

A fájlokban a 7. oszlopig ("Title") standardizáltak az adatok, a további oszlopokban a kutatók által megadott metaadatok szerepelnek. A kísérletek között változó számú, hogy hány metaadat érték (oszlop) van.

### Fájlok leírása
- *MODELORGANISM*_**TF_filtered_experiments_relevant_columns** fájlok -  Minden kísérletet tartalmaznak, ami releváns lehet.
- *MODELORGANISM*_**native_experiments.tsv** - A kezdeti szűrésen átjutott kísérletek.
- *MODELORGANISM*_**removed_experiments.tsv** - A kezdeti szűrésen át nem jutott kísérletek.
