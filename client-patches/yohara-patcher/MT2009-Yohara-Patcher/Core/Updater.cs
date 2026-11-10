using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

namespace MT2009Yohara.Core
{
	// MT2009_PLUS_YOHARA_PATCHER_V1 - the update logic of MT2009-Yohara-Patcher
	// without any UI (the same file runs in the window, in "--cli" mode and in
	// the Linux tests, MT2009-Yohara-Patcher.Tests).
	//
	// 1. The folder must be a Yohara client (YoharaClient.Detect) - a 2.x
	//    client or a folder without pack\ is refused.
	// 2. channels.json + <channel>/manifest.json from the Yohara mirror only.
	// 3. A different patcher on the list: downloaded and verified first (the
	//    caller swaps the exe and restarts - SwapSelf).
	// 4. Every file of the list is checked: size, then SHA-256 (a quick run
	//    trusts the hash remembered for the same size + time of change; "Napraw
	//    klienta" = FullVerify hashes everything).
	// 5. Changed / missing files: downloaded to .yohara-patcher\tmp\<sha256>.part
	//    (resumed with HTTP Range after a break, also in a later run), size +
	//    SHA-256 checked, then put in place with one File.Replace / File.Move
	//    (the old file stays whole until the new one is complete and right).
	// 6. .yohara-patcher\stan.json remembers the hashes and the installed
	//    version; YOHARA_VERSION gets the version.
	//
	// Nothing goes to the registry or AppData: everything lives in the client
	// folder (the 2.x patcher has no state of its own, its files are
	// MT2009-Patcher.*; ours are MT2009-Yohara-Patcher.* and .yohara-patcher\).
	public enum Phase
	{
		Connecting,
		SelfUpdate,
		Checking,
		Downloading,
		Done
	}

	public class UpdateProgress
	{
		public Phase Phase;
		public string Text;
		public int Done;
		public int Total;
		public long BytesDone;
		public long BytesTotal;
		public string File;
		public long FileDone;
		public long FileTotal;
	}

	public enum UpdateState
	{
		UpToDate,
		Updated,
		PatcherUpdated,
		Offline,
		Refused,
		Partial,
		Failed
	}

	public class UpdateResult
	{
		public UpdateState State;
		public string Message;
		public string Detail;
		public string Channel;
		public string Version;
		public string ClientVersion;
		public int Checked;
		public int Downloaded;
		public long Bytes;
		public int Deleted;
		public List<string> Failed = new List<string>();
		public bool GameRunning;
		public string NewPatcherPath;
		public string NewPatcherVersion;
	}

	public class UpdateOptions
	{
		public string Root;
		public string MirrorUrl;
		// null / "" = the mirror's default channel
		public string Channel;
		// "Napraw klienta": hash every file, trust no remembered hash
		public bool FullVerify;
		// the running patcher (self-update), null = no self-update
		public string SelfPath;
		public int Attempts = 3;
	}

	public class CachedHash
	{
		[JsonProperty("size")]
		public long Size { get; set; }

		[JsonProperty("mtime")]
		public long Mtime { get; set; }

		[JsonProperty("sha256")]
		public string Sha256 { get; set; }
	}

	public class LocalState
	{
		[JsonProperty("marker")]
		public string Marker { get; set; } = "MT2009_PLUS_YOHARA_PATCHER_STATE_V1";

		[JsonProperty("channel")]
		public string Channel { get; set; }

		[JsonProperty("version")]
		public string Version { get; set; }

		[JsonProperty("updated")]
		public string Updated { get; set; }

		[JsonProperty("files")]
		public Dictionary<string, CachedHash> Files { get; set; } = new Dictionary<string, CachedHash>(StringComparer.OrdinalIgnoreCase);

		// keep files: the hash of the base this patcher last saw / installed
		[JsonProperty("keep")]
		public Dictionary<string, string> Keep { get; set; } = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
	}

	public class Updater
	{
		public const string WorkFolder = ".yohara-patcher";

		public const string StateFileName = "stan.json";

		private readonly IHttp http;

		private readonly Action<string> log;

		private Action<UpdateProgress> onProgress;

