Minden egyes mappa egy osztályozási futtás adatait tartalmazza. 

A mappákban található fájlok:
- classification_run.log: Részletes logging a script futása során.
- classification_summary.csv: Egy átlátható összegzés az osztályozás eredményeiről. Az LLM által megadott "okok" is itt találhatóak.
- llm_responses.log: Az LLM válaszai a script futtatása során.
- native_classified.tsv: Az eredeti metaadat táblázat, de csak a szűrés közben natívnak megítélt ID-vel rendelkező sorokkal.
- non_native_classified.tsv: Az eredeti metaadat táblázat, de csak a szűrés közben nem-natívnak megítélt ID-vel rendelkező sorokkal.
