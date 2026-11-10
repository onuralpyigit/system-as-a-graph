# ADR-0015: Çizge depolama teknolojisi

> Bu doküman [0015-graph-storage-technology.md](0015-graph-storage-technology.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, platform ekibi |
| Tür | Karar (Decide) |
| İzlenen | SMM.1, 4, 27–31; DVE.17, 28–58; QA-02, QA-07 |
| Kapatır | CDR-29 (kısmi: Sistem Modeli, Çalışma Modeli) |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

Sistem Modeli (ADR-0014) saklanmalı, doğrulama kurallarınca sorgulanmalı (DVE.28–49), davranışsal analizlerce dolaşılmalı (DVE.53–58) ve birçok kez örneklenmelidir: Model Verisi dosyası başına bir temel model, ayrıca çalışma modelleri ve işlem başına aday modeller (ADR-0016; SMM.29–31). SDP §5 FalkorDB'yi belirtir. Henüz hiçbir şey gerçekleştirilmemiştir.

Beklenen ölçek: UXD §6, görselleştirme ayrıntı düzeyi eşiğini 1.000 düğüm olarak belirler. Geliştirme tohum verisinde birkaç birim vardır. Gerçek bir sistemin yüzlerce ile birkaç bin arası CSU, topic ve mesaja sahip olması beklenir; bu, her adayın kapasitesi içindedir. Belirleyici etkenler bu yüzden ham ölçek değil; örnek yalıtımı, sorgu dili ve işletim maliyetidir.

## Karar Etkenleri

* Birçok yalıtılmış çizge örneğinin ucuza oluşturulması ve silinmesi (QA-02).
* Kurallar için bildirimsel bir sorgu dili (ADR-0022) ve çizge algoritmalarına (döngüler, erişilebilirlik) erişim.
* Mevcut yığınla uyum: Redis zaten işletilmektedir (ADR-0006).
* Şirket içi iç kullanıma izin veren lisanslama.

## Değerlendirilen Seçenekler

* FalkorDB (SDP §5): Cypher destekli özellik çizgesi; Redis modülü olarak, sunucu başına birçok adlandırılmış çizgeyle
* Neo4j Community Edition
* Dosya olarak kalıcı hâle getirilen süreç içi bir NetworkX çizgesi
* Apache AGE eklentili PostgreSQL

## Karar Sonucu

Seçilen seçenek: *Doğrulama* bölümündeki ön çalışmaya bağlı olarak "FalkorDB". Her model örneği adlandırılmış bir çizgedir (bir Redis anahtarı). Örnekler `GRAPH.COPY` ile oluşturulur ve `GRAPH.DELETE` ile silinir; bu, ADR-0016'nın örnek modeline doğrudan uyar. Cypher (openCypher alt kümesi) bildirimsel kurallar için uygundur ve FalkorDB, ekibin zaten işlettiği Redis protokolüyle sunulur.

* **Kurulum:** AOF kalıcılığı olan ayrı bir FalkorDB konteyneri. Celery aracısı Redis'ten ayrıdır, çünkü ikisinin kalıcılık ve tahliye ayarları farklıdır.
* **Erişim:** tek adaptöre SMM sahiptir (`smm/adapters/falkordb_*`) ve bir `IGraphStore` portunun arkasındadır. Diğer CSC'ler SMM'nin cephesini kullanır (ADR-0007). Sorgular parametre kullanır; asla dizgi birleştirmeyle oluşturulmuş Cypher kullanmaz.
* **Algoritmalar:** Cypher ile ifade edilemeyen algoritmalara ihtiyaç duyan kurallar, örneğin alt çizgesini işçi içinde NetworkX'e yükleyebilir (ADR-0022). Bu salt okunurdur ve bellek içi kopya işlemden sonra atılır.
* **Yedek seçenek:** ön çalışma başarısız olursa sıradaki aday PostgreSQL + AGE'dir (adlandırılmış çizgeler, ADR-0008 ile aynı veri tabanı); ardından dosyalarla NetworkX gelir.

### Sonuçlar

* İyi, çünkü örnek başına yalıtım doğal ve ucuzdur; her sorguda kiracı filtresi gerekmez.
* İyi, çünkü bu karar değiştirilirse Cypher kuralları diğer openCypher motorlarına taşınabilir.
* Kötü, çünkü FalkorDB SSPL v1 ile lisanslıdır. Şirket içi iç kullanıma izin verilir, ancak kabulden önce projenin lisans yetkilisiyle netleştirilmelidir.
* Kötü, çünkü Neo4j'den daha genç bir üründür ve Cypher özellik seti daha dardır (ör. sınırlı prosedürler).
* Kötü, çünkü yedeklenmesi gereken bir durum tutan servis daha eklenir (ADR-0040).

### Doğrulama

Bu ADR kabul edilmeden önce R3'teki bir ön çalışma şunları geçmelidir:

1. 5.000 CSU, 5.000 topic ve 50.000 ilişkili sentetik bir modelin 30 saniyeden kısa sürede yüklenmesi.
2. Bu modelin `GRAPH.COPY` ile 5 saniyeden kısa sürede kopyalanması.
3. Yayımcı/tüketici eşleştirme ve döngü tespiti sorgularının 2 saniyeden kısa sürede dönmesi.
4. Lisansın netleştirilmesi.

Sonuçlar bu ADR'nin *Ek Bilgiler* bölümüne kaydedilir.

## Seçeneklerin Artıları ve Eksileri

### FalkorDB

* İyi, çünkü ucuz adlandırılmış çizgeleri ve Cypher'ı vardır, Redis protokolünde çalışır ve hızlıdır.
* Kötü, çünkü SSPL lisansı, ürün olgunluğu ve Cypher alt kümesi sorun oluşturur.

### Neo4j Community

* İyi, çünkü en olgun seçenektir; tam Cypher ve APOC/GDS (Community lisanslı alt kümeleri) sunar.
* Kötü, çünkü Community Edition tek bir kullanıcı veri tabanını destekler. Birçok örneği yalıtmak, her sorguda etiket veya özellik tabanlı kiracılık gerektirir. Ayrıca GPLv3 lisanslıdır ve sunucusu ağırdır.

### Süreç içi NetworkX

* İyi, çünkü saf Python'dur, tüm algoritmalara sahiptir, yeni servis gerektirmez ve kopyalaması önemsizdir.
* Kötü, çünkü sorgu dili yoktur, her işçi bütün modelleri bellekte tutar, kalıcılık yalnızca serileştirmedir ve arayüz sorgularından paylaşılan erişim yoktur.

### PostgreSQL + Apache AGE

* İyi, çünkü PostgreSQL'i yeniden kullanır (ADR-0008); adlandırılmış çizgeleri ve Cypher'ı vardır.
* Kötü, çünkü eklenti daha az olgundur, çizge kopyalama ilkeli yoktur ve dolaşım sorgularında performans daha zayıftır.

## Ek Bilgiler

* [SDP §5](../../planning/SDP.tr.md), [UXD §6](../UXD.md)
* İlgili: ADR-0006, ADR-0014, ADR-0016, ADR-0022, ADR-0033, ADR-0040
