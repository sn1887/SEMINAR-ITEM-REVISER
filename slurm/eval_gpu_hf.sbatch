#!/bin/bash
#SBATCH --job-name=item-reviser-hf
#SBATCH --partition=lrz-hgx-h100-94x4
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=40G
#SBATCH --output=logs/item_reviser_hf_%j.out
#SBATCH --error=logs/item_reviser_hf_%j.err

set -euo pipefail
mkdir -p logs

source ~/.bashrc || true
# source ~/miniconda3/etc/profile.d/conda.sh
# conda activate item-reviser

MODEL_PATH="/dss/dssmcmlfs01/pn25ju/pn25ju-dss-0000/models/CHANGE_ME"

python scripts/evaluate.py \
  experiment=item_reviser_eval \
  model=hf_local \
  model.model_path="$MODEL_PATH"
