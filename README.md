# PhishVision AI

## AI-Based Phishing Screenshot and Malicious Interface Detection System

PhishVision AI is a cybersecurity-focused artificial intelligence project designed to detect phishing websites and malicious web interfaces from screenshots and images.

The system combines **Computer Vision, Optical Character Recognition (OCR), URL Analysis, and cybersecurity-based risk assessment** to identify potentially malicious web interfaces.

The project explores how artificial intelligence can analyze both the **visual appearance** and **textual content** of a web interface to identify phishing indicators.

---

## 🎯 Project Objective

The primary objective of PhishVision AI is to develop an intelligent system capable of distinguishing between legitimate and phishing web interfaces using visual and textual information extracted from screenshots.

The system aims to answer the following research question:

> Can artificial intelligence detect phishing and malicious web interfaces directly from screenshots by combining computer vision with OCR-based textual analysis?

The project also investigates whether combining multiple security indicators can improve phishing detection compared with relying only on visual classification.

---

## 🔍 Key Features

* Phishing screenshot detection
* Legitimate website classification
* Computer Vision-based interface analysis
* OCR-based text extraction
* Suspicious text detection
* URL analysis of a user-supplied URL
* Cybersecurity risk scoring
* AI-based phishing classification
* Interactive web interface
* Security analysis report

---

## 🧠 System Architecture

```text
                    INPUT SCREENSHOT
                           │
                           ▼
                  Image Preprocessing
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      Visual Analysis (CNN)              OCR
             │                           │
             │                           ▼
             │                    Text Analysis
             │                           │
             └─────────────┬─────────────┘
                           │
                           ▼
                      Risk Engine
                           │
                           ▼
                  Final Classification
                           │
                    ┌──────┴──────┐
                    ▼             ▼
               LEGITIMATE      PHISHING
```

---

## 🔄 Detection Pipeline

The system follows a multi-stage detection pipeline. Every step below is
implemented in `src/`:

### 1. Image Input

The user provides a screenshot or image of a web interface.

### 2. Image Preprocessing

The input image is processed to improve its quality and prepare it for analysis.

Possible preprocessing operations include:

* Image resizing
* Normalization
* Noise reduction
* Color conversion
* Image enhancement

### 3. Computer Vision Analysis

Computer Vision techniques are used to analyze the visual characteristics of the interface.

Potential indicators include:

* Layout structure
* Forms and login interfaces
* Buttons
* Branding elements
* Visual patterns
* Suspicious interface components

### 4. OCR Analysis

OCR is used to extract visible text from the screenshot.

The extracted text can then be analyzed for potentially suspicious content such as:

* Login requests
* Password requests
* Account verification messages
* Urgency-related language
* Payment requests
* Security warnings
* Suspicious instructions

### 5. URL Analysis

The user-supplied URL is analyzed for potential security indicators.

Possible indicators include:

* Suspicious domains
* Unusual URL structures
* Excessive subdomains
* IP-based URLs
* URL obfuscation
* Suspicious characters
* Potentially malicious destinations

### 6. Risk Engine

Component scores are combined into a heuristic cybersecurity risk assessment.

The risk engine may consider:

* Visual risk indicators (CNN)
* Suspicious text indicators (OCR)
* URL indicators
* AI model prediction

### 7. Final Classification

The system produces a final classification:

```text
LEGITIMATE
    or
PHISHING
```

A risk score and supporting security indicators may also be presented to the user.

---

## 🛠️ Technology Stack

### Programming Language

* Python

### Artificial Intelligence / Machine Learning

* PyTorch
* TorchVision
* Convolutional Neural Networks (CNN)
* Transfer Learning

### Computer Vision

* OpenCV
* Pillow

### OCR

* EasyOCR

### Web Application

* Streamlit

### Version Control

* Git
* GitHub

---

## 📂 Project Structure

