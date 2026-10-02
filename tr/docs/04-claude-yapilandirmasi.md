# 4. Claude Code yapılandırması

## Katmanlar

| Katman | Dosya | Ne zaman yüklenir | İçerik |
|---|---|---|---|
| Kullanıcı | `~/.claude/CLAUDE.md` | Her oturumda | Kişisel skill tetikleyicileri |
| Proje | `<root>/CLAUDE.md` | Kökte açılan oturumlarda | Repo haritası, yasaklar, süreçler, tipografi, doğrulama politikası |
| Repo | `web/CLAUDE.md` vb. | O repodaki bir dosyaya dokunulunca | Kısa repo kuralları, repoda commit'li |
| Rule | `.claude/rules/*.md` | `paths:` ile eşleşen bir dosya okununca | Klasör yapısı, DB, helper'lar, endpoint'ler, kod standartları |
| Komut | `.claude/commands/*.md` | `/command` | Adım adım akışlar |
| Agent | `.claude/agents/*.md` | Claude iş devredince | Kendi context'i olan bir uzman |
| Skill | `~/.claude/skills/*/SKILL.md` | Açıklaması isteğe uyunca | Tetiklenen bilgi paketi |
| Hook | `.claude/settings.json` | Araç çağrılarının etrafında, yanıt sonunda | Zorunlu kontroller |
| Memory | `~/.claude/projects/<project>/memory/` | Her oturumda (index) | Düzeltmelerden öğrenilen tercihler |

```mermaid
flowchart TD
    S(["oturum kökte başlar"]) --> L1["~/.claude/CLAUDE.md"]
    L1 --> L2["kök CLAUDE.md"]
    L2 --> L3["memory index"]
    L3 --> L4["skill + agent tek satırlık açıklamaları"]
    L4 --> R{"Claude bir dosya okur"}
    R --> P{"bir rule'un paths'iyle eşleşiyor mu?"}
    P -- evet --> RL["rule dosyasını yükle"]
    R --> RC{"repoda CLAUDE.md var mı?"}
    RC -- evet --> RCL["onu yükle"]
    L4 --> SK{"istek bir skill'e uyuyor mu?"}
    SK -- evet --> SKL["SKILL.md'nin tamamını yükle"]
    L4 --> AG{"devretmeli mi?"}
    AG -- evet --> AGL["alt agent, kendi context'i,<br/>sadece bulguları döndürür"]
```

Pratik kural: kısa ve kesin olan CLAUDE.md'ye, uzun referans `rules/` altına. Repo referansını rule dosyalarına
taşıyınca frontend oturumları PHP standartlarını yüklemeyi bıraktı.

## Kök CLAUDE.md

Şablon: [templates/CLAUDE.md](../../templates/CLAUDE.md).

| Bölüm | Amaç |
|---|---|
| Codebase overview | Dört repo, rolleri, rule'ların yeri |
| Git | Kök bir repo değil; her zaman `git -C <repo>` |
| Typography | Em/en dash yok; slop listesine işaret |
| Verification: no tests | Sayfayı oku; skill'lerdeki TDD adımlarını geçersiz kılar |
| Never without confirmation | Bug fix, commit, push, tablo silme, altyapı değişikliği |
| Always safe | Arama, okuma, statik analiz, cache temizliği |
| Output | Raporlar, tek seferlik betikler ve AI planları için gitignore'daki klasörler |
| Processes | Çalışma alanları, `start task`, checklist ve UAT, `stop task` |
| Code graph | Grep'ten önce graf sorgusu |

Yasakları liste halinde yazın ve her kurala tek satırlık bir gerekçe verin; Claude sebebini bilince kenar durumlarda daha iyi karar veriyor.

## Yol bazlı rule'lar

```markdown
---
paths:
  - "web/**"
---
# web/ - Next.js frontend
```

Repo başına bir tane, bir de ortak güvenlik incelemesi dosyası. Örnek: [templates/.claude/rules/web.md](../../templates/.claude/rules/web.md).

