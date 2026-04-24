



###### 260423

* 10:55
* 现在我是能用你的, 我只是在.zshrc配了你的key, 但是, 我在家里面却不能用你, 我也已经uv更新过你了. 但是, 依旧提示我账户不行, 我之前在家里是扫码登录的, 现在也配了.zshrc, 为啥不行呢? 他好像还在认之前的扫码登录, 没有认我配在.zshrc的key



1. *运行* ***kimi --version\*** *确认 CLI 版本*
2. *运行* ***echo $KIMI_API_KEY\*** *确认环境变量生效*
3. *查看* ***~/.kimi/config.toml\*** *的内容*
4. *如果有 OAuth 残留，可能需要删除* ***~/.kimi/config.toml\*** *或者修改 provider 配置*
5. *或者使用* ***/logout\*** *命令退出 OAuth 登录*
6. *或者直接指定* ***--config\*** *参数使用 API key*



 ***问题分析：\***



1. *用户在家里电脑上之前通过* ***/login\*** *扫码登录（OAuth 授权）*
2. *现在在* ***.zshrc\*** *里配置了* ***KIMI_API_KEY\***
3. *但 Kimi CLI 似乎还在使用旧的 OAuth 认证，提示账户问题*



 ***可能的原因：\***



1. ***OAuth 配置残留\****：之前扫码登录会在* ***~/.kimi/config.toml\*** *中保存 OAuth 相关的 pr*

   *der 配置。环境变量* ***KIMI_API_KEY\*** *只能覆盖* ***api_key\*** *字段，但如果 OAuth 使用的*

   *一种认证机制（比如 access token / refresh token），环境变量可能无法覆盖。*

2. ***环境变量未生效\****：****.zshrc\*** *修改后没有* ***source ~/.zshrc\****，或者是在非交互式 shell*

   *行。*

3. ***配置优先级问题\****：根据文档，环境变量优先级最高，但这可能取决于 provider 的类*

   *如果 OAuth 登录创建的 provider 类型和环境变量覆盖的机制不完全匹配，可能会有*

   *题。*



*我需要告诉用户排查步骤：*



1. *先确认环境变量是否真的生效：****echo $KIMI_API_KEY\***
2. *查看* ***~/.kimi/config.toml\*** *的内容，特别是 provider 配置*
3. *如果里面有 OAuth 相关的 token 或* ***type = "kimi"\*** *但使用 OAuth，可能需要：*

  *• 删除或修改* ***~/.kimi/config.toml\*** *中的 provider 配置，改为使用* ***api_key\***

  *• 或者使用* ***/logout\*** *命令退出 OAuth*

  *• 或者直接运行* ***kimi --config '...'\*** *指定纯 API key 配置*



 *让我给用户一个清晰的排查和解决步骤。*

• 这个问题是因为 **OAuth 扫码登录的配置残留** 和 **API Key 的覆盖机制** 之间的冲突。

 根据文档，环境变量 **KIMI_API_KEY** 优先级最高，但它只能覆盖配置文件里的 **api_key**

 字段。而之前扫码登录（**/login**）时，Kimi CLI 在 **~/.kimi/config.toml** 里保存的是 **O**

 **Auth 授权信息**（access token/refresh token 机制），这和普通的 **api_key** 是两套不

 同的认证体系，所以环境变量覆盖不了。

 **排查步骤（在家里电脑上执行）**

 **1. 先确认环境变量是否生效**

```sh
 echo $KIMI_API_KEY
 如果输出为空，说明 **.zshrc** 没生效，运行：
 source ~/.zshrc
```

 **2. 查看当前配置**

 cat ~/.kimi/config.toml

 你会看到类似这样的 OAuth 残留配置：

```toml
 [providers.kimi-for-coding]
 type = "kimi"
 base_url = "https://api.kimi.com/coding/v1"
 *# 这里没有 api_key，或者有 token 相关的字段*
```

 **3. 解决方案（三选一）**

 **方案 A：直接修改配置文件（推荐）** 编辑 **~/.kimi/config.toml**，把 provider 改成用 api_key：

```toml
 [providers.kimi-for-coding]
 type = "kimi"
 base_url = "https://api.kimi.com/coding/v1"
 api_key = "sk-你的key"

 [models.kimi-for-coding]
 provider = "kimi-for-coding"
 model = "kimi-for-coding"
 max_context_size = 262144
```

 **方案 C：退出 OAuth 登录后重新配置** 在 Kimi CLI 交互界面里执行：

```sh
 /logout
 然后重新用 API Key 配置：
 /login
 这次选择平台时，**不要选"Kimi Code"（那个会走 OAuth）**，选其他平台（比如 Moonsho…
 OpenAI 兼容），然后输入你的 API Key。
```

 **4. 验证**

 kimi --version

 *# 然后启动 kimi，看是否还提示账户问题*

 ──────────────────────────────────────────────────────────────────────────────

 **最可能的情况**：你家里电脑的配置文件里还存着之前扫码拿到的 OAuth token，CLI 启动

 时优先走了 OAuth 流程，发现那个登录态已过期/无效，就报账户错误，根本没走到环境

 变量里的 API Key。



 按照方案 A 修改 **config.toml** 最彻底，改完就能和你在公司一样直接用。
