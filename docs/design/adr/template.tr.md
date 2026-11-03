# ADR-NNNN: {Problemin ve seçilen çözümün kısa başlığı}

| Alan | Değer |
|---|---|
| Durum | {Proposed \| Accepted \| Rejected \| Deprecated \| Superseded by [ADR-NNNN](NNNN-baslik.tr.md)} |
| Tarih | {Son durum değişikliğinin tarihi, YYYY-AA-GG} |
| Karar vericiler | CDR Kurulu{, karara katılan diğer kişiler} |
| Danışılanlar | {Görüşüne başvurulan kişi veya ekipler} |
| Tür | {Onaylama (Ratify) \| Uzlaştırma (Reconcile) \| Karar (Decide)} (bkz. [ADR Yol Haritası §2](../ADR-ROADMAP.tr.md#2-kurallar)) |
| İzlenen | {SRS ister kimlikleri, ör. SMM.29–31; kalite öznitelikleri, ör. QA-02} |
| Kapatır | {CDR maddeleri, ör. CDR-16, veya —} |
| Son karar tarihi | {[ADR Yol Haritası §5](../ADR-ROADMAP.tr.md#5-karar-takvimi)'teki dalga ve tarih} |
| Yerine geçtiği | {[ADR-NNNN](NNNN-baslik.tr.md) veya —} |

<!-- Bağlayıcı dil İngilizcedir. NNNN-baslik.md dosyasını aynı pull request içinde güncelleyin. Her iki dilde de SRS.md'deki kanonik kimlikleri (MDG, SCG, FDM, ADM, SMM, DVE) kullanın. Durum değerleri İngilizce yazılır. -->

## Bağlam ve Problem Tanımı

{Bağlamı ve problemi iki üç cümleyle ya da bir soru olarak açıklayın. Bu karara ihtiyaç doğuran SRS isterlerine, SDD bölümlerine ve CDR maddelerine atıf yapın.}

## Karar Etkenleri

* {Etken 1, ör. bir ister (DVE.27) veya kalite özniteliği (QA-06)}
* {Etken 2, ör. bir kısıt (şirket içi kurulum, `dve/` içindeki mevcut kod)}
* {…}

## Değerlendirilen Seçenekler

* {Seçenek 1, ör. "mevcut"}
* {Seçenek 2, ör. "SDP §5"}
* {Seçenek 3}

## Karar Sonucu

Seçilen seçenek: "{Seçenek N}", çünkü {gerekçe: hangi etkenleri karşıladığı, hangi eleme kriterini sağladığı veya diğerlerinden neden daha iyi olduğu}.

### Sonuçlar

* İyi, çünkü {olumlu sonuç, ör. artık karşılanabilen bir ister, daha basit kurulum}
* Kötü, çünkü {olumsuz sonuç, ör. taşıma işi, işletilmesi gereken yeni bir bağımlılık}
* {Takip işleri: güncellenecek SDD bölümleri, `Resolved` yapılacak CDR maddeleri, etkilenen backlog hikâyeleri}

### Doğrulama

{Bu karara uyumun nasıl denetlendiği: bir STD test durumu, otomatik test veya CI denetimi, mimari uygunluk fonksiyonu ya da inceleme kontrol listesi maddesi.}

## Seçeneklerin Artıları ve Eksileri

### {Seçenek 1}

{Örnek, açıklama veya ek bilgi bağlantısı}

* İyi, çünkü {argüman}
* Nötr, çünkü {argüman}
* Kötü, çünkü {argüman}

### {Seçenek 2}

{…}

## Ek Bilgiler

{İlgili ADR'lere, CDR maddelerine, SDD bölümlerine, kod yollarına, prototiplere veya ölçümlere bağlantılar. Bu kararın hangi koşulda yeniden ele alınması gerektiğini belirtin.}
