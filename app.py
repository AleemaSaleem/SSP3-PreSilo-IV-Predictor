# # ================================================================
# # SSP-III PRE-SILO V1.1
# # STREAMLIT LIVE IV PREDICTION APPLICATION
# #
# # USER INPUT:
# #   1. DCS Excel file
# #   2. Manual Feed IV from plant logbook
# #   3. Reactor Exit / Pre-Silo Date
# #   4. Reactor Exit / Pre-Silo Time
# #
# # OUTPUT:
# #   Predicted Pre-Silo IV
# #
# # IMPORTANT:
# #   - No Actual Lab IV input
# #   - Feed IV is entered manually
# #   - Exit time is entered manually
# #   - NO DCS processing occurs before Predict is clicked
# #   - NO model prediction occurs before Predict is clicked
# #   - Only DCS data <= selected exit time is used
# #   - Post-exit DCS data is NEVER used
# #   - Process window is automatically calculated
# #   - Feature order comes from saved Joblib model
# # ================================================================

# import os
# from pathlib import Path

# import joblib
# import numpy as np
# import pandas as pd
# import streamlit as st


# # ================================================================
# # PAGE CONFIGURATION
# # ================================================================

# st.set_page_config(
#     page_title="SSP-III Pre-Silo IV Predictor",
#     page_icon="🧪",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # ================================================================
# # SESSION STATE
# # ================================================================

# if "prediction_result" not in st.session_state:
#     st.session_state.prediction_result = None

# if "prediction_done" not in st.session_state:
#     st.session_state.prediction_done = False

# # ================================================================
# # CUSTOM CSS
# # ================================================================

# st.markdown(
#     """
#     <style>

#     .main-title {
#         font-size: 32px;
#         font-weight: 700;
#         color: #123B63;
#         margin-bottom: 5px;
#     }

#     .sub-title {
#         font-size: 17px;
#         color: #5B6573;
#         margin-bottom: 25px;
#     }

#     .prediction-box {
#         padding: 25px;
#         border-radius: 12px;
#         border: 2px solid #123B63;
#         text-align: center;
#         margin-top: 15px;
#         margin-bottom: 20px;
#     }

#     .prediction-label {
#         font-size: 18px;
#         font-weight: 600;
#         color: #5B6573;
#     }

#     .prediction-value {
#         font-size: 48px;
#         font-weight: 800;
#         color: #123B63;
#     }

#     .section-title {
#         font-size: 21px;
#         font-weight: 700;
#         color: #123B63;
#         margin-top: 20px;
#         margin-bottom: 10px;
#     }

#     .info-box {
#         padding: 15px;
#         border-radius: 8px;
#         background-color: #F4F7FA;
#         border-left: 5px solid #123B63;
#         margin-bottom: 15px;
#     }

#     </style>
#     """,
#     unsafe_allow_html=True,
# )


# # ================================================================
# # APPLICATION TITLE
# # ================================================================

# st.markdown(
#     '<div class="main-title">SSP-III Pre-Silo IV Predictor</div>',
#     unsafe_allow_html=True,
# )

# st.markdown(
#     '<div class="sub-title">'
#     'SSP-III Polymer Intrinsic Viscosity Prediction — V1.1'
#     '</div>',
#     unsafe_allow_html=True,
# )


# # ================================================================
# # MODEL FILE
# # ================================================================

# BASE_DIR = Path(__file__).resolve().parent

# MODEL_FILE = Path(
#     os.environ.get(
#         "SSP_MODEL_FILE",
#         str(
#             BASE_DIR
#             / "SSP3_PRE_SILO_V1_1_TUNING_CHECKPOINT (1).joblib"
#         ),
#     )
# )


# # ================================================================
# # TRAINING / PROCESS CONFIGURATION
# # ================================================================

# RPM_TO_TPH = 2.196

# # Crystallizer = 6.25 ton
# # Preheater = 65 ton
# PRE_REACTOR_INVENTORY_TON = 6.25 + 65.0

# TIME_COL = "TIME_STAMP"

# REACTOR_INVENTORY_TAG = "330-WIC3201"

# ROTARY_1_TAG = "325-HC2571"

# ROTARY_2_TAG = "325-HC2591"

# MAX_REASONABLE_REACTOR_RT_HR = 40

# MAX_REASONABLE_TOTAL_RT_HR = 60

# MAX_ENTRY_ITERATIONS = 8

# ENTRY_TIME_TOLERANCE_MIN = 5


# # ================================================================
# # LOAD MODEL BUNDLE
# #
# # IMPORTANT:
# # This only LOADS the trained model.
# # It does NOT read the DCS file.
# # It does NOT calculate features.
# # It does NOT call model.predict().
# # ================================================================

# @st.cache_resource
# def load_model_bundle(model_file):

#     model_file = Path(model_file)

#     if not model_file.exists():

#         raise FileNotFoundError(
#             f"Model file not found:\n{model_file}"
#         )

#     bundle = joblib.load(
#         model_file
#     )

#     if not isinstance(bundle, dict):

#         raise TypeError(
#             "The Joblib file is not a dictionary deployment bundle."
#         )

#     if "models" not in bundle:

#         raise KeyError(
#             "Saved Joblib bundle does not contain 'models'."
#         )

#     if (
#         "FINAL_FEATURES" not in bundle
#         and "features" not in bundle
#     ):

#         raise KeyError(
#             "Saved Joblib bundle does not contain "
#             "'FINAL_FEATURES' or 'features'."
#         )

#     return bundle


# # ================================================================
# # LOAD MODEL
# # ================================================================

# try:

#     deployment_bundle = load_model_bundle(
#         MODEL_FILE
#     )

# except Exception as e:

#     st.error(
#         "Unable to load the trained model."
#     )

#     st.code(
#         str(e)
#     )

#     st.info(
#         "Make sure the Joblib model is in the same folder "
#         "as app.py or set SSP_MODEL_FILE."
#     )

#     st.stop()


# # ================================================================
# # EXTRACT MODELS
# # ================================================================

# MODELS = deployment_bundle[
#     "models"
# ]


# FINAL_FEATURES_LIVE = deployment_bundle.get(
#     "FINAL_FEATURES",
#     deployment_bundle.get(
#         "features",
#         []
#     ),
# )


# if not MODELS:

#     st.error(
#         "No trained models were found in the Joblib bundle."
#     )

#     st.stop()


# if not FINAL_FEATURES_LIVE:

#     st.error(
#         "No trained model features were found in the Joblib bundle."
#     )

#     st.stop()


# # ================================================================
# # PRIMARY MODEL
# # ================================================================

# if "ExtraTrees" in MODELS:

#     PRIMARY_MODEL_NAME = "ExtraTrees"

# else:

#     PRIMARY_MODEL_NAME = list(
#         MODELS.keys()
#     )[0]


# PRIMARY_MODEL = MODELS[
#     PRIMARY_MODEL_NAME
# ]


# # ================================================================
# # SIDEBAR — MODEL INFORMATION
# # ================================================================

# with st.sidebar:

#     st.header(
#         "Model Information"
#     )

#     model_display_name = deployment_bundle.get(
#         "model_name",
#         "SSP-III Pre-Silo Model"
#     )

#     model_version = deployment_bundle.get(
#         "version",
#         "SSP3_PRE_SILO_V1.1"
#     )

#     st.write(
#         f"**Model:** {model_display_name}"
#     )

#     st.write(
#         f"**Version:** {model_version}"
#     )

#     st.write(
#         "**Prediction Point:** "
#         "Reactor Outlet / Pre-Silo"
#     )

#     st.write(
#         f"**Primary Model:** {PRIMARY_MODEL_NAME}"
#     )

#     st.divider()

#     st.subheader(
#         "Available Models"
#     )

#     for name in MODELS:

#         st.write(
#             f"• {name}"
#         )

#     st.divider()

#     st.subheader(
#         "Model Features"
#     )

#     st.write(
#         f"{len(FINAL_FEATURES_LIVE)} features"
#     )

#     st.divider()

#     st.caption(
#         "Model loading occurs when the application starts. "
#         "DCS processing and prediction occur only after "
#         "the Predict button is pressed."
#     )


# # ================================================================
# # INPUT SECTION
# # ================================================================

# st.markdown(
#     '<div class="section-title">'
#     '1. Prediction Inputs'
#     '</div>',
#     unsafe_allow_html=True,
# )


# col1, col2 = st.columns(
#     [1.5, 1]
# )


# with col1:

#     uploaded_file = st.file_uploader(
#         "Upload DCS Excel File",
#         type=[
#             "xlsx",
#             "xls"
#         ],
#         help=(
#             "Upload the SSP-III DCS data containing the "
#             "process history required for prediction."
#         ),
#     )


# with col2:

#     manual_feed_iv = st.number_input(
#         "Feed IV (Manual Logbook)",
#         min_value=0.0,
#         max_value=2.0,
#         value=0.606,
#         step=0.001,
#         format="%.3f",
#         help=(
#             "Enter the Feed IV manually from the "
#             "plant logbook."
#         ),
#     )


# # ================================================================
# # EXIT DATE / TIME
# # ================================================================

# st.markdown(
#     '<div class="section-title">'
#     '2. Reactor Exit / Pre-Silo Sample Time'
#     '</div>',
#     unsafe_allow_html=True,
# )


# date_col, time_col_ui = st.columns(
#     2
# )


# with date_col:

#     exit_date = st.date_input(
#         "Exit Date"
#     )


# with time_col_ui:

#     exit_time = st.time_input(
#         "Exit Time"
#     )


# # ================================================================
# # PREDICT BUTTON
# # ================================================================

# st.divider()


# run_prediction_button = st.button(
#     "🔬 Predict Pre-Silo IV",
#     type="primary",
#     use_container_width=True,
# )


# # ================================================================
# # HELPER FUNCTION
# # ================================================================

# def get_tag_type(tag):

#     t = str(tag).upper()

#     if "-TIC" in t or "-TI" in t:

#         return "TEMPERATURE"

#     if (
#         "-PDIC" in t
#         or "-PDI" in t
#         or "-PI" in t
#     ):

#         return "PRESSURE"

#     if "-FIC" in t or "-FI" in t:

#         return "FLOW"

#     if "-LIC" in t or "-LI" in t:

#         return "LEVEL"

#     return "OTHER"


# # ================================================================
# # DCS EXCEL READER
# # ================================================================

# def read_dcs_excel(
#     uploaded_file
# ):

#     # ------------------------------------------------------------
#     # Read workbook
#     # ------------------------------------------------------------

#     raw_dcs = pd.read_excel(
#         uploaded_file,
#         header=None
#     )


#     # ------------------------------------------------------------
#     # Detect TIME STAMP header row
#     # ------------------------------------------------------------

#     header_row = None


#     for r in range(
#         min(
#             20,
#             len(raw_dcs)
#         )
#     ):

#         row_values = (

#             raw_dcs
#             .iloc[r]
#             .astype(str)
#             .str.strip()
#             .str.upper()
#             .tolist()

#         )


#         if "TIME STAMP" in row_values:

#             header_row = r

#             break


#     if header_row is None:

#         raise ValueError(
#             "Could not find 'TIME STAMP' row in DCS Excel file."
#         )


#     # ------------------------------------------------------------
#     # Extract column names
#     # ------------------------------------------------------------

