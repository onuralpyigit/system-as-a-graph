# Yazılım Gereksinimleri Şartnamesi (SRS): System as a Graph (SaaG)

**Tanım:** System as a Graph (SaaG) Sayısal Sistem Modeli, mimari dijital ikiz yaklaşımıyla geliştirilmiş, sistem uygulamalarını fiilen çalıştırmaksızın, sistemin yapısal ve ilişkisel mimarisini düğüm-ilişki temsiliyle modelleyen statik bir sayısal sistem modelidir. Bu modelde yazılım birimleri, arakatman ve haberleşme servisleri, işlemci/konsol birimleri, topic ve mesaj gibi sistem varlıkları düğüm; aralarındaki bağımlılık, yayımlama ve tüketme bağıntıları ise ilişki olarak temsil edilir. Modelin davranışsal analizlere imkân tanıyan boyutu, bileşenlerin koşumuyla değil; saha kayıtlarından veya senaryo üretecinden türetilen Analitik Değerlendirme Verisinin bu model üzerine bindirilmesiyle sağlanır.

SaaG, Yazılım Kırılım Öğesidir (CSCI). Bu Yazılım Gereksinimleri Şartnamesi (SRS), Yazılım Komponentleri (CSC) ile Yazılım Birimleri (CSU) arasında birebir (1:1) bir eşleme kurarak sistemi altı CSC ve altı CSU'ya ayrıştırır. Her işlevsel ister tam olarak bir CSU'ya kapsamlandırılmış olup sisteme ait altyapı kısıtları da resmi olarak dokümante edilmiştir.

**Amaç:** Modelin birincil amacı mimari doğrulamadır. Bu kapsamda yapısal/döngüsel bağımlılıklar, yayımcı/tüketici eşleşmeleri, topic servis kalite parametrelerinin (QoS) uygunluğu, sistemde yer alan donanımların kapasite uygunluğu (CPU çekirdek adedi, RAM boyutu, ağ bant genişliği vb.) ve mimari kurallara aykırı tasarım örüntüleri tasarım aşamasında statik olarak denetlenir. Mimari doğrulama, tasarımda öngörülen mimari ile saha verisinde gözlemlenen çalışma-zamanı yapısı arasındaki sapmaların (architectural drift) tespitini de kapsar. Mimari doğrulamanın yanı sıra model, kurgusal senaryo analizlerine olanak tanır; kullanıcı, yapısal bütünlüğü bozmadan düğüm/ilişki ekleyip çıkararak ya da öznitelikleri değiştirerek deneysel tasarım kurguları oluşturabilir. Bu kurgusal senaryolarda bir varlığın devre dışı kalması, mesaj yoğunluğunun artması veya bant genişliğinin daralması gibi durumların bağımlı varlıklara yayılımı ve mimari üzerindeki etkileri analitik olarak değerlendirilir. Ayrıca model, yazılım birimlerinin hedef ortama kurulum uygunluğunu canlıya alma işlem hattında (pipeline) otomatik olarak değerlendiren bir mekanizma sunar. Böylelikle Sayısal Sistem Modeli, henüz yazılım birimlerinin hedef ortama kurulumları yapılmadan tasarım kararlarının ve değişikliklerinin mimari sonuçlarını öngörmeye yönelik, tekrarlanabilir bir doğrulama ortamı sağlar.

**Tablo 1. SRS İster Dağılımı**

| No | Bileşen | Kısaltma | CSU Sayısı | CSU Kimliği | İster Sayısı |
|---|---|---|---|---|---|
| 1 | Model Kurulum Üreteci | SaaG-MKU | 1 | MKU | 23 |
| 2 | Senaryo Üreteci | SaaG-SUR | 1 | SUR | 7 |
| 3 | Telemetri Veri Yöneticisi | SaaG-TVY | 1 | TVY | 5 (+ 1 Altyapı) |
| 4 | Analitik Veri Yöneticisi | SaaG-AVY | 1 | AVY | 6 |
| 5 | Çekirdek Sistem Modeli | SaaG-CSM | 1 | CSM | 37 |
| 6 | Tasarım Doğrulama Motoru | SaaG-TDM | 1 | TDM | 78 |
| **TOPLAM** | | | **6** | | **156 (+ 1 Altyapı)** |

Her bileşenin CSU başına ister dağılım tabloları, aşağıda ilgili bileşenin kendi bölümünde yer almaktadır. Bu belgedeki her ister, §7 üzerinden kaynak temel sistem kabiliyet isterine izlenebilir.

---

## 1. Model Kurulum Üreteci (SaaG-MKU)

**Tablo 2. SaaG-MKU İster Dağılımı**

| CSU | CSU Kimliği | İster Sayısı |
|---|---|---|
| Model Kurulum Üreteci | MKU | 23 |
| **Alt Toplam** | | **23** |

### 1.1 MKU: Model Kurulum Üreteci

1. MKU, Sayısal Sistem Modeli'nin oluşturulmasına esas Model Kurulum Verisinin kontrollü, izlenebilir, doğrulanabilir şekilde üretilmesini ve model inşası süreçlerine aktarılabilmesini sağlayacaktır.
2. MKU, Model Kurulum Verisi üretimi maksadıyla dış veri kaynağı olarak sistem konfigürasyon yönetimi veri tabanına erişim sağlayabilecek ve bu kaynaktan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir.
3. MKU, Model Kurulum Verisi üretimi maksadıyla dış veri kaynağı olarak sistem yazılım birimleri ve kurulum betikleri kaynak kodu deposuna erişim sağlayabilecek ve bu kaynaktan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir.
4. MKU, Model Kurulum Verisi üretimi maksadıyla dış veri kaynağı olarak Sistem Yazılım Birimleri Paket Deposuna erişim sağlayabilecek ve bu kaynaktan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir.
5. MKU, Model Kurulum Verisi üretimi maksadıyla dış veri kaynağı olarak Sistem Ağ Topolojisi Veri Kaynağına erişim sağlayabilecek ve bu kaynaktan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir.
6. MKU, sistem ağ topolojisi verisini, detayları kritik tasarım aşamasında belirlenecek dış bir veri kaynağından (dosya, veri tabanı vb.) otomatik olarak alabilecektir.
7. MKU, sistem ağ topolojisi verisini kullanıcının ağ topolojisi parametrelerini manuel olarak girmesi yoluyla alabilecektir.
8. MKU, her veri kaynağı için kaynak tipi, kaynak adı, erişim yöntemi, bağlantı adresi ve bağlantı için gerekli kullanıcı bilgilerini kullanıcı tarafından tanımlanabilir ve kaydedilebilir ayar bilgisi olarak yönetecektir.
9. MKU, veri alım işlemlerini proje bilgisi, platform bilgisi ve sistem sürüm numarası ile ilişkilendirilmiş şekilde yürütecektir.
10. MKU, konfigürasyon yönetimi veri tabanından mevcut proje bilgilerini alabilecektir.
11. MKU, konfigürasyon yönetimi veri tabanından seçilen projeye ait platform bilgilerini alabilecektir.
12. MKU, konfigürasyon yönetimi veri tabanından seçilen proje ve platforma ait sistem sürüm bilgilerini alabilecektir.
13. MKU, konfigürasyon yönetimi veri tabanından alınan sistem sürüm bilgileri içerisindeki yürürlükteki güncel sürüm bilgisini işaretleyecektir.
14. MKU, seçilen proje, platform ve sürüm bilgisine göre sistem ortamında çalışacak yazılım birimlerine ait isim ve sürüm bilgilerini "Yazılım Birimi Sürüm Envanteri" olarak kayıt altına alacaktır.
15. MKU, hedef ortama kurulması değerlendirilen yazılım biriminin aday sürümü ile seçilen sistem sürümünde tanımlı diğer yazılım birimi sürümlerini kullanarak Yazılım Birimi Sürüm Envanterini güncelleyecek ve kayıt altına alacaktır.
16. MKU, konfigürasyon yönetimi veri tabanından alınan verilerde eksiklik, erişim hatası veya format uyumsuzluğu tespit edilmesi durumunda veri alım sürecini hata durumu ile işaretleyecektir.
17. MKU, kaynak kodu deposu üzerinden Yazılım Birimi Sürüm Envanteri kapsamındaki yazılım birimlerine ait kaynak kodu, kurulum betikleri ve konfigürasyon dosyalarına erişerek sisteme aktaracaktır.
18. MKU, kaynak kodu deposundan alınan her dosya için dosya adı, dosya yolu, paket/versiyon bilgisi ve güncelleme zaman damgasını kayıt altına alacaktır.
19. MKU, kaynak kodu deposundan alınması zorunlu olan ve detayları kritik tasarım aşamasında belirlenecek dosyalardan herhangi birinin eksik olması durumunda veri alım sürecini "eksik veri" durumu ile raporlayacaktır.
20. MKU, kaynak kodu deposundan alınan dosyalarda erişim, yetki veya bütünlük hatası oluşması durumunda ilgili hatayı sergileyecek ve kayıt altına alacaktır.
21. MKU, alınan veya elle girilen tüm kaynak verileri için model inşası kapsamında gerekli alan varlığı kontrolü gerçekleştirecektir.
22. MKU, alan varlığı kontrolünden başarısız olan her veri için hata nedeni, kaynak adı, kaynak tipi, ilişkili proje/platform bilgisi ve hata zamanı bilgisini kayıt altına alacaktır.
23. MKU, doğrulama kontrollerinden geçen kaynak verileri model inşası sürecine aktarılmaya hazır hale getirecek ve Model Kurulum Verisi dosyası olarak kaydedecektir.

