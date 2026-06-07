#!/bin/bash
#SBATCH --job-name=item-reviser-mock
#SBATCH --time=00:20:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --output=logs/item_reviser_mock_%j.out
#SBATCH --error=logs/item_reviser_mock_%j.err

set -euo pipefail
mkdir -p logs

source ~/.bashrc || true
# source ~/miniconda3/etc/profile.d/conda.sh
# conda activate item-reviser

python scripts/evaluate.py experiment=item_reviser_eval model=mock
