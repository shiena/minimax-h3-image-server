# WindowsでH3・ComfyUI・アニメ調モデルを導入する

MiniMax H3 ImageサーバーをAPIとComfyUIから利用できるようにします。アニメ調の画像生成には、ComfyUIでAnima Turbo v1.1とAnimagine XL 4.0 Optを使用します。

確認日: 2026年11月16日。コマンドはPowerShellで実行します。初回導入はモデルのダウンロードを含め、数時間かかる場合があります。

## 基準フォルダーと配置を決める

Dドライブ上の任意のフォルダーを基準フォルダーとします。H3本体も含め、次の構成で同じ基準フォルダーに配置します。本文の配置先は、このフォルダーからの相対パスです。

```text
基準フォルダー/
├── minimax-h3-image-server/
│   ├── .venv/
│   ├── .env
│   ├── models/
│   ├── huggingface/
│   ├── uv-cache/
│   ├── temp/
│   ├── scripts/
│   └── outputs/
└── ComfyUI/
    ├── .venv/
    ├── models/
    ├── custom_nodes/
    └── output/
```

PowerShellを基準フォルダーで開いてから、各手順を開始します。コマンドは最初にH3リポジトリへ移動し、それ以降はリポジトリを作業フォルダーとして実行します。`.env`の相対パスも、H3リポジトリを基準に解決されます。

既存環境の測定は移設前の配置で実施しています。この文書の変更では、実ファイルの移動はしていません。既存環境をこの配置に移す場合は、両サーバーを停止してからソースとモデルを配置し、仮想環境は移動先で作り直してください。

## 導入した環境を起動する

以下は、上記の配置で導入した環境の起動方法です。基準フォルダーからリポジトリに移動します。

```powershell
Set-Location .\minimax-h3-image-server
```

H3とComfyUIの両方を起動する場合は、次を実行します。

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-comfyui.ps1 -ComfyRoot (Resolve-Path ..\ComfyUI).Path
```

H3 APIだけを起動する場合は、次を実行します。

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-api.ps1
```

| 用途 | URL |
|---|---|
| ComfyUI | http://127.0.0.1:8188 |
| H3 APIの操作画面 | http://127.0.0.1:8633/docs |
| H3の稼働確認 | http://127.0.0.1:8633/api/health |

スクリプトはバックグラウンドで起動し、起動済みのサーバーを再利用します。ターミナルを閉じてもサーバーは停止しません。API用スクリプトを実行しても、起動済みのComfyUIは停止しません。

`ExecutionPolicy Bypass`は、そのPowerShellプロセスだけに適用されます。両サーバーはローカルPCからのみ接続できます。

## 構成と前提条件を確認する

### モデルの実行場所

| モデル | 実行場所 | 利用方法 |
|---|---|---|
| MiniMax H3 Image | H3サーバー | ポート8633のAPI、またはComfyUIの専用ノード |
| Anima Turbo v1.1 | ComfyUI | ワークフロー、またはポート8188のComfyUI API |
| Animagine XL 4.0 Opt | ComfyUI | ワークフロー、またはポート8188のComfyUI API |

H3の専用ノードは、ローカルのH3 APIに生成を依頼します。AnimaとAnimagineはComfyUIが直接実行します。H3 APIでAnimaやAnimagineを選択する機能はありません。この構成は静止画像用です。

### 確認済みの環境

| 項目 | 構成 |
|---|---|
| OS | Windows |
| GPU | NVIDIA GeForce RTX 5070、VRAM 12GB |
| メモリ | 64GB |
| Python | 3.12.10、アプリごとに独立した仮想環境 |
| PyTorch | 2.11.0+cu130 |
| torchvision | 0.26.0+cu130 |
| ComfyUI | 0.45.0、コミット`e9afbccc2669677076feb08e52658f129cd8c12b` |
| H3リポジトリ（導入先） | `./minimax-h3-image-server` |
| H3モデル・キャッシュ（導入先） | `./minimax-h3-image-server/models`、`./minimax-h3-image-server/huggingface` |
| ComfyUI | `./ComfyUI` |

Git、uv、curl、およびCUDA 13系のPyTorchに対応するNVIDIAドライバーが必要です。次のコマンドが成功することを確認します。

```powershell
git --version
uv --version
curl.exe --version
nvidia-smi
```

