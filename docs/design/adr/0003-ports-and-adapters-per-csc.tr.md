# ADR-0003: CSC başına Portlar ve Adaptörler

> Bu doküman [0003-ports-and-adapters-per-csc.md](0003-ports-and-adapters-per-csc.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi |
| Tür | Onaylama (Ratify) |
| İzlenen | QA-11; MDG.2–5; DVE.3, 27; SDD §2.3 EXT-IF-01…07; SDP §5 |
| Kapatır | — |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SaaG yedi dış sistemle bütünleşir (SDD §2.3). Geliştirme ve testte bunların çoğu erişilemezdir ya da taklitlerle değiştirilmiştir (`dev/compose.yaml` MySQL ve Gitea çalıştırır; LDAP ve sistem deposu ayrıştırıcısı taklittir). SDP §5 "Portlar ve Adaptörler (Hexagonal); üretimde gerçek adaptörler, geliştirmede DI ile seçilen sahte adaptörler" yaklaşımını belirtir. `mdg/` ve `dve/` bu şekilde geliştirilmiştir. Bu ADR, kalan dört CSC'nin de aynı şekilde izlemesi için örüntüyü ve kurallarını kayda geçirir.

## Karar Etkenleri

* Alan mantığı (doğrulama, model inşası, doğrulama kuralları) dış sistemler olmadan test edilebilmelidir (QA-11).
* Dış sistemler yalnızca kısmen bilinmektedir (CDR-09, CDR-19, CDR-21). Adaptörleri, alan mantığı değişmeden değişecektir.
* Mevcut kod zaten bu örüntüyü izler; ondan sapmak yeniden iş demektir.

## Değerlendirilen Seçenekler

* Bağımlılık enjeksiyonuyla seçilen sahtelerle CSC başına Portlar ve Adaptörler (mevcut)
* Klasik katmanlı mimari (denetleyiciler → servisler → depolar)
* Doğrudan entegrasyon: servisler dış kütüphaneleri doğrudan çağırır

## Karar Sonucu

Seçilen seçenek: "CSC başına Portlar ve Adaptörler", çünkü `mdg/` ve `dve/` içinde zaten gerçekleştirilmiş ve test edilmiştir; ayrıca CDR'nin hâlâ açık bıraktığı tasarım kısımlarını yalıtır.

Her `<csc>/src/<csc>/` paketi için kurallar:

| Dizin | İçerik | İçe aktarabileceği |
|---|---|---|
| `domain/` | Değiştirilemez değer nesneleri ve varlıklar (`@dataclass(frozen=True)`), alan hataları | yalnızca standart kütüphane |
| `ports/` | `I<Ad>` adlı soyut arayüzler (ABC) ve porta özgü istisnalar | `domain` |
| `services/` | Kullanım durumları; her kullanım durumu bir sınıf; yalnızca portlara bağımlı | `domain`, `ports` |
| `adapters/<alan>/` | `<Teknoloji><Port>` adlı gerçekleştirmeler, ör. `GitSourceCodeRepository`, `RedisProductionLog` | `domain`, `ports`, üçüncü taraf kütüphaneler |
| `__init__.py` | CSC'nin genel cephesi: adaptörleri servislere bağlayan fabrika fonksiyonları (ör. `mdg.produce_model_setup_data`) | paketteki her şey |

* Sahteler `<csc>/tests/fakes/` altında `Fake<Port>` adıyla, paylaşılan bir `seed.py` ile yer alır. Aynı portu gerçekleştirirler ve `conftest.py` içinde seçilirler.
* Üretim kodunda bilinmeyen bir dış sistemin yerini tutan taklit adaptör (bugün `LdapDirectoryService` ve `SystemRepoParser` gibi) bunu ilk docstring satırında belirtir (`Mock: …`). Gerçek sisteme ihtiyaç duyan sürümden önce değiştirilmelidir.
* Diğer CSC'ler bir CSC'yi yalnızca cephesi üzerinden kullanır (ADR-0007).

### Sonuçlar

* İyi, çünkü her dış sistem kararı (ADR-0010, 0011, 0020, 0030) yalnızca bir adaptörü değiştirir.
* İyi, çünkü test takımları Docker servisleri olmadan çalışır.
* Kötü, çünkü basit CRUD yollarında ek bir dolaylılık katmanı oluşur.
* Kötü, çünkü sahteler portlarla eşgüdümlü tutulmalıdır. Bugün `dve/tests/fakes/`, `mdg/tests/fakes/`'in bazı kısımlarını yineler.

### Doğrulama

* CI'da paket başına bir `import-linter` sözleşmesi: `domain` paketten hiçbir şey içe aktarmaz; `services`, `adapters`'ı içe aktarmaz.
* ADR-0041, aynı test durumlarını sahte ve gerçek adaptöre karşı çalıştıran adaptör sözleşme testlerini belirler.

## Seçeneklerin Artıları ve Eksileri

### Portlar ve Adaptörler (mevcut)

* İyi, çünkü dış belirsizlik yalıtılır ve tasarım test edilebilir.
* Kötü, çünkü daha fazla dosya ve arayüz gerekir.

### Katmanlı mimari

* İyi, çünkü tanıdık ve basittir.
* Kötü, çünkü depolar genellikle tek bir kalıcılık teknolojisine bağlıdır ve sahte kullanmak için mock çatıları gerekir.

### Doğrudan entegrasyon

* İyi, çünkü en az kodu gerektirir.
* Kötü, çünkü testler gerçek sistemlere ihtiyaç duyar ve her CDR protokol kararı alan mantığına dokunur.

## Ek Bilgiler

* Kod: `mdg/src/mdg/{domain,ports,services,adapters}`, `dve/src/dve/{domain,ports,services,adapters}`
* [SDP §5](../../planning/SDP.tr.md), "Dış entegrasyon mimarisi"