#     tags = (

#         raw_dcs
#         .iloc[header_row]
#         .astype(str)
#         .str.strip()
#         .tolist()

#     )


#     time_position = tags.index(
#         "TIME STAMP"
#     )


#     tags[
#         time_position
#     ] = TIME_COL


#     clean_tags = []


#     for i, tag in enumerate(tags):

#         tag = str(tag).strip()


#         if (
#             tag == ""
#             or tag.lower() == "nan"
#         ):

#             tag = f"UNNAMED_{i}"


#         clean_tags.append(
#             tag
#         )


#     # ------------------------------------------------------------
#     # Data begins two rows after header
#     # ------------------------------------------------------------

#     data_start_row = (
#         header_row + 2
#     )


#     dcs_df = raw_dcs.iloc[
#         data_start_row:
#     ].copy()


#     dcs_df.columns = clean_tags


#     # ------------------------------------------------------------
#     # Remove duplicate columns
#     # ------------------------------------------------------------

#     dcs_df = dcs_df.loc[
#         :,
#         ~dcs_df.columns.duplicated(
#             keep="first"
#         )
#     ].copy()


#     # ------------------------------------------------------------
#     # Timestamp
#     # ------------------------------------------------------------

#     dcs_df[
#         TIME_COL
#     ] = pd.to_datetime(
#         dcs_df[
#             TIME_COL
#         ],
#         errors="coerce"
#     )


#     # ------------------------------------------------------------
#     # Clean rows
#     # ------------------------------------------------------------

#     dcs_df = (

#         dcs_df

#         .dropna(
#             subset=[
#                 TIME_COL
#             ]
#         )

#         .sort_values(
#             TIME_COL
#         )

#         .drop_duplicates(
#             subset=[
#                 TIME_COL
#             ]
#         )

#         .reset_index(
#             drop=True
#         )

#     )


#     if dcs_df.empty:

#         raise ValueError(
#             "No valid timestamped DCS records were found."
#         )


#     # ------------------------------------------------------------
#     # Convert process columns to numeric
#     # ------------------------------------------------------------

#     for col in dcs_df.columns:

#         if col == TIME_COL:

#             continue


#         dcs_df[
#             col
#         ] = pd.to_numeric(
#             dcs_df[col],
#             errors="coerce"
#         )


#     return dcs_df


# # ================================================================
# # PRODUCTION + RESIDENCE CALCULATIONS
# # ================================================================

# def calculate_process_columns(
#     dcs_df
# ):

#     # ------------------------------------------------------------
#     # Rotary values
#     # ------------------------------------------------------------

#     r1 = pd.to_numeric(
#         dcs_df[
#             ROTARY_1_TAG
#         ],
#         errors="coerce"
#     )


#     r2 = pd.to_numeric(
#         dcs_df[
#             ROTARY_2_TAG
#         ],
#         errors="coerce"
#     )


#     # ------------------------------------------------------------
#     # Operating logic
#     #
#     # Positive = running
#     # Negative / zero = not running
#     # ------------------------------------------------------------

#     r1_positive = r1.where(
#         r1 > 0,
#         0
#     )


#     r2_positive = r2.where(
#         r2 > 0,
#         0
#     )


#     # ------------------------------------------------------------
#     # Active rotary
#     # ------------------------------------------------------------

#     dcs_df[
#         "Active_Rotary_RPM"
#     ] = np.maximum(
#         r1_positive,
#         r2_positive
#     )


#     # ------------------------------------------------------------
#     # RPM → TPH
#     # ------------------------------------------------------------

#     dcs_df[
#         "Production_Rate_TPH"
#     ] = (

#         dcs_df[
#             "Active_Rotary_RPM"
#         ]

#         *

#         RPM_TO_TPH

#     )


#     # ------------------------------------------------------------
#     # Running status
#     # ------------------------------------------------------------

#     dcs_df[
#         "Production_Running"
#     ] = (

#         dcs_df[
#             "Active_Rotary_RPM"
#         ]

#         > 0

#     )


#     # ------------------------------------------------------------
#     # Minimum valid production
#     # ------------------------------------------------------------

#     if (
#         "minimum_valid_production_tph"
#         in deployment_bundle
#     ):

#         min_valid_production_tph = float(

#             deployment_bundle[
#                 "minimum_valid_production_tph"
#             ]

#         )

#     else:

#         positive_prod = (

#             dcs_df.loc[
#                 dcs_df[
#                     "Production_Rate_TPH"
#                 ] > 0,

#                 "Production_Rate_TPH"
#             ]

#             .dropna()

#         )


#         if positive_prod.empty:

#             raise ValueError(
#                 "No positive production values were found "
#                 "in the DCS data."
#             )


#         min_valid_production_tph = float(
#             positive_prod.quantile(
#                 0.05
#             )
#         )


#     # ------------------------------------------------------------
#     # Production used for residence calculation
#     # ------------------------------------------------------------

#     dcs_df[
#         "Residence_Production_TPH"
#     ] = (

#         dcs_df[
#             "Production_Rate_TPH"
#         ]

#         .where(

#             dcs_df[
#                 "Production_Rate_TPH"
#             ]

#             >=

#             min_valid_production_tph

#         )

#     )


#     # ------------------------------------------------------------
#     # Reactor inventory
#     # ------------------------------------------------------------

#     inventory = pd.to_numeric(
#         dcs_df[
#             REACTOR_INVENTORY_TAG
#         ],
#         errors="coerce"
#     )


#     # ------------------------------------------------------------
#     # Reactor residence time
#     #
#     # Residence = Inventory / Production
#     # ------------------------------------------------------------

#     dcs_df[
#         "Reactor_Residence_hr_Instant"
#     ] = (

#         inventory

#         /

#         dcs_df[
#             "Residence_Production_TPH"
#         ]

#     )


#     # ------------------------------------------------------------
#     # Crystallizer + Preheater residence
#     # ------------------------------------------------------------

#     dcs_df[
#         "Cryst_Preheater_Residence_hr_Instant"
#     ] = (

#         PRE_REACTOR_INVENTORY_TON

#         /

#         dcs_df[
#             "Residence_Production_TPH"
#         ]

#     )


#     # ------------------------------------------------------------
#     # Total residence
#     # ------------------------------------------------------------

#     dcs_df[
#         "Total_PreSilo_RT_hr_Instant"
#     ] = (

#         dcs_df[
#             "Reactor_Residence_hr_Instant"
#         ]

#         +

#         dcs_df[
#             "Cryst_Preheater_Residence_hr_Instant"
#         ]

#     )


#     # ------------------------------------------------------------
#     # Remove impossible reactor residence
#     # ------------------------------------------------------------

#     invalid_reactor_rt = (

#         (

#             dcs_df[
#                 "Reactor_Residence_hr_Instant"
#             ]

#             <= 0

#         )

#         |

#         (

#             dcs_df[
#                 "Reactor_Residence_hr_Instant"
#             ]

#             >

#             MAX_REASONABLE_REACTOR_RT_HR

#         )

#     )


#     dcs_df.loc[
#         invalid_reactor_rt,
#         "Reactor_Residence_hr_Instant"
#     ] = np.nan


#     # ------------------------------------------------------------
#     # Remove impossible total residence
#     # ------------------------------------------------------------

#     invalid_total_rt = (

#         (

#             dcs_df[
#                 "Total_PreSilo_RT_hr_Instant"
#             ]

#             <= 0

#         )

#         |

#         (

#             dcs_df[
#                 "Total_PreSilo_RT_hr_Instant"
#             ]

#             >

#             MAX_REASONABLE_TOTAL_RT_HR

#         )

#     )


#     dcs_df.loc[
#         invalid_total_rt,
#         "Total_PreSilo_RT_hr_Instant"
#     ] = np.nan


#     return (
#         dcs_df,
#         min_valid_production_tph
#     )


# # ================================================================
# # FEATURE ENGINEERING
# # ================================================================

# def summarize_presilo_window(
#     window,
#     process_tags
# ):

#     features = {}


#     # ============================================================
#     # RAW PROCESS TAG FEATURES
#     # ============================================================

#     for tag in process_tags:

#         s = pd.to_numeric(
#             window[tag],
#             errors="coerce"
#         ).dropna()


#         if s.empty:

#             continue


#         tag_type = get_tag_type(
#             tag
#         )


#         # --------------------------------------------------------
#         # Mean
#         # --------------------------------------------------------

#         features[
#             f"{tag}__mean"
#         ] = float(
#             s.mean()
#         )


#         # --------------------------------------------------------
#         # Standard deviation
#         # --------------------------------------------------------

#         if tag_type in [

#             "TEMPERATURE",
#             "PRESSURE",
#             "FLOW"

#         ]:

#             features[
#                 f"{tag}__std"
#             ] = float(
#                 s.std(
#                     ddof=0
#                 )
#             )


#         # --------------------------------------------------------
#         # Temperature min/max
#         # --------------------------------------------------------

#         if tag_type == "TEMPERATURE":

#             features[
#                 f"{tag}__min"
#             ] = float(
#                 s.min()
#             )


#             features[
#                 f"{tag}__max"
#             ] = float(
#                 s.max()
#             )


#     # ============================================================
#     # PRODUCTION FEATURES
#     # ============================================================

#     p = pd.to_numeric(

#         window[
#             "Residence_Production_TPH"
#         ],

#         errors="coerce"

#     ).dropna()


#     if not p.empty:

#         features[
#             "Production_Rate_TPH__mean"
#         ] = float(
#             p.mean()
#         )


#         features[
#             "Production_Rate_TPH__std"
#         ] = float(
#             p.std(
#                 ddof=0
#             )
#         )


#         features[
#             "Production_Rate_TPH__min"
#         ] = float(
#             p.min()
#         )


#         features[
#             "Production_Rate_TPH__max"
#         ] = float(
#             p.max()
#         )


#     # ============================================================
#     # REACTOR RESIDENCE
#     # ============================================================

#     r = pd.to_numeric(

#         window[
#             "Reactor_Residence_hr_Instant"
#         ],

#         errors="coerce"

#     ).dropna()


#     if not r.empty:

#         features[
#             "Reactor_Residence_hr__mean"
#         ] = float(
#             r.mean()
#         )


#         features[
#             "Reactor_Residence_hr__std"
#         ] = float(
#             r.std(
#                 ddof=0
#             )
#         )


#     # ============================================================
#     # CRYSTALLIZER + PREHEATER RESIDENCE
#     # ============================================================

#     cp = pd.to_numeric(

#         window[
#             "Cryst_Preheater_Residence_hr_Instant"
#         ],

#         errors="coerce"

#     ).dropna()


#     if not cp.empty:

#         features[
#             "Cryst_Preheater_Residence_hr__mean"
#         ] = float(
#             cp.mean()
#         )


#     # ============================================================
#     # WINDOW QUALITY
#     # ============================================================

#     features[
#         "Window_Readings"
#     ] = int(
#         len(window)
#     )


#     features[
#         "Valid_Production_Percent"
#     ] = float(

#         window[
#             "Residence_Production_TPH"
#         ]

#         .notna()

#         .mean()

#         *

#         100

#     )


#     features[
#         "Rotary_Positive_Percent"
#     ] = float(

