#!/usr/bin/env python3
"""
MCP服务器批量启动脚本
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

class MCPServerManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.servers: Dict[str, subprocess.Popen] = {}
        
    def start_server(self, name: str, script_path: str, *args) -> bool:
        """启动单个MCP服务器"""
        try:
            print(f"启动MCP服务器: {name}")
            process = subprocess.Popen(
                [sys.executable, script_path] + list(args),
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.servers[name] = process
            time.sleep(1)  # 等待服务器启动
            
            if process.poll() is None:
                print(f"✓ {name} 启动成功 (PID: {process.pid})")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"✗ {name} 启动失败: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"✗ {name} 启动失败: {e}")
            return False
    
    def start_all_servers(self):
        """启动所有可用的MCP服务器"""
        servers_config = [
            ("Browser MCP", "src/mcpsectrace/mcp_servers/browser_mcp.py"),
            ("Huorong MCP", "src/mcpsectrace/mcp_servers/huorong_mcp.py"),
            ("HRKill MCP", "src/mcpsectrace/mcp_servers/hrkill_mcp.py"),
            ("Focus Pack MCP", "src/mcpsectrace/mcp_servers/focus_pack_mcp.py"),
            ("Threat MCP", "external_mcp/ThreatMCP/run_server.py"),
            ("WinLog MCP", "external_mcp/winlog-mcp/src/main.py", "--storage-path", "./data/logs/"),
        ]
        
        print("=== MCPSecTrace 服务器启动管理器 ===\n")
        
        for name, script_path, *args in servers_config:
            full_path = self.project_root / script_path
            if full_path.exists():
                self.start_server(name, str(full_path), *args)
            else:
                print(f"⚠ {name} 脚本不存在: {script_path}")
        
        print(f"\n已启动 {len(self.servers)} 个MCP服务器")
        
    def stop_all_servers(self):
        """停止所有MCP服务器"""
        print("\n停止所有MCP服务器...")
        for name, process in self.servers.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✓ {name} 已停止")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"✓ {name} 已强制停止")
            except Exception as e:
                print(f"✗ 停止 {name} 时出错: {e}")

def main():
    manager = MCPServerManager()
    
    try:
        manager.start_all_servers()
        
        print("\n按 Ctrl+C 停止所有服务器...")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        manager.stop_all_servers()
        print("\n所有服务器已停止")

if __name__ == "__main__":
    main()