### ディスク容量

以下は移設前の導入・検証後の測定値です。H3本体・仮想環境は移設前の別ドライブで測定したため、Dドライブへの配置後は割り当て容量が変わります。GiBは1,024の3乗バイトです。「ディスク上」はファイルに実際に割り当てられた容量です。

| 区分 | ファイル容量 | ディスク上の容量 |
|---|---:|---:|
| H3モデル・Hugging Faceキャッシュ | 36.36GiB | 36.41GiB |
| Animaの3ファイル | 5.24GiB | 5.24GiB |
| Animagineの1ファイル | 6.46GiB | 6.46GiB |
| **モデル合計** | **48.06GiB** | **48.12GiB** |
| H3本体・仮想環境 | 3.47GiB | 3.52GiB |
| ComfyUI本体・仮想環境 | 4.13GiB | 28.53GiB |
| **システム合計** | **7.59GiB** | **32.05GiB** |
| uvキャッシュ | 4.91GiB | 32.15GiB |
| **生成物などを含む全体** | **60.58GiB** | **112.34GiB** |

Windows、GPUドライバー、共有Python本体は集計に含めていません。H3の値には重複キャッシュや残存する元データも含まれます。

現在のDドライブはexFATで、割り当て単位が512KiBです。小さいファイルの多いPython環境やuvキャッシュで容量が膨らみます。新規配置先を選べる場合は、NTFSのSSDも候補になります。

新規導入では、一時ファイルの余裕を含めてDドライブに150GiB以上の空きを確保することを目安にしてください。これは測定した最低要件ではありません。H3の初回処理では元モデルを順番に取得・削除するため、累計ダウンロード量は100GBを超えます。

## 新規導入用の作業フォルダーを準備する

以降は、新しい環境に導入する場合の手順です。導入済みのPCで再実行する必要はありません。

この手順は、**現在の作業ツリーにある追加ファイルと修正を含むリポジトリ**を前提とします。作成時点では連携ファイルなどが未コミットです。上流リポジトリのcloneだけでは、同じ構成になりません。

現在の作業ツリーから、少なくとも次のファイルを含むソース一式を配置してください。`.venv`はコピーせず、後の手順で作成します。

- [Windows用依存関係](requirements-windows.txt)
- [Windowsで元モデルを解放する修正](app/te_quant.py)
- [API起動スクリプト](scripts/start-api.ps1)
- [ComfyUI起動スクリプト](scripts/start-comfyui.ps1)
- [モデル準備スクリプト](scripts/prepare_models.py)
- [ベンチマークスクリプト](scripts/benchmark-comfyui.py)
- [連携ノード](integrations/comfyui/minimax_h3/__init__.py)と`integrations/comfyui`内のJSONファイル

基準フォルダーでPowerShellを開き、以下を実行します。その後も同じウィンドウで導入を続けます。パスは基準フォルダーから組み立てます。作業フォルダーの変更や子プロセスの起動に備え、変数には実行時に解決したパスを保持します。

```powershell
$ErrorActionPreference = 'Stop'
$BaseRoot = (Get-Location).Path
$Repo = Join-Path $BaseRoot 'minimax-h3-image-server'
$DataRoot = $Repo
$ComfyRoot = Join-Path $BaseRoot 'ComfyUI'
Set-Location $Repo
New-Item -ItemType Directory -Force -Path "$DataRoot\models", "$DataRoot\temp", "$DataRoot\uv-cache" | Out-Null
$env:UV_CACHE_DIR = "$DataRoot\uv-cache"
$env:TEMP = "$DataRoot\temp"
$env:TMP = $env:TEMP
$env:PYTHONUTF8 = '1'
```

USBドライブを使う場合は、Dドライブとして認識されていることを先に確認します。導入中・生成中は取り外さないでください。

## H3サーバーを導入する

### Python環境を作成する

```powershell
uv venv --python 3.12.10 .venv
if ($LASTEXITCODE -ne 0) { throw 'Failed to create H3 environment.' }
uv pip install --python .venv\Scripts\python.exe -r requirements-windows.txt --index-strategy unsafe-best-match --link-mode copy
if ($LASTEXITCODE -ne 0) { throw 'Failed to install H3 dependencies.' }
uv pip check --python .venv\Scripts\python.exe
```

