import os
import ctypes
import subprocess
import sys
import psutil
import win32evtlog
import json
import base64

# --- 配置项 ---
# 定义 Sysmon 的相关路径和名称
SYSMON_DIR = "tool\\Sysmon"
SYSMON_EXEC = "sysmon64.exe"
SYSMON_CONFIG = "sysmonconfig-export.xml"
SYSMON_SERVICE_NAME = "Sysmon64"
SYSMON_LOG_CHANNEL = "Microsoft-Windows-Sysmon/Operational"
# 定义输出的 JSON 文件名
JSON_OUTPUT_FILE = "logs\\sysmon_logs.json"


def is_admin():
    """检查当前脚本是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def check_sysmon_service():
    """检查 Sysmon 服务是否存在并且正在运行"""
    try:
        service = psutil.win_service_get(SYSMON_SERVICE_NAME)
        if service.status() == "running":
            print(f"[*] 服务 '{SYSMON_SERVICE_NAME}' 正在运行。")
            return True
        else:
            print(f"[*] 服务 '{SYSMON_SERVICE_NAME}' 存在但未运行。")
            return False
    except psutil.NoSuchProcess:
        print(f"[*] 服务 '{SYSMON_SERVICE_NAME}' 不存在。")
        return False


def install_and_run_sysmon():
    """安装并运行 Sysmon"""
    sysmon_path = os.path.join(SYSMON_DIR, SYSMON_EXEC)
    config_path = os.path.join(SYSMON_DIR, SYSMON_CONFIG)

    if not os.path.exists(sysmon_path):
        print(f"[!] 错误: Sysmon 可执行文件未找到于: {sysmon_path}")
        return False

    if not os.path.exists(config_path):
        print(f"[!] 错误: Sysmon 配置文件未找到于: {config_path}")
        return False

    print("[*] 正在尝试安装和运行 Sysmon...")
    command = [sysmon_path, "-accepteula", "-i", config_path]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        print("[+] Sysmon 安装成功。")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[!] Sysmon 安装失败。")
        print(f"返回码: {e.returncode}")
        print(f"输出: {e.stdout}")
        print(f"错误: {e.stderr}")
        return False
    except Exception as e:
        print(f"[!] 执行命令时发生未知错误: {e}")
        return False


def get_sysmon_logs_to_json(num_logs=50):
    """
    【函数已按新要求修改】
    使用新版 EvtQuery API 获取 Sysmon 日志，并直接将每条日志的原始 XML 原文写入 JSON 文件。
    """
    print(f"\n[*] 正在从 '{SYSMON_LOG_CHANNEL}' 获取最新的 {num_logs} 条日志原文...")

    log_entries = []
    query_handle = None

    try:
        # 使用 EvtQuery API，这部分保持不变，因为它是正确的
        query_handle = win32evtlog.EvtQuery(
            SYSMON_LOG_CHANNEL,
            win32evtlog.EvtQueryReverseDirection,
            "*"
        )

        print("[*] 成功创建查询句柄，正在读取事件原文...")

        read_count = 0
        while read_count < num_logs:
            events = win32evtlog.EvtNext(query_handle, 1)
            if not events:
                break

            read_count += 1
            event_handle = events[0]

            # 使用 EvtRender 获取 XML 原文
            xml_content = win32evtlog.EvtRender(event_handle, win32evtlog.EvtRenderEventXml)
            log_entry = {
                "EventRawXML": xml_content
            }
            log_entries.append(log_entry)

        # 确保日志目录存在
        output_dir = os.path.dirname(JSON_OUTPUT_FILE)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 将包含原始XML的列表写入JSON文件
        with open(JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(log_entries, f, ensure_ascii=False, indent=4)

        print(f"[+] {len(log_entries)} 条日志原文已成功写入到文件: {JSON_OUTPUT_FILE}")

    except Exception as e:
        import traceback
        print(f"[!] 获取或写入 Sysmon 日志失败: {e}")
        traceback.print_exc()
        print("[!] 请确保 Sysmon 已安装且正在运行，并且脚本以管理员权限执行。")
    finally:
        if query_handle:
            query_handle = None


def main():
    """主函数"""
    if not is_admin():
        print("[!] 请以管理员权限运行此脚本。")
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        except Exception as e:
            print(f"[!] 提权失败: {e}")
        return

    if not check_sysmon_service():
        if not install_and_run_sysmon():
            print("[!] 无法启动 Sysmon 服务，退出脚本。")
            return

    # 获取日志并写入 JSON 文件，获取最近50条
    get_sysmon_logs_to_json(num_logs=50)


if __name__ == "__main__":
    main()