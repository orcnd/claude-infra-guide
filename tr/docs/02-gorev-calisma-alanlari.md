# 2. Görev çalışma alanları ve `ws` CLI

## Hedef

`ws create 1234` yaklaşık iki dakikada şunları verir:

- `api/` ve `web/` için `feature/task-1234` branch'leri ve worktree'ler,
- görev klasöründe env dosyaları,
- `https://1234.ws.test:8443` (frontend) ve `https://api-1234.ws.test:8443` (API),
- `ws up 1234` sonrası, sadece o göreve ait bir Next dev sunucusu.

Kaynak checkout'lar hiç değişmez. Beş görev yan yana çalışabilir.

## `ws create`

```mermaid
sequenceDiagram
    autonumber
    actor U as Kullanıcı veya Claude
    participant WS as ws CLI
    participant G as git
    participant FS as Görev klasörü
    participant N as nginx

    U->>WS: ws create 1234
    WS->>WS: dir = tasks/task-1234<br/>port = 30000 + 1234
    WS->>G: fetch main
    WS->>G: worktree add .../api -b feature/task-1234
    WS->>G: worktree add .../web -b feature/task-1234
    WS->>FS: legacy, cms, CLAUDE.md, .claude için symlink
    WS->>FS: .env.local ve görev metadata'sını yaz
    WS->>N: servers/task-1234.conf yaz
    WS->>N: nginx -t
    alt test geçer
        WS->>N: nginx -s reload
    else test başarısız
        WS->>N: dosyayı sil, reload yok
        WS-->>U: nginx hatası
    end
    WS-->>U: yol + URL'ler
```

## Yönlendirme

```mermaid
flowchart LR
    B["Tarayıcı veya<br/>ws browse"] -->|1234.ws.test| D["dnsmasq<br/>*.ws.test -> 127.0.0.1"]
    D --> N["nginx :8443<br/>mkcert *.ws.test sertifikası"]
    N -->|1234.ws.test| F["Next sunucusu<br/>127.0.0.1:31234"]
    N -->|api-1234.ws.test| P["php-fpm :9000<br/>root = task-1234/api/public"]
    F -->|sunucu tarafı fetch| N
    P --> DB[("paylaşılan MySQL")]
```

| Parça | Nasıl | Not |
|---|---|---|
| Kod | Repo başına `git worktree add` | `node_modules` worktree başına; en yavaş adım ilk kurulum |
| Paylaşılan repolar | `legacy`, `cms`, `CLAUDE.md`, `.claude` için symlink | `.claude` olmazsa görev klasöründeki oturum hook'ları ve agent'ları kaybeder |
| Port | `30000 + görev numarası` | Çakışma yok, akılda tutulacak bir şey yok |
| DNS | dnsmasq `address=/ws.test/127.0.0.1` | Bir kez kurulur |
| HTTPS | `*.ws.test` için mkcert wildcard | Tarayıcılar https sayfadan http API'ye XHR'ı engeller; Node `NODE_EXTRA_CA_CERTS` ile güvenir |
| Yönlendirme | Görev başına bir nginx vhost | `nginx -t` başarısız olursa geri alınır |
| API | nginx -> paylaşılan php-fpm, root görev worktree'sinde | Süreç paylaşılan, kod göreve özel |
| Süreç | Detached Next sunucusu; pid ve mod `.ws/` altında | `.ws/server.log`, `.ws/build.log` |
| Bellek | Her `next dev`'e enjekte edilen Turbopack bellek sınırı | Çok görev açıkken makine kullanılabilir kalır |

Şablon: [templates/nginx/task-vhost.conf.example](../../templates/nginx/task-vhost.conf.example).

## Sunucu modları

`next dev` minify, statik üretim ve ISR adımlarını atlar; bu yüzden bir sayfa dev'de geçip release build'de
kırılabilir. Tüm modlar aynı URL'yi kullanır:

