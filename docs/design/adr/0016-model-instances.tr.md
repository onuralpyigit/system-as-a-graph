# ADR-0016: Model örnekleri: temel, çalışma ve aday değerlendirme modelleri

> Bu doküman [0016-model-instances.md](0016-model-instances.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi |
| Tür | Karar (Decide) |
| İzlenen | SMM.26, 29–31, 36; DVE.17, 28–30, 50–51, 71–78; MDG.15; QA-02, QA-03, QA-04 |
| Kapatır | CDR-29 (kısmi: Çalışma Modeli) |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SRS üç tür Sistem Modeli ima eder:

1. **Temel model:** bir Model Verisi dosyasından inşa edilir (SMM.4). Doğrulama veya analiz (DVE.29, 51) ya da veri bağlama (SMM.36) tarafından asla değiştirilmemelidir.
2. **Çalışma modeli:** "Sistem Modelinden türetilen", kullanıcının düğüm ve ilişki ekleyip çıkardığı ve doğrulama çalıştırdığı model (DVE.17).
3. **Aday değerlendirme modeli:** bir aday yazılım birimi sürümünü hedef sistem sürümüyle birleştiren "işleme özgü yeni bir Sistem Modeli" (SMM.31). MDG.15, adayın envanterde yer aldığı (`is_candidate`) bir Model Verisi dosyasını zaten üretir.

Bunlar, eşzamanlı kullanıcılar ve hat işlemleri altında birbirini etkilemeden bir arada bulunmalıdır (SMM.29–30).

## Karar Etkenleri

* Temel modeller kural gereği değil, yapı gereği değiştirilemez olmalıdır (QA-03).
* Bir çalışma veya aday modeli oluşturmak ve atmak ucuz olmalıdır (QA-02).
* Çalışma modeli düzenlemeleri izlenebilir ve raporlanabilir olmalıdır (DVE.17, DVE.26, QA-04).
* Hattan gelen aday değerlendirmeleri paralel ve bağımsız çalışır (DVE.78).

## Değerlendirilen Seçenekler

* Örnek başına ayrı adlandırılmış çizge; çalışma modelleri temel modellerinden kopyalanır
* Fark katmanı: çalışma modelleri, sorgu sırasında temel modelin üzerine uygulanan bir değişiklik seti olarak saklanır
* İşlem başına tam kopya: her doğrulama çalıştırması temel modeli kopyalar

## Karar Sonucu

Seçilen seçenek: "Örnek başına ayrı adlandırılmış çizge; çalışma modelleri temel modellerinden kopyalanır". Her örnek, kuralların özel bir mantık gerekmeden sorguladığı sıradan bir çizgedir. Seçilen depoda kopyalama ucuzdur (ADR-0015, `GRAPH.COPY`). Düzenleme geçmişi izlenebilirlik için yine de bir değişiklik günlüğü olarak tutulur.

| Tür | Kaynağı | Değiştirilebilirlik | Sahibi | Ömrü |
|---|---|---|---|---|
| `baseline` | Bir Model Verisi dosyası (SMM.4) | İnşadan sonra değiştirilemez | Sistem | ADR-0040'a göre saklanır |
| `working` | Bir temel modelin (veya başka bir çalışma modelinin) kopyası | Yalnızca SMM'nin çalışma modeli API'si üzerinden düzenlenir | Tek kullanıcı | Sahibi silene veya süresi dolana kadar (ADR-0040) |
| `candidate` | Bir adayla üretilmiş kendi Model Verisi dosyası (MDG.15) | İnşadan sonra değiştirilemez | Tek işlem | Değerlendirme işlemi bitince, bulgular kalıcı hâle getirildikten sonra silinir |

* **Kayıt:** her örnek, ilişkisel depoda (ADR-0008) şu alanları içeren bir tabloda bir satırdır:
  * `instance_id`, `kind`, `parent_instance_id`;
  * `model_data_ref` ve özeti;
  * proje, platform ve sistem sürümü;
  * `created_by`, `created_at`, `status`, `revision`.

  Çizge adı `model:<instance_id>`'dir.
* **Değiştirilemezlik:** SMM'nin cephesi yazma işlemlerini yalnızca `working` örnekleri için sunar. Doğrulama ve analiz salt okunur bir tutamaç alır (ADR-0007).
* **Düzenlemeler (DVE.17):** her düzenleme bir komuttur (düğüm ekle/çıkar, ilişki ekle/çıkar, öznitelik ata). Komut:
  1. şemaya ve yapısal bütünlük kurallarına göre doğrulanır (ADR-0014);
  2. çalışma çizgesine uygulanır;
  3. kullanıcı ve zamanla birlikte örneğin değişiklik günlüğüne eklenir;
  4. `revision` değerini artırır.

  Eşzamanlılık ADR-0033'ü izler.
* **İşlemler örneklere başvurur:** her doğrulama veya analiz işlemi `instance_id` ve `revision`'ı kaydeder (ADR-0024); böylece sonuçlar yeniden üretilebilir.
* **Analitik veri:** ADR-0017'ye göre ayrılabilir bir katman olarak bağlanır. Asla bir temel modelin çizgesine yazılmaz.

### Sonuçlar

* İyi, çünkü kuralların katmanlardan haberdar olması gerekmez. Her örnek düz bir çizgedir.
* İyi, çünkü hat değerlendirmeleri işlem başına bir çizgeyle tamamen yalıtılmıştır.
* İyi, çünkü değişiklik günlüğü her çalışma modelinin kesin ve raporlanabilir bir farkını verir.
* Kötü, çünkü depolama, çalışma modeli sayısıyla büyür. Bu, süre dolumu (ADR-0040) ve ADR-0033'ün örnek sınırlarıyla sınırlanır.
* Kötü, çünkü bir çalışma modeli sonraki temel model güncellemelerini izlemez. Yeniden temellendirme, değişiklik günlüğünü yeni bir temel modele yeniden uygulamak demektir ve şimdilik kapsam dışıdır.

### Doğrulama

* Bir test, SMM'nin API'si üzerinden bir `baseline` veya `candidate` örneğine yapılan her yazmanın başarısız olduğunu doğrular.
* Bir test, bir çalışma modelinin değişiklik günlüğünü üst temel modele yeniden uygulamanın çalışma çizgesini yeniden ürettiğini doğrular.
* Bir hat testi, iki aday değerlendirmesini paralel çalıştırır ve hiçbirinin diğerinin düğümlerini görmediğini denetler.

## Seçeneklerin Artıları ve Eksileri

### Örnek başına adlandırılmış çizge

* İyi, çünkü sorgulaması basittir, yalıtım güçlüdür ve doğal bir depo ilkelini kullanır.
* Kötü, çünkü örnek başına depolama gerekir.

### Fark katmanı

* İyi, çünkü depolama en azdır ve temel model güncellemeleri görünür kalır.
* Kötü, çünkü her kural sorgusunun katmanı birleştirmesi gerekir; bu karmaşık ve hataya açıktır. Cypher'ın doğal bir katman anlamı yoktur.

### İşlem başına tam kopya

* İyi, çünkü en yüksek yalıtımı sağlar.
* Kötü, çünkü hiçbir şey değişmediğinde bile kopyalar ve çalışma modeli düzenlemeleri işlemler arasında kaybolur.

## Ek Bilgiler

* İlgili: ADR-0007, ADR-0014, ADR-0015, ADR-0017, ADR-0024, ADR-0033, ADR-0040
