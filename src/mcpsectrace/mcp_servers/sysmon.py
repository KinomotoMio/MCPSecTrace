from mcp.server.fastmcp import FastMCP
import win32evtlog
import win32evtlogutil
import datetime
import os
import traceback
import logging
import argparse
import ctypes


parser = argparse.ArgumentParser()
# 获取项目根目录路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
default_storage_path = os.path.join(project_root, "logs", "sysmon")
parser.add_argument('--storage-path', type=str, default=default_storage_path, help='Log storage path')
args, unknown = parser.parse_known_args()

class Settings:
    STORAGE_PATH = args.storage_path
    LOG_NAME = "Microsoft-Windows-Sysmon/Operational"  # 默认获取 Sysmon 通道
    SOURCE_NAME = "Microsoft-Windows-Sysmon"           # 默认仅获取 Sysmon 来源
    SERVER_NAME = "localhost"
    SIZE = 10


mcp = FastMCP("Pywin32 win32evtlog for Retrieval Windows Logs")


@mcp.tool()
def ingest_syslog(
    source_name: str = Settings.SOURCE_NAME,
    log_name: str = Settings.LOG_NAME,
    server_name: str = Settings.SERVER_NAME,
    size: int = Settings.SIZE
):
    """
    摄取 Windows 日志

    参数：
        source_name (str, 可选): 事件源名称。空字符串表示无过滤（所有来源）。
        log_name (str, 可选): 事件日志名称。默认为 "Microsoft-Windows-Sysmon/Operational"。
        server_name (str, 可选): 服务器。默认为 "localhost"。
        size (int, 可选): 返回的日志行数

    返回：
        str: 日志内容
    """

    try:
        if os.path.isfile(Settings.STORAGE_PATH):
            return f"ERROR: storage_path points to a file instead of a directory ({Settings.STORAGE_PATH}), please use a directory path."
        os.makedirs(Settings.STORAGE_PATH, exist_ok=True)
        timestamp = datetime.datetime.now().strftime('%Y%m%d')
        dest_file = os.path.join(Settings.STORAGE_PATH, f"sysmon_mcp_{timestamp}.log")

        # 检查管理员权限
        if not ctypes.windll.shell32.IsUserAnAdmin():
            return "ERROR: Administrator privileges required."

        if log_name == "Microsoft-Windows-Sysmon/Operational":
            # 对于 Sysmon 日志使用 EvtQuery
            flags = win32evtlog.EvtQueryReverseDirection
            query = f"*[System/Provider/@Name='{source_name or 'Microsoft-Windows-Sysmon'}']"
            handle = win32evtlog.EvtQuery(log_name, flags, query)
            events = 1
            written = 0
            with open(dest_file, "a", encoding="utf-8") as f:
                while events and written < size:
                    events = win32evtlog.EvtNext(handle, 1)
                    if not events:
                        break
                    for event in events:
                        xml = win32evtlog.EvtRender(event, win32evtlog.EvtRenderEventXml)
                        f.write(xml + "\n")
                        written += 1
                        if written >= size:
                            break
        else:
            # 对于其他日志使用 OpenEventLog
            handle = win32evtlog.OpenEventLog(server_name, log_name)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            written = 0
            with open(dest_file, "a", encoding="utf-8") as f:
                events = True
                while events and written < size:
                    events = win32evtlog.ReadEventLog(handle, flags, 0)
                    if not events:
                        break
                    for event in events:
                        # 如果 source_name 为空，则不进行过滤
                        print(event)
                        try:
                            event_record = {}
                            event_record['RecordNumber'] = getattr(event, 'RecordNumber', None)
                            event_record['EventID'] = getattr(event, 'EventID', 0) & 0xFFFF
                            event_record['EventCategory'] = getattr(event, 'EventCategory', None)
                            event_record['EventType'] = getattr(event, 'EventType', None)
                            event_record['SourceName'] = getattr(event, 'SourceName', None)
                            event_record['ComputerName'] = getattr(event, 'ComputerName', None)
                            event_record['Sid'] = str(getattr(event, 'Sid', None)) if getattr(event, 'Sid', None) is not None else None
                            event_record['StringInserts'] = getattr(event, 'StringInserts', None)
                            event_record['Data'] = getattr(event, 'Data', None)
                            event_record['TimeGenerated'] = getattr(event, 'TimeGenerated', None).isoformat() if hasattr(getattr(event, 'TimeGenerated', None), 'isoformat') else str(getattr(event, 'TimeGenerated', None))
                            event_record['TimeWritten'] = getattr(event, 'TimeWritten', None).isoformat() if hasattr(getattr(event, 'TimeWritten', None), 'isoformat') else str(getattr(event, 'TimeWritten', None))
                            event_record['Message'] = None
                            try:
                                # 尝试获取格式化后的消息
                                event_record['Message'] = win32evtlogutil.SafeFormatMessage(event, log_name)
                            except Exception as msg_ex:
                                # 处理消息解析错误
                                event_record['Message'] = f"Message parse error: {msg_ex}"
                            f.write(str(event_record) + "\n")
                        except Exception as e:
                            # 处理事件解析错误
                            f.write(f"Error parsing event: {e}\n")
                        written += 1
                        if written >= size:
                            break

            win32evtlog.CloseEventLog(handle)
        return dest_file
    except Exception as e:
        logging.debug(traceback.format_exc())
        return f"ERROR: {e}"



