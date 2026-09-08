# Yazılım Gereksinimleri Şartnamesi (SRS): System as a Graph (SaaG)

**Tanım:** System as a Graph (SaaG) Sayısal Sistem Modeli, mimari dijital ikiz yaklaşımıyla geliştirilmiş, sistem uygulamalarını fiilen çalıştırmaksızın, sistemin yapısal ve ilişkisel mimarisini düğüm-ilişki temsiliyle modelleyen statik bir sayısal sistem modelidir. Bu modelde yazılım birimleri, arakatman ve haberleşme servisleri, işlemci/konsol birimleri, topic ve mesaj gibi sistem varlıkları düğüm; aralarındaki bağımlılık, yayımlama ve tüketme bağıntıları ise ilişki olarak temsil edilir. Modelin davranışsal analizlere imkân tanıyan boyutu, bileşenlerin koşumuyla değil; saha kayıtlarından veya senaryo üretecinden türetilen Analitik Değerlendirme Verisinin bu model üzerine bindirilmesiyle sağlanır.

SaaG, Yazılım Kırılım Öğesidir (CSCI). Bu Yazılım Gereksinimleri Şartnamesi (SRS), sistem ve yazılım isterlerini tek bir şartnamede birleştirerek tanımlanan altı Yazılım Komponentini (CSC) on Yazılım Birimine (CSU) ayrıştırır. Her işlevsel ister tam olarak bir CSU'ya kapsamlandırılmış olup sisteme ait altyapı kısıtları da resmi olarak dokümante edilmiştir.

**Amaç:** Modelin birincil amacı mimari doğrulamadır. Bu kapsamda yapısal/döngüsel bağımlılıklar, yayımcı/tüketici eşleşmeleri, topic servis kalite parametrelerinin (QoS) uygunluğu, sistemde yer alan donanımların kapasite uygunluğu (CPU çekirdek adedi, RAM boyutu, ağ bant genişliği vb.) ve mimari kurallara aykırı tasarım örüntüleri tasarım aşamasında statik olarak denetlenir. Mimari doğrulama, tasarımda öngörülen mimari ile saha verisinde gözlemlenen çalışma-zamanı yapısı arasındaki sapmaların (architectural drift) tespitini de kapsar. Mimari doğrulamanın yanı sıra model, kurgusal senaryo analizlerine olanak tanır; kullanıcı, yapısal bütünlüğü bozmadan düğüm/ilişki ekleyip çıkararak ya da öznitelikleri değiştirerek deneysel tasarım kurguları oluşturabilir. Bu kurgusal senaryolarda bir varlığın devre dışı kalması, mesaj yoğunluğunun artması veya bant genişliğinin daralması gibi durumların bağımlı varlıklara yayılımı ve mimari üzerindeki etkileri analitik olarak değerlendirilir. Ayrıca model, yazılım birimlerinin hedef ortama kurulum uygunluğunu canlıya alma işlem hattında (pipeline) otomatik olarak değerlendiren bir mekanizma sunar. Böylelikle Sayısal Sistem Modeli, henüz yazılım birimlerinin hedef ortama kurulumları yapılmadan tasarım kararlarının ve değişikliklerinin mimari sonuçlarını öngörmeye yönelik, tekrarlanabilir bir doğrulama ortamı sağlar.

**Tablo 1. SRS İster Dağılımı**

| No | Bileşen | Kısaltma | CSU Sayısı | CSU Kimlikleri | İster Sayısı |
|---|---|---|---|---|---|
| 1 | Model Kurulum Verisi Üretimi | SaaG-MKV | 1 | MKV | 23 |
| 2 | Senaryo Üreteci | SaaG-SUR | 1 | SUR | 7 |
| 3 | Saha Kayıtları Veri Tabanı | SaaG-SKV | 1 | SKV | 5 (+ 1 Altyapı) |
| 4 | Analitik Veri Hazırlama | SaaG-AVH | 1 | AVH | 6 |
| 5 | Düğüm-İlişki Tabanlı Çekirdek Sistem Modeli | SaaG-CSM | 2 | CSM-01, CSM-02 | 37 |
| 6 | Tasarım Doğrulama, Analiz ve Değerlendirme | SaaG-DAD | 4 | DAD-01, DAD-02, DAD-03, DAD-04 | 78 |
| **TOPLAM** | | | **10** | | **156 (+ 1 Altyapı)** |

Her bileşenin CSU başına ister dağılım tabloları, aşağıda ilgili bileşenin kendi bölümünde yer almaktadır. Bu belgedeki her ister, §7 üzerinden kaynak temel sistem kabiliyet isterine izlenebilir.
---

## 1. Model Kurulum Verisi Üretimi (SaaG-MKV)

**Tablo 2. SaaG-MKV İster Dağılımı**

| CSU | CSU Kimliği | İster Sayısı |
|---|---|---|
| Model Kurulum Verisi Üretimi | MKV | 23 |
| **Alt Toplam** | | **23** |

### 1.1 MKV: Model Kurulum Verisi Üretimi

