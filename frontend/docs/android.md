# Android 构建与安装

Capacitor 8.5.3，包名 `com.xinxin.personal`。需要 JDK 21、Android SDK 36、Build Tools 36.0.0。便携工具链可放在 Git 忽略的 `.toolchains/`，不必改动系统 Java/SDK 设置。

依据：[Capacitor Android](https://capacitorjs.com/docs/android)、[Capacitor 8 要求](https://capacitorjs.com/docs/updating/8-0)、[Microsoft OpenJDK](https://learn.microsoft.com/en-us/java/openjdk/download)、[Android SDK 工具](https://developer.android.com/studio)。

## 调试包（本机联调）

```powershell
$env:JAVA_HOME='<JDK21目录>'
$env:ANDROID_HOME='<AndroidSDK目录>'
./build-android.ps1
```

输出 `releases/Xinxin-0.1.0-debug.apk`，用于个人侧载测试，不上传应用商店。

## 局域网发布包（日常使用）

```powershell
./build-android.ps1 -Local -Release -BackendUrl 'http://192.168.1.5:8080'
```

`192.168.1.5` 换成自己电脑的局域网 IP，`8080` 换成本机网关端口（与根目录 `Start-Xinxin-Local.ps1 -GatewayPort` 一致）。脚本会自动：

- 校验地址：HTTP 只允许私网 IPv4（10.x / 172.16–31.x / 192.168.x），必须带端口且无路径；公网地址必须用 HTTPS
- 执行类型检查与生产构建、`cap sync`、Release 构建、zipalign、签名与签名核验
- 打开 WebView 混合内容放行（`allowMixedContent`），否则手机端无法请求局域网 HTTP 后端

输出 `releases/Xinxin-0.1.0-local.apk`，使用你自己的发布签名。

## 签名

发布签名在忽略目录 `.private/android-signing/` 首次创建：RSA3072 / PKCS12，随机密码且仅当前 Windows 用户可访问；之后始终复用。请私下备份密钥库与密码文件，两者都不能丢失、提交 Git 或公开。发布包关闭调试、清文与系统备份，minSdk24 / targetSdk36。

旧调试包与发布包签名不同，包名同为 `com.xinxin.personal`；首次安装发布包需先卸载调试版，手机端设置和令牌会清除，服务器资料保留。后续同发布签名可覆盖更新。

## 手机使用

1. 电脑运行 `./Start-Xinxin-Local.ps1`（网关默认 8080）。
2. 手机与电脑连同一个可信 Wi-Fi，打开 Xinxin，在连接页填 `http://<电脑局域网IP>:8080`（已预填的包可跳过）。
3. 用主人账号登录（与电脑端同一账号密码）。

手机的 localhost 指手机自己，不能用它连接电脑。不需要在 APK 中填模型密钥；密钥只留在后端。局域网 HTTP 仅供可信网络使用；要从外网访问请改用 HTTPS 域名方案。

应用仅需网络权限，系统备份已关闭。认证留在应用私有存储；私人资料和服务器/模型密钥留后端。原生壳使用 APK 内置网页，不再注册 PWA Service Worker；旧壳的注册在进入新版后解除，防止安装包更新被网页缓存遮住。
