import argparse;
import time;
import json;
import requests;

from rich           import print_json;
from rich.table     import Table;
from rich.prompt    import Prompt;
from prompt_toolkit import PromptSession;
from datetime       import datetime;

from program_data import ProgramDataClass;
from common       import DisplayCredits;

from utils import (
  RenderCmdPrompt,
  TimestampToYMD,
  EncodeImage,
  console
);

def GetModelsList(pd : ProgramDataClass) -> list:
  res = [];

  try:
    response = requests.get(
      url=pd.MODELS_LIST_URL_VIDEO,
      proxies=pd.Proxies,
      timeout=pd.RequestsTimeout
    );
    result = response.json();

    lst = result["data"];

    for item in lst:
      dict = {
          "modelId"     : item["id"]
        , "modelName"   : item["name"]
        , "createdAt"   : TimestampToYMD(item["created"])
        , "description" : item["description"]
        , "resolution"  : item["supported_sizes"]
        , "duration"    : item["supported_durations"]
        , "pricing"     : item["pricing_skus"]
        , "references"  : item["supported_frame_images"]
        , "audio"       : item["generate_audio"]
      };

      res.append(dict);

  except Exception as e:
    print(f"{ e }");
    exit(1);

  return res;

################################################################################

def DisplayModelsBrief(models : list):
  counter = 1;

  table = Table(show_header=False, show_lines=False, box=None);

  table.add_column(
    "No.",
    justify="left",
    style="bold bright_white"
  );
  table.add_column(
    "Id",
    justify="left",
    style="bold bright_cyan",
    overflow="fold"
  );
  table.add_column(
    "References",
    justify="left",
    style="bold white",
    overflow="fold"
  );
  table.add_column(
    "Pricing",
    justify="left",
    style="bold bright_yellow",
    overflow="fold"
  );

  for d in models:
    refs  = "-" if d["references"] is None else ", ".join(d["references"]);

    pricing = [];

    for k,v in d["pricing"].items():
      pricing.append(f"{ k } = { v }");

    table.add_row(
        f"{ counter }"
      , f"{ d['modelId'] }"
      , f"{ refs }"
      , f"{ ' | '.join(pricing) }"
    );

    counter += 1;

  console.print(table);

################################################################################

def DisplayModels(models : list):

  counter = 1;

  for d in models:
    table = Table(show_lines=True);

    table.add_column(
      "No.",
      justify="center",
      style="bold bright_white"
    );
    table.add_column(
      "Id",
      justify="center",
      style="bold bright_cyan",
      overflow="fold"
    );
    table.add_column(
      "Name",
      justify="center",
      style="bold bright_cyan"
    );
    table.add_column(
      "Description",
      justify="left",
      style="bold white",
      overflow="fold"
    );
    table.add_column(
      "Created",
      justify="center",
      style="bold white"
    );

    table.add_row(
        f"{ counter }"
      , f"{ d['modelId'] }"
      , f"{ d['modelName'] }"
      , f"{ d['description'] }"
      , f"{ d['createdAt'] }"
    );

    console.print(table);

    refs  = "-" if d["references"] is None else ", ".join(d["references"]);
    durs  = ", ".join(str(n) for n in d["duration"]);
    audio = "Yes" if d["audio"] else "No";

    table = Table(box=None);

    table.add_column(
      "Resolution",
      justify="left",
      style="bold white",
      overflow="fold"
    );
    table.add_column(
      "Duration",
      justify="left",
      style="bold white",
      overflow="fold"
    );
    table.add_column(
      "References",
      justify="left",
      style="bold white",
      overflow="fold"
    );
    table.add_column(
      "Use audio?",
      justify="center",
      style="bold white"
    );
    table.add_column(
      "Pricing",
      justify="left",
      style="bold bright_yellow",
      overflow="fold"
    );

    pricing = [];

    for k,v in d["pricing"].items():
      pricing.append(f"{ k } = { v }");

    table.add_row(
        f"{ ', '.join(d['resolution']) }"
      , f"{ durs }"
      , f"{ refs }"
      , f"{ audio }"
      , f"{ ', '.join(pricing) }"
    );

    console.print(table);
    console.rule();
    console.print();

    counter += 1;

################################################################################

def PrepareRequest(prompt : str, pd : ProgramDataClass) -> str:
  modelId = pd.Models[ pd.ModelInd ]["modelId"];
  dict = {
      "model": modelId
    , "prompt" : prompt
  };

  if pd.ReferenceImage:
    dict["input_references"] = [{
      "type" : "image_url",
      "image_url" : {
        "url" : pd.ReferenceImage
      }
    }];

  return json.dumps(dict);

CommandHandlers = {};

################################################################################

def Command(name : str):
  def _decorator(f):
    f.FunctionName = name;
    CommandHandlers[name] = f;
    return f;
  return _decorator;

################################################################################

@Command("/exit")
@Command("/quit")
def ProcessQuit(args : str, pd : ProgramDataClass) -> bool:
  return True;

################################################################################

@Command("/image")
def ProcessImage(args : str, pd : ProgramDataClass) -> bool:
  if not args:
    pd.InImage = "";
    pd.ReferenceImage = "";
    console.print("Reference image is reset.", style="bold white");
  else:
    pd.ReferenceImage = (
      EncodeImage(args) if (ProcessImage.FunctionName == "/image") else args
    );
    if pd.ReferenceImage:
      console.print(f"Reference image set: '{ args }'", style="bold white");
      pd.InImage = args;

  return False;

################################################################################