1. MKV, Sayısal Sistem Modeli'nin oluşturulmasına esas Model Kurulum Verisinin kontrollü, izlenebilir, doğrulanabilir şekilde üretilmesini ve model inşası süreçlerine aktarılabilmesini sağlayacaktır.
2. MKV, Model Kurulum Verisi üretimi maksadıyla dış veri kaynağı olarak sistem konfigürasyon yönetimi veri tabanına erişim sağlayabilecek ve bu kaynaktan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir.
3. MKV, Model Kurulum Verisi üretimi maksadıyla dış veri kaynağı olarak sistem yazılım birimleri ve kurulum betikleri kaynak kodu deposuna erişim sağlayabilecek ve bu kaynaktan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir.
4. MKV, Model Kurulum Verisi üretimi maksadıyla dış veri kaynağı olarak Sistem Yazılım Birimleri Paket Deposuna erişim sağlayabilecek ve bu kaynaktan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir.
5. MKV, Model Kurulum Verisi üretimi maksadıyla dış veri kaynağı olarak Sistem Ağ Topolojisi Veri Kaynağına erişim sağlayabilecek ve bu kaynaktan alınan verileri kontrollü, izlenebilir şekilde yönetebilecektir.
6. MKV, sistem ağ topolojisi verisini, detayları kritik tasarım aşamasında belirlenecek dış bir veri kaynağından (dosya, veri tabanı vb.) otomatik olarak alabilecektir.
7. MKV, sistem ağ topolojisi verisini kullanıcının ağ topolojisi parametrelerini manuel olarak girmesi yoluyla alabilecektir.
8. MKV, her veri kaynağı için kaynak tipi, kaynak adı, erişim yöntemi, bağlantı adresi ve bağlantı için gerekli kullanıcı bilgilerini kullanıcı tarafından tanımlanabilir ve kaydedilebilir ayar bilgisi olarak yönetecektir.
9. MKV, veri alım işlemlerini proje bilgisi, platform bilgisi ve sistem sürüm numarası ile ilişkilendirilmiş şekilde yürütecektir.
10. MKV, konfigürasyon yönetimi veri tabanından mevcut proje bilgilerini alabilecektir.
11. MKV, konfigürasyon yönetimi veri tabanından seçilen projeye ait platform bilgilerini alabilecektir.
12. MKV, konfigürasyon yönetimi veri tabanından seçilen proje ve platforma ait sistem sürüm bilgilerini alabilecektir.
13. MKV, konfigürasyon yönetimi veri tabanından alınan sistem sürüm bilgileri içerisindeki yürürlükteki güncel sürüm bilgisini işaretleyecektir.
14. MKV, seçilen proje, platform ve sürüm bilgisine göre sistem ortamında çalışacak yazılım birimlerine ait isim ve sürüm bilgilerini "Yazılım Birimi Sürüm Envanteri" olarak kayıt altına alacaktır.
15. MKV, hedef ortama kurulması değerlendirilen yazılım biriminin aday sürümü ile seçilen sistem sürümünde tanımlı diğer yazılım birimi sürümlerini kullanarak Yazılım Birimi Sürüm Envanterini güncelleyecek ve kayıt altına alacaktır.
16. MKV, konfigürasyon yönetimi veri tabanından alınan verilerde eksiklik, erişim hatası veya format uyumsuzluğu tespit edilmesi durumunda veri alım sürecini hata durumu ile işaretleyecektir.
17. MKV, kaynak kodu deposu üzerinden Yazılım Birimi Sürüm Envanteri kapsamındaki yazılım birimlerine ait kaynak kodu, kurulum betikleri ve konfigürasyon dosyalarına erişerek sisteme aktaracaktır.
18. MKV, kaynak kodu deposundan alınan her dosya için dosya adı, dosya yolu, paket/versiyon bilgisi ve güncelleme zaman damgasını kayıt altına alacaktır.
19. MKV, kaynak kodu deposundan alınması zorunlu olan ve detayları kritik tasarım aşamasında belirlenecek dosyalardan herhangi birinin eksik olması durumunda veri alım sürecini "eksik veri" durumu ile raporlayacaktır.
20. MKV, kaynak kodu deposundan alınan dosyalarda erişim, yetki veya bütünlük hatası oluşması durumunda ilgili hatayı sergileyecek ve kayıt altına alacaktır.
21. MKV, alınan veya elle girilen tüm kaynak verileri için model inşası kapsamında gerekli alan varlığı kontrolü gerçekleştirecektir.
22. MKV, alan varlığı kontrolünden başarısız olan her veri için hata nedeni, kaynak adı, kaynak tipi, ilişkili proje/platform bilgisi ve hata zamanı bilgisini kayıt altına alacaktır.
23. MKV, doğrulama kontrollerinden geçen kaynak verileri model inşası sürecine aktarılmaya hazır hale getirecek ve Model Kurulum Verisi dosyası olarak kaydedecektir.

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
7. SUR, üretilen sentetik veriyi Analitik Veri Hazırlama bileşenine aktarılmaya hazır hale getirecektir.

---

## 3. Saha Kayıtları Veri Tabanı (SaaG-SKV)

**Tablo 4. SaaG-SKV İster Dağılımı**

| CSU / Öğe | Kimlik | Tür | İster Sayısı |
|---|---|---|---|
| Saha Kayıtları Veri Tabanı | SKV | İşlevsel | 5 |
| Depolama Platform Ortamı | SKV-INF | Altyapı | 1 |
| **Alt Toplam** | | | **6** |

### 3.1 SKV: Saha Kayıtları Veri Tabanı

1. SKV, sistemin kurulu olduğu platformlardan sistem veri kayıt mekanizması ile alınan sistem veri kayıtlarını ve telemetri verilerini "Sistem Saha Kayıtları" olarak merkezi biçimde depolayacak ve yönetecektir.
2. SKV, kullanıcının sistem saha ortamından alınan telemetri ve sistem veri kayıtlarını kontrollü, izlenebilir şekilde yükleyebilmesini sağlayacak ve yüklenen kayıtları ilgili proje bilgisi, platform bilgisi ve sistem sürüm numarası ile ilişkilendirerek kaydedecektir.
3. SKV, yüklenen Sistem Saha Kayıtlarını kayıt kaynağı, yükleme zamanı, ilişkili proje, platform ve sistem sürüm bilgisiyle birlikte izlenebilir şekilde kayıt altına alacaktır.
4. SKV, kullanıcının mevcut Sistem Saha Kayıtlarını proje, platform, sistem sürümü, kayıt kaynağı veya yükleme zamanı ölçütlerine göre listeleyebilmesini, arayabilmesini ve seçebilmesini sağlayacaktır.
5. SKV, yükleme sırasında tespit edilen format uyumsuzluğu, bütünlük hatası veya eksik alan durumlarını raporlayacak ve kayıt altına alacaktır.

### 3.2 Altyapı ve Platform Kısıtları

1. **SKV-INF.1:** SKV, depolama donanımının disk kapasitesi ve donanım özellikleri kritik tasarım aşamasında belirlenecek bir depolama altyapısı üzerinde çalışacaktır.

---

## 4. Analitik Veri Hazırlama (SaaG-AVH)

**Tablo 5. SaaG-AVH İster Dağılımı**

| CSU | CSU Kimliği | İster Sayısı |
|---|---|---|
| Analitik Veri Hazırlama | AVH | 6 |
| **Alt Toplam** | | **6** |

### 4.1 AVH: Analitik Veri Hazırlama

1. AVH, analiz, doğrulama ve simülasyon süreçlerinde kullanılacak Analitik Değerlendirme Verisinin kontrollü, izlenebilir, doğrulanabilir şekilde hazırlanmasını ve Çekirdek Sistem Modeline aktarılabilmesini sağlayacaktır.
2. AVH, Analitik Değerlendirme Verisinin hazırlanmasında kullanılacak Sistem Saha Kayıtlarını Saha Kayıtları Veri Tabanından alabilecektir.
3. AVH, Analitik Değerlendirme Verisini oluşturmak için gerekli olan verileri, Senaryo Üreteci tarafından üretilen sentetik veriler olarak alabilecektir.
4. AVH, Sistem Saha Kayıtları veya Senaryo Üreteci tarafından sağlanan sentetik verileri işleyip uygun şekilde ilişkilendirerek detayları kritik tasarım aşamasında belirlenecek Analitik Değerlendirme Verisini üretecek ve Çekirdek Sistem Modeline iletecektir.
5. AVH, Sistem Saha Kayıtlarında format uyumsuzluğu veya okunamayan veri tespit edilmesi durumunu raporlayacak ve kayıt altına alacaktır.
6. AVH, Senaryo Üreteci tarafından sağlanan sentetik veride format uyumsuzluğu, okunamayan veri veya eksik alan tespit edilmesi durumunu raporlayacak ve kayıt altına alacaktır.

---

## 5. Düğüm-İlişki Tabanlı Çekirdek Sistem Modeli (SaaG-CSM)

**Tablo 6. SaaG-CSM İster Dağılımı**

| CSU | CSU Kimliği | İster Sayısı |
|---|---|---|
| Model Yöneticisi | CSM-01 | 31 |
| Analitik Veri Bağlayıcısı | CSM-02 | 6 |
| **Alt Toplam** | | **37** |

### 5.1 CSM-01: Model Yöneticisi

