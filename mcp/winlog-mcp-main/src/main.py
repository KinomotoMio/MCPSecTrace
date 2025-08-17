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
parser.add_argument('--storage-path', type=str, default="C:\\logs\\", help='Log storage path')
args, unknown = parser.parse_known_args()

class Settings:
    STORAGE_PATH = args.storage_path
    LOG_NAME = "Microsoft-Windows-Sysmon/Operational"  # 預設抓 Sysmon 通道
    SOURCE_NAME = "Microsoft-Windows-Sysmon"           # 預設只抓 Sysmon 來源
    SERVER_NAME = "localhost"
    SIZE = 10


mcp = FastMCP(
    describe="Pywin32 win32evtlog for Retrieval Windows Logs"
)


@mcp.tool()
def ingest_syslog(
    source_name: str = Settings.SOURCE_NAME,
    log_name: str = Settings.LOG_NAME,
    server_name: str = Settings.SERVER_NAME,
    size: int = Settings.SIZE
):
    """
    Ingest Windows logs

    Args:
        source_name (str, optional): event source name. Empty string means no filter (all sources).
        log_name (str, optional): event log name. Defaults to "Microsoft-Windows-Sysmon/Operational".
        server_name (str, optional): server. Defaults to "localhost".
        size (int, optional): number of log lines to return

    Returns:
        str: log content
    """

    try:
        if os.path.isfile(Settings.STORAGE_PATH):
            return f"ERROR: storage_path points to a file instead of a directory ({Settings.STORAGE_PATH}), please use a directory path."
        os.makedirs(Settings.STORAGE_PATH, exist_ok=True)
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        safe_log_name = log_name.replace("/", "_").replace("\\", "_")
        dest_file = os.path.join(Settings.STORAGE_PATH, f"{timestamp}_{safe_log_name}.log")

        # Check admin privileges
        if not ctypes.windll.shell32.IsUserAnAdmin():
            return "ERROR: Administrator privileges required."

        if log_name == "Microsoft-Windows-Sysmon/Operational":
            # Use EvtQuery for Sysmon log
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
            # Use OpenEventLog for other logs
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
                        # If source_name is empty, do not filter
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
                                # Attempt to get the formatted message
                                event_record['Message'] = win32evtlogutil.SafeFormatMessage(event, log_name)
                            except Exception as msg_ex:
                                # Handle message parsing error
                                event_record['Message'] = f"Message parse error: {msg_ex}"
                            f.write(str(event_record) + "\n")
                        except Exception as e:
                            # Handle event parsing error
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
    Query Windows logs

    Args:
        timestamp (str): the timestamp (YYYY-MM-DD_HH-MM-SS) to filter log files
        source_name (str, optional): event source name. Defaults to "Microsoft-Windows-Sysmon".
        size (int, optional): number of log lines to return

    Returns:
        str: log content
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
                    # Filter events by source name
                    if event_dict['SourceName'] != source_name:
                        continue
                logs.append(event.strip())

    if not logs:
        return "No events found in matching log files"

    return "\n".join(logs[-size:])


@mcp.prompt()
def prompt_guide():
    return f"""
    You are a Windows log analyst.

    Your task is to analyze the Windows log and provide a summary of the events.
    The log is stored in the following path:
    ```
    {Settings.STORAGE_PATH}
    ```
    
    You can use the following tools:
    - ingest_syslog: Ingest Windows log
        - Args:
            - source_name (str, optional): event source name. Defaults to "Microsoft-Windows-Sysmon".
            - size (int, optional): number of log lines to return
        - Returns:
            - str: log file path
    - query_syslog: Query Windows log
        - Args:
            - timestamp (str): the timestamp (YYYY-MM-DD_HH-MM-SS) to filter log files
            - source_name (str, optional): event source name. Defaults to "Microsoft-Windows-Sysmon".
            - size (int, optional): number of log lines to return
        - Returns:
            - str: log file path
    
    if you want to ingest the log, use the following prompt:
    ```
    ingest_syslog(
        source_name="{Settings.SOURCE_NAME}",
        size={Settings.SIZE}
    )
    ```
    
    if you want to query the log, use the following prompt:
    ```
    query_syslog(
        timestamp="2025-05-15_14-47-24",
        source_name="{Settings.SOURCE_NAME}",
        size={Settings.SIZE}
    )
    ```
    """


if __name__ == "__main__":
    mcp.run()

