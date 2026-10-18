param([switch]$SkipWebBuild,[switch]$LocalNetwork,[switch]$Release,[switch]$Local,[string]$BackendUrl='')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$portableJava=Join-Path $PSScriptRoot '.toolchains/jdk/jdk-21.0.12.1+1'
$portableSdk=Join-Path $PSScriptRoot '.toolchains/sdk'
if (-not $env:JAVA_HOME -and (Test-Path -LiteralPath $portableJava)) {$env:JAVA_HOME=$portableJava}
if (-not $env:ANDROID_HOME -and (Test-Path -LiteralPath $portableSdk)) {$env:ANDROID_HOME=$portableSdk}
if (-not $env:JAVA_HOME -or -not $env:ANDROID_HOME) {throw '请安装 JDK 21 和 Android SDK 36，并设置 JAVA_HOME、ANDROID_HOME。见 docs/android.md。'}
$env:GRADLE_USER_HOME=Join-Path $PSScriptRoot '.toolchains/gradle'
$previousLocalMode=$env:VITE_LOCAL_PHONE_TEST
$previousBackendUrl=$env:VITE_API_BASE
function Test-PrivateIPv4([string]$HostName){
  # 局域网直连只接受私网 IPv4（10./172.16-31./192.168.），公网 HTTP 一律拒绝
  if($HostName -notmatch '^(\d+)\.(\d+)\.(\d+)\.(\d+)$'){return $false}
  $o=[int]$Matches[1];$p=[int]$Matches[2]
  if($o -eq 10 -or $o -eq 127){return $true}
  if($o -eq 172 -and $p -ge 16 -and $p -le 31){return $true}
  if($o -eq 192 -and $p -eq 168){return $true}
  return $false
}
try {
  if($Release -and $LocalNetwork){throw 'Release 包要求 HTTPS，不能启用局域网 HTTP'}
  if($Release -and $SkipWebBuild){throw 'Release 包必须重新构建网页以核对 HTTPS 配置'}
  if($Local -and -not $Release){throw '本地版发布包需要配合 -Release 使用既有发布签名'}
  if($Local -and -not $BackendUrl){throw '本地版发布包必须提供 -BackendUrl（局域网如 http://192.168.1.5:8080，或公网 https://域名）'}
  $lanHttp=$false
  if($BackendUrl){
    $backendUri=$null
    if(-not [Uri]::TryCreate($BackendUrl,[UriKind]::Absolute,[ref]$backendUri) -or $backendUri.UserInfo -or $backendUri.Query -or $backendUri.Fragment) {throw 'BackendUrl 必须是没有账号、路径或参数的完整服务地址'}
    if($backendUri.Scheme -eq 'http'){
      if(-not (Test-PrivateIPv4 $backendUri.Host)){throw 'HTTP 地址只允许局域网私网 IP（10.x / 172.16-31.x / 192.168.x）；公网地址请用 HTTPS'}
      if($backendUri.Port -eq 80 -or $backendUri.AbsolutePath -ne '/'){throw 'HTTP 地址需带端口且无路径，如 http://192.168.1.5:8080'}
      $lanHttp=$true
    }elseif($backendUri.Scheme -ne 'https' -or -not $backendUri.Host){throw 'BackendUrl 只支持 https://公网域名 或 http://局域网私网IP:端口'}
    if($SkipWebBuild){throw '设置 BackendUrl 时必须重新构建网页'}
    $env:VITE_API_BASE=$BackendUrl.TrimEnd('/')
  }
  if($LocalNetwork -and $SkipWebBuild){throw '局域网测试包必须重新构建网页，不能使用 SkipWebBuild'}
  $env:VITE_LOCAL_PHONE_TEST=if($LocalNetwork -or $lanHttp){'1'}else{'0'}
  if (-not $SkipWebBuild) {npm run build; if ($LASTEXITCODE -ne 0) {throw '前端构建失败'}}
  npx cap sync android
  if ($LASTEXITCODE -ne 0) {throw 'Android 同步失败'}
} finally {$env:VITE_LOCAL_PHONE_TEST=$previousLocalMode;$env:VITE_API_BASE=$previousBackendUrl}
Push-Location -LiteralPath (Join-Path $PSScriptRoot 'android')
try {
  $gradleTask=if($Release){'assembleRelease'}else{'assembleDebug'}
  & ./gradlew.bat $gradleTask --no-daemon --console=plain '-Pandroid.overridePathCheck=true'
  if ($LASTEXITCODE -ne 0) {throw 'APK 构建失败'}
} finally {Pop-Location}
$output=Join-Path $PSScriptRoot 'releases'
New-Item -ItemType Directory -Path $output -Force | Out-Null
$packageName=if($Release){if($Local){'Xinxin-0.1.0-local.apk'}else{'Xinxin-0.1.0-cloud.apk'}}elseif($LocalNetwork){'Xinxin-0.1.0-local-test.apk'}else{'Xinxin-0.1.0-debug.apk'}
if($Release){
  $signingPath=Join-Path $PSScriptRoot '.private/android-signing'
  New-Item -ItemType Directory -Force -Path $signingPath | Out-Null
  $signingIdentity=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
  & icacls.exe $signingPath /inheritance:r /grant:r "*${signingIdentity}:(OI)(CI)F" | Out-Null
  if($LASTEXITCODE -ne 0){throw '无法限制签名目录的本地访问权限'}
  $keystorePath=Join-Path $signingPath 'xinxin-release.p12'
  $passwordPath=Join-Path $signingPath 'password.txt'
  $keytool=Join-Path $env:JAVA_HOME 'bin/keytool.exe'
  if(-not(Test-Path -LiteralPath $keystorePath)){
    if(Test-Path -LiteralPath $passwordPath){throw '签名密码存在但密钥库缺失，请先恢复原密钥库'}
    $passwordBytes=[byte[]]::new(32)
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($passwordBytes)
    [IO.File]::WriteAllText($passwordPath,[Convert]::ToBase64String($passwordBytes))
    & $keytool -genkeypair -keystore $keystorePath -storetype PKCS12 -alias xinxin -keyalg RSA -keysize 3072 -validity 10000 -dname 'CN=Xinxin Android,O=Xinxin,C=CN' '-storepass:file' $passwordPath '-keypass:file' $passwordPath
    if($LASTEXITCODE -ne 0){throw '生成私人 Android 签名密钥失败；不要删除已有密钥后重试'}
  }
  if(-not(Test-Path -LiteralPath $passwordPath)){throw '签名密码文件缺失，请恢复私人签名备份'}
  $androidTools=Join-Path $env:ANDROID_HOME 'build-tools/36.0.0'
  $unsigned=Join-Path $PSScriptRoot 'android/app/build/outputs/apk/release/app-release-unsigned.apk'
  $aligned=Join-Path $output 'xinxin-aligned-unsigned.apk'
  & (Join-Path $androidTools 'zipalign.exe') -P 16 -f 4 $unsigned $aligned
  if($LASTEXITCODE -ne 0){throw 'APK 对齐失败'}
  $signer=Join-Path $androidTools 'apksigner.bat'
  $signed=Join-Path $output $packageName
  & $signer sign --ks $keystorePath --ks-key-alias xinxin --ks-pass "file:$passwordPath" --out $signed $aligned
  if($LASTEXITCODE -ne 0){throw 'APK 签名失败'}
  & $signer verify --verbose --print-certs $signed
  if($LASTEXITCODE -ne 0){throw 'APK 签名核验失败'}
  Remove-Item -LiteralPath $aligned
}else{
  Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'android/app/build/outputs/apk/debug/app-debug.apk') -Destination (Join-Path $output $packageName)
}
Get-FileHash -LiteralPath (Join-Path $output $packageName) -Algorithm SHA256