`--link-mode copy`は、ドライブ間やexFATでのリンク作成を避けるために指定します。インストールが完了してから次へ進みます。

### 保存先とメモリ設定を指定する

リポジトリ直下に`.env`を作成します。既存の`.env`がある場合は、内容を残したまま該当項目を編集してください。次のコマンドは既存ファイルを上書きしません。

```powershell
if (Test-Path .env) { throw 'Edit the existing .env instead of overwriting it.' }
@'
H3IMG_MODELS_DIR=./models
HF_HOME=./huggingface
HF_HUB_DISABLE_XET=1
H3IMG_TE_HOST=file
H3IMG_TRANSFORMER_HOST=file
'@ | Set-Content -Encoding utf8 .env
```

`file`設定では、モデルをファイルから読み出してRAM使用量を抑えます。

### モデルを取得して3ステップ用キャッシュを作成する

```powershell
.venv\Scripts\python.exe -u scripts\prepare_models.py --build-cache 3
if ($LASTEXITCODE -ne 0) { throw 'H3 model preparation failed.' }
```

完了メッセージと終了コード0を確認します。元モデルは分割ファイル単位で処理され、処理後に削除されます。`--keep-source`を付けると元モデルも保持するため、保存容量が大きく増えます。

この構成では3ステップを使用します。2ステップや6ステップに切り替えると、追加のキャッシュ作成や取得が発生する場合があります。

## ComfyUIを導入する

### 本体と専用Python環境を用意する

次のcloneは、`./ComfyUI`がまだ存在しない環境で実行します。既存の環境がある場合は、そのフォルダーを上書きしないでください。

```powershell
git clone https://github.com/Comfy-Org/ComfyUI.git $ComfyRoot
if ($LASTEXITCODE -ne 0) { throw 'ComfyUI clone failed.' }
git -c "safe.directory=$($ComfyRoot.Replace('\', '/'))" -C $ComfyRoot checkout e9afbccc2669677076feb08e52658f129cd8c12b
if ($LASTEXITCODE -ne 0) { throw 'ComfyUI checkout failed.' }
uv venv --python 3.12.10 "$ComfyRoot\.venv"
if ($LASTEXITCODE -ne 0) { throw 'Failed to create ComfyUI environment.' }
uv pip install --python "$ComfyRoot\.venv\Scripts\python.exe" -r "$ComfyRoot\requirements.txt" 'torch==2.11.0+cu130' 'torchvision==0.26.0+cu130' --extra-index-url https://download.pytorch.org/whl/cu130 --index-strategy unsafe-best-match --link-mode copy
if ($LASTEXITCODE -ne 0) { throw 'Failed to install ComfyUI dependencies.' }
uv pip check --python "$ComfyRoot\.venv\Scripts\python.exe"
```

H3とComfyUIでは依存パッケージの版が異なるため、仮想環境を分けます。依存関係の一部には版指定の幅があるため、将来の導入時に全パッケージが同一になることまでは保証しません。

### 連携ノードとワークフローを配置する

新規導入時に、同梱ファイルをコピーします。既存の同名ファイルを編集済みの場合は、先に別名で保存してください。

```powershell
$NodeDir = "$ComfyRoot\custom_nodes\minimax_h3"
$WorkflowDir = "$ComfyRoot\user\default\workflows"
New-Item -ItemType Directory -Force -Path $NodeDir, $WorkflowDir | Out-Null
Copy-Item integrations\comfyui\minimax_h3\*.py $NodeDir
New-Item -ItemType Directory -Force -Path "$NodeDir\web" | Out-Null
Copy-Item integrations\comfyui\minimax_h3\web\*.js "$NodeDir\web"
Copy-Item integrations\comfyui\h3-image-workflow.json "$WorkflowDir\MiniMax H3 Image.json"
Copy-Item integrations\comfyui\anima-character-workflow.json "$WorkflowDir\Anima Turbo - Anime Character.json"
Copy-Item integrations\comfyui\animagine-character-workflow.json "$WorkflowDir\Animagine XL - Anime Character.json"
Copy-Item integrations\comfyui\anima-japanese-workflow.json "$WorkflowDir\Anima - Japanese Prompt.json"
```

## アニメ調モデルを配置する

### ダウンロードと検証用の関数を定義する

同梱マニフェストのリビジョン、サイズ、SHA-256を使用します。取得途中のファイルは`.part`として保持し、再実行時に続きを取得します。