#         window[
#             "Production_Running"
#         ]

#         .fillna(False)

#         .mean()

#         *

#         100

#     )


#     return features


# # ================================================================
# # MAIN PREDICTION FUNCTION
# #
# # THIS FUNCTION IS NOT CALLED UNTIL THE BUTTON IS PRESSED.
# # ================================================================

# def run_prediction(
#     uploaded_file,
#     manual_feed_iv,
#     exit_date,
#     exit_time
# ):

#     # ============================================================
#     # 1. VALIDATE FEED IV
#     # ============================================================

#     if not np.isfinite(
#         manual_feed_iv
#     ):

#         raise ValueError(
#             "Feed IV must be a valid numeric value."
#         )


#     if manual_feed_iv <= 0:

#         raise ValueError(
#             "Feed IV must be greater than zero."
#         )


#     # ============================================================
#     # 2. CREATE EXIT TIMESTAMP
#     # ============================================================

#     manual_exit_string = (
#         f"{exit_date} {exit_time}"
#     )


#     reactor_exit_time = pd.to_datetime(
#         manual_exit_string,
#         errors="coerce"
#     )


#     if pd.isna(
#         reactor_exit_time
#     ):

#         raise ValueError(
#             "Invalid Reactor Exit Date / Time."
#         )


#     # ============================================================
#     # 3. READ DCS EXCEL
#     # ============================================================

#     raw_dcs = read_dcs_excel(
#         uploaded_file
#     )


#     # ============================================================
#     # 4. REQUIRED RAW TAGS
#     # ============================================================

#     required_tags = [

#         ROTARY_1_TAG,

#         ROTARY_2_TAG,

#         REACTOR_INVENTORY_TAG,

#         "330-TI3202",

#         "330-TI3203",

#         "330-TI3204",

#         "320-TIC2132",

#     ]


#     missing_tags = [

#         tag

#         for tag in required_tags

#         if tag not in raw_dcs.columns

#     ]


#     if missing_tags:

#         raise ValueError(

#             "Missing required DCS tags:\n\n"

#             +

#             "\n".join(

#                 f"• {tag}"

#                 for tag in missing_tags

#             )

#         )


#     # ============================================================
#     # 5. CALCULATE PROCESS COLUMNS
#     # ============================================================

#     dcs_df, min_valid_production_tph = (
#         calculate_process_columns(
#             raw_dcs
#         )
#     )


#     # ============================================================
#     # 6. DCS TIME RANGE
#     # ============================================================

#     dcs_start = dcs_df[
#         TIME_COL
#     ].min()


#     dcs_end = dcs_df[
#         TIME_COL
#     ].max()


#     # ============================================================
#     # 7. EXIT MUST BE INSIDE DCS RANGE
#     # ============================================================

#     if reactor_exit_time < dcs_start:

#         raise ValueError(

#             "Selected exit time is BEFORE the DCS chunk.\n\n"

#             f"Selected exit: {reactor_exit_time}\n"

#             f"DCS starts: {dcs_start}\n\n"

#             "Please select an exit time inside the "
#             "uploaded DCS period."

#         )


#     if reactor_exit_time > dcs_end:

#         raise ValueError(

#             "Selected exit time is AFTER the DCS chunk.\n\n"

#             f"Selected exit: {reactor_exit_time}\n"

#             f"DCS ends: {dcs_end}\n\n"

#             "Upload a DCS chunk containing data up to "
#             "the selected exit time."

#         )


#     # ============================================================
#     # 8. ONLY DATA UP TO EXIT TIME
#     # ============================================================

#     dcs_until_exit = dcs_df.loc[

#         dcs_df[
#             TIME_COL
#         ]

#         <=

#         reactor_exit_time

#     ].copy()


#     if dcs_until_exit.empty:

#         raise ValueError(
#             "No DCS readings exist before the selected "
#             "exit time."
#         )


#     # ============================================================
#     # 9. FIND NEAREST DCS READING TO EXIT
#     # ============================================================

#     nearest_position = (

#         dcs_until_exit[
#             TIME_COL
#         ]

#         .sub(
#             reactor_exit_time
#         )

#         .abs()

#         .idxmin()

#     )


#     nearest_exit_row = (
#         dcs_until_exit.loc[
#             nearest_position
#         ]
#     )


#     nearest_dcs_exit_time = (
#         nearest_exit_row[
#             TIME_COL
#         ]
#     )


#     exit_difference_min = (

#         abs(

#             (
#                 reactor_exit_time
#                 -
#                 nearest_dcs_exit_time
#             ).total_seconds()

#         )

#         /

#         60.0

#     )


#     # ============================================================
#     # 10. INITIAL RESIDENCE TIME
#     # ============================================================

#     initial_rt = nearest_exit_row[
#         "Total_PreSilo_RT_hr_Instant"
#     ]


#     if (

#         pd.isna(initial_rt)

#         or initial_rt <= 0

#         or initial_rt > MAX_REASONABLE_TOTAL_RT_HR

#     ):

#         raise ValueError(

#             "Invalid residence time at the selected "
#             "exit time.\n\n"

#             f"Residence time: {initial_rt}\n\n"

#             "Check reactor inventory and production rate "
#             "around the selected exit time."

#         )


#     # ============================================================
#     # 11. INITIAL ENTRY TIME
#     # ============================================================

#     entry_time = (

#         reactor_exit_time

#         -

#         pd.Timedelta(
#             hours=float(
#                 initial_rt
#             )
#         )

#     )


#     # ============================================================
#     # 12. ITERATIVE ENTRY-TIME REFINEMENT
#     # ============================================================

#     iterations_used = 0


#     for iteration in range(
#         1,
#         MAX_ENTRY_ITERATIONS + 1
#     ):

#         iterations_used = iteration


#         current_window = dcs_df.loc[

#             (

#                 dcs_df[
#                     TIME_COL
#                 ]

#                 >=

#                 entry_time

#             )

#             &

#             (

#                 dcs_df[
#                     TIME_COL
#                 ]

#                 <=

#                 reactor_exit_time

#             )

#         ].copy()


#         if len(
#             current_window
#         ) < 3:

#             raise ValueError(

#                 f"Iteration {iteration}: "
#                 "fewer than 3 DCS readings inside "
#                 "the calculated process window."

#             )


#         # --------------------------------------------------------
#         # Production
#         # --------------------------------------------------------

#         production_series = pd.to_numeric(

#             current_window[
#                 "Residence_Production_TPH"
#             ],

#             errors="coerce"

#         ).dropna()


#         # --------------------------------------------------------
#         # Inventory
#         # --------------------------------------------------------

#         inventory_series = pd.to_numeric(

#             current_window[
#                 REACTOR_INVENTORY_TAG
#             ],

#             errors="coerce"

#         ).dropna()


#         if production_series.empty:

#             raise ValueError(

#                 f"Iteration {iteration}: "
#                 "no valid production values."

#             )


#         if inventory_series.empty:

#             raise ValueError(

#                 f"Iteration {iteration}: "
#                 "no valid reactor inventory values."

#             )


#         # --------------------------------------------------------
#         # Average production
#         # --------------------------------------------------------

#         avg_production = float(
#             production_series.mean()
#         )


#         # --------------------------------------------------------
#         # Average reactor inventory
#         # --------------------------------------------------------

#         avg_inventory = float(
#             inventory_series.mean()
#         )


#         # --------------------------------------------------------
#         # Reactor residence
#         # --------------------------------------------------------

#         reactor_rt = (

#             avg_inventory
#             /
#             avg_production

#         )


#         # --------------------------------------------------------
#         # Crystallizer + preheater residence
#         # --------------------------------------------------------

#         crystallizer_preheater_rt = (

#             PRE_REACTOR_INVENTORY_TON
#             /
#             avg_production

#         )


#         # --------------------------------------------------------
#         # Total residence
#         # --------------------------------------------------------

#         total_rt = (

#             reactor_rt
#             +
#             crystallizer_preheater_rt

#         )


#         if (

#             not np.isfinite(
#                 total_rt
#             )

#             or total_rt <= 0

#             or total_rt > MAX_REASONABLE_TOTAL_RT_HR

#         ):

#             raise ValueError(

#                 f"Iteration {iteration}: "
#                 f"invalid total residence time "
#                 f"{total_rt:.4f} hr."

#             )


#         # --------------------------------------------------------
#         # Calculate new entry time
#         # --------------------------------------------------------

#         new_entry_time = (

#             reactor_exit_time

#             -

#             pd.Timedelta(
#                 hours=float(
#                     total_rt
#                 )
#             )

#         )


#         # --------------------------------------------------------
#         # Convergence
#         # --------------------------------------------------------

#         difference_minutes = (

#             abs(

#                 (
#                     new_entry_time
#                     -
#                     entry_time
#                 ).total_seconds()

#             )

#             /

#             60.0

#         )


#         entry_time = (
#             new_entry_time
#         )


#         if (

#             difference_minutes
#             <=
#             ENTRY_TIME_TOLERANCE_MIN

#         ):

#             break


#     # ============================================================
#     # 13. FINAL PROCESS WINDOW
#     # ============================================================

#     pre_silo_entry_time = (
#         entry_time
#     )


#     w = dcs_df.loc[

#         (

#             dcs_df[
#                 TIME_COL
#             ]

#             >=

#             pre_silo_entry_time

#         )

#         &

#         (

#             dcs_df[
#                 TIME_COL
#             ]

#             <=

#             reactor_exit_time

#         )

#     ].copy()


#     if len(w) < 3:

#         raise ValueError(

#             "Final process window contains fewer than "
#             "3 DCS readings."

#         )


#     # ============================================================
#     # 14. PROCESS TAG LIST
#     # ============================================================

#     exclude_raw_tags = {

#         TIME_COL,

#         "Active_Rotary_RPM",

#         "Production_Rate_TPH",

#         "Production_Running",

#         "Residence_Production_TPH",

#         "Reactor_Residence_hr_Instant",

#         "Cryst_Preheater_Residence_hr_Instant",

#         "Total_PreSilo_RT_hr_Instant",

#     }


#     silo_tags_to_exclude = {

#         "350-LI5111",

#         "350-LI5121",

#         "350-L15121",

#     }


#     process_tags = [

#         c

#         for c in dcs_df.columns

#         if c not in exclude_raw_tags

#         and c not in silo_tags_to_exclude

#     ]


#     # ============================================================
#     # 15. FEATURE ENGINEERING
#     # ============================================================

#     live_features = summarize_presilo_window(
#         w,
#         process_tags
#     )


#     # ============================================================
#     # 16. MANUAL FEED IV
#     # ============================================================

#     live_features[
#         "Feed_IV"
#     ] = float(
#         manual_feed_iv
#     )


#     # ============================================================
#     # 17. CHECK EXACT TRAINED FEATURES
#     # ============================================================

#     missing_features = [

#         feature

#         for feature in FINAL_FEATURES_LIVE

#         if feature not in live_features

#     ]


#     if missing_features:

#         raise ValueError(

#             "Live feature engineering is missing "
#             "trained model features:\n\n"

#             +

#             "\n".join(

#                 f"• {feature}"

#                 for feature in missing_features

#             )

#         )


#     # ============================================================
#     # 18. CREATE MODEL INPUT
#     # ============================================================

#     live_X = (

