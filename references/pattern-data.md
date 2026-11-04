# Pattern: data processing / scripts

Signals: many standalone scripts, `notebooks/`, `*.ipynb`, `data/`, `input/`/`output/`, scheduled-job config; usually no test directory.

- **Q1**: write the architecture doc as a data flow: where input comes from → what each script does → where output goes; list the order in which scripts run.
- **Q2**: often no automated tests; per Occam's razor, don't force them. The minimal viable verification is usually: run on a sample input and compare with the expected output (or check row counts / column names / key statistics). If it cannot be automated, write the manual steps in "Definition of done".
- **Q3**: the data dictionary (field meanings, sources, refresh frequency) is the most important knowledge in such projects; put it in the design or references role.
- **Q4**: common key rules — never overwrite raw data, never commit large or sensitive data files, no hard-coded paths.
- **Q6**: focus on whether field names and file paths in docs still match the scripts.