---

## 2. Senaryo Üreteci (SaaG-SUR)

**Tablo 3. SaaG-SUR İster Dağılımı**

| CSU | CSU Kimliği | İster Sayısı |
|---|---|---|
| Senaryo Üreteci | SUR | 7 |
| **Alt Toplam** | | **7** |

### 2.1 SUR: Senaryo Üreteci

1. SUR, saha kayıtlarına ihtiyaç duyulmaksızın, kullanıcı tarafından belirlenen senaryo girdilerine göre sentetik veri üretebilecektir.
2. SUR, detayları kritik tasarım aşamasında belirlenecek sistem genelindeki tüm simülasyon işlemlerinin veri kaynağı olarak işlev görecek ve simülasyon süreçlerinde kullanılacak sentetik verileri üretecektir.
3. SUR, kullanıcının senaryo üretimi için gerekli senaryo kapsamı, senaryo türü, zaman aralığı, veri yoğunluğu ve üretilecek veri türlerini belirleyebilmesini sağlayacaktır.
4. SUR, kullanıcı girdilerine göre yazılım birimlerinin kullandığı topic/mesaj veri şemasına, alan adlandırmasına ve değer aralığı kısıtlarına uygun eşdeğer yapıda sentetik veri üretebilecektir.
5. SUR, üretilen sentetik verileri senaryo adı, üretim zamanı, ilişkili proje bilgisi, platform bilgisi ve sistem sürüm numarası ile kayıt altına alacaktır.
6. SUR, sentetik verinin üretiminde kullanılan kullanıcı girdilerini izlenebilir şekilde kayıt altına alacaktır.
7. SUR, üretilen sentetik veriyi Analitik Veri Yöneticisi bileşenine aktarılmaya hazır hale getirecektir.

---

## 3. Telemetri Veri Yöneticisi (SaaG-TVY)

**Tablo 4. SaaG-TVY İster Dağılımı**

| CSU / Öğe | Kimlik | Tür | İster Sayısı |
|---|---|---|---|
| Telemetri Veri Yöneticisi | TVY | İşlevsel | 5 |
| Depolama Platform Ortamı | TVY-INF | Altyapı | 1 |
| **Alt Toplam** | | | **6** |

### 3.1 TVY: Telemetri Veri Yöneticisi

1. TVY, sistemin kurulu olduğu platformlardan sistem veri kayıt mekanizması ile alınan sistem veri kayıtlarını ve telemetri verilerini "Sistem Saha Kayıtları" olarak merkezi biçimde depolayacak ve yönetecektir.
2. TVY, kullanıcının sistem saha ortamından alınan telemetri ve sistem veri kayıtlarını kontrollü, izlenebilir şekilde yükleyebilmesini sağlayacak ve yüklenen kayıtları ilgili proje bilgisi, platform bilgisi ve sistem sürüm numarası ile ilişkilendirerek kaydedecektir.
3. TVY, yüklenen Sistem Saha Kayıtlarını kayıt kaynağı, yükleme zamanı, ilişkili proje, platform ve sistem sürüm bilgisiyle birlikte izlenebilir şekilde kayıt altına alacaktır.
4. TVY, kullanıcının mevcut Sistem Saha Kayıtlarını proje, platform, sistem sürümü, kayıt kaynağı veya yükleme zamanı ölçütlerine göre listeleyebilmesini, arayabilmesini ve seçebilmesini sağlayacaktır.
5. TVY, yükleme sırasında tespit edilen format uyumsuzluğu, bütünlük hatası veya eksik alan durumlarını raporlayacak ve kayıt altına alacaktır.

### 3.2 Altyapı ve Platform Kısıtları

1. **TVY-INF.1:** TVY, depolama donanımının disk kapasitesi ve donanım özellikleri kritik tasarım aşamasında belirlenecek bir depolama altyapısı üzerinde çalışacaktır.

---

## 4. Analitik Veri Yöneticisi (SaaG-AVY)

**Tablo 5. SaaG-AVY İster Dağılımı**

| CSU | CSU Kimliği | İster Sayısı |
|---|---|---|
| Analitik Veri Yöneticisi | AVY | 6 |
| **Alt Toplam** | | **6** |

### 4.1 AVY: Analitik Veri Yöneticisi

1. AVY, analiz, doğrulama ve simülasyon süreçlerinde kullanılacak Analitik Değerlendirme Verisinin kontrollü, izlenebilir, doğrulanabilir şekilde hazırlanmasını ve Çekirdek Sistem Modeline aktarılabilmesini sağlayacaktır.
2. AVY, Analitik Değerlendirme Verisinin hazırlanmasında kullanılacak Sistem Saha Kayıtlarını Telemetri Veri Yöneticisi bileşeninden alabilecektir.
3. AVY, Analitik Değerlendirme Verisini oluşturmak için gereken veriler olarak Senaryo Üretecinin ürettiği sentetik verileri alabilecektir.
4. AVY, Telemetri Veri Yöneticisinden temin edilen Sistem Saha Kayıtlarını veya Senaryo Üretecinden sağlanan sentetik verileri işleyerek uygun şekilde ilişkilendirecek ve detayları kritik tasarım aşamasında belirlenecek Analitik Değerlendirme Verisini üreterek Çekirdek Sistem Modeline iletecektir.
5. AVY, Sistem Saha Kayıtlarında format uyumsuzluğu veya okunamayan veri tespit edilmesi durumunu raporlayacak ve kayıt altına alacaktır.
6. AVY, Senaryo Üretecinin sağladığı sentetik verilerde format uyumsuzluğu, okunamayan veri veya eksik alan tespit edilmesi durumunu raporlayacak ve kayıt altına alacaktır.

