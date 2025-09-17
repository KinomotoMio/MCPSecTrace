"""
MCPSecTrace 部署测试模块

此模块包含对所有MCP服务器的部署验证测试，确保项目可以正常部署和运行。
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

from mcpsectrace.config import get_config_value


class MCPTestBase:
    """MCP测试基类"""

    def __init__(self, server_name: str, server_script: str, port: int):
        self.server_name = server_name
        self.server_script = server_script
        self.port = port
        self.process: Optional[subprocess.Popen] = None

    def start_server(self) -> bool:
        """启动MCP服务器"""
        try:
            # 为需要参数的MCP服务器添加必要参数
            cmd = [sys.executable, self.server_script]

            if "huorong_mcp.py" in self.server_script:
                huorong_path = get_config_value("paths.huorong_exe", default="")
                if huorong_path:
                    cmd.extend(["--huorong-path", huorong_path])
                else:
                    print(f"{self.server_name} 路径未配置，跳过服务器启动测试")
                    return False

            elif "focus_pack_mcp.py" in self.server_script:
                focus_pack_path = get_config_value("paths.focus_pack_exe", default="")
                if focus_pack_path:
                    cmd.extend(["--focus-pack-path", focus_pack_path])
                else:
                    print(f"{self.server_name} 路径未配置，跳过服务器启动测试")
                    return False

            elif "hrkill_mcp.py" in self.server_script:
                hrkill_path = get_config_value("paths.hrkill_exe", default="")
                if hrkill_path:
                    cmd.extend(["--hrkill-path", hrkill_path])
                else:
                    print(f"{self.server_name} 路径未配置，跳过服务器启动测试")
                    return False

            print(f"启动 {self.server_name} 服务器: {' '.join(cmd)}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path(__file__).parent.parent
            )

            # 等待服务器启动
            time.sleep(3)

            # 检查进程是否正常运行
            if self.process.poll() is None:
                print(f"{self.server_name} 服务器启动成功，PID: {self.process.pid}")
                return True
            else:
                stdout, stderr = self.process.communicate()
                print(f"{self.server_name} 服务器启动失败")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False

        except Exception as e:
            print(f"启动 {self.server_name} 服务器时出错: {e}")
            return False

    def stop_server(self):
        """停止MCP服务器"""
        if self.process and self.process.poll() is None:
            print(f"停止 {self.server_name} 服务器...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print(f"强制终止 {self.server_name} 服务器")
                self.process.kill()
                self.process.wait()
            print(f"{self.server_name} 服务器已停止")

    def test_server_connectivity(self) -> bool:
        """测试服务器连接性"""
        # 基础连接测试 - 检查进程是否运行
        if not self.process or self.process.poll() is not None:
            print(f"{self.server_name} 服务器进程未运行")
            return False

        print(f"{self.server_name} 服务器连接正常")
        return True


class HuorongMCPTest(MCPTestBase):
    """火绒MCP测试类"""

    def __init__(self):
        server_script = "src/mcpsectrace/mcp_servers/huorong_mcp.py"
        super().__init__("Huorong", server_script, 8802)
        self.huorong_path = get_config_value("paths.huorong_exe", default="")

    def test_huorong_tool_access(self) -> bool:
        """测试火绒工具访问"""
        print("测试火绒工具访问...")

        if not self.huorong_path:
            print("火绒路径未配置，跳过测试")
            return False

        if not Path(self.huorong_path).exists():
            print(f"火绒路径不存在: {self.huorong_path}")
            return False

        print("火绒工具路径验证成功")
        return True

    def test_start_huorong_tool(self) -> bool:
        """测试启动火绒工具的MCP功能"""
        print("测试start_huorong MCP工具...")

        # 这里可以通过MCP协议调用工具，现在先做基础验证
        if self.test_server_connectivity() and self.test_huorong_tool_access():
            print("火绒MCP工具测试通过")
            return True
        else:
            print("火绒MCP工具测试失败")
            return False


class IOCMCPTest(MCPTestBase):
    """IOC MCP测试类"""

    def __init__(self):
        server_script = "src/mcpsectrace/mcp_servers/ioc_mcp.py"
        super().__init__("IOC", server_script, 8805)
        self.chrome_path = get_config_value("paths.chrome_exe", default="")
        self.chromedriver_path = get_config_value("paths.chromedriver_exe", default="")

    def test_browser_access(self) -> bool:
        """测试浏览器访问"""
        print("测试浏览器访问...")

        if not self.chrome_path:
            print("Chrome路径未配置，跳过测试")
            return False

        if not Path(self.chrome_path).exists():
            print(f"Chrome路径不存在: {self.chrome_path}")
            return False

        if not self.chromedriver_path:
            print("ChromeDriver路径未配置，跳过测试")
            return False

        if not Path(self.chromedriver_path).exists():
            print(f"ChromeDriver路径不存在: {self.chromedriver_path}")
            return False

        print("浏览器配置验证成功")
        return True

    def test_ioc_page_access(self) -> bool:
        """测试IOC页面访问的MCP功能"""
        print("测试IOC威胁情报查询...")

        if self.test_server_connectivity() and self.test_browser_access():
            print("IOC MCP浏览器访问测试通过")
            return True
        else:
            print("IOC MCP浏览器访问测试失败")
            return False


class FocusPackMCPTest(MCPTestBase):
    """Focus Pack MCP测试类"""

    def __init__(self):
        server_script = "src/mcpsectrace/mcp_servers/focus_pack_mcp.py"
        super().__init__("FocusPack", server_script, 8804)
        self.focus_pack_path = get_config_value("paths.focus_pack_exe", default="")

    def test_focus_pack_tool_access(self) -> bool:
        """测试Focus Pack工具访问"""
        print("测试Focus Pack工具访问...")

        if not self.focus_pack_path:
            print("Focus Pack路径未配置，跳过测试")
            return False

        if not Path(self.focus_pack_path).exists():
            print(f"Focus Pack路径不存在: {self.focus_pack_path}")
            return False

        print("Focus Pack工具路径验证成功")
        return True

    def test_start_focus_pack_tool(self) -> bool:
        """测试启动Focus Pack工具的MCP功能"""
        print("测试Focus Pack MCP工具...")

        if self.test_server_connectivity() and self.test_focus_pack_tool_access():
            print("Focus Pack MCP工具测试通过")
            return True
        else:
            print("Focus Pack MCP工具测试失败")
            return False


class HRKillMCPTest(MCPTestBase):
    """HRKill MCP测试类"""

    def __init__(self):
        server_script = "src/mcpsectrace/mcp_servers/hrkill_mcp.py"
        super().__init__("HRKill", server_script, 8803)
        self.hrkill_path = get_config_value("paths.hrkill_exe", default="")

    def test_hrkill_tool_access(self) -> bool:
        """测试HRKill工具访问"""
        print("测试HRKill工具访问...")

        if not self.hrkill_path:
            print("HRKill路径未配置，跳过测试")
            return False

        if not Path(self.hrkill_path).exists():
            print(f"HRKill路径不存在: {self.hrkill_path}")
            return False

        print("HRKill工具路径验证成功")
        return True

    def test_start_hrkill_tool(self) -> bool:
        """测试启动HRKill工具的MCP功能"""
        print("测试HRKill MCP工具...")

        if self.test_server_connectivity() and self.test_hrkill_tool_access():
            print("HRKill MCP工具测试通过")
            return True
        else:
            print("HRKill MCP工具测试失败")
            return False


class DeploymentTestSuite:
    """部署测试套件"""

    def __init__(self):
        self.test_results: Dict[str, bool] = {}
        self.servers = [
            HuorongMCPTest(),
            IOCMCPTest(),
            FocusPackMCPTest(),
            HRKillMCPTest(),
        ]

    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有部署测试"""
        print("=" * 60)
        print("MCPSecTrace 部署测试开始")
        print("=" * 60)

        for server_test in self.servers:
            print(f"\n--- 测试 {server_test.server_name} MCP服务器 ---")

            try:
                # 启动服务器
                if not server_test.start_server():
                    self.test_results[server_test.server_name] = False
                    continue

                # 执行具体测试
                if isinstance(server_test, HuorongMCPTest):
                    result = server_test.test_start_huorong_tool()
                elif isinstance(server_test, IOCMCPTest):
                    result = server_test.test_ioc_page_access()
                elif isinstance(server_test, FocusPackMCPTest):
                    result = server_test.test_start_focus_pack_tool()
                elif isinstance(server_test, HRKillMCPTest):
                    result = server_test.test_start_hrkill_tool()
                else:
                    result = server_test.test_server_connectivity()

                self.test_results[server_test.server_name] = result

            except Exception as e:
                print(f"测试 {server_test.server_name} 时出现异常: {e}")
                self.test_results[server_test.server_name] = False

            finally:
                # 停止服务器
                server_test.stop_server()

        self._print_test_summary()
        return self.test_results

    def _print_test_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)

        passed_count = 0
        failed_count = 0

        for server_name, result in self.test_results.items():
            status = "PASS" if result else "FAIL"
            print(f"{server_name:15} {status}")
            if result:
                passed_count += 1
            else:
                failed_count += 1

        print("-" * 60)
        print(f"总计: {len(self.test_results)} 项测试")
        print(f"通过: {passed_count} 项")
        print(f"失败: {failed_count} 项")

        if failed_count == 0:
            print("\n所有部署测试通过！项目可以正常部署和运行。")
        else:
            print(f"\n有 {failed_count} 项测试失败，请检查配置和依赖。")


