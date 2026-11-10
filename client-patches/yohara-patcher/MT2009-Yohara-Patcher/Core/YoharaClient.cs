using System;
using System.IO;

namespace MT2009Yohara.Core
{
	// MT2009_PLUS_YOHARA_PATCHER_V1: which client lies in a folder.
	//
	// The Yohara (3.x) client and the 2.x client look alike (metin2client.exe,
	// pack\, even CLIENT_VERSION 2.0.x in the Yohara base), so the folder is
	// told apart by:
	//   - YOHARA_VERSION in the client root (published by the Yohara mirror,
	//     written by this patcher), or
	//   - a pack only the Yohara client has (its maps: Hydra, Balathor,
	//     Seogan) - for Yohara clients installed from the test patches,
	//     before the patcher ever ran there.
	// The 2.x patcher (client-patches/patcher, PatchCore.IsYoharaClient) uses
	// the same markers to refuse a Yohara folder.
	public enum ClientKind
	{
		// no pack\ folder: not a client at all
		None,
		// a client folder without any Yohara marker: the 2.x client
		Classic2x,
		Yohara
	}

	public static class YoharaClient
	{
		public const string StampFile = "YOHARA_VERSION";

		public static readonly string[] MarkerPacks = new string[]
		{
			"pack/hydra_map.index",
			"pack/balathor_map.index",
			"pack/seoganland_map.index"
		};

		public static string Local(string root, string relative)
		{
			return Path.Combine(root, relative.Replace('/', Path.DirectorySeparatorChar).Replace('\\', Path.DirectorySeparatorChar));
		}

		public static bool HasYoharaMarker(string root)
		{
			if (File.Exists(Local(root, StampFile)))
			{
				return true;
			}
			foreach (string marker in MarkerPacks)
			{
				if (File.Exists(Local(root, marker)))
				{
					return true;
				}
			}
			return false;
		}

		public static ClientKind Detect(string root)
		{
			if (HasYoharaMarker(root))
			{
				return ClientKind.Yohara;
			}
			if (Directory.Exists(Local(root, "pack")))
			{
				return ClientKind.Classic2x;
			}
			return ClientKind.None;
		}

		// "3.0.23" from YOHARA_VERSION, or null.
		public static string ReadStamp(string root)
		{
			try
			{
				string path = Local(root, StampFile);
				if (!File.Exists(path))
				{
					return null;
				}
				string text = File.ReadAllText(path).Trim();
				return text.Length == 0 || text.Length > 40 ? null : text;
			}
			catch
			{
				return null;
			}
		}
	}
}
