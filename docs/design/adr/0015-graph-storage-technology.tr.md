# ADR-0015: Software-as-a-Graph depo portunun arkasında çizge depolama teknolojisi

> Bu doküman [0015-graph-storage-technology.md](0015-graph-storage-technology.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-17 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, platform ekibi |
| Tür | Karar (Decide) |
| İzlenen | SMM.1, 4, 27–31; DVE.17, 28–58; QA-02, QA-07, QA-11 |
| Kapatır | CDR-29 (kısmi: Sistem Modeli, Çalışma Modeli) |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

Sistem Modeli (ADR-0014) saklanmalı, doğrulama kurallarınca sorgulanmalı (DVE.28–49), davranışsal analizlerce dolaşılmalı (DVE.53–58) ve birçok kez örneklenmelidir: Model Verisi dosyası başına bir temel model, ayrıca çalışma modelleri ve işlem başına aday modeller (ADR-0016; SMM.29–31). ADR-0016 ve ADR-0033, bir örneğin ucuza kopyalanabilen adlandırılmış bir çizge olduğunu varsayar. SDP §5 FalkorDB'yi belirtir. SaaG'de henüz hiçbir şey gerçekleştirilmemiştir.

ADR-0014, Software-as-a-Graph çerçevesinin şemasını benimser (`d1f8b424` işlemesindeki [`docs/graph-model.md`](https://github.com/onuralpyigit/software-as-a-graph/blob/d1f8b42438e3c500715daefe2a3500b96b1cac49/docs/graph-model.md), **çerçeve modeli**). Çerçevenin bu şema için zaten bir depolama katmanı vardır:

* **Port:** `save_graph`, `derive_dependencies`, `get_graph_data`, `get_layer_data`, `get_statistics`, `export_json` ve `close` işlemlerine sahip `IGraphRepository` (`saag/core/ports/graph_repository.py`).
* **Motorlar:** `Neo4jRepository` (Neo4j 5, düz Cypher, APOC veya GDS yok) ve `MemoryRepository` (saf Python). Üçüncü bir motor olan `SimulationGraph`, aynı bağımlılıkları benzetim için yeniden türetir.
* **Eşdeğerlik:** `tests/test_repository_fidelity_parity.py`, motorlar arasında köşe ağırlıklarını, kenar ağırlıklarını ve yol sayılarını sabitler. `tests/test_simulation_dependency_derivation.py`, türetilmiş kenar kümelerini sabitler.
* **Kapsam:** veri tabanı başına bir çizge. `save_graph(clear=True)` onu değiştirir; dolayısıyla çerçevede model örneği kavramı yoktur.

Beklenen ölçek: UXD §6, görselleştirme ayrıntı düzeyi eşiğini 1.000 düğüm olarak belirler. Gerçek bir sistemin yüzlerce ile birkaç bin arası birim, topic ve mesaja sahip olması beklenir; bu, her adayın kapasitesi içindedir. Belirleyici etkenler bu yüzden ham ölçek değil; örnek yalıtımı, çerçeve modeliyle eşdeğerlik, sorgu dili ve işletim maliyetidir.

Soru şudur: Sistem Modeli örneklerini hangi motor saklar ve sunar, ve bu motor çerçevenin depo portu ve motorlarıyla nasıl ilişkilidir?

## Karar Etkenleri

* Birçok yalıtılmış çizge örneğinin oluşturulması, kopyalanması ve silinmesi ucuz olmalıdır (QA-02, ADR-0016, ADR-0033).
* Ağırlıklar ve türetilmiş `DEPENDS_ON` kenarları çerçeve modelininkilerle aynı olmalıdır; böylece çerçevenin analizleri ve yayımlanmış sonuçları uygulanabilir (ADR-0014).
* Kurallar bildirimsel bir sorgu diline (ADR-0022) ve Python'da çizge algoritmalarına ihtiyaç duyar.
* Geliştirme ve testler, sahte adaptörler üzerinden çizge sunucusu olmadan çalışabilmelidir (QA-11, ADR-0003).
* İşletilen yığınla uyum: Redis zaten çalıştırılmaktadır (ADR-0006).
* Lisanslama, şirket içi iç kullanıma izin vermelidir.

## Değerlendirilen Seçenekler

* Çerçevenin depo portunun arkasında FalkorDB; türetme motoru ve test sahtesi olarak çerçevenin bellek içi motoru
* Çerçevenin `Neo4jRepository` adaptörü üzerinden, olduğu gibi Neo4j
* Dosyalardan yeniden inşa edilen, işlem başına çerçeve `MemoryRepository`; çizge sunucusu yok
* Apache AGE eklentili PostgreSQL

## Karar Sonucu

Seçilen seçenek: *Doğrulama* bölümündeki ön çalışmaya bağlı olarak "Çerçevenin depo portunun arkasında FalkorDB; türetme motoru ve test sahtesi olarak çerçevenin bellek içi motoru". Çünkü ucuz adlandırılmış çizgeleri (ADR-0016 ve ADR-0033'ün varsaydığı gibi) sağlarken çerçevenin sözleşmesini koruyan, ağırlıkları ve bağımlılıkları çerçevenin kendi koduyla hesaplayan tek seçenek budur.

### 1. Port

SMM'nin çizge deposu portu `IGraphStore` (`smm/ports/graph_store.py`), SaaG için genişletilmiş çerçeve `IGraphRepository` portudur:

| İşlem | Kaynak | Amaç |
|---|---|---|
| `save_graph`, `derive_dependencies`, `get_graph_data`, `get_layer_data`, `get_statistics`, `export_json`, `close` | çerçeve, değişmeden | Bir örneği inşa etmek, türetmek ve okumak |
| `create_instance`, `copy_instance`, `delete_instance`, `list_instances` | SaaG | Örnek yaşam döngüsü (ADR-0016) |
| `save_extensions` | SaaG | ADR-0014 uzantı etiketlerini ve ilişkilerini yazmak |
| `apply_edit` | SaaG | Bir çalışma modeli düzenleme komutunu uygulamak (ADR-0016) |
| `query` | SaaG | Salt okunur, parametreli bir Cypher sorgusu çalıştırmak (ADR-0022 `ModelReader`) |

Her adaptör, `Neo4jRepository`'nin bir veri tabanına bağlanmasına benzer biçimde, açıldığında tek bir örneğe bağlanır.

### 2. Motorlar

| Motor | Rol |
|---|---|
| FalkorDB adaptörü (`smm/adapters/falkordb_graph_store.py`) | Üretim deposu. Örnek başına bir adlandırılmış çizge, `model:<instance_id>`. |
| Çerçeve `MemoryRepository` | FalkorDB adaptörü içindeki türetme motoru; geliştirme ve testler için sahte adaptör |

* **Türetme yeniden yazılmaz, hesaplanır.** FalkorDB adaptöründeki `derive_dependencies` üç şey yapar:
  1. örneğin yapısal görünümünü okur;
  2. üzerinde çerçevenin `MemoryRepository` 3., 4. ve 5. aşamalarını çalıştırır (topic ağırlıkları, yedi kural, kenar ağırlığı kesinleştirme);
  3. köşe ağırlıklarını ve `DEPENDS_ON` kenarlarını tek bir işlemde geri yazar.

  Bu yüzden SaaG'de türetme kurallarının üçüncü bir kopyası yoktur. Çerçeve modeliyle eşdeğerlik yapı gereği sağlanır ve çerçevenin eşdeğerlik testleri bunu yine de denetler.
* **Anahtarlar:** SMM, `save_graph`'ı `id` değeri ADR-0014 anahtarı (varlığın `name` değeri) olacak şekilde çağırır. Koşuya özgü Model Verisi kimliği `source_id`'ye gider. FalkorDB, etiket başına benzersiz bir `id` uygular.
* **Çerçeve bağımlılığı:** SaaG, çerçeve paketi `saag`'ı ADR-0014'ün adlandırdığı işlemeye sabitlenmiş bir kütüphane olarak kullanır. SMM yalnızca `saag.core` ve `saag.infrastructure.memory_repo` modüllerini içe aktarır.

### 3. FalkorDB kurulumu ve erişimi

* **Konteyner:** AOF kalıcılığı olan ayrı bir FalkorDB konteyneri. Celery aracısı Redis'ten ayrıdır, çünkü ikisi farklı kalıcılık ve tahliye ayarları gerektirir.
* **Örnekler:** `GRAPH.COPY` ile oluşturulur (çalışma modelleri ve işlem anlık görüntüleri, ADR-0016 ve ADR-0033) veya Model Verisinden inşa edilir (temel ve aday modeller) ve `GRAPH.DELETE` ile silinir.
* **Erişim:** tek adaptöre SMM sahiptir. Diğer CSC'ler SMM'nin cephesini kullanır (ADR-0007). Sorgular parametrelidir; asla dizgi birleştirmeyle oluşturulmaz.
* **Algoritmalar:** Cypher ile ifade edilemeyen bir algoritmaya ihtiyaç duyan kural, örneği veya katman izdüşümlerinden birini (`get_layer_data`) işçi içinde NetworkX'e yükler (ADR-0022). Kopya salt okunurdur ve işlemden sonra atılır.
* **Yedek seçenek:** ön çalışma başarısız olursa sıradaki aday, örnek başına bir Neo4j veri tabanıyla çerçevenin `Neo4jRepository` adaptörüdür; bu Neo4j Enterprise gerektirir. Ardından AGE eklentili PostgreSQL gelir.

### Sonuçlar

* İyi, çünkü örnek başına yalıtım doğal ve ucuzdur; hiçbir sorgu örnek filtresi gerektirmez.
* İyi, çünkü ağırlıklar ve bağımlılıklar çerçevenin kendi koduyla hesaplanır; böylece SaaG sonuçları çerçeveninkilerle karşılaştırılabilir kalır.
* İyi, çünkü geliştirme ve testler, çerçevenin test ettiği aynı motor üzerinde, sunucu olmadan çalışır.
* İyi, çünkü Cypher kuralları, çerçevenin Neo4j motoru dahil, diğer openCypher motorlarına taşınabilir kalır.
* Kötü, çünkü türetme gidiş-dönüşü her örneğin yapısal görünümünü Python belleğinden geçirir. Bu, beklenen ölçekte kabul edilebilirdir ve ön çalışmada ölçülür.
* Kötü, çünkü FalkorDB SSPL v1, çerçeve ise GPL-3.0-or-later ile lisanslıdır. Her ikisinin de şirket içi iç kullanıma izin vermesi beklenir, ancak ikisi de kabulden önce projenin lisans yetkilisiyle netleştirilmelidir.
* Kötü, çünkü FalkorDB, Neo4j'den daha genç bir üründür ve bir openCypher alt kümesine sahiptir.
* Kötü, çünkü yedeklenmesi gereken bir durum tutan servis daha eklenir (ADR-0040).
* Takip işi: SDP §5'teki çizge depolama satırı bu ADR'ye atıf yapacak şekilde güncellenir; kabulde CDR-29'un Sistem Modeli ve Çalışma Modeli kısımları `Resolved` yapılır.

### Doğrulama

Bu ADR kabul edilmeden önce R3'teki bir ön çalışma şunları geçmelidir:

1. **Eşdeğerlik:** çerçevenin eşdeğerlik takımı (`test_repository_fidelity_parity.py`, `test_simulation_dependency_derivation.py`), FalkorDB adaptörü bir motor olarak eklenmiş hâlde, çerçeve modeli §9'daki çalışılmış örnek dahil geçer.
2. **Yükleme:** 5.000 Application, 5.000 Topic ve 50.000 ilişkili sentetik bir model 30 saniyeden kısa sürede inşa edilir ve türetilir.
3. **Kopyalama:** bu modelin `GRAPH.COPY` ile kopyalanması 5 saniyeden kısa sürer.
4. **Sorgular:** yayımcı/tüketici eşleştirme ve döngü tespiti sorguları ile `get_layer_data("app")` 2 saniyeden kısa sürede döner.
5. **Lisanslama:** FalkorDB ve çerçeve paketi netleştirilir.

Sonuçlar bu ADR'nin *Ek Bilgiler* bölümüne kaydedilir. Bundan sonra bir CI işi, SMM'deki veya sabitlenmiş çerçeve sürümündeki her değişiklikte eşdeğerlik takımını FalkorDB adaptörüne karşı çalıştırır.

## Seçeneklerin Artıları ve Eksileri

### Çerçeve portunun arkasında FalkorDB (seçilen)

* İyi, çünkü ucuz adlandırılmış çizgeleri ve Cypher'ı vardır, Redis protokolünde çalışır ve çerçevenin sözleşmesini ve türetme kodunu yeniden kullanır.
* Nötr, çünkü türetme veri tabanında değil, Python'da çalışır.
* Kötü, çünkü SSPL lisansı, ürün olgunluğu ve openCypher alt kümesi sorun oluşturur.

### Çerçevenin `Neo4jRepository` adaptörü üzerinden Neo4j

* İyi, çünkü adaptör mevcuttur, eşdeğerlik testinden geçmiştir ve çerçevenin Cypher'ını değiştirmeden çalıştırır.
* Kötü, çünkü Neo4j Community tek bir kullanıcı veri tabanına sahiptir. Birçok örneği yalıtmak Neo4j Enterprise (lisans maliyeti), örnek başına bir sunucu ya da her sorguda bir örnek filtresi gerektirir; çerçevenin sorgularında böyle bir filtre yoktur.
* Kötü, çünkü çizge kopyalama ilkeli yoktur; ADR-0016 ve ADR-0033 kopyalamak yerine yeniden inşa etmek zorunda kalır.

### İşlem başına çerçeve `MemoryRepository`, sunucu yok

* İyi, çünkü çerçevenin kendi motorudur, yeni servis gerektirmez ve kopyalaması önemsizdir.
* Kötü, çünkü sorgu dili yoktur; ADR-0022'nin Cypher sorguları kaybolur ve her işçi bütün modelleri bellekte tutar.
* Kötü, çünkü örnekler yalnızca bir işlem çalışırken var olur; Operasyon Paneli paylaşılan bir modeli sorgulayamaz (DVE.17, DVE.19).

### PostgreSQL + Apache AGE

* İyi, çünkü PostgreSQL'i yeniden kullanır (ADR-0008); adlandırılmış çizgeleri ve Cypher'ı vardır.
* Kötü, çünkü eklenti daha az olgundur, çizge kopyalama ilkeli yoktur ve dolaşım performansı daha zayıftır.

## Ek Bilgiler

* Çerçeve: [`saag/core/ports/graph_repository.py`](https://github.com/onuralpyigit/software-as-a-graph/blob/d1f8b42438e3c500715daefe2a3500b96b1cac49/saag/core/ports/graph_repository.py), `saag/infrastructure/memory_repo.py`, `saag/infrastructure/neo4j_repo.py` ve çerçeve modeli §6.4 (gerçekleştirme eşdeğerliği)
* [SDP §5](../../planning/SDP.tr.md), [UXD §6](../UXD.md)
* İlgili: ADR-0003, ADR-0006, ADR-0007, ADR-0014, ADR-0016, ADR-0022, ADR-0033, ADR-0036, ADR-0040
* Ön çalışma başarısız olursa, lisans incelemesi FalkorDB'yi veya çerçeve paketini reddederse ya da çerçeveye örnek farkında bir motor eklenirse yeniden değerlendirilir.