1. CSM-01, Model Kurulum Verisini kullanarak sistemin yapısal ve ilişkisel temsilini bir düğüm-ilişki yapısında oluşturacak ve statik analiz, doğrulama ve simülasyon süreçlerinde kullanılabilir hâle getirecektir.
2. CSM-01, Model Kurulum Verisi Üretimi bileşeni tarafından oluşturulan Model Kurulum Verisini girdi olarak alabilecektir.
3. CSM-01, Çekirdek Sistem Modelinin inşası öncesinde Model Kurulum Verisinin biçim, şema, bütünlük ve zorunlu alan kontrollerini gerçekleştirecektir.
4. CSM-01, kontrolden geçen Model Kurulum Verisini düğüm-ilişki tabanlı Çekirdek Sistem Modeline dönüştürecektir.
5. CSM-01, Çekirdek Sistem Modelini ilgili proje, platform ve sistem sürüm bilgisi ile ilişkilendirilmiş şekilde oluşturacaktır.
6. CSM-01, Sistemi düğüm-ilişki yapısında bir düğüm olarak temsil edecektir.
7. CSM-01, Yazılım Segmentini düğüm-ilişki yapısında bir düğüm olarak temsil edecektir.
8. CSM-01, Yazılım Kırılım Öğesini (CSCI) düğüm-ilişki yapısında bir düğüm olarak temsil edecektir.
9. CSM-01, Yazılım Komponentini (CSC) düğüm-ilişki yapısında bir düğüm olarak temsil edecektir.
10. CSM-01, Yazılım Birimini (CSU) düğüm-ilişki yapısında bir düğüm olarak temsil edecektir.
11. CSM-01, Rolü düğüm-ilişki yapısında bir düğüm olarak temsil edecektir.
12. CSM-01, Topic'i düğüm-ilişki yapısında bir düğüm olarak temsil edecektir.
13. CSM-01, Mesajı düğüm-ilişki yapısında bir düğüm olarak temsil edecektir.
14. CSM-01, Operatör Konsolu ve İşlemci Birimlerini düğüm-ilişki yapısında düğümler olarak temsil edecektir.
15. CSM-01, Ağ bileşenlerini düğüm-ilişki yapısında düğümler olarak temsil edecektir.
16. CSM-01, Arakatman Servislerini düğüm-ilişki yapısında düğümler olarak temsil edecektir.
17. CSM-01, Haberleşme Teknolojilerine ait Servisleri düğüm-ilişki yapısında düğümler olarak temsil edecektir.
18. CSM-01, "Operatör Konsolu ve İşlemci Birimleri üzerinde çalışma" durumunu düğüm-ilişki yapısında bir ilişki olarak temsil edecektir.
19. CSM-01, "Arakatman ve İletişim Servislerini kullanma" durumunu düğüm-ilişki yapısında bir ilişki olarak temsil edecektir.
20. CSM-01, "Veri yayımlama" durumunu düğüm-ilişki yapısında bir ilişki olarak temsil edecektir.
21. CSM-01, "Veri tüketme" durumunu düğüm-ilişki yapısında bir ilişki olarak temsil edecektir.
22. CSM-01, "Kütüphane veya yazılım birimine bağımlı olma" durumunu düğüm-ilişki yapısında bir ilişki olarak temsil edecektir.
23. CSM-01, "Yazılım biriminin bir role tanımlanması" durumunu düğüm-ilişki yapısında bir ilişki olarak temsil edecektir.
24. CSM-01, sistem yazılım birimlerine ait işlemci çekirdek tahsisi (CPU allocation), işletim sistemi ayarları ve çalışma zamanı ortamı yapılandırmalarını (JVM vb.) düğüm-ilişki yapısı üzerinde sorgulanabilir öznitelikler olarak temsil edecektir.
25. CSM-01, Çekirdek Sistem Modelinin oluşturulması sırasında tespit edilen eksik varlık ve geçersiz ilişki hatalarını raporlayacak ve kayıt altına alacaktır.
26. CSM-01, oluşturulan Çekirdek Sistem Modeli için kullanılan Model Kurulum Verisi dosyasını, model oluşturma zamanını, proje bilgisini, platform bilgisini, sistem sürüm numarasını ve model durumunu kayıt altına alacaktır.
27. CSM-01, Çekirdek Sistem Modelini Tasarım Doğrulama, Analiz ve Değerlendirme bileşeninin kullanımına sunacaktır.
28. CSM-01, Tasarım Doğrulama, Analiz ve Değerlendirme bileşeninin düğümlere, ilişkilere ve bunlarla ilişkilendirilmiş Analitik Değerlendirme Verilerine erişebilmesini sağlayacaktır.
29. CSM-01, aynı Çekirdek Sistem Modeli üzerinde birden fazla kullanıcı oturumu tarafından eşzamanlı olarak gerçekleştirilen okuma/yazma işlemlerini, model bütünlüğünü ve sorgu sonuçlarının tutarlılığını bozmadan karşılayacaktır.
30. CSM-01, üretim dağıtım hattındaki işlemler ile kritik tasarım aşamasında belirlenecek sayıda kullanıcının analiz ve simülasyon işlemlerini eşzamanlı ve birbirinden bağımsız olarak yürütecek; işlemlerin birbirini etkilemesini engelleyecektir.
31. CSM-01, hedef ortama kurulması değerlendirilen yazılım biriminin aday sürümü ile hedef sistem sürümündeki diğer yazılım birimlerini kullanarak işleme özel yeni bir Çekirdek Sistem Modeli oluşturacaktır.

### 5.2 CSM-02: Analitik Veri Bağlayıcısı

1. CSM-02, Analitik Değerlendirme Verisini Çekirdek Sistem Modelindeki ilgili sistem varlıkları ile bunlar arasındaki bağlantılarla eşleştirerek statik analiz, doğrulama ve simülasyon süreçlerinde kullanılabilir hâle getirecektir.
2. CSM-02, Analitik Veri Hazırlama bileşeni tarafından üretilen Analitik Değerlendirme Verisini girdi olarak alabilecektir.
3. CSM-02, Analitik Değerlendirme Verisini ilgili proje, platform, sistem sürümü ve Çekirdek Sistem Modeli ile ilişkilendirecek; veride bulunan kayıt, telemetri ve sentetik verileri ilgili düğümlerle ve ilişkilerle eşleştirecek ve düğüm-ilişki yapısına bağlayacaktır.
4. CSM-02, Analitik Değerlendirme Verisinin Sistem Saha Kayıtları veya Senaryo Üreteci tarafından sağlanan sentetik verilerden hangisi kullanılarak üretildiği bilgisini koruyacaktır.
5. CSM-02, Analitik Değerlendirme Verisini Çekirdek Sistem Modelindeki düğümleri ve ilişkileri değiştirmeden modele bağlayacak ve Çekirdek Sistem Modeli verileri ile Analitik Değerlendirme Verilerinin birbirinden ayrıştırılabilir şekilde yönetilmesini sağlayacaktır.
6. CSM-02, Analitik Değerlendirme Verisinde karşılığı bulunamayan düğüm veya ilişki kayıtlarını raporlayacak ve kayıt altına alacaktır.

---

## 6. Tasarım Doğrulama, Analiz ve Değerlendirme (SaaG-DAD)

**Tablo 7. SaaG-DAD İster Dağılımı**

| CSU | CSU Kimliği | İster Sayısı |
|---|---|---|
| İşlem Paneli | DAD-01 | 27 |
| Tasarım Doğrulayıcı | DAD-02 | 22 |
| Tasarım Analizcisi | DAD-03 | 21 |
| Tasarım Değerlendiricisi | DAD-04 | 8 |
| **Alt Toplam** | | **78** |

