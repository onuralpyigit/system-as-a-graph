# ADR-0033: Eşzamanlılık denetimi ve işlem sınırları

> Bu doküman [0033-concurrency-control.md](0033-concurrency-control.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, platform ekibi, hat sorumluları |
| Tür | Karar (Decide) |
| İzlenen | SMM.29–31; DVE.17, 27, 78; QA-02, QA-07 |
| Kapatır | CDR-16 |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SMM.29, birden fazla oturumun aynı Sistem Modeli üzerinde, bütünlük veya sonuç tutarlılığı kaybı olmadan eşzamanlı okuma ve yazma yapmasını ister. SMM.30, hat işlemlerinin ve "kritik tasarım aşamasında belirlenecek sayıda kullanıcının" analiz veya simülasyon işlemlerinin eşzamanlı ve birbirinden bağımsız çalışmasını ister (CDR-16). DVE.78, paralel kurulum değerlendirmeleri ister.

ADR-0016 temel modelleri (değiştirilemez), çalışma modellerini (tek sahip) ve aday modelleri (tek işlem) zaten yalıtır. İki soru kalır: tek bir çalışma modeline eşzamanlı yazmalar nasıl ele alınır ve kapasite sınırları nelerdir?

## Karar Etkenleri

* Bir işlemin sonuçları, eşzamanlı bir düzenleme yüzünden değişmemelidir (SMM.29).
* CI hattı değerlendirmeleri, etkileşimli yük altında kapasitelerini korumalıdır (DVE.27, 78).
* Sınırlar açık ve yapılandırılabilir olmalıdır; böylece donanım onlara göre boyutlandırılabilir (ADR-0036).

## Değerlendirilen Seçenekler

* Yazma denetimi: çalışma modeli başına kötümser kilitler / revizyon numaralarıyla iyimser eşzamanlılık / son yazan kazanır
* Kapasite: tek bir paylaşılan işçi havuzu / yapılandırılmış sınırlarla sınıf başına kuyruklar ve işçi havuzları

## Karar Sonucu

Seçilen seçenekler: çalışma modeli yazmaları için **revizyon numaralarıyla iyimser eşzamanlılık** ve işlemler için **yapılandırılmış sınırlarla sınıf başına kuyruklar**.

* **Okumalar anlık görüntü tutarlıdır:**
  * Doğrulama ve analiz işlemleri sabit bir `(instance_id, revision)` ikilisini okur (ADR-0016, ADR-0024).
  * Bir çalışma modeli üzerinde işlem başlamadan önce SMM, modelin mevcut revizyondaki bir kopyasını alır (`GRAPH.COPY`, ADR-0015). İşlem bu kopya üzerinde çalışır.
  * Böylece sonraki düzenlemeler, çalışmakta olan bir işlemin girdisini asla değiştirmez.
* **Yazmalar iyimserdir:**
  * Her çalışma modeli düzenleme komutu `expected_revision` taşır.
  * SMM komutu yalnızca bu değer mevcut revizyonla eşleşirse uygular ve revizyonu artırır. Aksi hâlde mevcut revizyonla birlikte `409 Conflict` döner; arayüz yeniden yükler ve yeniden uygular.
  * Tek bir örneğe yapılan düzenlemeler, yalnızca komut uygulanırken tutulan kısa bir örnek başına kilitle sıraya sokulur.
* **Temel ve aday modeller:** inşadan sonra yazarları yoktur; bu yüzden kilitleme gerektirmezler.
* **Kuyruklar ve sınırlar (CDR-16'yı kapatır):** işlemler, ayrı işçi havuzlarına sahip Celery kuyruklarına gider (ADR-0006). İlk yapılandırılmış değerler aşağıda listelenmiştir. Bu ADR kabul edilmeden önce CDR Kurulu ve hat sorumlularınca doğrulanmalıdır.

  | Sınıf | Kuyruk | Başlangıçtaki eşzamanlı işlem sayısı | Notlar |
  |---|---|---|---|
  | Kurulum değerlendirmesi (hat) | `pipeline` | 4 | Ayrılmış; diğer sınıflarla asla paylaşılmaz |
  | Model Verisi üretimi, model inşası, doğrulama | `interactive` | 4 | |
  | Simülasyon ve saha analizi | `simulation` | 2 | Uzun süren, CPU yoğun |

  | Diğer sınır | Başlangıç değeri |
  |---|---|
  | Eşzamanlı oturum açmış etkileşimli kullanıcı | 20 |
  | Kullanıcı başına çalışma modeli | 5 |
  | Toplam canlı model örneği (tüm türler) | 200 |

  Bir kuyruğun kapasitesini aşan istekler kuyrukta `queued` durumunda bekler. Bir örnek sınırını aşan istekler açık bir hatayla reddedilir.

### Sonuçlar

* İyi, çünkü çalışan işlemler eşzamanlı düzenlemelerden bağımsız olarak yeniden üretilebilir.
* İyi, çünkü hattın kapasitesi güvence altındadır; bu da CI'ın simülasyonların arkasında bekleme riskini ortadan kaldırır.
* İyi, çünkü sınırlar, ADR-0036'nın donanımı boyutlandırabileceği açık sayılardır.
* Kötü, çünkü çalışma modelleri üzerinde işlem başına bir anlık görüntü kopyası alınır (ADR-0015'e göre ucuz, ama bedava değil).
* Kötü, çünkü iki sekme veya kullanıcının aynı çalışma modelinde eşzamanlı düzenlemeleri çakışma alır. Çalışma modellerinin tek sahibi olduğundan (ADR-0016) bu nadir olmalıdır.

### Doğrulama

* Eşzamanlılık testi: bir çalışma modelinde doğrulama çalışırken bir düzenleme işlenir. Doğrulama sonucu, düzenleme öncesi revizyondaki çalıştırmayla eşleşir.
* Çakışma testi: aynı `expected_revision` ile iki düzenleme. Biri başarılı olur, diğeri `409` alır.
* Yük testi (R8): yapılandırılmış sınırlar korunur ve hat gecikmesi, tam etkileşimli ve simülasyon yükü altında ADR-0036 bütçesi içinde kalır.

## Seçeneklerin Artıları ve Eksileri

### Kötümser kilitler

* İyi, çünkü ele alınacak çakışma yoktur.
* Kötü, çünkü uzun tutulan kilitler kullanıcıları engeller ve kaybolan bir istemci kilidi bayat bırakır.

### İyimser revizyonlar

* İyi, çünkü asla engellemez ve çakışmalar açıktır.
* Kötü, çünkü arayüzün `409` yanıtlarını ele alması gerekir.

### Son yazan kazanır

* İyi, çünkü önemsizdir.
* Kötü, çünkü düzenlemeler sessizce kaybolur; bu SMM.29'u ihlal eder.

### Tek paylaşılan havuz ve sınıf başına havuzlar

* Paylaşılan: İyi, çünkü en yüksek kullanımı sağlar. Kötü, çünkü hat kaynaksız kalabilir.
* Sınıf başına: İyi, çünkü kapasite güvence altındadır. Kötü, çünkü bazı kapasiteler boşta kalabilir.

## Ek Bilgiler

* [CDR-16](../CDR.md)
* İlgili: ADR-0006, ADR-0015, ADR-0016, ADR-0024, ADR-0036
