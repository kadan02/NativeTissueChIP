### A táblázatok értékei
A fájlokban minden sor 1-1 szekvenálás metaadatait tartalmazza. Kísérletenként lehet több szekvenálás is.

[Az oszlopok részletes leírása](https://github.com/inutano/chip-atlas/wiki#tables-summarizing-metadata-and-files). A 4. oszlopig standardizáltak az adatok, a további oszlopokban a kutatók által megadott metaadatok szerepelnek. Az eredeti táblázatból (lásd az utóbbi linket) a következő oszlopok törölve vannak: 2 3 8 9. A metaadatok közül a nem releváns értékek (nem a minta/kísérlet minőségére utalóak) is törölve vannak. 


### Fájlok leírása
- *MODELORGANISM*_**TF_filtered_experiments_relevant_columns** fájlok -  Minden kísérletet tartalmaznak, ami releváns lehet.
- *MODELORGANISM*_**native_runs.tsv** - A kezdeti szűrésen átjutott kísérletek.
- *MODELORGANISM*_**removed_runs.tsv** - A kezdeti szűrésen át nem jutott kísérletek.
