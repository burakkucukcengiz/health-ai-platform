from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, '..', 'models', 'nafld_model_proxy.pkl')
FEATURES_PATH = os.path.join(BASE_DIR, '..', 'models', 'feature_names_proxy.pkl')

# Eğitimdeki özellik sırası birebir aynı olmalı
FEATURES = ['RIAGENDR', 'BMI', 'BMXWT', 'BMXHT', 'Waist_cm', 'SBP', 'DBP',
            'Triglyceride', 'LDL', 'Total_Cholesterol', 'HDL']

# Eşik: test setinde precision/recall dengesine göre sonra belirlenecek
THRESHOLD_MODERATE = 0.3
THRESHOLD_HIGH = 0.6

try:
    model = joblib.load(MODEL_PATH)
    feature_names = joblib.load(FEATURES_PATH)
    assert list(feature_names) == FEATURES, "Feature sırası eğitimle uyuşmuyor"
    print("✅ Model loaded")
except Exception as e:
    print(f"❌ Error: {e}")
    model = None


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'model': 'proxy_metabolic_nafld',
        'test_auc': 0.7926,
        'training_samples': 51613,
        'cycles': '1999-2018',
    })


@app.route('/api/predict/nafld', methods=['POST'])
def predict_nafld():
    try:
        if model is None:
            return jsonify({'success': False, 'error': 'Model yüklenemedi'}), 500

        data = request.get_json()

        sex_code = 1 if data['sex'] == 'male' else 2  # NHANES: 1=erkek, 2=kadın
        height_m = data['height_cm'] / 100.0
        bmi = data['weight_kg'] / (height_m ** 2)

        row = [[
            sex_code, bmi, data['weight_kg'], data['height_cm'],
            data['waist_cm'], data['sbp'], data['dbp'],
            data['triglyceride'], data['ldl'],
            data['total_cholesterol'], data['hdl'],
        ]]
        features = np.array(row)

        risk_prob = float(model.predict_proba(features)[0, 1])

        if risk_prob < THRESHOLD_MODERATE:
            risk_level = 'Low'
        elif risk_prob < THRESHOLD_HIGH:
            risk_level = 'Moderate'
        else:
            risk_level = 'High'

        return jsonify({
            'success': True,
            'risk_score': round(risk_prob, 4),
            'risk_level': risk_level,
        })
    except KeyError as e:
        return jsonify({'success': False, 'error': f'Eksik alan: {e}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    app.run(debug=True, port=8000)