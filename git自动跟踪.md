###### 推送分支报错

```sh
# 错误1：当前分支没有上游分支
fatal: 当前分支 claud4 没有对应的上游分支。
为推送当前分支并建立与远程上游的跟踪，使用

    git push --set-upstream origin claud4

# 错误2：Git 配置值类型写错了
fatal: bad boolean config value 'simple' for 'push.autosetupremote'
```

说明：
错误1是本地分支还没和远程分支建立跟踪关系。
错误2是把 `push.default` 的值 `simple` 误写给了 `push.autoSetupRemote`。

先解决这一次：

```sh
git push --set-upstream origin 当前分支名
```

以后自动处理：

```sh
git config --global push.default simple
git config --global push.autoSetupRemote true
```

对应 `.gitconfig`：

```ini
[push]
  default = simple
  autoSetupRemote = true
```

验证：

```sh
git config --global --get push.default
git config --global --get push.autoSetupRemote
```

区分：
`simple` 属于 `push.default`，`true/false` 属于 `push.autoSetupRemote`。

`push.default simple` 的作用：
执行 `git push` 时，默认只推当前分支，并且要求本地分支和远程上游分支同名；不满足条件时会报错，这样更安全。

补充：
上面的 `claud4` 只是示例分支名，实际使用时换成你自己的分支名。


##### 拉取分支报错

```sh
-<1:%>- gst
On branch claud3
Your branch is up to date with 'origin/claud3'.

nothing to commit, working tree clean
((.pysidenv) ) -<mmm@mdeMac-Studio.local:/Users/x/keydog [claud3]>-
-<%>- gl origin/claud4
fatal: 'origin/claud4' does not appear to be a git repository
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
```

原因：
`origin/claud4` 是远程分支名，不是远程仓库名。
这里把 `origin/claud4` 直接传给 `git pull` 或别名 `gl` 时，Git 会把它当成 remote，所以报错。

正确做法：

```sh
# 切换到远程分支，并自动建立本地跟踪分支
git switch --track origin/claud4
```

如果本地已经有这个分支：

```sh
git switch claud4
```

如果只是想在当前分支拉取最新代码：

```sh
git pull
```

补充：
我知道你当时的目录是 `/Users/x/keydog`，是因为你贴出的终端提示符里已经包含了这个路径。
