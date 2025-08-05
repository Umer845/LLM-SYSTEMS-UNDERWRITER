import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

# Load Excel file
df = pd.read_excel("All_Pakistani_Vehicles_List.xlsx")  # adjust path if needed
df.columns = df.columns.str.strip()  # clean column names

print("👉 Columns in DataFrame:", df.columns.tolist())  # ✅ print for debugging

# Rename if needed
df.rename(columns={
    'MakeName': 'make_name',
    'SubMake': 'sub_make_name',
    'Year': 'model_year',
    'Tracker': 'tracker_id',
    'SumInsured': 'suminsured',
    'Claims': 'no_of_claims',
    'ClaimAmount': 'clam_amount',  # check actual spelling
    'VehicleCapacity': 'vehicle_capacity',
    'NetPremium': 'netpremium'
}, inplace=True)

# Check again
print("✅ Renamed Columns:", df.columns.tolist())

# Define features
features = ['make_name', 'sub_make_name', 'model_year', 'tracker_id', 
            'suminsured', 'no_of_claims', 'clam_amount', 'vehicle_capacity']
target = 'netpremium'

# Drop missing values
df = df.dropna(subset=features + [target])

# Encode categorical variables
df = pd.get_dummies(df, columns=['make_name', 'sub_make_name'])

# Train the model
X = df[features]
y = df[target]

model = RandomForestRegressor()
model.fit(X, y)

# Save model
joblib.dump(model, "premium_predictor_model.pkl")
print("🎉 Model trained and saved successfully.")
