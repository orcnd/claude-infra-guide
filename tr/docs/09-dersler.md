# 9. Dersler

## İşe yarayanlar

| Ders | Ayrıntı |
|---|---|
| Araçtan önce veri | "Daha çok test" gerektiğini sanıyorduk. Etiketlenmiş iadeler atlanan maddeleri, çelişen sayıları ve eksik çevirileri gösterdi. |
| Metin yerine hook | CLAUDE.md'deki yasaklar uzun oturumlarda unutuluyor; hook'lar unutulmuyor. |
| Agent ve insan için tek CLI | Kısa çıktı, Bash'ten çağrılıyor. Bakımı yapılacak tek şey, insanlar da çalıştırabiliyor. |
| Duraklar | Context sorusu, checklist onayı, düzeltme onayı. En pahalıya patlayan, erken yazılan kod. |
| Kanıt | "Hangi URL, ne gördün"; checklist ve kapı bunu zorunlu tutuyor. |
| Korunan context | Doğrulama bir sub-agent'ta, referans bilgisi path kurallarında, kod soruları grafta. |
| Tahmin edilebilir adresler | Port ve host görev numarasından türüyor; Claude URL'yi kendisi çıkarabiliyor. |
| Tek çağrıda durum | Jira, çalışma alanları, git ve geçmiş oturumlar tek bir JSON'da. |

## Tuzaklar

| Belirti | Sebep | Çözüm |
|---|---|---|
| Düzenlemeler görünmüyor | Sunucu build modunda kalmış | `ws ls` içindeki MODE sütunu; doğrulamayı her zaman bitirin |
| Görev oturumunda hook yok | Görev klasöründe `.claude` yok | Symlink verin |
| Kural dosyası yüklenmedi | Dosya oturum kökünün dışında | CLAUDE.md'de "önce kuralı oku" |
| Bir görev diğerini bozdu | Ortak repo veya DB | Ortak düzenlemelerden önce uyarın; migration'dan önce görevleri listeleyin |
| Kaynak checkout'ta düzenleme | Hangi görevde olduğu unutuldu | Oturum işareti + açık kural |
| Yavaş makine | Çok sayıda dev sunucusu | Bellek sınırı, `ws down`, `ws clean` |
| Allowlist'te token | Kişisel izinler komutları olduğu gibi saklıyor | Asla paylaşmayın; token'lar ortam değişkenlerinden gelsin |

## Nereden başlamalı

```mermaid
quadrantChart
    title Maliyet ve etki
    x-axis Düşük kurulum maliyeti --> Yüksek kurulum maliyeti
    y-axis Düşük etki --> Yüksek etki
    quadrant-1 Planlayın
    quadrant-2 Önce yapın
    quadrant-3 Olsa iyi olur
    quadrant-4 Yalnızca gerekirse
    "CLAUDE.md + onaylar": [0.15, 0.8]
    "Slop hook'ları": [0.2, 0.55]
    "Path kuralları": [0.3, 0.6]
    "Ticket checklist": [0.35, 0.85]
    "Doğrulama agent'ı": [0.45, 0.75]
    "Kod grafı": [0.4, 0.45]
    "Ortak tarayıcı": [0.7, 0.65]
    "UAT kapısı": [0.75, 0.8]
    "Görev çalışma alanları": [0.85, 0.5]
```

```mermaid
flowchart LR
    S1["1. İade veya hata<br/>verinizi etiketleyin"] --> S2["2. CLAUDE.md<br/>+ onaylar"]
    S2 --> S3["3. Slop kontrolü"]
    S3 --> S4["4. Checklist +<br/>doğrulama agent'ı"]
    S4 --> S5{"paralel görevler<br/>sık mı?"}
    S5 -- evet --> S6["5. Çalışma alanı CLI'ı"]
    S5 -- hayır --> S7["atla"]
    S6 --> S8["6. UAT kapısı:<br/>verinin gösterdiğini zorunlu kıl"]
    S7 --> S8
```

Bizim beş kontrolümüz bizim iadelerimize uyuyor. Önce sizinkileri etiketleyin, araçları o seçsin.
