# AlignAR

**AlignAR** is a generative sentence alignment framework for constructing high-quality Arabic–English parallel corpora, with a focus on **legal and literary texts**. It leverages large language models (LLMs) to perform robust alignment beyond traditional heuristic or statistical approaches.

---

## Overview

Parallel corpora are essential for machine translation and cross-lingual research, yet high-quality Arabic–English datasets remain scarce—especially for complex domains like legal and literary texts.

**AlignAR** addresses this gap by:
- Introducing a **generative alignment paradigm**
- Supporting **non 1-to-1 mappings** (e.g., 1-to-many, many-to-one)
- Improving robustness on difficult alignment cases
- Enabling scalable corpus construction with minimal manual effort

---

##  Key Features

-  **LLM-based alignment**  
  Uses generative models instead of rule-based or embedding-only methods

-  **Flexible mapping**  
  Handles complex alignments beyond simple sentence pairs

-  **Domain-specific datasets**  
  Focus on legal and literary corpora

-  **Lightweight pipeline**  
  Lower hardware requirements compared to traditional alignment systems

-  **Improved performance**  
  More robust on challenging datasets

---

## Methodology

AlignAR follows a **generative alignment pipeline**:

1. **Prompt-based Alignment**
   - Use LLMs to generate aligned sentence pairs
   - Encourage structured outputs with explicit indexing

2. **Evaluation**
   - Compare against gold alignments
   - Measure precision, recall, and F1

---


##  Citation

```bibtex
@misc{huang2026alignargenerativesentencealignment,
      title={AlignAR: Generative Sentence Alignment for Arabic-English Parallel Corpora of Legal and Literary Texts}, 
      author={Baorong Huang and Ali Asiri},
      year={2026},
      eprint={2512.21842},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2512.21842}, 
}
```
