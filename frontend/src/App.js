import React, { useState } from 'react';
import './App.css';

const API_URL_NAFLD = 'http://localhost:8000/api/predict/nafld';
const API_URL_METS = 'http://localhost:8000/api/predict/mets';

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
    title: 'Vucut',
    fields: [
      { name: 'height_cm', label: 'Boy', unit: 'cm' },
      { name: 'weight_kg', label: 'Kilo', unit: 'kg' },
      { name: 'waist_cm', label: 'Bel cevresi', unit: 'cm' },
    ],
  },
  {
    title: 'Tansiyon',
    fields: [
      { name: 'sbp', label: 'Buyuk tansiyon (SBP)', unit: 'mmHg' },
      { name: 'dbp', label: 'Kucuk tansiyon (DBP)', unit: 'mmHg' },
    ],
  },
  {
    title: 'Kan degerleri',
    fields: [
      { name: 'triglyceride', label: 'Trigliserit', unit: 'mg/dL' },
      { name: 'total_cholesterol', label: 'Toplam kolesterol', unit: 'mg/dL' },
      { name: 'ldl', label: 'LDL', unit: 'mg/dL' },
      { name: 'hdl', label: 'HDL', unit: 'mg/dL' },
    ],
  },
];

const RISK_STYLES = {
  Low: {
    bg: 'bg-green-500',
    label: 'Dusuk',
    text: 'Risk dusuk. Saglikli yasam aliskanliklarini surdurmek yeterli.',
  },
  Moderate: {
    bg: 'bg-yellow-500',
    label: 'Orta',
    text: 'Risk orta. Bir saglik profesyoneliyle gorusmeniz onerilir.',
  },
  High: {
    bg: 'bg-red-500',
    label: 'Yuksek',
    text: 'Risk yuksek. Bir hekime basvurmaniz onerilir.',
  },
};

const CRITERIA_LABELS = {
  waist: 'Bel cevresi',
  triglyceride: 'Trigliserit',
  hdl: 'HDL',
  blood_pressure: 'Tansiyon',
};

function App() {
  const [formData, setFormData] = useState(INITIAL_DATA);
  const [result, setResult] = useState(null);
  const [metsResult, setMetsResult] = useState(null);
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
      setError('Lutfen tum alanlari doldurun.');
      return;
    }

    setLoading(true);
    try {
      const [nafldRes, metsRes] = await Promise.all([
        fetch(API_URL_NAFLD, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        }),
        fetch(API_URL_METS, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        }),
      ]);
      const nafldData = await nafldRes.json();
      const metsData = await metsRes.json();

      if (!nafldData.success) {
        setError(nafldData.error || 'NAFLD tahmini alinamadi.');
        setResult(null);
      } else {
        setResult(nafldData);
      }

      if (metsData.success) {
        setMetsResult(metsData);
      } else {
        setMetsResult(null);
      }
    } catch (err) {
      console.error('Error:', err);
      setError('Backend baglantisi basarisiz. Flask sunucusunun 8000 portunda calistigini kontrol edin.');
    } finally {
      setLoading(false);
    }
  };

  const style = result ? RISK_STYLES[result.risk_level] : null;
  const metsStyle = metsResult ? RISK_STYLES[metsResult.risk_level] : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-2">Metabolik Saglik Taramasi</h1>
          <p className="text-blue-100 text-lg">NAFLD riski ve metabolik sendrom kriterleri icin destek araci</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
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
                <option value="female">Kadin</option>
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
              {loading ? 'Hesaplaniyor...' : 'Sonuclari Hesapla'}
            </button>
          </div>

          <div className="space-y-8">
            <div className="bg-white rounded-2xl shadow-2xl p-8">
              {result ? (
                <div className="text-center">
                  <h2 className="text-xl font-bold text-gray-800 mb-4">NAFLD Risk Taramasi</h2>

                  <div className={`${style.bg} text-white rounded-lg p-6 mb-6`}>
                    <p className="text-sm uppercase tracking-wide opacity-90">Risk seviyesi</p>
                    <p className="text-4xl font-bold mt-1">{style.label}</p>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4 text-left">
                    <p className="text-gray-600 text-sm mb-3">{style.text}</p>
                    <p className="text-gray-500 text-xs mb-3">
                      Model skoru: {result.risk_score.toFixed(4)}. Bu bir olasilik degildir; yalnizca
                      model ici siralama icin kullanilir. Yuzde olarak yorumlanmamalidir.
                    </p>
                    <p className="text-gray-500 text-xs">
                      Bu bir tani degil, tarama amacli bir tahmindir. Model, karaciger biyopsisi
                      yerine vekil bir etiketle egitilmistir ve klinik kararlarin yerini tutmaz.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center">
                  <p className="text-gray-500 text-lg">Bilgileri girin ve sonuclari hesaplayin</p>
                </div>
              )}
            </div>

            {metsResult && (
              <div className="bg-white rounded-2xl shadow-2xl p-8">
                <h2 className="text-xl font-bold text-gray-800 mb-4">Metabolik Sendrom Kriter Ozeti</h2>

                <div className={`${metsStyle.bg} text-white rounded-lg p-6 mb-6`}>
                  <p className="text-sm uppercase tracking-wide opacity-90">
                    {metsResult.criteria_met} / {metsResult.criteria_total} kriter karsilaniyor
                  </p>
                  <p className="text-4xl font-bold mt-1">{metsStyle.label}</p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 text-left">
                  <ul className="text-sm text-gray-700 mb-3 space-y-1">
                    {Object.entries(metsResult.criteria_detail).map(([key, met]) => (
                      <li key={key} className="flex items-center justify-between">
                        <span>{CRITERIA_LABELS[key]}</span>
                        <span className={met ? 'text-red-600 font-semibold' : 'text-green-600'}>
                          {met ? 'Esik ustu' : 'Normal'}
                        </span>
                      </li>
                    ))}
                  </ul>
                  <p className="text-gray-500 text-xs mb-3">{metsResult.note}</p>
                  <p className="text-gray-400 text-xs">
                    Ek bilgi (deneysel): model skoru {metsResult.model_score.toFixed(4)}. Bu skor, sadece
                    kriter sayisina gore kurulmus basit bir kurala gore cok kucuk bir iyilestirme saglar
                    (~0.013 AUC); birincil cikti olarak kullanilmamalidir.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
