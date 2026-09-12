# Yazılım Gereksinimleri Şartnamesi (SRS): System as a Graph (SaaG)

**Tanım:** System as a Graph (SaaG) Sayısal Sistem Modeli, mimari dijital ikiz yaklaşımıyla geliştirilmiş, sistem uygulamalarını fiilen çalıştırmaksızın, sistemin yapısal ve ilişkisel mimarisini düğüm-ilişki temsiliyle modelleyen statik bir sayısal sistem modelidir. Bu modelde yazılım birimleri, arakatman ve haberleşme servisleri, işlemci/konsol birimleri, topic ve mesaj gibi sistem varlıkları düğüm; aralarındaki bağımlılık, yayımlama ve tüketme bağıntıları ise ilişki olarak temsil edilir. Modelin davranışsal analizlere imkân tanıyan boyutu, bileşenlerin koşumuyla değil; saha kayıtlarından veya senaryo üretecinden türetilen Analitik Değerlendirme Verisinin bu model üzerine bindirilmesiyle sağlanır.

SaaG, Yazılım Kırılım Öğesidir (CSCI). Bu Yazılım Gereksinimleri Şartnamesi (SRS), Yazılım Komponentleri (CSC) ile Yazılım Birimleri (CSU) arasında birebir (1:1) bir eşleme kurarak sistemi altı CSC ve altı CSU'ya ayrıştırır. Her işlevsel ister tam olarak bir CSU'ya kapsamlandırılmış olup sisteme ait altyapı kısıtları da resmi olarak dokümante edilmiştir.

**Amaç:** Modelin birincil amacı mimari doğrulamadır. Bu kapsamda yapısal/döngüsel bağımlılıklar, yayımcı/tüketici eşleşmeleri, topic servis kalite parametrelerinin (QoS) uygunluğu, sistemde yer alan donanımların kapasite uygunluğu (CPU çekirdek adedi, RAM boyutu, ağ bant genişliği vb.) ve mimari kurallara aykırı tasarım örüntüleri tasarım aşamasında statik olarak denetlenir. Mimari doğrulama, tasarımda öngörülen mimari ile saha verisinde gözlemlenen çalışma-zamanı yapısı arasındaki sapmaların (architectural drift) tespitini de kapsar. Mimari doğrulamanın yanı sıra model, kurgusal senaryo analizlerine olanak tanır; kullanıcı, yapısal bütünlüğü bozmadan düğüm/ilişki ekleyip çıkararak ya da öznitelikleri değiştirerek deneysel tasarım kurguları oluşturabilir. Bu kurgusal senaryolarda bir varlığın devre dışı kalması, mesaj yoğunluğunun artması veya bant genişliğinin daralması gibi durumların bağımlı varlıklara yayılımı ve mimari üzerindeki etkileri analitik olarak değerlendirilir. Ayrıca model, yazılım birimlerinin hedef ortama kurulum uygunluğunu canlıya alma işlem hattında (pipeline) otomatik olarak değerlendiren bir mekanizma sunar. Böylelikle Sayısal Sistem Modeli, henüz yazılım birimlerinin hedef ortama kurulumları yapılmadan tasarım kararlarının ve değişikliklerinin mimari sonuçlarını öngörmeye yönelik, tekrarlanabilir bir doğrulama ortamı sağlar.

**Tablo 1. SRS İster Dağılımı**

| No | Bileşen | Kısaltma | CSU Sayısı | CSU Kimliği | İster Sayısı |
|---|---|---|---|---|---|
| 1 | Model Veri Üreteci | SaaG-MVU | 1 | MVU | 23 |
| 2 | Senaryo Üreteci | SaaG-SUR | 1 | SUR | 7 |
| 3 | Saha Veri Yöneticisi | SaaG-SVY | 1 | SVY | 5 (+ 1 Altyapı) |
| 4 | Analitik Veri Yöneticisi | SaaG-AVY | 1 | AVY | 6 |
| 5 | Sistem Model Yöneticisi | SaaG-SMY | 1 | SMY | 37 |
| 6 | Tasarım Doğrulama Motoru | SaaG-TDM | 1 | TDM | 78 |
| **TOPLAM** | | | **6** | | **156 (+ 1 Altyapı)** |

Her bileşenin CSU başına ister dağılım tabloları, aşağıda ilgili bileşenin kendi bölümünde yer almaktadır.

---

## 1. Model Veri Üreteci (SaaG-MVU)

**Tablo 2. SaaG-MVU İster Dağılımı**

| CSU | CSU Kimliği | İster Sayısı |
|---|---|---|
| Model Veri Üreteci | MVU | 23 |
| **Alt Toplam** | | **23** |

### 1.1 MVU: Model Veri Üreteci