@Command("/credits")
def ProcessCredits(args : str, pd : ProgramDataClass) -> bool:
  DisplayCredits(pd.API_KEY, pd);
  return False;

################################################################################

@Command("/brief")
def ProcessCredits(args : str, pd : ProgramDataClass) -> bool:
  DisplayModelsBrief(pd.Models);
  return False;

################################################################################

@Command("/models")
def ProcessCredits(args : str, pd : ProgramDataClass) -> bool:
  DisplayModels(pd.Models);
  return False;

################################################################################

@Command("/select")
def ProcessCredits(args : str, pd : ProgramDataClass) -> bool:
  if not args:
    console.print("Need model index!", style="bold red");
    return False;

  try:
    int(args);
  except ValueError as _:
    console.print("Invalid model index!", style="bold red");
    return False;

  pd.ModelInd = int(args);
  pd.ModelInd += -1;
  if (pd.ModelInd < 0) or (pd.ModelInd >= len(pd.Models)):
    console.print("Invalid model index!", style="bold red");
  else:
    console.print(
      f"Selected model { pd.Models[ pd.ModelInd ]['modelId'] }"
    );
    pd.InModel = pd.Models[ pd.ModelInd ]['modelId'];

  return False;

################################################################################

@Command("/prompt")
def ProcessPrompt(args : str, pd : ProgramDataClass) -> bool:
  prompt = args;

  if pd.ModelInd == -1:
    console.print("Select model first!", style="bold red");
    return False;

  if not prompt:
    console.print("Prompt string is empty!", style="bold red");
    return False;

  try:
    req = PrepareRequest(prompt, pd);
    toPrint = json.loads(req);
    refBlock = toPrint.get("input_references", {});
    if refBlock:
      imgRef = refBlock[0]["image_url"]["url"];
      if "data:image" in imgRef:
        imgRef = f"{ refBlock[0]['image_url']['url'][:50] }...";
      toPrint["input_references"][0]["image_url"]["url"] = imgRef;
    print_json(json.dumps(toPrint));
    choice = Prompt.ask("Proceed? ", choices=["y", "Y", "n", "N"]);
    choice = choice.lower();
    if choice == "y":
      response = requests.post(
        pd.GENERATION_URL_VIDEO,
        headers={
          "Authorization": f"Bearer { pd.API_KEY }",
          "Content-Type": "application/json",
        },
        json=json.loads(req),
        proxies=pd.Proxies,
        timeout=pd.RequestsTimeout
      );

      result = response.json();
      print_json(json.dumps(result));

      if (response.status_code != requests.codes.accepted):
        console.print("Got error:", style="bold red");
      else:
        jobId = result["id"];
        pollingUrl = result["polling_url"];
        console.print(f"Job submitted: '{ jobId }' -> { pollingUrl }");
        while True:
          pollResponse = requests.get(
            url=pollingUrl,
            headers={
              "Authorization": f"Bearer { pd.API_KEY }"
            },
            proxies=pd.Proxies,
            timeout=pd.RequestsTimeout
          );
          status = pollResponse.json();
          print(f"Status: { status['status'] }");

          if status["status"] == "completed":
            print_json(json.dumps(status));
            counter = 1;
            for vurl in status.get("unsigned_urls", []):
              console.print(f"Video URL: { vurl }");
              response = requests.get(
                vurl,
                headers={
                  "Authorization": f"Bearer { pd.API_KEY }",
                },
                proxies=pd.Proxies,
                timeout=pd.RequestsTimeout
              );
              n = datetime.now().replace(microsecond=0);
              ns = n.strftime("%Y-%m-%d-%H-%M-%S");
              fname = f"generated/video_{ ns }_{ counter }.mp4";
              with open(fname, "wb") as f:
                f.write(response.content);
              console.print(f"Written: '{ fname }'");
              counter += 1;
            break;
          elif status["status"] == "failed":
            print(f"Error: { status.get('error', 'Unknown error') }")
            break;
          console.print("Waiting 30 seconds...");
          time.sleep(30);
  except Exception as e:
    console.print(f"{ e }");

  return False;

################################################################################

def ProcessCommand(pd : ProgramDataClass, inline : str) -> bool:
  spl = inline.split(maxsplit=1);

  command = spl[0];

  args = "";

  if len(spl) >= 2:
    args = spl[1];

  if command in CommandHandlers.keys():
    return CommandHandlers[command](args, pd);
  else:
    console.print("Invalid command!", style="bold red");

  return False;

################################################################################

def main():
  programData = ProgramDataClass();

  parser = argparse.ArgumentParser();

  parser.add_argument(
    "--socks-creds",
    type=str,
    default="",
    help="JSON file with credentials for socks5 proxy server."
  );

  args = parser.parse_args();

  if (args.socks_creds):
    try:
      creds = None;
      with open(args.socks_creds, "r") as f:
        creds = json.loads(f.read());
      programData.ProcessSocksCreds(creds);
    except Exception as e:
      console.print(f"{ e }", style="bold red");
      exit(1);

  programData.Models = GetModelsList(programData);

  promptSession = PromptSession();

  shouldExit = False;

  try:
    while not shouldExit:
      programData.CmdPrompt = RenderCmdPrompt(programData.InModel,
                                              programData.InImage);

      inLine = promptSession.prompt(programData.CmdPrompt).strip();

      if inLine:
        shouldExit = ProcessCommand(programData, inLine);

  except (EOFError, KeyboardInterrupt):
    console.print();
    exit(1);

################################################################################

if __name__ == "__main__":
  main();
