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

Templates are in `slurm/`.

For a GPU Hugging Face model test, edit `slurm/eval_gpu_hf.sbatch` and set the model path.

## Recommended workflow

1. Run `python scripts/smoke_test.py` locally to check schema/control flow.
2. Move to LRZ.
3. Run `experiment.max_items=5` on a local model.
4. Run the full 200-item evaluation.
5. Save outputs and copy metrics into your meeting protocol.
