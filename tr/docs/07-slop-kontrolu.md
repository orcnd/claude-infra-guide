# 7. Slop kontrolü

## Sorun

Claude'un yazdığı metin commit'lere, PR'lara, yorumlara, arayüz metnine ve 7 dildeki çevirilere giriyor. Tanıdık
yapay zeka kalıpları (`delve`, `seamless`, `leverage`, "not only X but also Y", em dash'ler, kalın başlıklı maddeler)  <!-- slop-ok -->
metni kimsenin okumadığını gösteriyor. CLAUDE.md'deki yasaklı kelime listesi uzun oturumlarda tutunamadı.

## Çözüm

Bağımlılığı olmayan bir Python script'i ve bir kural dosyası ([templates/.claude/slop/](../../templates/.claude/slop/)),
üç hook tarafından çalıştırılıyor:

| Hook | Kontrol ettiği | Sonuç |
|---|---|---|
| PostToolUse `Edit\|Write\|MultiEdit` | Yalnızca eklenen satırlar. Kodda yorumlar; `.md`, `.txt`, `.html` ve çeviri dosyalarında tüm metin | Claude yeniden düzenler |
| PreToolUse `Bash` | `git commit`, `gh pr` mesajları | Komut reddedilir |
| Stop | Son cevap | Cevap yeniden yazılır |

```mermaid
flowchart TD
    IN(["payload veya dosya"]) --> P{"atlanan yol mu?<br/>vendor, build, minify"}
    P -- evet --> OK(["exit 0"])
    P -- hayır --> K{"girdi"}
    K -->|"metin dosyası veya çeviriler"| PR["her satır"]
    K -->|"kod dosyası"| CM["yalnızca yorumlar"]
    K -->|"düzenleme"| AD["yalnızca eklenen satırlar"]
    K -->|"commit mesajı, cevap"| TX["metnin kendisi"]
    PR --> MD["kod bloklarını, satır içi kodu<br/>ve URL'leri boşalt"]
    CM --> MD
    AD --> MD
    TX --> MD
    MD --> LN["her satır"]
    LN --> SO{"slop-ok?"}
    SO -- evet --> LN
    SO -- hayır --> ST["yapı: tireler,<br/>kalın başlıklı maddeler, emoji maddeler"]
    ST --> RX["regex kuralları,<br/>tüm dil bölümleri"]
    RX --> FD["bulgular (en fazla 15)"]
    FD --> M{"SLOP_MODE"}
    M -->|"block (varsayılan)"| BL["yeniden yaz / reddet"]
    M -->|warn| WR["yalnızca raporla"]
```

Çalışma anındaki LLM çıktısı (makine çevirisi, içerik üreten plugin'ler) kapsam dışında.

## Kurallar

```
[en]
leverag(e|es|ed|ing) => "use"
not only\b.{0,60}\bbut also => say both things plainly
```

`<regex> => <hint>`, büyük/küçük harf duyarsız. Kelime sınırı yalnızca başa ekleniyor, böylece ekler yine
eşleşiyor (Türkçe ve Almanca için işe yarıyor). Bölümler: `[en] [tr] [de] [es] [fr] [it] [pt]`. İpuçları eş
anlamlı bir kelime değil, sade bir yeniden yazım istiyor. Bir kalıbı iki kez gördükten sonra kural ekleyin;
sürekli yanlış alarm veriyorsa kaldırın.

## Kullanım

```bash
python3 .claude/slop/slop_check.py draft.md        # exit 1 = findings
pbpaste | python3 .claude/slop/slop_check.py -      # stdin
python3 .claude/slop/slop_check.py --json file.md
```

Doğrulama agent'ı render edilmiş sayfa metnini de bundan geçiriyor. Yanlış alarm: satıra `slop-ok` ekleyin.
Yalnızca uyarı için: `SLOP_MODE=warn`.