---

## 5. Çekirdek Sistem Modeli (SaaG-CSM)

**Tablo 6. SaaG-CSM İster Dağılımı**

| CSU | CSU Kimliği | İster Sayısı |
|---|---|---|
| Çekirdek Sistem Modeli | CSM | 37 |
| **Alt Toplam** | | **37** |

### 5.1 CSM: Çekirdek Sistem Modeli

#### 5.1.1 Yapısal Çizge İnşası ve Yönetimi

1. CSM, Sayısal Sistem Modeli'nin oluşturulmasına esas Model Kurulum Verisini kullanarak sistemin yapısal ve ilişkisel temsilini düğüm-ilişki yapısında inşa edecek; statik analiz, doğrulama ve simülasyon süreçlerinde kullanılabilir hale getirecektir.
2. CSM, Model Kurulum Üreteci bileşeni tarafından üretilen Model Kurulum Verisini girdi olarak kabul edebilecektir.
3. CSM, Çekirdek Sistem Modeli'nin inşasından önce Model Kurulum Verisi üzerinde format, şema, bütünlük ve zorunlu alan kontrollerini gerçekleştirecektir.
4. CSM, kontrollerden başarıyla geçen Model Kurulum Verisini düğüm-ilişki tabanlı Çekirdek Sistem Modeline dönüştürecektir.
5. CSM, Çekirdek Sistem Modelini ilgili proje, platform ve sistem sürüm bilgisiyle ilişkilendirilmiş şekilde oluşturacaktır.
6. CSM, Model Kurulum Verisinde yer alan yapısal sistem varlıklarından Sistemi düğüm-ilişki yapısında düğüm olarak temsil edecektir.
7. CSM, Model Kurulum Verisinde yer alan yapısal sistem varlıklarından Yazılım Segmentini düğüm-ilişki yapısında düğüm olarak temsil edecektir.
8. CSM, Model Kurulum Verisinde yer alan yapısal sistem varlıklarından Yazılım Kırılım Öğesini (CSCI) düğüm-ilişki yapısında düğüm olarak temsil edecektir.
9. CSM, Model Kurulum Verisinde yer alan yapısal sistem varlıklarından Yazılım Komponentini (CSC) düğüm-ilişki yapısında düğüm olarak temsil edecektir.
10. CSM, Model Kurulum Verisinde yer alan yapısal sistem varlıklarından Yazılım Birimini (CSU) düğüm-ilişki yapısında düğüm olarak temsil edecektir.
11. CSM, Model Kurulum Verisinde yer alan yapısal sistem varlıklarından Rolü düğüm-ilişki yapısında düğüm olarak temsil edecektir.
12. CSM, Model Kurulum Verisinde yer alan yapısal sistem varlıklarından Topici düğüm-ilişki yapısında düğüm olarak temsil edecektir.
13. CSM, Model Kurulum Verisinde yer alan yapısal sistem varlıklarından Mesajı düğüm-ilişki yapısında düğüm olarak temsil edecektir.
14. CSM, Model Kurulum Verisinde yer alan yapısal sistem varlıklarından Operatör Konsolu ve İşlemci Birimlerini düğüm-ilişki yapısında düğüm olarak temsil edecektir.
15. CSM, Model Kurulum Verisinde yer alan yapısal sistem varlıklarından Ağ bileşenlerini düğüm-ilişki yapısında düğüm olarak temsil edecektir.
16. CSM, Model Kurulum Verisinde yer alan yapısal sistem varlıklarından Arakatman Servislerini düğüm-ilişki yapısında düğüm olarak temsil edecektir.
17. CSM, Model Kurulum Verisinde yer alan yapısal sistem varlıklarından Haberleşme Teknolojilerine ait Servisleri düğüm-ilişki yapısında düğüm olarak temsil edecektir.
18. CSM, yapısal sistem varlıkları arasındaki ilişki türlerinden "Operatör Konsolu ve İşlemci Birimlerinde Koşma" ilişkisini düğüm-ilişki yapısında ilişki olarak temsil edecektir.
19. CSM, yapısal sistem varlıkları arasındaki ilişki türlerinden "Arakatman ve Haberleşme Servislerini Kullanma" ilişkisini düğüm-ilişki yapısında ilişki olarak temsil edecektir.
20. CSM, yapısal sistem varlıkları arasındaki ilişki türlerinden "Veri yayımlama" ilişkisini düğüm-ilişki yapısında ilişki olarak temsil edecektir.
21. CSM, yapısal sistem varlıkları arasındaki ilişki türlerinden "Veri tüketme" ilişkisini düğüm-ilişki yapısında ilişki olarak temsil edecektir.
22. CSM, yapısal sistem varlıkları arasındaki ilişki türlerinden "Kütüphane veya yazılım birimine bağımlı olma" ilişkisini düğüm-ilişki yapısında ilişki olarak temsil edecektir.
23. CSM, yapısal sistem varlıkları arasındaki ilişki türlerinden "Yazılım biriminin role atanması" ilişkisini düğüm-ilişki yapısında ilişki olarak temsil edecektir.
24. CSM, sistemin yazılım birimlerine ait işlemci çekirdek tahsisini (CPU allocation), işletim sistemi ayarlarını ve çalışma-zamanı ortamı konfigürasyonlarını (JVM vb.) düğüm-ilişki yapısı üzerinde sorgulanabilir öznitelikler olarak temsil edecektir.
25. CSM, Çekirdek Sistem Modeli inşası sırasında tespit edilen eksik varlık ve geçersiz ilişki hatalarını raporlayacak ve kayıt altına alacaktır.
26. CSM, oluşturulan Çekirdek Sistem Modeli için kullanılan Model Kurulum Verisi dosyasını, model oluşturma zamanını, proje bilgisini, platform bilgisini, sistem sürüm numarasını ve model durumunu kayıt altına alacaktır.
27. CSM, Çekirdek Sistem Modelini Tasarım Doğrulama Motoru bileşeninin kullanımına sunacaktır.
28. CSM, Tasarım Doğrulama Motoru bileşeninin düğümlere, ilişkilere ve bunlarla ilişkili Analitik Değerlendirme Verisine erişebilmesini sağlayacaktır.
29. CSM, aynı Çekirdek Sistem Modeli üzerinde birden fazla kullanıcı oturumu tarafından eşzamanlı olarak gerçekleştirilen okuma/yazma işlemlerini, model bütünlüğünü ve sorgu sonuçlarının tutarlılığını bozmayacak şekilde yönetecektir.
30. CSM, üretim dağıtım hattındaki işlemler ile detayları kritik tasarım aşamasında belirlenecek sayıda kullanıcının analiz ve simülasyon işlemlerini eşzamanlı ve birbirini etkilemeyecek şekilde bağımsız olarak yürütecektir.
31. CSM, hedef ortama kurulması değerlendirilen yazılım biriminin aday sürümü ile hedef sistem sürümündeki diğer yazılım birimlerini kullanarak işleme özel yeni bir Çekirdek Sistem Modeli oluşturacaktır.

