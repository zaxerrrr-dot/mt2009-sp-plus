using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Text.RegularExpressions;

namespace MT2009Yohara.Core
{
	// MT2009_PLUS_YOHARA_MIRROR_V1 - the Yohara update mirror
	// (http://141.94.100.53/aktualizacje/yohara/, built by tools/make_mirror.py):
	//
	//   channels.json            {"marker", "schema", "default": "test",
	//                             "channels": {"test": {"manifest": "test/manifest.json", "version": "3.0.23"}, ...}}
	//   <channel>/manifest.json  Manifest below
	//   files/<aa>/<sha256>      every file by its SHA-256 (aa = first 2 hex digits)
	//   news.json                news of the Yohara patcher window
	//
	// A file is always downloaded from <mirror>/files/<aa>/<sha256>: the
	// address is built here, never taken from the manifest, so the patcher
	// cannot be pointed at another server's (2.x, GitHub) files.
	public static class Mirror
	{
		public const string Marker = "MT2009_PLUS_YOHARA_MIRROR_V1";

		// highest manifest schema this patcher understands; a newer one needs
		// a newer patcher (self-update first)
		public const int Schema = 1;

		public static string Normalize(string mirrorUrl)
		{
			if (string.IsNullOrEmpty(mirrorUrl))
			{
				throw new ArgumentException("brak adresu serwera aktualizacji");
			}
			return mirrorUrl.EndsWith("/") ? mirrorUrl : mirrorUrl + "/";
		}

		public static string FileUrl(string mirrorUrl, string sha256)
		{
			string sha = sha256.ToLowerInvariant();
			return string.Concat(Normalize(mirrorUrl), "files/", sha.Substring(0, 2), "/", sha);
		}

		public static string ChannelsUrl(string mirrorUrl)
		{
			return Normalize(mirrorUrl) + "channels.json";
		}

		public static string NewsUrl(string mirrorUrl)
		{
			return Normalize(mirrorUrl) + "news.json";
		}

		private static readonly Regex Sha = new Regex("^[0-9a-fA-F]{64}$");

		private static readonly Regex ChannelName = new Regex("^[a-z0-9][a-z0-9_-]{0,31}$");

		private static readonly Regex RelativeJson = new Regex("^[a-z0-9_-]+/[a-z0-9_.-]+\\.json$");

		public static bool IsSha256(string text)
		{
			return text != null && Sha.IsMatch(text);
		}

		public static bool IsChannelName(string text)
		{
			return text != null && ChannelName.IsMatch(text);
		}

		// Files the Yohara mirror must never hand out: the 2.x patcher and the
		// 2.x update lists (the two patchers never touch each other's files).
		private static readonly string[] Foreign = new string[]
		{
			"MT2009-Patcher.exe", "MT2009-Patcher.exe.config", "MT2009-Patcher.exe.bak",
			"update-manifest-mt2009.json", "client-files.json"
		};

		// Relative path of a client file: no drive, no rooted path, no "..",
		// no empty parts; both separators allowed.
		public static bool IsSafePath(string name)
		{
			if (string.IsNullOrEmpty(name) || name.Length > 260)
			{
				return false;
			}
			if (name.IndexOf(':') >= 0 || name.StartsWith("\\") || name.StartsWith("/"))
			{
				return false;
			}
			foreach (char c in name)
			{
				if (c < 32 || c == '*' || c == '?' || c == '"' || c == '<' || c == '>' || c == '|')
				{
					return false;
				}
			}
			foreach (string part in name.Split(new char[] { '\\', '/' }))
			{
				if (part == ".." || part == "." || part.Length == 0 || part.EndsWith(" ") || part.EndsWith("."))
				{
					return false;
				}
			}
			return true;
		}

		public static bool IsForeign(string name)
		{
			string file = name.Replace('\\', '/');
			foreach (string f in Foreign)
			{
				if (string.Equals(file, f, StringComparison.OrdinalIgnoreCase))
				{
					return true;
				}
			}
			// the patcher's own work folder
			return file.StartsWith(Updater.WorkFolder + "/", StringComparison.OrdinalIgnoreCase);
		}

		public static ChannelsIndex ParseChannels(string json)
		{
			ChannelsIndex index = JsonConvert.DeserializeObject<ChannelsIndex>(json);
			if (index == null || index.Marker != Marker)
			{
				throw new FormatException("to nie jest lista kanałów serwera aktualizacji Yohary");
			}
			if (index.Channels == null || index.Channels.Count == 0)
			{
				throw new FormatException("serwer aktualizacji nie ma żadnego kanału");
			}
			foreach (KeyValuePair<string, ChannelInfo> pair in index.Channels)
			{
				if (!IsChannelName(pair.Key) || pair.Value == null || pair.Value.Manifest == null || !RelativeJson.IsMatch(pair.Value.Manifest))
				{
					throw new FormatException("zły wpis kanału: " + pair.Key);
				}
			}
			return index;
		}