```powershell
function Get-VerifiedModel {
    param([string]$Url, [string]$Destination, [long]$Size, [string]$Sha256)
    New-Item -ItemType Directory -Force -Path (Split-Path $Destination -Parent) | Out-Null
    if (Test-Path -LiteralPath $Destination) {
        $ValidSize = (Get-Item -LiteralPath $Destination).Length -eq $Size
        $ValidHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash -ieq $Sha256
        if ($ValidSize -and $ValidHash) { return }
        throw "Existing model does not match the manifest: $Destination"
    }
    $Partial = "$Destination.part"
    curl.exe -L --fail --retry 5 --connect-timeout 20 -C - -o $Partial $Url
    if ($LASTEXITCODE -ne 0) { throw "Download failed: $Url" }
    if ((Get-Item -LiteralPath $Partial).Length -ne $Size) { throw "Size mismatch: $Partial" }
    if ((Get-FileHash -LiteralPath $Partial -Algorithm SHA256).Hash -ine $Sha256) {
        throw "SHA256 mismatch: $Partial"
    }
    Move-Item -LiteralPath $Partial -Destination $Destination
}
```

### Anima Turbo v1.1を取得する

```powershell
$Manifest = Get-Content integrations\comfyui\anima-model.json -Raw | ConvertFrom-Json
foreach ($Entry in $Manifest.files) {
    $RelativePath = $Entry.file -replace '^split_files/', ''
    $Destination = Join-Path "$ComfyRoot\models" $RelativePath
    $Url = "https://huggingface.co/$($Manifest.repo)/resolve/$($Manifest.revision)/$($Entry.file)?download=true"
    Get-VerifiedModel -Url $Url -Destination $Destination -Size $Entry.size -Sha256 $Entry.sha256
}
```

次の3ファイルが配置されます。

| フォルダー（`./ComfyUI/models`内） | ファイル |
|---|---|
| `diffusion_models` | `anima-turbo-v1.1.safetensors` |
| `text_encoders` | `qwen_3_06b_base.safetensors` |
| `vae` | `qwen_image_vae.safetensors` |

### Animagine XL 4.0 Optを取得する

```powershell
$Manifest = Get-Content integrations\comfyui\animagine-model.json -Raw | ConvertFrom-Json
$Destination = Join-Path "$ComfyRoot\models\checkpoints" $Manifest.file
$Url = "https://huggingface.co/$($Manifest.repo)/resolve/$($Manifest.revision)/$($Manifest.file)?download=true"
Get-VerifiedModel -Url $Url -Destination $Destination -Size $Manifest.size -Sha256 $Manifest.sha256
```

`./ComfyUI/models/checkpoints/animagine-xl-4.0-opt.safetensors`に配置されます。このチェックポイントにはCLIPとVAEも含まれます。

両モデルとも、配布元の利用条件を確認してください。ライセンスの参照先は[Animaのマニフェスト](integrations/comfyui/anima-model.json)にある配布元、および[Animagineのマニフェスト](integrations/comfyui/animagine-model.json)です。この構成では追加のコンテンツフィルターを実装していませんが、すべての出力やプロンプトへの対応を保証するものではありません。

## 起動して画像を生成する

### 起動と接続を確認する

```powershell
& .\scripts\start-comfyui.ps1 -ComfyRoot (Resolve-Path ..\ComfyUI).Path
Invoke-RestMethod http://127.0.0.1:8633/api/health
Invoke-RestMethod http://127.0.0.1:8188/system_stats
Invoke-RestMethod http://127.0.0.1:8188/object_info/MiniMaxH3Image
```

H3が正常応答し、ComfyUIのノード情報に`MiniMaxH3Image`が表示されれば、連携ノードを利用できます。

### ComfyUIから生成する

1. ブラウザーでhttp://127.0.0.1:8188を開きます。
2. 下表のワークフローを開きます。見つからない場合は、対応するJSONファイルを画面へドラッグします。
3. プロンプトを編集します。
4. ワークフローを実行します。
5. 保存ノードの画像を確認します。