#### 5.1.2 Analitik Veri Bağlama

32. CSM, Analitik Değerlendirme Verisini Çekirdek Sistem Modeli içerisindeki ilgili sistem varlıkları ve aralarındaki bağlantılar ile eşleştirerek statik analiz, doğrulama ve simülasyon süreçlerinde kullanılabilir hale getirecektir.
33. CSM, Analitik Veri Yöneticisi bileşeni tarafından üretilen Analitik Değerlendirme Verisini girdi olarak kabul edebilecektir.
34. CSM, Analitik Değerlendirme Verisini ilgili proje, platform, sistem sürümü ve Çekirdek Sistem Modeli ile ilişkilendirecek; veri içeriğindeki kayıt, telemetri ve sentetik verileri ilgili düğüm ve ilişkilerle eşleştirerek düğüm-ilişki yapısına bağlayacaktır.
35. CSM, Analitik Değerlendirme Verisinin Telemetri Veri Yöneticisinden alınan verilerle mi yoksa Senaryo Üretecinin ürettiği sentetik verilerle mi üretildiği bilgisini koruyacaktır.
36. CSM, Analitik Değerlendirme Verisini Çekirdek Sistem Modelindeki düğüm ve ilişkileri değiştirmeksizin modele bağlayacak; Çekirdek Sistem Modeli verisi ile Analitik Değerlendirme Verisinin birbirinden ayrılabilir şekilde yönetilmesini sağlayacaktır.
37. CSM, Analitik Değerlendirme Verisinde karşılığı bulunamayan düğüm veya ilişki kayıtlarını raporlayacak ve kayıt altına alacaktır.

---

## 6. Tasarım Doğrulama Motoru (SaaG-TDM)

**Tablo 7. SaaG-TDM İster Dağılımı**

| CSU | CSU Kimliği | İster Sayısı |
|---|---|---|
| Tasarım Doğrulama Motoru | TDM | 78 |
| **Alt Toplam** | | **78** |

### 6.1 TDM: Tasarım Doğrulama Motoru

#### 6.1.1 Operasyonlar ve Görselleştirme

1. TDM, tasarım doğrulama, statik analiz ve değerlendirme operasyonlarını desteklemek amacıyla kullanıcının sistem bileşenleriyle doğrudan etkileşime girebilmesini sağlayacak ve bu işlemlerin sonuçlarını kullanıcıya sunacaktır.
2. TDM, Model Kurulum Üreteci, Senaryo Üreteci, Analitik Veri Yöneticisi ve Çekirdek Sistem Modeli bileşenleri ile etkileşim kurabilecektir.
3. TDM, sisteme erişmek isteyen kullanıcıların kullanıcı adı ve parola bilgilerini tanımlı bir LDAP dizin servisi üzerinden doğrulayacak ve yalnızca başarılı şekilde doğrulanan kullanıcıların yetkileri dahilinde sisteme erişimine izin verecektir.
4. TDM, kullanıcının üzerinde işlem yapılacak proje, platform ve sistem sürümünü seçebilmesini sağlayacak ve seçilen proje ile platform için yürürlükteki güncel sistem sürümünü belirgin şekilde sergileyecektir.
5. TDM, seçilen proje, platform ve sistem sürümüne ait Model Kurulum Verisi dosyalarını kullanıcıya listeleyecek ve kullanılacak dosyanın kullanıcı tarafından seçilebilmesini sağlayacaktır.
6. TDM, kullanıcının Model Kurulum Verisi üretim sürecini başlatabilmesini ve sürecin durumunu devam ediyor, başarılı veya başarısız durumlarından biri olarak izleyebilmesini sağlayacaktır.
7. TDM, kullanılan tüm veri kaynaklarının erişilebilirlik durumunu sürekli ve izlenebilir şekilde kullanıcıya sergileyecektir.
8. TDM, Model Kurulum Verisi üretimi sırasında tespit edilen eksik veri, erişim, yetki, format veya bütünlük hatalarını kullanıcıya sergileyecektir.
9. TDM, kullanıcının seçilen Model Kurulum Verisini kullanarak Çekirdek Sistem Modeli oluşturma sürecini başlatabilmesini ve işlem sonucunu başarılı veya başarısız olarak izleyebilmesini sağlayacaktır.
10. TDM, kullanıcının Analitik Değerlendirme Verisinin oluşturulmasında kullanılacak veri kaynağını Sistem Saha Kayıtları olarak seçebilmesini sağlayacaktır.
11. TDM, kullanıcının Analitik Değerlendirme Verisinin oluşturulmasında kullanılacak veri kaynağını Senaryo Üretecinin sağladığı sentetik veriler olarak seçebilmesini sağlayacaktır.
12. TDM, Analitik Değerlendirme Verisi kaynağı olarak Sistem Saha Kayıtlarının kullanılacağı durumda kullanıcının kullanılacak kayıtları seçebilmesini sağlayacaktır.
13. TDM, Analitik Değerlendirme Verisi kaynağı olarak sentetik verilerin kullanılacağı durumda kullanıcının senaryo kapsamı, senaryo türü, zaman aralığı, veri yoğunluğu ve üretilecek veri türlerine ilişkin girdileri belirleyebilmesini sağlayacaktır.
14. TDM, kullanıcının sentetik veri üretim sürecini başlatabilmesini, sürecin durumunu takip edebilmesini ve üretim sırasında oluşan hataları görüntüleyebilmesini sağlayacaktır.
15. TDM, kullanıcının Analitik Değerlendirme Verisi üretim sürecini başlatabilmesini, sürecin durumunu takip edebilmesini ve üretim sırasında oluşan hataları görüntüleyebilmesini sağlayacaktır.
16. TDM, Çekirdek Sistem Modeline bağlanan Analitik Değerlendirme Verisinin ilişkili olduğu proje, platform ve sistem sürüm bilgilerini kullanıcıya sergileyecek; veri içeriğindeki kayıt, telemetri ve sentetik verilerin düğüm ve ilişkilerle eşleşme durumunu raporlayacaktır.
17. TDM, kullanıcının Çekirdek Sistem Modelinden türetilmiş bir çalışma modeli üzerinde, yapısal bütünlüğü bozmadan düğüm ekleme/çıkarma, ilişki ekleme/çıkarma ve düğüm/ilişki özniteliklerini güncelleme gibi yapısal değişiklikler yapabilmesini sağlayacak ve güncellenen çalışma modeli üzerinde tasarım doğrulama ve analiz işlemlerinin yürütülmesine imkân tanıyacaktır.
18. TDM, detayları kritik tasarım aşamasında belirlenecek kural/metrikler doğrultusunda tasarım doğrulama ve analiz sonuçlarını "uygun" veya "uygun değil" olarak sınıflandıracaktır.
19. TDM, kullanıcının düğüm-ilişki yapısı üzerinde sistem varlığı veya ilişkisi arayabilmesini; sonuçları tür, proje, platform, sistem sürümü veya yazılım birimi bilgisine göre filtreleyebilmesini sağlayacaktır.
20. TDM, kullanıcının düğüm-ilişki yapısı üzerinde görsel yakınlaştırma, uzaklaştırma, kaydırma ve düğüm/ilişki seçimi ile öznitelik görüntüleme işlemlerini gerçekleştirebilmesini sağlayacaktır.
21. TDM, analiz sonuçlarında tespit edilen her bir bulguyu en az şu bilgilerle kullanıcıya sunacaktır: bulgu kimliği, bulgu türü, bulgu açıklaması, etkilenen sistem varlığı veya ilişkisi, ilgili doğrulama kuralı veya kabul kriteri, bulguyu destekleyen veri veya kanıt ve bulgunun bilgi, düşük, orta, yüksek veya kritik olarak ifade edilen önem derecesi.
22. TDM, aynı işlem kapsamında tespit edilen ilişkili bulgular arasındaki neden-sonuç bağıntısını kayıt altına alacak ve kullanıcıya sergileyecektir.
23. TDM, kullanıcının bulguları işlem türü, değerlendirme sonucu, bulgu türü, önem derecesi, proje, platform, sistem sürümü veya etkilenen düğümlere göre sıralayabilmesini ve filtreleyebilmesini sağlayacaktır.
24. TDM, bir tasarım doğrulama, analiz veya simülasyon işlemi sırasında oluşan hata nedenini, işlemin kesintiye uğradığı aşamayı ve hata zamanını kayıt altına alacaktır.
25. TDM, simülasyon işlemlerinde kullanılan senaryo adını, senaryo girdilerini, veri üretim zamanını ve ilişkili proje, platform ve sistem sürüm bilgisini kayıt altına alabilecektir.
26. TDM, tasarım doğrulama, analiz ve simülasyon sonuçlarını detayları kritik tasarım aşamasında belirlenecek dışa aktarılabilir bir dosya formatında özet veya detaylı sistem raporu olarak üretecek; raporların en az proje bilgisi, platform bilgisi, sistem sürüm bilgisi, kullanılan Çekirdek Sistem Modeli, kullanılan Analitik Değerlendirme Verisi ve veri kaynağı, işlem kimliği ve işlem türü, işlem başlangıç ve bitiş zamanı, değerlendirme sonucu, tespit edilen bulgular, etkilenen düğüm ve ilişkiler, önem dereceleri ve bulgulara ilişkin ek bilgileri içermesini sağlayacaktır.
27. TDM, kullanıcı arayüzleri üzerinden yapılan analiz taleplerini Yapı Otomasyon Araçları ve Komut Satırı Arayüzü (CLI) üzerinden de kabul edecek; sisteme erişen kullanıcılara ve otomasyon istemcilerine (örn. Jenkins) yürütülen işlemlerin durum bilgisini sunacak ve analiz işlemlerinin eşzamanlı ve birbirinden bağımsız olarak yürütülmesini sağlayacaktır.