Bizim kurulumumuzda, oturum kökü dışındaki dosyalarda (bir görev worktree'si) rule'lar her zaman otomatik yüklenmedi. CLAUDE.md, Claude'a
oradaki ilk düzenlemesinden önce eşleşen rule'u tam yoluyla okumasını söyler.

## Komutlar, agent, skill

| Ad | Tür | İş |
|---|---|---|
| `/start-task <n>` | Komut | Çalışma alanı, ticket, bağlam için durma, checklist |
| `/stop-task [n]` | Komut | Sunucuyu durdur, commit'lenmemiş işi işaretle, özet, çıkış |
| `page-logic-verifier` | Agent (salt okuma, daha küçük model) | Sayfayı ve API verisini okur, tutarsızlıkları raporlar |
| `status` | Skill | `ws board` ile "durum ne" |

Agent sayfa dökümlerini, ekran görüntülerini ve JSON'u ana oturumun dışında tutar; geriye sadece bulgular döner:

```mermaid
sequenceDiagram
    participant M as Ana oturum
    participant A as page-logic-verifier
    participant B as ws browse
    participant API as Görev API'si

    M->>A: /products, /tr/products doğrula
    A->>B: check --locales all
    B-->>A: ham anahtarlar, NaN, taşma, çevrilmemiş metin
    A->>B: crawl
    B-->>A: başarısız tıklamalar, kırık linkler
    A->>API: curl endpoint (?language=tr)
    API-->>A: JSON
    A->>B: numbers
    B-->>A: varlık başına sayılar
    A->>A: kart, tablo, grafik ve API karşılaştırması
    A-->>M: bulgular: nerede, ne, neden, kaynak
```

Skill `description` alanına göre seçilir; oraya insanların gerçekte yazdığı ifadeleri, kullandıkları her dilde koyun.

## Hook'lar

```mermaid
sequenceDiagram
    participant C as Claude
    participant H as Hook'lar
    participant T as Araç

    C->>H: PreToolUse (Grep, Glob, Read, Bash)
    H-->>C: "graf var: önce onu sorgula"
    C->>H: PreToolUse (git commit -m ...)
    alt mesajda slop var
        H-->>C: reddet, ifadeleri listele
    else temiz
        H->>T: çalıştır
    end
    C->>T: Edit / Write
    T-->>H: PostToolUse (eklenen satırlar)
    H-->>C: bulgular, Claude yeniden düzenler
    C->>H: Stop (son yanıt)
    H-->>C: bulgular, yanıt yeniden yazılır
```

Şablon: [templates/.claude/settings.json](../../templates/.claude/settings.json). Yollar `$CLAUDE_PROJECT_DIR` kullanır.

## Memory

- Yerleşik memory: dosya başına bir bilgi, her oturumda yüklenen bir index. Örnekler: "onay olmadan asla commit atma",
  "test yok, sayfayı oku", "fazladan satırı bulunduğu sırayı uzatan kartı işaretle". Sadece koddan anlaşılamayanı saklayın.
- remember plugin'i: oturum günlükleri; başlangıçta son günlerin özeti enjekte edilir.

## İzinler ve auto mode

| Dosya | Kapsam | İçerik |
|---|---|---|
| `.claude/settings.json` | Proje, paylaşılan | Salt okunur komutlar ve hook'lar |
| `.claude/settings.local.json` | Kişisel | Onaylar burada birikir, token'lar dahil. Asla paylaşmayın. |
| `~/.claude/settings.json` | Kullanıcı | Okuma izinleri, plugin'ler, status line, `autoMode` |

Auto mode'da `autoMode.environment` sınıflandırıcıya hangi alan adlarının güvenilir olduğunu, neyin production sayıldığını
ve gizli bilgilerin nerede durduğunu söyler; `soft_deny` force push'u ve production config yazımını yeniden onaya düşürür.

Paylaşılan allowlist'leri dar tutun. Sınırsız `Read` ile kısıtsız `curl` GET birlikte olunca bir prompt injection
bir gizli bilgiyi okuyup kimse istemeden bir URL içinde dışarı gönderebilir.