```text
PhishVision-AI/
├── app/app.py                 # Streamlit application entry point
├── src/
│   ├── config.py              # Paths, threshold, image/URL limits
│   ├── data/                  # Dataset, dataloader, transforms, splits
│   ├── models/                # CNN, predictor, checkpoint integrity
│   ├── ocr/                   # OCR engine (EasyOCR)
│   ├── security/              # Analyzer, risk engine, assessment, URL/text
│   └── training/              # Training entry points
├── robustness/                # FGSM/PGD adversarial evaluation
├── scripts/
│   ├── audit_*.py             # Dataset audit tools
│   ├── check_*.py             # Manual harnesses (need torch + dataset)
│   ├── create_train_val_test_split.py
│   ├── evaluate_predictor.py  # Reproducible per-image evaluation
│   ├── provision_model.py     # Verified production model download
│   └── _preflight.py          # Prerequisite checks for check_*.py
├── tests/                     # pytest suite (torch-free)
├── results/                   # Tracked evaluation reports and plots
├── pyproject.toml             # pytest configuration
├── requirements.txt           # Declared runtime dependencies
├── requirements-dev.txt       # Runtime + test/evaluation tooling
└── requirements-lock.txt      # Exact recorded environment
```

`data/` (dataset splits) and `models/` (checkpoints) are local-only and
intentionally not tracked.

---

## 📊 Dataset

The dataset will contain screenshots representing different types of web interfaces.

The primary classification categories are expected to include:

* **Phishing**
* **Legitimate**

The dataset pipeline is implemented and guarded (`scripts/capture_pages.py`,
`prune_captures.py`, `curate_pilot.py`, `build_manifest.py`, `triage_phishing.py`):

1. Capture with headless Chromium at a fixed viewport, recording each source URL.
2. Rejection of blank renders and blocked interstitials ("just a moment",
   "suspected phishing", "verify you are human") before a file is written.
3. Byte-identical duplicate removal, then perceptual near-duplicate clustering.
4. Curation: near-duplicate, registered-domain and brand channels are merged into
   one group, every group assigned to exactly one split, and cross-label
   contradictions dropped.
5. Manifest validation (schema, digests, per-domain/per-brand split integrity) and
   OCR label triage that flags captures with no credential vocabulary.

Running the whole sequence is one command: `python scripts/refresh_pilot.py`.

The evaluation set is **555 screenshots** (387 train / 83 validation / 85 test).

An audit of that split found **735 cross-split near-duplicate pairs**, so exact-file
checks were insufficient. The split was rebuilt by perceptual cluster (324 clusters,
none spanning two splits), and all quality figures reported below come from the
cluster-disjoint evaluation. A separate v3 pilot of 205 captures (fresh PhishTank
URLs plus real login pages) uses the same cluster, domain and brand grouping, with
an interstitial/blank guard, byte and perceptual deduplication, and OCR label
triage; see `docs/dataset-v3-plan.md` and `docs/status.md`.

---

## 🧠 AI/ML Methodology

The machine learning component will investigate image-based phishing classification.

The development process is planned to include:

### Baseline Model

A baseline Convolutional Neural Network (CNN) will be developed to establish an initial performance benchmark.

### Transfer Learning

Pre-trained computer vision models may be investigated to determine whether transfer learning can improve classification performance.

Potential architectures may include models available through TorchVision.

### Model Training

The training process will involve:

* Training dataset
* Validation dataset
* Image preprocessing
* Data augmentation
* Loss function
* Optimizer
* Learning rate
* Number of epochs

### Model Evaluation

The trained models will be evaluated using appropriate classification metrics.

---

## 📈 Evaluation Metrics

Model performance will be evaluated using:

* Accuracy
* Precision
* Recall
* F1-Score
* Confusion Matrix

Additional metrics may be considered depending on the final experimental design.

## Adversarial Robustness Evaluation

PhishVision includes an isolated adversarial robustness evaluation for the
CNN classifier. The robustness experiments do not modify the production
predictor or retrain the existing model.

The evaluation uses phishing screenshots from the clean validation split and
focuses on phishing samples that are correctly classified by the clean model.
This prevents samples that were already misclassified from being counted as
successful adversarial attacks.

### Threat Model

The robustness evaluation tests image-space perturbations against the trained
CNN using gradient-based attacks:

- **FGSM (Fast Gradient Sign Method)** — single-step gradient perturbation.
- **PGD (Projected Gradient Descent)** — iterative gradient perturbation
  constrained by an L-infinity perturbation budget.

The perturbation is applied to the image tensor in the `[0, 1]` pixel space.

