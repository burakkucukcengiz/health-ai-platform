from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import os
import pandas as pd

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- NAFLD (vekil etiket) modeli ----
MODEL_PATH = os.path.join(BASE_DIR, '..', 'models', 'nafld_model_proxy.pkl')
FEATURES_PATH = os.path.join(BASE_DIR, '..', 'models', 'feature_names_proxy.pkl')

FEATURES = ['RIAGENDR', 'BMI', 'BMXWT', 'BMXHT', 'Waist_cm', 'SBP', 'DBP',
            'Triglyceride', 'LDL', 'Total_Cholesterol', 'HDL']

THRESHOLD_MODERATE = 0.50
THRESHOLD_HIGH = 0.67

try:
    model = joblib.load(MODEL_PATH)
    feature_names = joblib.load(FEATURES_PATH)
    assert list(feature_names) == FEATURES, "Feature sirasi egitimle uyusmuyor"
    print("Model loaded: NAFLD")
except Exception as e:
    print(f"NAFLD model error: {e}")
    model = None

# ---- Metabolik sendrom (ATP III) modeli ----
MODEL_METS_PATH = os.path.join(BASE_DIR, '..', 'models', 'mets_model.pkl')
FEATURES_METS_PATH = os.path.join(BASE_DIR, '..', 'models', 'feature_names_mets.pkl')

try:
    mets_model = joblib.load(MODEL_METS_PATH)
    mets_feature_names = joblib.load(FEATURES_METS_PATH)
    assert list(mets_feature_names) == FEATURES, "MetS feature sirasi uyusmuyor"
    print("Model loaded: Metabolik sendrom")
except Exception as e:
    print(f"MetS model error: {e}")
    mets_model = None

# ---- HOMA-IR (insulin direnci) modeli ----
MODEL_HOMA_PATH = os.path.join(BASE_DIR, '..', 'models', 'homa_model.pkl')
FEATURES_HOMA_PATH = os.path.join(BASE_DIR, '..', 'models', 'feature_names_homa.pkl')

THRESHOLD_HOMA_MODERATE = 0.40
THRESHOLD_HOMA_HIGH = 0.60

try:
    homa_model = joblib.load(MODEL_HOMA_PATH)
    homa_feature_names = joblib.load(FEATURES_HOMA_PATH)
    assert list(homa_feature_names) == FEATURES, "HOMA-IR feature sirasi uyusmuyor"
    print("Model loaded: HOMA-IR")
except Exception as e:
    print(f"HOMA-IR model error: {e}")
    homa_model = None


def build_features(data):
    if data['height_cm'] <= 0 or data['weight_kg'] <= 0:
        raise ValueError('Boy ve kilo pozitif olmali')

    sex_code = 1 if data['sex'] == 'male' else 2
    height_m = data['height_cm'] / 100.0
    bmi = data['weight_kg'] / (height_m ** 2)

    row = [[
        sex_code, bmi, data['weight_kg'], data['height_cm'],
        data['waist_cm'], data['sbp'], data['dbp'],
        data['triglyceride'], data['ldl'],
        data['total_cholesterol'], data['hdl'],
    ]]
    return pd.DataFrame(row, columns=FEATURES), sex_code


def compute_mets_criteria(data, sex_code):
    is_male = sex_code == 1

    waist_crit = (data['waist_cm'] >= 102) if is_male else (data['waist_cm'] >= 88)
    tg_crit = data['triglyceride'] >= 150
    hdl_crit = (data['hdl'] < 40) if is_male else (data['hdl'] < 50)
    bp_crit = (data['sbp'] >= 130) or (data['dbp'] >= 85)

    detail = {
        'waist': bool(waist_crit),
        'triglyceride': bool(tg_crit),
        'hdl': bool(hdl_crit),
        'blood_pressure': bool(bp_crit),
    }
    count = sum(detail.values())
    return count, detail


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'models': {
            'nafld_proxy': {'test_auc': 0.7926, 'training_samples': 51613},
            'metabolic_syndrome': {'test_auc': 0.9752, 'naive_baseline_auc': 0.9624,
                                    'training_samples': 18009},
            'homa_ir': {'test_auc': 0.8127, 'logistic_test_auc': 0.8141,
                        'training_samples': 7562, 'threshold': 2.5},
        },
        'cycles': '1999-2018',
    })


@app.route('/api/predict/nafld', methods=['POST'])
def predict_nafld():
    try:
        if model is None:
            return jsonify({'success': False, 'error': 'Model yuklenemedi'}), 500

        data = request.get_json()
        features, _ = build_features(data)

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
    except (TypeError, ValueError) as e:
        return jsonify({'success': False, 'error': f'Gecersiz girdi: {e}'}), 400
    except Exception as e:
        print(f"Sunucu hatasi: {e}")
        return jsonify({'success': False, 'error': 'Sunucu hatasi'}), 500


@app.route('/api/predict/mets', methods=['POST'])
def predict_mets():
    try:
        if mets_model is None:
            return jsonify({'success': False, 'error': 'Model yuklenemedi'}), 500

        data = request.get_json()
        features, sex_code = build_features(data)

        criteria_met, detail = compute_mets_criteria(data, sex_code)

        if criteria_met <= 1:
            risk_level = 'Low'
        elif criteria_met == 2:
            risk_level = 'Moderate'
        else:
            risk_level = 'High'

        model_score = float(mets_model.predict_proba(features)[0, 1])

        return jsonify({
            'success': True,
            'criteria_met': criteria_met,
            'criteria_total': 4,
            'criteria_detail': detail,
            'risk_level': risk_level,
            'model_score': round(model_score, 4),
            'note': 'Glikoz olculmedigi icin tam ATP III tanisi (5 kriter) yapilamaz; '
                    'bu sonuc 4 kriterin bir ozetidir.',
        })
    except KeyError as e:
        return jsonify({'success': False, 'error': f'Eksik alan: {e}'}), 400
    except (TypeError, ValueError) as e:
        return jsonify({'success': False, 'error': f'Gecersiz girdi: {e}'}), 400
    except Exception as e:
        print(f"Sunucu hatasi: {e}")
        return jsonify({'success': False, 'error': 'Sunucu hatasi'}), 500


@app.route('/api/predict/homair', methods=['POST'])
def predict_homair():
    try:
        if homa_model is None:
            return jsonify({'success': False, 'error': 'Model yuklenemedi'}), 500

        data = request.get_json()
        features, _ = build_features(data)

        risk_prob = float(homa_model.predict_proba(features)[0, 1])

        if risk_prob < THRESHOLD_HOMA_MODERATE:
            risk_level = 'Low'
        elif risk_prob < THRESHOLD_HOMA_HIGH:
            risk_level = 'Moderate'
        else:
            risk_level = 'High'

        return jsonify({
            'success': True,
            'risk_score': round(risk_prob, 4),
            'risk_level': risk_level,
            'note': 'Bu model glikoz ve insulin degerlerini OZELLIK OLARAK KULLANMAZ; '
                    'bunlar sadece egitim hedefini (HOMA-IR >= 2.5) hesaplamak icin kullanildi. '
                    'Bu nedenle NAFLD ve MetS modellerinden farkli olarak sizinti icermez.',
        })
    except KeyError as e:
        return jsonify({'success': False, 'error': f'Eksik alan: {e}'}), 400
    except (TypeError, ValueError) as e:
        return jsonify({'success': False, 'error': f'Gecersiz girdi: {e}'}), 400
    except Exception as e:
        print(f"Sunucu hatasi: {e}")
        return jsonify({'success': False, 'error': 'Sunucu hatasi'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8000)