#         pd.DataFrame(
#             [live_features]
#         )

#         .reindex(
#             columns=FINAL_FEATURES_LIVE
#         )

#     )


#     # ============================================================
#     # 19. CHECK NaN / INF
#     # ============================================================

#     bad_columns = []


#     for col in live_X.columns:

#         value = live_X.iloc[
#             0
#         ][col]


#         if pd.isna(
#             value
#         ):

#             bad_columns.append(
#                 (
#                     col,
#                     "NaN"
#                 )
#             )


#         elif not np.isfinite(
#             float(value)
#         ):

#             bad_columns.append(
#                 (
#                     col,
#                     "Infinite"
#                 )
#             )


#     if bad_columns:

#         raise ValueError(

#             "Required model features contain invalid values:\n\n"

#             +

#             "\n".join(

#                 f"• {col}: {reason}"

#                 for col, reason in bad_columns

#             )

#         )


#     # ============================================================
#     # 20. MODEL PREDICTION
#     #
#     # THIS IS THE FIRST POINT WHERE model.predict() IS CALLED.
#     # ============================================================

#     predictions = {}


#     for model_name, model in MODELS.items():

#         predictions[
#             model_name
#         ] = float(

#             model.predict(
#                 live_X
#             )[0]

#         )


#     # ============================================================
#     # 21. PRIMARY PREDICTION
#     # ============================================================

#     primary_model = (
#         PRIMARY_MODEL_NAME
#     )


#     predicted_iv = float(
#         predictions[
#             primary_model
#         ]
#     )


#     # ============================================================
#     # 22. RETURN RESULT
#     # ============================================================

#     return {

#         "predicted_iv":
#             predicted_iv,

#         "primary_model":
#             primary_model,

#         "predictions":
#             predictions,

#         "manual_feed_iv":
#             float(
#                 manual_feed_iv
#             ),

#         "manual_exit_time":
#             reactor_exit_time,

#         "nearest_dcs_exit_time":
#             nearest_dcs_exit_time,

#         "nearest_exit_difference_min":
#             exit_difference_min,

#         "pre_silo_entry_time":
#             pre_silo_entry_time,

#         "window_duration_hr":
#             (

#                 reactor_exit_time
#                 -
#                 pre_silo_entry_time

#             ).total_seconds()
#             /
#             3600,

#         "window_readings":
#             len(w),

#         "dcs_rows":
#             len(dcs_df),

#         "dcs_start":
#             dcs_start,

#         "dcs_end":
#             dcs_end,

#         "min_valid_production_tph":
#             min_valid_production_tph,

#         "iterations":
#             iterations_used,

#         "average_production_tph":
#             avg_production,

#         "average_reactor_inventory_ton":
#             avg_inventory,

#         "reactor_residence_hr":
#             reactor_rt,

#         "cryst_preheater_residence_hr":
#             crystallizer_preheater_rt,

#         "total_residence_hr":
#             total_rt,

#         "live_X":
#             live_X,

#         "window":
#             w,

#         "dcs":
#             dcs_df,

#     }


# # ================================================================
# # BUTTON ACTION
# #
# # NOTHING BELOW THIS POINT RUNS AS A PREDICTION UNTIL THE BUTTON
# # IS PRESSED.
# # ================================================================

# if run_prediction_button:

#     # ============================================================
#     # 1. VALIDATE FILE
#     # ============================================================

#     if uploaded_file is None:

#         st.warning(
#             "Please upload the DCS Excel file before "
#             "running the prediction."
#         )

#         st.stop()


#     # ============================================================
#     # 2. VALIDATE FEED IV
#     # ============================================================

#     if (

#         not np.isfinite(
#             manual_feed_iv
#         )

#         or manual_feed_iv <= 0

#     ):

#         st.warning(
#             "Please enter a valid Feed IV greater than zero."
#         )

#         st.stop()


#     # ============================================================
#     # 3. RUN PREDICTION
#     # ============================================================

#     with st.spinner(
#         "Processing DCS data and calculating Pre-Silo IV..."
#     ):

#         try:

#             result = run_prediction(

#                 uploaded_file,

#                 manual_feed_iv,

#                 exit_date,

#                 exit_time

#             )


#         except Exception as e:

#             st.error(
#                 "Prediction failed."
#             )

#             st.exception(
#                 e
#             )

#             st.stop()


#     # ============================================================
#     # 4. SUCCESS
#     # ============================================================

#     st.success(
#         "Pre-Silo IV prediction completed successfully."
#     )


#     # ============================================================
#     # 5. MAIN PREDICTION
#     # ============================================================

#     st.markdown(
#         '<div class="prediction-box">',
#         unsafe_allow_html=True
#     )


#     st.markdown(
#         '<div class="prediction-label">'
#         'Predicted Pre-Silo IV'
#         '</div>',
#         unsafe_allow_html=True
#     )


#     st.markdown(
#         f'<div class="prediction-value">'
#         f'{result["predicted_iv"]:.4f}'
#         f'</div>',
#         unsafe_allow_html=True
#     )


#     st.markdown(
#         f'<div class="prediction-label">'
#         f'Model: {result["primary_model"]}'
#         f'</div>',
#         unsafe_allow_html=True
#     )


#     st.markdown(
#         '</div>',
#         unsafe_allow_html=True
#     )


#     # ============================================================
#     # 6. KEY INFORMATION
#     # ============================================================

#     st.markdown(
#         '<div class="section-title">'
#         'Prediction Information'
#         '</div>',
#         unsafe_allow_html=True
#     )


#     c1, c2, c3, c4 = st.columns(
#         4
#     )


#     with c1:

#         st.metric(
#             "Feed IV",
#             f'{result["manual_feed_iv"]:.4f}'
#         )


#     with c2:

#         st.metric(
#             "Process Window",
#             f'{result["window_duration_hr"]:.2f} hr'
#         )


#     with c3:

#         st.metric(
#             "DCS Readings Used",
#             result["window_readings"]
#         )


#     with c4:

#         st.metric(
#             "Model Features",
#             len(FINAL_FEATURES_LIVE)
#         )


#     # ============================================================
#     # 7. PROCESS CALCULATION INFORMATION
#     # ============================================================

#     st.markdown(
#         '<div class="section-title">'
#         'Process Calculation'
#         '</div>',
#         unsafe_allow_html=True
#     )


#     process_df = pd.DataFrame({

#         "Parameter": [

#             "Average Production Rate",

#             "Average Reactor Inventory",

#             "Reactor Residence Time",

#             "Crystallizer + Preheater Residence",

#             "Total Pre-Silo Residence",

#             "Entry-Time Iterations",

#         ],

#         "Value": [

#             f'{result["average_production_tph"]:.3f} TPH',

#             f'{result["average_reactor_inventory_ton"]:.3f} ton',

#             f'{result["reactor_residence_hr"]:.3f} hr',

#             f'{result["cryst_preheater_residence_hr"]:.3f} hr',

#             f'{result["total_residence_hr"]:.3f} hr',

#             result["iterations"],

#         ]

#     })


#     st.dataframe(
#         process_df,
#         use_container_width=True,
#         hide_index=True
#     )


#     # ============================================================
#     # 8. PROCESS TIMING
#     # ============================================================

#     st.markdown(
#         '<div class="section-title">'
#         'Process Timing'
#         '</div>',
#         unsafe_allow_html=True
#     )


#     timing_df = pd.DataFrame({

#         "Parameter": [

#             "DCS Start",

#             "DCS End",

#             "Manual Reactor Exit / Pre-Silo Time",

#             "Nearest DCS Exit Reading",

#             "Difference from DCS Exit Reading",

#             "Calculated Pre-Silo Entry Time",

#             "Process Window Duration",

#         ],

#         "Value": [

#             str(
#                 result["dcs_start"]
#             ),

#             str(
#                 result["dcs_end"]
#             ),

#             str(
#                 result["manual_exit_time"]
#             ),

#             str(
#                 result["nearest_dcs_exit_time"]
#             ),

#             f'{result["nearest_exit_difference_min"]:.2f} min',

#             str(
#                 result["pre_silo_entry_time"]
#             ),

#             f'{result["window_duration_hr"]:.3f} hr',

#         ]

#     })


#     st.dataframe(
#         timing_df,
#         use_container_width=True,
#         hide_index=True
#     )


#     # ============================================================
#     # 9. MODEL COMPARISON
#     # ============================================================

#     if len(
#         result["predictions"]
#     ) > 1:

#         st.markdown(
#             '<div class="section-title">'
#             'Model Predictions'
#             '</div>',
#             unsafe_allow_html=True
#         )


#         comparison_df = pd.DataFrame({

#             "Model":

#                 list(
#                     result[
#                         "predictions"
#                     ].keys()
#                 ),

#             "Predicted_PreSilo_IV":

#                 list(
#                     result[
#                         "predictions"
#                     ].values()
#                 ),

#         })


#         comparison_df[
#             "Predicted_PreSilo_IV"
#         ] = (

#             comparison_df[
#                 "Predicted_PreSilo_IV"
#             ]

#             .round(
#                 6
#             )

#         )


#         st.dataframe(
#             comparison_df,
#             use_container_width=True,
#             hide_index=True
#         )


#     # ============================================================
#     # 10. EXACT MODEL INPUT
#     # ============================================================

#     with st.expander(
#         "View Exact Model Input Features"
#     ):

#         st.caption(
#             "These are the exact features and values passed "
#             "to the trained model."
#         )


#         model_input_display = (

#             result[
#                 "live_X"
#             ]

#             .T

#             .rename(
#                 columns={
#                     0: "Value"
#                 }
#             )

#         )


#         st.dataframe(
#             model_input_display,
#             use_container_width=True
#         )


#     # ============================================================
#     # 11. PROCESS WINDOW
#     # ============================================================

#     with st.expander(
#         "View DCS Process Window Used for Prediction"
#     ):

#         st.write(
#             "Only readings from the calculated Pre-Silo "
#             "Entry Time through the manually selected "
#             "Reactor Exit Time were used."
#         )


#         st.dataframe(
#             result[
#                 "window"
#             ],
#             use_container_width=True,
#             hide_index=True
#         )


#     # ============================================================
#     # 12. DOWNLOAD MODEL INPUT
#     # ============================================================

#     model_input_download = (

#         result[
#             "live_X"
#         ]

#         .T

#         .rename(
#             columns={
#                 0: "Value"
#             }
#         )

#         .to_csv()

#     )


#     st.download_button(
#         "Download Model Input CSV",
#         data=model_input_download,
#         file_name="SSP3_PreSilo_Model_Input.csv",
#         mime="text/csv",
#     )


#     # ============================================================
#     # 13. FINAL STATUS
#     # ============================================================

#     st.divider()


#     st.success(
#         "Prediction complete. "
#         "No Actual Lab IV was used. "
#         "Post-exit DCS data was excluded."
#     )


# # ================================================================
# # INITIAL SCREEN
# #
# # This is displayed when Predict has NOT been pressed.
# # No DCS file processing occurs here.
# # ================================================================

# else:

#     st.markdown(
#         """
#         <div class="info-box">

#         <b>How to use the application</b>

#         <br><br>

#         <b>Step 1:</b> Upload the SSP-III DCS Excel chunk.

#         <br><br>

