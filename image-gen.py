import requests;
import json;
import argparse;
import base64;
import os;
import copy;
import time;

from rich           import box, print_json;
from rich.table     import Table;
from datetime       import datetime;
from prompt_toolkit import PromptSession;

from utils  import RenderCmdPrompt, TimestampToYMD, EncodeImage, console;
from common import DisplayCredits;

class ProgramDataClass:
  MODELS_LIST_URL = "https://openrouter.ai/api/v1/models?output_modalities=image";
  GENERATION_URL  = "https://openrouter.ai/api/v1/chat/completions";

  def __init__(self):
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

    self.CommandMode = False;
    self.ReferenceImage = "";
    self.Models = [];
    self.ModelsBrief = [];
    self.ModelInd = -1;

    # For displaying in command prompt.
    self.InModel = "";
    self.InImage = "";

################################################################################

def ListModels(silent : bool, pd : ProgramDataClass) -> list:
  try:
    response = requests.get(url=pd.MODELS_LIST_URL);
    result = response.json();

    table = Table(title="Available models", show_lines=True);

    table.add_column(
      "No.",
      justify="center",
      style="bold bright_white"
    );
    table.add_column(
      "Name",
      justify="center",
      style="bold bright_cyan",
      overflow="fold"
    );
    table.add_column(
      "Description",
      justify="left",
      style="bright_white",
      overflow="fold"
    );
    table.add_column(
      "Created",
      justify="center",
      style="bold"
    );
    table.add_column(
      "Price",
      justify="left",
      style="bold bright_yellow"
    );

    lst = result["data"];

    counter = 1;

    for item in lst:
      modelName = item["id"];
      modelDesc = item["description"];
      dateCreated = TimestampToYMD(item["created"]);

      modelPricing = item["pricing"];

      pricingStr = [];

      for k,v in modelPricing.items():
        pricingStr.append(f"{ k } = { v }");

      pricingStr = "\n".join(pricingStr);

      table.add_row(
        f"{ counter }",
        modelName,
        modelDesc,
        dateCreated,
        pricingStr
      );

      counter += 1;

    d = {
      "id" : "openrouter/free",
      "description" : "Automatic router to any free model.",
      "created" : "-",
      "pricing" : "0"
    };

    lst.append(d);

    table.add_row(
      f"{ counter }",
      d["id"],
      d["description"],
      d["created"],
      d["pricing"]
    );

    if not silent:
      console.print(table);

    return lst;

  except Exception as e:
    print(f"{ e }");
    exit(1);

################################################################################

def DisplayModelsBrief(models : list):
  table = Table(title="Available models", show_lines=True, box=None);

  table.add_column(
    "No.",
    justify="left",
    style="bold bright_white"
  );
  table.add_column(
    "Name",
    justify="left",
    style="bold bright_cyan"
  );
  table.add_column(
    "Pricing",
    justify="left",
    style="bold bright_yellow",
    overflow="fold"
  );

  counter = 1;

  for item in models:
    lstOut = [];

    if item[1]:
      for k,v in item[1].items():
        lstOut.append(f"{ k } = { v }");

    table.add_row(
      f"{ counter }", item[0], "0" if not lstOut else " | ".join(lstOut)
    );

    counter += 1;

  console.print(table);

################################################################################

def GetModelsListBrief(pd : ProgramDataClass) -> list:
  res = [];

  try:
    response = requests.get(url=pd.MODELS_LIST_URL);
    result = response.json();

    lst = result["data"];

    for item in lst:
      modelName = item["id"];
      pricing   = item["pricing"];

      pricingDict = {};

      for k,v in pricing.items():
        pricingDict[k] = v;

      res.append((modelName, pricing, pricingDict));

  except Exception as e:
    print(f"{ e }");
    exit(1);

  res.append(("openrouter/free", {}, {}));

  return res;

################################################################################

def ChooseModel(models : list) -> int:
  choice = 0;

  while True:
    entered = input(
      "Choose a model (? to display models again, -1 to exit): "
    ).rstrip();
    if (entered == "?"):
      DisplayModelsBrief(models);
      continue;
    try:
      choice = int(entered);

      if (choice == -1):
        return choice;

      if (choice <= 0 or choice > len(models)):
        print("No such model");
        continue;
      break;
    except:
      print("Please enter valid model number");

  choice -= 1;

  return choice;

################################################################################

