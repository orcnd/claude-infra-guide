# 1. Mimari ve ilkeler

## Parça haritası

```mermaid
flowchart TB
    subgraph EXT["Dış"]
        JIRA[("Jira")]
    end

    subgraph CLI["ws CLI (tek Node betiği)"]
        direction LR
        W1["create / up / verify<br/>down / rm / clean"]
        W2["checklist / i18n / uat"]
        W3["browse<br/>check / crawl / numbers"]
        W4["board / resume"]
    end

    subgraph ROOT["~/code/project (kaynak checkout'lar)"]
        direction LR
        R1["api/  web/<br/>main'de kalır"]
        R2["legacy/  cms/<br/>paylaşılan"]
        R3["CLAUDE.md  .claude/<br/>graphify-out/"]
    end

    subgraph TASK["~/code/tasks/task-1234"]
        direction LR
        T1["api/  web/<br/>worktree'ler<br/>feature/task-1234"]
        T2["legacy  cms  CLAUDE.md  .claude<br/>symlink'ler"]
        T3[".ws/<br/>loglar, mod, checklist, rapor"]
    end

    subgraph NET["Yerel ağ"]
        direction LR
        N1["https://1234.ws.test<br/>nginx -> Next :31234"]
        N2["https://api-1234.ws.test<br/>nginx -> php-fpm"]
    end

    JIRA <--> W2
    JIRA --> W4
    W1 -->|git worktree add| T1
    W1 -->|ln -s| T2
    R2 -.-> T2
    R3 -.-> T2
    W1 -->|vhost + sunucu| NET
    T1 --> NET
    W3 -->|headless Chromium| N1
```

Claude Code her zaman `~/code/project` içinde açılır, görev klasörüne kendisi geçer ve bir insanın
çalıştıracağı `ws` komutlarının aynısını çalıştırır.

## İlkeler

| İlke | Uygulamada |
|---|---|
| Bir görev, bir alan | Görev kodu sadece `tasks/task-<n>/` altında düzenlenir. Kökteki `api/` ve `web/` main'de kalır. |
| Teşhis et, sor, sonra düzelt | Claude dosya:satır, sebep ve düzeltmeyi gösterir, sonra bekler. |
| Commit ve push'u insan yapar | Claude mesajı ve dosya listesini önerir, onay bekler. |
| Sayfayı oku, test yazma | Her değişiklik render edilmiş sayfanın ve API verisinin mantıksal kontrolüyle biter ([05](05-dogrulama-ve-uat-kapisi.md)). |
| Kanıtla kapat | Checklist maddesi sayfada görülenle kapanır. |
| Bağlamı baştan ver | Repo bilgisi rule dosyalarında, kod ilişkileri grafta; ikisine de grep'ten önce bakılır. |
| Kuralları hook'lar zorlar | Tipografi, slop ve önce graf kuralı sadece metin değil, hook. |
| Agent ve insan için tek araç | `ws` terminalde de Claude'un Bash aracında da aynı davranır; çıktısı kısa düz metin. |

## Paylaşılan ve göreve özel

```mermaid
flowchart LR
    subgraph PER["Göreve özel"]
        A["api/ worktree"]
        W["web/ worktree"]
        S["Next dev sunucusu<br/>port 30000+n"]
        L[".ws/ loglar + checklist"]
    end
    subgraph SHARED["Tüm görevlerde ortak"]
        LG["legacy/"]
        CM["cms/"]
        DB[("MySQL")]
        RD[("Redis")]
        FPM["php-fpm"]
        CFG["CLAUDE.md + .claude/"]
    end
    A --> FPM --> DB
    A --> RD
    W --> S
    LG -.symlink.-> PER
    CM -.symlink.-> PER
    CFG -.symlink.-> PER
```

| Kaynak | Kapsam | Sonuç |
|---|---|---|
| `api/`, `web/` | Göreve özel | Kendi branch'i ve sunucusu |
| `legacy/`, `cms/` | Paylaşılan | Değişiklik her görevde görünür; Claude düzenlemeden önce uyarır |
| Veritabanı, Redis, php-fpm | Paylaşılan | Migration veya cache temizliğinden önce açık görevler listelenir |
| `CLAUDE.md`, `.claude/` | Paylaşılan | Görev klasöründeki oturumlar aynı hook'ları ve agent'ları kullanır |

`legacy/` ve `cms/` worktree değil: nadiren değişiyorlar ve görev başına kurulumları pahalı
(WordPress, çok host'lu bir framework). Bu ödünleşimi kabul ettik ve uyarıyı kurala çevirdik.