#         <b>Step 2:</b> Enter the current
#         <b>Feed IV</b> from the plant logbook.

#         <br><br>

#         <b>Step 3:</b> Select the actual
#         <b>Reactor Exit / Pre-Silo Sample Date and Time</b>.

#         <br><br>

#         <b>Step 4:</b> Click
#         <b>Predict Pre-Silo IV</b>.

#         <br><br>

#         The application will then:

#         <br>
#         • Read the DCS data
#         <br>
#         • Calculate production rate
#         <br>
#         • Calculate reactor residence time
#         <br>
#         • Calculate crystallizer/preheater residence time
#         <br>
#         • Calculate the upstream process window
#         <br>
#         • Generate the exact trained features
#         <br>
#         • Run the trained model
#         <br>
#         • Display the predicted Pre-Silo IV

#         <br><br>

#         <b>No Actual Lab IV is required.</b>

#         <br><br>

#         <b>No prediction is performed until the Predict button
#         is pressed.</b>

#         </div>
#         """,
#         unsafe_allow_html=True
#     )

# ================================================================
# SSP-III PRE-SILO V1.1
# STREAMLIT LIVE IV PREDICTION APPLICATION
#
# USER INPUT:
#   1. DCS Excel file
#   2. Manual Feed IV from plant logbook
#   3. Reactor Exit / Pre-Silo Date
#   4. Reactor Exit / Pre-Silo Time
#
# OUTPUT:
#   Predicted Pre-Silo IV
#
# IMPORTANT:
#   - No Actual Lab IV input
#   - Feed IV is entered manually
#   - Exit time is entered manually
#   - NO DCS processing occurs before Predict is clicked
#   - NO model prediction occurs before Predict is clicked
#   - Only DCS data <= selected exit time is used
#   - Post-exit DCS data is NEVER used
#   - Process window is automatically calculated
#   - Feature order comes from saved Joblib model
#   - Prediction survives Streamlit reruns
#   - Downloading CSV does NOT reset prediction
#   - New Prediction button completely resets the workflow
# ================================================================


import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st


# ================================================================
# PAGE CONFIGURATION
# ================================================================

st.set_page_config(
    page_title="SSP-III Pre-Silo IV Predictor",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ================================================================
# SESSION STATE
#
# IMPORTANT:
# Streamlit reruns the script when Download is clicked.
# Therefore the prediction result must live in session_state.
# ================================================================

if "prediction_result" not in st.session_state:
    st.session_state["prediction_result"] = None

if "prediction_done" not in st.session_state:
    st.session_state["prediction_done"] = False

if "widget_version" not in st.session_state:
    st.session_state["widget_version"] = 0


# ================================================================
# CUSTOM CSS
# ================================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 32px;
        font-weight: 700;
        color: #123B63;
        margin-bottom: 5px;
    }

    .sub-title {
        font-size: 17px;
        color: #5B6573;
        margin-bottom: 25px;
    }

    .prediction-box {
        padding: 25px;
        border-radius: 12px;
        border: 2px solid #123B63;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 20px;
    }

    .prediction-label {
        font-size: 18px;
        font-weight: 600;
        color: #5B6573;
    }

    .prediction-value {
        font-size: 48px;
        font-weight: 800;
        color: #123B63;
    }

    .section-title {
        font-size: 21px;
        font-weight: 700;
        color: #123B63;
        margin-top: 20px;
        margin-bottom: 10px;
    }

    .info-box {
        padding: 15px;
        border-radius: 8px;
        background-color: #F4F7FA;
        border-left: 5px solid #123B63;
        margin-bottom: 15px;
    }

    .reset-box {
        padding: 10px;
        border-radius: 8px;
        background-color: #FFF8E6;
        border-left: 5px solid #D99A00;
        margin-bottom: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ================================================================
# APPLICATION TITLE
# ================================================================

st.markdown(
    '<div class="main-title">SSP-III Pre-Silo IV Predictor</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-title">'
    'SSP-III Polymer Intrinsic Viscosity Prediction — V1.1'
    '</div>',
    unsafe_allow_html=True,
)


# ================================================================
# MODEL FILE
# ================================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_FILE = Path(
    os.environ.get(
        "SSP_MODEL_FILE",
        str(
            BASE_DIR
            / "SSP3_PRE_SILO_V1_1_TUNING_CHECKPOINT (1).joblib"
        ),
    )
)


# ================================================================
# TRAINING / PROCESS CONFIGURATION
# ================================================================

RPM_TO_TPH = 2.196

# Crystallizer = 6.25 ton
# Preheater = 65 ton
PRE_REACTOR_INVENTORY_TON = 6.25 + 65.0

TIME_COL = "TIME_STAMP"

REACTOR_INVENTORY_TAG = "330-WIC3201"

ROTARY_1_TAG = "325-HC2571"

ROTARY_2_TAG = "325-HC2591"

MAX_REASONABLE_REACTOR_RT_HR = 40

MAX_REASONABLE_TOTAL_RT_HR = 60

MAX_ENTRY_ITERATIONS = 8

ENTRY_TIME_TOLERANCE_MIN = 5


# ================================================================
# LOAD MODEL BUNDLE
#
# This only loads the trained model.
# It does NOT read DCS data.
# It does NOT calculate features.
# It does NOT call model.predict().
# ================================================================

@st.cache_resource
def load_model_bundle(model_file):

    model_file = Path(model_file)

    if not model_file.exists():

        raise FileNotFoundError(
            f"Model file not found:\n{model_file}"
        )

    bundle = joblib.load(
        model_file
    )

    if not isinstance(bundle, dict):

        raise TypeError(
            "The Joblib file is not a dictionary "
            "deployment bundle."
        )

    if "models" not in bundle:

        raise KeyError(
            "Saved Joblib bundle does not contain 'models'."
        )

    if (
        "FINAL_FEATURES" not in bundle
        and "features" not in bundle
    ):

        raise KeyError(
            "Saved Joblib bundle does not contain "
            "'FINAL_FEATURES' or 'features'."
        )

    return bundle


# ================================================================
# LOAD MODEL
# ================================================================

try:

    deployment_bundle = load_model_bundle(
        MODEL_FILE
    )

except Exception as e:

    st.error(
        "Unable to load the trained model."
    )

    st.code(
        str(e)
    )

    st.info(
        "Make sure the Joblib model is in the same folder "
        "as app.py or set SSP_MODEL_FILE."
    )

    st.stop()


# ================================================================
# EXTRACT MODELS
# ================================================================

MODELS = deployment_bundle[
    "models"
]


FINAL_FEATURES_LIVE = deployment_bundle.get(
    "FINAL_FEATURES",
    deployment_bundle.get(
        "features",
        []
    ),
)


if not MODELS:

    st.error(
        "No trained models were found in the Joblib bundle."
    )

    st.stop()


if not FINAL_FEATURES_LIVE:

    st.error(
        "No trained model features were found in "
        "the Joblib bundle."
    )

    st.stop()


# ================================================================
# PRIMARY MODEL
# ================================================================

if "ExtraTrees" in MODELS:

    PRIMARY_MODEL_NAME = "ExtraTrees"

else:

    PRIMARY_MODEL_NAME = list(
        MODELS.keys()
    )[0]


PRIMARY_MODEL = MODELS[
    PRIMARY_MODEL_NAME
]


# ================================================================
# SIDEBAR — MODEL INFORMATION
# ================================================================

with st.sidebar:

    st.header(
        "Model Information"
    )

    model_display_name = deployment_bundle.get(
        "model_name",
        "SSP-III Pre-Silo Model"
    )

    model_version = deployment_bundle.get(
        "version",
        "SSP3_PRE_SILO_V1.1"
    )

    st.write(
        f"**Model:** {model_display_name}"
    )

    st.write(
        f"**Version:** {model_version}"
    )

    st.write(
        "**Prediction Point:** "
        "Reactor Outlet / Pre-Silo"
    )

    st.write(
        f"**Primary Model:** {PRIMARY_MODEL_NAME}"
    )

    st.divider()

    st.subheader(
        "Available Models"
    )

    for name in MODELS:

        st.write(
            f"• {name}"
        )

    st.divider()

    st.subheader(
        "Model Features"
    )

    st.write(
        f"{len(FINAL_FEATURES_LIVE)} features"
    )

    st.divider()

    st.caption(
        "Model loading occurs when the application starts. "
        "DCS processing and prediction occur only after "
        "the Predict button is pressed."
    )


# ================================================================
# NEW PREDICTION / RESET BUTTON
#
# IMPORTANT:
# This button is placed BEFORE the input widgets.
# Therefore their session-state keys can safely be replaced
# by changing widget_version.
# ================================================================

reset_col1, reset_col2 = st.columns(
    [4, 1]
)


with reset_col2:

    new_prediction_button = st.button(
        "🔄 New Prediction",
        use_container_width=True,
        help=(
            "Clear the current prediction and all entered "
            "readings so a completely new prediction can be made."
        ),
    )


# ================================================================
# RESET WORKFLOW
# ================================================================

if new_prediction_button:

    # Clear prediction
    st.session_state["prediction_result"] = None

    st.session_state["prediction_done"] = False

    # Change widget namespace.
    # This forces Streamlit to create completely new widgets.
    st.session_state["widget_version"] += 1

    st.rerun()


# ================================================================
# CURRENT WIDGET VERSION
# ================================================================

widget_version = st.session_state[
    "widget_version"
]


# ================================================================
# INPUT SECTION
# ================================================================

st.markdown(
    '<div class="section-title">'
    '1. Prediction Inputs'
    '</div>',
    unsafe_allow_html=True,
)


col1, col2 = st.columns(
    [1.5, 1]
)


with col1:

    uploaded_file = st.file_uploader(
        "Upload DCS Excel File",
        type=[
            "xlsx",
            "xls"
        ],
        key=f"dcs_file_{widget_version}",
        help=(
            "Upload the SSP-III DCS data containing the "
            "process history required for prediction."
        ),
    )


with col2:

    manual_feed_iv = st.number_input(
        "Feed IV (Manual Logbook)",
        min_value=0.0,
        max_value=2.0,
        value=0.606,
        step=0.001,
        format="%.3f",
        key=f"feed_iv_{widget_version}",
        help=(
            "Enter the Feed IV manually from the "
            "plant logbook."
        ),
    )


# ================================================================
# EXIT DATE / TIME
# ================================================================

st.markdown(
    '<div class="section-title">'
    '2. Reactor Exit / Pre-Silo Sample Time'
    '</div>',
    unsafe_allow_html=True,
)


date_col, time_col_ui = st.columns(
    2
)


with date_col:

    exit_date = st.date_input(
        "Exit Date",
        key=f"exit_date_{widget_version}",
    )


with time_col_ui:

    exit_time = st.time_input(
        "Exit Time",
        key=f"exit_time_{widget_version}",
    )


# ================================================================
# PREDICT BUTTON
# ================================================================

st.divider()


run_prediction_button = st.button(
    "🔬 Predict Pre-Silo IV",
    type="primary",
    use_container_width=True,
    key=f"predict_button_{widget_version}",
)


# ================================================================
# HELPER FUNCTION
# ================================================================