@mcp.tool()
def query_syslog(
    timestamp: str,
    source_name: str = Settings.SOURCE_NAME,
    size: int = Settings.SIZE
):
    """
    查询 Windows 日志

    参数：
        timestamp (str): 时间戳 (YYYYMMDD) 用于过滤日志文件，例如 "20251216"
        source_name (str, 可选): 事件源名称。默认为 "Microsoft-Windows-Sysmon"。
        size (int, 可选): 返回的日志行数

    返回：
        str: 日志内容
    """
    files = os.listdir(Settings.STORAGE_PATH)
    matched_files = [
        f for f in files
        if f.endswith(".log") and timestamp in f
    ]
    if not matched_files:
        return "No log files found matching the timestamp"

    logs = []
    for file in matched_files:
        with open(os.path.join(Settings.STORAGE_PATH, file), "r", encoding="utf-8") as f:
            events = f.readlines()
            for event in events:
                try:
                    import ast
                    event_dict = ast.literal_eval(event.strip()) if event.strip().startswith('{') else None
                except Exception:
                    event_dict = None
                if source_name and event_dict and 'SourceName' in event_dict:
                    # 按源名称过滤事件
                    if event_dict['SourceName'] != source_name:
                        continue
                logs.append(event.strip())

    if not logs:
        return "在匹配的日志文件中未找到事件"

    return "\n".join(logs[-size:])


@mcp.prompt()
def prompt_guide():
    return f"""
    你是一个Windows日志分析员。

    你的任务是分析Windows日志并提供事件摘要。
    日志存储在以下路径：
    ```
    {Settings.STORAGE_PATH}
    ```

    你可以使用以下工具：
    - ingest_syslog: 摄取Windows日志
        - 参数：
            - source_name (str，可选): 事件源名称。默认为 "Microsoft-Windows-Sysmon"。
            - size (int，可选): 返回的日志行数
        - 返回值：
            - str: 日志文件路径
    - query_syslog: 查询Windows日志
        - 参数：
            - timestamp (str): 时间戳 (YYYYMMDD) 用于过滤日志文件，例如 "20251216"
            - source_name (str，可选): 事件源名称。默认为 "Microsoft-Windows-Sysmon"。
            - size (int，可选): 返回的日志行数
        - 返回值：
            - str: 日志内容

    如果你想摄取日志，请使用以下提示：
    ```
    ingest_syslog(
        source_name="{Settings.SOURCE_NAME}",
        size={Settings.SIZE}
    )
    ```

    如果你想查询日志，请使用以下提示：
    ```
    query_syslog(
        timestamp="20251216",
        source_name="{Settings.SOURCE_NAME}",
        size={Settings.SIZE}
    )
    ```
    """


if __name__ == "__main__":
    mcp.run()

