using MT2009Yohara.Core;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

// Linux tests of MT2009-Yohara-Patcher (Core/*.cs compiled as they are).
//   dotnet run -- unit                                   offline checks (fake mirror in a temp folder)
//   dotnet run -- update <mirror url> <client dir> [--napraw] [--kanal X]
//                                                        a real run against the mirror (as the patcher does it)
internal static class Program
{
	private static int failures;

	private static void Check(bool ok, string what)
	{
		Console.WriteLine((ok ? "  OK   " : "  FAIL ") + what);
		if (!ok)
		{
			failures++;
		}
	}

	private static int Main(string[] args)
	{
		string mode = args.Length > 0 ? args[0] : "unit";
		switch (mode)
		{
			case "unit": Unit(); break;
			case "update": return Update(args);
			default: Console.WriteLine("?"); return 2;
		}
		Console.WriteLine(failures == 0 ? "WYNIK: wszystko OK" : "WYNIK: błędów: " + failures);
		return failures == 0 ? 0 : 1;
	}

	private static int Update(string[] args)
	{
		UpdateOptions options = new UpdateOptions { MirrorUrl = args[1], Root = Path.GetFullPath(args[2]) };
		for (int i = 3; i < args.Length; i++)
		{
			if (args[i] == "--napraw") options.FullVerify = true;
			if (args[i] == "--kanal") options.Channel = args[++i];
		}
		Stopwatch watch = Stopwatch.StartNew();
		Phase last = Phase.Connecting;
		UpdateResult result = new Updater(new WebHttp(), s => Console.WriteLine("  log: " + s)).Run(options, p => {
			if (p.Phase != last)
			{
				last = p.Phase;
				Console.WriteLine(string.Format("  [{0}] {1} {2}/{3}", p.Phase, p.Text, p.Done, p.Total));
			}
		});
		Console.WriteLine(string.Format("STAN: {0}  wersja {1}  kanał {2}  sprawdzono {3}  pobrano {4} ({5:0.0} MB)  usunięto {6}  błędy {7}  czas {8:0.0} s",
			result.State, result.Version, result.Channel, result.Checked, result.Downloaded, result.Bytes / 1048576.0, result.Deleted, result.Failed.Count, watch.Elapsed.TotalSeconds));
		Console.WriteLine("KOMUNIKAT: " + result.Message);
		return result.State == UpdateState.UpToDate || result.State == UpdateState.Updated ? 0 : 1;
	}

	// ------------------------------------------------------------------ fake mirror

	// Serves a local folder as the mirror; can break a download after N bytes
	// (resume test) and ignore Range (a server without it).
	private class FakeHttp : IHttp
	{
		public string Prefix;
		public string Folder;
		public long BreakAfter = -1;
		public bool IgnoreRange;
		public List<long> Offsets = new List<long>();
		public List<string> Urls = new List<string>();

		private string Map(string url)
		{
			Urls.Add(url);
			if (!url.StartsWith(Prefix))
			{
				throw new HttpError(404, "obcy adres: " + url);
			}
			string path = Path.Combine(Folder, url.Substring(Prefix.Length).Replace('/', Path.DirectorySeparatorChar));
			if (!File.Exists(path))
			{
				throw new HttpError(404, "HTTP 404 - " + url);
			}
			return path;
		}

		public string GetString(string url)
		{
			return File.ReadAllText(Map(url), Encoding.UTF8);
		}

		public long Download(string url, string path, long offset, Action<long> onBytes, CancellationToken cancel)
		{
			byte[] data = File.ReadAllBytes(Map(url));
			if (IgnoreRange)
			{
				offset = 0;
			}
			Offsets.Add(offset);
			using (FileStream file = new FileStream(path, offset > 0 ? FileMode.Append : FileMode.Create))
			{
				for (long i = offset; i < data.Length; i++)
				{
					if (BreakAfter >= 0 && i - offset >= BreakAfter)
					{
						BreakAfter = -1;
						throw new IOException("zerwane połączenie (test)");
					}
					file.WriteByte(data[i]);
				}
			}
			onBytes?.Invoke(data.Length - offset);
			return offset;
		}
	}

	private static string Sha(byte[] data)
	{
		using (SHA256 sha = SHA256.Create())
		{
			return string.Concat(sha.ComputeHash(data).Select(b => b.ToString("x2")));
		}
	}

