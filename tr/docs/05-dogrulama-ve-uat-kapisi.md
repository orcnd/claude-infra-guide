# 5. Doğrulama ve UAT kapısı

## Neden test değil, sayfa

Jira'dan yaklaşık altı aylık UAT iadesini çektik (statü değişiklikleri ve her iadenin etrafındaki yorumlar),
üç ayrı model çalıştırmasıyla sabit bir sebep listesine göre etiketledik ve bir kısmını elle kontrol ettik.
UAT'ye teslim edilen işlerin yaklaşık üçte biri en az bir kez geri dönmüştü.

```mermaid
---
config:
  xyChart:
    width: 760
    height: 360
  themeVariables:
    xyChart:
      plotColorPalette: "#4C6EF5"
---
xychart-beta horizontal
    title "UAT iadesinin ana sebebi (iadelerin %'si)"
    x-axis ["Ticket maddeleri eksik", "Sayılar yanlış veya çelişkili", "Süreç, hata yok", "Kırık özellik veya link", "Çeviri veya dil biçimi", "Yerleşim veya mobil", "Dış bağımlılık", "Yanlış anlaşılan istek", "UAT'de gelen yeni istek", "Cache veya deploy"]
    y-axis "İadelerin %'si" 0 --> 20
    bar [17, 14, 14, 14, 12, 8, 6, 5, 5, 3]
```

Yaklaşık %70'i önlenebilirdi, ama birim testle değil. Her birini yakalayacak olan kontrol:

```mermaid
---
config:
  xyChart:
    width: 760
    height: 300
  themeVariables:
    xyChart:
      plotColorPalette: "#4C6EF5"
---
xychart-beta horizontal
    title "Yakalayacak olan kontrol (önlenebilir iadelerin %'si)"
    x-axis ["Ticket maddelerini sayfada yürümek", "Aynı sayıyı karşılaştırmak", "İngilizce dışı dilleri açmak", "Link, filtre, form tıklamak", "Mobil genişlikte açmak", "Diğer"]
    y-axis "Önlenebilir iadelerin %'si" 0 --> 35
    bar [32, 19, 18, 15, 7, 9]
```

İlk beşi %90'ın üzerini kapsıyor. Bu yüzden bu repolarda test yok; her değişiklik bu beş kontrolle bitiyor
ve kontrolleri araçlar yapıyor. CLAUDE.md, bunun "önce başarısız bir test yaz" adımlarının önüne geçtiğini söylüyor.

## Doğrulama turu

```mermaid
flowchart TD
    A["değişiklik yapıldı"] --> B["sayfayı + İngilizce dışı<br/>bir dili aç"]
    B --> C["sayfa metni + API payload"]
    C --> D["ws browse check --locales all"]
    C --> E["ws browse crawl"]
    C --> F["ws browse numbers ile API karşılaştırması"]
    C --> G["çelişkileri oku:<br/>aynı değer görünümler arasında farklı<br/>sıralar, toplamlar, %100'ü aşan değerler<br/>sayfanın gizlemesi gereken satırlar<br/>etiket ile veri, eski metin<br/>gelecek tarihler, yanlış etiket veya görsel<br/>bir kartın fazla satırının sırayı uzatması"]
    D --> X["bulgular"]
    E --> X
    F --> X
    G --> X
    X --> Y{"var mı?"}
    Y -- hayır --> Z["maddeyi kanıtla kapat"]
    Y -- evet --> R{{"nerede, ne, neden raporla<br/>onaydan sonra düzelt"}}
```

Bunu [page-logic-verifier](../../templates/.claude/agents/page-logic-verifier.md) agent'ı yürütüyor.

## `ws browse`: tüm agent'lar için tek tarayıcı

Playwright MCP her oturum için ayrı bir tarayıcı açıyor ve uzun çıktı veriyordu; paralel beş görev makinenin
belleğini bitirdi. Yerine tek bir headless Chromium daemon'ı koyduk (`playwright-core`, yaklaşık 1.100 satır):

