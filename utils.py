from datetime import datetime;

def TimestampToYMD(timestamp : int) -> str:
  return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d");
