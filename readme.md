# RxInsight 💊

RxInsight is an interactive pharmacovigilance application designed to make medication safety data more accessible and understandable.

The application allows users to search for medications and explore reported adverse drug events, patient demographics, and safety patterns through interactive data visualizations.

> **Disclaimer:** RxInsight is intended for informational and educational purposes only. The information presented by the application should not be considered medical advice, diagnosis, treatment, or a substitute for consultation with a qualified healthcare professional.

---

## 🎯 Project Rationale

Medication safety information can be complex and difficult for non-medical users to explore.

RxInsight was developed to provide a simple and interactive interface for exploring reported adverse drug event data from the **FDA Adverse Event Reporting System (FAERS)**.

The goal of the project is to transform raw pharmacovigilance data into accessible visual insights that allow users to explore medication safety patterns in an intuitive way.

The application is designed to present information clearly while emphasizing an important limitation of adverse-event reporting data: **a reported event does not necessarily mean that the medication caused the event.**

---

## ✨ Features

* 🔎 Search for medications by brand or generic name
* ⚠️ Explore reported adverse drug events
* 📊 Visualize adverse-event statistics
* 👥 Analyze patient demographics
* 🌐 Explore medication safety patterns
* 📈 Interactive data visualizations
* 🔄 Retrieve information dynamically from the OpenFDA API
* 📋 Present complex safety data in an accessible format

---

## 👥 Target Audience

RxInsight is designed primarily for:

* General users interested in medication safety
* Non-medical users who want to explore publicly available drug-safety information
* Students and learners interested in pharmacovigilance and data analysis

The application is **not intended for healthcare professionals or clinical decision-making**.

---

## 🌐 Data Source

RxInsight uses publicly available data from the **FDA Adverse Event Reporting System (FAERS)** through the **OpenFDA API**.

The application retrieves information from OpenFDA endpoints related to:

* Drug adverse events
* Drug labeling information

Because the application relies on reported data, the results may contain incomplete, inconsistent, or duplicated information.

---

## 🛠️ Technologies

The project was developed using:

* **Python** – application logic and data processing
* **Streamlit** – interactive web application interface
* **Pandas** – data processing and analysis
* **Plotly** – interactive data visualizations
* **OpenFDA API** – external pharmacovigilance data
* **Poetry** – dependency and project management

---

## 🏗️ Project Structure

The main executable file of the application is:

```text
main.py
```

The project is divided into separate Python modules to organize the application's functionality and keep the code modular and maintainable.

A simplified structure is:

```text
RxInsight/
│
├── main.py
├── config.py
├── api.client.py
├── ui_styles.py
├── visualizations.py
├── data_processor.py
├── requirements.txt
├── pyproject.toml
├── poetry.lock
└── README.md

```

### `main.py`

`main.py` is the entry point of the application.

It is responsible for connecting the user interface with the different application modules, handling user input, retrieving the relevant data, and displaying the results through Streamlit.

---

## ⚙️ Installation

### Prerequisites

Make sure you have:

* Python installed
* Poetry installed
* Git installed

### Clone the repository

```bash
git clone https://github.com/YaaritHanan/RxInsight.git
cd RxInsight
```

### Install dependencies

Using Poetry:

```bash
poetry install
```

This installs the dependencies specified in `pyproject.toml` and uses the project's `poetry.lock` file to maintain consistent package versions.

---

## ▶️ Running the Application

The executable file is:

```text
main.py
```

Run the application using:

```bash
poetry run streamlit run main.py
```

Alternatively, if the required environment is already activated:

```bash
streamlit run main.py
```

After running the command, Streamlit will provide a local URL through which the application can be accessed.

---

## 📖 How to Use

1. Open the RxInsight application.
2. Enter the name of a medication in the search field.
3. Search for the desired medication.
4. Explore the available reported adverse-event information.
5. Review the different statistics and patient demographic information.
6. Use the interactive visualizations to explore the data.
7. Interpret the results in the context of the provided disclaimer and data limitations.

---

## 📊 Data Visualization

RxInsight uses interactive Plotly visualizations to make the data easier to explore.

The visualizations can be used to identify patterns in:

* Reported adverse events
* Patient demographics
* Event frequencies
* Medication safety information
* Trends within the available dataset

Interactive charts allow users to explore the data rather than relying only on static tables.

---

## ⚠️ Limitations

The information provided by RxInsight has several important limitations:

* The application relies on **reported adverse-event data**.
* A reported adverse event does **not establish a causal relationship** between a medication and the event.
* Reports may contain incomplete or inconsistent information.
* The data may include duplicate or repeated reports.
* The availability and completeness of results depend on the data provided by the OpenFDA API.
* The application should not be used to make medical or treatment decisions.

---

## 🔐 Privacy and Security

RxInsight uses publicly available information retrieved through the OpenFDA API.

The application does not provide personalized medical recommendations and should not be used as a substitute for professional medical consultation.

API credentials or other sensitive information should not be stored directly in the source code or committed to the GitHub repository.

---

## 🚀 Live Application

The deployed Streamlit application is available here:

**https://rxinsight.streamlit.app/**

---

## 💻 GitHub Repository

The complete source code is available on GitHub:

**https://github.com/YaaritHanan/RxInsight**

---

## ⚠️ Disclaimer

RxInsight is intended for **informational and educational purposes only**.

The information presented by the application should not be considered medical advice, diagnosis, treatment, or a substitute for consultation with a qualified healthcare professional.

Adverse-event reports represent reported observations and do not necessarily demonstrate that a medication caused a particular event.

Users should consult a qualified healthcare professional regarding any medical or medication-related questions.

---

## 📚 Project Context

RxInsight was developed as a Python course project and demonstrates the use of:

* Object-oriented programming
* API integration
* Data processing
* Data visualization
* Interactive web application development
* Modular Python code organization
* Dependency management with Poetry
