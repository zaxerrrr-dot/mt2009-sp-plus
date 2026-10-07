using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace N2_Patcher.Core
{
	// MT2009_PLUS_DBDATA_AUTO_V1: the database editor's client files
	// (pack\dbdata.index + pack\dbdata.data + dbdata_stamp.txt) straight from
	// the panel of the server chosen in the patcher, instead of the zip the
	// player had to unpack himself.
	//
	// The Seban panel publishes (dbeditor/autodbdata.py, no login):
	//   GET <panel>/klient/dbdata/manifest.json
	//     {"format": "MT2009_PLUS_DBDATA_AUTO_V1", "client_version_base": "2.0.57",
	//      "stamp": "2.0.57[-<12 hex>]", "edited": bool,
	//      "files": [{"name": "pack/dbdata.index", "size": n, "sha256": "<HEX>", "url": "<relative>"},
	//                {"name": "pack/dbdata.data", ...}],
	//      "base": {"index_sha256": .., "data_sha256": ..}, "stamp_file": "<dbdata_stamp.txt>"}
	//   GET <the url of a file, relative to the manifest>
	//
	// Run(): manifest (every candidate address at once, the first in order
	// that answers wins) -> client version check -> SHA-256 of the local pack
	// -> download only what differs into *.tmp, size + SHA-256 checked ->
	// the files swapped (File.Replace, the old one kept as *.bak; the first
	// put back when the second fails) -> dbdata_stamp.txt. Nothing here ever
	// throws: every failure is a result the window shows, and the game
	// starts anyway.
	public enum DbDataState
	{
		Disabled,
		Unreachable,
		UpToDate,
		Updated,
		ClientOlder,
		ServerOlder,
		GameRunning,
		Failed
	}

	public class DbDataFile
	{
		[JsonProperty("name")] public string Name;
		[JsonProperty("size")] public long Size;
		[JsonProperty("sha256")] public string Sha256;
		[JsonProperty("url")] public string Url;
	}

	public class DbDataBase
	{
		[JsonProperty("index_sha256")] public string IndexSha256;
		[JsonProperty("data_sha256")] public string DataSha256;
	}

	public class DbDataManifest
	{
		[JsonProperty("format")] public string Format;
		[JsonProperty("client_version_base")] public string ClientVersionBase;
		[JsonProperty("stamp")] public string Stamp;
		[JsonProperty("edited")] public bool Edited;
		[JsonProperty("files")] public List<DbDataFile> Files;
		[JsonProperty("base")] public DbDataBase Base;
		[JsonProperty("stamp_file")] public string StampFile;
	}

	public class DbDataResult
	{
		public DbDataState State;
		// one short line for the window (Polish)
		public string Message = "";
		// the whole story (tooltip, log)
		public string Detail = "";
		public string ManifestUrl = "";
		public string Stamp = "";
		public List<string> Log = new List<string>();

		public bool IsWarning
		{
			get { return this.State == DbDataState.ClientOlder || this.State == DbDataState.ServerOlder || this.State == DbDataState.GameRunning || this.State == DbDataState.Failed; }
		}
	}

	public static class DbDataSync
	{
		public const string Format = "MT2009_PLUS_DBDATA_AUTO_V1";
		public const string ManifestPath = "klient/dbdata/manifest.json";
		public const int PanelPort = 7790;
		// the panel's port in a NAT block like the test servers' (login B+1000, panel B+7790)
		public const int PanelOffsetFromLogin = 6790;
		public const long MaxManifestBytes = 64 * 1024;
		public const long MaxPackBytes = 64L * 1024 * 1024;
		public const string StampFileName = "dbdata_stamp.txt";
		public static readonly string[] PackNames = { "dbdata.index", "dbdata.data" };
		private static readonly Regex StampRe = new Regex("^[0-9A-Za-z._-]{1,64}$");
		private static readonly Regex VersionRe = new Regex("^[0-9]+(\\.[0-9]+){1,3}$");
		private static readonly Regex ShaRe = new Regex("^[0-9A-F]{64}$");

		// fetch(url, timeout ms, max bytes) -> body; throws on any failure.
		public delegate byte[] Fetcher(string url, int timeoutMs, long maxBytes);

		// ------------------------------------------------ where to ask

		// setting = "DbDataManifest" of MT2009-Patcher.exe.config: empty = the
		// addresses worked out from the server, "off" = never, otherwise
		// manifest URLs separated by ';' ("{host}" = the server's address).
		// null = switched off.
		public static List<string> CandidateUrls(CoopServer server, string setting)
		{
			List<string> list = new List<string>();
			string value = (setting ?? "").Trim();
			string lower = value.ToLowerInvariant();
			if (lower == "off" || lower == "0" || lower == "false" || lower == "nie" || lower == "wylacz" || lower == "wyłącz")
			{
				return null;
			}
			string host = server == null ? "127.0.0.1" : server.Host;
			if (string.IsNullOrEmpty(host) || !CoopServer.IsValidHost(host))
			{
				host = "127.0.0.1";
			}
			if (value.Length > 0)
			{
				foreach (string part in value.Split(';'))
				{
					string url = ManifestUrlOf(part.Trim().Replace("{host}", host));
					if (url != null)
					{
						Add(list, url);
					}
				}
				return list;
			}
			string panel = server == null ? "" : (server.Panel ?? "").Trim();
			if (panel.Length > 0)
			{
				int port;
				if (int.TryParse(panel, NumberStyles.None, CultureInfo.InvariantCulture, out port) && port > 0 && port < 65536)
				{
					Add(list, string.Format(CultureInfo.InvariantCulture, "http://{0}:{1}/{2}", host, port, ManifestPath));
				}
				else
				{
					string url = ManifestUrlOf(panel.Replace("{host}", host));
					if (url != null)
					{
						Add(list, url);
					}
				}
			}
			Add(list, string.Format(CultureInfo.InvariantCulture, "http://{0}:{1}/{2}", host, PanelPort, ManifestPath));
			int auth = server == null ? CoopServer.DefaultAuth : server.Auth;
			int blockPort = auth + PanelOffsetFromLogin;
			if (blockPort > 0 && blockPort < 65536)
			{
				Add(list, string.Format(CultureInfo.InvariantCulture, "http://{0}:{1}/{2}", host, blockPort, ManifestPath));
			}
			// a gate on the web port that forwards only /klient/dbdata/ (README)
			Add(list, string.Format(CultureInfo.InvariantCulture, "http://{0}/{1}", host, ManifestPath));
			return list;
		}

		private static void Add(List<string> list, string url)
		{
			if (!list.Contains(url))
			{
				list.Add(url);
			}
		}

		// "http://h:7790", "http://h:7790/", "http://h/x/klient/dbdata/manifest.json" -> the manifest URL
		public static string ManifestUrlOf(string text)
		{
			Uri uri;
			if (string.IsNullOrEmpty(text) || !Uri.TryCreate(text, UriKind.Absolute, out uri) || (uri.Scheme != "http" && uri.Scheme != "https"))
			{
				return null;
			}
			string url = uri.GetLeftPart(UriPartial.Path);
			if (url.EndsWith(".json", StringComparison.OrdinalIgnoreCase))
			{
				return url;
			}
			return url.TrimEnd('/') + "/" + ManifestPath;
		}

		// ------------------------------------------------ local files

		public static string Sha256File(string path)
		{
			if (!File.Exists(path))
			{
				return null;
			}
			using (FileStream stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
			using (SHA256 sha = SHA256.Create())
			{
				return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", string.Empty);
			}
		}

		public static string Sha256Bytes(byte[] data)
		{
			using (SHA256 sha = SHA256.Create())
			{
				return BitConverter.ToString(sha.ComputeHash(data)).Replace("-", string.Empty);
			}
		}

		// The client's CLIENT_VERSION (the release zips and the patcher write it), or null.
		public static string ReadClientVersion(string root)
		{
			try
			{
				string path = Path.Combine(root, "CLIENT_VERSION");
				if (!File.Exists(path))
				{
					return null;
				}
				string text = File.ReadAllText(path, Encoding.ASCII).Trim();
				string first = text.Split(new char[] { ' ', '\t', '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries).FirstOrDefault() ?? "";
				first = first.TrimStart('v', 'V');
				return VersionRe.IsMatch(first) ? first : null;
			}
			catch
			{
				return null;
			}
		}

		public static int CompareVersions(string a, string b)
		{
			int[] x = a.Split('.').Select(p => int.Parse(p, CultureInfo.InvariantCulture)).ToArray();
			int[] y = b.Split('.').Select(p => int.Parse(p, CultureInfo.InvariantCulture)).ToArray();
			for (int i = 0; i < Math.Max(x.Length, y.Length); i++)
			{
				int u = i < x.Length ? x[i] : 0;
				int v = i < y.Length ? y[i] : 0;
				if (u != v)
				{
					return u < v ? -1 : 1;
				}
			}
			return 0;
		}

		// ------------------------------------------------ the manifest

		// null when it is not a manifest this patcher can trust.
		public static DbDataManifest ParseManifest(byte[] body)
		{
			DbDataManifest m;
			try
			{
				m = JsonConvert.DeserializeObject<DbDataManifest>(Encoding.UTF8.GetString(body));
			}
			catch
			{
				return null;
			}
			if (m == null || m.Format != Format || m.Files == null || m.Files.Count != 2)
			{
				return null;
			}
			if (m.ClientVersionBase == null || !VersionRe.IsMatch(m.ClientVersionBase) || m.Stamp == null || !StampRe.IsMatch(m.Stamp))
			{
				return null;
			}
			if (m.Stamp != m.ClientVersionBase && !m.Stamp.StartsWith(m.ClientVersionBase + "-", StringComparison.Ordinal))
			{
				return null;
			}
			for (int i = 0; i < 2; i++)
			{
				DbDataFile f = m.Files[i];
				if (f == null || f.Name != "pack/" + PackNames[i] || f.Size <= 0 || f.Size > MaxPackBytes || string.IsNullOrEmpty(f.Url))
				{
					return null;
				}
				f.Sha256 = (f.Sha256 ?? "").ToUpperInvariant();
				if (!ShaRe.IsMatch(f.Sha256))
				{
					return null;
				}
			}
			string stampFile = m.StampFile ?? "";
			if (stampFile.Length > 2048 || stampFile.Any(c => c > 126 || (c < 32 && c != '\r' && c != '\n'))
				|| !Regex.IsMatch(stampFile, "(^|\\n)stamp " + Regex.Escape(m.Stamp) + "\\r?\\n"))
			{
				return null;
			}
			return m;
		}

		// ------------------------------------------------ the whole run

		public static DbDataResult Run(string root, List<string> candidates, Fetcher fetch, Action<string> status, int manifestTimeoutMs = 4000)
		{
			DbDataResult result = new DbDataResult();
			try
			{
				return RunInner(root, candidates, fetch, status, manifestTimeoutMs, result);
			}
			catch (Exception exc)
			{
				result.Log.Add("błąd: " + exc);
				return Done(result, DbDataState.Failed, "Dane bazy: błąd - gra działa na starych plikach.", "Nie udało się zaktualizować danych bazy: " + exc.Message);
			}
		}

		private static DbDataResult Done(DbDataResult result, DbDataState state, string message, string detail)
		{
			result.State = state;
			result.Message = message;
			result.Detail = detail;
			result.Log.Add(state + ": " + detail);
			return result;
		}

		private static DbDataResult RunInner(string root, List<string> candidates, Fetcher fetch, Action<string> status, int manifestTimeoutMs, DbDataResult result)
		{
			if (candidates == null)
			{
				return Done(result, DbDataState.Disabled, "", "Wyłączone w MT2009-Patcher.exe.config (DbDataManifest).");
			}
			status?.Invoke("Dane bazy: sprawdzam serwer…");
			// every address at once; the first in order that answers wins
			Task<byte[]>[] tasks = candidates.Select(url => Task.Run(() => fetch(url, manifestTimeoutMs, MaxManifestBytes))).ToArray();
			try
			{
				Task.WaitAll(tasks, manifestTimeoutMs + 1500);
			}
			catch (AggregateException)
			{
			}
			DbDataManifest manifest = null;
			for (int i = 0; i < tasks.Length; i++)
			{
				if (tasks[i].Status != TaskStatus.RanToCompletion)
				{
					result.Log.Add(candidates[i] + ": " + (tasks[i].Exception != null ? tasks[i].Exception.GetBaseException().Message : "brak odpowiedzi"));
					continue;
				}
				DbDataManifest m = ParseManifest(tasks[i].Result);
				if (m == null)
				{
					result.Log.Add(candidates[i] + ": to nie jest manifest MT2009_PLUS_DBDATA_AUTO_V1");
					continue;
				}
				manifest = m;
				result.ManifestUrl = candidates[i];
				break;
			}
			if (manifest == null)
			{
				return Done(result, DbDataState.Unreachable, "Dane bazy: panel serwera niedostępny.",
					"Nie znaleziono panelu serwera (" + string.Join(", ", candidates) + "). Gra uruchomi się z obecnymi plikami; zmiany z edytora bazy danych można też wgrać z zipa z panelu.");
			}
			result.Stamp = manifest.Stamp;
			result.Log.Add("manifest: " + result.ManifestUrl + " stamp " + manifest.Stamp);

			string pack = Path.Combine(root, "pack");
			string[] targets = PackNames.Select(n => Path.Combine(pack, n)).ToArray();
			string[] local = targets.Select(Sha256File).ToArray();
			bool same = local[0] == manifest.Files[0].Sha256 && local[1] == manifest.Files[1].Sha256;

			// client version: the server's pack is made for its client base
			string version = ReadClientVersion(root);
			string baseVersion = manifest.ClientVersionBase;
			if (!same)
			{
				if (version != null && CompareVersions(version, baseVersion) < 0)
				{
					return Done(result, DbDataState.ClientOlder, "Dane bazy: najpierw zaktualizuj klienta.",
						string.Format("Serwer ma pliki dla klienta {0}, a Twój klient to {1}. Zaktualizuj klienta (patcher z serwera aktualizacji), potem uruchom patcher ponownie.", baseVersion, version));
				}
				if (version == null || CompareVersions(version, baseVersion) > 0)
				{
					// a newer client takes them only while its pack still is that base's own
					bool baseOwn = manifest.Base != null && local[0] != null
						&& string.Equals(local[0], manifest.Base.IndexSha256, StringComparison.OrdinalIgnoreCase)
						&& string.Equals(local[1], manifest.Base.DataSha256, StringComparison.OrdinalIgnoreCase);
					bool fromBase = StampOfLocal(root, targets) is string ls && (ls == baseVersion || ls.StartsWith(baseVersion + "-", StringComparison.Ordinal));
					if (!baseOwn && !fromBase)
					{
						return Done(result, DbDataState.ServerOlder, "Dane bazy: serwer ma starszą wersję klienta.",
							string.Format("Panel serwera ma pliki dla klienta {0}, a Twój klient to {1} - nie mieszam ich. Właściciel serwera musi zaktualizować serwer; do tego czasu gra działa na Twoich plikach.", baseVersion, version ?? "(nieznana wersja)"));
					}
				}
			}

			string stampPath = Path.Combine(root, StampFileName);
			byte[] stampBytes = Encoding.ASCII.GetBytes(manifest.StampFile);
			if (same)
			{
				bool stampSame = File.Exists(stampPath) && File.ReadAllBytes(stampPath).SequenceEqual(stampBytes);
				if (!stampSame)
				{
					WriteAtomic(stampPath, stampBytes);
					result.Log.Add("zapisano " + StampFileName);
				}
				return Done(result, DbDataState.UpToDate, "Dane bazy: aktualne (" + ShortStamp(manifest.Stamp) + ").",
					"Twoja paczka pack\\dbdata jest taka jak na serwerze (" + manifest.Stamp + ").");
			}

			status?.Invoke("Pobieram dane bazy z serwera…");
			Uri manifestUri = new Uri(result.ManifestUrl);
			string[] temps = new string[2];
			try
			{
				for (int i = 0; i < 2; i++)
				{
					DbDataFile f = manifest.Files[i];
					if (local[i] == f.Sha256)
					{
						continue;
					}
					Uri url = new Uri(manifestUri, f.Url);
					if (url.Scheme != "http" && url.Scheme != "https")
					{
						throw new InvalidDataException("zły adres pliku " + f.Url);
					}
					byte[] body = fetch(url.ToString(), 60000, f.Size);
					if (body.LongLength != f.Size || Sha256Bytes(body) != f.Sha256)
					{
						throw new InvalidDataException(PackNames[i] + ": suma SHA-256 lub rozmiar się nie zgadza");
					}
					Directory.CreateDirectory(pack);
					temps[i] = targets[i] + ".tmp";
					File.WriteAllBytes(temps[i], body);
					result.Log.Add("pobrano " + url + " (" + body.LongLength + " B)");
				}
			}
			catch (Exception exc)
			{
				DeleteQuietly(temps);
				return Done(result, DbDataState.Failed, "Dane bazy: nie udało się pobrać.",
					"Nie udało się pobrać danych bazy z serwera: " + exc.Message + ". Gra uruchomi się z obecnymi plikami.");
			}

			// the game holds its packs open: then nothing is swapped
			for (int i = 0; i < 2; i++)
			{
				if (temps[i] != null && IsLocked(targets[i]))
				{
					DeleteQuietly(temps);
					return Done(result, DbDataState.GameRunning, "Dane bazy: zamknij grę, aby je podmienić.",
						"Gra jest uruchomiona (pack\\" + PackNames[i] + " jest w użyciu). Zamknij grę i uruchom patcher ponownie - pobierze dane bazy serwera.");
				}
			}

			List<int> swapped = new List<int>();
			try
			{
				// data first: an index is useless without its data
				foreach (int i in new int[] { 1, 0 })
				{
					if (temps[i] == null)
					{
						continue;
					}
					if (File.Exists(targets[i]))
					{
						File.Replace(temps[i], targets[i], targets[i] + ".bak", true);
					}
					else
					{
						File.Move(temps[i], targets[i]);
					}
					swapped.Add(i);
				}
			}
			catch (Exception exc)
			{
				foreach (int i in swapped)
				{
					try
					{
						if (File.Exists(targets[i] + ".bak"))
						{
							File.Copy(targets[i] + ".bak", targets[i], true);
						}
					}
					catch
					{
					}
				}
				DeleteQuietly(temps);
				bool locked = exc is IOException || exc is UnauthorizedAccessException;
				return Done(result, locked ? DbDataState.GameRunning : DbDataState.Failed,
					locked ? "Dane bazy: zamknij grę, aby je podmienić." : "Dane bazy: nie udało się podmienić.",
					"Nie udało się podmienić pack\\dbdata (" + exc.Message + "). Stare pliki zostały. Zamknij grę i uruchom patcher ponownie.");
			}
			WriteAtomic(stampPath, stampBytes);
			result.Log.Add("podmieniono pack\\dbdata (kopie: *.bak), zapisano " + StampFileName);
			string what = manifest.Edited ? "zmiany z edytora serwera" : "oryginalne pliki klienta " + baseVersion;
			return Done(result, DbDataState.Updated, "Dane bazy: pobrano (" + ShortStamp(manifest.Stamp) + ").",
				"Pobrano dane bazy z serwera: " + what + " (" + manifest.Stamp + "). Poprzednie pliki: pack\\dbdata.*.bak.");
		}

		// The stamp of dbdata_stamp.txt while the pack still has its sizes
		// (as root/dbdatastamp.py ReadLocalStamp), else null.
		public static string StampOfLocal(string root, string[] targets)
		{
			try
			{
				string path = Path.Combine(root, StampFileName);
				if (!File.Exists(path))
				{
					return null;
				}
				string stamp = null;
				foreach (string raw in File.ReadAllLines(path, Encoding.ASCII))
				{
					string[] parts = raw.Split(new char[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
					if (parts.Length >= 2 && parts[0] == "stamp")
					{
						stamp = parts[1];
					}
					else if (parts.Length >= 3 && parts[0] == "size")
					{
						string name = parts[1].Replace('/', Path.DirectorySeparatorChar).Replace('\\', Path.DirectorySeparatorChar);
						string file = Path.Combine(root, name);
						if (!PatchCore.IsSafeName(parts[1].Replace('/', '\\')) || !File.Exists(file) || new FileInfo(file).Length.ToString(CultureInfo.InvariantCulture) != parts[2])
						{
							return null;
						}
					}
				}
				return stamp != null && StampRe.IsMatch(stamp) ? stamp : null;
			}
			catch
			{
				return null;
			}
		}

		public static string ShortStamp(string stamp)
		{
			return stamp ?? "";
		}

		public static bool IsLocked(string path)
		{
			if (!File.Exists(path))
			{
				return false;
			}
			try
			{
				using (new FileStream(path, FileMode.Open, FileAccess.ReadWrite, FileShare.None))
				{
				}
				return false;
			}
			catch (IOException)
			{
				return true;
			}
			catch (UnauthorizedAccessException)
			{
				return true;
			}
		}

		public static void WriteAtomic(string path, byte[] data)
		{
			string tmp = path + ".tmp";
			File.WriteAllBytes(tmp, data);
			if (File.Exists(path))
			{
				File.Replace(tmp, path, null, true);
			}
			else
			{
				File.Move(tmp, path);
			}
		}

		private static void DeleteQuietly(string[] paths)
		{
			foreach (string p in paths)
			{
				try
				{
					if (p != null && File.Exists(p))
					{
						File.Delete(p);
					}
				}
				catch
				{
				}
			}
		}

		// ------------------------------------------------ HTTP

		// The patcher's own fetch: no proxy, no redirects, a size cap.
		public static byte[] HttpFetch(string url, int timeoutMs, long maxBytes)
		{
			HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
			request.Proxy = null;
			request.Timeout = timeoutMs;
			request.ReadWriteTimeout = Math.Max(timeoutMs, 15000);
			request.AllowAutoRedirect = false;
			request.UserAgent = "MT2009-Patcher (" + Format + ")";
			using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
			{
				if (response.StatusCode != HttpStatusCode.OK)
				{
					throw new WebException("HTTP " + (int)response.StatusCode);
				}
				if (response.ContentLength > maxBytes)
				{
					throw new InvalidDataException("za duża odpowiedź");
				}
				using (Stream stream = response.GetResponseStream())
				using (MemoryStream buffer = new MemoryStream())
				{
					byte[] chunk = new byte[65536];
					int read;
					while ((read = stream.Read(chunk, 0, chunk.Length)) > 0)
					{
						buffer.Write(chunk, 0, read);
						if (buffer.Length > maxBytes)
						{
							throw new InvalidDataException("za duża odpowiedź");
						}
					}
					return buffer.ToArray();
				}
			}
		}
	}
}