	private class FakeMirror
	{
		public string Dir;
		public Dictionary<string, byte[]> Files = new Dictionary<string, byte[]>();
		public HashSet<string> Keep = new HashSet<string>();
		public List<string> Delete = new List<string>();
		public byte[] PatcherExe;
		public string Version = "3.0.23";

		public void Publish(string channel = "test", int schema = 1)
		{
			Files["YOHARA_VERSION"] = Encoding.ASCII.GetBytes(Version + "\r\n");
			List<object> list = new List<object>();
			foreach (KeyValuePair<string, byte[]> f in Files)
			{
				string sha = Sha(f.Value);
				string store = Path.Combine(Dir, "files", sha.Substring(0, 2), sha);
				Directory.CreateDirectory(Path.GetDirectoryName(store));
				File.WriteAllBytes(store, f.Value);
				list.Add(new { path = f.Key, size = f.Value.Length, sha256 = sha, keep = Keep.Contains(f.Key) });
			}
			object patcher = null;
			if (PatcherExe != null)
			{
				string sha = Sha(PatcherExe);
				string store = Path.Combine(Dir, "files", sha.Substring(0, 2), sha);
				Directory.CreateDirectory(Path.GetDirectoryName(store));
				File.WriteAllBytes(store, PatcherExe);
				patcher = new { version = "1.0.1", size = PatcherExe.Length, sha256 = sha };
			}
			Directory.CreateDirectory(Path.Combine(Dir, channel));
			File.WriteAllText(Path.Combine(Dir, channel, "manifest.json"), JsonConvert.SerializeObject(new {
				marker = Mirror.Marker, schema, product = "MT2009 PLUS Yohara", channel, version = Version, clientVersion = "1.3.3",
				published = "2026-11-10T00:00:00Z", files = list, delete = Delete, patcher }));
			File.WriteAllText(Path.Combine(Dir, "channels.json"), JsonConvert.SerializeObject(new {
				marker = Mirror.Marker, schema = 1, @default = "test",
				channels = new Dictionary<string, object> { { channel, new { manifest = channel + "/manifest.json", version = Version } } } }));
		}
	}

	private static UpdateResult RunOnce(FakeHttp http, string root, bool full = false, string self = null, string channel = null)
	{
		return new Updater(http, s => Console.WriteLine("        | " + s)).Run(new UpdateOptions {
			Root = root, MirrorUrl = http.Prefix, FullVerify = full, SelfPath = self, Channel = channel, Attempts = 3 }, null);
	}