1. MVU, Sayısal Sistem Modeli'nin oluşturulmasına esas Model Verisinin kontrollü, izlenebilir, doğrulanabilir şekilde üretilmesini ve model inşası süreçlerine aktarılabilmesini sağlayacaktır.
2. MVU, Model Verisi üretimi maksadıyla dış veri kaynağı olarak sistem konfigürasyon yönetimi veri tabanına erişim sağlayabilecek ve bu kaynaktan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir.
3. MVU, Model Verisi üretimi maksadıyla dış veri kaynağı olarak sistem yazılım birimleri ve kurulum betikleri kaynak kodu deposuna erişim sağlayabilecek ve bu kaynaktan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir.
4. MVU, Model Verisi üretimi maksadıyla dış veri kaynağı olarak Sistem Yazılım Birimleri Paket Deposuna erişim sağlayabilecek ve bu kaynaktan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir.
5. MVU, Model Verisi üretimi maksadıyla dış veri kaynağı olarak Sistem Ağ Topolojisi Veri Kaynağına erişim sağlayabilecek ve bu kaynaktan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir.
6. MVU, sistem ağ topolojisi verisini, detayları kritik tasarım aşamasında belirlenecek dış bir veri kaynağından (dosya, veri tabanı vb.) otomatik olarak alabilecektir.
7. MVU, sistem ağ topolojisi verisini kullanıcının ağ topolojisi parametrelerini manuel olarak girmesi yoluyla alabilecektir.
8. MVU, her veri kaynağı için kaynak tipi, kaynak adı, erişim yöntemi, bağlantı adresi ve bağlantı için gerekli kullanıcı bilgilerini kullanıcı tarafından tanımlanabilir ve kaydedilebilir ayar bilgisi olarak yönetecektir.
9. MVU, veri alım işlemlerini proje bilgisi, platform bilgisi ve sistem sürüm numarası ile ilişkilendirilmiş şekilde yürütecektir.
10. MVU, konfigürasyon yönetimi veri tabanından mevcut proje bilgilerini alabilecektir.
11. MVU, konfigürasyon yönetimi veri tabanından seçilen projeye ait platform bilgilerini alabilecektir.
12. MVU, konfigürasyon yönetimi veri tabanından seçilen proje ve platforma ait sistem sürüm bilgilerini alabilecektir.
13. MVU, konfigürasyon yönetimi veri tabanından alınan sistem sürüm bilgileri içerisindeki yürürlükteki güncel sürüm bilgisini işaretleyecektir.
14. MVU, seçilen proje, platform ve sürüm bilgisine göre sistem ortamında çalışacak yazılım birimlerine ait isim ve sürüm bilgilerini "Yazılım Birimi Sürüm Envanteri" olarak kayıt altına alacaktır.
15. MVU, hedef ortama kurulması değerlendirilen yazılım biriminin aday sürümü ile seçilen sistem sürümünde tanımlı diğer yazılım birimi sürümlerini kullanarak Yazılım Birimi Sürüm Envanterini güncelleyecek ve kayıt altına alacaktır.
16. MVU, konfigürasyon yönetimi veri tabanından alınan verilerde eksiklik, erişim hatası veya format uyumsuzluğu tespit edilmesi durumunda veri alım sürecini hata durumu ile işaretleyecektir.
17. MVU, kaynak kodu deposu üzerinden Yazılım Birimi Sürüm Envanteri kapsamındaki yazılım birimlerine ait kaynak kodu, kurulum betikleri ve konfigürasyon dosyalarına erişerek sisteme aktaracaktır.
18. MVU, kaynak kodu deposundan alınan her dosya için dosya adı, dosya yolu, paket/versiyon bilgisi ve güncelleme zaman damgasını kayıt altına alacaktır.
19. MVU, kaynak kodu deposundan alınması zorunlu olan ve detayları kritik tasarım aşamasında belirlenecek dosyalardan herhangi birinin eksik olması durumunda veri alım sürecini "eksik veri" durumu ile raporlayacaktır.
20. MVU, kaynak kodu deposundan alınan dosyalarda erişim, yetki veya bütünlük hatası oluşması durumunda ilgili hatayı sergileyecek ve kayıt altına alacaktır.
21. MVU, alınan veya elle girilen tüm kaynak verileri için model inşası kapsamında gerekli alan varlığı kontrolü gerçekleştirecektir.
22. MVU, alan varlığı kontrolünden başarısız olan her veri için hata nedeni, kaynak adı, kaynak tipi, ilişkili proje/platform bilgisi ve hata zamanı bilgisini kayıt altına alacaktır.
23. MVU, doğrulama kontrollerinden geçen kaynak verileri model inşası sürecine aktarılmaya hazır hale getirecek ve Model Verisi dosyası olarak kaydedecektir.

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

## 3. Saha Veri Yöneticisi (SaaG-SVY)

**Tablo 4. SaaG-SVY İster Dağılımı**

| CSU / Öğe | Kimlik | Tür | İster Sayısı |
|---|---|---|---|
| Saha Veri Yöneticisi | SVY | İşlevsel | 5 |
| Depolama Platform Ortamı | SVY-INF | Altyapı | 1 |
| **Alt Toplam** | | | **6** |

### 3.1 SVY: Saha Veri Yöneticisi

