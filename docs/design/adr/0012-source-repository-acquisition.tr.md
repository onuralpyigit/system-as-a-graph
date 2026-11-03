# ADR-0012: Kaynak kod deposundan veri alımı ve zorunlu dosya seti

> Bu doküman [0012-source-repository-acquisition.md](0012-source-repository-acquisition.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, yazılım birimi sorumluları |
| Tür | Onaylama (Ratify) |
| İzlenen | MDG.17–21; SMM.12–13, 20–22; QA-05 |
| Kapatır | CDR-10 |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

MDG.19, "detayları kritik tasarım aşamasında belirlenecek" zorunlu dosyalardan herhangi biri eksik olduğunda "eksik veri" durumu ister (CDR-10). MDG.17, kaynak kodun, kurulum betiklerinin ve yapılandırma dosyalarının aktarılmasını ister.

Mevcut durum (`mdg/src/mdg/adapters/source_code/`, `adapters/source_data/`):

* Yazılım Birimi Sürüm Envanterindeki her yazılım birimi etikete göre klonlanır (ADR-0010).
* `MandatoryFiles` birim başına iki zorunlu dosya tanımlar:
  * birim dizini altında herhangi bir yerde, yorum dışı içeriği yapılandırılmış içerme desenlerinden birini (`mdg.ini`: `include/Makefile_java.mk`) içeren bir `Makefile`;
  * bir topic bildirim dosyası `<birim_adı>.xml`.
* `SourceCodeParser`, topic bildirim dosyasını (yayımlanan ve tüketilen topic'ler) ve Java kaynaklarını (yapılandırılmış bir alan öneki ve bağımlılık sonekleriyle eşleşen içe aktarmalar → `uses` ilişkileri) statik olarak ayrıştırır.
* Topic tanımları ve QoS, hâlâ geliştirme tohum verisinin topic'lerini yer tutucu QoS ile döndüren bir taklit olan `TypeSupportParser`'dan gelir.
* İsteğe bağlı olarak (`[build] run_regenerate_code`, varsayılan kapalı), `GmakeBuildRunner` ayrıştırmadan önce Makefile dizininde, 300 sn zaman aşımıyla yerel bir alt süreç olarak `gmake regenerate_code` çalıştırır.

## Karar Etkenleri

* Zorunlu set mekanik olarak denetlenebilmeli ve birim başına raporlanmalıdır (MDG.19–20).
* Çıkarım deterministik olmalı ve SaaG sunucusundaki bir derleme araç zincirine bağlı olmamalıdır.
* SaaG sunucusunda depo kodu çalıştırmak bir güvenlik riskidir: birçok depodan gelen keyfi koddur.
* Ayrıştırıcı kuralları, kod değişikliği olmadan proje başına yapılandırılabilir olmalıdır.

## Değerlendirilen Seçenekler

* Bildirim dosyası ve kaynakların statik ayrıştırılması, yeniden üretim derlemesi varsayılan kapalı (mevcut)
* Kod üretmek için birimin derlemesini her zaman çalıştırmak, sonra ayrıştırmak
* Statik ayrıştırma, ayrıca etkinleştirildiğinde yeniden üretim derlemesini yalıtılmış, tek kullanımlık bir konteynerde çalıştırmak

## Karar Sonucu

Seçilen seçenek: "Statik ayrıştırma; yeniden üretim derlemesi yalnızca etkinleştirildiğinde ve yalıtılmış bir konteynerde". Bu, mevcut statik çıkarımı ve zorunlu seti onaylar ve `gmake`'in doğrudan ana makinede çalıştırılmasının yarattığı güvenlik açığını kapatır.

* **Zorunlu dosya seti (CDR-10'u kapatır):** yazılım birimi başına aşağıdaki iki dosya alınmalıdır. Eksik olan, birimi `missing_data` olarak işaretler ve bir hata kaydıyla kaydedilir (ADR-0034).

  | Dosya | Kural |
  |---|---|
  | `Makefile` | Birim dizini altında, yorum dışı içeriği `[mandatory_files] makefile_include_patterns` desenlerinden birini içeren herhangi bir `Makefile` |
  | `<birim_adı>.xml` | Birimin yayımladığı ve tükettiği topic'leri bildiren topic bildirim dosyası |

  Sistem deposu ayrıca ADR-0011'in topoloji dosyasını gerektirir. Kurulum betikleri ve yapılandırma dosyaları varsa alınır, MDG.18'e göre kaydedilir ve zorunlu değildir. Zorunlu sete dosya eklemek bu ADR'de bir değişikliktir.
* **Çıkarım:** yalnızca statik ayrıştırma; ayrıştırıcı ayarları `mdg.ini` `[source_parser]` bölümündedir. Ayrıştırıcılar sahteleri olan portlardır (ADR-0003). Taklit `TypeSupportParser`, R3'ün QoS kuralları (DVE.32–35) gerçek veride çalışmadan önce birimlerin topic tip tanımlarını okuyan gerçek bir ayrıştırıcıyla değiştirilmelidir. O zamana kadar yer tutucu QoS değerleri Model Verisinde bu şekilde işaretlenir (ADR-0014).
* **Yeniden üretim derlemesi:** varsayılan olarak kapalı kalır. Etkinleştirildiğinde, yapılandırılmış bir derleme imajından birim başına başlatılan bir konteynerde şu koşullarla çalışır:
  * ağ yok;
  * yalnızca birimin klonunun okuma-yazma bağlanması;
  * CPU, bellek ve süre sınırları.

  Ana makinede `gmake` alt süreci yolu kaldırılır.
* **Dosya başına kayıt (MDG.18):** dosya adı, yol, paket/sürüm, güncelleme zamanı (mevcut gibi), ayrıca klonun commit özeti (ADR-0035).

### Sonuçlar

* İyi, çünkü CDR-10, zaten gerçekleştirilmiş ve test edilmiş kuralla kapatılır.
* İyi, çünkü yeniden üretimi etkinleştirmek artık SaaG ana makinesinde güvenilmeyen kod çalıştıramaz.
* Kötü, çünkü konteynerli derleme, işçiden Docker erişimi ve bakımı yapılan bir derleme imajı gerektirir.
* Kötü, çünkü doğru topic'leri yalnızca kod üretiminden sonra elde eden bir birim, yeniden üretim kapalıyken eksik ayrıştırılır. Bu durum `missing_data` veya ayrıştırıcı uyarıları olarak görünür.

### Doğrulama

* `mdg/tests/adapters/test_mandatory_files.py` ve `test_acquire_source_code.py`, var olan, eksik ve yalnızca yorumda içerme durumlarını kapsar.
* Bir test, derleme çalıştırıcı adaptörünün ana makinede asla `gmake` çağırmadığını doğrular.

## Seçeneklerin Artıları ve Eksileri

### Statik ayrıştırma, yeniden üretim kapalı (mevcut)

* İyi, çünkü deterministik, hızlı ve zaten gerçekleştirilmiştir.
* Kötü, çünkü isteğe bağlı yeniden üretim ana makinede çalışır.

### Her zaman derlemek

* İyi, çünkü üretilen kod her zaman mevcuttur.
* Kötü, çünkü sunucuda tam araç zinciri gerekir, yavaştır ve keyfi kod çalıştırır.

### Statik ayrıştırma + yalıtılmış yeniden üretim

* İyi, çünkü varsayılanları korur ve isteğe bağlı yolu güvenli kılar.
* Kötü, çünkü konteyner tesisatı gerekir.

## Ek Bilgiler

* Kod: `mdg/src/mdg/adapters/source_code/mandatory_files.py`, `gmake_build_runner.py`, `mdg/src/mdg/adapters/source_data/`
* İlgili: ADR-0010, ADR-0011, ADR-0034, ADR-0035
