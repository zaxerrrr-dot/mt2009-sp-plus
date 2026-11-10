using System;
using System.Configuration;

namespace N2_Patcher.Model
{
	// MT2009_PLUS_YOHARA_PATCHER_V1: settings of the Yohara patcher
	// (MT2009-Yohara-Patcher.exe.config, optional - the defaults are built in).
	// The shared 2.x code (NewsSystem) reads Config.GetNews() from here.
	internal static class Config
	{
		public const string DefaultMirror = "http://141.94.100.53/aktualizacje/yohara/";

		private static readonly string mirror;
		private static readonly string channel;
		private static readonly string closeOnStart;
		private static readonly string homepage;
		private static readonly string discord;
		private static readonly string vote;
		private static readonly string start;
		private static readonly string config;

		static Config()
		{
			Config.mirror = Config.Read("MirrorUrl", DefaultMirror);
			Config.channel = Config.Read("Channel", "");
			Config.closeOnStart = Config.Read("CloseOnClientStart", "true");
			Config.homepage = Config.Read("Homepage", "https://metin2sp.pl");
			Config.discord = Config.Read("Discord", "https://discord.com/invite/vGE3T9gpm");
			Config.vote = Config.Read("Vote4Coins", "");
			Config.start = Config.Read("Start", "metin2client.exe");
			Config.config = Config.Read("Config", "config.exe");
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

		// "--serwer" / "--kanal" on the command line win over the file
		public static string MirrorOverride;

		public static string ChannelOverride;

		public static string GetMirror()
		{
			return string.IsNullOrEmpty(Config.MirrorOverride) ? Config.mirror : Config.MirrorOverride;
		}

		public static string GetChannel()
		{
			return Config.ChannelOverride ?? Config.channel;
		}

		public static string GetNews()
		{
			return MT2009Yohara.Core.Mirror.NewsUrl(Config.GetMirror());
		}

		public static bool isCLoseOnStart()
		{
			return Config.closeOnStart.ToLowerInvariant() == "true";
		}

		public static string getHomepage()
		{
			return Config.homepage;
		}

		public static string getDiscord()
		{
			return Config.discord;
		}

		public static string getVoteForCoins()
		{
			return Config.vote;
		}

		public static string GetStartFile()
		{
			return Config.start;
		}

		public static string GetConfigFile()
		{
			return Config.config;
		}
	}
}
