# ADR-0002: Kanonik bileşen kimlikleri ve alan terminolojisi

> Bu doküman [0002-canonical-component-identifiers.md](0002-canonical-component-identifiers.md) dosyasının Türkçe çevirisidir. Bağlayıcı metin İngilizce olandır.

| Alan | Değer |
|---|---|
| Durum | Proposed |
| Tarih | 2026-11-03 |
| Karar vericiler | CDR Kurulu |
| Danışılanlar | Geliştirme ekibi |
| Tür | Onaylama (Ratify) |
| İzlenen | Tüm SRS isterleri (atıf biçimi); BACKLOG bulguları T1, T2, T3, L3 |
| Kapatır | — |
| Son karar tarihi | A Dalgası (2026-11-27) |
| Yerine geçtiği | — |

## Bağlam ve Problem Tanımı

Aynı bileşen ve çıktılar, doküman seti ve kod genelinde farklı adlar taşır ([BACKLOG Ek A](../../planning/BACKLOG.md)):

- SRS.md `MDG / SCG / FDM / ADM / SMM / DVE` kullanır.
- SRS.tr ve SDP.tr `MVU / SUR / SVY / AVY / SMY / TDM` kullanır.
- SDD, STD ve CDR `MSG / SCG / TDM / ADM / CSM / DVE` kullanır.

Bu nedenle `TDM`, Türkçe dokümanlarda Tasarım Doğrulama Motorunu, SDD'de ise Telemetri Veri Yöneticisini (= FDM) ifade eder. CDR maddeleri var olmayan ister kimliklerine atıf yapar (`MSG.6`, `CSM.30`). Çıktıların adları da değiştirilmiştir: "Model Verisi" "Model Setup Data", "Sistem Modeli" ise "Core System Model" olmuştur. Kod SDD terminolojisini izler (`ModelSetupData`, `model_setup_data_store`, `test_msd.py`). Docstring'leri de eski bir ister numaralandırmasına atıf yapar ("SRS DSM-MDG req 19"). Tek bir kanonik şema olmadan SRS → SDD → STD → kod zincirindeki hiçbir iz güvenilir biçimde çözülemez.

## Karar Etkenleri

* Her ister atfı tam olarak bir SRS isterine çözülmelidir.
* Türkçe ve İngilizce dokümanlar aynı kimliklere atıf yapmalıdır.
* Yeniden adlandırma, R3 DVE isterlerine yoğun atıf yapan doğrulama kodunu eklemeden önce tamamlanabilecek kadar ucuz olmalıdır.

## Değerlendirilen Seçenekler

* Her yerde SRS.md kimlikleri ve terimleri (BACKLOG kararı T1)
* Doküman başına adları korumak ve bir eşleme tablosu eklemek
* Her yerde SDD terminolojisi (`MSG`, `TDM`, `CSM`, "Model Setup Data", "Core System Model")

## Karar Sonucu

Seçilen seçenek: "Her yerde SRS.md kimlikleri ve terimleri", çünkü SRS sözleşmesel temel dokümandır ve `TDM` çakışması içermeyen tek şema odur.

1. **Bileşen kimlikleri:** her dilde `MDG`, `SCG`, `FDM`, `ADM`, `SMM`, `DVE`. Altyapı kısıtı `FDM-INF.1`'dir. Türkçe dokümanlar bileşenlerin Türkçe *adlarını* (ör. "Model Veri Üreteci") kanonik kimliklerle birlikte kullanır. Türkçe kısaltmalar kullanımdan kaldırılır.
2. **İster atıfları:** SRS.md'deki numaralandırmayla `<KİMLİK>.<n>`, ör. `MDG.19`, `DVE.27`. Aralıklar `DVE.32–35` biçiminde yazılır.
3. **Çıktı terimleri:** SRS'teki gibi "Model Verisi" (dosya: "Model Verisi dosyası"), "Sistem Modeli", "Analitik Değerlendirme Verisi", "Sistem Saha Kayıtları", "Yazılım Birimi Sürüm Envanteri". "Model Setup Data" ve "Core System Model" kullanımdan kaldırılır.
4. **Kod:**
   * Paket dizinleri `mdg/ scg/ fdm/ adm/ smm/ dve/` (ADR-0004).
   * Genel tanımlayıcılar R3 sırasında tek bir yeniden düzenlemeyle `model_setup_data` / `ModelSetupData` yerine `model_data` / `ModelData` olur.
   * Docstring'ler isterlere `MDG.n` biçiminde atıf yapar.

### Sonuçlar

* İyi, çünkü her iz çözülebilir hâle gelir ve CDR-ister bağlantıları mekanik olarak denetlenebilir.
* İyi, çünkü yeni R3 kodu doğru terminolojiyle başlar.
* Kötü, çünkü SDD, STD ve CDR'nin yeniden adlandırılması gerekir (BACKLOG hikâyesi S0.2-01). Kod yeniden düzenlemesi `mdg` genel API'sine ve `dve`'nin bu API'yi içe aktarmalarına dokunur.
* Kötü, çünkü mevcut Model Verisi JSON dosyaları alan adlarında eski adlandırmayı taşır. Bunların sürümlenmesini ADR-0013 ele alır.
* Takip: BACKLOG S0.2-01 (doküman yeniden adlandırmaları); R3'te bir kod yeniden düzenleme hikâyesi; CDR "Source" hücrelerinin güncellenmesi.

### Doğrulama

* Bir CI denetimi `docs/` ve `*/src/` altında kaldırılmış biçimleri arar. Desen `\b(MSG|TDM|CSM|MVU|SUR|SVY|AVY|SMY)\.\d`, ayrıca "Model Setup Data" ve "Core System Model" ifadeleridir. `SRS.tr.md` ve `SDP.tr.md` taşınana kadar bunların dışındaki her eşleşmede başarısız olur.
* Pull request incelemesi atıf biçimini denetler.

## Seçeneklerin Artıları ve Eksileri

### Her yerde SRS.md kimlikleri ve terimleri

* İyi, çünkü tek bir doğruluk kaynağı vardır ve BACKLOG ile ADR yol haritası zaten bunu kullanır.
* Kötü, çünkü doküman ve kod genelinde tek seferlik bir yeniden adlandırma gerekir.

### Doküman başına adlar ve eşleme tablosu

* İyi, çünkü hiçbir şeyin yeniden adlandırılması gerekmez.
* Kötü, çünkü `TDM` belirsiz kalır ve her okuyucu her atfı çevirmek zorunda kalır.

### Her yerde SDD terminolojisi

* İyi, çünkü kod zaten bunu kullanır.
* Kötü, çünkü sözleşmesel doküman olan SRS ile çelişir ve Türkçede `TDM` eşadlılığını korur.

## Ek Bilgiler

* [BACKLOG §0.2 ve Ek A](../../planning/BACKLOG.md)
* [ADR Yol Haritası](../ADR-ROADMAP.tr.md)