		private readonly Stopwatch throttle = Stopwatch.StartNew();

		private long lastReport = -1000;

		public Updater(IHttp http, Action<string> log)
		{
			this.http = http;
			this.log = log ?? (s => { });
		}

		private void Log(string text)
		{
			this.log(text);
		}

		private void Report(UpdateProgress p, bool force)
		{
			if (this.onProgress == null)
			{
				return;
			}
			long now = this.throttle.ElapsedMilliseconds;
			if (!force && now - this.lastReport < 100)
			{
				return;
			}
			this.lastReport = now;
			try
			{
				this.onProgress(p);
			}
			catch
			{
			}
		}

		public static string WorkPath(string root, params string[] parts)
		{
			string path = Path.Combine(root, WorkFolder);
			foreach (string part in parts)
			{
				path = Path.Combine(path, part);
			}
			return path;
		}

		// ------------------------------------------------------------ hashes

		public static string Sha256File(string path)
		{
			using (FileStream stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read | FileShare.Delete, 1 << 20))
			using (SHA256 sha = SHA256.Create())
			{
				byte[] hash = sha.ComputeHash(stream);
				StringBuilder text = new StringBuilder(64);
				foreach (byte b in hash)
				{
					text.Append(b.ToString("x2"));
				}
				return text.ToString();
			}
		}

		// ------------------------------------------------------------ state

		public static LocalState LoadState(string root)
		{
			try
			{
				string path = WorkPath(root, StateFileName);
				if (File.Exists(path))
				{
					LocalState state = JsonConvert.DeserializeObject<LocalState>(File.ReadAllText(path, Encoding.UTF8));
					if (state != null && state.Files != null && state.Keep != null)
					{
						state.Files = new Dictionary<string, CachedHash>(state.Files, StringComparer.OrdinalIgnoreCase);
						state.Keep = new Dictionary<string, string>(state.Keep, StringComparer.OrdinalIgnoreCase);
						return state;
					}
				}
			}
			catch
			{
			}
			return new LocalState();
		}

		public static void SaveState(string root, LocalState state)
		{
			string dir = WorkPath(root);
			Directory.CreateDirectory(dir);
			string path = Path.Combine(dir, StateFileName);
			string tmp = path + ".tmp";
			File.WriteAllText(tmp, JsonConvert.SerializeObject(state, Formatting.Indented), new UTF8Encoding(false));
			ReplaceFile(tmp, path);
		}

		// ------------------------------------------------------------ files

		// Puts "source" in place of "target" in one step (same folder tree, so
		// the same volume): the old target stays whole until then.
		public static void ReplaceFile(string source, string target)
		{
			string dir = Path.GetDirectoryName(target);
			if (!string.IsNullOrEmpty(dir))
			{
				Directory.CreateDirectory(dir);
			}
			if (File.Exists(target))
			{
				FileAttributes attributes = File.GetAttributes(target);
				if ((attributes & FileAttributes.ReadOnly) != 0)
				{
					File.SetAttributes(target, attributes & ~FileAttributes.ReadOnly);
				}
				File.Replace(source, target, null, true);
			}
			else
			{
				File.Move(source, target);
			}
		}

		// After a self-update download: the running exe is renamed to
		// <exe>.old (a running exe can be renamed, not overwritten) and the new
		// one takes its name. On failure the old exe goes back.
		public static void SwapSelf(string selfPath, string newPath)
		{
			string old = selfPath + ".old";
			if (File.Exists(old))
			{
				File.Delete(old);
			}
			File.Move(selfPath, old);
			try
			{
				File.Move(newPath, selfPath);
			}
			catch
			{
				File.Move(old, selfPath);
				throw;
			}
		}

		public static void CleanupOldSelf(string selfPath)
		{
			try
			{
				string old = selfPath + ".old";
				if (File.Exists(old))
				{
					File.Delete(old);
				}
			}
			catch
			{
			}
		}

