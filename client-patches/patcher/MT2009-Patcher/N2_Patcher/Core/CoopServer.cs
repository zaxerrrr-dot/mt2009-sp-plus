using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

namespace N2_Patcher.Core
{
	// A bad value typed by the player; Message is a Polish sentence for a MessageBox.
	public class CoopException : Exception
	{
		public CoopException(string message) : base(message)
		{
		}
	}

	// One server of the client's server list besides localhost: coop.cfg
	// (slot 1) or coop2.cfg (slot 2). ASCII, CRLF, read by the client's
	// serverinfo.py (__LoadCoopServer):
	//   name=Serwer Artura / host=203.0.113.10 / auth=11000 / channel=13000 / channels=2
	// CH2 = channel + 10. The rules below are the ones of MT2009-Aktualizator.ps1
	// (New-AktCoopConfig, Read-AktCoopConfig), which follow the client.
	// MT2009_PLUS_CH34_AUTO_V1: the client takes channels=1..4 from 2.0.59 on
	// (CH3 = channel + 20, CH4 = channel + 30); ChannelSync sets the count from
	// the server, the VPS window still writes 1 or 2.
	public class CoopServer
	{
		public const int DefaultAuth = 11000;
		public const int DefaultChannel = 13000;
		public const int DefaultChannels = 2;
		public const int MaxChannels = 4;
		public const string LocalhostName = "mt2009 localhost";

		public bool Valid;
		public string Name = "";
		public string Host = "";
		public int Auth = DefaultAuth;
		public int Channel = DefaultChannel;
		public int Channels = DefaultChannels;
		public string Text = "";
		// 1 = coop.cfg, 2 = coop2.cfg, 0 = the built-in localhost server.
		public int Slot;
		// MT2009_PLUS_DBDATA_AUTO_V1: optional "panel=" line - the port of the
		// server's Seban panel, or its address (http://host:port/ or the whole
		// manifest URL), where the patcher asks for the database editor's
		// client files (DbDataSync). The client ignores the key.
		public string Panel = "";

		public static CoopServer Localhost()
		{
			return new CoopServer { Valid = true, Name = LocalhostName, Host = "127.0.0.1", Slot = 0 };
		}

		// The name the client shows in its server list.
		public string DisplayName
		{
			get { return this.Slot == 0 ? this.Name : "Online: " + this.Name; }
		}

		public int[] ChannelPorts
		{
			get
			{
				int[] ports = new int[Math.Max(1, Math.Min(MaxChannels, this.Channels))];
				for (int i = 0; i < ports.Length; i++)
				{
					ports[i] = this.Channel + 10 * i;
				}
				return ports;
			}
		}

		public static string FileName(int slot)
		{
			return slot == 2 ? "coop2.cfg" : "coop.cfg";
		}

		public static string PathFor(string root, int slot)
		{
			return Path.Combine(root, FileName(slot));
		}

		// Polish letters to their plain forms, other accents dropped, then
		// plain printable ASCII only - the client shows the name as bytes.
		public static string ToAsciiName(string text)
		{
			text = text ?? "";
			string[,] pairs = {
				{ "ą", "a" }, { "Ą", "A" }, { "ć", "c" }, { "Ć", "C" }, { "ę", "e" }, { "Ę", "E" },
				{ "ł", "l" }, { "Ł", "L" }, { "ń", "n" }, { "Ń", "N" }, { "ó", "o" }, { "Ó", "O" },
				{ "ś", "s" }, { "Ś", "S" }, { "ź", "z" }, { "Ź", "Z" }, { "ż", "z" }, { "Ż", "Z" }
			};
			for (int i = 0; i < pairs.GetLength(0); i++)
			{
				text = text.Replace(pairs[i, 0], pairs[i, 1]);
			}
			string decomposed = text.Normalize(NormalizationForm.FormD);
			StringBuilder builder = new StringBuilder();
			foreach (char c in decomposed)
			{
				if (CharUnicodeInfo.GetUnicodeCategory(c) == UnicodeCategory.NonSpacingMark)
				{
					continue;
				}
				if (c >= 32 && c <= 126)
				{
					builder.Append(c);
				}
			}
			string name = builder.ToString().Replace('=', '-').Trim();
			name = Regex.Replace(name, " {2,}", " ");
			if (name.Length > 80)
			{
				name = name.Substring(0, 80).Trim();
			}
			return name;
		}

