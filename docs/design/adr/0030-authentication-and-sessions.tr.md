# ADR-0030: Kimlik doğrulama ve oturum yönetimi

> Bu doküman [0030-authentication-and-sessions.md](0030-authentication-and-sessions.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, güvenlik, dizin servisi yöneticileri |
| Tür | Uzlaştırma (Reconcile) |
| İzlenen | DVE.3, 27, 77–78; QA-01 |
| Kapatır | CDR-22 |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

DVE.3, tanımlı bir LDAP dizin servisine karşı kimlik doğrulama ve erişimin her kullanıcının yetkileriyle sınırlandırılmasını ister. DVE.27, otomasyon istemcilerini (Jenkins, CLI) ekler. CDR-22, LDAP protokolünü açık bırakır. SDP §5, durumsuz JWT oturumlarıyla LDAP doğrudan bağlanmayı belirtir.

Mevcut durum:

* `LdapDirectoryService`, iki sabit kullanıcıyı (`admin`, `operator`) kabul eden ve bir `Role` döndüren bir taklittir.
* Oturum, Flask'ın varsayılan imzalı çerezidir. `username`, `role` ve bir bağlantı token'ı tutar; ömrü `session_lifetime` (24 saat) değeridir ve gizli anahtar `dve.ini`'den gelir (geliştirme varsayılanı `dev-insecure-change-me`).
* Otomasyon istemcisi kimlik doğrulaması yoktur.

## Karar Etkenleri

* Oturum kapatma ve rol değişiklikleri hemen etkili olmalıdır (QA-01).
* Tarayıcı oturumları XSS ile token hırsızlığına ve CSRF'ye dayanıklı olmalıdır.
* Otomasyon istemcileri etkileşimli oturum açamaz; uzun ömürlü, iptal edilebilir ve kapsamlı kimlik bilgilerine ihtiyaç duyar.
* Tek bir arka uç vardır (ADR-0004); bu yüzden durumsuz token'ların başka bir yerde doğrulanması gerekmez.

## Değerlendirilen Seçenekler

* Oturumlar: Flask imzalı çerezi (mevcut) / durumsuz JWT (SDP §5) / sunucu tarafı oturum deposuyla opak oturum kimliği
* Otomasyon: LDAP bağlanmalı paylaşılan servis hesabı / SaaG'nin verdiği kişisel veya servis API token'ları

## Karar Sonucu

Seçilen seçenekler: **LDAP ara-ve-bağlan**, tarayıcılar için **opak sunucu tarafı oturumlar** ve otomasyon istemcileri için **SaaG'nin verdiği API token'ları**. Sunucu tarafı oturumlar anında iptal edilebilir ve oturum deposu zaten vardır (PostgreSQL, ADR-0008). JWT'nin ana avantajı olan paylaşılan durum olmadan doğrulama, tek bir arka uçta fayda sağlamaz ve iptali zorlaştırır.

* **LDAP protokolü (CDR-22'yi kapatır):**
  * LDAPS (port 636) veya 389 üzerinde StartTLS ile LDAPv3. Sertifikalar yapılandırılmış CA paketine göre doğrulanır. `ldap3` kütüphanesi kullanılır.
  * Akış:
    1. Yapılandırılmış bir servis hesabı bağlanır ve kullanıcıyı bir temel DN altında `uid`/`sAMAccountName` ile arar.
    2. SaaG, verilen parolayla bulunan DN olarak bağlanır.
    3. SaaG, yetkilendirme için grup üyeliklerini okur (ADR-0031).
  * Parola asla saklanmaz veya günlüğe yazılmaz.
* **Tarayıcı oturumları:**
  * Oturum kimliği, `HttpOnly`, `Secure`, `SameSite=Strict` bir çerezde rastgele 256 bitlik bir değerdir. Oturum satırı (kullanıcı, roller, oluşturma, son görülme, sona erme) PostgreSQL'dedir.
  * Boşta kalma zaman aşımı 30 dakika, mutlak zaman aşımı 12 saattir. İkisi de yapılandırılabilir.
  * Oturum kapatma satırı siler.
  * Durum değiştiren istekler ayrıca bir CSRF başlık token'ı gerektirir.
* **Otomasyon istemcileri:**
  * Uygun role sahip bir kullanıcı (ADR-0031), ad, kapsam (ör. `evaluation:run`) ve sona erme tarihiyle API token'ları oluşturur.
  * Token'ın yalnızca özeti saklanır. İstemci `Authorization: Bearer <token>` gönderir.
  * Token'lar arayüzden iptal edilebilir. Kullanımları denetim izine kaydedilir (ADR-0035).
* **Taklit:** sabit kullanıcılı taklit yalnızca `tests/fakes/` altında bir test sahtesi olarak kalır (ADR-0003). Geliştirme yığını `dev/compose.yaml` içinde bir OpenLDAP konteyneri kazanır.

### Sonuçlar

* İyi, çünkü hem oturumlar hem token'lar için iptal anında etkilidir ve tarayıcı asla bir bearer token tutmaz.
* İyi, çünkü CI hatları, bir kişinin parolasını paylaşmadan kapsamlı ve iptal edilebilir kimlik bilgilerine sahip olur.
* Kötü, çünkü her istek ucuz, indeksli bir okuma olan bir oturum araması gerektirir.
* Kötü, çünkü LDAP servis hesabının dizin yöneticilerince sağlanması ve gizli bilgisinin yönetilmesi gerekir (ADR-0032).

### Doğrulama

* Geliştirme OpenLDAP'ına karşı bütünleştirme testleri geçerli oturum açmayı, yanlış parolayı, bilinmeyen kullanıcıyı ve TLS hatasını kapsar.
* Testler, oturum kapatmanın ve token iptalinin kimlik bilgisini sonraki istekte geçersiz kıldığını gösterir.
* Bir güvenlik testi, çerez bayraklarını ve CSRF denetiminin başlıksız istekleri reddettiğini doğrular.

## Seçeneklerin Artıları ve Eksileri

### Flask imzalı çerezi (mevcut)

* İyi, çünkü sunucu durumu gerektirmez.
* Kötü, çünkü süresi dolmadan iptal edilemez (oturum kapatma yalnızca tarayıcıdaki kopyayı temizler). Rol 24 saat boyunca çerezde dondurulmuş kalır ve bütünlüğü şu an bir ini dosyasında saklanan bir gizli bilgiye bağlıdır.

### Durumsuz JWT (SDP §5)

* İyi, çünkü paylaşılan durum olmadan doğrulanabilir ve CLI için de çalışır.
* Kötü, çünkü iptal bir engel listesi gerektirir; bu da durumu geri getirir. Tarayıcı deposunda tutulan token'lar XSS'e açıktır.

### Opak sunucu tarafı oturumlar + API token'ları

* İyi, çünkü iptal edilebilir, standart tarayıcı uygulamasını izler ve otomasyon istemcilerine ayrı kimlik bilgileri verir.
* Kötü, çünkü zaten var olan bir oturum deposu gerektirir.

## Ek Bilgiler

* Kod: `dve/src/dve/adapters/ldap_directory_service.py` (taklit), `dve/src/dve/api.py`
* İlgili: ADR-0005, ADR-0008, ADR-0028, ADR-0031, ADR-0032, ADR-0035