#### 6.1.2 Yapısal Tasarım Doğrulama

28. TDM, Çekirdek Sistem Modeli üzerinde tasarım doğrulama işlemlerini gerçekleştirecektir.
29. TDM, Çekirdek Sistem Modelindeki düğüm ve ilişkileri değiştirmeksizin tasarım doğrulama işlemlerini yürütecektir.
30. TDM, Analitik Değerlendirme Verisi kullanmaksızın yalnızca Çekirdek Sistem Modeli üzerinden analiz yapabilecektir.
31. TDM, Çekirdek Sistem Modeli üzerinde sistem varlıkları arasındaki yapısal bağımlılıkların, haberleşme bağlantılarının ve çalışma-zamanı ortamı ilişkilerinin analizini gerçekleştirebilecektir.
32. TDM, Çekirdek Sistem Modeli üzerinde, topic veri iletimi Durability (kalıcılık) servis kalite parametrelerinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve uyumsuzlukları tespit edecektir.
33. TDM, Çekirdek Sistem Modeli üzerinde, topic veri iletimi Reliability (güvenilirlik) servis kalite parametrelerinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve uyumsuzlukları tespit edecektir.
34. TDM, Çekirdek Sistem Modeli üzerinde, topic veri iletimi Lifespan (yaşam süresi) servis kalite parametrelerinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve uyumsuzlukları tespit edecektir.
35. TDM, Çekirdek Sistem Modeli üzerinde, topic veri iletimi Transport Priority (iletim önceliği) servis kalite parametrelerinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve uyumsuzlukları tespit edecektir.
36. TDM, Çekirdek Sistem Modeli üzerinde topic veri yayımcısı ve veri tüketicisi eşleşmelerini doğrulayacak ve veri yayımcısı bulunmayan topici tespit edecektir.
37. TDM, Çekirdek Sistem Modeli üzerinde topic veri yayımcısı ve veri tüketicisi eşleşmelerini doğrulayacak ve veri tüketicisi bulunmayan topici tespit edecektir.
38. TDM, Çekirdek Sistem Modeli üzerinde topic veri yayımcısı ve veri tüketicisi eşleşmelerini doğrulayacak ve aynı isimle tanımlanmış fakat içerik tanımları birbirinden farklı olan topicleri tespit edecektir.
39. TDM, Çekirdek Sistem Modeli üzerinde, detayları kritik tasarım aşamasında belirlenecek haberleşme servisleri üzerinden yürütülen arakatman dışı haberleşmelerde kaynak, hedef, mesaj ve haberleşme yönü bilgilerinin karşılıklı tutarlılığını doğrulayacaktır.
40. TDM, Çekirdek Sistem Modeli üzerinde sistemin yazılım birimlerinin Operatör Konsolu ve İşlemci Birimlerine dağılımının, detayları kritik tasarım aşamasında belirlenecek yük dengeleme kurallarına uygunluğunu analiz edecektir.
41. TDM, Çekirdek Sistem Modeli üzerinde sistemin yazılım birimlerine yapılan işlemci çekirdek tahsisinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve bir İşlemci Biriminde tahsis edilen toplam çekirdek sayısının mevcut çekirdek kapasitesini aşması durumunu tespit edecektir.
42. TDM, Çekirdek Sistem Modeli üzerinde sistemin yazılım birimlerine yapılan işlemci çekirdek tahsisinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve aynı çekirdeklerin birden fazla uygulamaya çakışacak şekilde tahsis edilmesi durumunu tespit edecektir.
43. TDM, Çekirdek Sistem Modeli üzerinde sistemin yazılım birimlerine yapılan işlemci çekirdek tahsisinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve yüksek performansla çalışması gereken uygulamalara adanmış çekirdek tahsis edilmemesi durumunu tespit edecektir.
44. TDM, Çekirdek Sistem Modeli üzerinde işlemci/konsol birimlerinde çalışan işletim sistemi ayarlarının, detayları kritik tasarım aşamasında belirlenecek kurallara ve yapılan işlemci çekirdek tahsisine uygunluğunu denetleyecektir.
45. TDM, Çekirdek Sistem Modeli üzerinde sistemin yazılım birimlerinin çalışma-zamanı ortamı konfigürasyonlarında yer alan bellek tahsis parametrelerinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacaktır.
46. TDM, Çekirdek Sistem Modeli üzerinde işlemci çekirdek tahsisi, işletim sistemi ayarları ve çalışma-zamanı ortamı konfigürasyonları arasındaki tutarsızlıklardan kaynaklanabilecek kaynak çekişmesi ve darboğaz yaratabilecek durumları tespit edecektir.
47. TDM, Çekirdek Sistem Modeli üzerinde sistemin yazılım birimleri arasındaki döngüsel bağımlılıkları tespit edecektir.
48. TDM, Çekirdek Sistem Modeli üzerinde, modeldeki düğümler arasında kopuk, eksik, geçersiz veya eşleşmeyen yapısal ilişkileri tespit edecektir.
49. TDM, Çekirdek Sistem Modeli üzerinde, detayları kritik tasarım aşamasında belirlenecek mimari kurallara aykırı tasarım örüntülerini tespit edecektir.