		// The client's own check (serverinfo.py __IsValidCoopHost).
		public static bool IsValidHost(string host)
		{
			if (string.IsNullOrWhiteSpace(host) || host.Length > 253)
			{
				return false;
			}
			if (!Regex.IsMatch(host, "^[A-Za-z0-9.-]+$"))
			{
				return false;
			}
			if (Regex.IsMatch(host, "^[0-9.]+$"))
			{
				string[] parts = host.Split('.');
				if (parts.Length != 4)
				{
					return false;
				}
				foreach (string part in parts)
				{
					if (!Regex.IsMatch(part, "^[0-9]{1,3}$") || int.Parse(part, CultureInfo.InvariantCulture) > 255)
					{
						return false;
					}
				}
				return true;
			}
			foreach (string label in host.Split('.'))
			{
				if (label.Length < 1 || label.Length > 63 || !Regex.IsMatch(label, "^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?$"))
				{
					return false;
				}
			}
			return true;
		}

		// What people paste: "http://1.2.3.4/", " 1.2.3.4 ", a domain. Returns
		// the bare host or throws a sentence that says what to type.
		public static string NormalizeHost(string text)
		{
			string value = (text ?? "").Trim();
			if (value.Length == 0)
			{
				throw new CoopException("Wpisz IP albo domenę serwera VPS.");
			}
			if (Regex.IsMatch(value, "^https?://", RegexOptions.IgnoreCase))
			{
				Uri uri;
				if (!Uri.TryCreate(value, UriKind.Absolute, out uri))
				{
					throw new CoopException("Nieprawidłowe IP lub domena.");
				}
				if (!uri.IsDefaultPort || (uri.AbsolutePath != "/" && uri.AbsolutePath != ""))
				{
					throw new CoopException("Wpisz samo IP albo domenę - bez portu i ścieżki.");
				}
				value = uri.Host;
			}
			value = value.TrimEnd('/');
			if (Regex.IsMatch(value, "^[^:]+:[0-9]+$"))
			{
				throw new CoopException("Wpisz samo IP, bez portu (porty są w polach poniżej).");
			}
			if (!IsValidHost(value))
			{
				if (Regex.IsMatch(value, "^[0-9.]+$"))
				{
					throw new CoopException("Nieprawidłowy adres IPv4 (cztery liczby 0-255 oddzielone kropkami, np. 203.0.113.10).");
				}
				throw new CoopException("Nieprawidłowe IP lub nazwa domeny (dozwolone: litery bez polskich znaków, cyfry, kropki i myślniki).");
			}
			return value;
		}

		public static int ParsePort(string text, string label)
		{
			int value;
			if (!int.TryParse((text ?? "").Trim(), out value) || value < 1 || value > 65535)
			{
				throw new CoopException(label + " musi być liczbą od 1 do 65535.");
			}
			return value;
		}

		// Validates everything and returns the server with the file text
		// (ASCII, CRLF). Throws CoopException with a Polish sentence.
		public static CoopServer Create(string name, string host, string auth = "11000", string channel = "13000", string channels = "2")
		{
			if (string.IsNullOrWhiteSpace(name))
			{
				throw new CoopException("Wpisz nazwę serwera.");
			}
			string cleanName = ToAsciiName(name);
			if (cleanName.Length == 0)
			{
				throw new CoopException("Nazwa serwera nie zawiera żadnych obsługiwanych znaków (użyj liter, cyfr i spacji).");
			}
			string cleanHost = NormalizeHost(host);
			int authPort = ParsePort(auth, "Port logowania");
			int channelPort = ParsePort(channel, "Port kanału 1");
			int count;
			if (!int.TryParse((channels ?? "").Trim(), out count) || count < 1 || count > 2)
			{
				throw new CoopException("Liczba kanałów musi wynosić 1 albo 2.");
			}
			if (channelPort + (count - 1) * 10 > 65535)
			{
				throw new CoopException(string.Format("Port kanału 2 wyniósłby {0} (kanał 1 + 10), a maksimum to 65535. Zmniejsz port kanału 1 albo wybierz 1 kanał.", channelPort + 10));
			}
			List<int> channelPorts = new List<int> { channelPort };
			if (count == 2)
			{
				channelPorts.Add(channelPort + 10);
			}
			if (channelPorts.Contains(authPort))
			{
				throw new CoopException(string.Format("Port logowania ({0}) nie może być taki sam jak port kanału ({1}).", authPort, string.Join(" / ", channelPorts)));
			}
			string text = string.Join("\r\n", new string[] {
				"# MT2009 PLUS - serwer VPS (zapisane przez MT2009-Patcher)",
				"name=" + cleanName,
				"host=" + cleanHost,
				"auth=" + authPort,
				"channel=" + channelPort,
				"channels=" + count,
				""
			});
			return new CoopServer { Valid = true, Name = cleanName, Host = cleanHost, Auth = authPort, Channel = channelPort, Channels = count, Text = text };
		}

