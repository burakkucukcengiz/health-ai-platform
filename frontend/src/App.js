import React, { useState } from 'react';
import './App.css';

const API_URL = 'http://localhost:8000/api/predict/nafld';

const INITIAL_DATA = {
  sex: 'male',
  height_cm: 175,
  weight_kg: 80,
  waist_cm: 95,
  sbp: 120,
  dbp: 80,
  triglyceride: 150,
  ldl: 120,
  total_cholesterol: 200,
  hdl: 45,
};

const FIELD_GROUPS = [
  {
    title: 'Vücut',
    fields: [
      { name: 'height_cm', label: 'Boy', unit: 'cm' },
      { name: 'weight_kg', label: 'Kilo', unit: 'kg' },
      { name: 'waist_cm', label: 'Bel çevresi', unit: 'cm' },
    ],
  },
  {
    title: 'Tansiyon',
    fields: [
      { name: 'sbp', label: 'Büyük tansiyon (SBP)', unit: 'mmHg' },
      { name: 'dbp', label: 'Küçük tansiyon (DBP)', unit: 'mmHg' },
    ],
  },
  {
    title: 'Kan değerleri',
    fields: [
      { name: 'triglyceride', label: 'Trigliserit', unit: 'mg/dL' },
      { name: 'total_cholesterol', label: 'Toplam kolesterol', unit: 'mg/dL' },
      { name: 'ldl', label: 'LDL', unit: 'mg/dL' },
      { name: 'hdl', label: 'HDL', unit: 'mg/dL' },
    ],
  },
];

const RISK_STYLES = {
  Low: { bg: 'bg-green-500', text: '✅ Risk düşük. Sağlıklı yaşam alışkanlıklarını sürdürmek yeterli.' },
  Moderate: { bg: 'bg-yellow-500', text: '⚠️ Risk orta. Bir sağlık profesyoneliyle görüşmeniz önerilir.' },
  High: { bg: 'bg-red-500', text: '🚨 Risk yüksek. Bir hekime başvurmanız önerilir.' },
};

function App() {
  const [formData, setFormData] = useState(INITIAL_DATA);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'sex' ? value : value === '' ? '' : Number(value),
    }));
  };

  const handlePredict = async () => {
    setError(null);

    const missing = Object.entries(formData).some(
      ([key, value]) => key !== 'sex' && (value === '' || Number.isNaN(value))
    );
    if (missing) {
      setError('Lütfen tüm alanları doldurun.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await response.json();
      if (!data.success) {
        setError(data.error || 'Tahmin alınamadı.');
        setResult(null);
      } else {
        setResult(data);
      }
    } catch (err) {
      console.error('Error:', err);
      setError('Backend bağlantısı başarısız. Flask sunucusunun 8000 portunda çalıştığını kontrol edin.');
    } finally {
      setLoading(false);
    }
  };

  const style = result ? RISK_STYLES[result.risk_level] : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-2">🏥 NAFLD Risk Tahmini</h1>
          <p className="text-blue-100 text-lg">Metabolik sağlık için yapay zekâ destekli tarama aracı</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form */}
          <div className="bg-white rounded-2xl shadow-2xl p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Hasta Bilgileri</h2>

            <div className="mb-6">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Cinsiyet</label>
              <select
                name="sex"
                value={formData.sex}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="male">Erkek</option>
                <option value="female">Kadın</option>
              </select>
            </div>

            <div className="space-y-6">
              {FIELD_GROUPS.map((group) => (
                <div key={group.title}>
                  <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">{group.title}</h3>
                  <div className="grid grid-cols-2 gap-4">
                    {group.fields.map((field) => (
                      <div key={field.name}>
                        <label className="block text-xs text-gray-600 mb-1">
                          {field.label} ({field.unit})
                        </label>
                        <input
                          type="number"
                          name={field.name}
                          value={formData[field.name]}
                          onChange={handleChange}
                          step="0.1"
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {error && (
              <div className="mt-4 bg-red-100 text-red-700 rounded-lg p-3 text-sm">{error}</div>
            )}

            <button
              onClick={handlePredict}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50 mt-6"
            >
              {loading ? 'Hesaplanıyor...' : '🔍 Riski Hesapla'}
            </button>
          </div>

          {/* Result */}
          <div className="bg-white rounded-2xl shadow-2xl p-8 flex flex-col justify-center">
            {result ? (
              <div className="text-center">
                <h2 className="text-2xl font-bold text-gray-800 mb-6">Sonuç</h2>

                <div className={`${style.bg} rounded-full w-40 h-40 mx-auto mb-6 flex items-center justify-center`}>
                  <span className="text-white text-5xl font-bold">
                    {(result.risk_score * 100).toFixed(0)}%
                  </span>
                </div>

                <div className={`${style.bg} text-white rounded-lg p-4 mb-6`}>
                  <p className="text-2xl font-bold">{result.risk_level} Risk</p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 text-left">
                  <p className="text-gray-700 font-semibold mb-2">
                    Risk skoru: {result.risk_score.toFixed(4)}
                  </p>
                  <p className="text-gray-600 text-sm mb-3">{style.text}</p>
                  <p className="text-gray-500 text-xs">
                    Bu bir tanı değil, tarama amaçlı bir tahmindir. Model, karaciğer biyopsisi
                    yerine vekil bir etiketle eğitilmiştir ve klinik kararların yerini tutmaz.
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-gray-500 text-lg">📊 Bilgileri girin ve riski hesaplayın</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;