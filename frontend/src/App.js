import React, { useState } from 'react';
import './App.css';

function App() {
  const [formData, setFormData] = useState({
    age: 55,
    bmi: 28.5,
    ast: 35,
    alt: 42,
    platelet: 250,
    triglyceride: 150,
    total_cholesterol: 200,
    ldl: 120,
    hdl: 45,
    sbp: 130,
    dbp: 85,
    waist_cm: 95,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: parseFloat(value) || value
    }));
  };

  const handlePredict = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/predict/nafld', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Backend bağlantısı başarısız!');
    }
    setLoading(false);
  };

  const getRiskColor = (level) => {
    if (level === 'Low') return 'bg-green-500';
    if (level === 'Moderate') return 'bg-yellow-500';
    if (level === 'High') return 'bg-red-500';
    return 'bg-gray-500';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-purple-700 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-white mb-2">🏥 NAFLD Risk Predictor</h1>
          <p className="text-blue-100 text-lg">AI-Powered Metabolic Health Assessment</p>
        </div>

        {/* Main Container */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
  {/* Form Section */}
          <div className="bg-white rounded-2xl shadow-2xl p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Patient Information</h2>
            
            <div className="space-y-4 overflow-y-auto max-h-96">
              <div className="grid grid-cols-2 gap-4">
                <input
                  type="number"
                  name="age"
                  placeholder="Age"
                  value={formData.age}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="number"
                  name="bmi"
                  placeholder="BMI"
                  value={formData.bmi}
                  onChange={handleChange}
                  step="0.1"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <input
                  type="number"
                  name="ast"
                  placeholder="AST"
                  value={formData.ast}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="number"
                  name="alt"
                  placeholder="ALT"
                  value={formData.alt}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <input
                  type="number"
                  name="platelet"
                  placeholder="Platelet (K)"
                  value={formData.platelet}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="number"
                  name="triglyceride"
                  placeholder="Triglyceride"
                  value={formData.triglyceride}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <input
                  type="number"
                  name="total_cholesterol"
                  placeholder="Total Cholesterol"
                  value={formData.total_cholesterol}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="number"
                  name="ldl"
                  placeholder="LDL"
                  value={formData.ldl}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <input
                  type="number"
                  name="hdl"
                  placeholder="HDL"
                  value={formData.hdl}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="number"
                  name="sbp"
                  placeholder="SBP"
                  value={formData.sbp}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <input
                  type="number"
                  name="dbp"
                  placeholder="DBP"
                  value={formData.dbp}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="number"
                  name="waist_cm"
                  placeholder="Waist (cm)"
                  value={formData.waist_cm}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <button
                onClick={handlePredict}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50 mt-4"
              >
                {loading ? 'Analyzing...' : '🔍 Predict Risk'}
              </button>
            </div>
          </div>

          {/* Result Section */}
          <div className="bg-white rounded-2xl shadow-2xl p-8 flex flex-col justify-center">
            {result ? (
              <div className="text-center">
                <h2 className="text-2xl font-bold text-gray-800 mb-6">Assessment Result</h2>
                
                <div className={`${getRiskColor(result.risk_level)} rounded-full w-40 h-40 mx-ao mb-6 flex items-center justify-center`}>
                  <span className="text-white text-5xl font-bold">
                    {(result.risk_score * 100).toFixed(0)}%
                  </span>
                </div>

                <div className={`${getRiskColor(result.risk_level)} text-white rounded-lg p-4 mb-6`}>
                  <p className="text-2xl font-bold">{result.risk_level} Risk</p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 text-left">
                  <p className="text-gray-700 font-semibold mb-2">Risk Score: {result.risk_score.toFixed(4)}</p>
                  <p className="text-gray-600 text-sm">
                    {result.risk_level === 'Low' && '✅ Your NAFLD risk is low. Maintain healthy lifestyle habits.'}
                    {result.risk_level === 'Moderate' && '⚠️ Your NAFLD risk is moderate. Consult a healthcare provider.'}
                    {result.risk_level === 'High' && '🚨 Your NAFLD risk is high. Seek immediate medical attention.'}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-gray-500 text-lg">📊 Enter patient data and click Predict</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