1. SVY, sistemin kurulu olduğu platformlardan sistem veri kayıt mekanizması ile alınan sistem veri kayıtlarını ve telemetri verilerini "Sistem Saha Kayıtları" olarak merkezi biçimde depolayacak ve yönetecektir.
2. SVY, kullanıcının sistem saha ortamından alınan telemetri ve sistem veri kayıtlarını kontrollü, izlenebilir şekilde yükleyebilmesini sağlayacak ve yüklenen kayıtları ilgili proje bilgisi, platform bilgisi ve sistem sürüm numarası ile ilişkilendirerek kaydedecektir.
3. SVY, yüklenen Sistem Saha Kayıtlarını kayıt kaynağı, yükleme zamanı, ilişkili proje, platform ve sistem sürüm bilgisiyle birlikte izlenebilir şekilde kayıt altına alacaktır.
4. SVY, kullanıcının mevcut Sistem Saha Kayıtlarını proje, platform, sistem sürümü, kayıt kaynağı veya yükleme zamanı ölçütlerine göre listeleyebilmesini, arayabilmesini ve seçebilmesini sağlayacaktır.
5. SVY, yükleme sırasında tespit edilen format uyumsuzluğu, bütünlük hatası veya eksik alan durumlarını raporlayacak ve kayıt altına alacaktır.

### 3.2 Altyapı ve Platform Kısıtları

1. **SVY-INF.1:** SVY, depolama donanımının disk kapasitesi ve donanım özellikleri kritik tasarım aşamasında belirlenecek bir depolama altyapısı üzerinde çalışacaktır.

---

## 4. Analitik Veri Yöneticisi (SaaG-AVY)

**Tablo 5. SaaG-AVY İster Dağılımı**

| CSU | CSU Kimliği | İster Sayısı |
|---|---|---|
| Analitik Veri Yöneticisi | AVY | 6 |
| **Alt Toplam** | | **6** |

### 4.1 AVY: Analitik Veri Yöneticisi

1. AVY, analiz, doğrulama ve simülasyon süreçlerinde kullanılacak Analitik Değerlendirme Verisinin kontrollü, izlenebilir, doğrulanabilir şekilde hazırlanmasını ve Sistem Modeline aktarılabilmesini sağlayacaktır.
2. AVY, Analitik Değerlendirme Verisinin hazırlanmasında kullanılacak Sistem Saha Kayıtlarını Saha Veri Yöneticisi bileşeninden alabilecektir.
3. AVY, Analitik Değerlendirme Verisini oluşturmak için gereken veriler olarak Senaryo Üretecinin ürettiği sentetik verileri alabilecektir.
4. AVY, Saha Veri Yöneticisinden temin edilen Sistem Saha Kayıtlarını veya Senaryo Üretecinden sağlanan sentetik verileri işleyerek uygun şekilde ilişkilendirecek ve detayları kritik tasarım aşamasında belirlenecek Analitik Değerlendirme Verisini üreterek Sistem Modeline iletecektir.
5. AVY, Sistem Saha Kayıtlarında format uyumsuzluğu veya okunamayan veri tespit edilmesi durumunu raporlayacak ve kayıt altına alacaktır.
6. AVY, Senaryo Üretecinin sağladığı sentetik verilerde format uyumsuzluğu, okunamayan veri veya eksik alan tespit edilmesi durumunu raporlayacak ve kayıt altına alacaktır.

---

## 5. Sistem Model Yöneticisi (SaaG-SMY)

**Tablo 6. SaaG-SMY İster Dağılımı**

| CSU | CSU Kimliği | İster Sayısı |
|---|---|---|
| Sistem Model Yöneticisi | SMY | 37 |
| **Alt Toplam** | | **37** |

### 5.1 SMY: Sistem Model Yöneticisi

#### 5.1.1 Yapısal Çizge İnşası ve Yönetimi

