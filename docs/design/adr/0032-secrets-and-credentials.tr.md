# ADR-0032: Gizli bilgiler ve veri kaynağı kimlik bilgilerinin korunması

> Bu doküman [0032-secrets-and-credentials.md](0032-secrets-and-credentials.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, güvenlik, platform ekibi |
| Tür | Uzlaştırma (Reconcile) |
| İzlenen | MDG.8; DVE.3, 7; QA-01, QA-10 |
| Kapatır | — |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SaaG iki tür gizli bilgi tutar:

1. **Uygulama gizli bilgileri:** oturum veya çerez anahtarı, veri tabanı parolaları, LDAP servis hesabı (ADR-0030) ve aşağıdaki şifreleme anahtarı.
2. **Veri kaynağı kimlik bilgileri:** CMDB, kaynak deposu ve paket deposu kullanıcı bilgileri. MDG.8 bunların kullanıcı tarafından tanımlanabilir ve *kaydedilebilir* olmasını ister.

Mevcut durum:

* Flask gizli anahtarı, bir geliştirme varsayılanıyla `dve.ini` içindedir.
* Veri kaynağı kimlik bilgileri, API sürecinin belleğinde oturum başına tutulur (`DataSourceConnections`). Yeniden başlatmada kaybolur ve kaydedilemez; bu MDG.8 ile çelişir. İkinci bir API süreci bunları göremez.
* Veri kaynağı kimlik bilgileri, Celery görev yükü içinde işçiye gönderilir (`DataSourceConfig.user_info = "kullanıcı:parola"`). Redis'ten düz metin olarak geçer.
* Git adaptörü parolayı süreç listesinde görünen klon URL'sine gömer ve TLS doğrulamasını devre dışı bırakır (`http.sslVerify=false`).
* SDP §5 ortam değişkenlerini (`.env`) belirtir.

## Karar Etkenleri

* MDG.8: kullanıcı bilgisi dahil yapılandırmalar kaydedilebilir olmalıdır.
* Hiçbir kimlik bilgisi mesaj aracılarında, günlüklerde, süreç argümanlarında veya depoda düz metin olarak görünmemelidir (QA-01).
* Docker Compose ile şirket içi kurulum. Bilinen ortamda mevcut bir gizli bilgi kasası yoktur.
* Rotasyon kod değişikliği olmadan mümkün olmalıdır.

## Değerlendirilen Seçenekler

* Uygulama gizli bilgileri: `.ini` dosyalarında (mevcut) / ortam değişkenlerinde (SDP §5) / konteynerlere bağlanan Docker secrets dosyalarında
* Veri kaynağı kimlik bilgileri: oturum başına bellekte (mevcut) / düz metin kaydedilmiş / ilişkisel depoda şifreli kaydedilmiş / harici bir kasada

## Karar Sonucu

Seçilen seçenekler: **uygulama gizli bilgileri için Docker secrets dosyaları**; geliştirme için yedek olarak ortam değişkenleri. **Veri kaynağı kimlik bilgileri ilişkisel depoda şifreli olarak kaydedilir ve diğer her yerde kimlikle başvurulur.**

* **Uygulama gizli bilgileri:**
  * `/run/secrets/` altındaki dosyalardan (Compose `secrets:`) ya da geliştirmede `SAAG_*` adlı ortam değişkenlerinden okunur.
  * Asla depoya işlenmez. `.ini` dosyaları yalnızca gizli olmayan ayarları tutar (ADR-0039).
  * Başlangıçta API, eksik bir gizli bilgiyle veya bilinen bir geliştirme varsayılanıyla üretim modunda çalışmayı reddeder.
* **Veri kaynağı kimlik bilgileri:**
  * Kaydedilmiş bir veri kaynağı yapılandırması (ADR-0010), PostgreSQL'de bir satırdır. Parola veya token, bir gizli bilgi dosyasından yüklenen veri şifreleme anahtarıyla AES-256-GCM (`cryptography`'nin `AESGCM`'i) kullanılarak şifrelenir.
  * Şifreli metin satırı bir anahtar kimliği saklar; böylece anahtar yeniden şifrelemeyle döndürülebilir.
  * Yapılandırmalar onları oluşturan kullanıcıya aittir. Paylaşılan yapılandırmalar bir yetkilendirme kararıdır (ADR-0031).
* **Kullanım:**
  * API yanıtları asla gizli alanı içermez; alan yalnızca yazılabilir.
  * Görev yükleri yalnızca `data_source_id` taşır (ADR-0006). İşçi şifreyi kullanım anında çözer ve düz değeri çağrı süresince bellekte tutar.
* **Git:** kimlik bilgileri URL ile değil, `GIT_ASKPASS` ile (o tek alt süreç için değerleri işçinin belleğinden veya ortamından okuyan bir yardımcı) verilir. TLS doğrulaması açıktır ve isteğe bağlı bir CA paketi yolu vardır (ADR-0010).
* **Günlükleme:** bir günlük filtresi bilinen gizli alanların değerlerini ve URL kullanıcı bilgisini maskeler. Testler bunu denetler.

### Sonuçlar

* İyi, çünkü MDG.8'in "kaydedilebilir" ifadesi karşılanır; bağlantılar yeniden başlatmalardan ve birden fazla API sürecinden etkilenmez.
* İyi, çünkü Redis, günlükler ve süreç argümanları artık kimlik bilgisi taşımaz.
* Kötü, çünkü anahtar yönetimi gerekir: veri şifreleme anahtarının kaybı, kaydedilmiş kimlik bilgilerini kurtarılamaz kılar (kullanıcıların yeniden girmesi gerekir). Anahtarın yedeklenmesi ADR-0040'a aittir.
* Kötü, çünkü ele geçirilmiş bir işçi ana makinesi kullanımdaki gizli bilgileri yine okuyabilir. Bu kaçınılmazdır; ana makine sıkılaştırmasıyla hafifletilir.

### Doğrulama

* Bir test, bir üretim görevinin Celery mesajında `user_info` veya parola bulunmadığını doğrular.
* Bir test bir klon çalıştırır ve parolanın `git` süreç argümanlarında bulunmadığını doğrular.
* Bir test, bir veri kaynağı yapılandırmasına yapılan `GET` isteğinin asla gizli bilgiyi döndürmediğini doğrular.
* Geliştirme gizli anahtarıyla üretim başlangıcı başarısız olur (test).

## Seçeneklerin Artıları ve Eksileri

### `.ini` / ortam / gizli bilgi dosyalarında uygulama gizli bilgileri

* `.ini`: İyi, çünkü basittir. Kötü, çünkü düz metin olarak depoya işlenir veya kopyalanır ve geliştirme varsayılanı üretime ulaşabilir.
* Ortam: İyi, çünkü 12 faktör standardıdır. Kötü, çünkü `docker inspect` ve alt süreçler tarafından görülebilir.
* Gizli bilgi dosyaları: İyi, çünkü imajda veya ortamda değildir ve Compose bunları doğal olarak destekler. Kötü, çünkü biraz daha fazla kurulum yapılandırması gerekir.

### Bellekte / düz / şifreli / kasada veri kaynağı kimlik bilgileri

* Bellekte: İyi, çünkü hiçbir şey kalıcı hâle getirilmez. Kötü, çünkü MDG.8'i ihlal eder, yeniden başlatmada bozulur ve görev yükü üzerinden sızar.
* Düz: Kötü, çünkü kabul edilemez.
* PostgreSQL'de şifreli: İyi, çünkü kaydedilebilir ve yeni servis gerektirmez. Kötü, çünkü anahtar yönetimi gerekir.
* Kasa: İyi, çünkü en güçlü seçenektir. Kötü, çünkü ortamda mevcut bir kasa yoktur ve yeni bir kritik servis olur.

## Ek Bilgiler

* Kod: `dve/src/dve/services/data_source_connections.py`, `dve/src/dve/worker.py`, `mdg/src/mdg/adapters/source_code/git_source_code_repository.py`, `dve/src/dve/dve.ini`
* İlgili: ADR-0006, ADR-0008, ADR-0010, ADR-0030, ADR-0031, ADR-0039, ADR-0040