### 6.1 DAD-01: İşlem Paneli

1. DAD-01, Tasarım Doğrulayıcı (DAD-02), Tasarım Analizcisi (DAD-03) ve Tasarım Değerlendiricisi (DAD-04) tarafından gerçekleştirilen tasarım doğrulama, statik analiz ve değerlendirme işlemlerinde kullanıcının sistem bileşenleriyle doğrudan etkileşim kurmasını sağlayacak ve bu işlemlerin sonuçlarını kullanıcıya sunacaktır.
2. DAD-01, Model Kurulum Verisi Üretimi, Senaryo Üreteci, Analitik Veri Hazırlama ve Çekirdek Sistem Modeli bileşenleriyle etkileşim kurabilecektir.
3. DAD-01, sisteme erişmek isteyen kullanıcıların kullanıcı adı ve parola bilgilerini tanımlı LDAP dizin hizmeti üzerinden doğrulayacak ve yalnızca kimlik doğrulaması başarılı olan kullanıcıların yetkileri kapsamında sisteme erişmesini sağlayacaktır.
4. DAD-01, kullanıcının işlem yapılacak proje, platform ve sistem sürümünü seçebilmesini sağlayacak ve proje ile platform için yürürlükte bulunan güncel sistem sürümünü ayırt edilebilir şekilde gösterecektir.
5. DAD-01, seçilen proje, platform ve sistem sürümüne ait Model Kurulum Verisi dosyalarını kullanıcıya listeleyecek ve kullanıcının kullanılacak dosyayı seçebilmesini sağlayacaktır.
6. DAD-01, kullanıcının Model Kurulum Verisi üretim sürecini başlatabilmesini ve sürecin durumunu devam ediyor, başarılı veya başarısız durumlarından biriyle izleyebilmesini sağlayacaktır.
7. DAD-01, kullanılan tüm veri kaynaklarına ait erişilebilirlik durumlarını kullanıcıya sürekli ve izlenebilir şekilde gösterecektir.
8. DAD-01, Model Kurulum Verisi üretimi sırasında tespit edilen eksik veri, erişim, yetki, biçim veya bütünlük hatalarını kullanıcıya gösterecektir.
9. DAD-01, kullanıcının seçilen Model Kurulum Verisini kullanarak Çekirdek Sistem Modelini oluşturma işlemini başlatabilmesini ve işlem sonucunu başarılı ya da başarısız durumlarından biriyle izleyebilmesini sağlayacaktır.
10. DAD-01, kullanıcının Analitik Değerlendirme Verisinin oluşturulmasında kullanılacak veri kaynağı olarak Sistem Saha Kayıtlarını seçebilmesini sağlayacaktır.
11. DAD-01, kullanıcının Analitik Değerlendirme Verisinin oluşturulmasında kullanılacak veri kaynağı olarak Senaryo Üreteci tarafından sağlanan sentetik verileri seçebilmesini sağlayacaktır.
12. DAD-01, Analitik Değerlendirme Verisi kaynağı olarak Sistem Saha Kayıtlarının kullanılacağı durumda kullanıcının kullanılacak kayıtları seçebilmesini sağlayacaktır.
13. DAD-01, Analitik Değerlendirme Verisi kaynağı olarak sentetik verilerin kullanılacağı durumda kullanıcının senaryo kapsamı, senaryo türü, zaman aralığı, veri yoğunluğu ve üretilecek veri türlerine ilişkin girdileri belirleyebilmesini sağlayacaktır.
14. DAD-01, kullanıcının sentetik veri üretim sürecini başlatabilmesini, takip edebilmesini ve üretim sırasında meydana gelen hataları görüntüleyebilmesini sağlayacaktır.
15. DAD-01, kullanıcının Analitik Değerlendirme Verisi üretim sürecini başlatabilmesini, takip edebilmesini ve üretim sırasında meydana gelen hataları görüntüleyebilmesini sağlayacaktır.
16. DAD-01, kullanıcıya Çekirdek Sistem Modeline bağlanan Analitik Değerlendirme Verisinin ilişkili olduğu proje, platform ve sistem sürümü bilgisini gösterecek; veride bulunan kayıt, telemetri ve sentetik verilerin düğümler ve ilişkilerle eşleştirme durumunu raporlayacaktır.
17. DAD-01, kullanıcının Çekirdek Sistem Modelinin yapısal bütünlüğünü bozmadan türetilen bir çalışma modeli üzerinde düğüm ekleme/çıkarma, ilişki ekleme/çıkarma ve düğüm/ilişki özniteliklerini güncelleme gibi yapısal değişiklikler gerçekleştirebilmesini; güncellenen çalışma modeli üzerinde tasarım doğrulama ve analiz işlemleri yürütebilmesini sağlayacaktır.
18. DAD-01, tasarım doğrulama ve analiz sonuçlarını detayları kritik tasarım aşamasında belirlenecek kurallara/metriklere göre "uygun" veya "uygun değil" durumlarından biriyle sınıflandıracaktır.
19. DAD-01, kullanıcının düğüm-ilişki yapısı üzerinde sistem varlığı veya ilişki araması yapabilmesini ve sonuçları tür, proje, platform, sistem sürümü veya yazılım birimi bilgilerine göre süzebilmesini sağlayacaktır.
20. DAD-01, kullanıcının düğüm-ilişki yapısı üzerinde görsel yakınlaştırma, uzaklaştırma, taşıma ve düğüm/ilişki seçme, öznitelik görüntüleme işlemlerini gerçekleştirebilmesini sağlayacaktır.
21. DAD-01, analiz sonuçlarında tespit edilen her bulguyu en az aşağıdaki bilgilerle birlikte kullanıcıya sunacaktır: bulgu kimliği, bulgu türü, bulgu açıklaması, etkilenen sistem varlığı veya ilişki, ilgili doğrulama kuralı veya kabul ölçütü, bulguyu destekleyen veri veya kanıt ve bulgunun bilgilendirme, düşük, orta, yüksek veya kritik seviyelerinden biriyle ifade edilen önem derecesi.
22. DAD-01, aynı işlem kapsamında tespit edilen birbiriyle ilişkili bulgular arasındaki neden-sonuç ilişkisini kayıt altına alacak ve kullanıcıya gösterecektir.
23. DAD-01, kullanıcının bulguları işlem türü, değerlendirme sonucu, bulgu türü, önem derecesi, proje, platform, sistem sürümü veya etkilenen düğümlere göre sıralayabilmesini ve süzebilmesini sağlayacaktır.
24. DAD-01, tasarım doğrulama, analiz veya simülasyon işlemi sırasında oluşan hata nedenini, işlemin kesildiği aşamayı ve hata zamanını kayıt altına alacaktır.
25. DAD-01, simülasyon işlemlerinde kullanılan senaryo adını, senaryo girdilerini, veri üretim zamanını ve ilişkili proje, platform ve sistem sürüm bilgilerini kaydedebilecektir.
26. DAD-01, tasarım doğrulama, analiz ve simülasyon sonuçlarının özet veya ayrıntılı sistem raporunu detayları kritik tasarım aşamasında belirlenecek dışa aktarılabilir dosya biçiminde oluşturacak ve raporlarda en az aşağıdaki bilgilerin yer almasını sağlayacaktır: proje bilgisi, platform bilgisi, sistem sürüm bilgisi, kullanılan Çekirdek Sistem Modeli, kullanılan Analitik Değerlendirme Verisi ve veri kaynağı, işlem kimliği ve işlem türü, işlem başlangıç ve bitiş zamanı, değerlendirme sonucu, tespit edilen bulgular, etkilenen düğümler ve ilişkiler, önem dereceleri ve bulgulara ilişkin ilave bilgiler.
27. DAD-01, kullanıcı arayüzleri üzerinden yapılan analiz isteklerini Derleme Otomasyon Araçları (Build Automation Tool) ve Komut Satırı Arayüzü (CLI) üzerinden de kabul edecek; sisteme erişen kullanıcılar ile otomasyon istemcilerine (Jenkins vb.) devam eden işlemlerin durum bilgisini sunacak ve analiz işlemlerinin birbirinden bağımsız olarak eş zamanlı yürütülmesini sağlayacaktır.

