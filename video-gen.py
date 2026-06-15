import time;
import json;
import requests;

from rich           import print_json;
from rich.table     import Table;
from rich.prompt    import Prompt;
from prompt_toolkit import PromptSession;
from datetime       import datetime;

from utils  import TimestampToYMD, EncodeImage, console;
from common import DisplayCredits;

class ProgramDataClass:
  MODELS_LIST_URL = "https://openrouter.ai/api/v1/videos/models";
  GENERATION_URL  = "https://openrouter.ai/api/v1/videos";

  def __init__(self):
    self.CmdPrompt = "> ";
    self.ModelInd = -1;
    self.Models = [];
    self.ReferenceImage = "";

    self.API_KEY = "";

    try:
      with open(".key") as f:
        self.API_KEY = f.readline().rstrip();
    except Exception as e:
      console.print(
        "OpenRouter API key not found! Put it inside .key file.",
        style="bold red"
      );
      exit(1);

    self.Models = self.GetModelsList();

  # ----------------------------------------------------------------------------

  def GetModelsList(self) -> list:
    res = [];

    try:
      response = requests.get(url=self.MODELS_LIST_URL);
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

################################################################################

def ProcessCommand(pd : ProgramDataClass, inline : str) -> bool:
  spl = inline.split(maxsplit=1);

  command = spl[0];

  args = "";

  if len(spl) >= 2:
    args = spl[1];

  if (command == "/exit" or command == "/quit"):
    return True;
  elif (command == "/image") or (command == "/url"):
    if not args:
      pd.ReferenceImage = "";
      console.print("Reference image is reset.", style="bold white");
    else:
      pd.ReferenceImage = (
        EncodeImage(args) if (command == "/image") else args
      );
      if pd.ReferenceImage:
        console.print(f"Reference image set: '{ args }'", style="bold white");
  elif (command == "/credits"):
    DisplayCredits(pd.API_KEY);
  elif (command == "/brief"):
    DisplayModelsBrief(pd.Models);
  elif (command == "/models"):
    DisplayModels(pd.Models);
  elif (command == "/select"):
    if not args:
      console.print("Need model index!", style="bold red");
    else:
      if not args.isdigit():
        console.print("Invalid model index!", style="bold red");
      else:
        pd.ModelInd = int(args);
        pd.ModelInd += -1;
        if (pd.ModelInd < 0) or (pd.ModelInd >= len(pd.Models)):
          console.print("Invalid model index!", style="bold red");
        else:
          console.print(
            f"Selected model { pd.Models[ pd.ModelInd ]['modelId'] }"
          );
          pd.CmdPrompt = f"{ pd.Models[ pd.ModelInd ]['modelId'] } > ";
  elif (command == "/prompt"):
    prompt = args;

    if pd.ModelInd == -1:
      console.print("Select model first!", style="bold red");
    else:
      if not prompt:
        console.print("Prompt string is empty!", style="bold red");
      else:
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
        coice = choice.lower();
        if choice == "y":
          response = requests.post(
            pd.GENERATION_URL,
            headers={
              "Authorization": f"Bearer { pd.API_KEY }",
              "Content-Type": "application/json",
            },
            json=json.loads(req)
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
                }
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
                      "Authorization": f"Bearer { pd.API_KEY }"
                  });
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

  return False;

################################################################################

def main():
  programData = ProgramDataClass();

  promptSession = PromptSession();

  shouldExit = False;

  try:
    while not shouldExit:
      inLine = promptSession.prompt(programData.CmdPrompt).strip();

      if inLine:
        shouldExit = ProcessCommand(programData, inLine);

  except (EOFError, KeyboardInterrupt):
    console.print();
    exit(1);

################################################################################

if __name__ == "__main__":
  main();
