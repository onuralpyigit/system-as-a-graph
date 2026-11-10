# ADR-0005: Arka uç web çatısı ve API biçimi

> Bu doküman [0005-backend-web-framework.md](0005-backend-web-framework.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi |
| Tür | Uzlaştırma (Reconcile) |
| İzlenen | DVE.1–2, 27, 78; QA-06, QA-11 |
| Kapatır | — |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

SDP §5, REST/JSON ile FastAPI'yi belirtir. `dve/` ise Flask 2.3 üzerine kuruludur (`dve/src/dve/api.py`, yaklaşık 320 satır, 15 API uç noktası, eşzamanlı (senkron) çalışma, `_json_body` içinde elle yazılmış gövde doğrulaması). R3'ten itibaren API önemli ölçüde büyür: çalışma modeli düzenleme, doğrulama işlemleri, bulgu sorguları ve R7'de makine tarafından işlenebilir olması gereken otomasyon istemcisi sözleşmesi (DVE.27, 78). Çatı seçimini değiştirmek, API küçükken en ucuzdur.

## Karar Etkenleri

* DVE.78, otomasyon istemcileri için sonuçların "makine tarafından işlenebilir bir biçimde" sunulmasını gerektirir. Yayımlanmış, sürümlü bir API şeması buna doğrudan hizmet eder (ADR-0028).
* İstek doğrulaması tutarlı olmalı ve ADR-0034'ün hata kayıtlarını üretmelidir.
* Taşıma maliyeti, R3'ün kapsamına göre küçük kalmalıdır.
* Ekip bir Python ekibidir; iki seçenek de Python'dur.

## Değerlendirilen Seçenekler

* Flask 2.3 (mevcut), isteğe bağlı olarak bir OpenAPI eklentisiyle (flask-smorest)
* Pydantic modelleriyle FastAPI (SDP §5)
* Django REST Framework

## Karar Sonucu

Seçilen seçenek: "Pydantic modelleriyle FastAPI", çünkü tek bir tip açıklamaları setinden üç şey sağlar: üretilen bir OpenAPI şeması, istek ve yanıt doğrulaması, ve CLI için tipli istemci üretimi. DVE.27/78 ve ADR-0028'in ihtiyaç duyduğu tam olarak bunlardır. Mevcut API, R3 içinde taşınabilecek kadar hâlâ küçüktür.

* **API biçimi:** JSON gövdeli REST; kaynaklar `/api/v1/` altında. Uzun süren işler `POST` ile başlatılır ve bir işlem kimliğiyle birlikte `202 Accepted` döner (ADR-0006, ADR-0024).
* **Hatalar:** alan hatalarından eşlenen tek bir hata gövdesi `{ "error": { "code", "message", "details" } }`.
* **Şema:** OpenAPI dokümanı derleme sırasında üretilir ve depoya işlenir; böylece API değişiklikleri incelemede görünür olur.
* **Taşıma:** `api.py` ve `test_api.py`, yeni uç noktalar eklenmeden önce R3'te rota rota taşınır. Oturum yönetimi ADR-0030'u izler.

### Sonuçlar

* İyi, çünkü API sözleşmesi, doğrulama ve dokümantasyon aynı kaynaktan gelir.
* İyi, çünkü ADR-0006 ileride SSE'yi benimserse durum akışı için asenkron uç noktalar kullanılabilir.
* Kötü, çünkü 15 uç noktanın ve testlerinin tek seferlik taşınması gerekir.
* Kötü, çünkü bugün kullanılan Flask oturum çerezi mekanizmasının doğrudan bir FastAPI karşılığı yoktur; ADR-0030 onun yerini alır.
* Nötr, çünkü Celery entegrasyonu çatıdan bağımsızdır.

### Doğrulama

* Üretilen OpenAPI dosyası depodakinden farklıysa CI başarısız olur.
* Taşınan `test_api.py`, test istemcisi üzerinden FastAPI uygulamasına karşı geçer.

## Seçeneklerin Artıları ve Eksileri

### Flask 2.3 (mevcut)

* İyi, çünkü zaten çalışır ve taşıma maliyeti yoktur.
* Kötü, çünkü doğrulama elle yazılmıştır ve OpenAPI bir eklenti ile paralel bir şema tanımı (marshmallow) gerektirir.

### FastAPI (SDP §5)

* İyi, çünkü üretilen bir OpenAPI şeması, Pydantic doğrulaması ve asenkron destek sunar.
* Kötü, çünkü taşıma emeği ve oturum yönetiminin yeniden işlenmesi gerekir.

### Django REST Framework

* İyi, çünkü yönetim arayüzü ve ORM içeren olgun bir çatıdır.
* Kötü, çünkü en büyük taşımayı gerektirir ve ORM'si ADR-0008 ile örtüşür.

## Ek Bilgiler

* Kod: `dve/src/dve/api.py`
* İlgili: ADR-0006, ADR-0024, ADR-0028, ADR-0030