### 6.2 DAD-02: Tasarım Doğrulayıcı

1. DAD-02, Çekirdek Sistem Modeli üzerinde tasarım doğrulama işlemlerini gerçekleştirecektir.
2. DAD-02, tasarım doğrulama işlemlerini Çekirdek Sistem Modelindeki düğüm ve ilişkileri değiştirmeden gerçekleştirecektir.
3. DAD-02, Analitik Değerlendirme Verisi kullanılmaksızın yalnızca Çekirdek Sistem Modeli üzerinde analizler gerçekleştirebilecektir.
4. DAD-02, sistem varlıkları arasındaki yapısal bağımlılıkların, haberleşme bağlantılarının ve çalışma ortamı ilişkilerinin analizini Çekirdek Sistem Modeli üzerinde gerçekleştirebilecektir.
5. DAD-02, topic veri iletimi servis kalite parametrelerinden Veri Saklama (Durability) parametresinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu Çekirdek Sistem Modeli üzerinde doğrulayacak ve uyumsuzlukları tespit edecektir.
6. DAD-02, topic veri iletimi servis kalite parametrelerinden Güvenilirlik (Reliability) parametresinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu Çekirdek Sistem Modeli üzerinde doğrulayacak ve uyumsuzlukları tespit edecektir.
7. DAD-02, topic veri iletimi servis kalite parametrelerinden Yaşam Süresi (Lifespan) parametresinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu Çekirdek Sistem Modeli üzerinde doğrulayacak ve uyumsuzlukları tespit edecektir.
8. DAD-02, topic veri iletimi servis kalite parametrelerinden Taşıma Önceliği (TransportPriority) parametresinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu Çekirdek Sistem Modeli üzerinde doğrulayacak ve uyumsuzlukları tespit edecektir.
9. DAD-02, topic veri yayımlayıcı ve veri tüketici eşleşmelerini Çekirdek Sistem Modeli üzerinde doğrulayacak ve veri yayımlayıcısı bulunmayan topic'leri tespit edecektir.
10. DAD-02, topic veri yayımlayıcı ve veri tüketici eşleşmelerini Çekirdek Sistem Modeli üzerinde doğrulayacak ve veri tüketicisi bulunmayan topic'leri tespit edecektir.
11. DAD-02, topic veri yayımlayıcı ve veri tüketici eşleşmelerini Çekirdek Sistem Modeli üzerinde doğrulayacak ve aynı isimle tanımlanan topic'lerin içerik tanımlarının birbirinden farklı olduğu durumları tespit edecektir.
12. DAD-02, kritik tasarım aşamasında belirlenecek haberleşme servisleri üzerinden gerçekleştirilen arakatman harici iletişimlerde kaynak, hedef, mesaj ve iletişim yönü bilgilerinin birbiriyle uyumunu Çekirdek Sistem Modeli üzerinde doğrulayacaktır.
13. DAD-02, sistem yazılım birimlerinin Operatör Konsolu ve İşlemci Birimleri üzerindeki dağılımının detayları kritik tasarım aşamasında belirlenecek yük dengeleme kurallarına uygunluğunu Çekirdek Sistem Modeli üzerinde analiz edecektir.
14. DAD-02, sistem yazılım birimlerine yapılan işlemci çekirdek tahsisinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu Çekirdek Sistem Modeli üzerinde doğrulayacak ve bir İşlemci Birimi üzerinde tahsis edilen toplam çekirdek sayısının mevcut çekirdek kapasitesini aşması durumunu tespit edecektir.
15. DAD-02, sistem yazılım birimlerine yapılan işlemci çekirdek tahsisinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu Çekirdek Sistem Modeli üzerinde doğrulayacak ve aynı çekirdeklerin birden fazla uygulamaya çakışacak şekilde tahsis edilmesi durumunu tespit edecektir.
16. DAD-02, sistem yazılım birimlerine yapılan işlemci çekirdek tahsisinin detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu Çekirdek Sistem Modeli üzerinde doğrulayacak ve yüksek performansla çalışması gereken uygulamalara özel (dedicated) çekirdek tahsis edilmemiş olması durumunu tespit edecektir.
17. DAD-02, işlemci/konsol birimlerinde çalışan işletim sistemi ayarlarının detayları kritik tasarım aşamasında belirlenecek kurallara ve yapılan işlemci çekirdek tahsisine uygunluğunu Çekirdek Sistem Modeli üzerinde denetleyecektir.
18. DAD-02, sistem yazılım birimlerine ait çalışma zamanı ortamı yapılandırmalarındaki bellek tahsis parametrelerinin, detayları kritik tasarım aşamasında belirlenecek kurallara uygunluğunu Çekirdek Sistem Modeli üzerinde doğrulayacaktır.
19. DAD-02, işlemci çekirdek tahsisi, işletim sistemi ayarları ve çalışma zamanı ortamı yapılandırmaları arasındaki tutarsızlıklardan kaynaklanabilecek kaynak yığılması ve darboğaz oluşturabilecek durumları Çekirdek Sistem Modeli üzerinde tespit edecektir.
20. DAD-02, sistem yazılım birimleri arasındaki döngüsel bağımlılıkları Çekirdek Sistem Modeli üzerinde tespit edecektir.
21. DAD-02, Çekirdek Sistem Modeli dahilindeki düğümler arasındaki kopuk, eksik, geçersiz veya karşılığı bulunmayan yapısal ilişkileri Çekirdek Sistem Modeli üzerinde tespit edecektir.
22. DAD-02, detayları kritik tasarım aşamasında belirlenecek mimari kurallara aykırı tasarım örüntülerini Çekirdek Sistem Modeli üzerinde tespit edecektir.

### 6.3 DAD-03: Tasarım Analizcisi

