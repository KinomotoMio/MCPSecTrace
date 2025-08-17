<h1 align="center">fdp-mcp-server</h1>

> 中文说明：[README-zh_CN.md](README-zh_CN.md).

QiAnXin XLab provides MCP tools for accessing foundational network security data.

## About XLab
XLab is a research team under QiAnXin dedicated to large-scale network security research, threat analysis and attribution, and the construction of multidimensional security data platforms.

XLab is one of the earliest teams in China to leverage large-scale data for cybersecurity research, security applications, and threat intelligence generation. It built the country’s first PassiveDNS system, along with several industry-leading foundational data systems covering NetFlow, Whois, digital certificates, IPs, and malware samples.

# Tool Categories
The fdp-mcp-server provides multiple categories of tools. Users can select specific URLs to load the corresponding tools based on their needs.

Currently available tool sets:
1. Basic Network Security Data Query  
   URL: https://fdp.qianxin.com/mcp/v1/basic/mcp/  
   Includes:
    * **flint rrset**: Query Resource Record Sets (RRsets) for specific domain names and record types
    * **flint rdata**: Reverse lookup of DNS response rrset records
    * **whois history**: Retrieve registration history of domain names or IP addresses
    * **certdb domain**: Query certificate data by domain name
    * **ioc**: Search XLab’s IOC (Indicators of Compromise) database
2. Domain-Related Data Query  
   URL: https://fdp.qianxin.com/mcp/v1/domain/mcp/  
   Includes:
    * **codomain**: Retrieve co-occurring domains and their associated tags
    * **float_fqdn**: Domain popularity rankings based on PassiveDNS data
    * **webdb**: Retrieve webpage content associated with a domain
    * **libra**: Access analytical data on domains from XLab’s Libra platform
3. IP-Related Data Query  
   URL: https://fdp.qianxin.com/mcp/v1/ip/mcp/  
   Includes:
    * **ip_geo**: Lookup for IPv4 geolocation, ASN, and IP ownership
4. Sample-Related Data Query  
   URL: https://fdp.qianxin.com/mcp/v1/sample/mcp/  
   Includes:
    * **sandbox**: Retrieve summarized network behavior of samples

# Execution Methods
## Overview
1. This application functions as a proxy that translates remote MCP tool calls into local Stdio-based interactions. Therefore, tools can be used either locally or by directly accessing the remote MCP server via its URL.
2. The remote MCP server currently supports only **streamable HTTP** access.
3. This toolset is a **trial version** intended for basic use. Under high concurrency, the backend may restrict access frequency. For production or high-frequency scenarios, please use the official version.
4. For official access, use the corresponding tool URL and include two HTTP headers: `fdp-access` and `fdp-secret`.
    * To obtain credentials, please contact QiAnXin XLab.
5. The following examples are based on the ``Basic Network Security Data Query`` tool.

## Trial Version Usage
### Run Locally from Source Code
1. Clone the repository.
2. Use uv to run and configure Claude Desktop:
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

### Run with Docker
1. Clone the repository.
2. Build the Docker image: `docker build . fdp-mcp-server:vxx.xx.xx`
3. Configure Claude Desktop:
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

### Run via PyPI Package
1. Use uvx and configure Claude Desktop as follows:
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

## Official Version Usage
If you want to call the fdp-mcp-server tools from within an intelligent agent application, you can configure the remote MCP server URL on the client side and include the required HTTP headers `fdp-access` and `fdp-secret`.

1. When writing agent code, add the headers when calling the MCP tools. Example using smolagents:
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
            agent.run("Query the domains associated with www.example.com and assess its likely business purpose based on the associated data.")


    if __name__ == "__main__":
        main()
    ```
2. If using Claude Desktop, you can use the mcp-remote library for proxy forwarding and configure the HTTP headers during the process:
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
                    "fdp-access:xxxx",
                    "--header",
                    "fdp-secret:yyyy"
                ],
            }
        }
    }
    ```