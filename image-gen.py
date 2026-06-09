import requests;
import json;
import argparse;
import base64;
import os;

from rich         import box, print_json;
from rich.table   import Table;
from rich.console import Console;
from datetime     import datetime;

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
  exit (1);

MODELS_LIST_URL = "https://openrouter.ai/api/v1/models?output_modalities=image";
GENERATION_URL  = "https://openrouter.ai/api/v1/chat/completions";
CREDITS_URL = "https://openrouter.ai/api/v1/credits"

################################################################################

def ListModels(silent : bool = False) -> list:
  try:
    response = requests.get(url=MODELS_LIST_URL);
    result = response.json();

    table = Table(title="Available models", show_lines=True);

    table.add_column("No.",         justify="left", style="bold bright_white");
    table.add_column("Name",        justify="left", style="bold bright_cyan", overflow="fold");
    table.add_column("Description", justify="left", style="bright_white", overflow="fold");
    table.add_column("Created",     justify="center", style="bold");
    table.add_column("Price",       justify="left", style="bold bright_yellow");

    lst = result["data"];

    counter = 1;

    for item in lst:
      modelName = item["id"];
      modelDesc = item["description"];
      dateCreated = datetime.fromtimestamp(item["created"]).strftime("%Y-%m-%d");

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

def DisplayModels(models : list):
  table = Table(title="Available models", show_lines=True, box=None);

  table.add_column("No.", justify="left", style="bold bright_white");
  table.add_column("Name", justify="left",style="bold bright_cyan");
  table.add_column("Pricing",justify="left", style="bold bright_yellow", overflow="fold");

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

def DisplayCredits():
  response = requests.get(
    url=CREDITS_URL,
    headers={
      "Authorization": f"Bearer { API_KEY }",
    }
  );

  if (response.status_code != requests.codes.ok):
    console.print(
      "Got error while trying to get credits information:",
      style="bold red"
    );
    print_json(json.dumps(response.json()));
    exit(1);

  result = response.json();

  table = Table(title="Credits", show_lines=True);

  table.add_column("Total", style="bold green");
  table.add_column("Used", style="bold red");
  table.add_column("Left", style="bold yellow");

  totalCreds = result.get("data", {}).get("total_credits", -1);
  totalUsage = result.get("data", {}).get("total_usage", -1);

  credsLeft = totalCreds - totalUsage;

  table.add_row(f"{ totalCreds }", f"{ totalUsage }", f"{ credsLeft }");

  console.print(table);

################################################################################

def GetModelsListBrief() -> list:
  res = [];

  try:
    response = requests.get(url=MODELS_LIST_URL);
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
      DisplayModels(models);
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

def GenerateImage(prompt : str, modelName : str):
  jsonPayload = {
      "model": modelName
    , "messages": [
        {
          "role": "user",
          "content": prompt
        }
      ]
    , "modalities": [ "image" ]
    , "image_config": {
      "aspect_ratio": "1:1"
    }
  };

  jsonToSend = json.dumps(jsonPayload);

  while True:
    print();
    print("Request to send:");
    print("-"*80);
    #print(f"{ jsonToSend }");
    print_json(jsonToSend);
    print("-"*80);
    print();
    reply = input(f"Proceed? (y/n): ").strip().lower();
    if reply in ("y", "yes"):
      break;
    elif reply in ("n", "no"):
      print("Aight den, not doing shit.");
      exit(1);
    else:
      console.print("Please enter y or n", style="red");

  console.print("Reaching out to OpenRouter...", style="cyan");

  response = requests.post(
    url=GENERATION_URL,
    headers={
      "Authorization": f"Bearer { API_KEY }",
      "Content-Type": "application/json",
    },
    data=jsonToSend
  );

  if (response.status_code != requests.codes.ok):
    console.print("Got error:", style="bold red");
    print_json(json.dumps(response.json()));
    exit(1);

  result = response.json();

  n = datetime.now().replace(microsecond=0);
  ns = n.strftime("%Y-%m-%d-%H-%M-%S");

  if not os.path.exists("raw"):
    os.mkdir("raw");

  os.makedirs("generated", exist_ok=True);
  os.makedirs("raw",       exist_ok=True);
  os.makedirs("errors",    exist_ok=True);

  with open(f"raw/full-reply-{ ns }.txt", "w") as f:
    f.write(json.dumps(result, indent=2));

  # The generated image will be in the assistant message
  if result.get("choices"):
    message = result["choices"][0]["message"];
    if message.get("images"):
      imageCount = 1;
      for image in message["images"]:
        #print(image)
        #print("-"*80)
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

    if ("openrouter/auto" in modelName) or ("openrouter/free" in modelName):
      console.print("Model used: ", end="");
      console.print(f"{ result['model'] }", style="bold cyan");

    console.print("Cost:");
    console.print("-"*80);
    print_json(json.dumps(result["usage"]));
    console.print("-"*80);
    console.print();

################################################################################

def ProcessCommands():
  cmds = {
    "/exit" : "Nuff said",
    "/credits" : "Display financial information",
    "/models" : "Display list of available models",
    "/prompt <TEXT>" : "Prepare request to image generation",
    "/select <NUMBER>" : "Select model from the /models list"
  };

  models = [];
  modelInd = -1;

  cmdPrompt = "> ";

  try:
    while True:
      inLine = input(cmdPrompt).strip();

      spl = inLine.split(maxsplit=1);

      if spl:
        command = spl[0];

        if command == "/exit":
          break;
        elif command == "/credits":
          DisplayCredits();
        elif command == "/models":
          models = ListModels();
        elif command == "/select":
          try:
            modelInd = int(spl[1]);
            if not models:
              models = ListModels(True);
            modelInd -= 1;

            if (modelInd < 0) or (modelInd >= len(models)):
              console.print("Invalid model index", style="bold red");
            else:
              console.print(f"Selected model '{ models[modelInd]['id'] }'");
              cmdPrompt = f"{ models[modelInd]['id'] } > ";

          except ValueError as e:
            console.print("Not a number", style="bold red");
        elif command == "/prompt":
          prompt = spl[1];
          if modelInd == -1:
            console.print("Select model first", style="bold red");
          else:
            GenerateImage(prompt, models[modelInd]["id"]);
        elif command == "/help":
          table = Table(title="Available commands", show_lines=False);

          table.add_column("Command", style="bold cyan");
          table.add_column("Description", style="bold white");

          for k,v in cmds.items():
            table.add_row(k, v);

          console.print(table);
        else:
          console.print("Invalid command", style="bold red");
  except EOFError:
    console.print();
    exit(1);

################################################################################

def main():
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
    ListModels();
  elif (prompt):
    models = GetModelsListBrief();
    DisplayModels(models);
    DisplayCredits();
    choice = ChooseModel(models);
    if (choice == -1):
      exit(1);
    console.print("Using model: ", end="");
    console.print(
      f"{ models[choice][0] }",
      style="bold bright_white"
    );
    GenerateImage(prompt, models[choice][0]);
  else:
    ProcessCommands();

################################################################################

if __name__ == "__main__":
  main()
