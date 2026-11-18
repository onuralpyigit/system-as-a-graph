# ADR-0014: Software-as-a-Graph modeliyle hizalı Sistem Modeli çizge şeması

> Bu doküman [0014-system-model-graph-schema.md](0014-system-model-graph-schema.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-17 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, sistem mühendisliği |
| Tür | Karar (Decide) |
| İzlenen | SMM.1, 4–25; DVE.19, 28–49, 53–58; QA-03, QA-07 |
| Kapatır | CDR-30 (kısmi: Sistem Modeli) |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SMM.4, doğrulanmış Model Verisinin düğüm-ilişki yapısında bir Sistem Modeline dönüştürülmesini ister. SMM.6–17 düğüm tiplerini, SMM.18–23 ilişki tiplerini adlandırır. SMM.24, CPU tahsisini, işletim sistemi ayarlarını ve çalışma zamanı yapılandırmasını sorgulanabilir öznitelikler olarak ister. SMM.5 ve SMM.26 her modeli bir proje, platform, sistem sürümü ve Model Verisi dosyasıyla ilişkilendirir. R3'teki her doğrulama kuralı (DVE.31–49) bu şemaya göre yazılır ve R6'daki yayılım analizleri (DVE.53–58) bu şema üzerinde dolaşır; bu yüzden şema önce sabitlenmelidir.

Software-as-a-Graph (SaaG) araştırma çerçevesi, yayınla-abone ol sistemleri için tipli bir çoklu çizgeyi zaten tanımlar: `d1f8b424` işlemesindeki [`docs/graph-model.md`](https://github.com/onuralpyigit/software-as-a-graph/blob/d1f8b42438e3c500715daefe2a3500b96b1cac49/docs/graph-model.md) (aşağıda **çerçeve modeli**). Bu modelde altı köşe tipi, altı yapısal kenar tipi, yedi kuralla üretilen türetilmiş bir `DEPENDS_ON` kenarı, QoS güdümlü ağırlıklar ve dört katman izdüşümü vardır. Türetilmiş bağımlılık çizgesi, JSS makalesinde değerlendirilen çizgedir (§3.1–3.3).

MDG, çerçeve modelinin terminolojisini zaten üretmektedir. Model Verisinin `graph` bölümünde (ADR-0013) `nodes`, `applications`, `libraries` ve `topics`; `runs_on`, `publishes_to`, `subscribes_to` ve `uses` ilişkileri ve çerçevenin kimlik düzeni (`N0`, `A0`, `L0`, `T0`) bulunur. SRS hiyerarşisi, rol, mesaj veya iletişim servisi düğümleri yoktur. Bunlar yalnızca öznitelik olarak (`system_hierarchy`, `role`) vardır ya da hiç yoktur.

Soru şudur: Sistem Modelinin düğüm etiketleri, ilişki tipleri, kimlik anahtarları ve öznitelikleri nelerdir ve model, çerçeve modelinin türetilmiş bağımlılık görünümüyle nasıl ilişkilidir?

## Karar Etkenleri

* Her SRS düğüm ve ilişki tipi temsil edilebilmeli ve tipe göre sorgulanabilmelidir (SMM.6–24, DVE.19).
* Çerçeve modelinin analizleri, metrikleri, test derlemi ve yayımlanmış sonuçları Sistem Modeline çeviri gerekmeden uygulanabilmelidir.
* Kurallar, varlıkları model örnekleri (çalışma ve aday modeller, ADR-0016) ve sistem sürümleri (sapma, DVE.66–68) arasında kararlı anahtarlarla adresleyebilmelidir.
* Alınmış olgular, türetilmiş değerler ve yer tutucular birbirinden ayırt edilebilir kalmalıdır (QA-03, ADR-0013).
* Yapısal olgular ile türetilmiş analiz ayrı kalmalıdır; biri düzenlendiğinde veya yeniden türetildiğinde diğeri bozulmamalıdır (çerçeve modeli §2.5).
* Şema, tek bir motorun özelliklerine bağlı kalmadan etiketli bir özellik çizgesine eşlenmelidir (ADR-0015).

## Değerlendirilen Seçenekler

* SRS'e özgü tiplerle genişletilmiş, yapısal görünüm ve türetilmiş bağımlılık görünümü olan, çerçeveyle hizalı tipli özellik çizgesi
* SRS adlı tipli özellik çizgesi (`CSU`, `ProcessingUnit`, `PUBLISHES`, `CONSUMES`, …) ve çerçeve modeline bir eşleme tablosu
* Genel çizge: `type` özelliğine sahip tek bir `Entity` etiketi ve `kind` özelliğine sahip tek bir `RELATES` kenarı

## Karar Sonucu

Seçilen seçenek: "SRS'e özgü tiplerle genişletilmiş, yapısal görünüm ve türetilmiş bağımlılık görünümü olan, çerçeveyle hizalı tipli özellik çizgesi". Çünkü hem SRS terminolojisine hem de çerçevenin analizlerine değişiklik gerekmeden hizmet eden tek seçenek budur. MDG bu terminolojiyi zaten üretir ve tipli etiketler kuralları okunabilir ve indekslenebilir tutar. Sürüm kapsamı öğe başına değil, model örneği başına ele alınır (ADR-0016).

### 1. SRS'ten şemaya eşleme

Çekirdek yayınla-abone ol terminolojisini çerçeve modeli sağlar. Çerçevede karşılığı olmayan SRS kavramları **uzantı** etiketleri ve ilişkileri olarak eklenir.

**Tablo 1. SRS düğüm tipleri → etiketler**

| SRS | SRS terimi | Etiket | Kaynak |
|---|---|---|---|
| SMM.6 | Sistem | `System` | uzantı |
| SMM.7 | Yazılım Segmenti | `SoftwareSegment` | uzantı |
| SMM.8 | CSCI | `CSCI` | uzantı |
| SMM.9 | CSC | `CSC` | uzantı |
| SMM.10 | CSU | `Application` (çalıştırılabilir birim) veya `Library` (paylaşılan birim) | çerçeve |
| SMM.11 | Rol | `Role` | uzantı |
| SMM.12 | Topic | `Topic` | çerçeve |
| SMM.13 | Mesaj | `Message` | uzantı |
| SMM.14 | Operatör konsolu ve işlemci birimleri | `kind` = `operator_console` \| `processor` olan `Node` | çerçeve |
| SMM.15 | Ağ bileşenleri | `role` = `switch` \| `router` olan `NetworkDevice` | çerçeve |
| SMM.16 | Ara katman servisleri | `Broker` | çerçeve |
| SMM.17 | İletişim teknolojilerine ait servisler | `CommunicationService` | uzantı |

Çerçeve `Application` ve `Library` tiplerini farklı ağırlıklandırdığı (§4) ve SMM.22 kütüphaneleri açıkça adlandırdığı için CSU bu iki etikete ayrılır. Her ikisi de CSU'nun hiyerarşisini `CONTAINS` üzerinden taşır.

**Tablo 2. SRS ilişki tipleri → ilişki tipleri**

| SRS | SRS terimi | İlişki tipi |
|---|---|---|
| SMM.18 | Operatör konsolu ve işlemci birimleri üzerinde çalışma | `RUNS_ON` |
| SMM.19 | Ara katman ve iletişim servislerini kullanma | `USES_SERVICE` (bildirilmiş) ve türetilmiş `DEPENDS_ON {app_to_broker}` (`ROUTES` üzerinden) |
| SMM.20 | Veri yayınlama | `PUBLISHES_TO` |
| SMM.21 | Veri tüketme | `SUBSCRIBES_TO` |
| SMM.22 | Bir kütüphaneye veya yazılım birimine bağımlı olma | `USES` (bildirilmiş) ve türetilmiş `DEPENDS_ON {app_to_lib, app_to_app}` |
| SMM.23 | Bir yazılım biriminin bir role atanması | `ASSIGNED_TO` |

### 2. Düğüm etiketleri

Her düğümün anahtarı `name`'dir (bkz. §6). Ayrıca `source_id` (varsa Model Verisi `id` değeri), `origin` ve `weight` taşır. Öznitelik adları çerçeve modeli §5.1'i izler.

**Tablo 3. Düğüm etiketleri**

| Etiket | Kaynak | Çekirdek öznitelikler |
|---|---|---|
| `Application` | çerçeve | `version`, `app_type`, `criticality` (`HIGH` \| `MEDIUM` \| `LOW`), `hotstandby`, `is_candidate`, `cm_*` kod metrikleri; `cpu_allocation`, `runtime_config` (SMM.24) |
| `Library` | çerçeve | `version`, `cm_*` kod metrikleri |
| `Topic` | çerçeve | `size` (bayt), `frequency` (Hz), `qos_reliability`, `qos_durability`, `qos_transport_priority`, `qos_deadline_ms`, `qos_history_depth`, `type_definition_hash`; `subscriber_count`, `publisher_count` (türetilmiş) |
| `Broker` | çerçeve | `type`, `version`, `max_connections` |
| `Node` | çerçeve | `kind`, `cpu_cores`, `memory_gb`, `os_type`, `ip_address`; `os_settings` (SMM.24) |
| `NetworkDevice` | çerçeve | `role` |
| `System`, `SoftwareSegment`, `CSCI`, `CSC` | uzantı | `description` |
| `Role` | uzantı | `description` |
| `Message` | uzantı | `size_bytes`, `fields_hash` |
| `CommunicationService` | uzantı | `technology`, `version` |
| `Model` | SaaG | model örneği başına bir tane; bkz. §6 |

### 3. İlişki tipleri

**Yapısal görünüm** (çerçevenin $G_{\text{structural}}$'ı), Model Verisinden inşa edilen ve çalışma modellerinde düzenlenen ilişkileri tutar.

**Tablo 4. Yapısal ilişkiler**

| Tip | Kaynak → Hedef | Kaynak | Öznitelikler |
|---|---|---|---|
| `PUBLISHES_TO` | Application \| Library → Topic | çerçeve | `weight` = w(Topic) |
| `SUBSCRIBES_TO` | Application \| Library → Topic | çerçeve | `weight` = w(Topic) |
| `ROUTES` | Broker → Topic | çerçeve | `weight` = w(Topic) |
| `RUNS_ON` | Application \| Broker → Node | çerçeve | — |
| `USES` | Application \| Library → Library | çerçeve | — |
| `CONNECTS_TO` | Node \| NetworkDevice — Node \| NetworkDevice (yönsüz) | çerçeve | `from_interface`, `to_interface`, `capacity_mbps` |
| `CONTAINS` | System → SoftwareSegment → CSCI → CSC → Application \| Library | uzantı | — |
| `ASSIGNED_TO` | Application → Role | uzantı | — |
| `CARRIES` | Topic → Message | uzantı | — |
| `USES_SERVICE` | Application → Broker \| CommunicationService | uzantı | — |

`CONNECTS_TO` bir kez, kaynağın listelediği yönde saklanır ve yönsüz olarak okunur (çerçeve modeli §5.2). Topolojisi ADR-0011'den gelir.

**Türetilmiş bağımlılık görünümü** (çerçevenin $G_{\text{analysis}}$'i) yalnızca `DEPENDS_ON` tutar. Kenar **bağımlı** olandan **bağımlılığa** doğru, yani veri akışının tersi yönünde işaret eder. Her kenar `dependency_type`, `weight`, `path_count` ve `origin = derived` taşır.

**Tablo 5. Bağımlılık türetme kuralları (çerçeve modeli §6.1)**

| Kural | `dependency_type` | Türetildiği yapı | Kenar ağırlığı |
|---|---|---|---|
| 1 | `app_to_app` | ortak bir Topic'in abonesi → yayıncısı; `USES` zincirleri 3 adıma kadar izlenir | olasılıksal birleşim $1-\prod(1-w(t))$ |
| 2 | `app_to_broker` | Application → yayınladığı veya abone olduğu bir Topic'i `ROUTES` ile yönlendiren Broker | olasılıksal birleşim |
| 3 | `node_to_node` | B'deki bir Application A'dakine bağımlıysa Node B → Node A | en kötü durum yükseltmesi $\max w$ |
| 4 | `node_to_broker` | Node → barındırdığı bir Application'ın kullandığı Broker | en kötü durum yükseltmesi |
| 5 | `app_to_lib` | `USES` | w(Application) ve w(Library) harmonik ortalaması |
| 6 | `broker_to_broker` | aynı Node üzerinde çalışan iki Broker (iki yönde) | ortak Node'ların en yüksek ağırlığı |
| 7 | `node_to_device` | d, B'yi bağımlı olduğu bir Node'dan ayırıyorsa Node B → NetworkDevice d | en kötü durum yükseltmesi |

Kurallar, normatif tanımları olan çerçeve modelindeki hâliyle benimsenir. SaaG bunları yeniden tanımlamaz. Uzantı ilişkileri `DEPENDS_ON` kenarı üretmez.

### 4. Ağırlıklar

Her düğüm ve ilişki, çerçeve modeli §5.3–5.4 ve §6.3'teki gibi hesaplanan, $[0.01, 1.0]$ aralığında bir `weight` taşır:

* **Topic:** $w(t) = 0.75\cdot\text{QoS}(t) + 0.15\cdot\text{SizeNorm}(t) + 0.10\cdot\text{FreqNorm}(t)$, sınırlandırılmış. QoS, AHP ağırlıkları 0.24 (güvenilirlik), 0.62 (kalıcılık) ve 0.14 (iletim önceliği) ile hesaplanır.
* **Application ve Broker:** Topic'lerinin ağırlıklarının kuvvet ortalaması ($p = 3$). Doğrudan Topic'i olmayan bir Application, kullandığı Library'lerin en yüksek ağırlığını alır.
* **Library:** Topic ve tüketici ağırlıklarının en yükseği, $1 + 0.15\cdot\log_2(1 + \text{tüketici sayısı})$ ile ölçeklenmiş.
* **Node:** üzerinde çalışanların en yüksek ağırlığı. **NetworkDevice:** ona bağımlı Node'ların en yüksek ağırlığı (Kural 7).
* **Uzantı etiketleri:** `weight` yoktur. Ağırlıklı analizin parçası değildirler.

Yukarıdaki sabitler `saag-graph-model@d1f8b424` **ağırlıklandırma profilini** oluşturur. `Model` düğümü, inşada kullanılan profili kaydeder. Bir sabitin değişmesi yeni bir şema değil, yeni bir profil oluşturur.

### 5. Katman izdüşümleri

Analizler, çerçeve modeli §7'deki dört izdüşüm üzerinde değiştirilmeden çalışır:

| Katman | Düğümler | `dependency_type` |
|---|---|---|
| `app` | Application, Library | `app_to_app`, `app_to_lib` |
| `infra` | Node, NetworkDevice | `node_to_node`, `node_to_device` |
| `mw` | Application, Broker, Node (yalnızca Broker'lar puanlanır) | `app_to_broker`, `node_to_broker`, `broker_to_broker` |
| `system` | tüm çerçeve etiketleri | yedisi de |

Uzantı etiketleri hiçbir izdüşüme dahil değildir. Doğrulama kuralları onları yine de tam çizge üzerinde sorgulayabilir.

### 6. Kurallar

* **Kimlik:** `(etiket, name)` bir model örneği içinde benzersiz, örnekler ve sürümler arasında kararlıdır. Sapma tespiti, çalışma modeli farkları ve bulgu başvuruları (ADR-0024) bu ikiliye göre eşleşir. Model Verisi `id` değeri (`A0`, `T3`, …) yalnızca `source_id` olarak saklanır; çünkü MDG onu bir koşu içinde adları sıralayarak atar ve koşular arasında değişir.
* **Köken:** her düğüm ve ilişki `origin` taşır: `acquired` (Model Verisinden), `derived` (SMM tarafından hesaplanmış: ağırlıklar, sayımlar ve her `DEPENDS_ON`) veya `edited` (çalışma modeli, ADR-0016).
* **Yer tutucular:** Model Verisinin `placeholders` listesindeki (ADR-0013) bir değer yok olarak, `placeholder_reasons` ile saklanır. Kurallar onu bilinmeyen olarak ele alır. Yok olan bir değerden veya bir çerçeve varsayılanından (örneğin 1 Hz varsayılan frekans) hesaplanan ağırlık yine saklanır ve `weight_basis = partial` taşır. Aksi hâlde `weight_basis = complete` olur.
* **Yapısal öznitelikler:** `cpu_allocation`, `os_settings` ve `runtime_config` (SMM.24), kuralların ayrıştırabilmesi için her biri kendi JSON Şemasına sahip JSON kodlu özelliklerdir.
* **Model üst verisi:** proje, platform, sistem sürümü, Model Verisi dosyası başvurusu ve SHA-256 özeti, oluşturma zamanı, durum ve ağırlıklandırma profili (SMM.5, 26) `Model` düğümünde ve örnek kaydında (ADR-0016) tutulur. Her öğede tekrarlanmaz.
* **İnşa hataları:** uç noktası eksik olan veya uç nokta etiketleri Tablo 4'e uymayan bir ilişki oluşturulmaz. Geçersiz ilişki hatası olarak raporlanır (SMM.25, ADR-0034).

### 7. Yaşam döngüsü

1. SMM, doğrulanmış Model Verisinden yapısal görünümü inşa eder (çerçevenin İçe Aktarma aşaması).
2. SMM ağırlıkları hesaplar ve bağımlılık görünümünü türetir (çerçevenin Ön Analiz aşaması).
3. Çalışma modelleri yalnızca yapısal görünümü düzenler. Bağımlılık görünümü ve ağırlıklar her düzenlemeden sonra yeniden hesaplanır ve hiçbir zaman doğrudan düzenlenmez.
4. Analitik Değerlendirme Verisi her iki görünümün içine değil, yanına bağlanır (ADR-0017).

### Sonuçlar

* İyi, çünkü çerçevenin metrik, tahmin ve benzetim hatları, senaryo derlemi ve yayımlanmış sonuçları SaaG modellerine çeviri gerekmeden uygulanır.
* İyi, çünkü her SRS tipinin bir yeri vardır (Tablo 1–2) ve kurallar doğal okunur: `MATCH (a:Application)-[:PUBLISHES_TO]->(t:Topic)`.
* İyi, çünkü bağımlılık görünümü yayılım analizlerini (DVE.53–58) doğrudan destekler ve ağırlıklar kuralların kritikliğe göre sıralama yapmasını sağlar.
* İyi, çünkü kararlı anahtarlar çalışma modeli farklarını, aday karşılaştırmasını ve sapma tespitini destekler.
* Kötü, çünkü iki terminoloji vardır (SRS terimleri ve çerçeve etiketleri). Tek eşleme Tablo 1–2'dir ve SDD bunları kullanır.
* Kötü, çünkü SaaG bir çerçeve sürümüne bağımlıdır. Sonraki bir çerçeve şema değişikliği yalnızca yeni bir ADR veya yeni bir ağırlıklandırma profiliyle benimsenir.
* Kötü, çünkü Model Verisi hiyerarşi, roller, mesajlar, broker'lar, iletişim servisleri ve topoloji bölümleri kazanmalıdır. O zamana kadar `CONTAINS` ve `ASSIGNED_TO`, MDG'nin bugün ürettiği `system_hierarchy` ve `role` özniteliklerinden inşa edilir; diğer uzantı etiketleri boş kalır.
* Kötü, çünkü türetme büyük modellerde inşa maliyetini artırır. Bütçeler ADR-0036'da belirlenir.
* Takip işi: SDD §2.4 (Sistem Modeli deposu) ve §3.5 bu ADR'ye atıf yapacak şekilde güncellenir; kabulde CDR-30'un Sistem Modeli kısmı `Resolved` yapılır.

### Doğrulama

* Şema kodda tek bir yerde bildirilir (`smm/schema.py`): etiketler, ilişki tipleri, izin verilen uç nokta etiketleri ve öznitelik şemaları. İnşa, orada bildirilmemiş her şeyi reddeder.
* Bir inşa testi, her etiket ve ilişki tipini kapsayan bir Model Verisi fikstürü kullanır.
* Bir eşdeğerlik testi, çerçeve modelinin çalışılmış örneğini (§9) yeniden üretir: $w(T0) = 0.5938$, $w(L0) = 0.7350$, `app_to_lib` ağırlığı 0.6569 ve tam olarak beş türetilmiş kenarı.
* Bir test, her `DEPENDS_ON` kenarının `origin = derived` taşıdığını ve hiçbir uzantı ilişkisinin `DEPENDS_ON` üretmediğini doğrular.

## Seçeneklerin Artıları ve Eksileri

### SRS uzantılı, çerçeveyle hizalı tipli özellik çizgesi (seçilen)

* İyi, çünkü MDG'nin çıktısıyla ve çerçevenin analizleriyle örtüşür ve SRS'i uzantılarla kapsar.
* İyi, çünkü yapısal/türetilmiş ayrımı olguları ve analizi ayrılabilir tutar.
* Nötr, çünkü SRS terimlerinin eşleme tablolarından bulunması gerekir.
* Kötü, çünkü katı bir terminolojisi vardır: yeni bir tip şema değişikliği gerektirir.

### Eşlemeli SRS adlı tipli özellik çizgesi

* İyi, çünkü etiketler SRS ile kelimesi kelimesine örtüşür.
* Kötü, çünkü her çerçeve analizi bir çeviri katmanı, MDG'nin çıktısı da yeniden adlandırma gerektirir.
* Kötü, çünkü tanımlı bir bağımlılık görünümü veya ağırlık yoktur; DVE.53–58 başka bir karar gerektirir.

### Genel tek etiket

* İyi, çünkü yeni tipler şema değişikliği gerektirmez.
* Kötü, çünkü her sorgu bir özellik üzerinden filtreler; bu daha yavaş ve okunması daha zordur. Tip hataları yakalanmaz.

## Ek Bilgiler

* Çerçeve modeli: [`software-as-a-graph/docs/graph-model.md` @ `d1f8b424`](https://github.com/onuralpyigit/software-as-a-graph/blob/d1f8b42438e3c500715daefe2a3500b96b1cac49/docs/graph-model.md), §4 (biçimsel tanım), §5 (ağırlıklar), §6 (türetme kuralları), §7 (katmanlar), §9 (çalışılmış örnek)
* [SRS §5.1.1](../../requirements/SRS.tr.md)
* Kod: `mdg/src/mdg/domain/model_setup_data_graph.py`
* İlgili: ADR-0002, ADR-0011, ADR-0013, ADR-0015, ADR-0016, ADR-0017, ADR-0022, ADR-0024, ADR-0026, ADR-0036
* Çerçeve modeli köşe veya kenar tiplerini değiştirirse ya da bir doğrulama kuralı Tablo 3–4'te olmayan bir tipe ihtiyaç duyarsa yeniden değerlendirilir.
