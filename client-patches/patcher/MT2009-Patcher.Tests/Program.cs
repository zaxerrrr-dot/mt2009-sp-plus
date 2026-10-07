using N2_Patcher.Core;
using N2_Patcher.Model;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net;
using System.Text;

// Linux tests of MT2009-Patcher (the non-UI .cs files, compiled as they are).
//   dotnet run -- unit                         checks without network
//   dotnet run -- coop <cases.json> <outdir>   coop.cfg results as JSON (+ files) for the PowerShell/Python comparison
//   dotnet run -- read <file>...               CoopServer.Read results as JSON
//   dotnet run -- patch <server url> <dir>     patch list + download + hash check against the patch server
//   dotnet run -- news <url>                   news.json parse
//   dotnet run -- probe                        server status (localhost test stack, closed port, bad host)
//   dotnet run -- dbdata <manifest url> <dir>  MT2009_PLUS_DBDATA_AUTO_V1 against a real panel (fresh client folder)
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
			case "coop": Coop(args[1], args[2]); return 0;
			case "read": Read(args.Skip(1).ToArray()); return 0;
			case "patch": Patch(args[1], args[2]); break;
			case "news": News(args[1]); break;
			case "probe": Probe(); break;
			case "dbdata": DbDataLive(args[1], args[2]); break;
			default: Console.WriteLine("?"); return 2;
		}
		Console.WriteLine(failures == 0 ? "WYNIK: wszystko OK" : "WYNIK: błędów: " + failures);
		return failures == 0 ? 0 : 1;
	}

	private static void Unit()
	{
		Console.WriteLine("PatchCore");
		Check(PatchCore.IsSafeName("pack\\root.data"), "pack\\root.data dozwolone");
		Check(PatchCore.IsSafeName("metin2client.exe"), "metin2client.exe dozwolone");
		foreach (string bad in new[] { "..\\x.exe", "pack\\..\\..\\x", "C:\\Windows\\x", "\\x", "/etc/x", "a\\\\b", "" })
		{
			Check(!PatchCore.IsSafeName(bad), "odrzucone: " + bad);
		}
		Check(PatchCore.GetFolder("C:\\Gry\\MT2009\\pack\\root.data") == "C:\\Gry\\MT2009\\pack", "GetFolder jak w oryginale");
		Check(PatchCore.DownloadUri("http://h/patcher/files/", new PatchItem { Uid = "abc" }).ToString() == "http://h/patcher/files/abc", "adres = Clientdata + uid");

		string dir = Path.Combine(Path.GetTempPath(), "mt2009-patcher-unit-" + Process.GetCurrentProcess().Id) + Path.DirectorySeparatorChar;
		Directory.CreateDirectory(Path.Combine(dir, "pack"));
		File.WriteAllText(dir + "same.txt", "hello");
		File.WriteAllText(dir + "other.txt", "changed");
		File.WriteAllText(dir + "old.txt", "remove me");
		File.WriteAllText(dir + "kept.txt", "the player's own");
		File.WriteAllText(Path.Combine(dir, "pack", "x.index"), "hello");
		string md5Hello = "5D41402ABC4B2A76B9719D911017C592";
		Check(PatchCore.GetMD5(dir + "same.txt") == md5Hello, "MD5 wielkimi literami (BitConverter)");
		string json = JsonConvert.SerializeObject(new object[] {
			new { name = "same.txt", size = 5, md5 = md5Hello, uid = "a", delete = 0 },
			new { name = "other.txt", size = 5, md5 = md5Hello, uid = "b", delete = 0 },
			new { name = "missing.txt", size = 5, md5 = md5Hello, uid = "c", delete = 0 },
			new { name = "old.txt", size = 1, md5 = "", uid = "", delete = 1 },
			new { name = "gone.txt", size = 1, md5 = "", uid = "", delete = 1 },
			new { name = "zero.txt", size = 0, md5 = md5Hello, uid = "d", delete = 0 },
			new { name = "..\\evil.txt", size = 5, md5 = md5Hello, uid = "e", delete = 0 },
			new { name = "pack\\x.index", size = 3, md5 = md5Hello.ToLowerInvariant(), uid = "f", delete = 0 },
			new { name = "kept.txt", size = 5, md5 = md5Hello, uid = "g", delete = 0, keep = 1 },
			new { name = "keptmissing.txt", size = 5, md5 = md5Hello, uid = "h", delete = 0, keep = 1 },
		});
		List<PatchItem> list = PatchCore.ParsePatchlist(json);
		int checkedCount = 0;
		List<PatchItem> need = PatchCore.SelectForDownload(list, dir, () => checkedCount++);
		string names = string.Join(",", need.Select(i => i.Filename));
		Check(names == "other.txt,missing.txt,pack\\x.index,keptmissing.txt", "do pobrania: inny MD5, brakujący, md5 małymi literami = różny, keep tylko brakujący (" + names + ")");
		Check(!File.Exists(dir + "old.txt"), "wpis delete usunął plik");
		Check(checkedCount == list.Count, "postęp sprawdzania: 1 na wpis (" + checkedCount + ")");
		Check(PatchCore.ParsePatchlist("[]").Count == 0, "pusta lista");
		bool threw = false;
		try { PatchCore.ParsePatchlist("<html>"); } catch (Exception) { threw = true; }
		Check(threw, "nie-JSON = wyjątek (patcher: serwer niedostępny)");
		Directory.Delete(dir, true);

		Console.WriteLine("CoopServer");
		CoopServer s = CoopServer.Create("Serwer Łukasza ąę", "http://203.0.113.10/", " 11000 ", "13000", "2");
		Check(s.Name == "Serwer Lukasza ae", "polskie litery -> ASCII (" + s.Name + ")");
		Check(s.Host == "203.0.113.10", "http://IP/ -> IP");
		Check(s.Text == "# MT2009 PLUS - serwer VPS (zapisane przez MT2009-Patcher)\r\nname=Serwer Lukasza ae\r\nhost=203.0.113.10\r\nauth=11000\r\nchannel=13000\r\nchannels=2\r\n", "tekst pliku CRLF");
		Check(CoopServer.ToAsciiName("a=b  c") == "a-b c", "= na -, podwójne spacje");
		Check(CoopServer.ToAsciiName(new string('x', 90)).Length == 80, "maks. 80 znaków");
		string Err(Func<CoopServer> f) { try { f(); return null; } catch (CoopException e) { return e.Message; } }
		Check(Err(() => CoopServer.Create("", "1.2.3.4")) == "Wpisz nazwę serwera.", "brak nazwy");
		Check(Err(() => CoopServer.Create("A", "1.2.3.4:13000")) == "Wpisz samo IP, bez portu (porty są w polach poniżej).", "IP:port");
		Check(Err(() => CoopServer.Create("A", "999.1.1.1"))?.StartsWith("Nieprawidłowy adres IPv4") == true, "zły IPv4");
		Check(Err(() => CoopServer.Create("A", "ser wer.pl"))?.StartsWith("Nieprawidłowe IP lub nazwa domeny") == true, "zła domena");
		Check(Err(() => CoopServer.Create("A", "1.2.3.4", "13000", "13000", "2")) == "Port logowania (13000) nie może być taki sam jak port kanału (13000 / 13010).", "logowanie = kanał");
		Check(Err(() => CoopServer.Create("A", "1.2.3.4", "11000", "65530", "2"))?.StartsWith("Port kanału 2 wyniósłby 65540") == true, "CH2 > 65535");
		Check(Err(() => CoopServer.Create("A", "1.2.3.4", "11000", "65530", "1")) == null, "1 kanał 65530 ok");
		Check(Err(() => CoopServer.Create("A", "1.2.3.4", "0")) == "Port logowania musi być liczbą od 1 do 65535.", "port 0");
		Check(Err(() => CoopServer.Create("A", "1.2.3.4", "11000", "13000", "3")) == "Liczba kanałów musi wynosić 1 albo 2.", "3 kanały");
		string root = Path.Combine(Path.GetTempPath(), "mt2009-coop-" + Process.GetCurrentProcess().Id);
		Directory.CreateDirectory(root);
		Check(CoopServer.Discover(root).Single().Slot == 0, "bez coop*.cfg: localhost");
		CoopServer.Save(root, 2, CoopServer.Create("Drugi", "vps.example.com", "21000", "23000", "1"));
		List<CoopServer> found = CoopServer.Discover(root);
		Check(found.Count == 1 && found[0].Slot == 2 && found[0].DisplayName == "Online: Drugi" && found[0].ChannelPorts.SequenceEqual(new[] { 23000 }), "coop2.cfg odczytany");
		File.WriteAllText(CoopServer.PathFor(root, 1), "name=Zly\r\nhost=1.2.3.4\r\n");
		Check(CoopServer.Read(CoopServer.PathFor(root, 1), 1).Valid == false && CoopServer.Discover(root).Count == 1, "uszkodzony coop.cfg pominięty");
		CoopServer.Save(root, 1, CoopServer.Create("Pierwszy", "1.2.3.4"));
		Check(CoopServer.Discover(root).Select(x => x.Slot).SequenceEqual(new[] { 1, 2 }), "oba serwery, kolejność 1, 2");
		Check(File.ReadAllBytes(CoopServer.PathFor(root, 1)).All(b => b < 128), "plik ASCII");
		CoopServer.Remove(root, 1);
		CoopServer.Remove(root, 2);
		Check(CoopServer.Discover(root).Single().Slot == 0, "po usunięciu: localhost");
		Directory.Delete(root, true);

		DbDataUnit();
	}

	// ------------------------------------------------ MT2009_PLUS_DBDATA_AUTO_V1

	private static string Sha(byte[] b) => DbDataSync.Sha256Bytes(b);

	private static string StampText(string stamp, long index, long data) =>
		"# MT2009_PLUS_DBDATA_STAMP_V1: test\r\nstamp " + stamp + "\r\nsize pack/dbdata.index " + index + "\r\nsize pack/dbdata.data " + data + "\r\n";

	// A panel in memory: {url: body}.
	private static Dictionary<string, byte[]> FakePanel(string root, string version, string stamp, byte[] index, byte[] data, byte[] baseIndex, byte[] baseData)
	{
		string m = JsonConvert.SerializeObject(new
		{
			format = "MT2009_PLUS_DBDATA_AUTO_V1", client_version_base = version, stamp = stamp, edited = stamp != version, built = 1,
			files = new object[] {
				new { name = "pack/dbdata.index", size = index.Length, sha256 = Sha(index), url = stamp + "/dbdata.index" },
				new { name = "pack/dbdata.data", size = data.Length, sha256 = Sha(data).ToLowerInvariant(), url = stamp + "/dbdata.data" } },
			@base = new { index_sha256 = Sha(baseIndex), data_sha256 = Sha(baseData) },
			stamp_file = StampText(stamp, index.Length, data.Length)
		});
		return new Dictionary<string, byte[]> {
			[root + "klient/dbdata/manifest.json"] = Encoding.UTF8.GetBytes(m),
			[root + "klient/dbdata/" + stamp + "/dbdata.index"] = index,
			[root + "klient/dbdata/" + stamp + "/dbdata.data"] = data,
		};
	}

	private static DbDataSync.Fetcher Fetch(Dictionary<string, byte[]> panel, List<string> asked = null) => (url, timeout, max) =>
	{
		asked?.Add(url);
		if (!panel.TryGetValue(url, out byte[] body)) throw new WebException("404 " + url);
		if (body.LongLength > max) throw new InvalidDataException("za duża odpowiedź");
		return body;
	};

	private static void DbDataUnit()
	{
		Console.WriteLine("DbDataSync (MT2009_PLUS_DBDATA_AUTO_V1)");
		CoopServer local = CoopServer.Localhost();
		List<string> urls = DbDataSync.CandidateUrls(local, "");
		Check(urls.SequenceEqual(new[] { "http://127.0.0.1:7790/klient/dbdata/manifest.json", "http://127.0.0.1:17790/klient/dbdata/manifest.json", "http://127.0.0.1/klient/dbdata/manifest.json" }),
			"localhost: 7790, logowanie+6790, port 80 (" + string.Join(" ", urls) + ")");
		CoopServer vps = new CoopServer { Valid = true, Name = "V", Host = "203.0.113.5", Auth = 21000, Channel = 23000, Channels = 2, Slot = 1, Panel = "27795" };
		urls = DbDataSync.CandidateUrls(vps, null);
		Check(urls[0] == "http://203.0.113.5:27795/klient/dbdata/manifest.json" && urls[1] == "http://203.0.113.5:7790/klient/dbdata/manifest.json" && urls[2] == "http://203.0.113.5:27790/klient/dbdata/manifest.json", "panel= z coop.cfg najpierw, potem 7790 i blok NAT");
		vps.Panel = "https://panel.example.com/gra/";
		Check(DbDataSync.CandidateUrls(vps, "")[0] == "https://panel.example.com/gra/klient/dbdata/manifest.json", "panel= jako adres");
		Check(DbDataSync.CandidateUrls(vps, "off") == null, "DbDataManifest=off wyłącza");
		Check(DbDataSync.CandidateUrls(vps, "http://{host}:8080/x/manifest.json;ftp://zle").SequenceEqual(new[] { "http://203.0.113.5:8080/x/manifest.json" }), "DbDataManifest z {host}, tylko http(s)");
		string coopDir = Path.Combine(Path.GetTempPath(), "mt2009-coop-panel-" + Process.GetCurrentProcess().Id);
		Directory.CreateDirectory(coopDir);
		File.WriteAllText(Path.Combine(coopDir, "coop.cfg"), "name=A\r\nhost=1.2.3.4\r\nauth=11000\r\nchannel=13000\r\nchannels=2\r\npanel=17790\r\n");
		CoopServer withPanel = CoopServer.Read(Path.Combine(coopDir, "coop.cfg"), 1);
		Check(withPanel.Valid && withPanel.Panel == "17790", "coop.cfg: panel= czytany, plik nadal ważny");
		Directory.Delete(coopDir, true);
		Check(DbDataSync.CompareVersions("2.0.57", "2.0.9") > 0 && DbDataSync.CompareVersions("2.0.56", "2.0.57") < 0 && DbDataSync.CompareVersions("2.0", "2.0.0") == 0, "porównanie wersji liczbowe");

		string dir = Path.Combine(Path.GetTempPath(), "mt2009-dbdata-" + Process.GetCurrentProcess().Id);
		if (Directory.Exists(dir)) Directory.Delete(dir, true);
		Directory.CreateDirectory(Path.Combine(dir, "pack"));
		string idx = Path.Combine(dir, "pack", "dbdata.index"), dat = Path.Combine(dir, "pack", "dbdata.data"), stampPath = Path.Combine(dir, "dbdata_stamp.txt");
		Random rnd = new Random(7);
		byte[] Bytes(int n) { byte[] b = new byte[n]; rnd.NextBytes(b); return b; }
		byte[] baseIndex = Bytes(292), baseData = Bytes(4096), editIndex = Bytes(300), editData = Bytes(5000);
		File.WriteAllBytes(idx, baseIndex);
		File.WriteAllBytes(dat, baseData);
		File.WriteAllText(Path.Combine(dir, "CLIENT_VERSION"), "2.0.57\n");
		string srv = "http://127.0.0.1:7790/";
		List<string> cands = DbDataSync.CandidateUrls(local, "");
		List<string> statuses = new List<string>();

		// the server untouched by the editor, the client's pack is the release's: nothing downloaded
		var panel = FakePanel(srv, "2.0.57", "2.0.57", baseIndex, baseData, baseIndex, baseData);
		List<string> asked = new List<string>();
		DbDataResult r = DbDataSync.Run(dir, cands, Fetch(panel, asked), statuses.Add, 2000);
		Check(r.State == DbDataState.UpToDate && !asked.Any(u => u.EndsWith(".data")), "baza = paczka klienta: nic nie pobrano (" + r.State + ")");
		Check(File.ReadAllText(stampPath) == StampText("2.0.57", 292, 4096), "dbdata_stamp.txt zapisany (" + DbDataSync.StampOfLocal(dir, null) + ")");

		// the editor changed items: both files, verified, swapped with .bak, stamp file
		panel = FakePanel(srv, "2.0.57", "2.0.57-0123456789ab", editIndex, editData, baseIndex, baseData);
		statuses.Clear();
		r = DbDataSync.Run(dir, cands, Fetch(panel), statuses.Add, 2000);
		Check(r.State == DbDataState.Updated, "zmiany z edytora: pobrano (" + r.State + " " + r.Detail + ")");
		Check(statuses.Contains("Pobieram dane bazy z serwera…"), "status po polsku: Pobieram dane bazy z serwera…");
		Check(File.ReadAllBytes(idx).SequenceEqual(editIndex) && File.ReadAllBytes(dat).SequenceEqual(editData), "pack/dbdata.* podmienione");
		Check(File.ReadAllBytes(idx + ".bak").SequenceEqual(baseIndex) && File.ReadAllBytes(dat + ".bak").SequenceEqual(baseData), "stare pliki w *.bak");
		Check(DbDataSync.StampOfLocal(dir, null) == "2.0.57-0123456789ab", "znacznik = serwera (gra nie pokaże ostrzeżenia)");
		Check(!Directory.GetFiles(Path.Combine(dir, "pack"), "*.tmp").Any() && !File.Exists(stampPath + ".tmp"), "bez plików *.tmp");
		r = DbDataSync.Run(dir, cands, Fetch(panel), null, 2000);
		Check(r.State == DbDataState.UpToDate, "drugi raz: aktualne");

		// a damaged download never reaches the pack
		var bad = FakePanel(srv, "2.0.57", "2.0.57-ffffffffffff", baseIndex, baseData, baseIndex, baseData);
		bad[srv + "klient/dbdata/2.0.57-ffffffffffff/dbdata.data"] = editData;
		r = DbDataSync.Run(dir, cands, Fetch(bad), null, 2000);
		Check(r.State == DbDataState.Failed && File.ReadAllBytes(dat).SequenceEqual(editData) && File.ReadAllBytes(idx).SequenceEqual(editIndex), "zła suma SHA-256: Failed, paczka bez zmian");

		// the game running (pack open without sharing): nothing swapped
		panel = FakePanel(srv, "2.0.57", "2.0.57", baseIndex, baseData, baseIndex, baseData);
		using (new FileStream(dat, FileMode.Open, FileAccess.Read, FileShare.Read))
		{
			r = DbDataSync.Run(dir, cands, Fetch(panel), null, 2000);
		}
		Check(r.State == DbDataState.GameRunning && File.ReadAllBytes(dat).SequenceEqual(editData), "gra uruchomiona: GameRunning, paczka bez zmian (" + r.State + ")");
		r = DbDataSync.Run(dir, cands, Fetch(panel), null, 2000);
		Check(r.State == DbDataState.Updated && File.ReadAllBytes(dat).SequenceEqual(baseData) && DbDataSync.StampOfLocal(dir, null) == "2.0.57", "serwer wrócił do oryginału: oryginalne pliki");

		// client versions
		var newer = FakePanel(srv, "2.0.58", "2.0.58-0123456789ab", editIndex, editData, Bytes(10), Bytes(10));
		r = DbDataSync.Run(dir, cands, Fetch(newer), null, 2000);
		Check(r.State == DbDataState.ClientOlder && r.Detail.Contains("2.0.58") && File.ReadAllBytes(dat).SequenceEqual(baseData), "klient starszy niż baza serwera: najpierw aktualizacja klienta");
		File.WriteAllText(Path.Combine(dir, "CLIENT_VERSION"), "2.0.60\r\n");
		r = DbDataSync.Run(dir, cands, Fetch(panel), null, 2000);
		Check(r.State == DbDataState.UpToDate, "nowszy klient, ta sama paczka: aktualne");
		var older = FakePanel(srv, "2.0.57", "2.0.57-0123456789ab", editIndex, editData, baseIndex, baseData);
		r = DbDataSync.Run(dir, cands, Fetch(older), null, 2000);
		Check(r.State == DbDataState.Updated, "nowszy klient z paczką bazy serwera: pobrano (" + r.State + ")");
		File.WriteAllBytes(dat, Bytes(4100));  // the newer client's own, different pack
		File.Delete(stampPath);
		r = DbDataSync.Run(dir, cands, Fetch(older), null, 2000);
		Check(r.State == DbDataState.ServerOlder && File.ReadAllBytes(dat).Length == 4100, "nowszy klient z inną paczką: nie mieszam (ServerOlder)");

		// nothing answers / not a manifest
		var junk = new Dictionary<string, byte[]> { [srv + "klient/dbdata/manifest.json"] = Encoding.UTF8.GetBytes("<html>login</html>") };
		r = DbDataSync.Run(dir, cands, Fetch(junk), null, 2000);
		Check(r.State == DbDataState.Unreachable, "strona logowania zamiast manifestu = niedostępny");
		Stopwatch sw = Stopwatch.StartNew();
		r = DbDataSync.Run(dir, cands, (u, t, m) => { System.Threading.Thread.Sleep(10000); return null; }, null, 1000);
		Check(r.State == DbDataState.Unreachable && sw.ElapsedMilliseconds < 4000, "brak odpowiedzi: po limicie czasu (" + sw.ElapsedMilliseconds + " ms)");
		r = DbDataSync.Run(dir, null, Fetch(panel), null, 2000);
		Check(r.State == DbDataState.Disabled, "wyłączone");
		// manifest checks
		var m = JObject.Parse(Encoding.UTF8.GetString(panel[srv + "klient/dbdata/manifest.json"]));
		Check(DbDataSync.ParseManifest(Encoding.UTF8.GetBytes(m.ToString())) != null, "manifest poprawny");
		foreach (var (key, value, what) in new (string, JToken, string)[] {
			("format", "X", "zły format"), ("stamp", "2.0.56-abc", "znacznik innej bazy"), ("stamp", "../x", "znacznik ze ścieżką"),
			("stamp_file", "stamp 2.0.1\r\n", "plik znacznika nie pasuje"), ("client_version_base", "abc", "zła wersja") })
		{
			JObject copy = (JObject)m.DeepClone();
			copy[key] = value;
			Check(DbDataSync.ParseManifest(Encoding.UTF8.GetBytes(copy.ToString())) == null, "odrzucony: " + what);
		}
		JObject renamed = (JObject)m.DeepClone();
		renamed["files"][1]["name"] = "metin2client.exe";
		Check(DbDataSync.ParseManifest(Encoding.UTF8.GetBytes(renamed.ToString())) == null, "odrzucony: inna nazwa pliku niż pack/dbdata.*");
		Directory.Delete(dir, true);
	}

	// Against a real panel: a client folder with the release's CLIENT_VERSION
	// and no pack -> downloaded, then up to date.
	private static void DbDataLive(string manifestUrl, string dir)
	{
		dir = Path.GetFullPath(dir);
		Directory.CreateDirectory(Path.Combine(dir, "pack"));
		List<string> cands = new List<string> { manifestUrl };
		byte[] mbytes = DbDataSync.HttpFetch(manifestUrl, 5000, DbDataSync.MaxManifestBytes);
		DbDataManifest m = DbDataSync.ParseManifest(mbytes);
		Check(m != null, "manifest z panelu poprawny");
		if (m == null) return;
		Console.WriteLine($"  baza {m.ClientVersionBase}, znacznik {m.Stamp}, zmiany: {m.Edited}, {m.Files[1].Size} B");
		File.WriteAllText(Path.Combine(dir, "CLIENT_VERSION"), m.ClientVersionBase + "\n");
		DbDataResult r = DbDataSync.Run(dir, cands, DbDataSync.HttpFetch, s => Console.WriteLine("  status: " + s), 5000);
		Console.WriteLine("  " + r.State + ": " + r.Detail);
		Check(r.State == DbDataState.Updated || r.State == DbDataState.UpToDate, "pobrano z panelu");
		Check(DbDataSync.Sha256File(Path.Combine(dir, "pack", "dbdata.data")) == m.Files[1].Sha256, "SHA-256 paczki = manifest");
		Check(DbDataSync.StampOfLocal(dir, null) == m.Stamp, "dbdata_stamp.txt = znacznik serwera");
		r = DbDataSync.Run(dir, cands, DbDataSync.HttpFetch, null, 5000);
		Check(r.State == DbDataState.UpToDate, "drugi raz: aktualne");
	}

	private static void Coop(string casesPath, string outDir)
	{
		Directory.CreateDirectory(outDir);
		JArray cases = JArray.Parse(File.ReadAllText(casesPath));
		JArray results = new JArray();
		int i = 0;
		foreach (JObject c in cases)
		{
			JObject r = new JObject();
			try
			{
				CoopServer s = CoopServer.Create((string)c["name"], (string)c["host"], (string)c["auth"], (string)c["channel"], (string)c["channels"]);
				r["ok"] = true;
				// the header line names the program that wrote the file
				r["text"] = string.Join("\r\n", s.Text.Split("\r\n").Skip(1));
				File.WriteAllText(Path.Combine(outDir, "case" + i + ".cfg"), s.Text, Encoding.ASCII);
			}
			catch (CoopException e)
			{
				r["ok"] = false;
				r["error"] = e.Message;
			}
			results.Add(r);
			i++;
		}
		Console.OutputEncoding = new UTF8Encoding(false);
		Console.WriteLine(results.ToString(Formatting.None));
	}

	private static void Read(string[] files)
	{
		JArray results = new JArray();
		foreach (string f in files)
		{
			CoopServer s = CoopServer.Read(f);
			results.Add(s == null ? JValue.CreateNull() : new JObject { ["valid"] = s.Valid, ["name"] = s.Name, ["host"] = s.Host, ["auth"] = s.Auth, ["channel"] = s.Channel, ["channels"] = s.Channels });
		}
		Console.OutputEncoding = new UTF8Encoding(false);
		Console.WriteLine(results.ToString(Formatting.None));
	}

	// The same steps as CreatePatchlist + DownloadFiles: list from the server,
	// check, download each file from Clientdata + uid, check again.
	private static void Patch(string server, string dir)
	{
		if (!server.EndsWith("/")) server += "/";
		dir = Path.GetFullPath(dir) + Path.DirectorySeparatorChar;
		Directory.CreateDirectory(dir);
		using WebClient wc = new WebClient { Encoding = Encoding.UTF8 };
		wc.Headers.Add("user-agent", ".NET Framework Web Application / Patcher Client");
		Stopwatch sw = Stopwatch.StartNew();
		List<PatchItem> list = PatchCore.ParsePatchlist(wc.DownloadString(server + "patchlist.json"));
		Console.WriteLine($"lista: {list.Count} wpisów, {list.Sum(i => i.Filesize) / 1048576.0:0.0} MB");
		Check(list.Count > 0, "lista niepusta");
		Check(list.All(i => i.Md5Hash.Length == 32 && i.Md5Hash == i.Md5Hash.ToUpperInvariant()), "md5: 32 znaki, wielkie litery");
		Check(list.All(i => i.Filesize > 0 && PatchCore.IsSafeName(i.Filename) && !i.Filename.Contains('/')), "rozmiar > 0, bezpieczne nazwy z \\");
		string[] never = { "coop.cfg", "coop2.cfg", "metin2.cfg", "config.cfg", "syserr.txt", "log.txt" };
		Check(!list.Any(i => never.Contains(i.Filename.ToLowerInvariant()) || i.Filename.ToLowerInvariant().EndsWith(".cfg") || i.Filename.ToLowerInvariant().StartsWith("screenshot")), "brak plików gracza");
		List<PatchItem> need = PatchCore.SelectForDownload(list, dir, null);
		Console.WriteLine($"do pobrania: {need.Count} plików ({sw.ElapsedMilliseconds} ms sprawdzania)");
		sw.Restart();
		long bytes = 0;
		foreach (PatchItem item in need)
		{
			string path = PatchCore.LocalPath(dir, item.Filename);
			if (item.Filename.Contains("\\"))
			{
				Directory.CreateDirectory(PatchCore.GetFolder(path));
			}
			wc.DownloadFile(PatchCore.DownloadUri(server + "files/", item), path);
			bytes += item.Filesize;
		}
		double secs = Math.Max(sw.Elapsed.TotalSeconds, 0.001);
		Console.WriteLine($"pobrano {bytes / 1048576.0:0.0} MB w {secs:0.0} s ({bytes / 1048576.0 / secs:0.0} MB/s)");
		sw.Restart();
		List<PatchItem> again = PatchCore.SelectForDownload(list, dir, null);
		Console.WriteLine($"ponowne sprawdzenie: {sw.ElapsedMilliseconds} ms");
		Check(again.Count == 0, "po pobraniu wszystko zgodne (" + again.Count + " różnych)");
		// one damaged, one missing -> exactly these two
		PatchItem first = list.First(i => i.Filename.StartsWith("pack\\") && i.Filename.EndsWith(".index"));
		PatchItem second = list.First(i => i.Filename.EndsWith(".exe"));
		File.AppendAllText(PatchCore.LocalPath(dir, first.Filename), "x");
		File.Delete(PatchCore.LocalPath(dir, second.Filename));
		List<PatchItem> two = PatchCore.SelectForDownload(list, dir, null);
		Check(two.Count == 2 && two.Contains(first) && two.Contains(second), "uszkodzony + brakujący = 2 do pobrania");
	}

	private static void News(string url)
	{
		using WebClient wc = new WebClient { Encoding = Encoding.UTF8 };
		string text = wc.DownloadString(url);
		List<NewsItem> news = JsonConvert.DeserializeObject<List<NewsItem>>(text);
		Console.OutputEncoding = new UTF8Encoding(false);
		foreach (NewsItem n in news)
		{
			Console.WriteLine($"  [{n.newsType}] {n.topic} | {n.creator} | {n.threadUrl}");
		}
		Check(news.Count > 0, "aktualności: " + news.Count);
		Check(news.All(n => n.newsType >= 0 && n.newsType <= 2 && !string.IsNullOrEmpty(n.topic)), "typ 0-2 i tytuł");
		Check(news.Any(n => n.topic.Contains("ł") || n.message.Contains("ś")), "polskie znaki po UTF-8");
		Check(news.Count <= 10, "najwyżej 10 kropek suwaka (miejsce w oknie)");
	}

	private static void Probe()
	{
		CoopServer local = CoopServer.Localhost();
		ChannelState st = ServerProbe.Probe(local, 2000).GetAwaiter().GetResult();
		Console.WriteLine($"  localhost: logowanie={st.auth} CH1={st.channel_1} CH2={st.channel_2}");
		Check(st.auth && st.channel_1 && st.channel_2, "serwer testowy na 127.0.0.1 (11000/13000/13010) online");
		Stopwatch sw = Stopwatch.StartNew();
		CoopServer closed = new CoopServer { Valid = true, Name = "x", Host = "127.0.0.1", Auth = 1, Channel = 2, Channels = 1, Slot = 1 };
		st = ServerProbe.Probe(closed, 2000).GetAwaiter().GetResult();
		Check(!st.auth && !st.channel_1, "zamknięte porty = OFFLINE (" + sw.ElapsedMilliseconds + " ms)");
		sw.Restart();
		CoopServer blackhole = new CoopServer { Valid = true, Name = "x", Host = "10.255.255.1", Auth = 11000, Channel = 13000, Channels = 2, Slot = 1 };
		st = ServerProbe.Probe(blackhole, 1500).GetAwaiter().GetResult();
		Check(!st.auth && !st.channel_1 && !st.channel_2 && sw.ElapsedMilliseconds < 4000, "brak odpowiedzi = OFFLINE po limicie czasu (" + sw.ElapsedMilliseconds + " ms)");
		sw.Restart();
		CoopServer nohost = new CoopServer { Valid = true, Name = "x", Host = "nie-ma-takiego-hosta.invalid", Auth = 11000, Channel = 13000, Channels = 1, Slot = 1 };
		st = ServerProbe.Probe(nohost, 2000).GetAwaiter().GetResult();
		Check(!st.auth && !st.channel_1, "nieznana domena = OFFLINE (" + sw.ElapsedMilliseconds + " ms)");
	}
}
