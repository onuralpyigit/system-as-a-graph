# ADR-0013: Model Verisi dosya biçimi ve sürümleme

> Bu doküman [0013-model-data-file-format.md](0013-model-data-file-format.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi |
| Tür | Onaylama (Ratify) |
| İzlenen | MDG.1, 14–15, 18, 22–23; SMM.2–3, 26; DVE.5; QA-03, QA-04 |
| Kapatır | CDR-29 (kısmi: Model Verisi dosyası), CDR-30 (kısmi: Model Verisi dosyası) |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

MDG.23, MDG'nin veriyi "Model Verisi dosyası olarak kaydetmesini", SMM.2–3 ise SMM'nin bu dosyayı kabul edip doğrulamasını ister. DVE.5, seçim başına Model Verisi dosyalarını listeler.

Mevcut durumda `FilesystemModelSetupDataStore`, çalıştırma başına bir JSON dosyası yazar:

```
<workspace>/<proje>/<platform>/<sürüm>/<run_id>/<proje>_<platform>_<sürüm>.json
```

Dosyanın üst düzey bölümleri `context`, `inventory`, `acquired_files`, `errors`, `generated_at`, `produced_by` ve `graph`'tır. `graph` bölümünde `metadata.scale`, `nodes`, `topics`, `applications`, `libraries` ve `relationships.{runs_on, publishes_to, subscribes_to, uses}` bulunur. `run_id`, Celery görev kimliğidir.

Dosyanın şema sürümü ve yayımlanmış bir şeması yoktur. Zaman damgaları yerel saatte ve saat dilimsizdir. Bazı uygulama öznitelikleri (`priority`, `hotstandby`) yer tutucu olarak tohumlanmış rastgele bir üreteçle doldurulur.

## Karar Etkenleri

* SMM, dosyanın biçimini, şemasını, bütünlüğünü ve zorunlu alanlarını doğrulamalıdır (SMM.3); bu da yayımlanmış bir şema gerektirir.
* Biçim geliştikçe dosyalar okunabilir kalmalıdır (DVE.5 eski çalıştırmaları listeler).
* Bir çalıştırmanın dosyası, ondan türetilen her sonucun kanıtıdır (QA-04); bu yüzden değiştirilemez ve özetle tanımlanabilir olmalıdır.
* Yer tutucu değerler asla alınmış gerçeklerle karıştırılmamalıdır (QA-03).

## Değerlendirilen Seçenekler

* Dosya sisteminde çalıştırma başına JSON dosyası (mevcut); sürümlü ve şemayla doğrulanır hâle getirilir
* Model Verisini ilişkisel depoda satırlar olarak saklamak
* Doğrudan bir çizge veri tabanı içe aktarma biçiminde yazmak

## Karar Sonucu

Seçilen seçenek: "Dosya sisteminde çalıştırma başına JSON dosyası; sürümlü ve şemayla doğrulanır hâle getirilir", çünkü biçim çalışır, insan tarafından incelenebilir ve indirilebilir (mevcut `/download` uç noktası). SRS de açıkça bir *dosyadan* söz eder.

* **Konum:** değişmez. Çalışma alanı kökü yapılandırmadan gelir (ADR-0039) ve kurulumda kalıcı bir birimdir.
* **Adlandırma:** `run_id`, üreten işlemin işlem kimliği olur (ADR-0024). Dosya adı değişmez.
* **Şema:**
  * Üst düzeye `"schema_version": "1.0"` eklenir.
  * `mdg/schemas/model-data-1.0.schema.json` konumunda bir JSON Şeması tanımlanır.
  * MDG dosyayı kaydetmeden önce doğrular; SMM girişte yeniden doğrular (SMM.3).
  * Şema 1.0'da bölüm adları kanonik terminolojiye göre yeniden adlandırılır (ADR-0002).
* **Evrim:** küçük sürümler yalnızca isteğe bağlı alanlar ekler. Büyük sürüm değişikliği, önceki büyük sürüm için bir okuyucuyla birlikte gelir; böylece listeleme (DVE.5) ve model inşası mevcut dosyalarla çalışmaya devam eder.
* **Değiştirilemezlik ve bütünlük:**
  * dosya bir kez, geçici bir adla yazılır ve sonra atomik olarak yeniden adlandırılır;
  * SHA-256 özeti çıktı kaydına kaydedilir (ADR-0035);
  * SMM, inşadan önce özeti doğrular.
* **Zaman damgaları:** ofsetli UTC olarak ISO 8601.
* **Yer tutucular:** alınmamış değerler `null` olarak yazılır ve JSON yolları ve nedenleriyle birlikte bir `placeholders` dizisinde listelenir. Örnekler, bugünün rastgele `priority`/`hotstandby` değerleri ve taklit QoS'tur. `"NOT_FOUND"` gözcü dizgisi kullanımdan kaldırılır. Çizge inşası (ADR-0014), yer tutucuları gerçeğe dönüştürmez.
* **Köken bilgisi bloğu:** `produced_by`, üreten işlem kimliği, araç sürümü ve birim başına klon commit özeti (ADR-0035).

### Sonuçlar

* İyi, çünkü SMM doğrulayabileceği bir sözleşmeye kavuşur ve eski dosyalar okunabilir kalır.
* İyi, çünkü sonuçlar bayt düzeyinde özdeş bir girdiye kadar izlenebilir.
* Kötü, çünkü şema 1.0'dan önceki mevcut dosyalarda sürüm alanı yoktur. Bir okuyucu bunları `0.x` olarak ele alır (en iyi çaba, salt okunur).
* Kötü, çünkü `ModelSetupDataGraph` içindeki rastgele yer tutucu mantığı kaldırılmalıdır.

### Doğrulama

* Bir birim testi, `produce_model_setup_data` çıktısını JSON Şemasına göre doğrular.
* Bir test, çıktıda hiç `"NOT_FOUND"` dizgisi ve rastgele değer bulunmadığını doğrular.

## Seçeneklerin Artıları ve Eksileri

### Çalıştırma başına JSON dosyası (mevcut, sürümlü)

* İyi, çünkü basit, incelenebilir ve indirilebilirdir; SRS ifadesiyle örtüşür.
* Kötü, çünkü çalıştırmalar arası sorgu yoktur. Listeleme her dosyanın başlığını okur; beklenen çalıştırma sayılarında bu kabul edilebilir.

### İlişkisel satırlar

* İyi, çünkü sorgulanabilir.
* Kötü, çünkü çizge biçimli yük birçok tabloya bölünür ve tek dosyalık kanıt kaybolur.

### Çizge veri tabanı içe aktarma biçimi

* İyi, çünkü hızlı yüklenir.
* Kötü, çünkü MDG'yi ADR-0015'in depolama seçimine bağlar ve insan tarafından okunamaz.

## Ek Bilgiler

* Kod: `mdg/src/mdg/domain/model_setup_data.py`, `model_setup_data_graph.py`, `workspace.py`, `adapters/model_setup_data/`
* İlgili: ADR-0002, ADR-0014, ADR-0024, ADR-0035
