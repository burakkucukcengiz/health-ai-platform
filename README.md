# NAFLD Risk Tahmin Platformu

CDC NHANES verisi (1999–2018) kullanılarak metabolik sağlık profiline dayalı NAFLD (yağlı karaciğer hastalığı) risk taraması yapan bir makine öğrenmesi uygulaması. Flask backend ve React frontend'den oluşur.

> **Önemli:** Bu proje bir tanı aracı değildir. Karaciğer biyopsisi ya da görüntüleme yerine vekil bir etiketle eğitilmiştir ve klinik karar yerine geçmez.

## İçindekiler

- [Özellikler](#özellikler)
- [Veri](#veri)
- [Etiket tanımı](#etiket-tanımı)
- [Model ve metrikler](#model-ve-metrikler)
- [Eşik seçimi](#eşik-seçimi)
- [Sınırlılıklar](#sınırlılıklar)
- [Kurulum](#kurulum)
- [API](#api)

## Özellikler

- Cinsiyet, boy, kilo, bel çevresi, tansiyon, trigliserit, LDL, toplam kolesterol ve HDL ile risk skoru hesaplama
- Üç seviyeli sonuç: Düşük, Orta, Yüksek
- Girdi doğrulama ve anlamlı hata mesajları

## Veri

- **Kaynak:** CDC NHANES, 10 döngü (1999–2000 ile 2017–2018 arası)
- **Ham veri:** 101.316 kişideğerleri eksiksiz)

Ham ve işlenmiş veriler repoya dahil değildir (`.gitignore`). Veriyi `scripts/download_multicycle.py`, `scripts/download_1999.py` ve `scripts/download_extra_cycles.py` ile indirip `scripts/clean_multicycle.py` ile temizleyebilirsiniz.

## Etiket tanımı

Modelin hedef değişkeni, karaciğer biyopsisi olmadığı için NAFLD'yi taklit eden bir vekil etikettir:

- ALT yüksek: erkekte > 30 U/L, kadında > 19 U/L
- **VE** en az bir metabolik kriter:
  - Bel çevresi yüksek (erkek ≥ 102 cm, kadın ≥ 88 cm), veya
  - Trigliserit ≥ 150 mg/dL, veya
  - HDL düşük (erkek < 40 mg/dL, kadın < 50 mg/dL)

Pozitif sınıf oranı: %26,6.

Bu etiket FIB-4 ve APRI formüllerinden **türetilmez**. Ancak ALT kullandığı için model FIB-4 bileşenlerinden tamamen bağımsız değildir. Bu, sınırlılıklar bölümünde ayrıca ele alınmıştır.

## Model ve metrikler

- **Algoritma:** **Özellikler (11):** cinsiyet, BMI, kilo, boy, bel çevresi, SBP, DBP, trigliserit, LDL, toplam kolesterol, HDL
- **Özellik olarak kullanılmayanlar:** yaş, AST, ALT, trombosit, FIB-4, APRI, TG/HDL (etiket kaynağı ve sızıntı riski olanlar)

| Metrik | Değer |
|---|---|
| 5-katlı CV AUC | 0.7989 ± 0.0046 |
| Test AUC | 0.7926 |
| Test PR-AUC | 0.4919 |

Eski FIB-4 tabanlı modelde AUC 0.99 çıkmıştı. Bu değer etiket sızıntısından kaynaklanıyordu ve kullanılmıyor.

### Model karşılaştırması

Aynı özellikler, aynı eğitim/test bölünmesi (`random_state=42`, stratified) ve aynı etiket kullanıldı (`scripts/baseline_compare.py`):

| Model | CV AUC (5-katlı) | Test AUC | CV PR-AUC | Test PR-AUC |
|---|---|---|---|---|
| Logistic regression (baseline) | 0.7727 ± 0.0032 | 0.7647 | 0.4836 | 0.4752 |
| Random Forest (seçilen) | 0.7989 ± 0.0046 | 0.7926 | 0.4978 | 0.4919 |

Random Forest, logistic baseline'a göre AUC'de yaklaşık 0.026 (CV) ve PR-AUC'de yaklaşık 0.014 (CV) üstünlük sağlıyor. Fark küçük olmakla birlikte tutarlı. Logistic regressionun güçlü performansı, etiketin büyük ölçüde doğrusal bir kombinasyon olduğunu düşündürüyor; bu bir hipotez olarak değerlendirilmelidir.


## Eşik seçimi

Risk seviyeleri, test setine bakılmadan 5-katlı çapraz doğrulamanın out-of-fold tahminleri üzerinden seçildi (`scripts/threshold_analysis.py`):

- **Orta:** ≥ 0.50
- **Yüksek:** ≥ 0.67

Bu eşikler tarama dilimleri içindir, klinik karar eşiği değildir. Ekranda gösterilen skor bir olasılık değil, modelin ürettiği risk skorudur; `class_weight='balanced'` kullanıldığı için mutlak olasılık olarak yorumlanmamalıdır.

## Sınırlılıklar

- **Vekil etiket:** Biyopsi doğrulaması yok. Sonuçlar gerçek NAFLD tanısı ile örtüşmeyebilir.
- **Düşük precision:** Orta ve üzeri grupta yaklaşık her iki kişiden biri vekil etikete göre pozitiftir.
- **ALT bağımlılığı:** Etiket ALT'ye dayandığı için model, ALT'nin doğrudan ölçülmediği bir senaryoda kullanılamaz.
- **Popülasyon:** Veri ABD nüfusuna aittir; diğer popülas# Gereksinimler

- Python 3.14
- Node.js (npm ile birlikte)

### Backend

```bash
cd backend
python -m venv ../venv
source ../venv/bin/activate
pip install -r requirements_backend.txt
python app.py
```

Backend `http://localhost:8000` adresinde çalışır.

### Frontend

```bash
cd frontend
npm install
npm start
```

Frontend `http://localhost:3000` adresinde açılır.

### Model dosyaları

Model dosyaları Git LFS ile saklanır. Klonlamadan önce `git lfs install` çalıştırın.

## API

### `GET /health`

Servis durumunu ve model bilgisini döndürür.

### `POST /api/predict/nafld`

Örnek istek:

```json
{
  "sex": "male",
  "height_cm": 175,
  "weight_kg": 80,
  "waist_cm": 95,
  "sbp": 120,
  "dbide": 150,
  "ldl": 120,
  "total_cholesterol": 200,
  "hdl": 45
}
```

Örnek yanıt:

```json
{
  "success": true,
  "risk_score": 0.4100,
  "risk_level": "Moderate"
}
```

Hatalı girdide `400`, sunucu hatasında `500` döner.
