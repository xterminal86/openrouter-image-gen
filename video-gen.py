import json;
import requests;

from rich           import print_json;
from rich.console   import Console;
from rich.table     import Table;
from rich.prompt    import Prompt;
from prompt_toolkit import PromptSession;

from utils import TimestampToYMD;

console = Console();

API_KEY = "";

try:
  with open(".key") as f:
    API_KEY = f.readline().rstrip();
except Exception as e:
  console.print(
    "OpenRouter API key not found! Put it inside .key file.",
    style="bold red"
  );
  exit(1);

MODELS_LIST_URL = "https://openrouter.ai/api/v1/videos/models";
GENERATION_URL  = "https://openrouter.ai/api/v1/videos";

CmdPrompt = "> ";
ModelInd = -1;
Models = [];

################################################################################

def GetModelsList() -> list:
  res = [];

  try:
    response = requests.get(url=MODELS_LIST_URL);
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

def PrepareRequest(prompt : str, modelId : str) -> str:
  return json.dumps({
      "model": modelId
    , "prompt" : prompt
  });

################################################################################

def ProcessCommand(cmd : str) -> bool:
  models = [];

  spl = cmd.split(maxsplit=1);

  cmd = spl[0];

  args = "";

  if len(spl) >= 2:
    args = spl[1];

  # FIXME
  global ModelInd;
  global Models;

  if (cmd == "/exit" or cmd == "/quit"):
    return True;
  elif (cmd == "/brief"):
    if not Models:
      Models = GetModelsList();
    DisplayModelsBrief(Models);
  elif (cmd == "/models"):
    if not Models:
      Models = GetModelsList();
    DisplayModels(Models);
  elif (cmd == "/select"):
    if not args:
      console.print("Need model index!", style="bold red");
    else:
      if not args.isdigit():
        console.print("Invalid model index!", style="bold red");
      else:
        ModelInd = int(args);
        ModelInd += -1;
        if not Models:
          Models = GetModelsList();
        if (ModelInd < 0) or (ModelInd >= len(Models)):
          console.print("Invalid model index!", style="bold red");
        else:
          console.print(f"Selected model { Models[ModelInd]['modelId'] }");
          global CmdPrompt;
          CmdPrompt = f"{ Models[ModelInd]['modelId'] } > ";
  elif (cmd == "/prompt"):
    prompt = args;

    if ModelInd == -1:
      console.print("Select model first!", style="bold red");
    else:
      if not prompt:
        console.print("Prompt string is empty!", style="bold red");
      else:
        if not Models:
          Models = GetModelsList();
        req = PrepareRequest(prompt, Models[ModelInd]["modelId"]);
        print_json(req);
        choice = Prompt.ask("Proceed? ", choices=["y", "Y", "n", "N"]);
        coice = choice.lower();
        if choice == "y":
          response = requests.post(
            GENERATION_URL,
            headers={
              "Authorization": f"Bearer { API_KEY }",
              "Content-Type": "application/json",
            },
            json=json.loads(req)
          );

          if (response.status_code != requests.codes.ok):
            console.print("Got error:", style="bold red");

          result = response.json();
          print_json(json.dumps(result));

  return False;

################################################################################

def main():
  promptSession = PromptSession();

  shouldExit = False;

  try:
    while not shouldExit:
      inLine = promptSession.prompt(CmdPrompt).strip();

      if inLine:
        shouldExit = ProcessCommand(inLine);

  except (EOFError, KeyboardInterrupt):
    console.print();
    exit(1);

################################################################################

if __name__ == "__main__":
  main();