1. SMY, Sayısal Sistem Modeli'nin oluşturulmasına esas Model Verisini kullanarak sistemin yapısal ve ilişkisel temsilini düğüm-ilişki yapısında inşa edecek; statik analiz, doğrulama ve simülasyon süreçlerinde kullanılabilir hale getirecektir.
2. SMY, Model Veri Üreteci bileşeni tarafından üretilen Model Verisini girdi olarak kabul edebilecektir.
3. SMY, Sistem Modeli'nin inşasından önce Model Verisi üzerinde format, şema, bütünlük ve zorunlu alan kontrollerini gerçekleştirecektir.
4. SMY, kontrollerden başarıyla geçen Model Verisini düğüm-ilişki tabanlı Sistem Modeline dönüştürecektir.
5. SMY, Sistem Modelini ilgili proje, platform ve sistem sürüm bilgisiyle ilişkilendirilmiş şekilde oluşturacaktır.
6. SMY, Model Verisinde yer alan yapısal sistem varlıklarından Sistemi düğüm-ilişki yapısında düğüm olarak temsil edecektir.
7. SMY, Model Verisinde yer alan yapısal sistem varlıklarından Yazılım Segmentini düğüm-ilişki yapısında düğüm olarak temsil edecektir.
8. SMY, Model Verisinde yer alan yapısal sistem varlıklarından Yazılım Kırılım Öğesini (CSCI) düğüm-ilişki yapısında düğüm olarak temsil edecektir.
9. SMY, Model Verisinde yer alan yapısal sistem varlıklarından Yazılım Komponentini (CSC) düğüm-ilişki yapısında düğüm olarak temsil edecektir.
10. SMY, Model Verisinde yer alan yapısal sistem varlıklarından Yazılım Birimini (CSU) düğüm-ilişki yapısında düğüm olarak temsil edecektir.
11. SMY, Model Verisinde yer alan yapısal sistem varlıklarından Rolü düğüm-ilişki yapısında düğüm olarak temsil edecektir.
12. SMY, Model Verisinde yer alan yapısal sistem varlıklarından Topici düğüm-ilişki yapısında düğüm olarak temsil edecektir.
13. SMY, Model Verisinde yer alan yapısal sistem varlıklarından Mesajı düğüm-ilişki yapısında düğüm olarak temsil edecektir.
14. SMY, Model Verisinde yer alan yapısal sistem varlıklarından Operatör Konsolu ve İşlemci Birimlerini düğüm-ilişki yapısında düğüm olarak temsil edecektir.
15. SMY, Model Verisinde yer alan yapısal sistem varlıklarından Ağ bileşenlerini düğüm-ilişki yapısında düğüm olarak temsil edecektir.
16. SMY, Model Verisinde yer alan yapısal sistem varlıklarından Arakatman Servislerini düğüm-ilişki yapısında düğüm olarak temsil edecektir.
17. SMY, Model Verisinde yer alan yapısal sistem varlıklarından Haberleşme Teknolojilerine ait Servisleri düğüm-ilişki yapısında düğüm olarak temsil edecektir.
18. SMY, yapısal sistem varlıkları arasındaki ilişki türlerinden "Operatör Konsolu ve İşlemci Birimlerinde Koşma" ilişkisini düğüm-ilişki yapısında ilişki olarak temsil edecektir.
19. SMY, yapısal sistem varlıkları arasındaki ilişki türlerinden "Arakatman ve Haberleşme Servislerini Kullanma" ilişkisini düğüm-ilişki yapısında ilişki olarak temsil edecektir.
20. SMY, yapısal sistem varlıkları arasındaki ilişki türlerinden "Veri yayımlama" ilişkisini düğüm-ilişki yapısında ilişki olarak temsil edecektir.
21. SMY, yapısal sistem varlıkları arasındaki ilişki türlerinden "Veri tüketme" ilişkisini düğüm-ilişki yapısında ilişki olarak temsil edecektir.
22. SMY, yapısal sistem varlıkları arasındaki ilişki türlerinden "Kütüphane veya yazılım birimine bağımlı olma" ilişkisini düğüm-ilişki yapısında ilişki olarak temsil edecektir.
23. SMY, yapısal sistem varlıkları arasındaki ilişki türlerinden "Yazılım biriminin role atanması" ilişkisini düğüm-ilişki yapısında ilişki olarak temsil edecektir.
24. SMY, sistemin yazılım birimlerine ait işlemci çekirdek tahsisini (CPU allocation), işletim sistemi ayarlarını ve çalışma-zamanı ortamı konfigürasyonlarını (JVM vb.) düğüm-ilişki yapısı üzerinde sorgulanabilir öznitelikler olarak temsil edecektir.
25. SMY, Sistem Modeli inşası sırasında tespit edilen eksik varlık ve geçersiz ilişki hatalarını raporlayacak ve kayıt altına alacaktır.
26. SMY, oluşturulan Sistem Modeli için kullanılan Model Verisi dosyasını, model oluşturma zamanını, proje bilgisini, platform bilgisini, sistem sürüm numarasını ve model durumunu kayıt altına alacaktır.
27. SMY, Sistem Modelini Tasarım Doğrulama Motoru bileşeninin kullanımına sunacaktır.
28. SMY, Tasarım Doğrulama Motoru bileşeninin düğümlere, ilişkilere ve bunlarla ilişkili Analitik Değerlendirme Verisine erişebilmesini sağlayacaktır.
29. SMY, aynı Sistem Modeli üzerinde birden fazla kullanıcı oturumu tarafından eşzamanlı olarak gerçekleştirilen okuma/yazma işlemlerini, model bütünlüğünü ve sorgu sonuçlarının tutarlılığını bozmayacak şekilde yönetecektir.
30. SMY, üretim dağıtım hattındaki işlemler ile detayları kritik tasarım aşamasında belirlenecek sayıda kullanıcının analiz ve simülasyon işlemlerini eşzamanlı ve birbirini etkilemeyecek şekilde bağımsız olarak yürütecektir.
31. SMY, hedef ortama kurulması değerlendirilen yazılım biriminin aday sürümü ile hedef sistem sürümündeki diğer yazılım birimlerini kullanarak işleme özel yeni bir Sistem Modeli oluşturacaktır.

#### 5.1.2 Analitik Veri Bağlama

