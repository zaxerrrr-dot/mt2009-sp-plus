using N2_Patcher.Control;
using System;
using System.Collections.Specialized;
using System.Configuration;

namespace N2_Patcher.Model
{
	internal static class Config
	{
		private readonly static string crypted;

		private readonly static string closeOnStart;

		private readonly static string userAgent;

		private readonly static string voteForCoins;

		private readonly static string homepage;

		private readonly static string discord;

		private readonly static string clientdata;

		private readonly static string patchlist;

		private readonly static string slider;

		private readonly static string stats;

		private readonly static string news;

		private readonly static string update;

		private readonly static string config;

		private readonly static string start;

		private readonly static string startToken;

		// MT2009 PLUS: the values used when MT2009-Patcher.exe.config is missing
		// or lacks a key, so the exe also works on its own.
		public const string DefaultServer = "http://141.94.100.53/patcher/";

		static Config()
		{
			Config.crypted = Config.Read("PatchServerSettingsCrypted", "false");
			Config.closeOnStart = Config.Read("CloseOnClientStart", "true");
			Config.userAgent = ".NET Framework Web Application / Patcher Client";
			Config.voteForCoins = Config.Read("Vote4Coins", "https://buycoffee.to/mt2009plus");
			Config.homepage = Config.Read("Homepage", "https://metin2sp.pl");
			Config.discord = Config.Read("Discord", "https://discord.com/invite/vGE3T9gpm");
			Config.clientdata = Config.Read("Clientdata", DefaultServer + "files/");
			Config.patchlist = Config.Read("Patchlist", DefaultServer + "patchlist.json");
			Config.slider = Config.Read("Slider", "");
			Config.stats = Config.Read("Stats", "");
			Config.news = Config.Read("News", DefaultServer + "news.json");
			Config.update = Config.Read("Update", "");
			Config.config = Config.Read("Config", "config.exe");
			Config.start = Config.Read("Start", "metin2client.exe");
			Config.startToken = Config.Read("StartToken", "false");
		}

		private static string Read(string key, string fallback)
		{
			string value = null;
			try
			{
				value = ConfigurationManager.AppSettings.Get(key);
			}
			catch
			{
			}
			return value ?? fallback;
		}

		private static string Get_clear_key(string value)
		{
			string str;
			str = (Config.crypted.ToLower() != "true" || string.IsNullOrEmpty(value) ? value : CryptoService.DecryptString(value));
			return str;
		}

		public static string GetClientdata()
		{
			return Config.Get_clear_key(Config.clientdata);
		}

		public static string GetConfigFile()
		{
			return Config.config;
		}

		public static string getDiscord()
		{
			return Config.discord;
		}

		public static string getHomepage()
		{
			return Config.homepage;
		}

		public static string GetNews()
		{
			return Config.Get_clear_key(Config.news);
		}

		public static string GetPatchlist()
		{
			return Config.Get_clear_key(Config.patchlist);
		}

		public static string getPrivateKey()
		{
			return "8Abz9qM4x5ev7nMrWrJZmrRpUsBk37k0SdkL2bq0";
		}

		public static string GetSlider()
		{
			return Config.Get_clear_key(Config.slider);
		}

		public static string GetStartFile()
		{
			return Config.start;
		}

		public static string GetStats()
		{
			return Config.Get_clear_key(Config.stats);
		}

		public static string GetUpdateFile()
		{
			return Config.update;
		}

		public static string getUserAgent()
		{
			return Config.userAgent;
		}

		public static string getVoteForCoins()
		{
			return Config.voteForCoins;
		}

		public static bool isCLoseOnStart()
		{
			return Config.closeOnStart.ToLower() == "true";
		}

		public static bool isStartToken()
		{
			return Config.startToken.ToLower() == "true";
		}
	}
}
