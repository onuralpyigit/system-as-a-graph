# ADR-0004: Kurulum birimleri ve depo yerleşimi

> Bu doküman [0004-deployable-units-and-repository-layout.md](0004-deployable-units-and-repository-layout.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, platform ekibi |
| Tür | Uzlaştırma (Reconcile) |
| İzlenen | QA-10, QA-11; SMM.30; DVE.27; BACKLOG T3; SDP §4 |
| Kapatır | — |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SRS, CSCI'ı altı CSC'ye ayrıştırır. SDP §4, `msd/ scg/ frd/ adp/ csm/ vae/` dizinlerinden oluşan bir depo tarif eder. Depoda ise gerçekte `mdg/` (bir kütüphane), `dve/` (`mdg` üzerinde Flask API + Celery işçisi + arayüz) ve `dev/` (taklit veri kaynakları) bulunur. BACKLOG bulgusu T3, CSC → dizin eşlemesinin hiçbir dokümanda sahiplenilmediğini belirtir. SCG, FDM, ADM ve SMM koda kavuşmadan önce projenin iki şeye karar vermesi gerekir. Her CSC ayrı kurulabilir bir servis mi olacak, yoksa CSCI tek bir kurulum birimi mi olacak? Her CSC depoda nerede yer alacak?

## Karar Etkenleri

* Docker Compose ile, orkestrasyon olmadan, tek ekipli şirket içi kurulum (SDP §5).
* CSC'ler büyük çıktılar alışverişi yapar (Model Verisi, Sistem Modeli, Analitik Değerlendirme Verisi) ve katı bir sırayla çalışır (SDD §2.2).
* SRS izlenebilirliği, görünür bire bir bir CSC → kod eşlemesi gerektirir.
* Eşzamanlı işlemler birbirinden yalıtılmalıdır (SMM.30). Bu bir kurulum özelliği değil, çalışma zamanı özelliğidir.

## Değerlendirilen Seçenekler

* Modüler monolit: tek depoda CSC başına bir Python dağıtımı; iki süreç türüyle (API ve işçi) tek bir imaj olarak birlikte kurulur
* CSC başına servis: ağ API'leri olan altı ayrı kurulabilir servis
* Dizin adlarıyla birlikte SDP §4 yerleşimi

## Karar Sonucu

Seçilen seçenek: "Modüler monolit", çünkü CSC'ler tek bir ekibin sahip olduğu ardışık aşamalardır. Ayrı servisler, hiçbir bağımsız ölçekleme veya sahiplik ihtiyacı olmadan ağ sözleşmeleri, kurulum birimleri ve hata türleri ekler.

* **Depo yerleşimi:**

  ```
  mdg/  scg/  fdm/  adm/  smm/  dve/   CSC başına bir Python dağıtımı: <csc>/setup.py, <csc>/src/<csc>/, <csc>/tests/
  web/                                 ADR-0009 ayrı bir ön yüz derlemesi seçerse Operasyon Paneli ön yüzü
  dev/                                 yalnızca geliştirmeye özgü taklit veri kaynakları
  deploy/                              üretim Compose dosyaları ve yapılandırma şablonları (ADR-0039)
  docs/
  ```

  Kesişen tipler (hata kayıtları, ADR-0034; köken bilgisi, ADR-0035) için paylaşılan çekirdek yedinci bir dağıtımda, `common/` içinde yer alır. İş mantığı içermez.
* **Bağımlılık yönü:** `dve` → `smm`, `adm`, `mdg`, `scg`, `fdm`; `adm` → `scg`, `fdm`; `smm` → `mdg` (Model Verisi tipleri), `adm` (AED tipleri). Döngü yoktur.
* **Süreç türleri:** tek bir konteyner imajı `api` (HTTP) veya `worker` (arka plan işlemleri, ADR-0006) olarak çalışır. İşçiler kopya sayısıyla ölçeklenebilir. İşlemler arası yalıtım ayrı servislerden değil, ADR-0016 ve ADR-0033'ten gelir.
* SDP §4 bu yerleşime göre güncellenir.

### Sonuçlar

* İyi, çünkü kurulum tek bir imaj olarak kalırken CSC sınırları görünür ve test edilebilir kalır (paket başına içe aktarma sözleşmeleri).
* İyi, çünkü aktarımlar süreç içi çağrılardır (ADR-0007); aşamalar arasında serileştirme yükü yoktur.
* Kötü, çünkü tüm CSC'ler tek bir sürüm döngüsünü ve tek bir bağımlılık setini paylaşır. Bir CSC'nin ağır bir bağımlılığı her yere kurulur.
* Kötü, çünkü sınırlar ağ yerine araçlar ve incelemeyle korunur.
* Takip: `scg/ fdm/ adm/ smm/ common/` iskeletlerinin oluşturulması ve SDP §4'ün güncellenmesi.

### Doğrulama

* Dağıtımlar arasında bir `import-linter` "katmanlar" sözleşmesi yukarıdaki bağımlılık yönünü zorlar.
* Compose dosyası yalnızca `api`, `worker` ve destek depolarını tanımlar.

## Seçeneklerin Artıları ve Eksileri

### Modüler monolit

* İyi, çünkü kurulumu ve hata ayıklaması basittir ve mevcut `mdg` + `dve` yapısıyla örtüşür.
* Kötü, çünkü yalnızca bütün olarak ölçeklenir (işçinin ölçeklenmesiyle hafifletilir).

### CSC başına servis

* İyi, çünkü katı sınırlar ve bağımsız kurulum sağlar.
* Kötü, çünkü tek bir ekip için altı servis, bunların API'leri ve sürümlemesi gerekir. SRS bunların hiçbirini gerektirmez.

### SDP §4 yerleşimi

* İyi, çünkü zaten yazılıdır.
* Kötü, çünkü adları (`msd`, `frd`, `adp`, `csm`, `vae`) kanonik kimliklerle çelişir (ADR-0002).

## Ek Bilgiler

* [BACKLOG bulgusu T3 ve Ek A](../../planning/BACKLOG.md)
* İlgili: ADR-0003, ADR-0006, ADR-0007, ADR-0039