		public static Manifest ParseManifest(string json, string expectedChannel)
		{
			Manifest manifest = JsonConvert.DeserializeObject<Manifest>(json);
			if (manifest == null || manifest.Marker != Marker)
			{
				throw new FormatException("to nie jest lista plików klienta Yohara");
			}
			if (expectedChannel != null && manifest.Channel != expectedChannel)
			{
				throw new FormatException(string.Format("lista jest dla kanału \"{0}\", nie \"{1}\"", manifest.Channel, expectedChannel));
			}
			if (string.IsNullOrEmpty(manifest.Version) || manifest.Files == null || manifest.Files.Count == 0)
			{
				throw new FormatException("lista plików jest pusta");
			}
			HashSet<string> seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
			foreach (ManifestFile file in manifest.Files)
			{
				if (file == null || !IsSafePath(file.Path) || IsForeign(file.Path) || !IsSha256(file.Sha256) || file.Size < 0)
				{
					throw new FormatException("zły wpis na liście plików: " + (file == null ? "(pusty)" : file.Path));
				}
				if (!seen.Add(file.Path.Replace('\\', '/')))
				{
					throw new FormatException("plik dwa razy na liście: " + file.Path);
				}
			}
			if (manifest.Delete != null)
			{
				foreach (string path in manifest.Delete)
				{
					if (!IsSafePath(path) || IsForeign(path) || seen.Contains(path.Replace('\\', '/')))
					{
						throw new FormatException("zły wpis do usunięcia: " + path);
					}
				}
			}
			if (manifest.Patcher != null && (!IsSha256(manifest.Patcher.Sha256) || manifest.Patcher.Size <= 0))
			{
				throw new FormatException("zły wpis patchera na liście");
			}
			return manifest;
		}
	}

	public class ChannelInfo
	{
		[JsonProperty("manifest")]
		public string Manifest { get; set; }

		[JsonProperty("version")]
		public string Version { get; set; }

		[JsonProperty("published")]
		public string Published { get; set; }
	}

	public class ChannelsIndex
	{
		[JsonProperty("marker")]
		public string Marker { get; set; }

		[JsonProperty("schema")]
		public int Schema { get; set; }

		[JsonProperty("default")]
		public string Default { get; set; }

		[JsonProperty("channels")]
		public Dictionary<string, ChannelInfo> Channels { get; set; }
	}

	public class ManifestFile
	{
		// relative to the client folder, "/" separators
		[JsonProperty("path")]
		public string Path { get; set; }

		[JsonProperty("size")]
		public long Size { get; set; }

		// lower-case hex
		[JsonProperty("sha256")]
		public string Sha256 { get; set; }

		// true = the player's own copy wins (pack/dbdata.*: the database
		// editor's files from the player's server panel). Downloaded when
		// missing, or when the mirror publishes a new base of it (its hash
		// differs from the one this patcher last installed); never "repaired".
		[JsonProperty("keep")]
		public bool Keep { get; set; }
	}

	public class PatcherInfo
	{
		[JsonProperty("version")]
		public string Version { get; set; }

		[JsonProperty("size")]
		public long Size { get; set; }

		[JsonProperty("sha256")]
		public string Sha256 { get; set; }
	}

	public class Manifest
	{
		[JsonProperty("marker")]
		public string Marker { get; set; }

		[JsonProperty("schema")]
		public int Schema { get; set; }

		[JsonProperty("product")]
		public string Product { get; set; }

		[JsonProperty("channel")]
		public string Channel { get; set; }

		// the Yohara client version, e.g. "3.0.23" (written to YOHARA_VERSION)
		[JsonProperty("version")]
		public string Version { get; set; }

		// the exe's own client version (constinfo), e.g. "1.3.3"
		[JsonProperty("clientVersion")]
		public string ClientVersion { get; set; }

		[JsonProperty("published")]
		public string Published { get; set; }

		[JsonProperty("files")]
		public List<ManifestFile> Files { get; set; }

		[JsonProperty("delete")]
		public List<string> Delete { get; set; }

		[JsonProperty("patcher")]
		public PatcherInfo Patcher { get; set; }
	}
}