Tested perturbation magnitudes:

- `epsilon = 0.005`
- `epsilon = 0.010`
- `epsilon = 0.020`
- `epsilon = 0.040`

For PGD, the evaluation uses 10 iterations with a step size of
`epsilon / 10`.

### Evaluation Protocol

The validation split contains 58 phishing images. The clean model correctly
classifies 35 of these as phishing.

Only those 35 correctly classified phishing images are used for adversarial
evaluation.

A successful adversarial attack is defined as:

```text
clean prediction:       phishing
adversarial prediction: legitimate

### Why These Metrics Matter

For phishing detection, accuracy alone may not be sufficient.

**Precision** measures how many predicted phishing samples are actually phishing.

**Recall** measures how many actual phishing samples are successfully detected.

**F1-Score** provides a balance between precision and recall.

Measured on the cluster-disjoint split (n=83, no image shares a cluster with
training data):

| Signal | ROC AUC | 95% bootstrap CI |
|---|---|---|
| OCR text heuristics | 0.638 | 0.529-0.743 |
| CNN | 0.657 | 0.537-0.772 |
| combined score | 0.694 | 0.566-0.808 |

Calibration of the CNN: **Brier 0.230, ECE 0.041**.

The **leaky split recorded F1 72.2 %; the leakage-free figure is 60.8 %**, and the
earlier number is marked superseded in the evidence ledger. The current model's
false-positive rate is **0.33** (95% CI 0.14-0.61) on the pilot's legitimate test
images.

Four candidate remedies for that false-positive rate were tested against
pre-registered criteria on data they were not tuned on, and **all four were
rejected**:

| Candidate | Verdict |
|---|---|
| Decision threshold risk >= 25/100 (P-1) | rejected: recall 0.60 -> 0.20 |
| Frozen-backbone linear probe (4.2) | no evidence: AUC 0.50 vs 0.56 |
| Calibrated text/CNN fusion | no gain: identical to CNN-only; text weight negative |
| URL supplied + threshold 20/100 (P-4) | rejected: detection 0.526, FPR 0.333 |

The one confirmed effect: supplying the reported URL raises phishing risk by
**+3.75 points** and legitimate risk by **+0.00** on a 100-point scale (P-3).
Details in `docs/measurements/` and `docs/pre-registered-experiments.md`.

**Tests:** 171 fast and 36 slow (`pytest -m "not slow"` runs the fast set).

---

## 🔐 Cybersecurity Analysis

PhishVision AI is not intended to rely solely on the machine learning classifier.

The project also investigates additional cybersecurity indicators.

### Visual Indicators

The system may identify suspicious visual patterns such as:

* Fake login interfaces
* Account verification screens
* Suspicious payment forms
* Brand impersonation
* Unusual interface layouts

### Text Indicators

OCR-extracted text may be analyzed for:

* Urgency
* Account suspension warnings
* Credential requests
* Payment requests
* Verification requests
* Suspicious instructions

### URL Indicators

The user-supplied URL is analyzed for:

* Suspicious domains
* IP addresses
* Long or obfuscated URLs
* Unusual subdomains
* Suspicious URL patterns

---

## ⚠️ Risk Scoring

The project aims to provide a risk-oriented interpretation of the analysis.

A conceptual risk model may combine multiple indicators:

```text
Visual Evidence
       +
OCR/Text Evidence
       +
URL Evidence
       +
AI Prediction
       │
       ▼
  Risk Assessment
       │
       ▼
