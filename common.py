import requests;
import json;

from rich       import print_json;
from rich.table import Table;

from program_data import ProgramDataClass;
from utils        import console;

def DisplayCredits(API_KEY : str, pd : ProgramDataClass):
  CREDITS_URL = "https://openrouter.ai/api/v1/credits";

  response = requests.get(
    url=CREDITS_URL,
    headers={
      "Authorization": f"Bearer { API_KEY }",
    },
    proxies=pd.Proxies,
    timeout=pd.RequestsTimeout
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

  table.add_column("Total", justify="center", style="bold green");
  table.add_column("Used",  justify="center", style="bold red");
  table.add_column("Left",  justify="center", style="bold yellow");

  totalCreds = result.get("data", {}).get("total_credits", -1);
  totalUsage = result.get("data", {}).get("total_usage", -1);

  credsLeft = totalCreds - totalUsage;

  table.add_row(f"{ totalCreds }", f"{ totalUsage }", f"{ credsLeft }");

  console.print(table);