32. SMY, Analitik Değerlendirme Verisini Sistem Modeli içerisindeki ilgili sistem varlıkları ve aralarındaki bağlantılar ile eşleştirerek statik analiz, doğrulama ve simülasyon süreçlerinde kullanılabilir hale getirecektir.
33. SMY, Analitik Veri Yöneticisi bileşeni tarafından üretilen Analitik Değerlendirme Verisini girdi olarak kabul edebilecektir.
34. SMY, Analitik Değerlendirme Verisini ilgili proje, platform, sistem sürümü ve Sistem Modeli ile ilişkilendirecek; veri içeriğindeki kayıt, telemetri ve sentetik verileri ilgili düğüm ve ilişkilerle eşleştirerek düğüm-ilişki yapısına bağlayacaktır.
35. SMY, Analitik Değerlendirme Verisinin Saha Veri Yöneticisinden alınan verilerle mi yoksa Senaryo Üretecinin ürettiği sentetik verilerle mi üretildiği bilgisini koruyacaktır.
36. SMY, Analitik Değerlendirme Verisini Sistem Modelindeki düğüm ve ilişkileri değiştirmeksizin modele bağlayacak; Sistem Modeli verisi ile Analitik Değerlendirme Verisinin birbirinden ayrılabilir şekilde yönetilmesini sağlayacaktır.
37. SMY, Analitik Değerlendirme Verisinde karşılığı bulunamayan düğüm veya ilişki kayıtlarını raporlayacak ve kayıt altına alacaktır.

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
2. TDM, Model Veri Üreteci, Senaryo Üreteci, Analitik Veri Yöneticisi ve Sistem Model Yöneticisi bileşenleri ile etkileşim kurabilecektir.
3. TDM, sisteme erişmek isteyen kullanıcıların kullanıcı adı ve parola bilgilerini tanımlı bir LDAP dizin servisi üzerinden doğrulayacak ve yalnızca başarılı şekilde doğrulanan kullanıcıların yetkileri dahilinde sisteme erişimine izin verecektir.
4. TDM, kullanıcının üzerinde işlem yapılacak proje, platform ve sistem sürümünü seçebilmesini sağlayacak ve seçilen proje ile platform için yürürlükteki güncel sistem sürümünü belirgin şekilde sergileyecektir.
5. TDM, seçilen proje, platform ve sistem sürümüne ait Model Verisi dosyalarını kullanıcıya listeleyecek ve kullanılacak dosyanın kullanıcı tarafından seçilebilmesini sağlayacaktır.
6. TDM, kullanıcının Model Verisi üretim sürecini başlatabilmesini ve sürecin durumunu devam ediyor, başarılı veya başarısız durumlarından biri olarak izleyebilmesini sağlayacaktır.
7. TDM, kullanılan tüm veri kaynaklarının erişilebilirlik durumunu sürekli ve izlenebilir şekilde kullanıcıya sergileyecektir.
8. TDM, Model Verisi üretimi sırasında tespit edilen eksik veri, erişim, yetki, format veya bütünlük hatalarını kullanıcıya sergileyecektir.
9. TDM, kullanıcının seçilen Model Verisini kullanarak Sistem Modeli oluşturma sürecini başlatabilmesini ve işlem sonucunu başarılı veya başarısız olarak izleyebilmesini sağlayacaktır.
10. TDM, kullanıcının Analitik Değerlendirme Verisinin oluşturulmasında kullanılacak veri kaynağını Sistem Saha Kayıtları olarak seçebilmesini sağlayacaktır.
11. TDM, kullanıcının Analitik Değerlendirme Verisinin oluşturulmasında kullanılacak veri kaynağını Senaryo Üretecinin sağladığı sentetik veriler olarak seçebilmesini sağlayacaktır.
12. TDM, Analitik Değerlendirme Verisi kaynağı olarak Sistem Saha Kayıtlarının kullanılacağı durumda kullanıcının kullanılacak kayıtları seçebilmesini sağlayacaktır.
13. TDM, Analitik Değerlendirme Verisi kaynağı olarak sentetik verilerin kullanılacağı durumda kullanıcının senaryo kapsamı, senaryo türü, zaman aralığı, veri yoğunluğu ve üretilecek veri türlerine ilişkin girdileri belirleyebilmesini sağlayacaktır.
14. TDM, kullanıcının sentetik veri üretim sürecini başlatabilmesini, sürecin durumunu takip edebilmesini ve üretim sırasında oluşan hataları görüntüleyebilmesini sağlayacaktır.
15. TDM, kullanıcının Analitik Değerlendirme Verisi üretim sürecini başlatabilmesini, sürecin durumunu takip edebilmesini ve üretim sırasında oluşan hataları görüntüleyebilmesini sağlayacaktır.
16. TDM, Sistem Modeline bağlanan Analitik Değerlendirme Verisinin ilişkili olduğu proje, platform ve sistem sürüm bilgilerini kullanıcıya sergileyecek; veri içeriğindeki kayıt, telemetri ve sentetik verilerin düğüm ve ilişkilerle eşleşme durumunu raporlayacaktır.
17. TDM, kullanıcının Sistem Modelinden türetilmiş bir çalışma modeli üzerinde, yapısal bütünlüğü bozmadan düğüm ekleme/çıkarma, ilişki ekleme/çıkarma ve düğüm/ilişki özniteliklerini güncelleme gibi yapısal değişiklikler yapabilmesini sağlayacak ve güncellenen çalışma modeli üzerinde tasarım doğrulama ve analiz işlemlerinin yürütülmesine imkân tanıyacaktır.
18. TDM, detayları kritik tasarım aşamasında belirlenecek kural/metrikler doğrultusunda tasarım doğrulama ve analiz sonuçlarını "uygun" veya "uygun değil" olarak sınıflandıracaktır.
19. TDM, kullanıcının düğüm-ilişki yapısı üzerinde sistem varlığı veya ilişkisi arayabilmesini; sonuçları tür, proje, platform, sistem sürümü veya yazılım birimi bilgisine göre filtreleyebilmesini sağlayacaktır.
20. TDM, kullanıcının düğüm-ilişki yapısı üzerinde görsel yakınlaştırma, uzaklaştırma, kaydırma ve düğüm/ilişki seçimi ile öznitelik görüntüleme işlemlerini gerçekleştirebilmesini sağlayacaktır.
21. TDM, analiz sonuçlarında tespit edilen her bir bulguyu en az şu bilgilerle kullanıcıya sunacaktır: bulgu kimliği, bulgu türü, bulgu açıklaması, etkilenen sistem varlığı veya ilişkisi, ilgili doğrulama kuralı veya kabul kriteri, bulguyu destekleyen veri veya kanıt ve bulgunun bilgi, düşük, orta, yüksek veya kritik olarak ifade edilen önem derecesi.
22. TDM, aynı işlem kapsamında tespit edilen ilişkili bulgular arasındaki neden-sonuç bağıntısını kayıt altına alacak ve kullanıcıya sergileyecektir.
23. TDM, kullanıcının bulguları işlem türü, değerlendirme sonucu, bulgu türü, önem derecesi, proje, platform, sistem sürümü veya etkilenen düğümlere göre sıralayabilmesini ve filtreleyebilmesini sağlayacaktır.
24. TDM, bir tasarım doğrulama, analiz veya simülasyon işlemi sırasında oluşan hata nedenini, işlemin kesintiye uğradığı aşamayı ve hata zamanını kayıt altına alacaktır.
25. TDM, simülasyon işlemlerinde kullanılan senaryo adını, senaryo girdilerini, veri üretim zamanını ve ilişkili proje, platform ve sistem sürüm bilgisini kayıt altına alabilecektir.
26. TDM, tasarım doğrulama, analiz ve simülasyon sonuçlarını detayları kritik tasarım aşamasında belirlenecek dışa aktarılabilir bir dosya formatında özet veya detaylı sistem raporu olarak üretecek; raporların en az proje bilgisi, platform bilgisi, sistem sürüm bilgisi, kullanılan Sistem Modeli, kullanılan Analitik Değerlendirme Verisi ve veri kaynağı, işlem kimliği ve işlem türü, işlem başlangıç ve bitiş zamanı, değerlendirme sonucu, tespit edilen bulgular, etkilenen düğüm ve ilişkiler, önem dereceleri ve bulgulara ilişkin ek bilgileri içermesini sağlayacaktır.
27. TDM, kullanıcı arayüzleri üzerinden yapılan analiz taleplerini Yapı Otomasyon Araçları ve Komut Satırı Arayüzü (CLI) üzerinden de kabul edecek; sisteme erişen kullanıcılara ve otomasyon istemcilerine (örn. Jenkins) yürütülen işlemlerin durum bilgisini sunacak ve analiz işlemlerinin eşzamanlı ve birbirinden bağımsız olarak yürütülmesini sağlayacaktır.

