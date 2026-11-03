# ADR-0008: Üst veri, işlem ve bulgular için ilişkisel depo

> Bu doküman [0008-relational-store.md](0008-relational-store.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, platform ekibi |
| Tür | Uzlaştırma (Reconcile) |
| İzlenen | MDG.8, 14–15; DVE.21–26, 78; SMM.26; QA-04, QA-08 |
| Kapatır | CDR-29 (kısmi: Yazılım Birimi Sürüm Envanteri; Bulgular, İşlemler ve Raporlar) |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SDD §2.4'teki birçok depo, kalıcı, sorgulanabilir ve filtrelenebilir olması gereken yapısal kayıtlar tutar:

- Yazılım Birimi Sürüm Envanteri;
- Bulgular, İşlemler ve Raporlar deposu;
- veri kaynağı yapılandırmaları (MDG.8);
- model örneği ve çıktı kayıtları (ADR-0016, ADR-0035).

DVE.23, bulguların birçok alana göre sıralanmasını ve filtrelenmesini gerektirir. SDP §5 PostgreSQL'i belirtir. Kodun kendine ait bir ilişkisel deposu yoktur. Envanter Model Verisi JSON'una gömülüdür; işlem durumu ve günlükler Redis'tedir (ADR-0006). MySQL yalnızca `dev/` içindeki *dış* konfigürasyon yönetim veri tabanı taklidi olarak bulunur.

## Karar Etkenleri

* Kayıtlar kalıcı ve işlemsel (transactional) olmalıdır (QA-04, QA-08).
* Bulgular sabit bir çekirdek ile değişken kanıtlardan oluşur (DVE.21); bu yüzden depo yarı yapısal sütunları işleyebilmelidir.
* Şema sürümlenmeli ve yeniden üretilebilir biçimde taşınmalıdır.
* İşletim emeği: şirket içi bir Compose kurulumunda iyi bilinen tek bir veri tabanı motoru.

## Değerlendirilen Seçenekler

* PostgreSQL (SDP §5)
* MySQL/MariaDB (geliştirme CMDB taklidiyle aynı motor)
* İlişkisel depo yok: kayıtlar Redis'te ve JSON dosyalarında tutulur (mevcut)

## Karar Sonucu

Seçilen seçenek: "PostgreSQL", çünkü JSONB sütunları, bulgu kanıtlarını ve işlem parametrelerini indeksli çekirdek alanlarla yan yana tutar. Ayrıca güçlü işlem anlamlarına sahiptir ve ileride başka ihtiyaçları da (ör. ADR-0021 kapsamında zaman serisi eklentileri) ikinci bir motor gerekmeden barındırabilir.

* **Sürüm:** PostgreSQL 16; kalıcı birimle bir Compose servisi olarak çalışır.
* **Erişim:** depo portlarının arkasında SQLAlchemy 2 (Core, uygun yerlerde ORM) (ADR-0003). Alembic ile göçler; CSC şeması başına bir göç geçmişi.
* **Şemalar:** sahip CSC başına bir PostgreSQL şeması (`mdg`, `fdm`, `dve`, …), ayrıca işlemler, çıktılar ve denetim için `common` (ADR-0024, ADR-0035).
* **Burada tutulan depolar:**
  * Yazılım Birimi Sürüm Envanteri (kendi kendine yeterli olması için Model Verisi dosyasında da tutulur);
  * veri kaynağı yapılandırmaları (kimlik bilgileri şifreli, ADR-0032);
  * işlemler, bulgular ve rapor üst verisi (ADR-0024);
  * model örneği kaydı (ADR-0016);
  * çıktı ve köken bilgisi kaydı (ADR-0035).
* **Burada tutulmayanlar:** Sistem Modeli çizgesi (ADR-0015), Model Verisi dosyaları (ADR-0013) ve toplu telemetri (ADR-0021).
* Geliştirme CMDB taklidi MySQL olarak kalır, çünkü bir dış sistemi taklit eder; SaaG'nin deposu değildir.

### Sonuçlar

* İyi, çünkü bulgu filtreleme (DVE.23), işlem geçmişi ve raporlar kalıcı, indeksli bir yere kavuşur.
* İyi, çünkü tek bir motor her CSC'nin kayıtlarına hizmet eder.
* Kötü, çünkü yedeklenmesi gereken yeni bir durum tutan servis (ADR-0040) ve sürdürülmesi gereken göçler eklenir.
* Kötü, çünkü envanter hem veri tabanında hem Model Verisi dosyasında bulunur. Dosya bir çalıştırmanın dondurulmuş kopyasıdır; veri tabanı kopyası sorgulama içindir.

### Doğrulama

* CI'da bir PostgreSQL servis konteynerine karşı `alembic upgrade head` çalışır ve depo adaptörleri ona karşı test edilir.
* Bulgu listeleme uç noktası, hedef bulgu hacminde ADR-0036'nın gecikme bütçesini karşılar.

## Seçeneklerin Artıları ve Eksileri

### PostgreSQL

* İyi, çünkü JSONB, zengin indeksleme, işlemsel DDL ve geniş bir şirket içi kullanım geçmişi sunar.
* Kötü, çünkü mevcut dosya-ve-Redis kurulumuna göre bir servis daha eklenir.

### MySQL/MariaDB

* İyi, çünkü ekip onu zaten `dev/` içinde çalıştırır.
* Kötü, çünkü JSON desteği daha zayıftır ve JSONB tarzı indeksleme yoktur. Motorun yeniden kullanılması, dış CMDB ile SaaG'nin kendi verisi arasındaki sınırı da bulanıklaştırır.

### Redis ve JSON dosyaları (mevcut)

* İyi, çünkü yeni bir şey gerekmez.
* Kötü, çünkü sorgu, kısıt veya işlem yoktur ve kalıcılık Redis'in kalıcılık ayarlarına bağlıdır.

## Ek Bilgiler

* [SDD §2.4](../SDD.md), [CDR-29](../CDR.md)
* İlgili: ADR-0006, ADR-0016, ADR-0024, ADR-0032, ADR-0035, ADR-0040