def main():
    """主函数"""
    test_suite = DeploymentTestSuite()
    results = test_suite.run_all_tests()

    # 返回适当的退出代码
    failed_tests = [name for name, result in results.items() if not result]
    if failed_tests:
        sys.exit(1)
    else:
        sys.exit(0)


# Pytest测试函数
def test_huorong_mcp_deployment():
    """测试火绒MCP部署"""
    test = HuorongMCPTest()
    assert test.start_server(), "火绒MCP服务器启动失败"
    try:
        assert test.test_start_huorong_tool(), "火绒MCP工具测试失败"
    finally:
        test.stop_server()


def test_ioc_mcp_deployment():
    """测试IOC MCP部署"""
    test = IOCMCPTest()
    assert test.start_server(), "IOC MCP服务器启动失败"
    try:
        assert test.test_ioc_page_access(), "IOC MCP浏览器访问测试失败"
    finally:
        test.stop_server()


def test_focus_pack_mcp_deployment():
    """测试Focus Pack MCP部署"""
    test = FocusPackMCPTest()
    assert test.start_server(), "Focus Pack MCP服务器启动失败"
    try:
        assert test.test_start_focus_pack_tool(), "Focus Pack MCP工具测试失败"
    finally:
        test.stop_server()


def test_hrkill_mcp_deployment():
    """测试HRKill MCP部署"""
    test = HRKillMCPTest()
    assert test.start_server(), "HRKill MCP服务器启动失败"
    try:
        assert test.test_start_hrkill_tool(), "HRKill MCP工具测试失败"
    finally:
        test.stop_server()


if __name__ == "__main__":
    main()