#### 6.1.3 Davranışsal Simülasyon ve Analiz

50. TDM, Çekirdek Sistem Modeli üzerinde statik analiz işlemlerini gerçekleştirecektir.
51. TDM, Çekirdek Sistem Modelindeki düğüm ve ilişkileri değiştirmeksizin analiz işlemlerini yürütecektir.
52. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak analiz yapabilecektir.
53. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak düğümler arasındaki mesaj akış yönünü, mesaj adedini, veri hacmini ve mesajlaşma sıklığını analiz edecektir.
54. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak bir düğüm veya ilişkinin devre dışı kalmasının Çekirdek Sistem Modeli üzerindeki etkilerini değerlendirebilecektir.
55. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak tasarım-zamanı trafik analizi yapabilecek; simülasyon dahilinde oluşturulan yük koşullarının sistem varlıkları ve ilişkiler üzerindeki etkileri kapsamında Topic/Mesaj yoğunluğunun artması durumunu değerlendirebilecektir.
56. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak tasarım-zamanı trafik analizi yapabilecek; simülasyon dahilinde oluşturulan yük koşullarının sistem varlıkları ve ilişkiler üzerindeki etkileri kapsamında Topic/Mesaj yayımlama veya tüketme davranışının değişmesi durumunu değerlendirebilecektir.
57. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak simülasyon dahilinde oluşturulan arıza, yük, haberleşme kesintisi veya bant genişliği daralması durumlarının bağımlı düğümlere yayılımını belirleyecek; doğrudan veya dolaylı etkilenen düğüm/ilişkileri ve etkinin izlediği yayılım yolunu tespit edecektir.
58. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak gerçekleştirilecek simülasyon sonucunda en yüksek kaynak kullanımına sahip veya en yoğun mesajlaşan sistem varlıklarını belirleyecek ve bunları kullanıcıya özet değerlendirme göstergeleri olarak sunacaktır.
59. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak analiz yapabilecektir.
60. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde operasyonel durum ve sağlık durumu konularında analiz yapabilecektir.
61. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde işlemci, bellek, depolama ve ağ kullanım değerleri konularında analiz yapabilecektir.
62. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde hata, uyarı, yeniden başlama ve zaman aşımı bilgileri konularında analiz yapabilecektir.
63. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde mesaj akış yönü, mesaj adedi, veri hacmi ve mesajlaşma sıklığı konularında analiz yapabilecektir.
64. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde haberleşme gecikmesi, mesaj kaybı ve başarılı iletim oranları konularında analiz yapabilecektir.
65. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde topic yayımlama ve tüketme aktiviteleri konularında analiz yapabilecektir.
66. TDM, Model Kurulum Verisinde yer alan düğüm ve ilişkileri Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde gözlemlenen çalışma-zamanı sistem varlıkları ve ilişkileri ile karşılaştıracak; Model Kurulum Verisinde yer alan ancak çalışma-zamanı verisinde gözlemlenmeyen sistem varlığı ve ilişkilerini tespit edecektir.
67. TDM, Model Kurulum Verisinde yer alan düğüm ve ilişkileri Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde gözlemlenen çalışma-zamanı sistem varlıkları ve ilişkileri ile karşılaştıracak; Model Kurulum Verisinde yer almayan ancak çalışma-zamanı verisinde gözlemlenen sistem varlığı ve ilişkilerini tespit edecektir.
68. TDM, Model Kurulum Verisinde yer alan düğüm ve ilişkileri Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde gözlemlenen çalışma-zamanı sistem varlıkları ve ilişkileri ile karşılaştıracak; Model Kurulum Verisi ile çalışma-zamanı verisi arasında uyumsuzluk gösteren sistem varlığı ve ilişkilerini tespit edecektir.
69. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde yer alan düğüm ve ilişkilerle ilişkili olay kayıtlarını analiz edecektir.
70. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak yapılacak analiz sonucunda en yüksek kaynak kullanımına sahip veya en yoğun mesajlaşan sistem varlıklarını belirleyecek ve bunları özet değerlendirme göstergeleri olarak kullanıcıya sunacaktır.

#### 6.1.4 Kurulum Uygunluk Değerlendirmesi

71. TDM, Çekirdek Sistem Modeli üzerinde, aday yazılım birimleri için kurulum uygunluk değerlendirmesi şeklinde değerlendirme işlemlerini gerçekleştirecektir.
72. TDM, bir yazılım biriminin hedef ortama kurulum uygunluğunu yapısal ve mimari uygunluk değerlendirme başlığı altında analiz edecektir.
73. TDM, bir yazılım biriminin hedef ortama kurulum uygunluğunu arayüz, topic ve haberleşme uygunluğu değerlendirme başlığı altında analiz edecektir.
74. TDM, bir yazılım biriminin hedef ortama kurulum uygunluğunu bağımlılık ve entegrasyon uygunluğu değerlendirme başlığı altında analiz edecektir.
75. TDM, bir yazılım biriminin hedef ortama kurulum uygunluğunu kaynak ve performans yeterliliği değerlendirme başlığı altında analiz edecektir.
76. TDM, kurulum uygunluk değerlendirmesinde kullanılan her bir kontrol kuralını kural kimliği, değerlendirme başlığı, önem derecesi, ağırlık değeri, kabul kriteri ve bloke edici olma durumu ile tanımlayacak; kural sonuçlarına ait uygunluk kategorilerini ve puanlama yöntemini detayları kritik tasarım aşamasında belirlenecek şekilde sınıflandıracak ve puanlayacaktır.
77. TDM, kritik önem derecesine sahip bir bulgunun veya değerlendirme profilinde bloke edici olarak tanımlanmış bir kontrol kuralı ihlalinin tespit edilmesi durumunda genel uygunluk puanından bağımsız olarak hedef ortama kurulum sonucunu "uygun değil" olarak belirleyecek ve üretim dağıtım hattının devam etmesini engelleyecek karar bilgisini otomasyon istemcisine iletecektir.
78. TDM, üretim dağıtım hattı kapsamında bir veya birden fazla yazılım birimi için başlatılan kurulum uygunluk değerlendirmelerini birbirinden bağımsız işlem kimlikleriyle yürütecek; her yazılım birimi için ayrı uygunluk puanı, skor sınıfı, bloke edici bulgular ve kurulum kararının yanı sıra toplu işlem sonucunu makine tarafından işlenebilir biçimde otomasyon istemcisine sunacaktır.

---

