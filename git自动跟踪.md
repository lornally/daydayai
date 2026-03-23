致命错误：当前分支 claud4 没有对应的上游分支。
为推送当前分支并建立与远程上游的跟踪，使用

    git push --set-upstream origin claud4

为了让没有追踪上游的分支自动配置，参见 'git help config' 中的 'push.autoSetupRemote'。
这个是配置config, 以后就可以自动了吗?

git config --global push.autoSetupRemote true

git config --global push.autoSetupRemote simple
[push]
  autoSetupRemote = true


[push]
  autoSetupRemote = simple


  ai推荐使用simple, 可以避免潜在的误操作.
验证配置:
git config push.autoSetupRemote