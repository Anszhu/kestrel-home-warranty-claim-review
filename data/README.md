# data/ - PRIVATE Kestrel input files

This folder is git-ignored (except this note). Kestrel data is confidential: never publish it,
upload it to a public repository, or share it beyond the engagement team.

Required private files (exact names):

- `train.csv`
- `test_unlabelled.csv`
- `partners.csv`
- `products.csv`
- `sample_submission.csv` (optional; used to check the output shape)

You may also keep `ops-policy.pdf`, `email-thread.txt` and the data pack `README.txt` here for reference.
They are ignored by git and excluded from the project ZIP.

Without these files the Streamlit app and API still start and can score a single claim from the bundled
`src/model_config.json`; training, validation and the review queue need the files.

`products.csv` is part of the data pack but is not used by the current score. `train.csv` + `partners.csv` are needed for `src.train` and `src.validate`; `test_unlabelled.csv` (and ideally `sample_submission.csv`) for `src.predict`.
