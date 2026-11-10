# ADR-0023: Doğrulama kural seti kataloğu ve yönetişimi

> Bu doküman [0023-verification-rule-set-catalog.md](0023-verification-rule-set-catalog.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, sistem mühendisliği, arakatman sorumluları |
| Tür | Karar (Decide) |
| İzlenen | DVE.18, 32–49, 76–77; QA-04, QA-11 |
| Kapatır | CDR-01, CDR-02, CDR-03, CDR-04, CDR-05, CDR-06, CDR-07, CDR-08 |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

CDR-01…08, doğrulama kurallarının *içeriğini* açık bırakır: QoS kuralları, kapsamdaki haberleşme servisleri, yük dengeleme, çekirdek tahsisi, işletim sistemi ayarları, bellek tahsisi, mimari kurallar ve sınıflandırma ölçütleri. Bunlar, mühendislerin yıllarca iyileştireceği alan kurallarıdır; mimari kararlar değildir. Her kural setini bir ADR olarak yazmak, her eşik değişikliğini bir ADR'ye dönüştürür.

Mimari karar olan şey, kural içeriğinin nerede tutulduğu, nasıl sürümlendiği, kimin onayladığı ve nasıl test edildiğidir. ADR-0022 kural kaydı biçimini sabitler. DVE.77 ayrıca seçilebilir kural setlerini ima eden bir "değerlendirme profili"nden söz eder.

## Karar Etkenleri

* Her bulgu, onu üreten kesin kural tanımına kadar izlenebilir olmalıdır (QA-04).
* Kural değişiklikleri alan uzmanı onayı ve inceleme gerektirir.
* R3, her kural setinde uzlaşılmadan önce başlamalıdır. Geçici kurallar onaylı olanlardan ayırt edilebilmelidir.
* Farklı projeler veya platformlar farklı eşiklere ihtiyaç duyabilir (DVE.77 "değerlendirme profili").

## Değerlendirilen Seçenekler

* Depoda, pull request ile onaylanan sürümlü bir kural kataloğu
* Çalışma zamanında bir yönetim arayüzüyle düzenlenebilen, veri tabanındaki kurallar
* Kural ailesi başına bir ADR

## Karar Sonucu

Seçilen seçenek: "Depoda, pull request ile onaylanan sürümlü bir kural kataloğu", çünkü ek araç maliyeti olmadan tam geçmiş, inceleme, CI'da test ve kesin yeniden üretilebilirlik (katalog sürümü = git etiketi) sağlar.

* **Konum:** aile başına bir YAML dosyasıyla `dve/rules/`:

  | Dosya | Kural ailesi | Kapatır |
  |---|---|---|
  | `qos.yaml` | Topic QoS (DVE.32–35) | CDR-01 |
  | `communication.yaml` | Kapsamdaki arakatman dışı haberleşme servisleri (DVE.39) | CDR-02 |
  | `load_balancing.yaml` | İşlemci birimlerine dağılım (DVE.40) | CDR-03 |
  | `cpu_allocation.yaml` | Çekirdek tahsisi (DVE.41–43) | CDR-04 |
  | `os_settings.yaml` | İşletim sistemi ayarları (DVE.44) | CDR-05 |
  | `memory.yaml` | Çalışma zamanı bellek tahsisi (DVE.45) | CDR-06 |
  | `architecture.yaml` | Mimari kurallar (DVE.49) | CDR-07 |
  | `structural.yaml` | Yayımcı/tüketici eşleştirme, döngüler, bütünlük (DVE.36–38, 46–48) | — |
  | `classification.yaml` | Uygunluk sınıflandırma eşikleri (DVE.18) | CDR-08 |

* **Profiller:** `dve/rules/profiles/<ad>.yaml`, kural kimliklerini seçer ve parametreleri geçersiz kılar. Bir profil bir projeye veya platforma kapsamlandırılabilir. Hiçbiri seçilmezse `default.yaml` kullanılır. Her kurulum değerlendirmesi isteği kendi profilini belirtir (DVE.77).
* **Sürümleme:**
  * Her kuralın kendi `version` değeri vardır.
  * Katalog bütün olarak, onu içeren sürümün depo etiketiyle sürümlenir.
  * Her işlem, kullanılan katalog sürümünü ve profili kaydeder (ADR-0024).
* **Onay:**
  * Bir kural `provisional` olarak girer. Geliştirme ekibi incelemesiyle birleştirilebilir; raporlanır ama sınıflandırmayı etkilemez (ADR-0022).
  * `status: approved` ataması, CDR Kurulunun o aile için belirlediği alan sorumlusunun onayını gerektirir; onay pull request'te kayıtlıdır.
* **Test:** her kural, onu tetiklemesi ve tetiklememesi gereken fikstür modelleriyle birlikte gelir (`dve/rules/fixtures/`). CI bunları çalıştırır.
* **Çalışma zamanı değişiklikleri:** yoktur. Kullanıcılar çalışma zamanında profil seçer, ama kural düzenleyemez. Yeni bir eşik, bir katalog değişikliği ve bir sürüm gerektirir.
* **CDR kapanışı:** CDR-01…08'in her biri, aile dosyası CDR maddesinin kaynak aralığındaki her isteri kapsayan en az bir `approved` kural içerdiğinde `Resolved` olur. CDR kaydı dosyaya ve katalog sürümüne bağlantı verir. O zamana kadar madde `Open` kalır ve R3 geçici kurallarla çalışır.

### Sonuçlar

* İyi, çünkü kural içeriği, ADR değişikliklerine yol açmadan alan uzmanlarının denetiminde gelişebilir.
* İyi, çünkü her bulgu (katalog sürümü, profil, model örneği revizyonu) üçlüsünden yeniden üretilebilir.
* Kötü, çünkü bir eşiği değiştirmek bir sürüm gerektirir. Bu kabul edilmiştir: izlenebilirlik, düzenleme hızından daha değerlidir.
* Kötü, çünkü alan sorumluları YAML'ı pull request'lerde incelemelidir; bu yüzden biçim okunabilir ve belgelenmiş kalmalıdır.

### Doğrulama

* Bir CI şema denetimi her kural dosyasını kural kaydına (ADR-0022), her profili kataloğa göre doğrular.
* Her kural için fikstür testleri geçer.
* `approved` bir kural `version` artırılmadan değişirse CI denetimi başarısız olur.

## Seçeneklerin Artıları ve Eksileri

### Depoda sürümlü katalog

* İyi, çünkü geçmiş, inceleme, CI ve yeniden üretilebilirlik sağlar.
* Kötü, çünkü değişiklikler sürüme bağlıdır.

### Çalışma zamanında düzenlenebilen veri tabanı kuralları

* İyi, çünkü değişiklikler anında etkili olur.
* Kötü, çünkü değişiklikler incelenmez ve geçmiş ek denetim gerektirir. Sonuçların yeniden üretilmesi zorlaşır ve fikstür testi yoktur.

### Kural ailesi başına ADR

* İyi, çünkü diğer kararlarla aynı süreci kullanır.
* Kötü, çünkü kural içeriği mimari değildir ve her eşik değişikliği bir ADR değişimi olur.

## Ek Bilgiler

* [CDR §1.1](../CDR.md)
* İlgili: ADR-0022, ADR-0024, ADR-0027, ADR-0041