def get_tag_type(tag):

    t = str(tag).upper()

    if "-TIC" in t or "-TI" in t:

        return "TEMPERATURE"

    if (
        "-PDIC" in t
        or "-PDI" in t
        or "-PI" in t
    ):

        return "PRESSURE"

    if "-FIC" in t or "-FI" in t:

        return "FLOW"

    if "-LIC" in t or "-LI" in t:

        return "LEVEL"

    return "OTHER"


# ================================================================
# DCS EXCEL READER
# ================================================================

def read_dcs_excel(
    uploaded_file
):

    # ------------------------------------------------------------
    # Read workbook
    # ------------------------------------------------------------

    raw_dcs = pd.read_excel(
        uploaded_file,
        header=None
    )


    # ------------------------------------------------------------
    # Detect TIME STAMP header row
    # ------------------------------------------------------------

    header_row = None


    for r in range(
        min(
            20,
            len(raw_dcs)
        )
    ):

        row_values = (

            raw_dcs
            .iloc[r]
            .astype(str)
            .str.strip()
            .str.upper()
            .tolist()

        )


        if "TIME STAMP" in row_values:

            header_row = r

            break


    if header_row is None:

        raise ValueError(
            "Could not find 'TIME STAMP' row "
            "in DCS Excel file."
        )


    # ------------------------------------------------------------
    # Extract column names
    # ------------------------------------------------------------

    tags = (

        raw_dcs
        .iloc[header_row]
        .astype(str)
        .str.strip()
        .tolist()

    )


    time_position = tags.index(
        "TIME STAMP"
    )


    tags[
        time_position
    ] = TIME_COL


    clean_tags = []


    for i, tag in enumerate(tags):

        tag = str(tag).strip()


        if (
            tag == ""
            or tag.lower() == "nan"
        ):

            tag = f"UNNAMED_{i}"


        clean_tags.append(
            tag
        )


    # ------------------------------------------------------------
    # Data begins two rows after header
    # ------------------------------------------------------------

    data_start_row = (
        header_row + 2
    )


    dcs_df = raw_dcs.iloc[
        data_start_row:
    ].copy()


    dcs_df.columns = clean_tags


    # ------------------------------------------------------------
    # Remove duplicate columns
    # ------------------------------------------------------------

    dcs_df = dcs_df.loc[
        :,
        ~dcs_df.columns.duplicated(
            keep="first"
        )
    ].copy()


    # ------------------------------------------------------------
    # Timestamp
    # ------------------------------------------------------------

    dcs_df[
        TIME_COL
    ] = pd.to_datetime(
        dcs_df[
            TIME_COL
        ],
        errors="coerce"
    )


    # ------------------------------------------------------------
    # Clean rows
    # ------------------------------------------------------------

    dcs_df = (

        dcs_df

        .dropna(
            subset=[
                TIME_COL
            ]
        )

        .sort_values(
            TIME_COL
        )

        .drop_duplicates(
            subset=[
                TIME_COL
            ]
        )

        .reset_index(
            drop=True
        )

    )


    if dcs_df.empty:

        raise ValueError(
            "No valid timestamped DCS records were found."
        )


    # ------------------------------------------------------------
    # Convert process columns to numeric
    # ------------------------------------------------------------

    for col in dcs_df.columns:

        if col == TIME_COL:

            continue


        dcs_df[
            col
        ] = pd.to_numeric(
            dcs_df[col],
            errors="coerce"
        )


    return dcs_df


# ================================================================
# PRODUCTION + RESIDENCE CALCULATIONS
# ================================================================

def calculate_process_columns(
    dcs_df
):

    # ------------------------------------------------------------
    # Rotary values
    # ------------------------------------------------------------

    r1 = pd.to_numeric(
        dcs_df[
            ROTARY_1_TAG
        ],
        errors="coerce"
    )


    r2 = pd.to_numeric(
        dcs_df[
            ROTARY_2_TAG
        ],
        errors="coerce"
    )


    # ------------------------------------------------------------
    # Operating logic
    #
    # Positive = running
    # Negative / zero = not running
    # ------------------------------------------------------------

    r1_positive = r1.where(
        r1 > 0,
        0
    )


    r2_positive = r2.where(
        r2 > 0,
        0
    )


    # ------------------------------------------------------------
    # Active rotary
    # ------------------------------------------------------------

    dcs_df[
        "Active_Rotary_RPM"
    ] = np.maximum(
        r1_positive,
        r2_positive
    )


    # ------------------------------------------------------------
    # RPM → TPH
    # ------------------------------------------------------------

    dcs_df[
        "Production_Rate_TPH"
    ] = (

        dcs_df[
            "Active_Rotary_RPM"
        ]

        *

        RPM_TO_TPH

    )


    # ------------------------------------------------------------
    # Running status
    # ------------------------------------------------------------

    dcs_df[
        "Production_Running"
    ] = (

        dcs_df[
            "Active_Rotary_RPM"
        ]

        >

        0

    )


    # ------------------------------------------------------------
    # Minimum valid production
    # ------------------------------------------------------------

    if (
        "minimum_valid_production_tph"
        in deployment_bundle
    ):

        min_valid_production_tph = float(

            deployment_bundle[
                "minimum_valid_production_tph"
            ]

        )

    else:

        positive_prod = (

            dcs_df.loc[
                dcs_df[
                    "Production_Rate_TPH"
                ] > 0,

                "Production_Rate_TPH"
            ]

            .dropna()

        )


        if positive_prod.empty:

            raise ValueError(
                "No positive production values were found "
                "in the DCS data."
            )


        min_valid_production_tph = float(
            positive_prod.quantile(
                0.05
            )
        )


    # ------------------------------------------------------------
    # Production used for residence calculation
    # ------------------------------------------------------------

    dcs_df[
        "Residence_Production_TPH"
    ] = (

        dcs_df[
            "Production_Rate_TPH"
        ]

        .where(

            dcs_df[
                "Production_Rate_TPH"
            ]

            >=

            min_valid_production_tph

        )

    )


    # ------------------------------------------------------------
    # Reactor inventory
    # ------------------------------------------------------------

    inventory = pd.to_numeric(
        dcs_df[
            REACTOR_INVENTORY_TAG
        ],
        errors="coerce"
    )


    # ------------------------------------------------------------
    # Reactor residence time
    #
    # Residence = Inventory / Production
    # ------------------------------------------------------------

    dcs_df[
        "Reactor_Residence_hr_Instant"
    ] = (

        inventory

        /

        dcs_df[
            "Residence_Production_TPH"
        ]

    )


    # ------------------------------------------------------------
    # Crystallizer + Preheater residence
    # ------------------------------------------------------------

    dcs_df[
        "Cryst_Preheater_Residence_hr_Instant"
    ] = (

        PRE_REACTOR_INVENTORY_TON

        /

        dcs_df[
            "Residence_Production_TPH"
        ]

    )


    # ------------------------------------------------------------
    # Total residence
    # ------------------------------------------------------------

    dcs_df[
        "Total_PreSilo_RT_hr_Instant"
    ] = (

        dcs_df[
            "Reactor_Residence_hr_Instant"
        ]

        +

        dcs_df[
            "Cryst_Preheater_Residence_hr_Instant"
        ]

    )


    # ------------------------------------------------------------
    # Remove impossible reactor residence
    # ------------------------------------------------------------

    invalid_reactor_rt = (

        (

            dcs_df[
                "Reactor_Residence_hr_Instant"
            ]

            <= 0

        )

        |

        (

            dcs_df[
                "Reactor_Residence_hr_Instant"
            ]

            >

            MAX_REASONABLE_REACTOR_RT_HR

        )

    )


    dcs_df.loc[
        invalid_reactor_rt,
        "Reactor_Residence_hr_Instant"
    ] = np.nan


    # ------------------------------------------------------------
    # Remove impossible total residence
    # ------------------------------------------------------------

    invalid_total_rt = (

        (

            dcs_df[
                "Total_PreSilo_RT_hr_Instant"
            ]

            <= 0

        )

        |

        (

            dcs_df[
                "Total_PreSilo_RT_hr_Instant"
            ]

            >

            MAX_REASONABLE_TOTAL_RT_HR

        )

    )


    dcs_df.loc[
        invalid_total_rt,
        "Total_PreSilo_RT_hr_Instant"
    ] = np.nan


    return (
        dcs_df,
        min_valid_production_tph
    )


# ================================================================
# FEATURE ENGINEERING
# ================================================================

def summarize_presilo_window(
    window,
    process_tags
):

    features = {}


    # ============================================================
    # RAW PROCESS TAG FEATURES
    # ============================================================

    for tag in process_tags:

        s = pd.to_numeric(
            window[tag],
            errors="coerce"
        ).dropna()


        if s.empty:

            continue


        tag_type = get_tag_type(
            tag
        )


        # --------------------------------------------------------
        # Mean
        # --------------------------------------------------------

        features[
            f"{tag}__mean"
        ] = float(
            s.mean()
        )


        # --------------------------------------------------------
        # Standard deviation
        # --------------------------------------------------------

        if tag_type in [

            "TEMPERATURE",
            "PRESSURE",
            "FLOW"

        ]:

            features[
                f"{tag}__std"
            ] = float(
                s.std(
                    ddof=0
                )
            )


        # --------------------------------------------------------
        # Temperature min/max
        # --------------------------------------------------------

        if tag_type == "TEMPERATURE":

            features[
                f"{tag}__min"
            ] = float(
                s.min()
            )


            features[
                f"{tag}__max"
            ] = float(
                s.max()
            )


    # ============================================================
    # PRODUCTION FEATURES
    # ============================================================

    p = pd.to_numeric(

        window[
            "Residence_Production_TPH"
        ],

        errors="coerce"

    ).dropna()


    if not p.empty:

        features[
            "Production_Rate_TPH__mean"
        ] = float(
            p.mean()
        )


        features[
            "Production_Rate_TPH__std"
        ] = float(
            p.std(
                ddof=0
            )
        )


        features[
            "Production_Rate_TPH__min"
        ] = float(
            p.min()
        )


        features[
            "Production_Rate_TPH__max"
        ] = float(
            p.max()
        )


    # ============================================================
    # REACTOR RESIDENCE
    # ============================================================

    r = pd.to_numeric(

        window[
            "Reactor_Residence_hr_Instant"
        ],

        errors="coerce"

    ).dropna()


    if not r.empty:

        features[
            "Reactor_Residence_hr__mean"
        ] = float(
            r.mean()
        )


        features[
            "Reactor_Residence_hr__std"
        ] = float(
            r.std(
                ddof=0
            )
        )


    # ============================================================
    # CRYSTALLIZER + PREHEATER RESIDENCE
    # ============================================================

    cp = pd.to_numeric(

        window[
            "Cryst_Preheater_Residence_hr_Instant"
        ],

        errors="coerce"

    ).dropna()


    if not cp.empty:

        features[
            "Cryst_Preheater_Residence_hr__mean"
        ] = float(
            cp.mean()
        )


    # ============================================================
    # WINDOW QUALITY
    # ============================================================

    features[
        "Window_Readings"
    ] = int(
        len(window)
    )


    features[
        "Valid_Production_Percent"
    ] = float(

        window[
            "Residence_Production_TPH"
        ]

        .notna()

        .mean()

        *

        100

    )


    features[
        "Rotary_Positive_Percent"
    ] = float(

        window[
            "Production_Running"
        ]

        .fillna(False)

        .mean()

        *

        100

    )


    return features


