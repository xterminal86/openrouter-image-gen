import base64;
import io;

from PIL          import Image;
from datetime     import datetime;
from rich.console import Console;

console = Console();

################################################################################

def TimestampToYMD(timestamp : int) -> str:
  return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d");

################################################################################

def Image2PngBase64(fname : str) -> str:
  try:
    buffer = io.BytesIO();
    with Image.open(fname) as f:
      f.save(buffer, format="PNG");
    pngBytes = buffer.getvalue();
    b64img = base64.b64encode(pngBytes).decode('utf-8');
    return b64img;
  except Exception as e:
    console.print(f"{ e }", style="bold red");
    return "";

################################################################################

def EncodeImage(fname : str) -> str:
  spl = fname.rsplit(".", maxsplit=1);
  if len(spl) == 1:
    console.print("Cannot split by extension!", style="bold red");
    return "";
  extension = spl[1];
  pngOrJpg = (extension == "png" or extension == "jpeg" or extension == "jpg");
  try:
    if pngOrJpg:
      imageBytes = bytes();
      with open(fname, "rb") as f:
        imageBytes = base64.b64encode(f.read());
      imgDataMarkerByExtension = {
        "png"  : "png",
        "jpeg" : "jpeg",
        "jpg"  : "jpeg"
      };
      return f"data:image/{ imgDataMarkerByExtension[extension] };base64,{ imageBytes.decode('utf-8') }";
    else:
      console.print("Converting to png in memory...", style="bold white");
      imageBase64 = Image2PngBase64(fname);
      return f"data:image/png;base64,{ imageBase64 }" if imageBase64 else "";
  except Exception as e:
    console.print(f"{ e }", style="bold red");
    return "";

################################################################################

def RenderCmdPrompt(inModel : str, inImg : str) -> str:
  cmdPromptTemplate = "{model} | {image} > ";
  m   = "(none)" if not inModel else inModel;
  img = "(none)" if not inImg else inImg.rsplit("/", maxsplit=1)[-1];
  return cmdPromptTemplate.format(model=m, image=img);
