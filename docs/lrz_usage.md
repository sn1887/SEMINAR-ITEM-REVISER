# LRZ Usage Notes

This repository is designed to run both locally and on LRZ.

## Personal storage

Use your personal LRZ storage for code, virtual environments, and outputs.

Example:

```bash
cd /dss/dsshome1/01/<username>/
git clone <repo-url> seminar-item-reviser
```

## Shared model storage

The model path is intentionally not hard-coded. Pass the model path through Hydra:

```bash
python scripts/evaluate.py \
  model=hf_local \
  model.model_path=/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/<MODEL_NAME>
```

## Interactive test

Request a GPU and run a short local-model evaluation first:

```bash
python scripts/evaluate.py \
  model=hf_local \
  model.model_path=/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/<MODEL_NAME> \
  experiment.max_items=5
```

## SLURM

The final matrix submitter is in `slurm/`.

Validate the frozen matrix before scheduling:

```bash
python scripts/validate_final_26_manifest.py validate --check-hydra
```

Print the exact `sbatch` commands without submitting:

```bash
DRY_RUN=1 slurm/submit_final_26_matrix.sh
```

## Recommended workflow

1. Run `python scripts/smoke_test.py` locally to check schema/control flow.
2. Move to LRZ.
3. Run `experiment.max_items=5` on a local model.
4. Run the full default v4 evaluation or the frozen final matrix.
5. Save outputs and copy metrics into the final report artifacts.
