import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
from math import sqrt

# Load your CSV file
df = pd.read_csv("Motor_Insurance_Dataset.csv")  # update path if needed

# Clean column names
df.columns = df.columns.str.strip()

# Rename for easier coding
df.rename(columns={
    'INSURANCE TYPE': 'insurance_type',
    'VEHICLE TYPE': 'vehicle_type',
    'VEHICLE USE': 'vehicle_use',
    'VEHICLE MAKE': 'vehicle_make',
    'VEHICLE MODEL': 'vehicle_model',
    'VEHICLE MAKE YEAR': 'vehicle_make_year',
    'SUM INSURED': 'sum_insured',
    'POLICY PREMIUM': 'policy_premium'
}, inplace=True)

# Drop rows with missing values
df = df.dropna()

# Define features and target
features = ['insurance_type', 'vehicle_type', 'vehicle_use', 
            'vehicle_make', 'vehicle_model', 'vehicle_make_year', 'sum_insured']
target = 'policy_premium'

# One-hot encode categorical features
df_encoded = pd.get_dummies(df[features])

# Match encoded features with target
X = df_encoded
y = df[target]

# Train-test split (optional but good practice)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
rmse = sqrt(mean_squared_error(y_test, y_pred))
print(f"✅ Model trained. RMSE on test set: {rmse:.2f}")

# Save the model
joblib.dump(model, "premium_predictor_model.pkl")
print("💾 Model saved as premium_predictor_model.pkl")