def GenerateImage(prompt : str, modelName : str, pd : ProgramDataClass):
  jsonPayload = {
      "model": modelName
    , "messages": [
        {
          "role": "user",
          "content" : [
            {
              "type" : "text",
              "text" : prompt
            }
          ]
        }
      ]
    , "modalities": [ "image" ]
    , "image_config": {
      "aspect_ratio": "1:1"
    }
  };

  if pd.ReferenceImage:
    toAppend = {
      "type" : "image_url",
      "image_url" : {
        "url" : pd.ReferenceImage
      }
    };
    jsonPayload["messages"][0]["content"].append(toAppend);
  else:
    jsonPayload["messages"][0]["content"] = prompt;

  jsonToSend = json.dumps(jsonPayload);
  payloadCopy = copy.deepcopy(jsonPayload);

  if isinstance(payloadCopy["messages"][0]["content"], list):
    d = payloadCopy["messages"][0]["content"][1];
    imgUrl = d["image_url"]["url"];
    if "data:image" in imgUrl:
      imgUrl = f"{ d['image_url']['url'][:50] }...";
    d["image_url"]["url"] = imgUrl;

  jsonToPrint = json.dumps(payloadCopy);

  while True:
    print();
    print("Request to send:");
    print("-"*80);
    print_json(jsonToPrint);
    print("-"*80);
    print();
    reply = input(f"Proceed? (y/n): ").strip().lower();
    if reply in ("y", "yes"):
      break;
    elif reply in ("n", "no"):
      console.print("Aight den, not doing shit.", style="bold white");
      if not pd.CommandMode:
        exit(1);
      else:
        return;
    else:
      console.print("Please enter y or n", style="red");

  console.print("Reaching out to OpenRouter...", style="cyan");

  start = time.perf_counter();
  end = start;
  wasError = False;
  
  try:
    response = requests.post(
      url=pd.GENERATION_URL,
      headers={
        "Authorization": f"Bearer { pd.API_KEY }",
        "Content-Type": "application/json",
      },
      data=jsonToSend,
      timeout=240
    );
    end = time.perf_counter();  
    timeSpent = end - start;   
    console.print(
      f"Execution took {timeSpent:.6f} seconds", style="bold green"
    );  
  except Exception as e:
    wasError = True;
    console.print("Failed to perform request!", style="bold red");
    console.print(f"{ e }", style="bold red");
    
  if wasError:
    if not pd.CommandMode:
      exit(1);
    else:
      return;
      
  if (response.status_code != requests.codes.ok):
    console.print("Got error:", style="bold red");
    print_json(json.dumps(response.json()));

    if not pd.CommandMode:
      exit(1);
    else:
      return;
  
  result = None;
  
  try:
    result = response.json();
  except Exception as e:
    console.print(
      "Error while trying to deserialize response object as JSON!",
      style="bold red"
    );
    console.print(f"{ e }");
    console.print("-"*80);
    console.print(response.text);
    console.print("-"*80);
    return;

  if "error" in result.keys():
    console.print("Got error:", style="bold red");
    print_json(json.dumps(result));
    return;

  n = datetime.now().replace(microsecond=0);
  ns = n.strftime("%Y-%m-%d-%H-%M-%S");

  os.makedirs("generated", exist_ok=True);
  os.makedirs("raw",       exist_ok=True);
  os.makedirs("errors",    exist_ok=True);

  with open(f"raw/full-reply-{ ns }.txt", "w") as f:
    f.write(json.dumps(result, indent=2));

  if result.get("choices"):
    message = result["choices"][0]["message"];
    if message.get("images"):
      imageCount = 1;
      for image in message["images"]:
        output = image["image_url"]["url"];
        metadata, encoded_image = output.split(",", 1);
        print(f"Got { metadata }");
        extension = None;
        if ("image/jpg" in metadata) or ("image/jpeg" in metadata):
          extension = ".jpg";
        elif "image/png" in metadata:
          extension = ".png";
        elif "image/svg" in metadata:
          extension = ".svg";
        elif "image/webp" in metadata:
          extension = ".webp";
        image_data = base64.b64decode(encoded_image);
        dump_fname = f"raw/output-{ ns }_{ imageCount }.txt";
        with open(dump_fname, "w") as f:
          f.write(prompt);
          f.write("\n");
          f.write(modelName);
          f.write("\n");
          f.write(metadata);
          f.write("\n");
          f.write(encoded_image);
          f.write("\n");
        image_fname = f"generated/image-{ ns }_{ imageCount }{ extension }";
        if extension is not None:
          with open(image_fname, "wb") as f:
            f.write(image_data);
          console.print("Written ", end="");
          console.print(f"{ image_fname }!", style="bold bright_white");
        else:
          console.print(
            f"Unknown image format - check { dump_fname }",
            style="bold bright_yellow"
          );
        imageCount += 1;

      if ("openrouter/auto" in modelName) or ("openrouter/free" in modelName):
        console.print("Model used: ", end="");
        console.print(f"{ result['model'] }", style="bold cyan");

      console.print("Cost:");
      console.print("-"*80);
      print_json(json.dumps(result["usage"]));
      console.print("-"*80);
      console.print();
    else:
      console.print(
        "Received no images - it might've fallen back to text generation.",
        style="bold yellow"
      );
      fname = f"errors/{ ns }-full-response.txt";
      fullResponse = json.dumps(result, indent=2);
      with open(fname, "w") as f:
        f.write(fullResponse);
      console.print(f"Written { fname }");