Risk Level / Classification
```

The exact scoring methodology will be determined during the cybersecurity analysis and experimentation phase.

---

## 🖥️ Web Application

A Streamlit-based web interface is planned for the project.

The application will allow users to:

1. Upload a screenshot.
2. Run AI-based analysis.
3. Extract text using OCR.
4. Analyze the supplied URL.
5. Generate a risk assessment.
6. Display the final classification.

The intended output will provide both the classification and supporting security indicators.

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd PhishVision-AI
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

#### Windows PowerShell

```powershell
.\venv\Scripts\Activate.ps1
```

#### Windows Command Prompt

```cmd
venv\Scripts\activate
```

### 4. Install Dependencies

| File | Contents | Use when |
|---|---|---|
| `requirements.txt` | Direct runtime imports of `app/` and `src/` | Running the application |
| `requirements-dev.txt` | Runtime deps + pytest, scikit-learn, matplotlib | Running tests and evaluation |
| `requirements-lock.txt` | Exact versions of the recorded environment | Reproducing a known-good environment |

```bash
python -m pip install -r requirements-dev.txt
```

Python 3.11 is the supported runtime. The application also needs the
production checkpoint described below.

## Production Model Provisioning

The production CNN model is distributed as a GitHub Release artifact rather than tracked in Git.

From the project root, run:

```powershell
python .\scripts\provision_model.py
```

The provisioning script:

1. Downloads the frozen PhishVision CNN v2 production artifact.
2. Verifies its SHA-256 checksum.
3. Installs the verified artifact as `models/phishvision_cnn_v2.pth`.
4. Replaces the local model only after checksum verification succeeds.

Expected SHA-256:

```text
1403582CCE07BE1E36E70E4A0D425CFB152B86C7ABEE5D1074DEF79CBB2FB628
```

The production CNN threshold is `0.35`.

### Runtime model verification

The predictor re-verifies the checkpoint against the published SHA-256
before loading it. A mismatch aborts loading: the analyzer degrades to
"CNN unavailable" and the expected and actual digests are printed to
stderr. `scripts/provision_model.py` and the predictor share one digest
constant in `src/models/integrity.py`.

Experimental checkpoints can be loaded deliberately:

```powershell
$env:PHISHVISION_ALLOW_UNVERIFIED_MODEL = "1"
python .\scripts\evaluate_predictor.py --split test --model path\to\candidate.pth `
    --threshold 0.35 --output reports\candidate.csv --allow-unverified-model
```

The bypass prints the digest that was actually loaded. Never use it for
the production path.

Run model provisioning before starting the application:

```powershell
python .\scripts\provision_model.py
streamlit run app/app.py
```

---

## ▶️ Usage

Run the application from the project root:

```bash
streamlit run app/app.py
```

The user will then be able to upload a screenshot and receive a phishing/security analysis.

The application validates the upload and image dimensions before running
OCR, URL analysis, and CNN inference, then renders component scores,
evidence, and a recommended action.

---

## 🧪 Testing

The pytest suite is torch-free, so it runs without the ML stack, the
model checkpoint, or a dataset:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

| Module | Covers |
|---|---|
| `tests/test_risk_engine.py` | Published 30/30/40 weights, clamping, risk bands |
| `tests/test_security_assessment.py` | Verdict/action mapping and OCR/URL/CNN evidence |
| `tests/test_model_integrity.py` | Checkpoint digest verification and the experiment bypass |
| `tests/test_app_upload_boundary.py` | Upload size limit enforced before image decoding |

The Streamlit page is never imported by the tests: the upload validator is
extracted from `app/app.py` with `ast` and executed in isolation.

### Manual validation harnesses

`scripts/check_*.py` exercise the full analyzer (torch, EasyOCR, CNN, a real
screenshot). They need `requirements.txt`, the provisioned model, and
`data/clean_split_v2/`. When a prerequisite is missing they print one SKIP
line and exit with status `2` instead of raising:

```powershell
python .\scripts\check_security_assessment.py
python .\scripts\check_production_hardening.py
python .\scripts\check_failure_injection.py
python .\scripts\check_security_scenarios.py
```

---

## 🗺️ Development Roadmap

> This roadmap is the original project plan, kept for history. Current
> behaviour is documented in the sections above and in `results/`;
> unchecked boxes are not evidence that a capability is missing or present.

### Phase 1 — Project Foundation

* [x] Development environment setup
* [x] Git repository initialization
* [x] Project folder structure
* [x] Initial documentation

### Phase 2 — Dataset Development

* [ ] Dataset research
* [ ] Phishing screenshot collection
* [ ] Legitimate screenshot collection
* [ ] Dataset cleaning
* [ ] Dataset labeling
* [ ] Dataset preprocessing
* [ ] Train/validation/test split

### Phase 3 — AI Model Development

* [ ] Baseline CNN
* [ ] Transfer learning
* [ ] Model training
* [ ] Hyperparameter experimentation
* [ ] Model evaluation
* [ ] Confusion matrix analysis

