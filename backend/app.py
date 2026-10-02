from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np

app = Flask(__name__)
CORS(app)

# Load model
try:
    model = joblib.load('../models/nafld_model.pkl')
    print("✅ Model loaded")
except Exception as e:
    print(f"❌ Error: {e}")
    model = None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'auc': 0.9892})

@app.route('/api/predict/nafld', methods=['POST'])
def predict_nafld():
    try:
        data = request.get_json()
        
        features = np.array([[
            data['age'], data['bmi'], data['ast'], data['alt'],
            data['platelet'], data['triglyceride'], data['total_cholesterol'],
            data['ldl'], data['hdl'], data['sbp'], data['dbp'], data['waist_cm']
        ]])
        
        risk_prob = model.predict_proba(features)[0, 1]
        
        if risk_prob < 0.33:
            risk_level = 'Low'
        elif risk_prob < 0.67:
            risk_level = 'Moderate'
        else:
            risk_level = 'High'
        
        return jsonify({
            'success': True,
            'risk_score': float(risk_prob),
            'risk_level': risk_level
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=8000)
