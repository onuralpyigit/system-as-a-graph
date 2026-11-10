# ADR-0034: Ortak doğrulama ve hata kaydı örüntüsü

> Bu doküman [0034-validation-and-error-records.md](0034-validation-and-error-records.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi |
| Tür | Onaylama (Ratify) |
| İzlenen | MDG.16, 19–22; SCG.4; SMM.3, 25, 37; FDM.5; ADM.5–6; DVE.8, 14–15, 24; SDD §1 karar 5; QA-05 |
| Kapatır | — |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SDD §1 karar 5, her veri alım yolunun girdisini doğrulamasını ve hataları tutarlı bir öznitelik setiyle kaydetmesini ister. SRS bu ihtiyacı her CSC'de tekrarlar: MDG.16, 19–22; SMM.3, 25, 37; FDM.5; ADM.5–6.

`mdg` içindeki mevcut durum:

* `ErrorRecord`; `status` (`ERROR` | `MISSING_DATA`), `reason`, `source_name`, `source_type`, `project_platform` (birleşik tek bir dizgi) ve `occurred_at` (saat dilimsiz yerel zaman) alanlarını tutar.
* `DataAcquisitionError` bir kayıt taşır. Süreç sınırını geçerken iletisinden yeniden oluşturulur ve kayıt kaybolur.
* Porta özgü istisnalar hata kategorisini sınıf adlarında taşır: `SourceRepoAccessError`, `SourceRepoAuthError`, `SourceRepoIntegrityError` ve `ConfigManagementAccessError`. Kayıt bunu yalnızca serbest metin `reason` içinde tutar.
* Birim başına sonuçlar `UnitStatus` kullanır (`ok`, `missing_data`, `error`, `not_acquired`).

Diğer beş CSC'nin de aynı örüntüye ihtiyacı olacaktır ve DVE bu kayıtları göstermeli ve filtrelemelidir (DVE.8, 24).

## Karar Etkenleri

* SRS hata türlerini ayırır: eksik veri, erişim, yetkilendirme, biçim, bütünlük ve eksik alan (MDG.16, 20; DVE.8). Bunlar metne gömülü değil, filtrelenebilir olmalıdır.
* Tüm CSC'lerde tek bir kayıt tipi; böylece DVE hepsini aynı şekilde gösterir.
* Kayıtlar işçi sınırını aşabilmelidir (ADR-0006).
* Zaman damgaları ana makineler arasında karşılaştırılabilir olmalıdır (QA-04).

## Değerlendirilen Seçenekler

* `mdg` hata kaydını olduğu gibi tutmak ve her CSC'ye kopyalamak
* Bir kategori ve yapısal kapsamla genişletilmiş, `common/` içinde paylaşılan bir hata kaydı tipi
* CSC başına hata modelleri

## Karar Sonucu

Seçilen seçenek: "Bir kategori ve yapısal kapsamla genişletilmiş, `common/` içinde paylaşılan bir hata kaydı tipi". Bu, mevcut örüntüyü (kayıt + fırlatan hata + öğe başına durum) onaylar ve eksiklerini giderir.

* **Tip** (`common/errors.py`, ADR-0004):

  | Alan | Notlar |
  |---|---|
  | `status` | `error` / `missing_data` (mevcut), ayrıca engelleyici olmayan anormallikler için `warning` (ör. eşleşmeyen bir AED kaydı, SMM.37) |
  | `category` | `access`, `authorization`, `integrity`, `format`, `schema`, `missing_field`, `missing_data`, `invalid_relationship`, `internal` |
  | `reason` | İnsan tarafından okunabilir metin |
  | `source_name`, `source_type` | Mevcut gibi |
  | `stage` | İşleme aşaması (ör. `acquire_context`, `clone`, `parse`, `validate`, `construct`, `bind`) (DVE.24) |
  | `project`, `platform`, `system_version` | Birleşik `project_platform` yerine ayrı alanlar |
  | `subject` | İsteğe bağlı: hatanın ilgili olduğu birim adı, dosya yolu, kayıt kimliği veya varlık anahtarı |
  | `operation_id` | Ait olduğu işlem (ADR-0024) |
  | `occurred_at` | Ofsetli UTC, ISO 8601 |

* **Fırlatma:** her port istisnası tek bir `category`'ye eşlenir. Adaptörler port istisnaları fırlatır, servisler bunları kayıtlara dönüştürür. Durması gereken bir servis `DataAcquisitionError(kayıt)` fırlatır. Kayıt, görevin hatasında JSON olarak serileştirilir ve işlemde saklanır (ADR-0024); böylece süreç sınırını aşar.
* **Her alım için doğrulama sırası** (MDG Model Verisi, SMM girdisi, FDM yüklemesi, ADM girdileri):
  1. okunabilirlik ve biçim;
  2. şema;
  3. bütünlük (özetler, başvurular);
  4. zorunlu alan varlığı.

  Bir öğenin tüm hataları, öğe reddedilmeden önce toplanır; böylece kullanıcı her sorunu bir kerede görür.
* **Öğe başına durum:** `UnitStatus` benzeri bir öğe başına sonuç sıralaması (`ok`, `missing_data`, `error`, `not_acquired`) toplu girdiler (birimler, kayıtlar) için korunur. İşlem sonucu bunu özetler.
* **Depolama:** kayıtlar işlemleriyle birlikte PostgreSQL'de kalıcı hâle getirilir. SRS istediğinde, ilgili oldukları çıktıya da gömülürler; örneğin Model Verisinin `errors` bölümü (ADR-0013).

### Sonuçlar

* İyi, çünkü DVE her CSC'nin hatalarını kategori, aşama ve kapsama göre filtreleyebilir (DVE.8, 23–24).
* İyi, çünkü kayıtlar işçiye geçerken artık yapılarını kaybetmez.
* Kötü, çünkü `mdg`'nin `ErrorRecord`'u biçim değiştirir. Model Verisi şeması 1.0 (ADR-0013) yeni alanları benimser; eski dosyalar bir dönüştürücüyle okunur.

### Doğrulama

* `mdg`'deki her adaptör için bir test, her port istisnası için üretilen `category`'yi doğrular.
* Gidiş-dönüş testi: bir Celery görevinde fırlatılan bir kayıt, işlemin `failure` alanından eksiksiz alınır.
* Lint: hiçbir CSC kendi hata kaydı tipini tanımlamaz (bir `import-linter` kuralı kayıtların `common`'dan içe aktarıldığını denetler).

## Seçeneklerin Artıları ve Eksileri

### Olduğu gibi tutmak ve kopyalamak

* İyi, çünkü değişiklik yoktur.
* Kötü, çünkü kopyalar oluşur, kategori yalnızca metin olarak kalır ve kayıt süreçler arasında kaybolur.

### Paylaşılan, genişletilmiş tip

* İyi, çünkü tek bir model vardır, filtrelenebilir ve kalıcıdır.
* Kötü, çünkü `mdg`'nin ve Model Verisi şemasının taşınması gerekir.

### CSC başına modeller

* İyi, çünkü her CSC kendi ihtiyacına göre serbesttir.
* Kötü, çünkü SDD §1 karar 5 ile çelişir ve DVE'nin CSC başına bir gösterici gerekir.

## Ek Bilgiler

* Kod: `mdg/src/mdg/domain/error_record.py`, `mdg/src/mdg/domain/model_setup_data.py` (`UnitStatus`), `mdg/src/mdg/ports/*.py`
* İlgili: ADR-0004, ADR-0006, ADR-0013, ADR-0024, ADR-0035