## 7. Sistem Kabiliyeti Dağılımı ve İster İzlenebilirliği

Bu bölüm, sistem seviyesi temel kabiliyet isterleri (CSCI/CSC seviyesi) ile Yazılım Birimi (CSU) işlevsel isterleri arasındaki iki yönlü izlenebilirliği ve dağılımı ortaya koyar.

**İlişki türü açıklamaları:**
- **Doğrudan**: Temel bir sistem kabiliyet isterinin ayrıştırılmadan tek bir CSU işlevsel isterine doğrudan atanması.
- **Bölünmüş**: Bileşik bir sistem kabiliyet isterinin birden fazla bağımsız ve test edilebilir CSU işlevsel isterine ayrıştırılması.
- **Birleşik**: Sistem geneline veya bileşen misyonuna yönelik bir kabiliyet isterinin birden fazla CSU'nun eşgüdümlü işlevsel isterleriyle karşılanması.
- **Altyapı**: Çalışma-zamanı ortamına veya fiziksel platform donanımına tahsis edilmiş işlevsel olmayan sistem kısıtı.

### SaaG-MKU

| SRS İster No | CSU | Temel Sistem İster No | İlişki |
|---|---|---|---|
| MKU.1 | MKU | SSS-MKV.1 | Doğrudan (görev tanımı) |
| MKU.2 | MKU | SSS-MKV.2 | Bölünmüş |
| MKU.3 | MKU | SSS-MKV.2 | Bölünmüş |
| MKU.4 | MKU | SSS-MKV.2 | Bölünmüş |
| MKU.5 | MKU | SSS-MKV.2 | Bölünmüş |
| MKU.6 | MKU | SSS-MKV.3 | Bölünmüş |
| MKU.7 | MKU | SSS-MKV.3 | Bölünmüş |
| MKU.8 | MKU | SSS-MKV.4 | Doğrudan |
| MKU.9 | MKU | SSS-MKV.5 | Doğrudan |
| MKU.10 | MKU | SSS-MKV.6 | Doğrudan |
| MKU.11 | MKU | SSS-MKV.7 | Doğrudan |
| MKU.12 | MKU | SSS-MKV.8 | Doğrudan |
| MKU.13 | MKU | SSS-MKV.9 | Doğrudan |
| MKU.14 | MKU | SSS-MKV.10 | Doğrudan |
| MKU.15 | MKU | SSS-MKV.11 | Doğrudan |
| MKU.16 | MKU | SSS-MKV.12 | Doğrudan |
| MKU.17 | MKU | SSS-MKV.13 | Doğrudan |
| MKU.18 | MKU | SSS-MKV.14 | Doğrudan |
| MKU.19 | MKU | SSS-MKV.15 | Doğrudan |
| MKU.20 | MKU | SSS-MKV.16 | Doğrudan |
| MKU.21 | MKU | SSS-MKV.17 | Doğrudan |
| MKU.22 | MKU | SSS-MKV.18 | Doğrudan |
| MKU.23 | MKU | SSS-MKV.19 | Doğrudan |

### SaaG-SUR

| SRS İster No | CSU | Temel Sistem İster No | İlişki |
|---|---|---|---|
| SUR.1 | SUR | SSS-SUR.1 | Doğrudan (görev tanımı) |
| SUR.2 | SUR | SSS-SUR.2 | Doğrudan |
| SUR.3 | SUR | SSS-SUR.3 | Doğrudan |
| SUR.4 | SUR | SSS-SUR.4 | Doğrudan |
| SUR.5 | SUR | SSS-SUR.5 | Doğrudan |
| SUR.6 | SUR | SSS-SUR.6 | Doğrudan |
| SUR.7 | SUR | SSS-SUR.7 | Doğrudan |

### SaaG-TVY

| SRS İster No | CSU | Temel Sistem İster No | İlişki |
|---|---|---|---|
| TVY.1 | TVY | SSS-SKV.1 | Doğrudan (görev tanımı) |
| TVY.2 | TVY | SSS-SKV.2 | Doğrudan |
| TVY.3 | TVY | SSS-SKV.3 | Doğrudan |
| TVY.4 | TVY | SSS-SKV.4 | Doğrudan |
| TVY.5 | TVY | SSS-SKV.5 | Doğrudan |
| TVY-INF.1 | TVY-INF | SSS-SKV.6 | Altyapı (platform depolama) |

### SaaG-AVY

| SRS İster No | CSU | Temel Sistem İster No | İlişki |
|---|---|---|---|
| AVY.1 | AVY | SSS-AVH.1 | Doğrudan (görev tanımı) |
| AVY.2 | AVY | SSS-AVH.2 | Doğrudan |
| AVY.3 | AVY | SSS-AVH.3 | Doğrudan |
| AVY.4 | AVY | SSS-AVH.4 | Doğrudan |
| AVY.5 | AVY | SSS-AVH.5 | Doğrudan |
| AVY.6 | AVY | SSS-AVH.6 | Doğrudan |

### SaaG-CSM

| SRS İster No | CSU | Temel Sistem İster No | İlişki |
|---|---|---|---|
| CSM.1 | CSM | SSS-CSM.1 | Birleşik |
| CSM.2 | CSM | SSS-CSM.2 | Doğrudan |
| CSM.3 | CSM | SSS-CSM.3 | Doğrudan |
| CSM.4 | CSM | SSS-CSM.4 | Doğrudan |
| CSM.5 | CSM | SSS-CSM.5 | Doğrudan |
| CSM.6 | CSM | SSS-CSM.6 | Bölünmüş |
| CSM.7 | CSM | SSS-CSM.6 | Bölünmüş |
| CSM.8 | CSM | SSS-CSM.6 | Bölünmüş |
| CSM.9 | CSM | SSS-CSM.6 | Bölünmüş |
| CSM.10 | CSM | SSS-CSM.6 | Bölünmüş |
| CSM.11 | CSM | SSS-CSM.6 | Bölünmüş |
| CSM.12 | CSM | SSS-CSM.6 | Bölünmüş |
| CSM.13 | CSM | SSS-CSM.6 | Bölünmüş |
| CSM.14 | CSM | SSS-CSM.6 | Bölünmüş |
| CSM.15 | CSM | SSS-CSM.6 | Bölünmüş |
| CSM.16 | CSM | SSS-CSM.6 | Bölünmüş |
| CSM.17 | CSM | SSS-CSM.6 | Bölünmüş |
| CSM.18 | CSM | SSS-CSM.7 | Bölünmüş |
| CSM.19 | CSM | SSS-CSM.7 | Bölünmüş |
| CSM.20 | CSM | SSS-CSM.7 | Bölünmüş |
| CSM.21 | CSM | SSS-CSM.7 | Bölünmüş |
| CSM.22 | CSM | SSS-CSM.7 | Bölünmüş |
| CSM.23 | CSM | SSS-CSM.7 | Bölünmüş |
| CSM.24 | CSM | SSS-CSM.8 | Doğrudan |
| CSM.25 | CSM | SSS-CSM.9 | Doğrudan |
| CSM.26 | CSM | SSS-CSM.15 | Doğrudan |
| CSM.27 | CSM | SSS-CSM.16 | Doğrudan |
| CSM.28 | CSM | SSS-CSM.17 | Doğrudan |
| CSM.29 | CSM | SSS-CSM.18 | Doğrudan |
| CSM.30 | CSM | SSS-CSM.19 | Doğrudan |
| CSM.31 | CSM | SSS-CSM.20 | Doğrudan |
| CSM.32 | CSM | SSS-CSM.1 | Birleşik |
| CSM.33 | CSM | SSS-CSM.10 | Doğrudan |
| CSM.34 | CSM | SSS-CSM.11 | Doğrudan |
| CSM.35 | CSM | SSS-CSM.12 | Doğrudan |
| CSM.36 | CSM | SSS-CSM.13 | Doğrudan |
| CSM.37 | CSM | SSS-CSM.14 | Doğrudan |

