# ADR-0007: CSC'ler arası iç entegrasyon biçimi

> Bu doküman [0007-internal-csc-integration-style.md](0007-internal-csc-integration-style.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi |
| Tür | Karar (Decide) |
| İzlenen | MDG.23; SCG.7; FDM.4; ADM.2–4; SMM.2, 27–28, 33; SDD §2.3 INT-IF-01…05 |
| Kapatır | CDR-24, CDR-25, CDR-26, CDR-27, CDR-28 |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SDD §2.3 beş iç arayüz tanımlar:

| Arayüz | Aktarım |
|---|---|
| INT-IF-01 | MDG → SMM, Model Verisi |
| INT-IF-02 | SCG → ADM, sentetik veri |
| INT-IF-03 | FDM → ADM, saha kayıtları |
| INT-IF-04 | ADM → SMM, Analitik Değerlendirme Verisi |
| INT-IF-05 | SMM → DVE, model erişimi |

CDR-24…28 bunların "haberleşme yöntemi/protokolü"nü açık bırakır. Bugün `dve`, bir Celery görevi içinde `mdg`'yi paket API'si üzerinden çağırır (`mdg.produce_model_setup_data(...)`) ve sonuç diskte bir dosyadır. ADR-0004, CSCI'ı CSC başına bir paketle tek bir kurulum birimi yapar. Aktarım yöntemine SMM geliştirilmeden önce karar verilmelidir.

## Karar Etkenleri

* Birçok SRS isteri, aktarılan verinin *kaydedildiğini* ve *izlenebilir* olduğunu söyler: MDG.23 ("Model Verisi dosyası olarak kaydedecektir"), SCG.5, FDM.3, SMM.26 ve SMM.35. Dolayısıyla bir aktarım, kalıcı ve tanımlanabilir bir çıktı bırakmalıdır.
* Her bileşen aynı kurulum biriminde çalışır (ADR-0004).
* Aktarımlar büyük yükler taşır: bütün modeller ve veri setleri.
* Arayüzler değiştirilebilir ve sahtelerle test edilebilir kalmalıdır (ADR-0003).

## Değerlendirilen Seçenekler

* Kimlikle başvurulan kalıcı çıktılarla, her CSC'nin genel cephesi üzerinden süreç içi çağrılar
* Dosya bırakma: üretici paylaşılan bir dizine yazar, tüketici dizini yoklar
* Mesaj kuyruğu: CSC'ler aracı üzerinden olay yayımlar ve tüketir
* CSC'ler arasında iç HTTP API'leri

## Karar Sonucu

Seçilen seçenek: "Kimlikle başvurulan kalıcı çıktılarla, her CSC'nin genel cephesi üzerinden süreç içi çağrılar", çünkü tüm CSC'ler aynı süreç imajında çalışır. SRS mesajlaşma değil, kaydedilmiş çıktılar ister. Aktarılan şey çıktının kendisidir; çağrı yalnızca onun tanımlayıcısını iletir.

* **Yöntem:** tüketici, üretici CSC'nin cephe fonksiyonlarını (`<csc>/__init__.py`) çağırır, asla iç modüllerini çağırmaz. Uzun süren çağrılar bir işçi görevi içinde çalışır (ADR-0006).
* **Yük:** üretici önce çıktıyı kalıcı hâle getirir ve bir çıktı başvurusu döner (kimlik, tür, konum, içerik özeti; ADR-0035). Tüketici çıktıyı bu başvuruyla yükler.

| Arayüz | Üretici çağrısının döndürdüğü | Çıktı deposu |
|---|---|---|
| INT-IF-01 MDG → SMM | Model Verisi dosyası başvurusu | Dosya sistemi (ADR-0013) |
| INT-IF-02 SCG → ADM | Sentetik veri seti başvurusu | ADR-0019'a göre |
| INT-IF-03 FDM → ADM | Saha kaydı seçimi (kayıt kimlikleri) | ADR-0021'e göre |
| INT-IF-04 ADM → SMM | Analitik Değerlendirme Verisi başvurusu | ADR-0019'a göre |
| INT-IF-05 SMM → DVE | Salt okunur model örneği tutamacı | Çizge deposu (ADR-0015, 0016) |

* **INT-IF-05 erişimi:** DVE, SMM'nin cephesinden bir model erişim nesnesi alır. Nesne yalnızca sorgular sunar ve tek bir model örneğine bağlıdır. Yazmalar, tutamaç üzerinden değil, SMM'nin çalışma modeli API'si üzerinden yapılır (ADR-0016).
* **Hatalar:** cephe fonksiyonları hata kaydı taşıyan alan hataları fırlatır (ADR-0034).

### Sonuçlar

* İyi, çünkü CSCI içinde ağ protokolü, serileştirme katmanı veya sürümlü bir kablo biçimi yoktur.
* İyi, çünkü her aktarım kalıcı ve özeti alınabilir bir çıktıdır; bu da izlenebilirlik isterlerini doğrudan karşılar.
* Kötü, çünkü bir CSC'yi ileride ayrı bir servise bölmek yeni bir arayüz gerektirir; ADR-0004 bunu şimdilik dışarıda bırakır.
* Kötü, çünkü CSC sınırları içe aktarma disiplinine dayanır (CI'da zorlanır, ADR-0003/0004).

### Doğrulama

* `import-linter`: tüketiciler `<csc>.services` veya `<csc>.adapters`'ı değil, yalnızca `<csc>`'yi (cepheyi) içe aktarır.
* Her cephe fonksiyonunun sahte bir üretici çıktısıyla bir sözleşme testi vardır.

## Seçeneklerin Artıları ve Eksileri

### Kalıcı çıktılarla süreç içi cephe çağrıları

* İyi, çünkü en basit seçenektir ve kurulum birimi ile SRS kayıt isterleriyle örtüşür.
* Kötü, çünkü CSC'leri paylaşılan bir çalışma zamanına bağlar.

### Dosya bırakma

* İyi, çünkü gevşek bağlılık sağlar.
* Kötü, çünkü yoklama ve yarım dosya yarışları vardır ve tipli bir sözleşme yoktur.

### Mesaj kuyruğu

* İyi, çünkü asenkron ve ayrıktır.
* Kötü, çünkü büyük yükler aracıda taşınmamalıdır ve aşamalar zaten ADR-0006'nın işlemleriyle sıralanır.

### İç HTTP

* İyi, çünkü ileride servislere bölünmeye hazırdır.
* Kötü, çünkü şu an hiçbir fayda sağlamadan tek bir kurulum biriminin içine ağ kaynaklı hata türleri ekler.

## Ek Bilgiler

* [SDD §2.3](../SDD.md), [CDR §1.4](../CDR.md)
* İlgili: ADR-0003, ADR-0004, ADR-0013, ADR-0016, ADR-0019, ADR-0035
