# bilibili-live-tools

    再次想起的话，春华秋实、夏炽冬霜，还会一直轮回下去

## Docker使用

先从 [READ_SAMPLE_CONF.toml](./READ_SAMPLE_CONF.toml) 制作配置文件

```shell
docker run -itd --name <容器名称> \
      -e USER_NAME=<B站账户> -e USER_PASSWORD=<B站密码> \
      -e TELEGRAM_BOT_TOKEN=<Telegram Token> -e TELEGRAM_CHAT_ID=<Telegram Chat> \
      -v <宿主机配置文件路径>:/app/conf/user.toml \
      wacky6/bilibili-live-tools
```

Telegram Token 和 Chat 可参考 [wacky6/hikaru#telegram](https://github.com/wacky6/hikaru/blob/a985961b73e95a256df04b8fe969a5d89aef3842/README.md#telegram-%E5%BC%80%E6%92%AD%E9%80%9A%E7%9F%A5)。仅用于解决验证码识别服务故障的情况。此时会将验证码图片发动到指定的 Telegram 聊天，回复内容为对应的验证码文字。如果不提供，验证码服务故障时将无法登录。

`-v` 选项（可选）将宿主机中的配置文件挂载到容器中，方便修改。如果不提供，将使用默认配置文件。也可以用 `docker exec -it <容器名称> vi /app/conf/user.toml` 手动修改。修改后需重启容器使新配置生效。

## 感谢

- https://github.com/Dawnnnnnn/bilibili-live-tools
- https://github.com/lyyyuna
- https://github.com/lkeme/BiliHelper
- https://github.com/czp3009/bilibili-api
- https://github.com/lzghzr/bilive_client


## LICENSE
MIT
