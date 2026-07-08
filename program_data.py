from urllib.parse import quote;
from rich.console import Console;

console = Console();

class ProgramDataClass:
  MODELS_LIST_URL_IMAGE = "https://openrouter.ai/api/v1/models?output_modalities=image";
  GENERATION_URL_IMAGE  = "https://openrouter.ai/api/v1/chat/completions";

  MODELS_LIST_URL_VIDEO = "https://openrouter.ai/api/v1/videos/models";
  GENERATION_URL_VIDEO  = "https://openrouter.ai/api/v1/videos";

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

    #
    # The "heaviest" model being riverflow pro generates image in about
    # 3 minutes. So 5 for read timeout should be enough.
    #
    self.RequestsTimeout = (10, 300);

    #
    # For socks5 proxying.
    #
    self.Proxies = None;

  # ----------------------------------------------------------------------------

  def ProcessSocksCreds(self, creds : dict):
    username = creds["username"];
    passwd   = quote(creds["password"], safe='');
    host     = creds["host"];
    port     = creds["port"];

    self.Proxies = {
      'http' : f'socks5h://{ username }:{ passwd }@{ host }:{ port }',
      'https': f'socks5h://{ username }:{ passwd }@{ host }:{ port }'
    };
