<h1 align="center">fdp-mcp-server</h1>

> English version: [README.md](README.md).

奇安信X实验室提供的关于网络安全基础数据相关的mcp工具。

# X实验室介绍
X实验室（XLab）是奇安信公司致力于大网安全研究、威胁分析溯源和大规模多维度安全数据平台建设的团队。
X实验室是国内最早利用大规模数据进行安全研究、安全应用和威胁情报生产的团队，建立了国内首个PassiveDNS系统，以及多个业内领先的 Netflow、Whois、证书、IP 和恶意样本等基础数据系统。

# 工具分类
fdp-mcp-server提供了不同种类的工具，在使用时可以根据需要，选择不同的URL来加载不同类型的工具。

目前提供的工具有：
1. **网络安全基础数据查询**: `https://fdp.qianxin.com/mcp/v1/basic/mcp/`。包含工具：
    * **flint rrset**: 用于查询特定域名和记录类型的资源记录集（Resource Record Set，简称 RRset）
    * **flint rdata**: 是用来反向查询DNS响应的rrset记录的数据
    * **whois history**: 查询域名或IP的注册历史信息
    * **certdb domain**: 通过域名查询域名证书信息
    * **ioc**: 查询X实验室IOC数据库
2. **域名相关基础数据查询**: `https://fdp.qianxin.com/mcp/v1/domain/mcp/`。包含工具：
    * **codomain**: 域名的伴生域名以及伴生域名的标签数据
    * **float_fqdn**: 基于PassiveDNS数据计算得到的域名流行度的排名
    * **webdb**: 查询域名关联的网页内容
    * **libra**: 查询奇安信X实验室对针对域名的分析系统中的数据
3. **IP相关基础数据查询**: `https://fdp.qianxin.com/mcp/v1/ip/mcp/`。包含工具：
    * **ip_geo**: 查询ipv4地理位置、ASN、IP所有者等信息
4. **样本相关基础数据查询**: `https://fdp.qianxin.com/mcp/v1/sample/mcp/`。包含工具：
    * **sandbox**: 查询样本网络行为摘要信息

# 运行方式
## 说明
1. 本应用是一个代理程序，可以将对远端mcp工具的调用转换成本地的Stdio运行的方式。所以运行方式就可以分为本地运行和直接访问远端mcp工具的url运行。
2. 远端的mcp server url地址目前只支持Streamable HTTP的访问方式。
3. 当前工具集是基础安全数据查询的**体验版**，高并发情况下后端会限制网络访问频率。在高频场景下，请使用正式版。
4. 正式版的访问，请直接使用相对应工具的url。需要提供fdp-access和fdp-secret这两个http请求头
    * 获取访问凭据，请联系奇安信X实验室
5. 以下都以**网络安全基础数据查询**为示例

## 体验版使用
### 本地代码运行
1. 从仓库客隆代码
2. 使用uv运行，配置claude desktop：
    ```json
    {
        "mcpServers": {
            "fdp-mcp-server": {
                "command": "uv",
                "args": [
                    "run",
                    "--project",
                    "/PATH/TO/fdp-mcp-server",
                    "fdp-mcp-server",
                    "--url",
                    "https://fdp.qianxin.com/mcp/v1/basic/mcp/"
                ]
            }
        }
    }
    ```

### docker镜像运行
1. 从仓库客隆代码
2. 编译docker镜像：`docker build . fdp-mcp-server:vxx.xx.xx`
3. 配置claude desktop
    ```json
    {
        "mcpServers": {
            "fdp-mcp-server": {
                "command": "docker",
                "args": [
                    "run",
                    "-i",
                    "--rm",
                    "fdp-mcp-server:vxx.xx.xx"
                ]
            }
        }
    }
    ```

### 本地运行pypi包
使用uvx，配置claude desktop:
```json
{
    "mcpServers": {
        "fdp-mcp-server": {
            "command": "uvx",
            "args": [
                "fdp-mcp-server",
                "--url",
                "https://fdp.qianxin.com/mcp/v1/basic/mcp/"
            ]
        }
    }
}
```

## 正式版使用
如果想在智能体应用中调用fdp-mcp-server工具，可以在客户端上配置远端mcp server的url地址直接调用工具。并提供dp-access和fdp-secret这两个http请求头
1. 编写agents代码时，调用连接mcp工具时将fdp-access和fdp-secret增加到http请求头中。以smolagents为例进行说明：
	```python
	from smolagents import ToolCollection
    from smolagents.agents import ToolCallingAgent
    from smolagents.models import OpenAIServerModel


    def main():
        with ToolCollection.from_mcp(
            {
                "url": "https://fdp.qianxin.com/mcp/v1/domain/mcp/",
                "transport": "streamable-http",
                "headers": {
                    "fdp-access": "xxxx",
                    "fdp-secret": "yyyy",
                },
            },
            trust_remote_code=True,
        ) as tools:
            agent = ToolCallingAgent(
                tools=[*tools.tools],
                model=OpenAIServerModel(
                    model_id="YOUR-LLM-MODEL-ID",
                    api_base="YOUR-LLM-MODEL-API-URL",
                    api_key="YOUR-LLM-MODEL-API-KEY",
                ),
            )
            agent.run("查询www.example.com的关联域名，并给根据关联域名的数据对查询的域名可能的业务做一个判断。")


    if __name__ == "__main__":
        main()

	```
2. 如果是使用在claude desktop上，可以利用`mcp-remote`库进行代理转发，在转发过程配置http请求头，配置说明：
	```json
	{
	    "mcpServers": {
	        "fdp_domain": {
	            "command": "npx",
	            "args": [
	            	"-y",
	                "mcp-remote@latest",
	                "https://fdp.qianxin.com/mcp/v1/domain/mcp/",
	                "--header",
	                "fdp-access:xxxx"
	                "--header",
	                "fdp-secret:yyyy"
	            ],
	        }
	    }
	}
	```