| ワークフロー | 元ファイル | 主な設定 |
|---|---|---|
| MiniMax H3 Image | [h3-image-workflow.json](integrations/comfyui/h3-image-workflow.json) | 3ステップ、ローカルH3 API |
| Anima Turbo - Anime Character | [anima-character-workflow.json](integrations/comfyui/anima-character-workflow.json) | 832×1216、10ステップ、CFG 1、Euler／simple |
| Animagine XL - Anime Character | [animagine-character-workflow.json](integrations/comfyui/animagine-character-workflow.json) | 832×1216、28ステップ、CFG 5、Euler ancestral／normal |

Animaは英語の自然文とタグ形式を利用できます。日本語を直接入力した検証では指定に沿わなかったため、日本語は後述の翻訳ノードを使用します。Animagineは英語のタグ形式から調整すると扱いやすくなります。

AnimaのCLIPLoaderは、同梱ワークフローの`type=stable_diffusion`を使用します。独自判断で別の種類へ変更せず、まず同梱設定で確認してください。

ComfyUIの保存先は`./ComfyUI/output`です。H3 API側の生成物は`./minimax-h3-image-server/outputs`にも保存されます。

H3ノードは生成前にComfyUIのモデルを解放します。`unload_after=true`では、生成後にH3のモデルも解放します。12GBのGPUでは、両サーバーで同時に生成せず、順番に実行してください。

### H3 APIから生成する

APIだけを起動する場合も、保存先の`.env`とモデルは共通です。

```powershell
& .\scripts\start-api.ps1
$Body = @{
    mode = 't2i'
    prompt = 'An anime character standing in a sunny garden, clean line art'
    width = 1024
    height = 1024
    seed = 20261116
    steps = 3
    generation_area = 'native'
} | ConvertTo-Json
$Job = Invoke-RestMethod http://127.0.0.1:8633/api/jobs -Method Post -ContentType 'application/json' -Body $Body
$Deadline = (Get-Date).AddMinutes(30)
do {
    Start-Sleep -Seconds 2
    $Result = Invoke-RestMethod "http://127.0.0.1:8633/api/jobs/$($Job.id)"
    if ((Get-Date) -gt $Deadline) { throw "Timed out waiting for job $($Job.id)" }
} while ($Result.status -in @('queued', 'running'))
if ($Result.status -ne 'completed') { throw ($Result | ConvertTo-Json -Depth 10) }
Write-Host "http://127.0.0.1:8633$($Result.image_url)"
```

`native`では最低4MPで生成して指定サイズに縮小します。指定解像度で直接生成する場合は`requested`を指定します。

API経由の生成後、AnimaやAnimagineに切り替える場合はH3のモデルを解放します。

```powershell
Invoke-RestMethod http://127.0.0.1:8633/api/admin/unload -Method Post -ContentType 'application/json' -Body '{}'
```

生成中の解放要求には409が返ります。逆に、ComfyUIで生成した後にH3 APIを直接利用する場合は、ComfyUIの処理完了後に次を実行します。

```powershell
Invoke-RestMethod http://127.0.0.1:8188/free -Method Post -ContentType 'application/json' -Body '{"unload_models":true,"free_memory":true}'
```

### AnimaとAnimagineをAPIから利用する

ComfyUIを起動した状態で、UI用ではなく`-api.json`を送信します。次はAnimaの例です。

```powershell
$Graph = Get-Content integrations\comfyui\anima-character-api.json -Raw | ConvertFrom-Json
$Body = @{ prompt = $Graph } | ConvertTo-Json -Depth 100
$Queued = Invoke-RestMethod http://127.0.0.1:8188/prompt -Method Post -ContentType 'application/json' -Body $Body
Write-Host "http://127.0.0.1:8188/history/$($Queued.prompt_id)"
```

返された`prompt_id`で`/history/{prompt_id}`を取得します。履歴にジョブが現れたら`status.status_str`が`success`であることを確認し、`outputs`内の画像情報を参照します。Animagineでは、入力ファイルを`animagine-character-api.json`に変更します。

## 日本語の指示を英語へ変換する

追加ワークフロー[anima-japanese-workflow.json](integrations/comfyui/anima-japanese-workflow.json)では、日本語の指示をローカルLLMで英語へ変換してからAnimaへ渡します。Negativeは既存の英語設定を使用します。

現在の環境にはQwen2.5-3B-InstructのQ4_K_M版と、llama.cppのCPU版を追加しています。LLMはCPUで実行し、画像生成用のVRAMを使用しません。初回取得後の翻訳はローカルで完結します。

