# ADR-0011: Ağ topolojisi verisinin alınması

> Bu doküman [0011-network-topology-acquisition.md](0011-network-topology-acquisition.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, sistem/ağ mühendisliği |
| Tür | Karar (Decide) |
| İzlenen | MDG.5–7, 21; SMM.14–15, 18; DVE.40–46 |
| Kapatır | CDR-09, CDR-20 |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

MDG.6, ağ topolojisi verisinin "detayları kritik tasarım aşamasında belirlenecek dış bir veri kaynağından (dosya, veri tabanı vb.)" otomatik olarak alınmasını ister (CDR-09). MDG.7 ayrıca elle girişi ister. CDR-20, EXT-IF-04'ün protokolünü açık bırakır. Topoloji, Sistem Modelinin işlemci/konsol ve ağ düğümlerini (SMM.14–15, 18) ve kaynak kurallarını (DVE.40–46) besler.

Bugün hiçbir topoloji kaynağı gerçekleştirilmemiştir. Uygulama-işlemci birimi ilişkisi (`runs_on`), taklit bir sistem deposu ayrıştırıcısından (`SystemRepoParser`) gelir. Bu ayrıştırıcı, MDG'nin sistem sürümü başına zaten klonladığı sistem deposunu okur.

## Karar Etkenleri

* Topoloji sistem sürümüyle birlikte sürümlenmelidir; böylece N sürümünün modeli her zaman N sürümünün topolojisini kullanır (MDG.9).
* SaaG veri kaynağı olarak yetkili bir ağ yönetim sistemi belirlenmemiştir.
* Elle giriş (MDG.7) ve otomatik alım aynı veriyi üretmelidir; böylece aynı şekilde doğrulanabilirler (MDG.21).
* Kaynak kuralları için kapasite öznitelikleri (çekirdek, RAM, bant genişliği) gereklidir.

## Değerlendirilen Seçenekler

* Sistem deposunda, SaaG tarafından tanımlanmış bir şemada, sistem deposu klonuyla birlikte alınan bir topoloji dosyası
* Konfigürasyon yönetim veri tabanına sorgu
* Bir ağ yönetim sisteminden dışa aktarım
* Yalnızca elle giriş

## Karar Sonucu

Seçilen seçenek: "Sistem deposunda, SaaG tarafından tanımlanmış bir şemada bir topoloji dosyası". Sistem deposu, sistem sürümü başına etikete göre zaten klonlanmaktadır (ADR-0010, ADR-0012); bu yüzden topoloji, barındırdığı yazılımla tam olarak aynı şekilde sürümlenir. Yeni bir dış arayüz veya kimlik bilgisi gerekmez.

* **Biçim:** sistem deposunda yapılandırılmış bir yolda, MDG'nin sahip olduğu bir JSON Şemasına (`mdg/schemas/topology.schema.json`) göre doğrulanan `topology.yaml`. Bölümleri:
  * `processing_units`: ad, tür (`operator_console` | `processor`), çekirdek, RAM, işletim sistemi profili başvurusu;
  * `network_components`: ad, tür, bant genişliği;
  * `links`: birim ↔ ağ bileşeni, bant genişliği;
  * `schema_version`.
* **EXT-IF-04 protokolü (CDR-20'yi kapatır):** EXT-IF-02 ile aynı adaptör ve kimlik bilgileri üzerinden HTTPS ile Git. MDG'nin zaten yaptığı sistem deposu klonundan okunur.
* **Otomatik alım (CDR-09'u kapatır):** MDG dosyayı Model Verisi üretimi sırasında okur. Dosya yoksa çalıştırma topoloji için `missing_data` olarak işaretlenir (MDG.19). Şema doğrulamasından geçemezse bir biçim hatası kaydedilir (ADR-0034).
* **Elle giriş (MDG.7):** arayüz aynı şemayı düzenler ve onu çalıştırmaya bağlı bir topoloji geçersiz kılması olarak kaydeder. Geçersiz kılma, çalıştırmanın köken bilgisinde elle girilmiş olarak kaydedilir (ADR-0035). Asla sistem deposuna geri yazılmaz.
* **İleride başka kaynaklar:** bir CMDB tablosu veya ağ yönetim dışa aktarımı için bir adaptör, bir `ITopologySource` portunun arkasına eklenebilir. Aynı şemayı üretmelidir.

### Sonuçlar

* İyi, çünkü topoloji sistem sürümü başına yeniden üretilebilir ve yeni bir entegrasyon gerektirmez.
* İyi, çünkü tek bir şema otomatik yola, elle girişe ve doğrulamaya hizmet eder.
* Kötü, çünkü sistem mühendisliği `topology.yaml`'ı sistem deposunda sürdürmelidir; bu bir süreç değişikliğidir.
* Kötü, çünkü taklit `SystemRepoParser`, `runs_on`'u da sistem deposundan okuyan gerçek bir ayrıştırıcıyla değiştirilmelidir (ADR-0012).

### Doğrulama

* `dev/gitea` tohum verisindeki `system_repo_1.0.0` örnek bir `topology.yaml` kazanır. MDG testleri geçerli, eksik ve geçersiz durumları kapsar.
* Şema dosyası sürümlüdür ve Model Verisi kullanılan `schema_version`'ı kaydeder (ADR-0013).

## Seçeneklerin Artıları ve Eksileri

### Sistem deposunda topoloji dosyası

* İyi, çünkü sistemle birlikte sürümlenir; yeni arayüz veya kimlik bilgisi gerekmez.
* Kötü, çünkü mühendislerin dosyayı güncel tutmasına bağlıdır.

### CMDB sorgusu

* İyi, çünkü donanım verisini zaten tutuyor olabilir.
* Kötü, çünkü CMDB şeması doğrulanmamıştır ve ağ verisi tuttuğu bilinmemektedir.

### Ağ yönetim dışa aktarımı

* İyi, çünkü canlı ağ için yetkili kaynak olabilir.
* Kötü, çünkü hiçbiri belirlenmemiştir. Belirli bir sistem sürümü için *tasarlanan* ağı değil, *kurulu* ağı tarif eder.

### Yalnızca elle giriş

* İyi, çünkü gerçekleştirmesi önemsizdir.
* Kötü, çünkü MDG.6'yı karşılamaz; hataya açıktır ve yeniden üretilebilir değildir.

## Ek Bilgiler

* Kod: `mdg/src/mdg/adapters/source_data/system_repo_parser.py` (taklit)
* İlgili: ADR-0010, ADR-0012, ADR-0013, ADR-0014, ADR-0034