1. DAD-03, Çekirdek Sistem Modeli üzerinde statik analiz işlemlerini gerçekleştirecektir.
2. DAD-03, analiz işlemlerini Çekirdek Sistem Modelindeki düğüm ve ilişkileri değiştirmeden gerçekleştirecektir.
3. DAD-03, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisi kullanılarak analizler gerçekleştirebilecektir.
4. DAD-03, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak düğümler arasındaki mesaj akış yönünü, mesaj sayısını, veri hacmini ve mesajlaşma sıklığını analiz edecektir.
5. DAD-03, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak bir düğümün ya da ilişkinin devre dışı kalması durumunun Çekirdek Sistem Modeli üzerindeki etkilerini değerlendirebilecektir.
6. DAD-03, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak tasarım zamanı trafik analizi yapabilecek ve simülasyon kapsamında oluşturulan yük koşullarının sistem varlıkları ve ilişkiler üzerindeki etkileri kapsamında Topic/Mesaj yoğunluğunun artması durumunu değerlendirebilecektir.
7. DAD-03, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak tasarım zamanı trafik analizi yapabilecek ve simülasyon kapsamında oluşturulan yük koşullarının sistem varlıkları ve ilişkiler üzerindeki etkileri kapsamında Topic/Mesaj yayın veya tüketim davranışının değişmesi durumunu değerlendirebilecektir.
8. DAD-03, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak simülasyon kapsamında oluşturulan arıza, yük, iletişim kesintisi veya bant genişliği daralması durumlarının bağımlı düğümler üzerindeki yayılımını belirleyecek; doğrudan veya dolaylı olarak etkilenen düğümler/ilişkileri ve etkinin izlediği yayılım yolunu tespit edecektir.
9. DAD-03, Senaryo Üreteci tarafından sağlanan sentetik verilerden üretilen Analitik Değerlendirme Verisini kullanarak yapılacak simülasyon sonucunda en yüksek kaynak kullanımına sahip veya en yoğun mesajlaşan sistem varlıklarını belirleyecek ve özet değerlendirme göstergeleri olarak kullanıcıya sunacaktır.
10. DAD-03, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisi kullanılarak analizler gerçekleştirebilecektir.
11. DAD-03, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde çalışma ve sağlık durumlarına ilişkin analizler gerçekleştirebilecektir.
12. DAD-03, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde işlemci, bellek, depolama ve ağ kullanım değerlerine ilişkin analizler gerçekleştirebilecektir.
13. DAD-03, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde hata, uyarı, yeniden başlatma ve zaman aşımı bilgilerine ilişkin analizler gerçekleştirebilecektir.
14. DAD-03, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde mesaj akış yönü, mesaj sayısı, veri hacmi ve mesajlaşma sıklığına ilişkin analizler gerçekleştirebilecektir.
15. DAD-03, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde iletişim gecikmesi, mesaj kaybı ve başarılı iletim oranlarına ilişkin analizler gerçekleştirebilecektir.
16. DAD-03, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak Çekirdek Sistem Modeli üzerinde topic yayın ve tüketim etkinliklerine ilişkin analizler gerçekleştirebilecektir.
17. DAD-03, Model Kurulum Verisindeki düğümler ve ilişkiler ile Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde gözlemlenen çalışma zamanı sistem varlıklarını ve ilişkilerini karşılaştıracak ve Model Kurulum Verisinde yer aldığı hâlde çalışma zamanı verilerinde gözlemlenmeyen sistem varlıklarını ve ilişkileri tespit edecektir.
18. DAD-03, Model Kurulum Verisindeki düğümler ve ilişkiler ile Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde gözlemlenen çalışma zamanı sistem varlıklarını ve ilişkilerini karşılaştıracak ve Model Kurulum Verisinde yer almadığı hâlde çalışma zamanı verilerinde gözlemlenen sistem varlıklarını ve ilişkileri tespit edecektir.
19. DAD-03, Model Kurulum Verisindeki düğümler ve ilişkiler ile Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde gözlemlenen çalışma zamanı sistem varlıklarını ve ilişkilerini karşılaştıracak ve Model Kurulum Verisi ile çalışma zamanı verileri arasında uyumsuzluk bulunan sistem varlıklarını ve ilişkileri tespit edecektir.
20. DAD-03, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisinde bulunan düğümler ve ilişkilerle bağlantılı olay kayıtlarını analiz edecektir.
21. DAD-03, Sistem Saha Kayıtlarından üretilen Analitik Değerlendirme Verisini kullanarak analiz sonucunda en yüksek kaynak kullanımına sahip veya en yoğun mesajlaşan sistem varlıklarını belirleyecek ve özet değerlendirme göstergeleri olarak kullanıcıya sunacaktır.

### 6.4 DAD-04: Tasarım Değerlendiricisi

1. DAD-04, aday yazılım birimleri için kurulum uygunluk değerlendirmesi biçiminde Çekirdek Sistem Modeli üzerinde değerlendirme işlemlerini gerçekleştirecektir.
2. DAD-04, bir yazılım biriminin hedef ortama kurulum uygunluğunu yapısal ve mimari uygunluk değerlendirme başlığı altında analiz edecektir.
3. DAD-04, bir yazılım biriminin hedef ortama kurulum uygunluğunu arayüz, topic ve haberleşme uygunluğu değerlendirme başlığı altında analiz edecektir.
4. DAD-04, bir yazılım biriminin hedef ortama kurulum uygunluğunu bağımlılık ve entegrasyon uygunluğu değerlendirme başlığı altında analiz edecektir.
5. DAD-04, bir yazılım biriminin hedef ortama kurulum uygunluğunu kaynak ve performans yeterliliği değerlendirme başlığı altında analiz edecektir.
6. DAD-04, kurulum uygunluk değerlendirmesinde kullanılan her kontrol kuralını kural kimliği, değerlendirme başlığı, önem derecesi, ağırlık değeri, kabul ölçütü ve bloke edici olma durumu ile tanımlayacak; kural sonuçlarına ait uygunluk kategorileri ve puanlama yöntemi detayları kritik tasarım aşamasında belirlenecek şekilde sınıflandıracak ve puanlayacaktır.
7. DAD-04, kritik önem derecesine sahip bir bulgunun veya değerlendirme profilinde bloke edici olarak tanımlanmış bir kontrol kuralı ihlalinin tespit edilmesi durumunda genel uygunluk puanından bağımsız olarak hedef ortama kurulum sonucunu "uygun değil" olarak belirleyecek ve üretim dağıtım hattının devam etmesini engelleyecek karar bilgisini otomasyon istemcisine iletecektir.
8. DAD-04, üretim dağıtım hattı kapsamında bir veya birden fazla yazılım birimi için başlatılan kurulum uygunluk değerlendirmelerini birbirinden bağımsız işlem kimlikleriyle yürütecek; her yazılım birimi için ayrı uygunluk puanı, skor sınıfı, bloke edici bulgular ve kurulum kararının yanı sıra toplu işlem sonucunu makine tarafından işlenebilir biçimde otomasyon istemcisine sunacaktır.

---

## 7. Sistem Kabiliyeti Dağılımı ve İster İzlenebilirliği

Bu bölüm, sistem seviyesi temel kabiliyet isterleri (CSCI/CSC seviyesi) ile Yazılım Birimi (CSU) işlevsel isterleri arasındaki iki yönlü izlenebilirliği ve dağılımı ortaya koyar.

**İlişki türü açıklamaları:**
- **Doğrudan**: Temel bir sistem kabiliyet isterinin ayrıştırılmadan tek bir CSU işlevsel isterine doğrudan atanması.
- **Bölünmüş**: Bileşik bir sistem kabiliyet isterinin birden fazla bağımsız ve test edilebilir CSU işlevsel isterine ayrıştırılması.
- **Birleşik**: Sistem geneline veya bileşen misyonuna yönelik bir kabiliyet isterinin birden fazla CSU'nun eşgüdümlü işlevsel isterleriyle karşılanması.
- **Altyapı**: Çalışma-zamanı ortamına veya fiziksel platform donanımına tahsis edilmiş işlevsel olmayan sistem kısıtı.