#### 6.1.2 Yapısal Tasarım Doğrulama

28. TDM, Sistem Modeli üzerinde tasarım doğrulama işlemlerini gerçekleştirecektir.
29. TDM, Sistem Modelindeki düğüm ve ilişkileri değiştirmeksizin tasarım doğrulama işlemlerini yürütecektir.
30. TDM, Analitik Değerlendirme Verisi kullanmaksızın yalnızca Sistem Modeli üzerinden analiz yapabilecektir.
31. TDM, Sistem Modeli üzerinde sistem varlıkları arasındaki yapısal bağımlılıkların, haberleşme bağlantılarının ve çalışma-zamanı ortamı ilişkilerinin analizini gerçekleştirebilecektir.
32. TDM, Sistem Modeli üzerinde, topic veri iletimi Durability (kalıcılık) servis kalite parametrelerinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve uyumsuzlukları tespit edecektir.
33. TDM, Sistem Modeli üzerinde, topic veri iletimi Reliability (güvenilirlik) servis kalite parametrelerinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve uyumsuzlukları tespit edecektir.
34. TDM, Sistem Modeli üzerinde, topic veri iletimi Lifespan (yaşam süresi) servis kalite parametrelerinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve uyumsuzlukları tespit edecektir.
35. TDM, Sistem Modeli üzerinde, topic veri iletimi Transport Priority (iletim önceliği) servis kalite parametrelerinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve uyumsuzlukları tespit edecektir.
36. TDM, Sistem Modeli üzerinde topic veri yayımcısı ve veri tüketicisi eşleşmelerini doğrulayacak ve veri yayımcısı bulunmayan topici tespit edecektir.
37. TDM, Sistem Modeli üzerinde topic veri yayımcısı ve veri tüketicisi eşleşmelerini doğrulayacak ve veri tüketicisi bulunmayan topici tespit edecektir.
38. TDM, Sistem Modeli üzerinde topic veri yayımcısı ve veri tüketicisi eşleşmelerini doğrulayacak ve aynı isimle tanımlanmış fakat içerik tanımları birbirinden farklı olan topicleri tespit edecektir.
39. TDM, Sistem Modeli üzerinde, detayları kritik tasarım aşamasında belirlenecek haberleşme servisleri üzerinden yürütülen arakatman dışı haberleşmelerde kaynak, hedef, mesaj ve haberleşme yönü bilgilerinin karşılıklı tutarlılığını doğrulayacaktır.
40. TDM, Sistem Modeli üzerinde sistemin yazılım birimlerinin Operatör Konsolu ve İşlemci Birimlerine dağılımının, detayları kritik tasarım aşamasında belirlenecek yük dengeleme kurallarına uygunluğunu analiz edecektir.
41. TDM, Sistem Modeli üzerinde sistemin yazılım birimlerine yapılan işlemci çekirdek tahsisinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve bir İşlemci Biriminde tahsis edilen toplam çekirdek sayısının mevcut çekirdek kapasitesini aşması durumunu tespit edecektir.
42. TDM, Sistem Modeli üzerinde sistemin yazılım birimlerine yapılan işlemci çekirdek tahsisinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve aynı çekirdeklerin birden fazla uygulamaya çakışacak şekilde tahsis edilmesi durumunu tespit edecektir.
43. TDM, Sistem Modeli üzerinde sistemin yazılım birimlerine yapılan işlemci çekirdek tahsisinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacak ve yüksek performansla çalışması gereken uygulamalara adanmış çekirdek tahsis edilmemesi durumunu tespit edecektir.
44. TDM, Sistem Modeli üzerinde işlemci/konsol birimlerinde çalışan işletim sistemi ayarlarının, detayları kritik tasarım aşamasında belirlenecek kurallara ve yapılan işlemci çekirdek tahsisine uygunluğunu denetleyecektir.
45. TDM, Sistem Modeli üzerinde sistemin yazılım birimlerinin çalışma-zamanı ortamı konfigürasyonlarında yer alan bellek tahsis parametrelerinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu doğrulayacaktır.
46. TDM, Sistem Modeli üzerinde işlemci çekirdek tahsisi, işletim sistemi ayarları ve çalışma-zamanı ortamı konfigürasyonları arasındaki tutarsızlıklardan kaynaklanabilecek kaynak çekişmesi ve darboğaz yaratabilecek durumları tespit edecektir.
47. TDM, Sistem Modeli üzerinde sistemin yazılım birimleri arasındaki döngüsel bağımlılıkları tespit edecektir.
48. TDM, Sistem Modeli üzerinde, modeldeki düğümler arasında kopuk, eksik, geçersiz veya eşleşmeyen yapısal ilişkileri tespit edecektir.
49. TDM, Sistem Modeli üzerinde, detayları kritik tasarım aşamasında belirlenecek mimari kurallara aykırı tasarım örüntülerini tespit edecektir.

