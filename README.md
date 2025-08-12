# HAFix: History-Augmented Large Language Models for Bug Fixing

[![Paper](https://img.shields.io/badge/Paper-arXiv:2501.09135-red)](https://arxiv.org/abs/2501.09135)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 📖 About

This repository contains the implementation and evaluation framework for HAFix, a novel approach to improve Large Language Models' performance on automated bug fixing by incorporating historical information from software repositories.

### Authors
- Yu Shi, Abdul Ali Bangash, Emad Fallahzadeh, Bram Adams, Ahmed E. Hassan
- [Lab on Maintenance, Construction and Intelligence of Software (MCIS)](https://mcis.cs.queensu.ca)
- [Software Analysis and Intelligence Lab (SAIL)](https://sail.cs.queensu.ca)
- School of Computing, Queen's University, Canada

## 🏗️ Repository Structure

```
📁 HAFix/
├── 📁 dataset/              # Dataset collection and processing
│   ├── 📁 bugsinpy/         # BugsInPy dataset processing
│   └── 📁 defects4j/        # Defects4J dataset processing
├── 📁 model_inference/      # LLM inference and prompt construction
├── 📁 evaluation/           # Model evaluation framework
├── 📁 analysis/             # Result analysis and visualization (RQ1-3)
├── 📄 Dockerfile           # Docker environment setup
├── 📄 env_setup.sh         # Environment setup script
└── 📄 README.md            # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker (for evaluation environments)
- CUDA-compatible GPU (recommended)

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/SAILResearch/HAFix-History-Augmented-LLMs-for-Bug-Fixing.git
cd HAFix-History-Augmented-LLMs-for-Bug-Fixing

# Set up subject projects
bash env_setup.sh

# Install Python dependencies
pip install -r requirement.txt

# Set up conda environment (recommended)
conda create -n replay-env python=3.8
conda activate replay-env
pip install -r requirement.txt
```

### Dataset Preparation

Our evaluation uses two benchmark datasets:

#### BugsInPy Dataset
```bash
cd dataset/bugsinpy/src
python bugsinpy_analysis.py                # Analyze bug characteristics
python bugsinpy_meta_data_mining.py        # Extract metadata
python bugsinpy_history_mining.py          # Mine historical information
```

#### Defects4J Dataset
```bash
git clone https://github.com/rjust/defects4j.git
cd dataset/defects4j/src
python defects4j_analysis.py               # Analyze bug characteristics  
python defects4j_meta_data_mining.py       # Extract metadata
python defects4j_history_mining.py         # Mine historical information
```

## 🔧 1. Model Serving and Inference 

#### Evaluated Models
- CodeLlama-7B-Instruct
- DeepSeek-Coder-6.7B-Instruct
- DeepSeek-Coder-V2-16B-Lite-Instruct

#### Prompt Styles
- **Instruction**: Standard instruction-based prompts
- **InstructionLabel**: Prompts with labeled buggy lines
- **InstructionMask**: Infill-style prompts with masked buggy lines

#### Running Model Inference

**Start Model Serving** (using Ollama):
```bash
cd model_inference

# Start Docker containers for model
# Customizing the API port and other config in this .yml file
docker compose -f model_serving_docker_compose.yml up -d

# Monitor model status
bash monitor_model_serving_status.sh
```

**Generate Fixes**:
```bash
# Example: Run DeepSeek-Coder on BugsInPy with Instruction prompts
bash ollama_model_generate.sh \
    bugsinpy \
    deepseek-coder:6.7b-instruct-fp16 \
    Instruction \
    11430 \
    10 \
    "1 2 3 4 5 6 7 8"
```

## 🐳 2. Evaluation in Docker

**For BugsInPy:**
```bash
# Using the official docker image of BugsInPy.
```

**For Defects4J:**
```bash
cd defects4j
docker build -t defects4j .
```

#### Running Evaluations

**Single Model Evaluation:**
```bash
docker exec "[your bugsinpy container]"
python evaluate.py \
    --dataset bugsinpy \
    --model_inference_dirs "deepseek_coder_6.7b_instruct_fp16_Instruction" \
    --history_settings "1,2,3,4,5,6,7,8"
```

**Multi-Container Evaluation** (for faster processing):
```bash
# For Defects4J (parallel evaluation), customizing your config such as the number of containers, log file in config file 
bash evaluate_defects4j_multi_containers.sh
```

#### Post-Processing Results

```bash
# Merge evaluation results of all bugs
bash merge_eval_result.sh

# Calculate pass@k metrics
bash pass_at_k.sh
```

## 📊 3. Analysis and Results

### Research Questions

Our evaluation addresses three main research questions:

- **RQ1**: Do History-Augmented LLMs Improve Bug Fixing Compared to Models Without Historical Context?
- **RQ2**: How Do Different Prompt Styles Impact the Bug-Fixing Performance of History-Augmented LLMs?
- **RQ3**: What Is the Cost of History-Augmented LLMs on Bug Fixing?

### Generate Analysis Results

```bash
cd analysis

# RQ1 & RQ2 Analysis
bash analysis_rq12.sh

# RQ3 Analysis (Computational Cost)  
bash analysis_rq3.sh

# Statistical Analysis (requires Rstudio and R environment) for RQ1, RQ2 and RQ3
statistical_test_plot_RQ123.r
```

### Key Results

-  HAFix-Agg achieves substantial performance gains by combining individual heuristics, improving bug-fixing rates 
by an average of 45.05% on BugsInPy and 49.92% on Defects4J, while fixing nearly all bugs solved by the baseline, 
plus significant additional unique fixes.
- Across both the baseline and HAFix-Agg, the Instruction prompt style consistently outperforms InstructionLabel and InstructionMask 
in the majority of model-dataset configurations, with statistically significant improvements and large effect sizes.
- The Exhaustive scenario incurs significantly higher inference time and token usage than all early stopping strategies (ES, ES
AccSorted, ES-UniSorted) across all configurations, with all 𝑝 values < 0.001. Early stopping reduces inference time and tokens by an average of 69% and 73%, respectively.


## 📚 Citation

If you use HAFix in your research, please cite our paper:

```bibtex
@article{shi2025hafix,
  title={HAFix: History-Augmented Large Language Models for Bug Fixing},
  author={Shi, Yu and Bangash, Abdul Ali and Fallahzadeh, Emad and Adams, Bram and Hassan, Ahmed E},
  journal={arXiv preprint arXiv:2501.09135},
  year={2025}
}
```

## 📧 Contact

For questions or issues, please:
- Open a GitHub issue
