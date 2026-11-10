# ADR-0025: Çizge görselleştirme ve büyük model çizimi

> Bu doküman [0025-graph-visualization.md](0025-graph-visualization.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, UX |
| Tür | Karar (Decide) |
| İzlenen | DVE.17, 19–20, 22, 57; QA-07, QA-12; UXD §4–7 |
| Kapatır | — |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

DVE.19–20, düğüm-ilişki yapısı üzerinde arama, filtreleme, yakınlaştırma, kaydırma, seçim ve öznitelik gösterimi ister. DVE.17, bunun üzerinde bir çalışma modelinin düzenlenmesini ister. UXD §6; 60 fps kaydırma ve yakınlaştırmayı, 1.000 düğümün altında tam ayrıntıyı ve üstünde basitleştirilmiş çizimi belirler. UXD ve SDP §5 React Flow'u belirtir.

Hiçbir şey gerçekleştirilmemiştir: mevcut arayüzde çizge görünümü yoktur. ADR-0009 bir React SPA'sı seçer.

## Karar Etkenleri

* Düzenleme etkileşimleri (DVE.17) görüntüleme kadar önemlidir.
* Modeller 1.000 öğeyi aşabilir; görünüm akıcı kalmalıdır (QA-07).
* Özel düğüm çizimi gereklidir: önem rozetleri, durum renkleri (UXD §2.2) ve klavye erişimi (UXD §7).
* Kütüphane React'e uymalıdır (ADR-0009).

## Değerlendirilen Seçenekler

* Sunucu tarafı kapsamlama ve otomatik yerleşim kütüphanesiyle React Flow
* Cytoscape.js (tuval çizici, yerleşik yerleşimler)
* Sigma.js (çok büyük çizgeler için WebGL çizici)

## Karar Sonucu

Seçilen seçenek: "Sunucu tarafı kapsamlama ve otomatik yerleşim kütüphanesiyle React Flow". Birinci sınıf düzenleme desteği (bağlama, sürükleme, silme, seçim) vardır; düğümleri React bileşenleridir (özel rozetler, odak yönetimi, erişilebilirlik); ve zaten UXD tasarımının temelidir. DOM ile çizilen düğümlerin ölçek sınırı, büyük çizgenin tamamını tarayıcıya asla göndermeyerek ele alınır.

* **Kapsamlama:** API, modellerin tamamını değil, *görünümler* sunar:
  * işlemci birimine veya CSC'ye göre toplanmış, genişletilebilir gruplu bir genel görünüm;
  * seçili bir varlığın çevresindeki N adımlık komşuluk;
  * aramadan gelen filtrelenmiş bir alt küme (DVE.19).

  Sunucu, bir görünümü UXD §6'nın 1.000 öğelik ayrıntı eşiğiyle sınırlar. Daha büyük sonuçlar sayılarla birlikte toplanmış olarak döner.
* **Yerleşim:** ELK (`elkjs`) bir Web Worker'da çalışır; böylece ana iş parçacığı serbest kalır. Çalışma modellerinin düğüm konumları örnekle birlikte saklanır, böylece düzenlemeler yerleşimi karıştırmaz.
* **Düzenleme:** tuval düzenlemeleri SMM'nin çalışma modeli komutlarını çağırır (ADR-0016). İyimser olarak uygulanır ve sunucu yanıtıyla uzlaştırılır (UXD §6).
* **Katmanlar:** bulgular (DVE.22 neden/sonuç zincirleri) ve yayılım yolları (DVE.57), mevcut görünüm üzerinde vurgulanmış kenar ve düğüm stilleri olarak çizilir.
* **Yedek seçenek:** ADR-0036 performans bütçesi ölçümü toplanmış genel görünümlerin yetersiz olduğunu gösterirse, salt okunur bir Sigma.js genel görünümü eklenebilir. Bu yeni bir ADR gerektirir.

### Sonuçlar

* İyi, çünkü düzenleme, özel düğüm arayüzü ve klavye erişimi kütüphaneyle gelir ve UXD geçerli kalır.
* İyi, çünkü sunucu tarafı kapsamlama yükleri ve belleği de küçük tutar.
* Kötü, çünkü genel görünüm toplama ve komşuluk sorguları SMM'de ek sunucu işidir.
* Kötü, çünkü kullanıcı çok büyük bir modelin her düğümünü aynı anda göremez; bunun yerine toplama üzerinden çalışır.

### Doğrulama

* Bir Playwright performans testi, 1.000 öğelik bir görünümü kaydırıp yakınlaştırır ve kare hızını UXD §6'ya göre denetler.
* Bir API testi, hiçbir görünüm yanıtının öğe sınırını aşmadığını doğrular.

## Seçeneklerin Artıları ve Eksileri

### React Flow + kapsamlama

* İyi, çünkü en iyi düzenleme deneyimini ve React'e özgü düğümleri sunar; UXD ile örtüşür.
* Kötü, çünkü DOM düğümleri tek bir görünümün boyutunu sınırlar.

### Cytoscape.js

* İyi, çünkü tuvalde çizer, yaklaşık 10 bin öğeyi kaldırır ve birçok yerleşim ile algoritma sunar.
* Kötü, çünkü düzenleme eklentiler gerektirir, özel düğüm içeriği sınırlıdır ve tuval erişilebilirliği daha zayıftır.

### Sigma.js

* İyi, çünkü WebGL çok büyük çizgeleri kaldırır.
* Kötü, çünkü düzenleme desteği asgari düzeydedir ve etkileşim için en fazla özel işi gerektirir.

## Ek Bilgiler

* [UXD §4–7](../UXD.md)
* İlgili: ADR-0009, ADR-0014, ADR-0016, ADR-0036, ADR-0042