		// null when the slot is empty; Valid = false when the file is there but
		// the client would ignore it. The same rules as serverinfo.py.
		public static CoopServer Read(string path, int slot = 1)
		{
			if (!File.Exists(path))
			{
				return null;
			}
			CoopServer result = new CoopServer { Valid = false, Slot = slot };
			try
			{
				byte[] bytes = File.ReadAllBytes(path);
				if (bytes.Length > 8192)
				{
					return result;
				}
				Dictionary<string, string> settings = new Dictionary<string, string>();
				string content = Encoding.GetEncoding(28591).GetString(bytes);
				foreach (string raw in Regex.Split(content, "\r\n|\n|\r"))
				{
					string line = raw.Trim();
					if (line.Length == 0 || line.StartsWith("#"))
					{
						continue;
					}
					int at = line.IndexOf('=');
					if (at < 0)
					{
						return result;
					}
					string key = line.Substring(0, at).Trim().ToLowerInvariant();
					if (key.Length == 0 || settings.ContainsKey(key))
					{
						return result;
					}
					settings[key] = line.Substring(at + 1).Trim();
				}
				if (settings.ContainsKey("name"))
				{
					result.Name = settings["name"];
				}
				if (settings.ContainsKey("host"))
				{
					result.Host = settings["host"];
				}
				foreach (string key in new string[] { "name", "host", "auth", "channel", "channels" })
				{
					if (!settings.ContainsKey(key) || settings[key].Length == 0)
					{
						return result;
					}
				}
				int authPort, channelPort, count;
				if (!int.TryParse(settings["auth"], out authPort) || !int.TryParse(settings["channel"], out channelPort) || !int.TryParse(settings["channels"], out count))
				{
					return result;
				}
				result.Auth = authPort;
				result.Channel = channelPort;
				result.Channels = count;
				if (!IsValidHost(settings["host"]))
				{
					return result;
				}
				if (authPort < 1 || authPort > 65535 || channelPort < 1 || channelPort > 65535)
				{
					return result;
				}
				if (count < 1 || count > MaxChannels || channelPort + (count - 1) * 10 > 65535)
				{
					return result;
				}
				if (settings.ContainsKey("panel"))
				{
					result.Panel = settings["panel"];
				}
				result.Valid = true;
			}
			catch
			{
			}
			return result;
		}

		public static string Save(string root, int slot, CoopServer server)
		{
			string path = PathFor(root, slot);
			if (File.Exists(path))
			{
				try
				{
					File.SetAttributes(path, FileAttributes.Normal);
				}
				catch
				{
				}
			}
			File.WriteAllText(path, server.Text, Encoding.ASCII);
			return path;
		}

		public static void Remove(string root, int slot)
		{
			string path = PathFor(root, slot);
			if (File.Exists(path))
			{
				try
				{
					File.SetAttributes(path, FileAttributes.Normal);
				}
				catch
				{
				}
				File.Delete(path);
			}
		}

		// The servers whose status the patcher shows: the valid coop.cfg and
		// coop2.cfg, or the built-in localhost when there is none.
		public static List<CoopServer> Discover(string root)
		{
			List<CoopServer> list = new List<CoopServer>();
			for (int slot = 1; slot <= 2; slot++)
			{
				CoopServer server = Read(PathFor(root, slot), slot);
				if (server != null && server.Valid)
				{
					list.Add(server);
				}
			}
			if (list.Count == 0)
			{
				list.Add(Localhost());
			}
			return list;
		}
	}
}
