# ADR-0009: Ön yüz uygulama mimarisi

> Bu doküman [0009-frontend-application-architecture.md](0009-frontend-application-architecture.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi, UX |
| Tür | Uzlaştırma (Reconcile) |
| İzlenen | DVE.1, 4–27; QA-07, QA-12; UXD §1–7 |
| Kapatır | — |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

Operasyon Paneli bugün tek bir Flask şablonu (`templates/index.html`) ve 1.950 satırlık tek bir sade JavaScript dosyası (`static/app.js`) olarak geliştirilmiştir. Oturum açma, veri kaynağı bağlantısı, seçim ve Model Verisi üretimini kapsar. R3'ten itibaren arayüzün çok daha fazlasına ihtiyacı vardır:

- etkileşimli bir çizge düzenleyici (DVE.17, 19–20);
- sanallaştırılmış bulgu tabloları (DVE.21–23);
- grafikler (DVE.58, 70);
- çok daha fazla ekran.

UXD ve SDP §5; Next.js 14 ile React 18, Refine, shadcn/ui, Tailwind, TanStack Query/Table, React Flow ve Recharts/ECharts'ı varsayar. UXD §6 rota düzeyinde kod bölme ve performans bütçelerini, UXD §7 ise erişilebilirlik kurallarını belirler.

## Karar Etkenleri

* R3'ten itibaren arayüz kapsamı: bir çizge düzenleyici, veri tabloları, grafikler, yaklaşık 15 ekran (UXD §4).
* UXD §6 bütçeleri (rota parçalama, tablo sanallaştırma, 60 fps tuval) ve UXD §7 erişilebilirliği.
* Şirket içi kurulum: daha az çalışma zamanı servisi daha iyidir (QA-10).
* İhtiyaç duyulan bileşen ekosistemi (çizge tuvali, tablolar, grafikler) React merkezlidir.

## Değerlendirilen Seçenekler

* Sunucu tarafında işlenen şablonlar ve sade JavaScript ile devam etmek (mevcut)
* Refine ve shadcn/ui ile Next.js (SDP §5, UXD)
* Vite ile derlenen, arka uç tarafından statik dosya olarak sunulan ve UXD bileşen kütüphanelerini kullanan bir React tek sayfa uygulaması

## Karar Sonucu

Seçilen seçenek: "Vite ile derlenen bir React tek sayfa uygulaması". UXD'nin tüm kütüphane seçimlerini (Radix üzerinde shadcn/ui, Tailwind, TanStack Query/Table, React Flow, Recharts/ECharts) korur, bu yüzden UXD geçerliliğini sürdürür. Ayrıca statik dosyalara derlenir, böylece üretimde Node.js sunucusu çalışmaz. Oturum açma arkasındaki bir iç araç, Next.js'in sunucu tarafı işlemesinden bir kazanç elde etmez.

* **Konum:** `web/` (ADR-0004), TypeScript, React 18, tembel rotalarla React Router. Bu, UXD §6'nın "ekran grubu başına bir rota parçası" kuralını karşılar.
* **Veri katmanı:** REST API'ye (ADR-0005) karşı TanStack Query. Tipli API istemcisi, depodaki OpenAPI dokümanından üretilir.
* **Yönetim/CRUD iskeleti:** Refine isteğe bağlıdır. Yalnızca özel çizge ve bulgu görünümlerini kısıtlamadan CRUD ekranlarını kısaltıyorsa benimsenir.
* **Sunum:** API konteyneri derlenmiş `web/dist`'i `/` adresinden sunar; böylece API ile aynı kökendir (origin). Çerezler birinci taraf kalır (ADR-0030).
* **Taşıma:** mevcut dört görünüm (oturum açma, kaynaklar, seçim, üretim) R3'te yeniden yazılır. Eşdeğerlik sağlandığında `app.js` kaldırılır.
* UXD'deki Next.js'e özgü özellik atıfları güncellenir:
  * `next/font` → kendi barındırılan `@fontsource` dosyaları;
  * rota segmentleri → tembel rotalar.

### Sonuçlar

* İyi, çünkü çerçeve kabuğu dışında UXD tasarımı ve kütüphane seçimleri değişmeden taşınır.
* İyi, çünkü Next.js'e göre üretimde bir çalışma zamanı eksiktir ve statik dosyalar önbelleğe alınabilir.
* Kötü, çünkü mevcut sade arayüz yeniden yazılır ve CI ile geliştirmede (üretimde değil) bir Node araç zinciri gerekir.
* Kötü, çünkü SSR yoktur. İlk boyama, UXD §6'nın bütçelediği JS paketine bağlıdır.

### Doğrulama

* CI derlemesi `web/dist`'i üretir. Bir paket boyutu denetimi, rota başına bütçeyi zorlar.
* Playwright duman testleri (ADR-0041), paketi sunan API konteynerine karşı çalışır.
* Her rotada otomatik erişilebilirlik denetimleri (axe) çalışır (ADR-0042).

## Seçeneklerin Artıları ve Eksileri

### Şablonlar + sade JavaScript (mevcut)

* İyi, çünkü derleme araç zinciri gerektirmez ve zaten çalışır.
* Kötü, çünkü bileşen çatısı olmadan bir çizge düzenleyici, sanallaştırılmış tablolar ve grafikler, kütüphanelerin sağladıklarını yeniden yazmak demektir. 1.950 satırlık tek bir dosyanın bakımı zaten zordur.

### Next.js + Refine (SDP, UXD)

* İyi, çünkü dokümanlarla birebir örtüşür ve dosya tabanlı yönlendirmesi vardır.
* Kötü, çünkü varsayılan modunda üretimde bir Node.js sunucusu gerektirir. Statik dışa aktarma Next.js özelliklerinin çoğundan vazgeçer; geriye ek kısıtlarla bir Vite SPA'sı kalır.

### Vite ile React SPA

* İyi, çünkü UXD kütüphanelerini korur, sunucu çalışma zamanı gerektirmez ve derlemesi basittir.
* Kötü, çünkü yönlendirme ve yerleşim kurallarını ekip belirlemelidir.

## Ek Bilgiler

* [UXD](../UXD.md), [SDP §5](../../planning/SDP.tr.md)
* Kod: `dve/src/dve/templates/index.html`, `dve/src/dve/static/app.js`
* İlgili: ADR-0005, ADR-0025, ADR-0030, ADR-0042
