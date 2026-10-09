# NAFLD Risk Tahmin Platformu

CDC NHANES verisi (1999–2018) kullanılarak metabolik sağlık profiline dayalı NAFLD (yağlı karaciğer hastalığı) ve metabolik sendrom risk taraması yapan bir makine öğrenmesi uygulaması. Flask backend ve React frontend'den oluşur.

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

- **Kaynak:** CDC NHANES, 10 döngü (1999–2000 i** 51.613 yetişkin (18 yaş ve üstü, ALT, AST ve BMI değerleri eksiksiz)
- **Metabolik sendrom alt kümesi:** 18.009 kişi (açlık glikozu ölçülmüş olanlar; bkz. aşağıda)

Ham ve işlenmiş veriler repoya dahil değildir (`.gitignore`). Veriyi `scripts/download_multicycle.py` ve `scripts/clean_multicycle.py` ile temizleyebilirsiniz. Metabolik sendrom alt kümesi için ayrıca `scripts/download_glucose.py` ve `scripts/merge_metabolic.py` çalıştırılmalıdır.

## Etiket tanımı

### NAFLD (vekil etiket)

Modelin hedef değişkeni, karaciğer biyopsisi olmadığı için NAFLD'yi taklit eden bir vekil etikettir:

- ALT yüksek: erkekte > 30 U/L, kadında > 19 U/L
- **VE** en az bir metabolik kriter:
  - Bel çevresi yüksek (erkek ≥ 102 cm, kadın ≥ 88 cm), veya
  - Trigliserit ≥ 150 mg/dL, veya
  - HDL düşük (erkek < 40 mg/dL, kadın < 50 mg/dL)

Pozitif sınıf oranı: %26,6.

Bu etiket FIB-4 ve APRI formüllerinden türetilmez. Ancak etiketin metabolik yarısı (bel, TG, HDL) modelin girdileriyle aynıdır. Ayrıntı için [sınırlılıklar](#sınırlılıklar) bölümüne bakın.

### Metabolik sendrom (ATP III)

İkinci bir hedef olarak, standart ATP III kriterleri kullanılarak metabolik sendrom etiketi oluşturulmuştur (5 kriterden ≥3'ü karşılanırsa pozitif):

- Bel çevresi yüksek (erkek ≥ 102 cm, kadın ≥ 88 cm)
- Trigliserit ≥ 150 mg/dL
- HDL düşük (erkek < 40 mg/dL, kadın < 50 mg/dL)
- Tansiyon yüksek (SBP ≥ 130 veya DBP ≥ 85)
- Açlık glikozu ≥ 100 mg/dL

Açlık glikozu NHANES'in sadece açlık alt örnekleminde ölçüldüğü için, bu etiket 18.009 kişilik bir alt kümede tanımlıdır. Pozitif sınıf oranı: %32,6.

**Önemli not:** Bu kriterlerin 4'ü (glikoz hariç) modelin girdi değişkenleriyle doğrudan aynıdır. Bu durumun modelin performans metriklerine etkisi [Model ve metrikler](#model-ve-metrikler) bölümünde ayrıca ele alınmıştır.

## Model ve metrikler

- **Algoritma:** Random Forest (300 ağaç, `class_weight='balanced'`)
- **Özellikler (11):** cinsiyet, BMI, kilo, boy, bel çevresi, SBP, DBP, trigliserit, LDL, toplam kolesterol, HDL
- **Modelden çıkarılanlar (NAFLD modeli):** yaş, AST, ALT, trombosit, FIB-4, APRI, TG/HDL oranı (etiket kaynakları ve sızıntı riski olanlar)

Eski FIB-4 tabanlı modelde AUC 0.99 çıkmıştı. Bu değer etiket sızıntısından kaynaklanıyordu ve kullanılmıyor.

### Model karşılaştırması (NAFLD)

Aynı özellikler, aynı eğitim/test bölünmesi (`random_state=42`, stratified):

| Model | CV AUC | Test AUC | CV PR-AUC | Test PR-AUC |
|---|---|---|---|---|
| Logistic regression (baseline) | 0.7727 ± 0.0032 | 0.7647 | 0.4836 | 0.4752 |
| Random Forest (seçilen) | 0.7989 ± 0.0046 | 0.7926 | 0.4978 | 0.4919 |

Random Forest, logistic baseline'a göre CV AUC'de yaklaşık 0.026, CV PR-AUC'de yaklaşık 0.014 üstünlük sağlıyor. Fark küçük olmakla birlikte tutarlı. Logistic regression'ın güçlü performansı, etiketin büyük ölçüde doğrusal bir kombinasyon olduğunu düşündürüyor; bu bir hipotez olarak değerlendirilmelidir.

### Hedef-girdi örtüşmesi (NAFLD)

| Hedef | Türetildiği değişkenler | Modelde girdi mi? |
|---|---|---|
| Karaciğer (vekil) | ALT, cinsiyet, bel, TG, HDL | ALT: hayır. Cinsiyet, bel, TG, HDL: **evet** |
| FIB-4 (eski model, kullanılmıyor) | Yaş, AST, ALT, trombosit | Eski modelde evet, güncel modelde hayır |

### Metabolik sendrom modeli ve sızıntı derecesi

Metabolik sendrom etiketinde, NAFLD etiketine göre çok daha ciddi bir örtüşme vardır: 5 ATP III kriterinden 4'ü (bel, TG, HDL, tansiyon) modelin girdi değişkenleriyle birebir aynıdır. Sadece açlık glikozu modele görünmez. Bunun etkisini ölçmek için, modelsiz bir referans kural tanımlandı: görünür 4 kriterin basit toplamı (0–4).

| Yaklaşım | Test AUC | Test PR-AUC |
|---|---|---|
| Naive kural (sadece 4 kriterin toplamı, model yok) | 0.9624 | 0.8827 |
| Random Forest (11 özellik) |orest'ın eklediği gerçek tahmin değeri çok küçüktür (yaklaşık 0.013 AUC puanı) ve esas olarak glikoz kriterinin dolaylı olarak diğer değişkenlerden kısmen tahmin edilebilmesinden kaynaklanır.

Bu, aynı projede iki farklı sızıntı derecesini karşılaştırmak için kullanılmıştır:

| Model | Sızıntı türü | Model AUC | Referans/naive AUC | Modelin net katkısı |
|---|---|---|---|---|
| NAFLD (vekil) | Kısmi (3/5 bileşen girdide, ALT girdide değil) | 0.7926 | — (ALT ölçülmeden naive kural kurulamaz) | Anlamlı (logistic'e göre de +0.026) |
| Metabolik sendrom | Neredeyse tam (4/5 kriter doğrudan girdi) | 0.9752 | 0.9624 | Çok düşük (+0.013) |

**Pratik sonuç:** Metabolik sendrom skoru, bir "AI tahmini" olarak değil, büyük ölçüde "kaç ATP III kriterini karşılıyorsunuz" sorusunun otomatik bir özeti olarak yorumlanmalıdır. Uygulamada bu skor bu şekilde sunulur.

## Eşik seçimi

Risk seviyeleri, test setine bakılmadan 5-katlı çapraz doğrulamanın out-of-fold tahminleri üzerinden seçildi (`scripts/threshold_analysis.py`):

- **Orta:** ≥ 0.50
- **Yüksek:** ≥ 0.67

Bu eşikler klinik karar eşiği değildir. Ekranda gösterilen skor bir olasılık değil, modelin ürettiği risk skorudur; `class_weight='balanced'` kullanıldığı için mutlak olasılık olarak yorumlanmamalıdır.

## Sınırlılıklar

- **Vekil etiket:** Biyopsi doğrulaması yok. Sonuçlar gerçek NAFLD tanısı ile örtüşmeyebilir.
- **Etiket ve girdi örtüşmesi (NAFLD):** Etiket bel çevresi, trigliserit ve HDL kullanır; bunlar modelin de girdisidir. AUC bu nedenle kısmen kuralın yeniden üretilmesinden gelir.
- **Etiket ve girdi örtüşmesi (metabolik sendrom):** Çok daha ciddi — 5 kriterden 4'ü modelin girdisiyle birebir aynıdır. Naive kural karşılaştırması bu bölümde ayrıntılıdır; modelin katkısı sınırlıdır.
- **Düşük precision (NAFLD):** Orta ve üzeri grupta yaklaşık her iki kişiden biri vekil etikete göre pozitiftir (0.50 eşiğinde precision ≈ 0.48).
- **Eşikler aynı veriden seçildi:** Eşikler out-of-fold tahminlerle seçildi; bağımsız bir dış veri seti yoktur.
- **Popülasyon:** Veri ABD nüfusuna aittir; diğer popülasyonlarda performans farklı olabilir.
- **Kalibrasyon:** Skorlar kalibre edilmemiştir, mutlak olasılık olarak yorumlanmamalıdır.
- **Metabolik sendrom alt örneklemi:** Sadece açlık glikozu ölçülen 18.009 kişiyi kapsar; tüm NHANES örneklemini temsil etmeyebilir.

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

Model dosyaları Git LFS ile saklanır. Klonlamadan önce `git lfs install` komutunu çalıştırmanız gerekebilir.

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

### `POST /api/predict/mets`

Metabolik sendrom kriter özeti (ATP III, glikoz hariç 4 kriter). Aynı girdi alanlarını kullanır.

Örnek istek: yukarıdakiyle aynı JSON gövdesi.

Örnek yanıt:

```json
{
  "success": true,
  "criteria_met": 1,
  "criteria_total": 4,
  "criteria_detail": {
    "waist": false,
    "triglyceride": true,
    "hdl": false,
    "blood_pressure": false
  },
  "risk_level": "Low",
  "model_score": 0.4100,
  "note": "Glikoz olculmedigi icin tam ATP III tanisi (5 kriter) yapilamaz; bu sonuc 4 kriterin bir ozetidir."
}
```

`model_score` ikincil/deneysel bir alandır; birincil çıktı `criteria_met` ve `risk_level`dir (bkz. [Metabolik sendrom modeli ve sızıntı derecesi](#model-ve-metrikler)).
