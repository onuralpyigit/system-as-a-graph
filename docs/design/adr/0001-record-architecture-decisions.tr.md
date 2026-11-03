# ADR-0001: Mimari kararların MADR ile kaydedilmesi

> Bu doküman [0001-record-architecture-decisions.md](0001-record-architecture-decisions.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Accepted |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi |
| Tür | Onaylama (Ratify) |
| İzlenen | BACKLOG S0.2-02 (karar kaydı iş akışı); BACKLOG bulguları L2, L5 |
| Kapatır | — |
| Son karar tarihi | — |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SaaG'nin bir karar kaydı yoktur. SRS ve SDD, 30 tasarım noktasını "kritik tasarım aşamasında belirlenecek" diye ertelemiştir. Bunlar [CDR kaydında](../CDR.md) listelenmiştir, ancak hepsi `Open` durumundadır ve kayıt ne değerlendirilen seçenekleri ne de seçimin gerekçesini içerir. Öte yandan [SDP §5](../../planning/SDP.tr.md), CDR'nin hâlâ açık gösterdiği bir teknoloji yığınını sabitlemiştir ([BACKLOG](../../planning/BACKLOG.md) bulgusu L2). `mdg/` ve `dve/` içindeki kod ise kısmen farklı bir yığınla geliştirilmiştir (FastAPI ve Procrastinate yerine Flask ve Celery + Redis). Projenin, her önemli kararın gerekçelendirildiği, onaylandığı ve çözdüğü isterlere ve CDR maddelerine bağlandığı tek bir yere ihtiyacı vardır.

## Karar Etkenleri

* Bir karar, SRS ister kimliklerine ve kapattığı CDR maddelerine izlenebilir olmalıdır.
* Gerekçeler ve reddedilen seçenekler, ekip değişikliklerinden ve sonraki incelemelerden sonra da korunmalıdır.
* Kararlar, kod ve dokümanlarla aynı pull request akışıyla incelenmelidir.
* Proje dokümanları İngilizce ve Türkçe tutulmaktadır (SRS, SDP).
* Süreç, süresi geçmiş BACKLOG karar şeridi maddelerini hızla kapatabilecek kadar hafif olmalıdır (L5).

## Değerlendirilen Seçenekler

* Depoda MADR kayıtları (`docs/design/adr/`)
* Depoda Nygard tarzı kayıtlar
* CDR kaydını yalnızca bir "karar" sütunuyla genişletmek
* Depo dışında bir wiki

## Karar Sonucu

Seçilen seçenek: "Depoda MADR kayıtları", çünkü MADR'ın *Karar Etkenleri*, *Değerlendirilen Seçenekler* ve *Artılar ve Eksiler* bölümleri, CDR maddelerinin kapatılma biçimiyle örtüşür: alternatifleri isterlere göre karşılaştırmak. Kayıtların depoda tutulması, onların SRS, SDD ve kodla birlikte sürümlenmesini ve incelenmesini sağlar.

Süreç şöyledir:

1. **Konum ve adlandırma.** [template.md](template.md) kullanılarak `docs/design/adr/NNNN-kebab-case-baslik.md`. Numaraları [ADR Yol Haritası](../ADR-ROADMAP.tr.md) ayırır. Bir numara asla yeniden kullanılmaz.
2. **Diller.** Bağlayıcı dil İngilizcedir. Türkçe çeviri `NNNN-kebab-case-baslik.tr.md` ([template.tr.md](template.tr.md) kullanılarak) aynı pull request içinde eklenir veya güncellenir. Her iki dilde de SRS.md'deki kanonik kimlikler `MDG / SCG / FDM / ADM / SMM / DVE` kullanılır (BACKLOG Ek A).
3. **SaaG alanları.** MADR bölümlerine ek olarak her ADR, başlık tablosunda `Tür`, `İzlenen`, `Kapatır` ve `Son karar tarihi` alanlarını belirtir.
4. **Yaşam döngüsü.** `Planned` (yalnızca yol haritasında) → `Proposed` (açık bir pull request'te dosya) → `Accepted` veya `Rejected`. Daha sonra `Deprecated` veya `Superseded by ADR-NNNN` olabilir. Önerilmeden önce vazgeçilen bir yol haritası maddesi `Withdrawn` olur. Kabul edilmiş bir ADR'nin özü değiştirilmez; kararın değişmesi, onun yerine geçen yeni bir ADR demektir.
5. **Onay.** CDR Kurulu, önerilen bir ADR'yi pull request'ini onaylayarak kabul eder veya reddeder.
6. **CDR maddelerinin kapatılması.** Bir ADR'yi kabul eden pull request, `Kapatır` alanındaki her CDR maddesini ADR bağlantısıyla `Resolved` durumuna da getirir. SRS veya SDD'deki "kritik tasarım aşamasında belirlenecek" ifadesini kararla değiştirir ve yol haritasındaki ADR durumunu günceller.
7. **Seçenek olarak SDP §5.** SDP §5'teki teknoloji seçimleri aday seçeneklerdir. Kod bunlardan farklıysa, bir *Uzlaştırma* ADR'si ikisini birlikte değerlendirir; ardından SDP §5 veya kod uyumlu hâle getirilir.

### Sonuçlar

* İyi, çünkü her CDR maddesi bir sahip, bir son tarih (yol haritası dalgası) ve kayıtlı bir gerekçe kazanır.
* İyi, çünkü SDP §5 / CDR çelişkisi (L2) tanımlı bir çözüm yoluna kavuşur.
* İyi, çünkü kararlar etkiledikleri doküman ve kodla birlikte incelenir ve sürümlenir.
* Kötü, çünkü her karar için bir İngilizce ve bir Türkçe dosya gerekir; bu da yazma ve inceleme emeğini ikiye katlar.
* Kötü, çünkü bir ADR'nin kabulü, tek bir pull request içinde birden fazla dokümana (ADR, yol haritası, CDR, SRS veya SDD) dokunmayı gerektirir.

### Doğrulama

* Her sürümün tamamlanma kriterleri bir yol haritası denetimi içerir: o sürümde süresi dolan dalgadaki her ADR `Accepted`, `Rejected` veya `Withdrawn` durumundadır ya da gerekçesiyle yeniden planlanmıştır ([ADR Yol Haritası §7](../ADR-ROADMAP.tr.md#7-yol-haritasının-bakımı)).
* Pull request incelemesi, kabul edilen bir ADR'nin `Kapatır` maddelerinin CDR.md'de `Resolved` olduğunu ve `.tr.md` dosyasının bulunduğunu denetler.

## Seçeneklerin Artıları ve Eksileri

### Depoda MADR kayıtları

* İyi, çünkü yapısı alternatifleri ve etkenleri açıkça ortaya koyar; bu da CDR kapanışına uyar.
* İyi, çünkü düz Markdown'dır, pull request'lerde incelenir ve araç gerektirmeden okunabilir.
* Kötü, çünkü yazması Nygard biçiminden uzundur.

### Depoda Nygard tarzı kayıtlar

* İyi, çünkü kısadır (Bağlam, Karar, Sonuçlar).
* Kötü, çünkü reddedilen seçenekler ve ödünleşimleri çoğu zaman kaybolur; oysa CDR Kurulunun incelemesi gereken tam olarak bunlardır.

### Yalnızca CDR kaydını genişletmek

* İyi, çünkü yeni bir doküman türü gerekmez.
* Kötü, çünkü bir tablo satırı bağlamı, seçenekleri ve sonuçları taşıyamaz. Kayıt, nedenini açıklamadan SDP §5 ile çelişmeye devam eder.

### Depo dışında bir wiki

* İyi, çünkü düzenlemesi kolaydır.
* Kötü, çünkü kod ve dokümanlarla birlikte sürümlenmez ve incelenmez; ister kimliklerine verilen bağlantılar zamanla bozulur.

## Ek Bilgiler

* [ADR Yol Haritası](../ADR-ROADMAP.tr.md): planlanan ADR'lerin kataloğu, karar dalgaları ve kapsama matrisleri.
* [CDR kaydı](../CDR.md): ADR'lerle kapatılan açık maddeler.
* MADR: <https://adr.github.io/madr/>
