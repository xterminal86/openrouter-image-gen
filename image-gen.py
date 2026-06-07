import requests;
import json;
import argparse;
import base64;

from rich         import box, print_json;
from rich.table   import Table;
from rich.console import Console;
from datetime     import datetime;

console = Console();

MODELS_LIST_URL = "https://openrouter.ai/api/v1/models?output_modalities=image";
GENERATION_URL  = "https://openrouter.ai/api/v1/chat/completions";

################################################################################

def ListModels():
  try:
    response = requests.get(url=MODELS_LIST_URL);
    result = response.json();

    table = Table(title="Available models", show_lines=True);

    table.add_column("No.",         justify="left", style="bold bright_white");
    table.add_column("Name",        justify="left", style="bold bright_cyan", overflow="fold");
    table.add_column("Description", justify="left", style="bright_white", overflow="fold");
    table.add_column("Created",     justify="left", style="bold");
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

    console.print(table);

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
    dick = [];
    for k,v in item[1].items():
      dick.append(f"{ k } = { v }");

    table.add_row(f"{ counter }", item[0], " | ".join(dick));
    counter += 1;

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

  apiKey = "";

  with open(".key") as f:
    apiKey = f.readline().rstrip();

  console.print("Reaching out to OpenRouter...", style="cyan");

  response = requests.post(
    url=GENERATION_URL,
    headers={
      "Authorization": f"Bearer { apiKey }",
      "Content-Type": "application/json",
    },
    data=jsonToSend
  );

  result = response.json();

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
        n = datetime.now().replace(microsecond=0);
        ns = n.strftime("%Y-%m-%d-%H-%M-%S");
        dump_fname = f"output-{ ns }_{ imageCount }.txt";
        with open(dump_fname, "w") as f:
          f.write(modelName);
          f.write("\n");
          f.write(metadata);
          f.write("\n");
          f.write(encoded_image);
          f.write("\n");
        image_fname = f"image-{ ns }_{ imageCount }{ extension }";
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

################################################################################

def main():
  parser = argparse.ArgumentParser();

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
    "--list",
    action="store_true",
    help="List available models"
  );

  args = parser.parse_args();

  prompt = args.prompt;

  if (args.file):
    try:
      with open(args.file, "r") as f:
        prompt = "".join(f.readlines());
    except Exception as e:
      console.print(f"{ e }", style="red");
      exit(1);

  if (args.list):
    ListModels();
  elif (prompt):
    models = GetModelsListBrief();
    DisplayModels(models);
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
    parser.print_help();

################################################################################

if __name__ == "__main__":
  main()
