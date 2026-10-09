from app import app

VALID = {
    'sex': 'male', 'height_cm': 175, 'weight_kg': 80, 'waist_cm': 95,
    'sbp': 120, 'dbp': 80, 'triglyceride': 150, 'ldl': 120,
    'total_cholesterol': 200, 'hdl': 45,
}


def client():
    app.config['TESTING'] = True
    return app.test_client()


def test_health():
    assert client().get('/health').status_code == 200


def test_predict_valid():
    r = client().post('/api/predict/nafld', json=VALID)
    body = r.get_json()
    assert r.status_code == 200
    assert body['risk_level'] in {'Low', 'Moderate', 'High'}
    assert 0 <= body['risk_score'] <= 1


def test_default_profile_is_low():
    r = client().post('/api/predict/nafld', json=VALID)
    assert r.get_json()['risk_level'] == 'Low'


def test_zero_height_rejected():
    r = client().post('/api/predict/nafld', json={**VALID, 'height_cm': 0})
    assert r.status_code == 400


def test_missing_field_rejected():
    payload = {k: v for k, v in VALID.items() if k != 'hdl'}
    r = client().post('/api/predict/nafld', json=payload)
    assert r.status_code == 400
    assert 'Eksik alan' in r.get_json()['error']