### SaaG-MKV

| SRS İster No | CSU | Temel Sistem İster No | İlişki |
|---|---|---|---|
| MKV.1 | MKV | SSS-MKV.1 | Doğrudan (görev tanımı) |
| MKV.2 | MKV | SSS-MKV.2 | Bölünmüş |
| MKV.3 | MKV | SSS-MKV.2 | Bölünmüş |
| MKV.4 | MKV | SSS-MKV.2 | Bölünmüş |
| MKV.5 | MKV | SSS-MKV.2 | Bölünmüş |
| MKV.6 | MKV | SSS-MKV.3 | Bölünmüş |
| MKV.7 | MKV | SSS-MKV.3 | Bölünmüş |
| MKV.8 | MKV | SSS-MKV.4 | Doğrudan |
| MKV.9 | MKV | SSS-MKV.5 | Doğrudan |
| MKV.10 | MKV | SSS-MKV.6 | Doğrudan |
| MKV.11 | MKV | SSS-MKV.7 | Doğrudan |
| MKV.12 | MKV | SSS-MKV.8 | Doğrudan |
| MKV.13 | MKV | SSS-MKV.9 | Doğrudan |
| MKV.14 | MKV | SSS-MKV.10 | Doğrudan |
| MKV.15 | MKV | SSS-MKV.11 | Doğrudan |
| MKV.16 | MKV | SSS-MKV.12 | Doğrudan |
| MKV.17 | MKV | SSS-MKV.13 | Doğrudan |
| MKV.18 | MKV | SSS-MKV.14 | Doğrudan |
| MKV.19 | MKV | SSS-MKV.15 | Doğrudan |
| MKV.20 | MKV | SSS-MKV.16 | Doğrudan |
| MKV.21 | MKV | SSS-MKV.17 | Doğrudan |
| MKV.22 | MKV | SSS-MKV.18 | Doğrudan |
| MKV.23 | MKV | SSS-MKV.19 | Doğrudan |

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

### SaaG-SKV

| SRS İster No | CSU | Temel Sistem İster No | İlişki |
|---|---|---|---|
| SKV.1 | SKV | SSS-SKV.1 | Doğrudan (görev tanımı) |
| SKV.2 | SKV | SSS-SKV.2 | Doğrudan |
| SKV.3 | SKV | SSS-SKV.3 | Doğrudan |
| SKV.4 | SKV | SSS-SKV.4 | Doğrudan |
| SKV.5 | SKV | SSS-SKV.5 | Doğrudan |
| SKV-INF.1 | SKV-INF | SSS-SKV.6 | Altyapı (platform depolama) |

### SaaG-AVH

| SRS İster No | CSU | Temel Sistem İster No | İlişki |
|---|---|---|---|
| AVH.1 | AVH | SSS-AVH.1 | Doğrudan (görev tanımı) |
| AVH.2 | AVH | SSS-AVH.2 | Doğrudan |
| AVH.3 | AVH | SSS-AVH.3 | Doğrudan |
| AVH.4 | AVH | SSS-AVH.4 | Doğrudan |
| AVH.5 | AVH | SSS-AVH.5 | Doğrudan |
| AVH.6 | AVH | SSS-AVH.6 | Doğrudan |

### SaaG-CSM

| SRS İster No | CSU | Temel Sistem İster No | İlişki |
|---|---|---|---|
| CSM-01.1 | CSM-01 | SSS-CSM.1 | Birleşik |
| CSM-01.2 | CSM-01 | SSS-CSM.2 | Doğrudan |
| CSM-01.3 | CSM-01 | SSS-CSM.3 | Doğrudan |
| CSM-01.4 | CSM-01 | SSS-CSM.4 | Doğrudan |
| CSM-01.5 | CSM-01 | SSS-CSM.5 | Doğrudan |
| CSM-01.6 | CSM-01 | SSS-CSM.6 | Bölünmüş |
| CSM-01.7 | CSM-01 | SSS-CSM.6 | Bölünmüş |
| CSM-01.8 | CSM-01 | SSS-CSM.6 | Bölünmüş |
| CSM-01.9 | CSM-01 | SSS-CSM.6 | Bölünmüş |
| CSM-01.10 | CSM-01 | SSS-CSM.6 | Bölünmüş |
| CSM-01.11 | CSM-01 | SSS-CSM.6 | Bölünmüş |
| CSM-01.12 | CSM-01 | SSS-CSM.6 | Bölünmüş |
| CSM-01.13 | CSM-01 | SSS-CSM.6 | Bölünmüş |
| CSM-01.14 | CSM-01 | SSS-CSM.6 | Bölünmüş |
| CSM-01.15 | CSM-01 | SSS-CSM.6 | Bölünmüş |
| CSM-01.16 | CSM-01 | SSS-CSM.6 | Bölünmüş |
| CSM-01.17 | CSM-01 | SSS-CSM.6 | Bölünmüş |
| CSM-01.18 | CSM-01 | SSS-CSM.7 | Bölünmüş |
| CSM-01.19 | CSM-01 | SSS-CSM.7 | Bölünmüş |
| CSM-01.20 | CSM-01 | SSS-CSM.7 | Bölünmüş |
| CSM-01.21 | CSM-01 | SSS-CSM.7 | Bölünmüş |
| CSM-01.22 | CSM-01 | SSS-CSM.7 | Bölünmüş |
| CSM-01.23 | CSM-01 | SSS-CSM.7 | Bölünmüş |
| CSM-01.24 | CSM-01 | SSS-CSM.8 | Doğrudan |
| CSM-01.25 | CSM-01 | SSS-CSM.9 | Doğrudan |
| CSM-01.26 | CSM-01 | SSS-CSM.15 | Doğrudan |
| CSM-01.27 | CSM-01 | SSS-CSM.16 | Doğrudan |
| CSM-01.28 | CSM-01 | SSS-CSM.17 | Doğrudan |
| CSM-01.29 | CSM-01 | SSS-CSM.18 | Doğrudan |
| CSM-01.30 | CSM-01 | SSS-CSM.19 | Doğrudan |
| CSM-01.31 | CSM-01 | SSS-CSM.20 | Doğrudan |
| CSM-02.1 | CSM-02 | SSS-CSM.1 | Birleşik |
| CSM-02.2 | CSM-02 | SSS-CSM.10 | Doğrudan |
| CSM-02.3 | CSM-02 | SSS-CSM.11 | Doğrudan |
| CSM-02.4 | CSM-02 | SSS-CSM.12 | Doğrudan |
| CSM-02.5 | CSM-02 | SSS-CSM.13 | Doğrudan |
| CSM-02.6 | CSM-02 | SSS-CSM.14 | Doğrudan |

### SaaG-DAD

