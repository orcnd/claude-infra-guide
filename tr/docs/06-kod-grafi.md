# 6. Kod grafı (graphify)

## Neden

Dört repo, PHP ve TypeScript, repolar arası çağrılar (frontend servisi -> API route -> controller -> tablo).
Claude her soru için grep yapıp onlarca dosya okuyordu. [graphify](https://pypi.org/project/graphifyy/) AST'den
bir graf kuruyor (burada yaklaşık 9 bin node, 25 bin edge) ve Claude yalnızca ilgili alt grafı çekiyor.

```mermaid
flowchart LR
    subgraph BEFORE["Graf olmadan"]
        Q1["soru"] --> G1["grep"] --> R1["10-30 dosya oku"] --> G2["yine grep"] --> A1["cevap,<br/>context'in çoğu harcanmış"]
    end
    subgraph AFTER["Grafla"]
        Q2["soru"] --> GQ["graphify query"] --> SG["file:line içeren alt graf"] --> RF["2-4 dosya oku"] --> A2["cevap"]
    end
```

## Kurulum

```bash
uv tool install graphifyy
graphify install --platform claude        # /graphify skill
cd ~/code/project && graphify update .    # AST only, no LLM cost
```

`.graphifyignore` WordPress'i, vendor kodunu, görselleri ve minify edilmiş dosyaları dışarıda tutuyor. Minify
edilmiş dosyalar grafı tek harfli sembollerle dolduruyordu, ilk onlar çıkarıldı.

## Sorgular

```mermaid
flowchart TD
    Q{"soru tipi"} -->|"X nasıl çalışıyor"| A["graphify query ... --budget 4000"]
    Q -->|"bu sembol ne"| B["graphify explain Symbol"]
    Q -->|"A ile B nasıl bağlı"| C["graphify path A B"]
    Q -->|"değiştirirsem ne bozulur"| D["graphify affected Symbol"]
    A --> R{"yeterli mi?"}
    B --> R
    C --> R
    D --> R
    R -- evet --> E["adı geçen dosyaları oku"]
    R -- hayır --> F["hedefli grep"]
```

- Varsayılan 2000 token'lık bütçe mimari cevapları kısa kesiyor; 4000 kullanın.
- `trim` ve `json_decode` gibi builtin'ler geniş sorguları boğuyor; `explain` ve `path` odaklı kalıyor.
- Kaynak dosyası olmayan node'lar builtin'dir.

## Claude'u yönlendirmek

- CLAUDE.md: kod soruları için önce graf.
- Bir hook (`graphify hook-guard`), `Grep`, `Glob`, `Read` veya `Bash` içinde bir aramadan önce Claude'a hatırlatıyor.
- Graf komutları onay istemiyor.

## Güncel tutmak

```mermaid
sequenceDiagram
    participant D as Geliştirici veya Claude
    participant G as git
    participant H as post-commit hook
    participant GR as graphify

    D->>G: commit
    G->>H: hook'u çalıştır
    H-)GR: graphify update . (arka planda)
    H-->>G: exit 0
    G-->>D: bitti, bekleme yok
    GR->>GR: değişen dosyaları yeniden çıkar
```

Şablon: [templates/git-hooks/post-commit](../../templates/git-hooks/post-commit).