### SaaG-TDM

| SRS İster No | CSU | Temel Sistem İster No | İlişki |
|---|---|---|---|
| TDM.1 | TDM | SSS-DAD.1 | Birleşik |
| TDM.2 | TDM | SSS-DAD.2 | Doğrudan |
| TDM.3 | TDM | SSS-DAD.3 | Doğrudan |
| TDM.4 | TDM | SSS-DAD.4 | Doğrudan |
| TDM.5 | TDM | SSS-DAD.5 | Doğrudan |
| TDM.6 | TDM | SSS-DAD.6 | Doğrudan |
| TDM.7 | TDM | SSS-DAD.7 | Doğrudan |
| TDM.8 | TDM | SSS-DAD.8 | Doğrudan |
| TDM.9 | TDM | SSS-DAD.9 | Doğrudan |
| TDM.10 | TDM | SSS-DAD.10 | Bölünmüş |
| TDM.11 | TDM | SSS-DAD.10 | Bölünmüş |
| TDM.12 | TDM | SSS-DAD.11 | Doğrudan |
| TDM.13 | TDM | SSS-DAD.12 | Doğrudan |
| TDM.14 | TDM | SSS-DAD.13 | Doğrudan |
| TDM.15 | TDM | SSS-DAD.14 | Doğrudan |
| TDM.16 | TDM | SSS-DAD.16 | Doğrudan |
| TDM.17 | TDM | SSS-DAD.17 | Doğrudan |
| TDM.18 | TDM | SSS-DAD.42 | Doğrudan |
| TDM.19 | TDM | SSS-DAD.43 | Bölünmüş |
| TDM.20 | TDM | SSS-DAD.43 | Bölünmüş |
| TDM.21 | TDM | SSS-DAD.44 | Doğrudan |
| TDM.22 | TDM | SSS-DAD.45 | Doğrudan |
| TDM.23 | TDM | SSS-DAD.46 | Doğrudan |
| TDM.24 | TDM | SSS-DAD.47 | Doğrudan |
| TDM.25 | TDM | SSS-DAD.48 | Doğrudan |
| TDM.26 | TDM | SSS-DAD.49 | Doğrudan |
| TDM.27 | TDM | SSS-DAD.50 | Doğrudan |
| TDM.28 | TDM | SSS-DAD.1 | Birleşik |
| TDM.29 | TDM | SSS-DAD.15 | Birleşik |
| TDM.30 | TDM | SSS-DAD.18 | Doğrudan |
| TDM.31 | TDM | SSS-DAD.19 | Doğrudan |
| TDM.32 | TDM | SSS-DAD.20 | Bölünmüş |
| TDM.33 | TDM | SSS-DAD.20 | Bölünmüş |
| TDM.34 | TDM | SSS-DAD.20 | Bölünmüş |
| TDM.35 | TDM | SSS-DAD.20 | Bölünmüş |
| TDM.36 | TDM | SSS-DAD.21 | Bölünmüş |
| TDM.37 | TDM | SSS-DAD.21 | Bölünmüş |
| TDM.38 | TDM | SSS-DAD.21 | Bölünmüş |
| TDM.39 | TDM | SSS-DAD.22 | Doğrudan |
| TDM.40 | TDM | SSS-DAD.23 | Doğrudan |
| TDM.41 | TDM | SSS-DAD.24 | Bölünmüş |
| TDM.42 | TDM | SSS-DAD.24 | Bölünmüş |
| TDM.43 | TDM | SSS-DAD.24 | Bölünmüş |
| TDM.44 | TDM | SSS-DAD.25 | Doğrudan |
| TDM.45 | TDM | SSS-DAD.26 | Doğrudan |
| TDM.46 | TDM | SSS-DAD.27 | Doğrudan |
| TDM.47 | TDM | SSS-DAD.28 | Doğrudan |
| TDM.48 | TDM | SSS-DAD.29 | Doğrudan |
| TDM.49 | TDM | SSS-DAD.30 | Doğrudan |
| TDM.50 | TDM | SSS-DAD.1 | Birleşik |
| TDM.51 | TDM | SSS-DAD.15 | Birleşik |
| TDM.52 | TDM | SSS-DAD.31 | Doğrudan |
| TDM.53 | TDM | SSS-DAD.32 | Doğrudan |
| TDM.54 | TDM | SSS-DAD.33 | Doğrudan |
| TDM.55 | TDM | SSS-DAD.34 | Bölünmüş |
| TDM.56 | TDM | SSS-DAD.34 | Bölünmüş |
| TDM.57 | TDM | SSS-DAD.35 | Doğrudan |
| TDM.58 | TDM | SSS-DAD.36 | Doğrudan |
| TDM.59 | TDM | SSS-DAD.37 | Doğrudan |
| TDM.60 | TDM | SSS-DAD.38 | Bölünmüş |
| TDM.61 | TDM | SSS-DAD.38 | Bölünmüş |
| TDM.62 | TDM | SSS-DAD.38 | Bölünmüş |
| TDM.63 | TDM | SSS-DAD.38 | Bölünmüş |
| TDM.64 | TDM | SSS-DAD.38 | Bölünmüş |
| TDM.65 | TDM | SSS-DAD.38 | Bölünmüş |
| TDM.66 | TDM | SSS-DAD.39 | Bölünmüş |
| TDM.67 | TDM | SSS-DAD.39 | Bölünmüş |
| TDM.68 | TDM | SSS-DAD.39 | Bölünmüş |
| TDM.69 | TDM | SSS-DAD.40 | Doğrudan |
| TDM.70 | TDM | SSS-DAD.41 | Doğrudan |
| TDM.71 | TDM | SSS-DAD.1 | Birleşik |
| TDM.72 | TDM | SSS-DAD.51 | Bölünmüş |
| TDM.73 | TDM | SSS-DAD.51 | Bölünmüş |
| TDM.74 | TDM | SSS-DAD.51 | Bölünmüş |
| TDM.75 | TDM | SSS-DAD.51 | Bölünmüş |
| TDM.76 | TDM | SSS-DAD.52 | Doğrudan |
| TDM.77 | TDM | SSS-DAD.53 | Doğrudan |
| TDM.78 | TDM | SSS-DAD.54 | Doğrudan |

**Kapsam kontrolü:** 112 temel sistem kabiliyetinin tamamı yukarıda en az bir kez yer almaktadır (111'i işlevsel CSU isteri olarak, 1'i — SSS-SKV.6 / TVY-INF.1 — platform altyapı kısıtı olarak). Toplam SRS işlevsel isteri sayısı: **156**; altyapı kısıtı sayısı: **1**; toplam yönetilen ister: **157**.