# ================================================================
# MAIN PREDICTION FUNCTION
# ================================================================

def run_prediction(
    uploaded_file,
    manual_feed_iv,
    exit_date,
    exit_time
):

    # ============================================================
    # 1. VALIDATE FEED IV
    # ============================================================

    if not np.isfinite(
        manual_feed_iv
    ):

        raise ValueError(
            "Feed IV must be a valid numeric value."
        )


    if manual_feed_iv <= 0:

        raise ValueError(
            "Feed IV must be greater than zero."
        )


    # ============================================================
    # 2. CREATE EXIT TIMESTAMP
    # ============================================================

    manual_exit_string = (
        f"{exit_date} {exit_time}"
    )


    reactor_exit_time = pd.to_datetime(
        manual_exit_string,
        errors="coerce"
    )


    if pd.isna(
        reactor_exit_time
    ):

        raise ValueError(
            "Invalid Reactor Exit Date / Time."
        )


    # ============================================================
    # 3. READ DCS EXCEL
    # ============================================================

    raw_dcs = read_dcs_excel(
        uploaded_file
    )


    # ============================================================
    # 4. REQUIRED RAW TAGS
    #
    # 310-TIC1056 is included because it is one of the
    # exact trained model features.
    # ============================================================

    required_tags = [

        ROTARY_1_TAG,

        ROTARY_2_TAG,

        REACTOR_INVENTORY_TAG,

        "330-TI3202",

        "330-TI3203",

        "330-TI3204",

        "320-TIC2132",

        "310-TIC1056",

    ]


    missing_tags = [

        tag

        for tag in required_tags

        if tag not in raw_dcs.columns

    ]


    if missing_tags:

        raise ValueError(

            "Missing required DCS tags:\n\n"

            +

            "\n".join(

                f"• {tag}"

                for tag in missing_tags

            )

        )


    # ============================================================
    # 5. CALCULATE PROCESS COLUMNS
    # ============================================================

    dcs_df, min_valid_production_tph = (
        calculate_process_columns(
            raw_dcs
        )
    )


    # ============================================================
    # 6. DCS TIME RANGE
    # ============================================================

    dcs_start = dcs_df[
        TIME_COL
    ].min()


    dcs_end = dcs_df[
        TIME_COL
    ].max()


    # ============================================================
    # 7. EXIT MUST BE INSIDE DCS RANGE
    # ============================================================

    if reactor_exit_time < dcs_start:

        raise ValueError(

            "Selected exit time is BEFORE the DCS chunk.\n\n"

            f"Selected exit: {reactor_exit_time}\n"

            f"DCS starts: {dcs_start}\n\n"

            "Please select an exit time inside the "
            "uploaded DCS period."

        )


    if reactor_exit_time > dcs_end:

        raise ValueError(

            "Selected exit time is AFTER the DCS chunk.\n\n"

            f"Selected exit: {reactor_exit_time}\n"

            f"DCS ends: {dcs_end}\n\n"

            "Upload a DCS chunk containing data up to "
            "the selected exit time."

        )


    # ============================================================
    # 8. ONLY DATA UP TO EXIT TIME
    # ============================================================

    dcs_until_exit = dcs_df.loc[

        dcs_df[
            TIME_COL
        ]

        <=

        reactor_exit_time

    ].copy()


    if dcs_until_exit.empty:

        raise ValueError(
            "No DCS readings exist before the selected "
            "exit time."
        )


    # ============================================================
    # 9. FIND NEAREST DCS READING TO EXIT
    # ============================================================

    nearest_position = (

        dcs_until_exit[
            TIME_COL
        ]

        .sub(
            reactor_exit_time
        )

        .abs()

        .idxmin()

    )


    nearest_exit_row = (
        dcs_until_exit.loc[
            nearest_position
        ]
    )


    nearest_dcs_exit_time = (
        nearest_exit_row[
            TIME_COL
        ]
    )


    exit_difference_min = (

        abs(

            (
                reactor_exit_time
                -
                nearest_dcs_exit_time
            ).total_seconds()

        )

        /

        60.0

    )


    # ============================================================
    # 10. INITIAL RESIDENCE TIME
    # ============================================================

    initial_rt = nearest_exit_row[
        "Total_PreSilo_RT_hr_Instant"
    ]


    if (

        pd.isna(
            initial_rt
        )

        or initial_rt <= 0

        or initial_rt > MAX_REASONABLE_TOTAL_RT_HR

    ):

        raise ValueError(

            "Invalid residence time at the selected "
            "exit time.\n\n"

            f"Residence time: {initial_rt}\n\n"

            "Check reactor inventory and production rate "
            "around the selected exit time."

        )


    # ============================================================
    # 11. INITIAL ENTRY TIME
    # ============================================================

    entry_time = (

        reactor_exit_time

        -

        pd.Timedelta(
            hours=float(
                initial_rt
            )
        )

    )


    # ============================================================
    # 12. ITERATIVE ENTRY-TIME REFINEMENT
    # ============================================================

    iterations_used = 0


    avg_production = np.nan
    avg_inventory = np.nan
    reactor_rt = np.nan
    crystallizer_preheater_rt = np.nan
    total_rt = np.nan


    for iteration in range(
        1,
        MAX_ENTRY_ITERATIONS + 1
    ):

        iterations_used = iteration


        current_window = dcs_df.loc[

            (

                dcs_df[
                    TIME_COL
                ]

                >=

                entry_time

            )

            &

            (

                dcs_df[
                    TIME_COL
                ]

                <=

                reactor_exit_time

            )

        ].copy()


        if len(
            current_window
        ) < 3:

            raise ValueError(

                f"Iteration {iteration}: "
                "fewer than 3 DCS readings inside "
                "the calculated process window."

            )


        # --------------------------------------------------------
        # Production
        # --------------------------------------------------------

        production_series = pd.to_numeric(

            current_window[
                "Residence_Production_TPH"
            ],

            errors="coerce"

        ).dropna()


        # --------------------------------------------------------
        # Inventory
        # --------------------------------------------------------

        inventory_series = pd.to_numeric(

            current_window[
                REACTOR_INVENTORY_TAG
            ],

            errors="coerce"

        ).dropna()


        if production_series.empty:

            raise ValueError(

                f"Iteration {iteration}: "
                "no valid production values."

            )


        if inventory_series.empty:

            raise ValueError(

                f"Iteration {iteration}: "
                "no valid reactor inventory values."

            )


        # --------------------------------------------------------
        # Average production
        # --------------------------------------------------------

        avg_production = float(
            production_series.mean()
        )


        # --------------------------------------------------------
        # Average reactor inventory
        # --------------------------------------------------------

        avg_inventory = float(
            inventory_series.mean()
        )


        # --------------------------------------------------------
        # Reactor residence
        # --------------------------------------------------------

        reactor_rt = (

            avg_inventory
            /
            avg_production

        )


        # --------------------------------------------------------
        # Crystallizer + preheater residence
        # --------------------------------------------------------

        crystallizer_preheater_rt = (

            PRE_REACTOR_INVENTORY_TON
            /
            avg_production

        )


        # --------------------------------------------------------
        # Total residence
        # --------------------------------------------------------

        total_rt = (

            reactor_rt
            +
            crystallizer_preheater_rt

        )


        if (

            not np.isfinite(
                total_rt
            )

            or total_rt <= 0

            or total_rt > MAX_REASONABLE_TOTAL_RT_HR

        ):

            raise ValueError(

                f"Iteration {iteration}: "
                f"invalid total residence time "
                f"{total_rt:.4f} hr."

            )


        # --------------------------------------------------------
        # Calculate new entry time
        # --------------------------------------------------------

        new_entry_time = (

            reactor_exit_time

            -

            pd.Timedelta(
                hours=float(
                    total_rt
                )
            )

        )


        # --------------------------------------------------------
        # Convergence
        # --------------------------------------------------------

        difference_minutes = (

            abs(

                (
                    new_entry_time
                    -
                    entry_time
                ).total_seconds()

            )

            /

            60.0

        )


        entry_time = (
            new_entry_time
        )


        if (

            difference_minutes
            <=
            ENTRY_TIME_TOLERANCE_MIN

        ):

            break


    # ============================================================
    # 13. FINAL PROCESS WINDOW
    # ============================================================

    pre_silo_entry_time = (
        entry_time
    )


    w = dcs_df.loc[

        (

            dcs_df[
                TIME_COL
            ]

            >=

            pre_silo_entry_time

        )

        &

        (

            dcs_df[
                TIME_COL
            ]

            <=

            reactor_exit_time

        )

    ].copy()


    if len(w) < 3:

        raise ValueError(

            "Final process window contains fewer than "
            "3 DCS readings."

        )


    # ============================================================
    # 14. PROCESS TAG LIST
    # ============================================================

    exclude_raw_tags = {

        TIME_COL,

        "Active_Rotary_RPM",

        "Production_Rate_TPH",

        "Production_Running",

        "Residence_Production_TPH",

        "Reactor_Residence_hr_Instant",

        "Cryst_Preheater_Residence_hr_Instant",

        "Total_PreSilo_RT_hr_Instant",

    }


    silo_tags_to_exclude = {

        "350-LI5111",

        "350-LI5121",

        "350-L15121",

    }


    process_tags = [

        c

        for c in dcs_df.columns

        if c not in exclude_raw_tags

        and c not in silo_tags_to_exclude

    ]


    # ============================================================
    # 15. FEATURE ENGINEERING
    # ============================================================

    live_features = summarize_presilo_window(
        w,
        process_tags
    )


    # ============================================================
    # 16. MANUAL FEED IV
    # ============================================================

    live_features[
        "Feed_IV"
    ] = float(
        manual_feed_iv
    )


    # ============================================================
    # 17. CHECK EXACT TRAINED FEATURES
    # ============================================================

    missing_features = [

        feature

        for feature in FINAL_FEATURES_LIVE

        if feature not in live_features

    ]


    if missing_features:

        raise ValueError(

            "Live feature engineering is missing "
            "trained model features:\n\n"

            +

            "\n".join(

                f"• {feature}"

                for feature in missing_features

            )

        )


    # ============================================================
    # 18. CREATE MODEL INPUT
    # ============================================================

    live_X = (

        pd.DataFrame(
            [live_features]
        )

        .reindex(
            columns=FINAL_FEATURES_LIVE
        )

    )


    # ============================================================
    # 19. CHECK NaN / INF
    # ============================================================

    bad_columns = []


    for col in live_X.columns:

        value = live_X.iloc[
            0
        ][col]


        if pd.isna(
            value
        ):

            bad_columns.append(
                (
                    col,
                    "NaN"
                )
            )


        elif not np.isfinite(
            float(value)
        ):

            bad_columns.append(
                (
                    col,
                    "Infinite"
                )
            )


    if bad_columns:

        raise ValueError(

            "Required model features contain invalid values:\n\n"

            +

            "\n".join(

                f"• {col}: {reason}"

                for col, reason in bad_columns

            )

        )


    # ============================================================
    # 20. RUN MODELS
    # ============================================================

    predictions = {}


    for model_name, model in MODELS.items():

        predictions[
            model_name
        ] = float(

            model.predict(
                live_X
            )[0]

        )


    # ============================================================
    # 21. PRIMARY PREDICTION
    # ============================================================

    primary_model = (
        PRIMARY_MODEL_NAME
    )


    predicted_iv = float(
        predictions[
            primary_model
        ]
    )


    # ============================================================
    # 22. RETURN RESULT
    # ============================================================

    return {

        "predicted_iv":
            predicted_iv,

        "primary_model":
            primary_model,

        "predictions":
            predictions,

        "manual_feed_iv":
            float(
                manual_feed_iv
            ),

        "manual_exit_time":
            reactor_exit_time,

        "nearest_dcs_exit_time":
            nearest_dcs_exit_time,

        "nearest_exit_difference_min":
            exit_difference_min,

        "pre_silo_entry_time":
            pre_silo_entry_time,

        "window_duration_hr":
            (
                reactor_exit_time
                -
                pre_silo_entry_time
            ).total_seconds()
            /
            3600,

        "window_readings":
            len(w),

        "dcs_rows":
            len(dcs_df),

        "dcs_start":
            dcs_start,

        "dcs_end":
            dcs_end,

        "min_valid_production_tph":
            min_valid_production_tph,

        "iterations":
            iterations_used,

        "average_production_tph":
            avg_production,

        "average_reactor_inventory_ton":
            avg_inventory,

        "reactor_residence_hr":
            reactor_rt,

        "cryst_preheater_residence_hr":
            crystallizer_preheater_rt,

        "total_residence_hr":
            total_rt,

        "live_X":
            live_X,

        "window":
            w,

        "dcs":
            dcs_df,

    }


