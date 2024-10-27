# SPICEPilot: AI-Powered SPICE Code Generation and Simulation Framework

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Overview

**SPICEPilot** is an AI-driven framework designed to enhance the automation of SPICE code generation and circuit simulation. Utilizing advanced Large Language Models (LLMs), SPICEPilot bridges gaps between software and hardware domains, generating SPICE code for analog and digital circuits with standardized benchmarking and performance evaluations. This tool is developed with a focus on Python and leverages the PySpice library, enabling robust simulation and analysis of complex circuit designs.

## Table of Contents

- [Motivation](#motivation)
- [Key Features](#key-features)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [Benchmarking & Performance](#benchmarking--performance)
- [Limitations & Future Work](#limitations--future-work)
- [Contributing](#contributing)
- [License](#license)

## Motivation

Traditional circuit design and simulation methodologies are struggling to keep up with the escalating complexity of modern hardware and software systems. While LLMs show promising capabilities in code generation, applying these models to SPICE code for analog circuits remains challenging due to limited domain-specific knowledge. SPICEPilot addresses these limitations by providing a framework that can generate SPICE code, validate it, and apply structured benchmarking to assess its performance, creating a streamlined and accessible tool for the hardware design community.

## Key Features

- **Automated SPICE Code Generation:** Uses LLMs to generate Python-based SPICE codes for a range of circuit configurations.
- **Benchmarking Framework:** Establishes criteria for evaluating circuit performance with classifications by difficulty (Easy, Medium, Hard, Extreme).
- **Error Identification & Mitigation:** Integrates error-detection capabilities to refine and validate LLM-generated code, ensuring compliance with hardware design standards.
- **Data Augmentation:** Leverages open-source datasets to address data scarcity and facilitate future research in analog circuit design.

## Installation

To run SPICEPilot, please ensure you have Python 3.8 or above installed. Follow the steps below:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/ACADLab/SPICEPilot.git
   cd SPICEPilot
   ```


3. **Setup PySpice**
   - SPICEPilot requires PySpice to run simulations. Instructions for installing PySpice can be found [here](https://pyspice.fabrice-salvaire.fr/installation.html).

## Getting Started
### Example usage
The `prompt_pilot.md` should be infered to the LLM it can either be added to the knowledge or the instrctions of LLM. Later, the prompt and description: a very good verbal example of how the circuit is constrcuted needs to be quired to the LLM and ask it to generate the PySpice code.


### Dataset & Benchmarking Criteria

SPICEPilot includes a benchmarking framework to assess LLM performance in circuit generation. Circuits are categorized by difficulty:
- **Easy:** ≤10 transistors
- **Medium:** 11–25 transistors
- **Hard:** 26–45 transistors
- **Extreme:** >45 transistors

Each circuit is evaluated based on accuracy, functional compliance, and ability to perform required analyses (e.g., AC, DC, transient).

### Experimental Results

SPICEPilot outperforms prior models like AnalogCoder in SPICE code generation accuracy and robustness, achieving higher success rates across all difficulty levels and circuit types. See our published [tobeupdated](tobeupdatted) for detailed results and comparisons.

## Limitations & Future Work

While SPICEPilot offers significant advancements in automating SPICE code generation, limitations remain, particularly in:
- **Advanced Parameterization**: Improvements are needed for finer control over device-specific configurations (e.g., gate width, input signals).
- **Enhanced Reasoning**: Additional work is required to improve LLM logical reasoning within hardware-specific contexts.
- **Expansion of Benchmarking Dataset**: Future versions will include a larger and more diverse set of circuits to refine evaluation criteria.

Plans include implementing multi-modal capabilities, enabling the model to interpret circuit diagrams alongside text-based descriptions, and expanding the dataset to include more complex analog circuits.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