################################################################################

def DisplayModel(modelInd : int, model : dict):
  table = Table(show_lines=True);

  table.add_column(
    "No.",
    justify="center",
    style="bold bright_white"
  );
  table.add_column(
    "Name",
    justify="center",
    style="bold bright_cyan",
    overflow="fold"
  );
  table.add_column(
    "Description",
    justify="left",
    style="bright_white",
    overflow="fold"
  );
  table.add_column(
    "Created",
    justify="center",
    style="bold"
  );
  table.add_column(
    "Pricing",
    justify="left",
    style="bold bright_yellow",
    overflow="fold"
  );

  modelName = model["id"];

  pricing = [];

  pricingStr = "";
  dateCreated = "-";
  descStr = "";

  if "openrouter/free" not in modelName:
    for k,v in model["pricing"].items():
      pricing.append(f"{ k } = { v }");
    pricingStr = " | ".join(pricing);
    dateCreated = TimestampToYMD(model["created"]);
    descStr = model["description"];
  else:
    pricingStr = "0";
    descStr = "Auto router to random free model.";

  table.add_row(
    f"{ modelInd + 1 }",
    modelName,
    descStr,
    dateCreated,
    pricingStr
  );

  console.print(table);

CommandHandlers = {}

AllCommands = {
    "/brief"   : [
      "/brief", "Display models brief information"
  ]
  , "/credits" : [
    "/credits", "Display financial information"
  ]
  , "/exit" : [
    "/exit", "Nuff said"
  ]
  , "/help" : [
    "/help", "Display this"
  ]
  , "/image" : [
    "/image [<PATH TO FILE>]", "Set / reset base64 encoded image file"
  ]
  , "/info" : [
    "/info <MODEL INDEX>", "Display information about model no. <MODEL INDEX>"
  ]
  , "/models" : [
    "/models", "Display list of available models"
  ]
  , "/prompt" : [
    "/prompt <TEXT>", "Prepare request to image generation"
  ]
  , "/select" : [
    "/select <MODEL INDEX>", "Select model from the /models list"
  ]
  , "/url" : [
    "/url [<IMAGE URL>]", "Set / reset reference image URL"
  ]
};

################################################################################

def Command(name : str):
  def _decorator(f):
    f.FunctionName = name;
    CommandHandlers[name] = f;
    return f;
  return _decorator;

################################################################################

@Command("/help")
def ProcessHelp(args : str, pd : ProgramDataClass) -> bool:
  table = Table(title="Available commands", show_lines=False);

  table.add_column("Command", style="bold cyan");
  table.add_column("Description", style="bold white");

  sortedKeys = sorted(CommandHandlers.keys());

  for k in sortedKeys:
    commandHelp = AllCommands[k][0] if k in AllCommands.keys() else k;
    helpText = AllCommands[k][1] if k in AllCommands.keys() else "(no help)";
    table.add_row(commandHelp, helpText);

  console.print(table);

  return False;

################################################################################

@Command("/info")
def ProcessInfo(args : str, pd : ProgramDataClass) -> bool:
  try:
    if not args:
      console.print("Need model index!", style="bold red");
    else:
      pd.ModelInd = int(args);
      if not pd.Models:
        pd.Models = ListModels(True, pd);
      pd.ModelInd -= 1;
      if (pd.ModelInd < 0) or (pd.ModelInd >= len(pd.Models)):
        console.print("Invalid model index", style="bold red");
      else:
        DisplayModel(pd.ModelInd, pd.Models[pd.ModelInd]);
  except ValueError as _:
    console.print("Not a number!", style="bold red");

  return False;

################################################################################

@Command("/credits")
def ProcessCredits(args : str, pd : ProgramDataClass) -> bool:
  DisplayCredits(pd.API_KEY);
  return False;