# ================================================================
# RUN PREDICTION
#
# Prediction is executed ONLY when Predict is clicked.
# ================================================================

if run_prediction_button:

    # ============================================================
    # VALIDATE FILE
    # ============================================================

    if uploaded_file is None:

        st.warning(
            "Please upload the DCS Excel file before "
            "running the prediction."
        )

        st.stop()


    # ============================================================
    # VALIDATE FEED IV
    # ============================================================

    if (

        not np.isfinite(
            manual_feed_iv
        )

        or manual_feed_iv <= 0

    ):

        st.warning(
            "Please enter a valid Feed IV greater than zero."
        )

        st.stop()


    # ============================================================
    # RUN PREDICTION
    # ============================================================

    with st.spinner(
        "Processing DCS data and calculating Pre-Silo IV..."
    ):

        try:

            result = run_prediction(

                uploaded_file,

                manual_feed_iv,

                exit_date,

                exit_time

            )


        except Exception as e:

            st.error(
                "Prediction failed."
            )

            st.exception(
                e
            )

            st.stop()


    # ============================================================
    # SAVE RESULT TO SESSION STATE
    #
    # THIS IS THE CRITICAL FIX.
    #
    # The result will survive Streamlit reruns caused by:
    #   - Download button
    #   - Other widget interaction
    #   - Browser refresh within the same session
    # ============================================================

    st.session_state[
        "prediction_result"
    ] = result

    st.session_state[
        "prediction_done"
    ] = True


    # ============================================================
    # RERUN
    #
    # This makes the display come from session_state rather
    # than only existing during the button-click execution.
    # ============================================================

    st.rerun()


# ================================================================
# DISPLAY STORED PREDICTION
#
# IMPORTANT:
# This section is OUTSIDE the Predict button block.
#
# Therefore clicking Download Model Input CSV will rerun the
# application, but the prediction remains available.
# ================================================================

if (

    st.session_state[
        "prediction_done"
    ]

    and

    st.session_state[
        "prediction_result"
    ] is not None

):

    result = st.session_state[
        "prediction_result"
    ]


    # ============================================================
    # SUCCESS
    # ============================================================

    st.success(
        "Pre-Silo IV prediction completed successfully."
    )


    # ============================================================
    # MAIN PREDICTION
    # ============================================================

    # st.markdown(
    #     '<div class="prediction-box">',
    #     unsafe_allow_html=True
    # )


    st.markdown(
        '<div class="prediction-label">'
        'Predicted Pre-Silo IV'
        '</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        f'<div class="prediction-value">'
        f'{result["predicted_iv"]:.4f}'
        f'</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        f'<div class="prediction-label">'
        f'Model: {result["primary_model"]}'
        f'</div>',
        unsafe_allow_html=True
    )


    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


    # ============================================================
    # KEY INFORMATION
    # ============================================================

    st.markdown(
        '<div class="section-title">'
        'Prediction Information'
        '</div>',
        unsafe_allow_html=True
    )


    c1, c2, c3, c4 = st.columns(
        4
    )


    with c1:

        st.metric(
            "Feed IV",
            f'{result["manual_feed_iv"]:.4f}'
        )


    with c2:

        st.metric(
            "Process Window",
            f'{result["window_duration_hr"]:.2f} hr'
        )


    with c3:

        st.metric(
            "DCS Readings Used",
            result["window_readings"]
        )


    with c4:

        st.metric(
            "Model Features",
            len(FINAL_FEATURES_LIVE)
        )


    # ============================================================
    # PROCESS CALCULATION
    # ============================================================

    st.markdown(
        '<div class="section-title">'
        'Process Calculation'
        '</div>',
        unsafe_allow_html=True
    )


    process_df = pd.DataFrame({

        "Parameter": [

            "Average Production Rate",

            "Average Reactor Inventory",

            "Reactor Residence Time",

            "Crystallizer + Preheater Residence",

            "Total Pre-Silo Residence",

            "Entry-Time Iterations",

        ],

        "Value": [

            f'{result["average_production_tph"]:.3f} TPH',

            f'{result["average_reactor_inventory_ton"]:.3f} ton',

            f'{result["reactor_residence_hr"]:.3f} hr',

            f'{result["cryst_preheater_residence_hr"]:.3f} hr',

            f'{result["total_residence_hr"]:.3f} hr',

            result["iterations"],

        ]

    })


    st.dataframe(
        process_df,
        use_container_width=True,
        hide_index=True
    )


    # ============================================================
    # PROCESS TIMING
    # ============================================================

    st.markdown(
        '<div class="section-title">'
        'Process Timing'
        '</div>',
        unsafe_allow_html=True
    )


    timing_df = pd.DataFrame({

        "Parameter": [

            "DCS Start",

            "DCS End",

            "Manual Reactor Exit / Pre-Silo Time",

            "Nearest DCS Exit Reading",

            "Difference from DCS Exit Reading",

            "Calculated Pre-Silo Entry Time",

            "Process Window Duration",

        ],

        "Value": [

            str(
                result[
                    "dcs_start"
                ]
            ),

            str(
                result[
                    "dcs_end"
                ]
            ),

            str(
                result[
                    "manual_exit_time"
                ]
            ),

            str(
                result[
                    "nearest_dcs_exit_time"
                ]
            ),

            f'{result["nearest_exit_difference_min"]:.2f} min',

            str(
                result[
                    "pre_silo_entry_time"
                ]
            ),

            f'{result["window_duration_hr"]:.3f} hr',

        ]

    })


    st.dataframe(
        timing_df,
        use_container_width=True,
        hide_index=True
    )


    # ============================================================
    # MODEL COMPARISON
    # ============================================================

    if len(
        result[
            "predictions"
        ]
    ) > 1:

        st.markdown(
            '<div class="section-title">'
            'Model Predictions'
            '</div>',
            unsafe_allow_html=True
        )


        comparison_df = pd.DataFrame({

            "Model":

                list(
                    result[
                        "predictions"
                    ].keys()
                ),

            "Predicted_PreSilo_IV":

                list(
                    result[
                        "predictions"
                    ].values()
                ),

        })


        comparison_df[
            "Predicted_PreSilo_IV"
        ] = (

            comparison_df[
                "Predicted_PreSilo_IV"
            ]

            .round(
                6
            )

        )


        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True
        )


    # ============================================================
    # EXACT MODEL INPUT
    # ============================================================

    with st.expander(
        "View Exact Model Input Features"
    ):

        st.caption(
            "These are the exact features and values "
            "passed to the trained model."
        )


        model_input_display = (

            result[
                "live_X"
            ]

            .T

            .rename(
                columns={
                    0: "Value"
                }
            )

        )


        st.dataframe(
            model_input_display,
            use_container_width=True
        )


    # ============================================================
    # PROCESS WINDOW
    # ============================================================

    with st.expander(
        "View DCS Process Window Used for Prediction"
    ):

        st.write(
            "Only readings from the calculated Pre-Silo "
            "Entry Time through the manually selected "
            "Reactor Exit Time were used."
        )


        st.dataframe(
            result[
                "window"
            ],
            use_container_width=True,
            hide_index=True
        )


    # ============================================================
    # DOWNLOAD MODEL INPUT
    #
    # IMPORTANT:
    # This uses session_state result.
    # Clicking it will NOT delete the prediction.
    # ============================================================

    st.markdown(
        '<div class="section-title">'
        'Download'
        '</div>',
        unsafe_allow_html=True
    )


    model_input_download = (

        result[
            "live_X"
        ]

        .T

        .rename(
            columns={
                0: "Value"
            }
        )

        .to_csv()

    )


    st.download_button(
        "⬇️ Download Model Input CSV",
        data=model_input_download,
        file_name="SSP3_PreSilo_Model_Input.csv",
        mime="text/csv",
        key="download_model_input",
    )


    # ============================================================
    # FINAL STATUS
    # ============================================================

    st.divider()


    st.success(
        "Prediction complete. "
        "No Actual Lab IV was used. "
        "Post-exit DCS data was excluded."
    )


    # ============================================================
    # RESET REMINDER
    # ============================================================

    st.markdown(
        """
        <div class="reset-box">
        <b>Ready for another sample?</b><br>
        Click <b>🔄 New Prediction</b> at the top to clear
        the current DCS file, Feed IV, Exit Date/Time and
        prediction result.
        </div>
        """,
        unsafe_allow_html=True
    )


# ================================================================
# INITIAL SCREEN
#
# Displayed when there is no stored prediction.
# ================================================================

else:

    st.markdown(
        """
        <div class="info-box">

        <b>How to use the application</b>

        <br>

        <b>Step 1:</b> Upload the SSP-III DCS Excel chunk.

        <br>

        <b>Step 2:</b> Enter the current
        <b>Feed IV</b> from the plant logbook.

        <br>

        <b>Step 3:</b> Select the actual
        <b>Reactor Exit / Pre-Silo Sample Date and Time</b>.

        <br>

        <b>Step 4:</b> Click
        <b>Predict Pre-Silo IV</b>.

        <br>

        The application will automatically:

        <br>
        • Read the DCS data
        <br>
        • Calculate production rate
        <br>
        • Calculate reactor residence time
        <br>
        • Calculate crystallizer/preheater residence time
        <br>
        • Calculate the upstream process window
        <br>
        • Generate the exact trained features
        <br>
        • Run the trained model
        <br>
        • Display the predicted Pre-Silo IV

        <br><br>
        <b>No Actual Lab IV is required.</b>

        <br>

        <b>No prediction is performed until the Predict button
        is pressed.</b>

        <br>

        <b>🔄 New Prediction</b> clears all current readings
        and starts a completely fresh prediction cycle.

        </div>
        """,
        unsafe_allow_html=True
    )