#### 6.1.3 Davranışsal Simülasyon ve Analiz

50. TDM, Sistem Modeli üzerinde statik analiz işlemlerini gerçekleştirecektir.
51. TDM, Sistem Modelindeki düğüm ve ilişkileri değiştirmeksizin analiz işlemlerini yürütecektir.
52. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak analiz yapabilecektir.
53. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak düğümler arasındaki mesaj akış yönünü, mesaj adedini, veri hacmini ve mesajlaşma sıklığını analiz edecektir.
54. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak bir düğüm veya ilişkinin devre dışı kalmasının Sistem Modeli üzerindeki etkilerini değerlendirebilecektir.
55. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak tasarım-zamanı trafik analizi yapabilecek; simülasyon dahilinde oluşturulan yük koşullarının sistem varlıkları ve ilişkiler üzerindeki etkileri kapsamında Topic/Mesaj yoğunluğunun artması durumunu değerlendirebilecektir.
56. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak tasarım-zamanı trafik analizi yapabilecek; simülasyon dahilinde oluşturulan yük koşullarının sistem varlıkları ve ilişkiler üzerindeki etkileri kapsamında Topic/Mesaj yayımlama veya tüketme davranışının değişmesi durumunu değerlendirebilecektir.
57. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak simülasyon dahilinde oluşturulan arıza, yük, haberleşme kesintisi veya bant genişliği daralması durumlarının bağımlı düğümlere yayılımını belirleyecek; doğrudan veya dolaylı etkilenen düğüm/ilişkileri ve etkinin izlediği yayılım yolunu tespit edecektir.
58. TDM, Senaryo Üretecinin sağladığı sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak gerçekleştirilecek simülasyon sonucunda en yüksek kaynak kullanımına sahip veya en yoğun mesajlaşan sistem varlıklarını belirleyecek ve bunları kullanıcıya özet değerlendirme göstergeleri olarak sunacaktır.
59. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak analiz yapabilecektir.
60. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Sistem Modeli üzerinde operasyonel durum ve sağlık durumu konularında analiz yapabilecektir.
61. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Sistem Modeli üzerinde işlemci, bellek, depolama ve ağ kullanım değerleri konularında analiz yapabilecektir.
62. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Sistem Modeli üzerinde hata, uyarı, yeniden başlama ve zaman aşımı bilgileri konularında analiz yapabilecektir.
63. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Sistem Modeli üzerinde mesaj akış yönü, mesaj adedi, veri hacmi ve mesajlaşma sıklığı konularında analiz yapabilecektir.
64. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Sistem Modeli üzerinde haberleşme gecikmesi, mesaj kaybı ve başarılı iletim oranları konularında analiz yapabilecektir.
65. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Sistem Modeli üzerinde topic yayımlama ve tüketme aktiviteleri konularında analiz yapabilecektir.
66. TDM, Model Verisinde yer alan düğüm ve ilişkileri Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde gözlemlenen çalışma-zamanı sistem varlıkları ve ilişkileri ile karşılaştıracak; Model Verisinde yer alan ancak çalışma-zamanı verisinde gözlemlenmeyen sistem varlığı ve ilişkilerini tespit edecektir.
67. TDM, Model Verisinde yer alan düğüm ve ilişkileri Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde gözlemlenen çalışma-zamanı sistem varlıkları ve ilişkileri ile karşılaştıracak; Model Verisinde yer almayan ancak çalışma-zamanı verisinde gözlemlenen sistem varlığı ve ilişkilerini tespit edecektir.
68. TDM, Model Verisinde yer alan düğüm ve ilişkileri Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde gözlemlenen çalışma-zamanı sistem varlıkları ve ilişkileri ile karşılaştıracak; Model Verisi ile çalışma-zamanı verisi arasında uyumsuzluk gösteren sistem varlığı ve ilişkilerini tespit edecektir.
69. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde yer alan düğüm ve ilişkilerle ilişkili olay kayıtlarını analiz edecektir.
70. TDM, Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak yapılacak analiz sonucunda en yüksek kaynak kullanımına sahip veya en yoğun mesajlaşan sistem varlıklarını belirleyecek ve bunları özet değerlendirme göstergeleri olarak kullanıcıya sunacaktır.