		private static bool IsSharingViolation(Exception e)
		{
			if (e is UnauthorizedAccessException)
			{
				return true;
			}
			IOException io = e as IOException;
			if (io == null || e is FileNotFoundException || e is DirectoryNotFoundException)
			{
				return false;
			}
			int code = io.HResult & 0xFFFF;
			// ERROR_SHARING_VIOLATION, ERROR_LOCK_VIOLATION, ERROR_UNABLE_TO_REMOVE_REPLACED, ERROR_UNABLE_TO_MOVE_REPLACEMENT(_2)
			return code == 32 || code == 33 || code == 1175 || code == 1176 || code == 1177;
		}

		// Downloads one store file to .yohara-patcher\tmp\<sha256>.part and
		// checks it; a part left by a break (this run or an earlier one) is
		// continued. Returns the checked part.
		private string DownloadVerified(UpdateOptions options, string sha256, long size, string label, UpdateProgress progress)
		{
			string tmp = WorkPath(options.Root, "tmp");
			Directory.CreateDirectory(tmp);
			string part = Path.Combine(tmp, sha256.ToLowerInvariant() + ".part");
			string url = Mirror.FileUrl(options.MirrorUrl, sha256);
			Exception last = null;
			long baseDone = progress.BytesDone;
			for (int attempt = 1; attempt <= Math.Max(1, options.Attempts); attempt++)
			{
				try
				{
					long have = File.Exists(part) ? new FileInfo(part).Length : 0;
					if (have > size)
					{
						File.Delete(part);
						have = 0;
					}
					if (have > 0)
					{
						this.Log(string.Format("  wznawiam {0} od {1} / {2} B", label, have, size));
					}
					if (have < size || size == 0 && !File.Exists(part))
					{
						long written = 0;
						long used = this.http.Download(url, part, have, n => {
							written += n;
							progress.FileDone = Math.Min(size, have + written);
							progress.BytesDone = baseDone + progress.FileDone;
							this.Report(progress, false);
						}, CancellationToken.None);
						if (used == 0 && have > 0)
						{
							this.Log("  serwer nie wznawia pobierania (bez Range) - plik od początku");
						}
					}
					long got = File.Exists(part) ? new FileInfo(part).Length : -1;
					if (got == size && Sha256File(part) == sha256.ToLowerInvariant())
					{
						progress.FileDone = size;
						progress.BytesDone = baseDone + size;
						this.Report(progress, true);
						return part;
					}
					this.Log(string.Format("  {0}: zła suma lub rozmiar po pobraniu ({1} B) - próba {2}", label, got, attempt));
					last = new IOException("plik po pobraniu jest uszkodzony (suma SHA-256 się nie zgadza)");
					try
					{
						File.Delete(part);
					}
					catch
					{
					}
				}
				catch (HttpError e) when (e.Status == 404)
				{
					throw new IOException("brak pliku na serwerze aktualizacji (" + e.Message + ")");
				}
				catch (Exception e) when (!(e is OutOfMemoryException))
				{
					last = e;
					this.Log(string.Format("  {0}: błąd pobierania ({1}) - próba {2}", label, e.Message, attempt));
				}
				progress.BytesDone = baseDone;
				if (attempt < options.Attempts)
				{
					Thread.Sleep(attempt * 1000);
				}
			}
			throw last ?? new IOException("nie udało się pobrać " + label);
		}

		// ------------------------------------------------------------ run