基準フォルダーに、次のフォルダーを追加します。モデルと実行環境の取得元は[マニフェスト](integrations/comfyui/prompt-llm-model.json)を参照してください。LLMモデルだけで約2.1GB増えます。

```text
prompt-llm/
├── runtime/llama-server.exe
├── models/qwen2.5-3b-instruct-q4_k_m.gguf
└── logs/
```

`runtime`には配布ZIPのDLLを含む全ファイルを展開します。ComfyUIと同じ基準フォルダーに配置すると、`start-comfyui.ps1`が翻訳サーバーも起動します。単独で起動する場合は、H3リポジトリから次を実行します。

```powershell
& .\scripts\start-prompt-llm.ps1 -LlmRoot ..\prompt-llm
```

1. ComfyUIの画面を再読み込みします。編集中のワークフローは先に保存してください。
2. ［Anima - Japanese Prompt］を開きます。
3. ［Japanese Prompt to English (LLM)］ノードの`instruction`に日本語の指示を入力します。
4. ワークフローを実行します。

接続先は`http://127.0.0.1:1234/v1`、モデル名は`prompt-translator`です。翻訳結果はノードの実行結果にも出力します。翻訳の誤りがある場合は、元の指示を具体的に書き直してください。同じ入力の再実行ではComfyUIのキャッシュが使われる場合があります。

翻訳ノード内の［Last translated Positive Prompt］に、最後に翻訳された英文を表示します。この欄は閲覧・コピー用です。日本語を編集しただけでは更新されず、再実行で翻訳結果を受け取ると更新されます。拡張機能を追加した後は、編集中のワークフローを保存してからブラウザーを再読み込みしてください。

日本語ワークフローの［Save Image with Positive Prompt］は、実際に使用した英文をPNGの`positive_prompt`項目にも保存します。保存したPNGをComfyUIへドラッグすると、［Saved Positive Prompt］メモで英文を確認できます。元の日本語とワークフローも引き続き保存されます。

このメモは記録用です。再実行時の翻訳を固定するものではありません。保存した英文をそのまま再利用する場合は、Positiveのテキスト入力への接続を外してウィジェットへ戻し、メモの英文を貼り付けます。保存ノードの`positive_prompt`にも同じ英文を渡してください。

更新前のPNGには英文をさかのぼって追加できません。既に開いているワークフローでは、通常のSaveImageを新しい保存ノードに置き換え、翻訳ノードの`english_prompt`を`positive_prompt`にも接続します。更新済みJSONを開き直しても利用できます。ComfyUIを`--disable-metadata`で起動すると、これらの設定は保存されません。

## 動作と性能を検証する

同梱スクリプトは、モデル解放後と、モデルを保持した状態で各1回生成します。実行前に、ほかの生成ジョブが終わっていることを確認してください。

```powershell
.venv\Scripts\python.exe scripts\benchmark-comfyui.py integrations\comfyui\anima-character-api.json --output outputs\benchmark-anima.json
.venv\Scripts\python.exe scripts\benchmark-comfyui.py integrations\comfyui\animagine-character-api.json --output outputs\benchmark-animagine.json
```

現在のPCでの測定結果は次のとおりです。解像度832×1216、バッチ数1、同一プロンプトで比較しました。

| モデル | モデル解放後 | モデル保持時 | GPU全体のピークVRAM（解放後／保持時） |
|---|---:|---:|---:|
| Anima Turbo v1.1 | 16.09秒 | 4.08秒 | 10.89／9.58GiB |
| Animagine XL 4.0 Opt | 16.20秒 | 9.14秒 | 10.87／10.90GiB |

VRAMは`nvidia-smi`で250msごとに測定したGPU全体の値です。他アプリや表示用の使用量を含み、モデル単体の必要VRAMではありません。解放後の測定でも、OSのディスクキャッシュは消去していません。保持時はシードを変更しています。

H3は1024×1024出力、`native`、3ステップで約62〜71秒でした。内部解像度と生成方式が異なるため、上表とは直接比較できません。

## 問題を解決する