| SRS İster No | CSU | Temel Sistem İster No | İlişki |
|---|---|---|---|
| DAD-01.1 | DAD-01 | SSS-DAD.1 | Birleşik |
| DAD-01.2 | DAD-01 | SSS-DAD.2 | Doğrudan |
| DAD-01.3 | DAD-01 | SSS-DAD.3 | Doğrudan |
| DAD-01.4 | DAD-01 | SSS-DAD.4 | Doğrudan |
| DAD-01.5 | DAD-01 | SSS-DAD.5 | Doğrudan |
| DAD-01.6 | DAD-01 | SSS-DAD.6 | Doğrudan |
| DAD-01.7 | DAD-01 | SSS-DAD.7 | Doğrudan |
| DAD-01.8 | DAD-01 | SSS-DAD.8 | Doğrudan |
| DAD-01.9 | DAD-01 | SSS-DAD.9 | Doğrudan |
| DAD-01.10 | DAD-01 | SSS-DAD.10 | Bölünmüş |
| DAD-01.11 | DAD-01 | SSS-DAD.10 | Bölünmüş |
| DAD-01.12 | DAD-01 | SSS-DAD.11 | Doğrudan |
| DAD-01.13 | DAD-01 | SSS-DAD.12 | Doğrudan |
| DAD-01.14 | DAD-01 | SSS-DAD.13 | Doğrudan |
| DAD-01.15 | DAD-01 | SSS-DAD.14 | Doğrudan |
| DAD-01.16 | DAD-01 | SSS-DAD.16 | Doğrudan |
| DAD-01.17 | DAD-01 | SSS-DAD.17 | Doğrudan |
| DAD-01.18 | DAD-01 | SSS-DAD.42 | Doğrudan |
| DAD-01.19 | DAD-01 | SSS-DAD.43 | Bölünmüş |
| DAD-01.20 | DAD-01 | SSS-DAD.43 | Bölünmüş |
| DAD-01.21 | DAD-01 | SSS-DAD.44 | Doğrudan |
| DAD-01.22 | DAD-01 | SSS-DAD.45 | Doğrudan |
| DAD-01.23 | DAD-01 | SSS-DAD.46 | Doğrudan |
| DAD-01.24 | DAD-01 | SSS-DAD.47 | Doğrudan |
| DAD-01.25 | DAD-01 | SSS-DAD.48 | Doğrudan |
| DAD-01.26 | DAD-01 | SSS-DAD.49 | Doğrudan |
| DAD-01.27 | DAD-01 | SSS-DAD.50 | Doğrudan |
| DAD-02.1 | DAD-02 | SSS-DAD.1 | Birleşik |
| DAD-02.2 | DAD-02 | SSS-DAD.15 | Birleşik |
| DAD-02.3 | DAD-02 | SSS-DAD.18 | Doğrudan |
| DAD-02.4 | DAD-02 | SSS-DAD.19 | Doğrudan |
| DAD-02.5 | DAD-02 | SSS-DAD.20 | Bölünmüş |
| DAD-02.6 | DAD-02 | SSS-DAD.20 | Bölünmüş |
| DAD-02.7 | DAD-02 | SSS-DAD.20 | Bölünmüş |
| DAD-02.8 | DAD-02 | SSS-DAD.20 | Bölünmüş |
| DAD-02.9 | DAD-02 | SSS-DAD.21 | Bölünmüş |
| DAD-02.10 | DAD-02 | SSS-DAD.21 | Bölünmüş |
| DAD-02.11 | DAD-02 | SSS-DAD.21 | Bölünmüş |
| DAD-02.12 | DAD-02 | SSS-DAD.22 | Doğrudan |
| DAD-02.13 | DAD-02 | SSS-DAD.23 | Doğrudan |
| DAD-02.14 | DAD-02 | SSS-DAD.24 | Bölünmüş |
| DAD-02.15 | DAD-02 | SSS-DAD.24 | Bölünmüş |
| DAD-02.16 | DAD-02 | SSS-DAD.24 | Bölünmüş |
| DAD-02.17 | DAD-02 | SSS-DAD.25 | Doğrudan |
| DAD-02.18 | DAD-02 | SSS-DAD.26 | Doğrudan |
| DAD-02.19 | DAD-02 | SSS-DAD.27 | Doğrudan |
| DAD-02.20 | DAD-02 | SSS-DAD.28 | Doğrudan |
| DAD-02.21 | DAD-02 | SSS-DAD.29 | Doğrudan |
| DAD-02.22 | DAD-02 | SSS-DAD.30 | Doğrudan |
| DAD-03.1 | DAD-03 | SSS-DAD.1 | Birleşik |
| DAD-03.2 | DAD-03 | SSS-DAD.15 | Birleşik |
| DAD-03.3 | DAD-03 | SSS-DAD.31 | Doğrudan |
| DAD-03.4 | DAD-03 | SSS-DAD.32 | Doğrudan |
| DAD-03.5 | DAD-03 | SSS-DAD.33 | Doğrudan |
| DAD-03.6 | DAD-03 | SSS-DAD.34 | Bölünmüş |
| DAD-03.7 | DAD-03 | SSS-DAD.34 | Bölünmüş |
| DAD-03.8 | DAD-03 | SSS-DAD.35 | Doğrudan |
| DAD-03.9 | DAD-03 | SSS-DAD.36 | Doğrudan |
| DAD-03.10 | DAD-03 | SSS-DAD.37 | Doğrudan |
| DAD-03.11 | DAD-03 | SSS-DAD.38 | Bölünmüş |
| DAD-03.12 | DAD-03 | SSS-DAD.38 | Bölünmüş |
| DAD-03.13 | DAD-03 | SSS-DAD.38 | Bölünmüş |
| DAD-03.14 | DAD-03 | SSS-DAD.38 | Bölünmüş |
| DAD-03.15 | DAD-03 | SSS-DAD.38 | Bölünmüş |
| DAD-03.16 | DAD-03 | SSS-DAD.38 | Bölünmüş |
| DAD-03.17 | DAD-03 | SSS-DAD.39 | Bölünmüş |
| DAD-03.18 | DAD-03 | SSS-DAD.39 | Bölünmüş |
| DAD-03.19 | DAD-03 | SSS-DAD.39 | Bölünmüş |
| DAD-03.20 | DAD-03 | SSS-DAD.40 | Doğrudan |
| DAD-03.21 | DAD-03 | SSS-DAD.41 | Doğrudan |
| DAD-04.1 | DAD-04 | SSS-DAD.1 | Birleşik |
| DAD-04.2 | DAD-04 | SSS-DAD.51 | Bölünmüş |
| DAD-04.3 | DAD-04 | SSS-DAD.51 | Bölünmüş |
| DAD-04.4 | DAD-04 | SSS-DAD.51 | Bölünmüş |
| DAD-04.5 | DAD-04 | SSS-DAD.51 | Bölünmüş |
| DAD-04.6 | DAD-04 | SSS-DAD.52 | Doğrudan |
| DAD-04.7 | DAD-04 | SSS-DAD.53 | Doğrudan |
| DAD-04.8 | DAD-04 | SSS-DAD.54 | Doğrudan |

**Kapsam kontrolü:** 112 temel sistem kabiliyetinin tamamı yukarıda en az bir kez yer almaktadır (111'i işlevsel CSU isteri olarak, 1'i — SSS-SKV.6 / SKV-INF.1 — platform altyapı kısıtı olarak). Toplam SRS işlevsel isteri sayısı: **156**; altyapı kısıtı sayısı: **1**; toplam yönetilen ister: **157**.
