# ADR-0022: Doğrulama kural motoru ve kural modeli

> Bu doküman [0022-verification-rule-engine.md](0022-verification-rule-engine.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, sistem mühendisliği |
| Tür | Karar (Decide) |
| İzlenen | DVE.18, 28–49, 72–77; QA-03, QA-11 |
| Kapatır | — |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

R3, yapısal doğrulamayı (DVE.28–49) geliştirir:

- topic QoS uygunluğu;
- yayımcı/tüketici eşleştirme;
- haberleşme tutarlılığı;
- yük dengeleme;
- çekirdek, işletim sistemi ve bellek tahsisi;
- kaynak çekişmesi, döngüler ve yapısal bütünlük;
- mimari kurallar.

DVE.76, her denetim kuralının bir tanımlayıcı, değerlendirme başlığı, önem düzeyi, ağırlık, kabul kriteri ve engelleme durumuna sahip olmasını ister. DVE.18, her sonucun uygun veya uygun değil olarak sınıflandırılmasını ister. Kural *içerikleri* hâlâ açıktır (CDR-01…08; ADR-0023 tarafından yönetilir). *Motor* ise şimdi sabitlenmelidir; böylece CDR maddeleri kapandıkça kurallar yeniden iş gerekmeden eklenebilir.

## Karar Etkenleri

* Aynı kural modeli yapısal doğrulamaya (R3) ve kurulum değerlendirmesine (R7; DVE.72–77) hizmet etmelidir.
* Bazı denetimler örüntü sorgularıdır (eşleşmeyen topic'ler); bazıları algoritma gerektirir (döngüler, kapasite toplamları, çekişme).
* Kural parametreleri (eşikler, izin verilen QoS birleşimleri) kural mantığından daha sık değişir ve sahibi alan mühendisleridir (ADR-0023).
* Kurallar deterministik olmalı ve model üzerinde salt okunur çalışmalıdır (DVE.29, QA-03).
* Her kural küçük fikstür modelleriyle yalıtılmış olarak test edilebilmelidir (QA-11).

## Değerlendirilen Seçenekler

* Yalnızca veri olarak kurallar: her kural bildirimsel bir Cypher sorgusu ve üst veridir
* Yalnızca kod olarak kurallar: her kural, üst verisi koda gömülü bir Python sınıfıdır
* Karma: kural üst verisi ve parametreleri veri olarak; denetim mantığı ise Cypher veya algoritma kullanabilen kayıtlı Python denetim fonksiyonları olarak

## Karar Sonucu

Seçilen seçenek: "Karma". Üst veri ve parametreler, alan mühendislerinin onayladığı kataloğa aittir (ADR-0023). Denetim mantığı Python'un ve çizge algoritmalarının tüm gücüne ihtiyaç duyar, ama küçük, incelenmiş ve test edilmiş kalmalıdır.

**Kural kaydı (veri, katalogdan):**

| Alan | Anlamı |
|---|---|
| `rule_id` | Kararlı tanımlayıcı, ör. `QOS-DUR-001` |
| `version` | Bu kural tanımının anlamsal sürümü |
| `heading` | Değerlendirme başlığı: DVE.72–75 başlıklarından biri veya bir yapısal doğrulama ailesi |
| `check` | Kayıtlı denetim fonksiyonunun adı |
| `params` | Denetime aktarılan parametreler (eşikler, izin verilen değerler) |
| `severity` | `informational` / `low` / `medium` / `high` / `critical` (DVE.21) |
| `weight` | Kurulum puanlamasında kullanılan ağırlık (DVE.76, ADR-0027) |
| `acceptance_criterion` | Neyin uygun olduğunun insan tarafından okunabilir ifadesi |
| `blocking` | İhlalin kurulumu engelleyip engellemediği (DVE.77) |
| `status` | `provisional` / `approved` (ADR-0023) |

**Denetim fonksiyonu (kod):**

```python
@check("topic_has_publisher")
def topic_has_publisher(model: ModelReader, params: Mapping) -> Iterable[Violation]: ...
```

* `ModelReader`, SMM'nin salt okunur tutamacıdır (ADR-0007, ADR-0016). Parametreli Cypher sorguları ve algoritmalar için `to_networkx(alt_çizge)` sunar.
* Bir denetim `Violation` üretir: etkilenen varlık anahtarları, kanıt ve isteğe bağlı bir ileti. Motor bunları kural üst verisini ekleyerek bulgulara dönüştürür (ADR-0024).
* Bir denetim yazma yapmamalı, dış sistemleri çağırmamalı, saati veya rastgeleliği okumamalıdır.

**Motor:**

1. Bir *kural profili* yükler (parametre geçersiz kılmalarıyla bir kural kimlikleri kümesi, ADR-0023).
2. Her kuralın denetimini örnek üzerinde çalıştırır.
3. İhlal başına bir bulgu kaydeder.
4. İşlem sonucunu sınıflandırır.

Denetimi istisna fırlatan bir kural, o kural için bir `error` bulgusu üretir; diğer kurallar çalışmaya devam eder (DVE.24).

**Sınıflandırma (DVE.18):** bir işlem, onaylı bir kuraldan profil eşiğine (varsayılan `high`) eşit veya daha yüksek önemde bir bulgu ya da onaylı bir engelleyici kuraldan bir bulgu varsa `non-conforming`, aksi hâlde `conforming` olur. `provisional` kurallardan gelen bulgular raporlanır, ancak sınıflandırmayı etkilemez. Kurulum puanlaması ADR-0027'ye göre ağırlıkları ekler.

### Sonuçlar

* İyi, çünkü CDR-01…08'in kapanması bir motor değişikliği değil, bir katalog değişikliği (parametreler veya yeni kurallar) olur.
* İyi, çünkü R3 ve R7 tek bir motoru ve tek bir bulgu modelini paylaşır.
* İyi, çünkü her denetim, fikstür çizgeleriyle test edilebilen saf bir fonksiyondur.
* Kötü, çünkü yeni bir denetim *türü* yine kod ve sürüm gerektirir.
* Kötü, çünkü NetworkX'e dönüştüren denetimler, ADR-0036'nın süre bütçelerini karşılamak için alt çizgeleri küçük tutmalıdır.

### Doğrulama

* Kayıtlı her denetimin, ihlal üretmesi gereken bir fikstür modeli ve üretmemesi gereken bir fikstür modeliyle birim testleri vardır (ADR-0041).
* Bir test, onaylı profilin tamamını geliştirme tohum modeline karşı çalıştırır ve sonucu saklanan bir anlık görüntüyle karşılaştırır.

## Seçeneklerin Artıları ve Eksileri

### Yalnızca veri olarak kurallar (Cypher)

* İyi, çünkü kurallar kod olmadan tamamen düzenlenebilir.
* Kötü, çünkü döngü tespiti, kapasite toplama ve çekişme analizi desteklenen Cypher alt kümesinde (ADR-0015) zahmetli veya imkânsızdır; sorgu metni tipsizdir ve test edilmesi zordur.

### Yalnızca kod olarak kurallar

* İyi, çünkü en yüksek ifade gücünü sunar.
* Kötü, çünkü bir eşiği değiştirmek kod sürümü gerektirir; önem düzeyleri ve ağırlıklar kodda gizli kalır ve CDR Kurulunun incelemesi dışında olur.

### Karma

* İyi, çünkü her parça için doğru sahibi belirler.
* Kötü, çünkü kural başına tutarlı tutulması gereken iki çıktı (kayıt + denetim) vardır. Motor, başlangıçta her kaydın `check` değerinin var olduğunu doğrular.

## Ek Bilgiler

* [SRS §6.1.2, §6.1.4](../../requirements/SRS.tr.md)
* İlgili: ADR-0014, ADR-0016, ADR-0023, ADR-0024, ADR-0027, ADR-0036
