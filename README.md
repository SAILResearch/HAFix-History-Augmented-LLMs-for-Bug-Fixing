**HAFix** is an approach that leverages individual historical heuristics associated with bugs and aggregates the results of these heuristics (HAFix-Agg) to enhance LLMs’ bug-fixing capabilities

<p align="center"><strong>HAFix: History-Augmented Large Language Models for Bug Fixing</strong></p>

<p align="center">Yu Shi, Abdul Ali Bangash, Emad Fallahzadeh, Bram Adams, Ahmed E. Hassan</p>

<p align="center"><a href="https://mcis.cs.queensu.ca">lab on Maintenance, Construction and Intelligence of Software (MCIS)</a></p>
<p align="center"><a href="https://sail.cs.queensu.ca">Software Analysis and Intelligence Lab (SAIL)</a></p>
<p align="center">School of Computing, Queen's University</p>

If you find this repository useful, please consider giving us a star :star: and citation:

```
@article{shi2025hafix,
  title={HAFix: History-Augmented Large Language Models for Bug Fixing},
  author={Shi, Yu and Bangash, Abdul Ali and Fallahzadeh, Emad and Adams, Bram and Hassan, Ahmed E},
  journal={arXiv preprint arXiv:2501.09135},
  year={2025}
}
```
## Project Structure
- dataset: collecting the data of baseline and historical heuristics
- model_inference: conduct prompt construction and LLM inference
- evaluation: evaluating the model-generated fixed code and calculating the pass@k
- analysis: generate the figure and box plot for 3 RQs
