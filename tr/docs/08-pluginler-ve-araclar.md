# 8. Plugin'ler, skill'ler ve MCP sunucuları

## Plugin'ler

Resmi `claude-plugins-official` marketplace'inden.

| Plugin | Kullanım |
|---|---|
| superpowers | Süreç skill'leri: beyin fırtınası, planlar, sistematik debug, "bitti" demeden önce kanıt, code review |
| remember | Oturum kayıtları; başlangıçta son günlerin özeti |
| atlassian | Confluence araması, toplantı notlarından Jira görevleri, sprint özetleri |
| playwright | Görsel kontrol veya login gerektiren tarayıcı kontrolleri |

## Bu projede superpowers

```mermaid
flowchart LR
    R(["istek"]) --> Q{"küçük ve net mi?"}
    Q -- evet --> DO["yap"]
    Q -- hayır --> BS["brainstorming"]
    BS --> WP["writing-plans"]
    WP --> EX{"nasıl yürütülecek?"}
    EX -->|"adım başına sub-agent"| SD["subagent-driven-development"]
    EX -->|"bu oturum"| EP["executing-plans"]
    SD --> VC["verification-before-completion"]
    EP --> VC
    DO --> VC
    BUG(["hata"]) --> SYS["systematic-debugging"]
    SYS --> VC
```

CLAUDE.md iki varsayılanı geçersiz kılıyor: TDD adımları (yerlerine sayfa kontrolleri geliyor) ve planların
commit edilmesi (gitignore'daki bir klasöre gidiyorlar).

## Yerleşik komutlar

| Komut | Kullanım |
|---|---|
| `/code-review`, `/simplify`, `/security-review` | İnceleme, temizlik, güvenlik |
| `/fewer-permission-prompts` | Geçmiş oturumlardaki salt okunur komutlardan allowlist |
| `/hooks`, `/agents`, `/plugin` | Kurulumu kontrol etmek |

## Tarayıcılar ve MCP

```mermaid
flowchart TD
    N(["tarayıcı gerekiyor"]) --> L{"senin login'in gerekiyor mu?"}
    L -- evet --> CH["Claude in Chrome"]
    L -- hayır --> V{"görsel değerlendirme veya<br/>uzun form akışı?"}
    V -- evet --> PW["Playwright MCP"]
    V -- hayır --> WB["ws browse"]
```

Bir editör MCP sunucusu, "bu dosya" dediğinizde Claude'un aktif dosyayı, seçimi ve açık dosyaları okumasını sağlıyor.

## Durum satırı

En alttaki satırda klasör, model ve context kullanımı; böylece yeni bir oturuma ne zaman geçeceğinizi görürsünüz:

```sh
#!/bin/sh
input=$(cat)
dir=$(basename "$(echo "$input" | jq -r '.workspace.current_dir // .cwd')")
model=$(echo "$input" | jq -r '.model.display_name // empty')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
printf '%s | %s | ctx: %s%%' "$dir" "$model" "$(printf '%.0f' "${used:-0}")"
```
