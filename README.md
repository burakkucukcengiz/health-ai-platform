# NAFLD Risk Tahmin Platformu

CDC NHANES verisi (1999-2018) kullanılarak metabolik sağlık profiline dayalı NAFLD (yağlı karaciğer hastalığı), metabolik sendrom ve insulin direnci (HOMA-IR) risk taraması yapan bir makine öğrenmesi uygulaması. Flask backend ve React frontend'den oluşur.

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
- Üç ayrı model: NAFLD riski, metabolik sendrom kriter özeti, insulin direnci (HOMA-IR) riski
- Üç seviyelmlı hata mesajları

## Veri

- **Kaynak:** CDC NHANES, 10 döngü (1999-2018)
- **Örneklem:** 51.613 yetişkin (18 yaş ve üstü, ALT, AST ve BMI değerleri eksiksiz)
- **Metabolik sendrom alt kümesi:** 18.009 kişi (açlık glikozu ölçülmüş olanlar; bkz. aşağıda)
- **HOMA-IR (insulin direnci) alt kümesi:** 7.562 kişi (insulin ölçümü sadece 2013-2014, 2015-2016 ve 2017-2018 döngülerinde mevcut; bkz. `scripts/download_insulin.py`)

Ham ve işlenmiş veriler repoya dahil değildir (`.gitignore`). Veriyi `scripts/download_multicycle.py` ve `scripts/clean_multicycle.py` ile temizleyebilirsiniz. Metabolik sendrom alt kümesi için ayrıca `scripts/download_glucose.py` ve `scripts/merge_metabolic.py`, HOMA-IR alt kümesi için `scripts/download_insulin.py` ve `scripts/merge_homa.py` çalıştırılmalıdır.

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

### HOMA-IR (insulin direnci)

Üçüncü bir hedef olarak, HOMA-IR (Homeostatic Model Assessment for Insulin Resistance) formülüyle insulin direnci etiketi oluşturulmuştur:

HOMA-IR = (açlık glikozu [mg/dL] × açlık insulini [uIU/mL]) / 405

Klinik olarak yaygın kullanılan eşik: HOMA-IR ≥ 2,5 → insulin direnci pozitif kabul edilir. Bu eşiğe göre örneklemin %49,5'i pozitiftir (dengeli bir sınıf dağılımı).

**Önemli fark:** Bu etiket glikoz ve insulin ölçümlerinden hesaplanır, ancak **modelin girdi listesine glikoz veya insulin dahil edilmez** — model yalnızca NAFLD ve MetS modelleriyle aynı 11 özelliği (vücut ölçüleri ve lipid paneli) kullanır. Bu, NAFLD (kısmi örtüşme) ve metabolik sendromun (neredeyse tam örtüşme) aksine, **sıfır özellik-etiket örtüşmesi** olan tek hedeftir. Bu yüzden bu model, projedeki "sızıntı derecesi" karşılaştırmasının referans (temiz) ucunu oluşturur.

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

Metabolik sendrom etiketinde, NAFLD etiketine göre çok daha ciddi bir örtüşme vardır: 5 ATP III kriterinden 4'ü (bel, TG, HDL, tansiyon) modelin girdi değişkenleriyle birebir aynıdır. Sadece açlık glikozu modele görünmez. Bunun etkisini ölçmek için, modelsiz bir referans kural tanımlandı: görünür 4 kriterin basit toplamı (0-4).

| Yaklaşım | Test AUC | Test PR-AUC |
|---|---|---|
| Naive kural (sadece 4 kriterin toplamı, model yok) | 0.9624 | 0.8827 |
| Random Forest (11 özellik) | 0.9752 | 0.9474 |
| **Modelin gerçek katkısı** | **+0.0128** | — |

Random Forest'ın eklediği gerçek tahmin değeri çok küçüktür (yaklaşık 0.013 AUC puanı) ve esas olarak glikoz kriterinin dolaylı olarak diğer değişkenlerden kısmen tahmin edilebilmesinden kaynaklanır.

### HOMA-IR modeli: sızıntısız referans

HOMA-IR modelinde glikoz ve insulin hiç özellik olarak kullanılmadığı için (sadece hedef üretiminde kullanıldılar), bu model sızıntı içermeyen bir referans noktası sağlar. Aynı 11 özellikle, aynı eğitim/test bölünmesiyle:

| Model | CV AUC | Test AUC | CV PR-AUC | Test PR-AUC |
|---|---|---|---|---|
| Logistic regression | 0.8370 | 0.8141 | 0.8287 | 0.8069 |
| Random Forest | 0.8323 | 0.8127 | 0.8315 | 0.8120 |

Dikkat çekici nokta: logistic regression, Random Forest'tan daha iyi ya da eşdeğer performans gösteriyor (0.8141 vs 0.8127). Bu, metabolik sendrom modelinde görülenin tam tersidir — orada Random Forest, kriterleri örtük biçimde ezberleyerek naive kuralın üzerine çıkıyordu. Burada ezberlenecek bir kriter kümesi olmadığı için, basit ve karmaşık modeller benzer sonuç veriyor; bu da gerçek bir ilişkinin öğrenildiğine işaret eder.

### Üç modelin sızıntı derecesi karşılaştırması

Aşağıdaki tablo, aynı 11 özellikle eğitilen üç modelin hedef-girdi örtüşmesini ve bunun model performansına etkisini karşılaştırır:

| Model | Sızıntı türü | Model AUC | Referans/naive AUC | Modelin net katkısı |
|---|---|---|---|---|
| NAFLD (vekil) | Kısmi (3/5 bileşen girdide, ALT girdide değil) | 0.7926 | — (ALT ölçülmeden naive kural kurulamaz) | Anlamlı (logistic'e göre de +0.026) |
| Metabolik sendrom | Neredeyse tam (4/5 kriter doğrudan girdi) | 0.9752 | 0.9624 | Çok düşük (+0.013) |
| HOMA-IR (insulin direnci) | Yok (glikoz/insulin hiç girdi değil) | 0.8127 (RF) / 0.8141 (logistic) | — (kriterler girdide olmadığı için naive kural kurulamaz) | Sızıntı yok; basit model karmaşık modelden geride kalmıyor |

**Pratik sonuç:** Metabolik sendrom skoru, bir "AI tahmini" olarak değil, büyük ölçüde "kaç ATP III kriterini karşılıyorsunuz" sorusunun otomatik bir özeti olarak yorumlanmalıdır. Uygulamada bu skor bu şekilde sunulur. HOMA-IR modeli ise, aynı özellik setiyle gerçekten "öğrenilmiş" bir ilişkinin neye benzediğini gösteren bir karşılaştırma noktasıdır.

## Eşik seçimi

Risk seviyeleri, test setine bakılmadan 5-katlı çapraz doğrulamanın out-of-fold tahminleri üzerinden seçildi (`scripts/threshold_analysis.py`, HOMA-IR için `scripts/threshold_homa.py`):

**NAFLD modeli:**
- **Orta:** ≥ 0.50
- **Yüksek:** ≥ 0.67

**HOMA-IR modeli:**
- **Orta:** ≥ 0.40 (OOF precision 0.696, recall 0.838)
- **Yüksek:** ≥ 0.60 (OOF precision 0.808, recall 0.657)

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
- **HOMA-IR alt örneklemi:** Sadece insulin ölçümü yapılan 2013-2018 döngülerindeki 7.562 kişiyi kapsar (ana veri setinin ~%15'i); daha küçük ve daha yeni döngülere ait olduğu için diğer modellerle doğrudan karşılaştırılırken bu fark göz önünde bulundurulmalıdır. HOMA-IR ≥ 2,5 eşiği yaygın kullanılan bir klinik referans değeridir, kesin tanı ölçütü değildir.

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

### `POST /api/predict/homair`

İnsulin direnci (HOMA-IR ≥ 2,5) riski. Aynı girdi alanlarını kullanır; glikoz veya insulin değeri istenmez.

Örnek istek: yukarıdakiyle aynı JSON gövdesi.

Örnek yanıt:

```json
{
  "success": true,
  "risk_score": 0.5800,
  "risk_level": "Moderate",
  "note": "Bu model glikoz ve insulin degerlerini OZELLIK OLARAK KULLANMAZ; bunlar sadece egitim hedefini (HOMA-IR >= 2.5) hesaplamak icin kullanildi. Bu nedenle NAFLD ve MetS modellerinden farkli olarak sizinti icermez."
}
```

Bu model, projedeki üç model arasında sızıntı içermeyen tek modeldir (bkz. [Üç modelin sızıntı derecesi karşılaştırması](#model-ve-metrikler)). Hatalı girdide `400`, sunucu hatasında `500` döner.