#### 6.1.4 Kurulum Uygunluk Değerlendirmesi

71. TDM, Sistem Modeli üzerinde, aday yazılım birimleri için kurulum uygunluk değerlendirmesi şeklinde değerlendirme işlemlerini gerçekleştirecektir.
72. TDM, bir yazılım biriminin hedef ortama kurulum uygunluğunu yapısal ve mimari uygunluk değerlendirme başlığı altında analiz edecektir.
73. TDM, bir yazılım biriminin hedef ortama kurulum uygunluğunu arayüz, topic ve haberleşme uygunluğu değerlendirme başlığı altında analiz edecektir.
74. TDM, bir yazılım biriminin hedef ortama kurulum uygunluğunu bağımlılık ve entegrasyon uygunluğu değerlendirme başlığı altında analiz edecektir.
75. TDM, bir yazılım biriminin hedef ortama kurulum uygunluğunu kaynak ve performans yeterliliği değerlendirme başlığı altında analiz edecektir.
76. TDM, kurulum uygunluk değerlendirmesinde kullanılan her bir kontrol kuralını kural kimliği, değerlendirme başlığı, önem derecesi, ağırlık değeri, kabul kriteri ve bloke edici olma durumu ile tanımlayacak; kural sonuçlarına ait uygunluk kategorilerini ve puanlama yöntemini detayları kritik tasarım aşamasında belirlenecek şekilde sınıflandıracak ve puanlayacaktır.
77. TDM, kritik önem derecesine sahip bir bulgunun veya değerlendirme profilinde bloke edici olarak tanımlanmış bir kontrol kuralı ihlalinin tespit edilmesi durumunda genel uygunluk puanından bağımsız olarak hedef ortama kurulum sonucunu "uygun değil" olarak belirleyecek ve üretim dağıtım hattının devam etmesini engelleyecek karar bilgisini otomasyon istemcisine iletecektir.
78. TDM, üretim dağıtım hattı kapsamında bir veya birden fazla yazılım birimi için başlatılan kurulum uygunluk değerlendirmelerini birbirinden bağımsız işlem kimlikleriyle yürütecek; her yazılım birimi için ayrı uygunluk puanı, skor sınıfı, bloke edici bulgular ve kurulum kararının yanı sıra toplu işlem sonucunu makine tarafından işlenebilir biçimde otomasyon istemcisine sunacaktır.
