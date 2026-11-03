# ADR-0014: Sistem Modeli çizge şeması

> Bu doküman [0014-system-model-graph-schema.md](0014-system-model-graph-schema.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, sistem mühendisliği |
| Tür | Karar (Decide) |
| İzlenen | SMM.4–25; DVE.19, 28–49; QA-03 |
| Kapatır | CDR-30 (kısmi: Sistem Modeli) |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SMM.6–17 düğüm tiplerini, SMM.18–23 ilişki tiplerini adlandırır. SMM.24, CPU tahsisini, işletim sistemi ayarlarını ve çalışma zamanı yapılandırmasını sorgulanabilir öznitelikler olarak ister. SMM.5, her modelin proje, platform ve sistem sürümüyle ilişkilendirilmesini ister.

Model Verisinin çizge bölümü (ADR-0013) bu terminolojinin yalnızca bir kısmına sahiptir: `nodes` (işlemci birimleri), `applications`, `libraries`, `topics` ve `runs_on`, `publishes_to`, `subscribes_to`, `uses` ilişkileri. R3'teki her doğrulama kuralı (DVE.31–49) şemaya göre yazılır; bu yüzden şema önce sabitlenmelidir.

## Karar Etkenleri

* Her SRS düğüm ve ilişki tipi temsil edilebilmeli ve tipe göre sorgulanabilmelidir (SMM.6–24, DVE.19).
* Kurallar, varlıkları model örnekleri (çalışma ve aday modeller, ADR-0016) ve sürümler (sapma, DVE.66–68) arasında kararlı anahtarlarla adresleyebilmelidir.
* Özniteliklerin kökeni (alınmış, türetilmiş veya yer tutucu) kurallar için görünür olmalıdır (QA-03).
* Şema, tek bir motorun özelliklerine bağlanmadan doğrudan etiketli bir özellik çizgesine (ADR-0015) eşlenmelidir.

## Değerlendirilen Seçenekler

* SRS düğüm tipi başına bir etiket ve SRS ilişkisi başına bir ilişki tipi olan etiketli özellik çizgesi
* Genel çizge: `type` özelliğine sahip tek bir `Entity` etiketi ve `kind` özelliğine sahip tek bir `RELATES` kenarı
* Sürüm damgalı tek çizge: tüm sürümler tek çizgede, her öğede sürüm özellikleri

## Karar Sonucu

Seçilen seçenek: "SRS düğüm tipi başına bir etiket ve SRS ilişkisi başına bir ilişki tipi olan etiketli özellik çizgesi". Tipli etiketler kuralları okunabilir ve indekslenebilir kılar ve SRS'e 1:1 eşlenir. Sürüm kapsamı öğe başına değil, model örneği başına ele alınır (ADR-0016).

**Düğüm etiketleri (SMM.6–17):**

| Etiket | SRS | Anahtar (model örneği içinde benzersiz) | Çekirdek öznitelikler |
|---|---|---|---|
| `System` | SMM.6 | `name` | — |
| `SoftwareSegment` | SMM.7 | `name` | — |
| `CSCI` | SMM.8 | `name` | — |
| `CSC` | SMM.9 | `name` | — |
| `CSU` | SMM.10 | `name` | `version`, `criticality`, `is_candidate`, `cpu_allocation`, `runtime_config` (SMM.24) |
| `Role` | SMM.11 | `name` | — |
| `Topic` | SMM.12 | `name` | `qos_durability`, `qos_reliability`, `qos_lifespan`, `qos_transport_priority`, `type_definition_hash` |
| `Message` | SMM.13 | `name` | `size_bytes`, `fields_hash` |
| `ProcessingUnit` | SMM.14 | `name` | `kind` (`operator_console` / `processor`), `cores`, `ram_mb`, `os_settings` (SMM.24) |
| `NetworkComponent` | SMM.15 | `name` | `kind`, `bandwidth_mbps` |
| `MiddlewareService` | SMM.16 | `name` | `version` |
| `CommunicationService` | SMM.17 | `name` | `technology` |

Model Verisindeki kütüphaneler (`libraries`), `kind = "library"` olan `CSU` düğümleridir. Bu, SMM.22 ile ("bir kütüphaneye veya yazılım birimine bağımlı olma") örtüşür.

**İlişki tipleri (SMM.18–23) ve kapsama ilişkisi:**

| Tip | Kaynak → Hedef | SRS |
|---|---|---|
| `RUNS_ON` | CSU → ProcessingUnit | SMM.18 |
| `USES_SERVICE` | CSU → MiddlewareService / CommunicationService | SMM.19 |
| `PUBLISHES` | CSU → Topic | SMM.20 |
| `CONSUMES` | CSU → Topic | SMM.21 (Model Verisinde `subscribes_to`) |
| `DEPENDS_ON` | CSU → CSU | SMM.22 (Model Verisinde `uses`) |
| `ASSIGNED_TO` | CSU → Role | SMM.23 |
| `CONTAINS` | System → SoftwareSegment → CSCI → CSC → CSU | SMM.6–10'un ima ettiği hiyerarşi |
| `CARRIES` | Topic → Message | SMM.12–13 |
| `CONNECTED_TO` | ProcessingUnit → NetworkComponent | topoloji (ADR-0011) |

**Öznitelik kuralları:**

* Skaler öznitelikler düz özelliklerdir. Yapısal ayarlar (`cpu_allocation`, `os_settings`, `runtime_config`), kuralların ayrıştırabilmesi için öznitelik başına bir şemaya sahip JSON kodlu özelliklerdir.
* Her düğüm ve ilişki `origin` taşır: `acquired` (Model Verisinden), `derived` (SMM tarafından hesaplanmış) veya `edited` (çalışma modeli, ADR-0016). Model Verisinin `placeholders` listesindeki (ADR-0013) bir değer yok olarak, `placeholder_reasons` ile saklanır. Kurallar onu bir değer olarak değil, bilinmeyen olarak ele alır.
* Kimlik: `(etiket, anahtar)` bir model örneği içinde benzersiz, örnekler ve sürümler arasında kararlıdır. Sapma tespiti ve çalışma modeli farkları bu ikiliye göre eşleştirilir.
* Model düzeyindeki üst veri (proje, platform, sistem sürümü, Model Verisi dosyası başvurusu ve özeti, oluşturma zamanı, durum; SMM.5, 26) örnek başına tek bir `Model` düğümünde ve örnek kaydında (ADR-0016) tutulur. Her öğede tekrarlanmaz.

**İnşa hataları:** uç noktası eksik olan bir ilişki oluşturulmaz. Geçersiz ilişki hatası olarak raporlanır (SMM.25, ADR-0034).

### Sonuçlar

* İyi, çünkü kurallar SRS terminolojisiyle yazılır (`MATCH (c:CSU)-[:PUBLISHES]->(t:Topic)`) ve her SRS maddesinin belirgin bir yeri vardır.
* İyi, çünkü kararlı anahtarlar çalışma modeli farklarını, aday karşılaştırmasını ve sapma tespitini destekler.
* Kötü, çünkü yeni bir düğüm tipi eklemek şema değişikliği gerektirir (ve bu ADR'nin yerine yenisi geçer). Bu bilinçli bir tercihtir.
* Kötü, çünkü Model Verisinin çizge bölümü eksik bölümleri (hiyerarşi, roller, mesajlar, servisler, topoloji) kazanmalıdır. Kazanana kadar bu etiketler boş kalır.

### Doğrulama

* Şema kodda tek bir yerde bildirilir (`smm/schema.py`). Model inşası, orada bildirilmemiş etiket ve tipleri reddeder.
* Bir inşa testi, her etiket ve ilişki tipini kapsayan bir Model Verisi fikstürü kullanır.

## Seçeneklerin Artıları ve Eksileri

### Tipli etiketli özellik çizgesi

* İyi, çünkü okunabilir, indekslenebilir ve SRS'e 1:1 eşlenir.
* Kötü, çünkü katı bir terminolojisi vardır.

### Genel tek etiket

* İyi, çünkü yeni tipler şema değişikliği gerektirmez.
* Kötü, çünkü her sorgu bir özellik üzerinden filtreler; bu daha yavaş ve okunması daha zordur. Tip hataları yakalanmaz.

### Sürüm damgalı tek çizge

* İyi, çünkü yönetilecek tek bir çizge vardır.
* Kötü, çünkü her sorgu bir sürüm filtresi gerektirir ve çalışma ile aday modellerin yalıtımı hataya açık hâle gelir.

## Ek Bilgiler

* [SRS §5.1.1](../../requirements/SRS.tr.md)
* Kod: `mdg/src/mdg/domain/model_setup_data_graph.py`
* İlgili: ADR-0011, ADR-0013, ADR-0015, ADR-0016, ADR-0022
