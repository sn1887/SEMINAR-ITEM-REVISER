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

Use the mock backend first:

```bash
python scripts/evaluate.py model=mock experiment.max_items=5
```

Only after this works, request a GPU and try a local model.

## SLURM

Templates are in `slurm/`.

For a CPU smoke test:

```bash
sbatch slurm/eval_cpu_mock.sbatch
```

For a GPU Hugging Face model test, edit `slurm/eval_gpu_hf.sbatch` and set the model path.

## Recommended workflow

1. Develop locally with `model=mock`.
2. Run full 200-item mock evaluation.
3. Move to LRZ.
4. Run `experiment.max_items=5` on a local model.
5. Run the full 200-item evaluation.
6. Save outputs and copy metrics into your meeting protocol.
