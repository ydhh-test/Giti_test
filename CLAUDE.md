# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an internal testing project for the VibeCoding collaboration paradigm, focusing on tire image post-processing for JT (吉泰) tires. It is **not** intended as a production code repository. The project contains tire post-processing components as documented in the Feishu documentation.

**Important**: Do not merge to the main branch.

## Development Environment Setup

This project uses Python 3.12 with a conda environment. Before running any code:

```bash
# Activate the conda environment
conda activate py12_giti_speckit

# Navigate to the project directory
cd /Users/guiyu/aiProjects/claudeProjects/giti-tire-ai-pattern

# Set PYTHONPATH to include the project root
export PYTHONPATH=/Users/guiyu/aiProjects/claudeProjects/giti-tire-ai-pattern:$PYTHONPATH
```

You can also use the setup script:
```bash
./.setup_giti_speckit_py12.sh
```

## Project Architecture

The codebase follows a clear layered architecture organized into functional modules:

### Configuration Layer (`configs/`)
- **base_config.py**: Base configuration for paths and default parameters
- **postprocessor_config.py**: Configuration for post-processing parameters
- **rules_config.py**: Rule-based configuration definitions

### Business Logic Layer (`services/`)
This is the core implementation layer containing the tire processing pipeline:
- **preprocessor.py**: Preprocessing of user input data (gray border removal, CMYK conversion)
- **inference.py**: Pattern block generation calls (center/edge regions)
- **postprocessor.py**: Main post-processing flow (RIB assembly, symmetry implementation)
- **analyzers.py**: Geometric rationality analysis (period detection, sea-land ratio)
- **scorer.py**: Scoring system (business/aesthetic evaluation)

### Utilities Layer (`utils/`)
Common function library containing business-agnostic base functionality:
- **io_utils.py**: File I/O operations and directory traversal
- **cv_utils.py**: Basic image operation wrappers (scaling, cropping, color conversion)
- **logger.py**: Standardized logging system

### Testing (`tests/`)
Test datasets and test cases.

### Documentation (`docs/`)
Project documentation and architecture diagrams.

## Processing Pipeline Flow

The tire processing follows this sequence:
1. **Preprocessing** → User input data preparation
2. **Inference** → Pattern block generation (center/edge)
3. **Post-processing** → RIB assembly and symmetry
4. **Analysis** → Geometric validation (periods, sea-land ratio)
5. **Scoring** → Business and aesthetic evaluation

## Code Organization Principles

- Business logic is isolated in `services/` with clear separation of concerns
- Reusable utilities are in `utils/` and should remain business-agnostic
- Configuration is centralized in `configs/` for easy parameter management
- The architecture supports the full tire post-processing pipeline from input to evaluation