```mermaid
flowchart LR
    subgraph CLIENTS["Çağıranlar"]
        C1["oturum, görev 1234"]
        C2["oturum, görev 1240"]
        C3["sen, terminalde"]
    end
    CL["ws browse istemcisi<br/>yerel socket"]
    subgraph D["Daemon, makine başına bir tane"]
        BR["Chromium headless shell"]
        X1["context: görev 1234<br/>sayfalar p1, p2"]
        X2["context: görev 1240<br/>sayfa p3"]
    end
    C1 --> CL
    C2 --> CL
    C3 --> CL
    CL --> D
    BR --- X1
    BR --- X2
```

- Her görev için bir context; bir oturum başka bir görevin sayfalarına dokunamaz.
- Metin çıktısı: açılışta `[eN]` referanslı bir taslak, tıklamada yalnızca fark.
- Görseller, fontlar ve analytics varsayılan olarak engelli.
- Boşta kalan sayfalar 10 dakika sonra, daemon 15 dakika sonra kapanır.

| Komut | Yakaladığı |
|---|---|
| `check <url> --locales all` | Her dilde: ham key'ler, `NaN`/`undefined`/`null`, kırık görseller, tekrarlanan satırlar, h1 sayısı, `lang` uyuşmazlığı, console/HTTP hataları, hâlâ İngilizce kalan metin, virgüllü dillerde `.` ondalık, 390px taşma (ekran görüntüsüyle) |
| `crawl <url>` | Her buton, sekme, select ve checkbox tek tek tıklanır; hatalar ve 4xx/5xx linkler listelenir |
| `numbers <url>` | Tablo ve kartlardan varlık başına sayılar, API ile karşılaştırmak için |

`ws i18n` tüm dil dosyalarında key eşliğini kontrol eder.

## Checklist

```mermaid
stateDiagram-v2
    [*] --> open: add "text" --page /path
    open --> done: done id --evidence "..."
    open --> dropped: drop id --reason "..."
    done --> open: reopen id
    dropped --> open: reopen id
    done --> [*]
    dropped --> [*]
    note right of open
        açık madde oldukça
        ws uat engeller
    end note
```

Kanıt demek URL, görünen şey ve hangi kontrolün temiz döndüğü demek. Tek başına "Bitti" sayılmaz.

## `ws uat <n>`

UAT'ye tek giriş yolu:

```mermaid
flowchart TD
    S(["ws uat 1234"]) --> C1{"açık madde var mı?"}
    C1 -- evet --> F["ENGELLENDİ<br/>sebepleri yazdır"]
    C1 -- hayır --> C2{"commit edilmemiş veya<br/>push edilmemiş iş?"}
    C2 -- evet --> F
    C2 -- hayır --> C3{"eksik dil key'i?"}
    C3 -- evet --> F
    C3 -- hayır --> B["release build"]
    B --> L["her checklist sayfası<br/>x 7 dil + mobil"]
    L --> C4{"HTTP/sayfa hatası, ham key,<br/>çevrilmemiş metin, ondalık,<br/>taşma, hatalı tıklama,<br/>kırık link?"}
    C4 -- evet --> F
    C4 -- hayır --> R["uat-report.md yaz"]
    R --> T[("ticket -> UAT")]
    T --> CM{"--comment?"}
    CM -- "evet, insan istedi" --> J["raporu Jira'ya gönder"]
    F -.->|"--force sebep<br/>yalnızca insan"| R
```

Jira'ya göndermek ve `--force` insanın kararı; CLAUDE.md, Claude'un ikisini de kendi başına yapmasını yasaklıyor.

Sırada: kapıyla geçen bir aydan sonra iadeleri aynı yöntemle yeniden etiketleyip önlenebilir payın düşüp düşmediğine bakmak.
