# SSP3 Pre-Silo IV Predictor

A Streamlit-based soft sensor application for predicting **Intrinsic Viscosity (IV)** at the **SSP-III Reactor Outlet / Pre-Silo** using DCS process data and manually entered Feed IV.

## Overview

This application estimates Pre-Silo IV from historical DCS readings over an automatically calculated process window.

The application:

1. Loads DCS data from an Excel file.
2. Accepts the Feed IV from the plant logbook.
3. Accepts the Reactor Exit / Pre-Silo date and time.
4. Uses only DCS readings available **at or before the selected exit time**.
5. Calculates production rate from the active rotary speed.
6. Calculates reactor and crystallizer/preheater residence times.
7. Automatically determines the process-entry time using the residence-time calculation.
8. Aggregates the required process features over the calculated window.
9. Applies the trained machine-learning models.
10. Displays the predicted Pre-Silo IV along with diagnostics and model comparison.

## Prediction Point

**SSP-III Reactor Outlet / Pre-Silo**

The prediction is intended to represent the IV of material reaching the Pre-Silo at the selected Reactor Exit time.

## Input Data

### 1. DCS Excel File

Upload the DCS Excel export containing the required process tags and a `TIME STAMP` column.

The application uses DCS data only up to the selected Reactor Exit / Pre-Silo time. Future rows are excluded from the prediction window.

### 2. Feed IV

Enter the Feed IV manually from the plant logbook.

### 3. Reactor Exit / Pre-Silo Date and Time

Select the date and time corresponding to the prediction point.

## Process Calculations

### Production Rate

The application uses the two rotary tags:

- `325-HC2571`
- `325-HC2591`

The active rotary speed is determined from the positive running rotary value.

Production rate is calculated using:

**Production Rate (TPH) = Active Rotary RPM × 2.196**

### Residence Time

Reactor residence time is calculated from:

**Reactor Residence Time = Reactor Inventory / Production Rate**

Reactor inventory is obtained from:

- `330-WIC3201`

Crystallizer and preheater inventory is:

- Crystallizer = 6.25 tons
- Preheater = 65 tons
- Combined = 71.25 tons

Therefore:

**Crystallizer + Preheater Residence Time = 71.25 / Production Rate**

The total Pre-Silo residence time is the sum of reactor and crystallizer/preheater residence times.

## Model

The deployed model bundle contains the trained machine-learning models and the final feature list.

The application uses **ExtraTrees** as the primary model when it is available in the model bundle. Other available models are also evaluated and shown for comparison.

### Version

**SSP3_PRE_SILO_V1.1**

### Final Live Features

The deployed V1.1 model expects the following 11 features:

1. `Production_Rate_TPH__max`
2. `330-TI3204__mean`
3. `330-TI3203__mean`
4. `330-TI3202__mean`
5. `Production_Rate_TPH__mean`
6. `320-TIC2132__max`
7. `Production_Rate_TPH__std`
8. `Cryst_Preheater_Residence_hr__mean`
9. `Reactor_Residence_hr__mean`
10. `310-TIC1056__max`
11. `Feed_IV`

The application verifies that all required model features are available before making a prediction.

## Application Features

- Excel DCS upload
- Manual Feed IV input
- Manual Reactor Exit / Pre-Silo date and time
- Automatic production-rate calculation
- Automatic residence-time calculation
- Automatic process-window calculation
- Strict cutoff at the selected exit time
- Multi-model prediction comparison
- Exact model-input inspection
- Process-window diagnostics
- DCS/process calculation diagnostics
- CSV download of model input
- New Prediction / reset workflow

## Project Structure

A recommended deployment structure is:

```text
SSP3-PreSilo-IV-Predictor/
├── app.py
├── requirements.txt
├── README.md
└── models/
    └── SSP3_PRE_SILO_V1_1_MODEL.joblib
```

If the model file is kept in the project root instead, the application can be configured to use the corresponding model path.

## Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd SSP3-PreSilo-IV-Predictor
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

The application will normally open at:

```text
http://localhost:8501
```

## Deployment

The application can be deployed using **Streamlit Community Cloud** from a GitHub repository.

Typical deployment configuration:

- Repository: your GitHub repository
- Branch: the branch containing `app.py`
- Main file: `app.py`

Make sure the model file is included in the repository or is otherwise made available to the application.

## Model File Configuration

By default, the application can load the model file from the project directory.

If the application uses the `SSP_MODEL_FILE` environment variable, it can be used to specify an alternative model path.

Example:

```text
SSP_MODEL_FILE=/path/to/model.joblib
```

## Important Data & Security Notes

Do **not** commit confidential plant information to a public repository.

In particular, do not upload:

- Raw plant DCS data
- Production logs
- Lab records
- Credentials or passwords
- API keys
- Internal company documents
- Other confidential or proprietary information

For an industrial/company deployment, use an appropriate private repository and access controls according to your organization's policies.

## Data Leakage Prevention

A key design rule of this application is that DCS data after the selected prediction time must not be used.

The application therefore:

- Filters DCS data at the selected exit timestamp.
- Uses only readings available at or before that timestamp.
- Calculates the process window backward from the prediction point.
- Does not require the future laboratory IV value for live prediction.

This is important for making the soft-sensor prediction representative of a real-time deployment scenario.

## Troubleshooting

### Model file not found

Verify that the `.joblib` model file exists in the expected location and that the filename/path configured in the application is correct.

### Missing DCS tags

Verify that the uploaded Excel file contains the required process tags and the `TIME STAMP` column.

### Exit time outside the DCS range

Select a Reactor Exit / Pre-Silo time that falls within the timestamps available in the uploaded DCS file.

### Prediction cannot be generated

Check:

- Feed IV is valid and greater than zero.
- Required DCS tags are present.
- DCS timestamps are valid.
- The selected exit time is within the DCS data range.
- The calculated process window contains sufficient valid data.
- All 11 trained model features can be generated.

## Technology Stack

- Python
- Streamlit
- Pandas
- NumPy
- Scikit-learn
- CatBoost
- Joblib
- OpenPyXL

## Intended Use

This application is a **soft-sensor / decision-support tool** for estimating SSP-III Pre-Silo IV from process measurements.

Predictions should be evaluated and validated against plant laboratory measurements and process-team requirements before being used for operational decision-making.

## Version

**SSP3 Pre-Silo IV Predictor — V1.1**