	private static void Unit()
	{
		Console.WriteLine("Ścieżki i lista");
		foreach (string ok in new[] { "pack/root.data", "pack\\root.index", "metin2client.exe", "lib/os.pyc", "YOHARA_VERSION" })
		{
			Check(Mirror.IsSafePath(ok) && !Mirror.IsForeign(ok), "dozwolone: " + ok);
		}
		foreach (string badPath in new[] { "../x.exe", "pack/../../x", "C:\\Windows\\x", "\\x", "/etc/x", "a//b", "", "pack/./x", "x.", "a|b" })
		{
			Check(!Mirror.IsSafePath(badPath), "odrzucone: " + badPath);
		}
		foreach (string foreign in new[] { "MT2009-Patcher.exe", "mt2009-patcher.exe.config", "update-manifest-mt2009.json", "client-files.json", ".yohara-patcher/stan.json" })
		{
			Check(Mirror.IsForeign(foreign), "plik 2.x / własny odrzucony: " + foreign);
		}
		Check(Mirror.FileUrl("http://h/aktualizacje/yohara", "AB" + new string('c', 62)) == "http://h/aktualizacje/yohara/files/ab/ab" + new string('c', 62), "adres pliku = mirror/files/aa/sha");
		string zero = new string('0', 64);
		Func<object, string> j = o => JsonConvert.SerializeObject(o);
		Action<string, string> rejects = (json, what) => {
			bool threw = false;
			try { Mirror.ParseManifest(json, "test"); } catch (FormatException) { threw = true; } catch (JsonException) { threw = true; }
			Check(threw, "lista odrzucona: " + what);
		};
		rejects("{\"schema\":1,\"version\":\"2.0.71\",\"files\":[{\"path\":\"metin2client.exe\",\"size\":1,\"sha256\":\"" + zero + "\"}]}", "client-files.json 2.x (bez markera)");
		rejects("{\"server\":{\"version\":\"2.42.0\"},\"client\":{\"version\":\"2.0.71\",\"url\":\"https://github.com/x\"}}", "update-manifest-mt2009.json");
		rejects(j(new { marker = Mirror.Marker, channel = "stable", version = "3", files = new[] { new { path = "a", size = 1, sha256 = zero } } }), "inny kanał");
		rejects(j(new { marker = Mirror.Marker, channel = "test", version = "3", files = new[] { new { path = "a", size = 1, sha256 = zero }, new { path = "A", size = 1, sha256 = zero } } }), "plik dwa razy");
		rejects(j(new { marker = Mirror.Marker, channel = "test", version = "3", files = new[] { new { path = "MT2009-Patcher.exe", size = 1, sha256 = zero } } }), "patcher 2.x na liście");
		rejects(j(new { marker = Mirror.Marker, channel = "test", version = "3", files = new[] { new { path = "..\\a", size = 1, sha256 = zero } } }), "ścieżka ..");
		rejects(j(new { marker = Mirror.Marker, channel = "test", version = "3", files = new[] { new { path = "a", size = 1, sha256 = "xyz" } } }), "zła suma");
		bool chThrew = false;
		try { Mirror.ParseChannels(j(new { marker = Mirror.Marker, @default = "test", channels = new Dictionary<string, object> { { "test", new { manifest = "https://github.com/x.json" } } } })); } catch (FormatException) { chThrew = true; }
		Check(chThrew, "kanał z adresem bezwzględnym odrzucony");

		string tmp = Path.Combine(Path.GetTempPath(), "yohara-patcher-unit-" + Process.GetCurrentProcess().Id);
		if (Directory.Exists(tmp)) Directory.Delete(tmp, true);
		Directory.CreateDirectory(tmp);

		Console.WriteLine("Rozpoznanie folderu");
		string none = Path.Combine(tmp, "pusty");
		Directory.CreateDirectory(none);
		string classic = Path.Combine(tmp, "klient-2x");
		Directory.CreateDirectory(Path.Combine(classic, "pack"));
		File.WriteAllText(Path.Combine(classic, "pack", "root.index"), "2x");
		File.WriteAllText(Path.Combine(classic, "CLIENT_VERSION"), "2.0.71");
		string yoh = Path.Combine(tmp, "klient-yohara");
		Directory.CreateDirectory(Path.Combine(yoh, "pack"));
		File.WriteAllText(Path.Combine(yoh, "pack", "hydra_map.index"), "y");
		File.WriteAllText(Path.Combine(yoh, "CLIENT_VERSION"), "2.0.64");
		Check(YoharaClient.Detect(none) == ClientKind.None, "pusty folder = brak klienta");
		Check(YoharaClient.Detect(classic) == ClientKind.Classic2x, "klient 2.x rozpoznany");
		Check(YoharaClient.Detect(yoh) == ClientKind.Yohara, "Yohara po paczce hydra_map");
		string yoh2 = Path.Combine(tmp, "klient-yohara-stamp");
		Directory.CreateDirectory(yoh2);
		File.WriteAllText(Path.Combine(yoh2, "YOHARA_VERSION"), "3.0.23\r\n");
		Check(YoharaClient.Detect(yoh2) == ClientKind.Yohara && YoharaClient.ReadStamp(yoh2) == "3.0.23", "Yohara po YOHARA_VERSION");

		Console.WriteLine("Aktualizacja (atrapa serwera)");
		FakeMirror mirror = new FakeMirror { Dir = Path.Combine(tmp, "mirror") };
		byte[] big = new byte[200000];
		new Random(7).NextBytes(big);
		mirror.Files["pack/root.data"] = big;
		mirror.Files["pack/root.index"] = Encoding.ASCII.GetBytes("root index v23");
		mirror.Files["pack/hydra_map.index"] = Encoding.ASCII.GetBytes("y");
		mirror.Files["pack/dbdata.data"] = Encoding.ASCII.GetBytes("dbdata base 23");
		mirror.Files["lib/os.pyc"] = Encoding.ASCII.GetBytes("os");
		mirror.Files["YOHARA_VERSION"] = Encoding.ASCII.GetBytes("3.0.23\r\n");
		mirror.Files["empty.txt"] = new byte[0];
		mirror.Keep.Add("pack/dbdata.data");
		mirror.Publish();
		FakeHttp http = new FakeHttp { Prefix = "http://mirror.test/aktualizacje/yohara/", Folder = mirror.Dir };

		UpdateResult r = RunOnce(http, classic);
		Check(r.State == UpdateState.Refused && !File.Exists(Path.Combine(classic, "pack", "root.data")) && http.Urls.Count == 0, "folder 2.x: odmowa, nic nie pobrane, bez połączenia");
		r = RunOnce(http, none);
		Check(r.State == UpdateState.Refused && Directory.GetFileSystemEntries(none).Length == 0, "folder bez klienta: odmowa");

		File.WriteAllText(Path.Combine(yoh, "pack", "dbdata.data"), "the player's own dbdata");
		File.WriteAllText(Path.Combine(yoh, "pack", "old.data"), "old");
		mirror.Delete.Add("pack/old.data");
		mirror.Publish();
		http.BreakAfter = 50000;
		r = RunOnce(http, yoh);
		Check(r.State == UpdateState.Updated, "pierwsza aktualizacja: " + r.State + " - " + r.Message);
		Check(http.Offsets.Any(o => o == 50000), "pobieranie wznowione od bajtu 50000 po zerwaniu");
		Check(File.ReadAllBytes(Path.Combine(yoh, "pack", "root.data")).SequenceEqual(big), "root.data poprawny po wznowieniu");
		Check(File.ReadAllText(Path.Combine(yoh, "pack", "dbdata.data")) == "the player's own dbdata", "dbdata gracza zostaje (keep, pierwsze uruchomienie)");
		Check(!File.Exists(Path.Combine(yoh, "pack", "old.data")) && r.Deleted == 1, "plik z listy delete usunięty");
		Check(YoharaClient.ReadStamp(yoh) == "3.0.23", "YOHARA_VERSION = 3.0.23");
		Check(File.Exists(Path.Combine(yoh, "empty.txt")) && new FileInfo(Path.Combine(yoh, "empty.txt")).Length == 0, "pusty plik");
		Check(File.Exists(Path.Combine(yoh, ".yohara-patcher", "stan.json")) && Directory.GetFiles(Path.Combine(yoh, ".yohara-patcher", "tmp")).Length == 0, "stan.json zapisany, tmp pusty");
		Check(http.Urls.All(u => u.StartsWith(http.Prefix)), "tylko adresy serwera Yohary");

		http.Urls.Clear();
		r = RunOnce(http, yoh);
		Check(r.State == UpdateState.UpToDate && r.Downloaded == 0, "drugie uruchomienie: aktualny");

		// same size, other content (time of change moves): the quick check sees it
		string idx = Path.Combine(yoh, "pack", "root.index");
		File.WriteAllText(idx, "root index BAD");
		r = RunOnce(http, yoh);
		Check(r.State == UpdateState.Updated && r.Downloaded == 1 && File.ReadAllText(idx) == "root index v23", "zmieniony plik (ten sam rozmiar) naprawiony");

		// the same, but the time of change put back: only "Napraw klienta" sees it
		DateTime when = File.GetLastWriteTimeUtc(idx);
		File.WriteAllText(idx, "root index XXX");
		File.SetLastWriteTimeUtc(idx, when);
		r = RunOnce(http, yoh);
		Check(r.State == UpdateState.UpToDate, "szybkie sprawdzenie ufa zapamiętanej sumie (ten sam rozmiar i czas)");
		r = RunOnce(http, yoh, full: true);
		Check(r.State == UpdateState.Updated && r.Downloaded == 1 && File.ReadAllText(idx) == "root index v23", "Napraw klienta: pełne sprawdzenie naprawia");
		r = RunOnce(http, yoh, full: true);
		Check(r.State == UpdateState.UpToDate && r.Checked == mirror.Files.Count, "Napraw klienta: wszystko poprawne");

		// keep: a new base of dbdata on the mirror is downloaded once
		mirror.Files["pack/dbdata.data"] = Encoding.ASCII.GetBytes("dbdata base 24");
		mirror.Version = "3.0.24";
		mirror.Publish();
		r = RunOnce(http, yoh);
		Check(r.State == UpdateState.Updated && File.ReadAllText(Path.Combine(yoh, "pack", "dbdata.data")) == "dbdata base 24", "nowa baza dbdata z serwera pobrana");
		File.WriteAllText(Path.Combine(yoh, "pack", "dbdata.data"), "panel zip again");
		r = RunOnce(http, yoh, full: true);
		Check(r.State == UpdateState.UpToDate && File.ReadAllText(Path.Combine(yoh, "pack", "dbdata.data")) == "panel zip again", "dbdata z panelu zostaje także przy naprawie");
		File.Delete(Path.Combine(yoh, "pack", "dbdata.data"));
		r = RunOnce(http, yoh);
		Check(r.Downloaded == 1 && File.ReadAllText(Path.Combine(yoh, "pack", "dbdata.data")) == "dbdata base 24", "brakujące dbdata pobrane");

		// server without Range
		mirror.Files["pack/root.data"] = big.Reverse().ToArray();
		mirror.Publish();
		string rootData = Path.Combine(yoh, "pack", "root.data");
		http.BreakAfter = 1000;
		http.IgnoreRange = true;
		http.Offsets.Clear();
		r = RunOnce(http, yoh);
		Check(r.State == UpdateState.Updated && File.ReadAllBytes(rootData).SequenceEqual(big.Reverse()) && http.Offsets.All(o => o == 0), "serwer bez Range: pobranie od nowa, plik poprawny");
		http.IgnoreRange = false;

		// a broken store file: the old file stays untouched
		byte[] newIndex = Encoding.ASCII.GetBytes("root index v25");
		mirror.Files["pack/root.index"] = newIndex;
		mirror.Publish();
		string bad = Path.Combine(mirror.Dir, "files", Sha(newIndex).Substring(0, 2), Sha(newIndex));
		File.WriteAllText(bad, "root index ZZZ");
		r = RunOnce(http, yoh);
		Check(r.State == UpdateState.Partial && r.Failed.Contains("pack/root.index") && File.ReadAllText(idx) == "root index v23", "uszkodzony plik na serwerze: stary plik nietknięty, błąd zgłoszony");
		Check(YoharaClient.ReadStamp(yoh) == "3.0.24", "wersja nie zmienia się przy błędzie");
		File.WriteAllBytes(bad, newIndex);
		r = RunOnce(http, yoh);
		Check(r.State == UpdateState.Updated && File.ReadAllText(idx) == "root index v25", "po naprawie serwera plik pobrany");

		// self-update
		string self = Path.Combine(yoh, "MT2009-Yohara-Patcher.exe");
		File.WriteAllText(self, "old patcher");
		mirror.PatcherExe = Encoding.ASCII.GetBytes("new patcher 1.0.1");
		mirror.Publish();
		r = RunOnce(http, yoh, self: self);
		Check(r.State == UpdateState.PatcherUpdated && r.NewPatcherPath != null && File.ReadAllText(r.NewPatcherPath) == "new patcher 1.0.1", "nowy patcher pobrany i sprawdzony");
		Updater.SwapSelf(self, r.NewPatcherPath);
		Check(File.ReadAllText(self) == "new patcher 1.0.1" && File.ReadAllText(self + ".old") == "old patcher", "podmiana exe (stary jako .old)");
		Updater.CleanupOldSelf(self);
		Check(!File.Exists(self + ".old"), ".old usunięty po restarcie");
		r = RunOnce(http, yoh, self: self);
		Check(r.State == UpdateState.UpToDate, "aktualny patcher: brak samoaktualizacji");

		// a newer list schema
		mirror.Publish(schema: 2);
		r = RunOnce(http, yoh);
		Check(r.State == UpdateState.Failed && r.Message.Contains("nowszego patchera"), "nowszy schemat listy: prośba o nowy patcher");
		mirror.Publish();

		r = RunOnce(http, yoh, channel: "stable");
		Check(r.State == UpdateState.Failed && r.Message.Contains("stable"), "nieistniejący kanał");
		http.Prefix = "http://nie-ma.test/";
		http.Folder = Path.Combine(tmp, "nie-ma");
		r = RunOnce(http, yoh);
		Check(r.State == UpdateState.Offline, "serwer niedostępny: można grać");

		Directory.Delete(tmp, true);
	}
}
