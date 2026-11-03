# ADR-0035: İzlenebilirlik, köken bilgisi ve denetim izi

> Bu doküman [0035-traceability-and-provenance.md](0035-traceability-and-provenance.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, güvenlik, kalite güvence |
| Tür | Karar (Decide) |
| İzlenen | MDG.1, 9, 14, 18, 22; SCG.5–6; FDM.2–3; ADM.1; SMM.5, 26, 35; DVE.16, 24–26, 78; QA-04 |
| Kapatır | — |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

"Kontrollü, izlenebilir" ifadesi neredeyse her CSC'nin ilk isterinde geçer (MDG.1, ADM.1) ve belirli isterler neyin kaydedileceğini adlandırır:

* bir model için kullanılan Model Verisi dosyası (SMM.26);
* Analitik Değerlendirme Verisinin saha ya da sentetik kaynağı (SMM.35);
* senaryo girdileri (SCG.6, DVE.25);
* yükleme kaynağı ve zamanı (FDM.3);
* her yerde proje, platform ve sistem sürümü.

Mevcut durum:

* Model Verisi `produced_by`, `generated_at` ve dosya başına üst veriyi kaydeder.
* Çalıştırma kimlikleri Celery görev kimlikleridir.
* Zaman damgaları saat dilimsiz yerel zamandır.
* Türetilmiş sonuçları girdilerine bağlayan, dosya yollarının ötesinde hiçbir şey yoktur.
* Kimin ne yaptığına dair denetim izi yoktur.

## Karar Etkenleri

* Her sonuç (bulgu, rapor, kurulum kararı), onu üreten kesin girdilere, kurallara ve araç sürümüne kadar izlenebilir ve yeniden üretilebilir olmalıdır (QA-04).
* Güvenlik açısından önemli eylemler bir kullanıcıya veya otomasyon istemcisine atfedilebilir olmalıdır (QA-01).
* Çıktı türü başına bir mekanizma değil, tüm CSC'ler için tek bir mekanizma.
* Kayıtlar kurcalamaya karşı belirgin ve yalnızca eklenebilir olmalıdır.

## Değerlendirilen Seçenekler

* Her çıktıda geçici üst veri alanları (mevcut)
* İlişkisel depoda içerik özetli bir çıktı kaydı ve soy çizgesi, ayrıca bir denetim günlüğü
* Tüm durum değişikliklerinin tam olay kaynaklaması (event sourcing)

## Karar Sonucu

Seçilen seçenek: PostgreSQL'de (ADR-0008) "İçerik özetli bir çıktı kaydı ve soy çizgesi, ayrıca bir denetim günlüğü". Tek bir tablo tasarımıyla uçtan uca soy sağlar ve her CSC'yi olaylar etrafında yeniden yapılandırmayı gerektirmez.

* **Çıktılar:** kalıcı hâle getirilen her çıktı, oluşturulduğu anda `artifact` tablosuna şu alanlarla kaydedilir:
  * `artifact_id` (UUID) ve `kind`; tür `model_data_file`, `model_instance`, `synthetic_data_set`, `field_record`, `analytical_evaluation_data` veya `report`'tur;
  * `location` (yol, çizge adı veya tablo anahtarı) ve `sha256` (dosyalar ve veri setleri için içerik özeti);
  * `project`, `platform`, `system_version`;
  * `created_by` (kullanıcı veya otomasyon istemcisi kimliği), `created_at` (UTC), `producing_operation_id`;
  * `tool_version` (paket sürümü + SaaG derlemesinin git commit'i);
  * `attributes` (JSONB, türe özgü; ör. AED için `source_kind: field | synthetic`, SMM.35).
* **Soy:** `artifact_input(artifact_id, input_artifact_id, role)` her çıktıyı türetildiği çıktılara bağlar. Örneğin:
  * Model Verisi dosyası ← CMDB anlık görüntü başvurusu ve klon commit özetleri;
  * temel model ← Model Verisi dosyası;
  * AED ← saha kayıtları veya sentetik veri seti;
  * rapor ← işlem.

  İşlemler (ADR-0024) girdi çıktı kimliklerini, kural kataloğu sürümünü ve profili kaydeder.
* **Dış girdiler:** SaaG çıktısı olmayan girdiler, tüketen çıktının öznitelikleri olarak kaydedilir: CMDB sorgu zamanı ve seçim, ayrıca birim başına etiket ve commit özetiyle Git depo URL'si (ADR-0010, ADR-0012). SaaG çıktıları değiştirilemezdir (ADR-0013, ADR-0016).
* **Zaman damgaları:** tüm zaman damgaları, saat dilimi bilgili `datetime` ile ofsetli UTC olarak ISO 8601'dir.
* **Denetim günlüğü:** `audit_event(at, actor, actor_kind, action, target, outcome, details)`. Yalnızca eklenebilirdir; uygulama rolünün yalnızca `INSERT` ve `SELECT` yetkisi vardır, `UPDATE` veya `DELETE` yetkisi yoktur. Kaydedilen olaylar:
  * başarılı ve başarısız oturum açma, oturum kapatma;
  * API token oluşturma ve iptali (ADR-0030);
  * veri kaynağı yapılandırması oluşturma, değiştirme, silme ve bağlanma (ADR-0032);
  * işlem başlatma ve iptali;
  * çalışma modeli düzenlemeleri (özet; ayrıntı değişiklik günlüğündedir, ADR-0016);
  * kurulum değerlendirmesi için kural profili seçimi;
  * rapor dışa aktarma.
* **Saklama:** ADR-0040'a göre. Soy satırları tanımladıkları çıktılardan daha uzun yaşar; böylece silinmiş çıktılar açıklanabilir kalır.

### Sonuçlar

* İyi, çünkü her bulgu veya karar izlenebilir:
  bulgu → işlem → model örneği + revizyon → Model Verisi dosyası (özet) → commit'ler ve CMDB anlık görüntüsü. Ardından yeniden çalıştırılabilir.
* İyi, çünkü tek bir mekanizma SMM.26, SMM.35, SCG.6, FDM.3 ve DVE.26'nın "kullanılan Sistem Modeli / kullanılan AED ve veri kaynağı" rapor alanlarına hizmet eder.
* Kötü, çünkü çıktı üreten her kod yolunun çıktısını kaydetmesi gerekir. Bu, depolara kaydı yapan tek bir `save` yolu verilerek zorlanır.
* Kötü, çünkü denetim günlüğü saklama (ADR-0040) uygulanana kadar sınırsız büyür.

### Doğrulama

* Uçtan uca bir test bir Model Verisi dosyası üretir, bir model inşa eder ve doğrulama çalıştırır. Ardından bir bulgudan klon commit özetlerine kadar soyu geriye doğru izler.
* Bir veri tabanı testi, uygulama rolünün `audit_event` satırlarını güncelleyemediğini veya silemediğini doğrular.
* Bir test, `mdg`'nin yazdığı her zaman damgasının saat dilimi bilgili olduğunu doğrular.

## Seçeneklerin Artıları ve Eksileri

### Geçici üst veri (mevcut)

* İyi, çünkü basittir.
* Kötü, çünkü çıktılar arasında bağlantı, özet ve denetim yoktur.

### Çıktı kaydı + soy + denetim günlüğü

* İyi, çünkü makul bir şema işiyle tam soy ve atıf sağlar.
* Kötü, çünkü gerektirdiği kayıt disiplini gerekir.

### Olay kaynaklama

* İyi, çünkü tam geçmiş örtüktür.
* Kötü, çünkü her CSC'nin büyük ölçüde yeniden tasarlanması demektir; bu, ihtiyaçla orantısızdır.

## Ek Bilgiler

* Kod: `mdg/src/mdg/domain/model_setup_data.py`, `acquired_file.py`, `workspace.py`
* İlgili: ADR-0008, ADR-0010, ADR-0012, ADR-0013, ADR-0016, ADR-0024, ADR-0030, ADR-0032, ADR-0040