| 症状 | 確認・対処 |
|---|---|
| Dドライブやモデルが見つからない | ドライブ文字と`.env`を確認します。ComfyUIの配置先を変えた場合は`start-comfyui.ps1 -ComfyRoot (Resolve-Path ..\ComfyUI).Path`のように指定します。 |
| モデル名が選択肢にない | ファイル名と配置先を確認し、生成処理の完了後にComfyUIを再起動します。 |
| DLLやPythonモジュールの読み込みに失敗する | パッケージ導入が終了コード0で完了したことと、各アプリ専用のPythonを使用していることを確認します。 |
| VRAM不足になる | 両アプリの生成を同時に実行せず、前のモデルを解放します。バッチ数は1で確認します。 |
| H3ノードが見つからない | `custom_nodes\minimax_h3\__init__.py`と`logs\comfy.stderr.log`を確認します。コピー後はComfyUIの再起動が必要です。 |
| 起動がタイムアウトする | リポジトリ内の`logs`を確認します。ポート8188または8633を別アプリが使用していないか確認します。 |
| ダウンロードのハッシュが一致しない | 対象ファイル名とマニフェストを確認します。不一致ファイルを別名で退避してから、取得をやり直します。 |

### Gitに「dubious ownership」と表示される

exFAT上のuvキャッシュでdiffusersの取得が失敗する場合は、次の設定をそのPowerShellセッションに適用してから、H3の依存関係を再インストールします。

```powershell
$env:GIT_CONFIG_COUNT = '1'
$env:GIT_CONFIG_KEY_0 = 'safe.directory'
$CacheRoot = (Resolve-Path .\uv-cache).Path.Replace('\', '/')
$env:GIT_CONFIG_VALUE_0 = "$CacheRoot/git-v1/*"
```

既存の`GIT_CONFIG_*`環境変数を使っている場合は、上書きせず設定を統合してください。信頼対象はこのキャッシュ配下に限定しています。ComfyUIのGit操作には、前述の`git -c "safe.directory=$($ComfyRoot.Replace('\', '/'))"`を使用します。

### H3の準備中に元ファイルを削除できない

`app/te_quant.py`にWindows向けの修正が含まれているか確認します。保持するテンソルを`copy=True`で複製し、元ファイルへの参照を解放する変更が必要です。このガイドと一緒に、現在の修正済みファイルを移してください。

### サーバーを停止する

バックグラウンド起動したサーバーは、ターミナルのCtrl＋Cでは停止しません。まずジョブ完了を確認し、次のコマンドでポートを使用するプロセスを調べます。

```powershell
Get-NetTCPConnection -State Listen -LocalPort 8188, 8633 |
    Select-Object LocalAddress, LocalPort, OwningProcess
```

起動スクリプトに対応する停止スクリプトを、H3リポジトリから実行します。停止はプロセスの終了です。生成中に実行すると処理が中断されるため、先にジョブの完了を確認してください。

| 起動 | 停止 | 停止対象 |
|---|---|---|
| `start-api.ps1` | `stop-api.ps1` | H3 APIのみ |
| `start-comfyui.ps1` | `stop-comfyui.ps1` | ComfyUI、H3 API、翻訳LLM |
| `start-prompt-llm.ps1` | `stop-prompt-llm.ps1` | 翻訳LLMのみ |

```powershell
& .\scripts\stop-comfyui.ps1 -ComfyRoot ..\ComfyUI
```

個別に停止する場合は、次のいずれかを実行します。

```powershell
& .\scripts\stop-api.ps1
& .\scripts\stop-prompt-llm.ps1 -LlmRoot ..\prompt-llm
```

`-WhatIf`を付けると、停止対象の確認だけを実行します。

```powershell
& .\scripts\stop-comfyui.ps1 -ComfyRoot ..\ComfyUI -WhatIf
```

停止スクリプトは、待ち受けポートとプロセスの実行内容を確認します。PIDファイルだけを根拠に終了しません。対象が停止済みなら何も終了せず、別のプロセスが同じポートを使用していればエラーにします。起動時に再利用した既存サーバーも停止対象です。再起動時は、対応する起動スクリプトを実行します。

## 関連ファイル

- [H3リポジトリのREADME](README.md)
- [Animaの固定リビジョン・SHA-256](integrations/comfyui/anima-model.json)
- [Animagineの固定リビジョン・SHA-256](integrations/comfyui/animagine-model.json)
- [ComfyUI連携ノードの実装](integrations/comfyui/minimax_h3/__init__.py)
