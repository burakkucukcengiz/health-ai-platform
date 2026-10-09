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
- **Ham veri:** 101.316 kişi
- **Temiz veri:** 51.613 yetişkin (18 yaş ve üstü, ALT, AST ve BMI değerleri eksiksiz)

Ham ve işlenmiş veriler repoya dahil değildir (`.gitignore`). Veriyi `scripts/download_multicycle.py`ip `scripts/clean_multicycle.py` ile temizleyebilirsiniz.

## Etiket tanımı

Modelin hedef değişkeni, karaciğer biyopsisi olmadığı için NAFLD'yi taklit eden bir vekil etikettir:

- ALT yüksek: erkekte > 30 U/L, kadında > 19 U/L
- **VE** en az bir metabolik kriter:
  - Bel çevresi yüksek (erkek ≥ 102 cm, kadın ≥ 88 cm), veya
  - Trigliserit ≥ 150 mg/dL, veya
  - HDL düşük (erkek < 40 mg/dL, kadın < 50 mg/dL)

Pozitif sınıf oranı: %26,6.

Bu etiket FIB-4 ve APRI formüllerinden türetilmez. Ancak etiketin metabolik yarısı (bel, TG, HDL) modelin girdileriyle aynıdır. Ayrıntı için [sınırlılıklar](#sınırlılıklar) bölümüne bakın.

## Model ve metrikler

- **Algoritma:** Random Forest (300 ağaç, `class_weight='balanced'`)
- **Özellikler (11):** cinsiyet, BMI, kilo, boy, bel çevresi, SBP, DBP, trigliserit, LDL, toplam kolesterol, HDL
- **Modelden çıkarılanlar:** yaş, AST, ALT, trombosit, FIB-4, APRI, TG/HDL oranı (etiket kaynakları ve sızıntı riski olanlar)

Eski FIB-4 tabanlı modelde AUC 0.99 çıkmıştı. Bu değer etiket sızıntısından kaynaklanıyordu ve kullanılmıyor.

### Model karşılaştırması

Aynı özellikler, aynı eğitim/test bölünmesi (`random_state=42`, stratified)  | Test AUC | CV PR-AUC | Test PR-AUC |
|---|---|---|---|---|
| Logistic regression (baseline) | 0.7727 ± 0.0032 | 0.7647 | 0.4836 | 0.4752 |
| Random Forest (seçilen) | 0.7989 ± 0.0046 | 0.7926 | 0.4978 | 0.4919 |

Random Forest, logistic baseline'a göre CV AUC'de yaklaşık 0.026, CV PR-AUC'de yaklaşık 0.014 üstünlük sağlıyor. Fark küçük olmakla birlikte tutarlı. Logistic regression'ın güçlü performansı, etiketin büyük ölçüde doğrusal bir kombinasyon olduğunu düşündürüyor; bu bir hipotez olarak değerlendirilmelidir.

### Hedef-girdi örtüşmesi

| Hedef | Türetildiği değişkenler | Modelde girdi mi? |
|---|---|---|
| Karaciğer (vekil) | ALT, cinsiyet, bel, TG, HDL | ALT: hayır. Cinsiyet, bel, TG, HDL: **evet** |
| FIB-4 (eski model, kullanılmıyor) | Yaş, AST, ALT, trombosit | Eski modelde evet, güncel modelde hayır |

## Eşik seçimi

Risk seviyeleri, test setine bakılmadan 5-katlı çapraz doğrulamanın out-of-fold tahminleri üzerinden seçildi (`scripts/threshold_analysis.py`):

- **Orta:** ≥ ir, klinik karar eşiği değildir. Ekranda gösterilen skor bir olasılık değil, modelin ürettiği risk skorudur; `class_weight='balanced'` kullanıldığı için mutlak olasılık olarak yorumlanmamalıdır.

## Sınırlılıklar

- **Vekil etiket:** Biyopsi doğrulaması yok. Sonuçlar gerçek NAFLD tanısı ile örtüşmeyebilir.
- **Etiket ve girdi örtüşmesi:** Etiket bel çevresi, trigliserit ve HDL kullanır; bunlar modelin de girdisidir. AUC bu nedenle kısmen kuralın yeniden üretilmesinden gelir.
- **Düşük precision:** Orta ve üzeri grupta yaklaşık her iki kişiden biri vekil etikete göre pozitiftir (0.50 eşiğinde precision ≈ 0.48).
- **Eşikler aynı veriden seçildi:** Eşikler out-of-fold tahminlerle seçildi; bağımsız bir dış veri seti yoktur.
- **Popülasyon:** Veri ABD nüfusuna aittir; diğer popülasyonlarda performans farklı olabilir.
- **Kalibrasyon:** Skorlar kalibre edilmemiştir, mutlak olasılık olarak yorumlanmamalıdır.

## Kurulum

### Gereksinimler

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

Model dosyaları Git LFS ile saklanır. Klonlamadan önce `git lfs install` ç sürebilir.

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
  "dbp": 80,
  "triglyceride": 150,
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
  "risk_level": "Low"
}
```

Hatalı girdide `400`, sunucu hatasında `500` döner.
