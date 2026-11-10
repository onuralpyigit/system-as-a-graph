# ADR-0010: Dış veri kaynağı adaptörleri ve bağlantı yapılandırması

> Bu doküman [0010-external-data-source-adapters.md](0010-external-data-source-adapters.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, konfigürasyon yönetimi sorumluları |
| Tür | Uzlaştırma (Reconcile) |
| İzlenen | MDG.2–4, 8, 10–13, 17–20; DVE.7; QA-06 |
| Kapatır | CDR-17, CDR-18, CDR-19 |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

MDG, protokolleri CDR'de açık olan üç dış kaynaktan veri okur:

- konfigürasyon yönetim veri tabanı (EXT-IF-01, CDR-17);
- kaynak kod deposu (EXT-IF-02, CDR-18);
- yazılım birimleri paket deposu (EXT-IF-03, CDR-19).

Mevcut durum:

* **CMDB:** `MysqlConfigManagementRepository`, geliştirme taklidinin tablolarına (`platform_pkg_version`, `platform_current_atm_version`, `csu_csms_relation`) karşı elle yazılmış SQL ile PyMySQL kullanır. SDP §5 ise "genel SQL adaptörü (SQLAlchemy)" belirtir.
* **Kaynak deposu:** `GitSourceCodeRepository`, HTTP(S) üzerinden `git` komut satırı aracını çalıştırır. `<base_url>/<org>/<birim>.git` deposunun birim sürümüne eşit etiketini sığ klonlar ve sürümleri `git ls-remote --tags` ile listeler. Kimlik bilgileri URL'ye gömülüdür ve `http.sslVerify=false` her zaman ayarlıdır.
* **Paket deposu:** gerçekleştirilmemiştir. SDP §5 "REST API (Artifactory/Nexus tarzı)" belirtir.
* **Bağlantı yapılandırması:** `DataSourceConfig` (kaynak türü, ad, erişim yöntemi, bağlantı adresi, kullanıcı bilgisi) MDG.8 alanlarını karşılar. Yapılandırmalar yalnızca oturum başına bellekte tutulur ve kaydedilemez; oysa MDG.8 "kaydedilebilir" olmalarını ister.

## Karar Etkenleri

* Üretimdeki CMDB motoru ve şeması doğrulanmamıştır. Yalnızca geliştirme taklidi bilinmektedir.
* Sürüm seçimi yeniden üretilebilir olmalıdır: aynı sürüm her zaman aynı dosyaları vermelidir (MDG.17–18).
* Protokoller, iç sertifika otoriteleri olan şirket içi bir ağda çalışmalıdır.
* MDG.8, kullanıcı tarafından tanımlanabilir ve kaydedilebilir kaynak başına yapılandırma ister.

## Değerlendirilen Seçenekler

* CMDB: sabit SQL ile PyMySQL (mevcut) / lehçesi bağlantı URL'sinden alınan SQLAlchemy Core (SDP §5)
* Kaynak deposu: etikete göre `git` komut satırıyla sığ klon (mevcut) / Git sunucusu REST API'si (arşiv indirme) / bir Python Git kütüphanesi
* Paket deposu: bir depo yöneticisi API'sine karşı HTTP REST istemcisi / dosya sistemi bağlama

## Karar Sonucu

Seçilen seçenekler:

* **EXT-IF-01, CMDB (CDR-17'yi kapatır):** **SQLAlchemy Core** aracılığıyla, üreticinin yerel protokolü üzerinden salt okunur SQL. DBMS lehçesi ve sürücüsü bağlantı URL'sinden gelir (geliştirme taklidi için `mysql+pymysql://…`). Tüm sorgular tek bir adaptörde kalır. Kullanılan tablo ve sütun adları tek bir yerde eşlenir; böylece farklı bir üretim şeması yalnızca eşlemeyi değiştirir. Bu, mevcut portu korur ve motora bağımlılık riskini küçük bir maliyetle giderir.
* **EXT-IF-02, kaynak deposu (CDR-18'i kapatır):** `git` komut satırıyla, birim sürümüne eşit etiketin sığ klonuyla (`--depth 1`) **HTTPS üzerinden Git** (mevcut). Mevcut adaptöre göre değişiklikler:
  * TLS doğrulaması varsayılan olarak açıktır ve isteğe bağlı bir CA paketi ayarı vardır. `http.sslVerify=false` kaldırılır.
  * Kimlik bilgileri URL ile değil, `GIT_ASKPASS` veya bir kimlik bilgisi yardımcısıyla verilir (ADR-0032).
  * Köken bilgisi için her klonun commit özeti kaydedilir (ADR-0035).
* **EXT-IF-03, paket deposu (CDR-19'u kapatır):** bir `IPackageRepository` portunun arkasında, token kimlik doğrulamalı **HTTPS REST**. İlk adaptör gerçekte kullanılan depo yöneticisini hedefler; ürün R5'ten önce sahipleriyle doğrulanır, o zamana kadar bir sahte kullanılır. Port paket üst verisini (ad, sürüm, sağlama toplamı) döner ve çıktıları sürüme göre indirir.
* **Bağlantı yapılandırması (MDG.8):** `DataSourceConfig` alan tipi olarak kalır. Yapılandırmalar kullanıcı başına ilişkisel depoda saklanır (ADR-0008), kimlik bilgileri şifrelenir (ADR-0032). `dve.ini` bölümleri yalnızca varsayılanları sağlar. Her kaynak, bağlandığı anda tek bir ucuz çağrıyla doğrulanır; mevcut gibi (DVE.7).

### Sonuçlar

* İyi, çünkü MySQL olmayan bir üretim CMDB'si yeni bir adaptör değil, yalnızca yeni bir URL ve eşleme gerektirir.
* İyi, çünkü kaynak alımı yeniden üretilebilir kalır (etiket → commit özeti) ve varsayılan olarak güvenli hâle gelir.
* Kötü, çünkü CMDB adaptörünün SQLAlchemy Core üzerine küçük bir yeniden yazımı gerekir.
* Kötü, çünkü paket deposu protokolü, sahipleri ürünü doğrulayana kadar geçici kalır.

### Doğrulama

* Adaptör sözleşme testleri (ADR-0041), `dev/` MySQL ve Gitea yığınına karşı çalışır.
* Bir test, hiçbir kimlik bilgisinin başlatılan süreçlerin komut satırında veya günlük çıktısında görünmediğini doğrular.

## Seçeneklerin Artıları ve Eksileri

### PyMySQL (mevcut) / SQLAlchemy Core ile CMDB

* PyMySQL: İyi, çünkü bugün çalışır. Kötü, çünkü MySQL'e bağlıdır ve üretim CMDB motoru doğrulanmamıştır.
* SQLAlchemy Core: İyi, çünkü lehçeden bağımsızdır ve SQL hâlâ açıktır. Kötü, çünkü bir bağımlılık katmanı ekler.

### `git` komut satırı / REST arşivi / Python kütüphanesi ile kaynak deposu

* `git` komut satırı: İyi, çünkü her Git sunucusuyla çalışır, gerçekleştirilmiştir ve etiketler kesindir. Kötü, çünkü alt süreç ve kimlik bilgisi tesisatı gerekir.
* REST arşivi: İyi, çünkü `git` ikilisi gerekmez. Kötü, çünkü sunucuya özgüdür (Gitea, GitLab ve Bitbucket farklıdır).
* Python kütüphanesi: İyi, çünkü süreç içinde çalışır. Kötü, çünkü sığ klon ve kimlik doğrulama desteği değişkendir.

### REST / dosya sistemi bağlama ile paket deposu

* REST: İyi, çünkü depo yöneticilerinin standart arayüzüdür. Kötü, çünkü ürün henüz doğrulanmamıştır.
* Bağlama: İyi, çünkü basittir. Kötü, çünkü altyapıya bağımlıdır ve sağlama toplamı veya üst veri yoktur.

## Ek Bilgiler

* Kod: `mdg/src/mdg/adapters/config_management/`, `mdg/src/mdg/adapters/source_code/git_source_code_repository.py`, `dve/src/dve/services/data_source_connections.py`
* İlgili: ADR-0003, ADR-0008, ADR-0032, ADR-0035