		public UpdateResult Run(UpdateOptions options, Action<UpdateProgress> onProgress)
		{
			this.onProgress = onProgress;
			UpdateResult result = new UpdateResult();
			string root = options.Root;
			this.Log(string.Format("folder: {0}  serwer: {1}  kanał: {2}  pełne sprawdzenie: {3}",
				root, options.MirrorUrl, string.IsNullOrEmpty(options.Channel) ? "(domyślny)" : options.Channel, options.FullVerify ? "tak" : "nie"));

			ClientKind kind = YoharaClient.Detect(root);
			if (kind != ClientKind.Yohara)
			{
				result.State = UpdateState.Refused;
				result.Message = kind == ClientKind.Classic2x
					? "To jest folder klienta 2.x, nie Yohary - patcher Yohary nic tu nie zmieni."
					: "W tym folderze nie ma klienta Yohara (brak folderu pack).";
				result.Detail = kind == ClientKind.Classic2x
					? "Ten folder ma klienta MT2009 PLUS 2.x. Do niego służy MT2009-Patcher.exe.\r\nMT2009-Yohara-Patcher.exe skopiuj do folderu klienta Yohara (obok metin2client.exe) i uruchom go stamtąd."
					: "Skopiuj MT2009-Yohara-Patcher.exe do folderu klienta Yohara (obok metin2client.exe i folderu pack) i uruchom go stamtąd.";
				this.Log("odmowa: " + kind);
				return result;
			}

			UpdateProgress progress = new UpdateProgress { Phase = Phase.Connecting, Text = "Łączenie z serwerem aktualizacji Yohary…" };
			this.Report(progress, true);
			ChannelsIndex channels;
			Manifest manifest;
			string channel;
			try
			{
				options.MirrorUrl = Mirror.Normalize(options.MirrorUrl);
				channels = Mirror.ParseChannels(this.http.GetString(Mirror.ChannelsUrl(options.MirrorUrl)));
				channel = string.IsNullOrEmpty(options.Channel) ? channels.Default : options.Channel;
				ChannelInfo info;
				if (channel == null || !channels.Channels.TryGetValue(channel, out info))
				{
					result.State = UpdateState.Failed;
					result.Message = string.Format("Serwer aktualizacji nie ma kanału \"{0}\".", channel);
					result.Detail = "Dostępne kanały: " + string.Join(", ", channels.Channels.Keys);
					this.Log(result.Message);
					return result;
				}
				result.Channel = channel;
				manifest = Mirror.ParseManifest(this.http.GetString(options.MirrorUrl + info.Manifest), channel);
			}
			catch (FormatException e)
			{
				result.State = UpdateState.Failed;
				result.Message = "Serwer aktualizacji Yohary zwrócił złą listę plików - możesz grać.";
				result.Detail = e.Message;
				this.Log("zła lista: " + e.Message);
				return result;
			}
			catch (Exception e) when (e is WebException || e is HttpError || e is IOException || e is JsonException || e is UriFormatException || e is ArgumentException)
			{
				result.State = UpdateState.Offline;
				result.Message = "Serwer aktualizacji Yohary niedostępny - możesz grać.";
				result.Detail = e.Message;
				this.Log("serwer niedostępny: " + e.Message);
				return result;
			}
			result.Version = manifest.Version;
			result.ClientVersion = manifest.ClientVersion;
			this.Log(string.Format("lista: kanał {0}, wersja {1}, plików {2}, opublikowano {3}", manifest.Channel, manifest.Version, manifest.Files.Count, manifest.Published));

			// self-update first: a newer list may need a newer patcher
			if (!string.IsNullOrEmpty(options.SelfPath) && manifest.Patcher != null && File.Exists(options.SelfPath))
			{
				string own = Sha256File(options.SelfPath);
				if (own != manifest.Patcher.Sha256.ToLowerInvariant())
				{
					this.Log(string.Format("nowy patcher {0} ({1})", manifest.Patcher.Version, manifest.Patcher.Sha256));
					progress = new UpdateProgress { Phase = Phase.SelfUpdate, Text = "Pobieranie nowej wersji patchera…", Total = 1, BytesTotal = manifest.Patcher.Size, File = "MT2009-Yohara-Patcher.exe", FileTotal = manifest.Patcher.Size };
					try
					{
						result.NewPatcherPath = this.DownloadVerified(options, manifest.Patcher.Sha256, manifest.Patcher.Size, "patcher", progress);
						result.NewPatcherVersion = manifest.Patcher.Version;
						result.State = UpdateState.PatcherUpdated;
						result.Message = "Patcher Yohary został zaktualizowany i uruchomi się ponownie.";
						return result;
					}
					catch (Exception e)
					{
						// not fatal: the files can still be updated by this one
						this.Log("nowego patchera nie udało się pobrać: " + e.Message);
					}
				}
			}
			if (manifest.Schema > Mirror.Schema)
			{
				result.State = UpdateState.Failed;
				result.Message = "Ta lista plików wymaga nowszego patchera Yohary - pobierz go ponownie.";
				result.Detail = string.Format("schemat listy {0}, patcher zna {1}", manifest.Schema, Mirror.Schema);
				return result;
			}

			LocalState state = LoadState(root);
			if (state.Channel != null && state.Channel != channel)
			{
				this.Log(string.Format("zmiana kanału {0} -> {1}", state.Channel, channel));
			}

			// files to delete
			if (manifest.Delete != null)
			{
				foreach (string path in manifest.Delete)
				{
					string local = YoharaClient.Local(root, path);
					try
					{
						if (File.Exists(local))
						{
							File.SetAttributes(local, FileAttributes.Normal);
							File.Delete(local);
							state.Files.Remove(path);
							result.Deleted++;
							this.Log("usunięty: " + path);
						}
					}
					catch (Exception e)
					{
						result.Failed.Add(path);
						result.GameRunning |= IsSharingViolation(e);
						this.Log(string.Format("nie usunięto {0}: {1}", path, e.Message));
					}
				}
			}

			// check
			List<ManifestFile> need = new List<ManifestFile>();
			long needBytes = 0;
			progress = new UpdateProgress { Phase = Phase.Checking, Text = options.FullVerify ? "Naprawa klienta - sprawdzanie wszystkich plików" : "Sprawdzanie plików klienta", Total = manifest.Files.Count };
			foreach (ManifestFile file in manifest.Files)
			{
				progress.File = file.Path;
				this.Report(progress, false);
				try
				{
					if (this.NeedsDownload(root, file, state, options.FullVerify))
					{
						need.Add(file);
						needBytes += file.Size;
					}
				}
				catch (Exception e)
				{
					// unreadable (locked by the game?) - try to replace it anyway
					this.Log(string.Format("nie da się sprawdzić {0}: {1}", file.Path, e.Message));
					need.Add(file);
					needBytes += file.Size;
				}
				progress.Done++;
				result.Checked++;
			}
			this.Report(progress, true);
			this.Log(string.Format("do pobrania: {0} plików, {1:0.0} MB", need.Count, needBytes / 1048576.0));

			if (need.Count > 0)
			{
				long free = FreeSpace(root);
				long partBytes = 0;
				foreach (ManifestFile file in need)
				{
					string part = WorkPath(root, "tmp", file.Sha256 + ".part");
					if (File.Exists(part))
					{
						partBytes += new FileInfo(part).Length;
					}
				}
				if (free >= 0 && free < needBytes - partBytes + 64L * 1048576)
				{
					result.State = UpdateState.Failed;
					result.Message = string.Format("Za mało miejsca na dysku: potrzeba {0:0} MB, wolne {1:0} MB.", (needBytes - partBytes) / 1048576.0 + 64, free / 1048576.0);
					this.Log(result.Message);
					SaveState(root, state);
					return result;
				}
			}

			// download
			progress = new UpdateProgress { Phase = Phase.Downloading, Text = "Pobieranie", Total = need.Count, BytesTotal = needBytes };
			foreach (ManifestFile file in need)
			{
				progress.File = file.Path;
				progress.FileDone = 0;
				progress.FileTotal = file.Size;
				this.Report(progress, true);
				long before = progress.BytesDone;
				string local = YoharaClient.Local(root, file.Path);
				try
				{
					string part = this.DownloadVerified(options, file.Sha256, file.Size, file.Path, progress);
					ReplaceFile(part, local);
					FileInfo info = new FileInfo(local);
					state.Files[file.Path] = new CachedHash { Size = info.Length, Mtime = info.LastWriteTimeUtc.Ticks, Sha256 = file.Sha256.ToLowerInvariant() };
					if (file.Keep)
					{
						state.Keep[file.Path] = file.Sha256.ToLowerInvariant();
					}
					result.Downloaded++;
					result.Bytes += file.Size;
					this.Log(string.Format("pobrany: {0} ({1} B)", file.Path, file.Size));
				}
				catch (Exception e)
				{
					result.Failed.Add(file.Path);
					result.GameRunning |= IsSharingViolation(e);
					progress.BytesDone = before + file.Size;
					this.Log(string.Format("NIE pobrano {0}: {1}", file.Path, e.Message));
				}
				progress.Done++;
			}
			progress.Phase = Phase.Done;
			this.Report(progress, true);

			if (result.Failed.Count == 0)
			{
				// YOHARA_VERSION (the mirror lists it too; this keeps it right
				// even for a list without it)
				try
				{
					bool listed = manifest.Files.Exists(f => string.Equals(f.Path, YoharaClient.StampFile, StringComparison.OrdinalIgnoreCase));
					if (!listed && YoharaClient.ReadStamp(root) != manifest.Version)
					{
						File.WriteAllText(YoharaClient.Local(root, YoharaClient.StampFile), manifest.Version + "\r\n", new UTF8Encoding(false));
					}
				}
				catch (Exception e)
				{
					this.Log("YOHARA_VERSION: " + e.Message);
				}
				state.Channel = channel;
				state.Version = manifest.Version;
				state.Updated = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");
				CleanTmp(root);
			}
			try
			{
				SaveState(root, state);
			}
			catch (Exception e)
			{
				this.Log("stan.json: " + e.Message);
			}

			if (result.Failed.Count > 0)
			{
				result.State = UpdateState.Partial;
				result.Message = result.GameRunning
					? string.Format("Nie podmieniono plików: {0} - zamknij grę i uruchom patcher ponownie.", result.Failed.Count)
					: string.Format("Nie pobrano plików: {0} - uruchom patcher ponownie (pobieranie zostanie wznowione).", result.Failed.Count);
				result.Detail = string.Join("\r\n", result.Failed);
			}
			else if (result.Downloaded > 0 || result.Deleted > 0)
			{
				result.State = UpdateState.Updated;
				result.Message = string.Format("Klient Yohara {0} zaktualizowany ({1} plików). Możesz grać.", manifest.Version, result.Downloaded);
			}
			else
			{
				result.State = UpdateState.UpToDate;
				result.Message = options.FullVerify
					? string.Format("Klient sprawdzony: wszystkie pliki są poprawne ({0}).", result.Checked)
					: "Gra jest aktualna! Możesz grać.";
			}
			this.Log(string.Format("wynik: {0} - {1}", result.State, result.Message));
			return result;
		}