```mermaid
stateDiagram-v2
    [*] --> stopped
    stopped --> dev: ws up n
    dev --> verify: ws verify n<br/>(next build, bundle sunulur)
    verify --> verify: ws rebuild n
    verify --> dev: ws verify n --end
    stopped --> prod: ws up n --prod
    prod --> prod: ws rebuild n
    dev --> stopped: ws down n
    verify --> stopped: ws down n
    prod --> stopped: ws down n
    stopped --> [*]: ws rm n<br/>(branch'ler kalır)

    note right of verify
        Derlenmiş bundle.
        Düzenlemeler rebuild'e kadar görünmez.
        ws ls MODE = verify gösterir.
    end note
```

Dev saniyeler içinde açılır ve kaydedince yenilenir; build 1-3 dakika sürer ve push'tan önce bir kez kullanılır.
`verify`, `--end` ile dev'e dönen bir kontrol oturumudur; `prod` durdurulana kadar release build sunar.
`ws rebuild` hangi build modu çalışıyorsa onu yeniden derler.
Build'de source map'ler açık kalır.

## Komutlar

| Grup | Komutlar |
|---|---|
| Çalışma alanı | `setup`, `create`, `up`, `verify [--end]`, `rebuild`, `down`, `ls`, `rm`, `clean` |
| Jira | `config` (token işletim sistemi keychain'inde), `jira`, `board`, `resume`, `export` |
| Kalite | `checklist`, `i18n`, `uat` |
| Tarayıcı | `browse open/click/type/eval/shot/check/crawl/numbers` |

Tasarım kararları:

- Tek Node betiği, tarayıcı daemon'ı dışında npm bağımlılığı yok. Kurulum = symlink.
- Numara verilmezse görev branch adından (`feature/task-<n>`) çıkarılır.
- `setup` root gerektiren adımları çalıştırmak yerine yazdırır.
- `rm` branch'leri tutar, sonradan eklediğiniz dosyaları arşivler.
- `resume` iade edilen bir ticket'ı ve onunla ilgili eski bir oturumu seçtirir, yeni bir sekmede `claude --resume <id>` çalıştırır.

### `ws clean`

```mermaid
flowchart TD
    S["her çalışma alanı"] --> Q1{"Jira'da Done mı?"}
    Q1 -- hayır --> K1["tut: açık"]
    Q1 -- evet --> Q2{"commit'lenmemiş dosya?"}
    Q2 -- evet --> K2["tut: kirli"]
    Q2 -- hayır --> Q3{"merge veya rebase<br/>sürüyor mu?"}
    Q3 -- evet --> K3["tut: git meşgul"]
    Q3 -- hayır --> Q4{"tüm commit'ler<br/>push'lanmış mı?"}
    Q4 -- hayır --> K4["tut: push'lanmamış"]
    Q4 -- evet --> D["worktree, vhost, klasörü sil<br/>ekstraları arşivle, branch'leri tut"]
```

### `ws board`

Tek bir JSON; Claude "durum ne" sorusuna tek çağrıyla cevap verir:

```mermaid
flowchart LR
    J["Jira: assignee = ben,<br/>Done değil"] --> M["ticket numarasına<br/>göre birleştir"]
    W["çalışma alanı metadata'sı<br/>+ pid + mod"] --> M
    G["worktree başına git status"] --> M
    C["~/.claude/projects/*.jsonl<br/>ticket anahtarını grep'le"] --> M
    M --> O["önce UAT'den dönenler,<br/>sonra statü, sonra güncellenme"]
```

## Uyarlarken

- Port tabanını ve TLD'yi ortam değişkeni yapın.
- Sadece sık değişen repoları worktree yapın.
- Env dosyalarını CLI yazsın; elle kopyalananlar ilk kırılan olur.
- Her görevin loglarını tek klasörde symlink'leyin (`tasks/.logs/`), Claude nereye bakacağını bilsin.
