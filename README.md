# PhishVision AI

## AI-Based Phishing Screenshot and Malicious Interface Detection System

PhishVision AI is a cybersecurity-focused artificial intelligence project designed to detect phishing websites and malicious web interfaces from screenshots and images.

The system combines **Computer Vision, Optical Character Recognition (OCR), QR Code Detection, URL Analysis, and cybersecurity-based risk assessment** to identify potentially malicious web interfaces.

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
* URL extraction and analysis
* QR code detection
* QR-based URL extraction
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
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
      Visual Analysis     OCR       QR Detection
             │             │             │
             │             ▼             ▼
             │       Text Analysis   URL Extraction
             │             │             │
             └─────────────┼─────────────┘
                           │
                           ▼
                     URL Analysis
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

The system follows a multi-stage detection pipeline:

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

### 5. QR Code Detection

The system can identify QR codes appearing within screenshots.

If a QR code is detected, the system attempts to extract the encoded information, particularly URLs.

### 6. URL Analysis

Extracted URLs can be analyzed for potential security indicators.

Possible indicators include:

* Suspicious domains
* Unusual URL structures
* Excessive subdomains
* IP-based URLs
* URL obfuscation
* Suspicious characters
* Potentially malicious destinations

### 7. Risk Engine

The different analysis results are combined into a cybersecurity risk assessment.

The risk engine may consider:

* Visual risk indicators
* Suspicious text indicators
* URL indicators
* QR code indicators
* AI model prediction

### 8. Final Classification

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
│
├── app/                     # Web application
│
├── data/                    # Dataset storage
│
├── models/                  # Trained AI models
│
├── notebooks/               # Research and experiments
│
├── src/
│   ├── data/               # Data loading and preprocessing
│   ├── models/             # AI/ML model implementations
│   ├── ocr/                # OCR processing
│   └── security/           # Cybersecurity analysis
│
├── tests/                   # Unit and integration tests
│
├── .gitignore               # Git ignored files
└── README.md                # Project documentation
```

---

## 📊 Dataset

The dataset will contain screenshots representing different types of web interfaces.

The primary classification categories are expected to include:

* **Phishing**
* **Legitimate**

The dataset development process will include:

1. Dataset research
2. Data collection
3. Data cleaning
4. Duplicate removal
5. Image preprocessing
6. Dataset labeling
7. Train/validation/test splitting
8. Dataset analysis

The final dataset size and composition will be documented after the dataset development phase is completed.

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

### Why These Metrics Matter

For phishing detection, accuracy alone may not be sufficient.

**Precision** measures how many predicted phishing samples are actually phishing.

**Recall** measures how many actual phishing samples are successfully detected.

**F1-Score** provides a balance between precision and recall.

The final experimental results will be added to this section after model training and evaluation.

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

Extracted URLs may be analyzed for:

* Suspicious domains
* IP addresses
* Long or obfuscated URLs
* Unusual subdomains
* Suspicious URL patterns

### QR Indicators

QR codes may be detected and decoded to determine whether they contain potentially suspicious URLs or other information.

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
QR Evidence
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
4. Detect QR codes.
5. Analyze URLs.
6. Generate a risk assessment.
7. Display the final classification.

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

Once the project dependencies are finalized:

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

After completing the application implementation, the system will be launched using:

```bash
streamlit run app/app.py
```

The user will then be able to upload a screenshot and receive a phishing/security analysis.

> **Note:** The exact application entry point may change during development.

---

## 🧪 Testing

The `tests/` directory will contain tests for important system components.

Testing may cover:

* Data preprocessing
* Image processing
* OCR extraction
* QR detection
* URL analysis
* Risk scoring
* Model inference
* Application functionality

---

## 🗺️ Development Roadmap

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

🚧 **Currently under active development.**

The project is currently in the foundational development stage. Dataset development, model experimentation, cybersecurity analysis, and application implementation will be completed progressively.

Experimental results will be added after the relevant experiments are conducted.

---

## 👨‍💻 Author

**Rubayat Karim**

Bachelor's Student
Computer Science and Technology
Nanjing Tech University, China

---

## 📄 License

License information will be added after the project's licensing strategy is finalized.

---

## ⭐ Project Vision

The long-term goal of PhishVision AI is to develop a practical and research-oriented cybersecurity system capable of analyzing suspicious web interfaces using multiple sources of evidence.

The project aims to demonstrate how artificial intelligence can support phishing detection by combining **visual intelligence, textual analysis, and cybersecurity reasoning**.