		private bool NeedsDownload(string root, ManifestFile file, LocalState state, bool full)
		{
			string local = YoharaClient.Local(root, file.Path);
			if (!File.Exists(local))
			{
				return true;
			}
			string sha = file.Sha256.ToLowerInvariant();
			if (file.Keep)
			{
				// the player's own copy (from the server panel) wins; only a new
				// base on the mirror is downloaded again
				string seen;
				if (!state.Keep.TryGetValue(file.Path, out seen))
				{
					state.Keep[file.Path] = sha;
					return false;
				}
				return seen != sha;
			}
			FileInfo info = new FileInfo(local);
			if (info.Length != file.Size)
			{
				return true;
			}
			CachedHash cached;
			long mtime = info.LastWriteTimeUtc.Ticks;
			if (!full && state.Files.TryGetValue(file.Path, out cached) && cached.Size == info.Length && cached.Mtime == mtime && cached.Sha256 != null)
			{
				return cached.Sha256 != sha;
			}
			string actual = Sha256File(local);
			state.Files[file.Path] = new CachedHash { Size = info.Length, Mtime = mtime, Sha256 = actual };
			return actual != sha;
		}

		private static long FreeSpace(string root)
		{
			try
			{
				string drive = Path.GetPathRoot(Path.GetFullPath(root));
				return new DriveInfo(drive).AvailableFreeSpace;
			}
			catch
			{
				return -1;
			}
		}

		// parts of an older list (never needed again) once a run ended well
		private static void CleanTmp(string root)
		{
			try
			{
				string tmp = WorkPath(root, "tmp");
				if (Directory.Exists(tmp))
				{
					foreach (string file in Directory.GetFiles(tmp, "*.part"))
					{
						try
						{
							File.Delete(file);
						}
						catch
						{
						}
					}
				}
			}
			catch
			{
			}
		}
	}
}