################################################################################

@Command("/models")
def ProcessModels(args : str, pd : ProgramDataClass) -> bool:
  pd.Models = ListModels(False, pd);
  return False;

################################################################################

@Command("/brief")
def ProcessBrief(args : str, pd : ProgramDataClass) -> bool:
  if not pd.ModelsBrief:
    pd.ModelsBrief = GetModelsListBrief(pd);
  DisplayModelsBrief(pd.ModelsBrief);
  return False;

################################################################################

@Command("/select")
def ProcessSelect(args : str, pd : ProgramDataClass) -> bool:
  try:
    pd.ModelInd = int(args);
  except ValueError as e:
    console.print("Not a number", style="bold red");
    return False;

  if not pd.Models:
    pd.Models = ListModels(True, pd);

  pd.ModelInd -= 1;

  if (pd.ModelInd < 0) or (pd.ModelInd >= len(pd.Models)):
    console.print("Invalid model index", style="bold red");
  else:
    console.print(f"Selected model '{ pd.Models[pd.ModelInd]['id'] }'");
    pd.InModel = pd.Models[pd.ModelInd]['id'];

  return False;

################################################################################

@Command("/image")
@Command("/url")
def ProcessImage(args : str, pd : ProgramDataClass) -> bool:
  if not args:
    pd.ReferenceImage = "";
    console.print("Reference image is reset.", style="bold white");
    pd.InImage = "";
  else:
    pd.ReferenceImage = (
      EncodeImage(args) if (ProcessImage.FunctionName == "/image") else args
    )
    if pd.ReferenceImage:
      console.print(
        f"Reference image set: '{ args }'", style="bold white"
      );
      pd.InImage = args;
  return False;

################################################################################

@Command("/prompt")
def ProcessPrompt(args : str, pd : ProgramDataClass) -> bool:
  prompt = args;
  if not prompt:
    console.print("Empty prompt string!", style="bold red");
    return False;

  if pd.ModelInd == -1:
    console.print("Select model first!", style="bold red");
    return False;
  else:
    GenerateImage(prompt, pd.Models[pd.ModelInd]["id"], pd);

  return False;

################################################################################

@Command("/exit")
@Command("/quit")
def ProcessExit(args : str, pd : ProgramDataClass) -> bool:
  return True;

################################################################################

def ProcessCommands(pd : ProgramDataClass):
  console.print("Starting command mode.", style="bold white");
  console.print("/help to display help.");
  console.print("/exit to exit.");

  promptSession = PromptSession();

  shouldExit = False;

  try:
    while not shouldExit:
      cmdPrompt = RenderCmdPrompt(pd.InModel, pd.InImage);

      inLine = promptSession.prompt(cmdPrompt).strip();

      spl = inLine.split(maxsplit=1);

      if spl:
        command = spl[0];

        args = "";

        if len(spl) >= 2:
          args = spl[1];

        if command in CommandHandlers.keys():
          shouldExit = CommandHandlers[command](args, pd);
        else:
          console.print("Invalid command", style="bold red");
  except (EOFError, KeyboardInterrupt):
    console.print();
    exit(1);

################################################################################

def main():
  pd = ProgramDataClass();

  parser = argparse.ArgumentParser(
    epilog="Runs in command mode if started without arguments."
  );

  group = parser.add_mutually_exclusive_group();

  group.add_argument(
    "--prompt",
    type=str,
    default="",
    help="Prompt for image generation"
  );
  group.add_argument(
    "--file",
    type=str,
    help="Read prompt from file"
  );
  group.add_argument(
    "--models",
    action="store_true",
    help="List available models"
  );

  args = parser.parse_args();

  prompt = args.prompt;

  if (args.file):
    try:
      with open(args.file, "r") as f:
        prompt = "".join(f.readlines()).replace("\n", " ");
    except Exception as e:
      console.print(f"{ e }", style="red");
      exit(1);

  if (args.models):
    ListModels(False, pd);
  elif (prompt):
    pd.Models = GetModelsListBrief(pd);
    DisplayModelsBrief(pd.Models);
    DisplayCredits(pd.API_KEY);
    choice = ChooseModel(pd.Models);
    if (choice == -1):
      exit(1);
    console.print("Using model: ", end="");
    console.print(
      f"{ pd.Models[choice][0] }",
      style="bold bright_white"
    );
    GenerateImage(prompt, pd.Models[choice][0], pd);
  else:
    pd.CommandMode = True;
    ProcessCommands(pd);

################################################################################

if __name__ == "__main__":
  main()
