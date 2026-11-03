# ADR-0006: Arka plan işlem yürütme ve durum iletimi

> Bu doküman [0006-background-operation-execution.md](0006-background-operation-execution.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, platform ekibi |
| Tür | Uzlaştırma (Reconcile) |
| İzlenen | DVE.6, 9, 14–15, 24, 27, 78; SMM.30; QA-02, QA-08 |
| Kapatır | — |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

Model Verisi üretimi, model inşası, doğrulama, simülasyon ve kurulum uygunluk değerlendirmesi, bir HTTP isteğinden uzun sürer. Kullanıcılar ve otomasyon istemcileri bu işlemleri başlatabilmeli, ilerlemesini ve sonucunu görebilmeli, iptal edebilmeli ve eşzamanlı çalıştırabilmelidir (DVE.6, 27, 78; SMM.30).

SDP §5, arayüz için SSE ve CLI için REST yoklaması ile Procrastinate'i (PostgreSQL tabanlı bir görev kuyruğu) belirtir. Kod ise farklı geliştirilmiştir:

- `dve/worker.py`, aracı ve sonuç deposu olarak Redis kullanan bir Celery 5.2 işçisi çalıştırır.
- İlerleme, görevin `STARTED` üst verisi (`percent`, `phase`) olarak yayımlanır.
- Günlük satırları çalıştırma başına bir Redis listesine yazılır (`RedisProductionLog`).
- İptal `revoke(terminate=True)` ile yapılır.
- Arayüz `GET /api/mdg/tasks/<id>?after=<satır>` ile yoklama yapar.
- Sonuçlar `result_expires = None` ile tutulur; yani Redis temizlenene kadar Redis'te kalır.

## Karar Etkenleri

* İşlem kayıtları kalıcı ve izlenebilir olmalıdır (DVE.24–25, QA-04); bir önbellek boşaltıldığında kaybolmamalıdır.
* İptal, ilerleme raporlama ve işlem sınıfı başına eşzamanlılık sınırları gereklidir (QA-02, QA-08).
* Hat (kurulum uygunluk değerlendirmesi), etkileşimli simülasyonlar yüzünden kaynaksız kalmamalıdır (DVE.27, 78).
* Şirket içi, tek ekipli bir kurulum için durum tutan servis sayısı ne kadar az olursa o kadar iyidir (QA-10).

## Değerlendirilen Seçenekler

* Celery + Redis (mevcut)
* PostgreSQL üzerinde Procrastinate (SDP §5)
* Yalnızca aracı olarak Redis ile Celery, kalıcı işlem durumu ise ilişkisel depoda

## Karar Sonucu

Seçilen seçenek: "Yalnızca aracı olarak Redis ile Celery, kalıcı işlem durumu ise ilişkisel depoda". Celery zaten bütünleşik ve test edilmiştir; olgun yönlendirme, eşzamanlılık, yeniden deneme ve iptal özelliklerine sahiptir. Mevcut kurulumun zayıflığı, Redis'in sonuçlar ve günlükler için *asıl kayıt sistemi* olarak kullanılmasıdır; bu seçenek o durumu PostgreSQL'e taşır (ADR-0008).

* **Yürütme:** Celery işçileri işlem sınıfı başına adlandırılmış kuyrukları tüketir: `pipeline` (kurulum uygunluk değerlendirmesi, DVE.71–78), `interactive` (Model Verisi üretimi, model inşası, doğrulama) ve `simulation` (davranışsal analiz). Her kuyruğun kendi işçi eşzamanlılığı vardır (ADR-0033).
* **İşlem kayıtları:** API, kuyruğa almadan önce bir işlem kaydı oluşturur (ADR-0024) ve `operation_id`'sini göreve aktarır. Celery görev kimliği tanımlayıcı olarak kullanılmaz, bir öznitelik olarak saklanır. İşçi; durum geçişlerini (`queued → running → succeeded | failed | cancelled`), ilerlemeyi (`percent`, `phase`), kesinti aşamasını ve hatayı (DVE.24) ve günlük satırlarını ilişkisel depoya yazar.
* **Redis:** yalnızca aracı. Sonuç deposu devre dışıdır veya kısa ömürlüdür. Redis'in kaybı kuyruktaki mesajları kaybettirir, ama geçmişi kaybettirmez; kuyruktaki işlemler kayıtlarından yeniden kuyruğa alınır (ADR-0037).
* **Görev yükleri:** yalnızca kimlikler (işlem, veri kaynağı, model örneği kimlikleri) taşır; asla kimlik bilgisi taşımaz (ADR-0032).
* **Durum iletimi:** artımlı imleçli REST yoklaması (`GET /api/v1/operations/{id}?log_after=<n>`, mevcut gibi), hem arayüz hem CLI için sözleşmedir. SSE, aynı kaynak modelinin arkasında, arayüz için ileride bir iyileştirme olarak eklenebilir.

### Sonuçlar

* İyi, çünkü işlem geçmişi Redis yeniden başlatmalarından etkilenmez; bulgular, raporlar ve denetim için sorgulanabilir (ADR-0035).
* İyi, çünkü ayrı kuyruklar CI kapısının kendi kapasitesini korumasını sağlar.
* İyi, çünkü mevcut işçi, ilerleme ve iptal kodu korunur.
* Kötü, çünkü Redis işletilmesi gereken bir servis olarak kalır (ADR-0015 FalkorDB'yi seçerse zaten gerekir).
* Kötü, çünkü işlem durumu iki yere yazılır (Celery ve veri tabanı). Yetkili kaynak veri tabanıdır ve işçi onu güvenilir biçimde güncellemelidir.
* Takip: `RedisProductionLog`'un mevcut `IProductionLog` portu arkasında ilişkisel bir adaptörle değiştirilmesi ve `result_expires`'ın ayarlanması.

### Doğrulama

* Bütünleştirme testi: bir işlem tamamlandıktan sonra Redis boşaltılır; durumu, ilerlemesi ve günlükleri hâlâ alınabilir.
* Bütünleştirme testi: uzun bir `simulation` işlemi, kuyruktaki bir `pipeline` işlemini geciktirmez.

## Seçeneklerin Artıları ve Eksileri

### Celery + Redis (mevcut)

* İyi, çünkü ilerleme ve iptal ile bugün çalışır.
* Kötü, çünkü geçmiş, süre sonu ve kalıcılık garantisi olmadan Redis'te tutulur. İşlem tanımlayıcıları Celery'nin iç ayrıntılarıdır.

### PostgreSQL üzerinde Procrastinate (SDP §5)

* İyi, çünkü işler işlem kaydıyla aynı veri tabanı işleminde (transaction) kuyruğa alınır ve Redis gerekmez.
* Kötü, çünkü daha az olgundur. İlerleme, iptal ve kuyruk yönlendirmesi yeniden gerçekleştirilmeli, mevcut kod yeniden yazılmalıdır.

### Yalnızca aracı olarak Celery + ilişkisel işlem durumu

* İyi, çünkü kanıtlanmış yürütmeyi korur ve kalıcı kayıtlar sağlar.
* Kötü, çünkü tutarlı tutulması gereken iki depo vardır.

## Ek Bilgiler

* Kod: `dve/src/dve/worker.py`, `dve/src/dve/adapters/celery_production_runner.py`, `dve/src/dve/adapters/redis_production_log.py`
* İlgili: ADR-0008, ADR-0024, ADR-0032, ADR-0033, ADR-0037