### Phase 4 — Cybersecurity Intelligence

* [ ] OCR integration
* [ ] Suspicious text detection
* [ ] URL extraction
* [ ] URL security analysis
* [ ] QR code detection
* [ ] QR-based URL analysis
* [ ] Risk scoring engine

### Phase 5 — Application Development

* [ ] Streamlit interface
* [ ] Image upload
* [ ] AI prediction
* [ ] OCR results
* [ ] URL analysis results
* [ ] Risk assessment
* [ ] Security report

### Phase 6 — Evaluation and Documentation

* [ ] Experimental evaluation
* [ ] Performance comparison
* [ ] Error analysis
* [ ] Limitations analysis
* [ ] Final documentation
* [ ] Research findings

---

## 🎓 Research Direction

PhishVision AI explores the intersection of:

**Artificial Intelligence + Computer Vision + Optical Character Recognition + Cybersecurity**

A major research direction of the project is **multimodal phishing detection**, where different sources of evidence are combined rather than relying on a single classification method.

Future research may investigate:

* Multimodal AI
* Explainable AI (XAI)
* Improved phishing datasets
* Advanced visual feature extraction
* Transformer-based vision models
* More sophisticated URL analysis
* Real-time phishing detection
* Adversarial robustness
* Model interpretability

---

## ⚠️ Limitations

The system may have limitations related to:

* Dataset quality and diversity
* Screenshot resolution
* Unseen website designs
* OCR accuracy
* Dynamic web content
* Obfuscated URLs
* False positives
* False negatives
* Generalization to real-world phishing campaigns

These limitations will be evaluated more thoroughly during the experimental phase.

---

## 🔒 Ethical and Security Considerations

PhishVision AI is developed for **educational, research, and defensive cybersecurity purposes**.

The project focuses on identifying potentially malicious interfaces and improving awareness of phishing threats.

Any datasets, screenshots, URLs, or external resources used during development should be handled responsibly and in accordance with applicable laws, licenses, and terms of use.

---

## 📌 Project Status

The application, the frozen v2 production CNN, the security assessment
layer, and the robustness evaluation are implemented. Evaluation records,
including the adversarial robustness study and candidate-model
experiments, are tracked under `results/`.

The frozen production checkpoint remains v2; candidate and experimental
models documented in `results/` have not been promoted.

---

## 👨‍💻 Author

**Rubayat Karim**

Bachelor's Student
Computer Science and Technology
Nanjing Tech University, China

---

## 📄 License

No license has been selected yet. The source is public for review, study and research use; reuse beyond that should be discussed with the author, since the training captures were gathered from third-party feeds under their own terms.

---

## ⭐ Project Vision

The long-term goal of PhishVision AI is to develop a practical and research-oriented cybersecurity system capable of analyzing suspicious web interfaces using multiple sources of evidence.

The project aims to demonstrate how artificial intelligence can support phishing detection by combining **visual intelligence, textual analysis, and cybersecurity reasoning**.

## Claims to evidence

Every claim below names its ledger row in `docs/ledger.md`. Anything not listed
is **not claimed**.

| Claim | Evidence | Status |
|---|---|---|
| 159 tests pass (131 fast, 28 slow) | `R-PV-tests-01`, `pytest -q` | verified |
| Checkpoint digest is verified before load | `R-PV-integrity-01` | verified |
| Dataset accepted: 555 images, no cross-split duplicates | `R-PV-dataset-01` | verified |
| Development-set metrics at 0.35 on a **cluster-disjoint** split: acc 62.7 %, F1 60.8 %, CNN AUC 0.657, combined AUC 0.694 | `R-PV-leakagefree-01`, `R-PV-components-cluster-01` | **DEVELOPMENT; supersedes the leaky-split F1 72.2 % and the leaky component AUCs** |
| Threshold 0.35 retained after test was consulted | `R-PV-threshold-01` | recorded |
| Candidate `advtrained_v2` rejected (test F1 0.699 vs 0.722) | `R-PV-advtrained-test` | recorded |
| QR-code detection, URL extraction from images | — | **not claimed / not implemented** |
| Sealed-holdout performance | — | **not claimed** |
| Deployable service | — | **not claimed** |
