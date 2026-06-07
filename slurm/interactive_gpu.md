# Interactive GPU Session

Example:

```bash
salloc -p lrz-hgx-h100-94x4 --time=0-2:00:00 --gres=gpu:1
srun --pty bash
```

Then run:

```bash
python scripts/evaluate.py experiment.max_items=5 model=hf_local model.model_path=/path/to/model
```
