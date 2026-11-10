# ADR-0024: Bulgu ve işlem kaydı modeli

> Bu doküman [0024-findings-and-operation-records.md](0024-findings-and-operation-records.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi |
| Tür | Karar (Decide) |
| İzlenen | DVE.6, 15–16, 18, 21–26, 77–78; SMM.26; QA-04, QA-08 |
| Kapatır | CDR-30 (kısmi: Bulgular, İşlemler ve Raporlar) |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SRS ayrıntılı kayıtlar ister:

* DVE.21, her bulgunun içeriğini listeler.
* DVE.22, aynı işlemin bulguları arasında neden-sonuç bağlantıları ister.
* DVE.23, sıralama ve filtreleme ister.
* DVE.24, başarısız işlemlerin hata nedenini, kesinti aşamasını ve zamanını ister.
* DVE.25, simülasyonların senaryo üst verisini ister.
* DVE.26, raporların içeriğini listeler.
* DVE.78, bağımsız işlem tanımlayıcıları ve birim başına sonuçlar ister.

Bugün tek işlem kaydı bir Celery görevidir (kimlik, durum, ilerleme üst verisi, sonuç) ve bir Redis günlük listesidir (ADR-0006). R3 ilk bulguları üretir; bu yüzden modelleri şimdi sabitlenmelidir.

## Karar Etkenleri

* Model Verisi üretiminden kurulum değerlendirmesine kadar her uzun süren etkinlik için tek bir işlem modeli.
* Bulgular, DVE.21'in listelediği her şeyi taşımalı ve DVE.23'ün her alanına göre filtrelenebilmelidir.
* Sonuçlar kaydedilmiş girdilerden yeniden üretilebilir olmalıdır (QA-04).
* Raporlar (DVE.26) ve otomasyon sonucu (DVE.78, ADR-0028) bu kayıtlardan üretilir, ayrıca saklanmaz.

## Değerlendirilen Seçenekler

* Değişken kısımlar için JSONB ile ilişkisel kayıtlar (işlemler, bulgular, bulgu bağlantıları)
* Model öğelerine bağlı bir çizge olarak bulgular
* İşlem kaydına gömülü bir JSON dokümanı olarak bulgular

## Karar Sonucu

Seçilen seçenek: PostgreSQL'de (ADR-0008) "Değişken kısımlar için JSONB ile ilişkisel kayıtlar", çünkü DVE.23'ün çok alanlı filtreleme ve sıralaması doğrudan indeksli sütunlara eşlenir. Değişken kanıt ise JSONB'ye uyar.

**`operation`**

| Sütun | Notlar |
|---|---|
| `operation_id` | API'nin ürettiği UUID; kullanıcılara ve otomasyon istemcilerine sunulan tanımlayıcı (DVE.78) |
| `parent_operation_id` | Çok birimli bir değerlendirmenin birim başına alt işlemleri için atanır (DVE.78) |
| `type` | `model_data_production`, `model_construction`, `synthetic_data_production`, `aed_production`, `structural_verification`, `simulation_analysis`, `field_analysis`, `installation_evaluation` |
| `project`, `platform`, `system_version` | Seçim (DVE.4) |
| `requested_by`, `client_kind` | Kullanıcı adı veya otomasyon istemcisi kimliği; `ui` / `cli` / `automation` |
| `inputs` | JSONB: model örneği kimliği ve revizyonu, AED başvurusu, kural kataloğu sürümü ve profili, senaryo girdileri (DVE.25), parametreler |
| `state` | `queued`, `running`, `succeeded`, `failed`, `cancelled` |
| `progress` | JSONB `{percent, phase}` |
| `result` | `conforming` / `non-conforming` / null (DVE.18); kurulum değerlendirmesi için ayrıca puan, sınıf ve karar (ADR-0027) |
| `failure` | JSONB hata kaydı (ADR-0034) ve `stage` (DVE.24) |
| `queued_at`, `started_at`, `ended_at` | UTC |
| `executor_ref` | Celery görev kimliği (iç) |

**`finding`** (DVE.21)

| Sütun | Notlar |
|---|---|
| `finding_id` | UUID; `<işlem kısa kimliği>-<sıra>` olarak gösterilir |
| `operation_id` | Sahip işlem |
| `rule_id`, `rule_version` | İlgili doğrulama kuralı (ADR-0022/0023) |
| `finding_type` | Ör. `qos_mismatch`, `unpublished_topic`, `cycle`, `capacity_exceeded`, `drift_missing` |
| `severity` | `informational`, `low`, `medium`, `high`, `critical` |
| `description` | Metin |
| `affected` | Varlık başvuruları `{label, key}` ve ilişki başvuruları `{type, from, to}` içeren JSONB dizisi (ADR-0014) |
| `acceptance_criterion` | Yürütme anında kuraldan kopyalanır |
| `evidence` | Destekleyici veriyi içeren JSONB |
| `blocking` | Kuraldan kopyalanır |

**`finding_link`** (DVE.22): `(cause_finding_id, effect_finding_id, kind)`. İki bulgu da aynı işleme aittir.

**Günlük:** `operation_log(operation_id, seq, at, level, message)`. Redis listesinin yerini alır (ADR-0006).

**Raporlar (DVE.26):** ADR-0029 tarafından istek üzerine bu tablolardan üretilir. Rapor üst verisi (kimlik, biçim, işlem, üretim zamanı, üreten) saklanır. Dosyanın kendisi çıktı deposuna gider (ADR-0035).

İndeksler: `finding(operation_id, severity)`, `finding(rule_id)`, `finding(finding_type)`, `affected` üzerinde bir GIN indeksi ve `operation(project, platform, system_version, type, queued_at)`.

### Sonuçlar

* İyi, çünkü DVE.21–26 içeriği yapı gereği karşılanır ve filtreleme düz SQL'dir.
* İyi, çünkü aynı kayıtlar arayüzü, raporları ve CI sonucunu besler.
* Kötü, çünkü model geliştikçe göç gerektiren üç tablo ve bir günlük vardır.
* Kötü, çünkü etkilenen varlık anahtarları, ileride silinebilecek çizge öğelerine başvurur (örneğin süresi dolar, ADR-0040). Bulgular anahtarları ve örnek kimliğini tarihsel başvurular olarak korur.

### Doğrulama

* PostgreSQL üzerinde göç ve depo testleri (ADR-0008).
* Bir test, motorun (ADR-0022) ürettiği her bulgunun DVE.21 alanlarının hepsinin dolu olduğunu doğrular.

## Seçeneklerin Artıları ve Eksileri

### İlişkisel + JSONB

* İyi, çünkü indeksli filtreleme, kısıtlar ve işlemlerle birleştirme sağlar.
* Kötü, çünkü şema göç işi gerekir.

### Çizgede bulgular

* İyi, çünkü etkilenen düğümlere doğrudan bağlantı verir.
* Kötü, çünkü örnekler silindiğinde bulgular kaybolur; Cypher'da filtreleme ve sayfalama daha zayıftır.

### İşlem başına JSON dokümanı

* İyi, çünkü yazması basittir.
* Kötü, çünkü işlemler arası filtreleme (DVE.23), dokümanları taramak demektir.

## Ek Bilgiler

* [SRS §6.1.1](../../requirements/SRS.tr.md)
* İlgili: ADR-0006, ADR-0008, ADR-0022, ADR-0027, ADR-0028, ADR-0029, ADR-0034, ADR-0035
