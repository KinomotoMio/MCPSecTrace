# 🪟 WinLog-mcp

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

A Model Context Protocol (MCP) tool for retrieving and analyzing Windows event logs (e.g. Application, System, Security). WinLog-mcp provides programmatic access to ingest and query Windows event logs, making it ideal for security monitoring, incident response, and log analysis automation.

> ⚠️ **Warning: This tool must be run with Administrator privileges. Please exercise caution to avoid causing unintended changes to your system.**

---

## ✨ Features

- **Ingest Windows Sysmon logs** and store them as files in a user-defined directory
- **Query logs** by timestamp, returning recent event entries for analysis or troubleshooting
- **Seamless interoperability** with MCP tools and ecosystem

### 📄 Log files format

- Log files are named with the format `<timestamp>_<log_type>.log` in the chosen storage path

## MCP Server (tool, prompts,...)

### 🛠️ Available Tools

- `ingest_syslog`: Ingests recent Sysmon logs and writes them to a file
- `query_syslog`: Queries ingested logs by timestamp and returns recent events

## 📋 Requirements

- **Operating System:** Windows
- **Python:** 3.7 or higher
- **Dependencies:**
  - [pywin32](https://pypi.org/project/pywin32/)
  - [mcp.server.fastmcp](https://github.com/agi-partners/fastmcp) (or your MCP server implementation)

## 💾 Installation

Clone the repository and install dependencies:

```sh
pip install -r requirements.txt
```

## 🚀 Usage

### 🖥️ Sysmon Installation

Reference: [Sysmon Installation Guideline](./sysmon/Guideline.md)

```cmd
cd sysmon
install.bat
```

### ▶️ Running Directly

Run the tool as an MCP server:

```sh
python main.py --storage-path \\PATH\\TO\\logs\\
```

### 🧑‍💻 Development Mode

You can inspect or debug using the MCP Inspector:

```sh
# Run in development mode
python \\PATH\\TO\\main.py --storage-path \\PATH\\TO\\logs\\

# Run in inspector mode
npx @modelcontextprotocol/inspector python \\PATH\\TO\\main.py --storage-path \\PATH\\TO\\logs\\
```

## ⚙️ Configuration

MCP configuration to run winlog-mcp tool. 

```json
{
  "mcpServers": {
    "winlog-mcp": {
      "command": "python",
      "args": [
        "\\PATH\\TO\\main.py",
        "--storage-path",
        "\\PATH\\TO\\logs\\"
      ]
    }
  }
}

```


### 🤖 MCP Clients Integration

#### 💬 Claude Desktop Integration

The configuration file is located at:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Once integrated with Claude Desktop, you can ask Claude to:
> Please show me the last 10 events in the last 24 hours, and Analyze them.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
