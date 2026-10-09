using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace N2_Patcher.Core
{
	// MT2009_PLUS_CH34_AUTO_V1: "channels=" of coop.cfg / coop2.cfg from the
	// server itself, so CH3/CH4 appear in the game's list without anybody
	// editing the file.
	//
	// The Seban panel publishes (app.py public_channels, no login):
	//   GET <panel>/klient/dbdata/channels.json   (also /klient/channels.json)
	//     {"format": "MT2009_PLUS_CH34_AUTO_V1", "channels": 1..4, "ports": [13000, 13010, ...]}
	// next to the dbdata manifest, so the same addresses (DbDataSync.CandidateUrls:
	// panel=, 7790, login + 6790, port 80) and the same gate (/klient/dbdata/) work.
	//
	// The client's serverinfo.py takes up to 4 channels from 2.0.59 on; an older
	// one drops the whole coop.cfg for channels > 2, so it gets 2 - as does any
	// failure (no panel, no CLIENT_VERSION, a strange answer). Only the
	// "channels=" line is rewritten; the ports are the file's own (a NAT block
	// publishes the channels under other numbers than the server's "ports").
	// Nothing here throws and nothing waits for the game.
	public class ChannelSyncResult
	{
		public int Slot;
		public int Before;
		public int Channels = ChannelSync.SafeChannels;
		public int? ServerChannels;
		public string ClientVersion;
		public string Url = "";
		public bool Changed;
		public List<string> Log = new List<string>();
	}

	public static class ChannelSync
	{
		public const string Format = "MT2009_PLUS_CH34_AUTO_V1";
		public const string FileName = "channels.json";
		// the first client whose serverinfo.py lists CH3/CH4 from coop.cfg
		public const string MinClientVersion = "2.0.59";
		public const int SafeChannels = 2;
		public const int MaxChannels = 4;
		public const long MaxBytes = 4096;

		// The dbdata manifest's addresses with channels.json in place of
		// manifest.json. DbDataManifest=off keeps the addresses worked out
		// from the server (it switches off the pack, not this).
		public static List<string> CandidateUrls(CoopServer server, string dbdataSetting)
		{
			List<string> manifests = DbDataSync.CandidateUrls(server, dbdataSetting) ?? DbDataSync.CandidateUrls(server, "");
			List<string> list = new List<string>();
			foreach (string manifest in manifests)
			{
				string url = ChannelsUrlOf(manifest);
				if (url != null && !list.Contains(url))
				{
					list.Add(url);
				}
			}
			return list;
		}

		// ".../klient/dbdata/manifest.json" -> ".../klient/dbdata/channels.json"
		public static string ChannelsUrlOf(string manifestUrl)
		{
			int slash = (manifestUrl ?? "").LastIndexOf('/');
			if (slash < 0 || !manifestUrl.EndsWith(".json", StringComparison.OrdinalIgnoreCase))
			{
				return null;
			}
			return manifestUrl.Substring(0, slash + 1) + FileName;
		}

		// 1..4, or null when it is not an answer of this format.
		public static int? ParseChannels(byte[] body)
		{
			try
			{
				JObject o = JObject.Parse(Encoding.UTF8.GetString(body));
				if ((string)o["format"] != Format || o["channels"] == null || o["channels"].Type != JTokenType.Integer)
				{
					return null;
				}
				int count = (int)o["channels"];
				return count >= 1 && count <= MaxChannels ? count : (int?)null;
			}
			catch
			{
				return null;
			}
		}

		// The count the client should list: the server's one for a client that
		// takes it, otherwise 2.
		public static int Wanted(string clientVersion, int? serverChannels)
		{
			if (serverChannels == null || clientVersion == null)
			{
				return SafeChannels;
			}
			try
			{
				if (DbDataSync.CompareVersions(clientVersion, MinClientVersion) < 0)
				{
					return SafeChannels;
				}
			}
			catch
			{
				return SafeChannels;
			}
			return Math.Max(1, Math.Min(MaxChannels, serverChannels.Value));
		}

		// No more than the ports allow: the last channel <= 65535, none on the login port.
		public static int Fit(CoopServer server, int wanted)
		{
			int count = wanted;
			while (count > 1)
			{
				bool ok = server.Channel + (count - 1) * 10 <= 65535;
				for (int i = 1; ok && i < count; i++)
				{
					ok = server.Channel + 10 * i != server.Auth;
				}
				if (ok)
				{
					break;
				}
				count--;
			}
			return count;
		}

		// The file's text with its "channels=" line set to count; everything
		// else (comments, panel=, the line ends) as it was. null = no such line.
		public static string WithChannels(string text, int count)
		{
			Regex line = new Regex("^([ \\t]*channels[ \\t]*=)[^\\r\\n]*", RegexOptions.Multiline | RegexOptions.IgnoreCase);
			if (!line.IsMatch(text))
			{
				return null;
			}
			return line.Replace(text, "${1}" + count, 1);
		}

		// The first answer in order of the candidates (all asked at once), or null.
		public static int? Fetch(List<string> candidates, DbDataSync.Fetcher fetch, int timeoutMs, ChannelSyncResult result)
		{
			if (candidates == null || candidates.Count == 0)
			{
				return null;
			}
			Task<byte[]>[] tasks = candidates.Select(url => Task.Run(() => fetch(url, timeoutMs, MaxBytes))).ToArray();
			try
			{
				Task.WaitAll(tasks, timeoutMs + 1500);
			}
			catch (AggregateException)
			{
			}
			for (int i = 0; i < tasks.Length; i++)
			{
				if (tasks[i].Status != TaskStatus.RanToCompletion)
				{
					result.Log.Add(candidates[i] + ": " + (tasks[i].Exception != null ? tasks[i].Exception.GetBaseException().Message : "brak odpowiedzi"));
					continue;
				}
				int? count = ParseChannels(tasks[i].Result);
				if (count == null)
				{
					result.Log.Add(candidates[i] + ": to nie jest odpowiedź " + Format);
					continue;
				}
				result.Url = candidates[i];
				return count;
			}
			return null;
		}

		// One coop file (slot 1 / 2) of the client in root. Never throws.
		public static ChannelSyncResult Run(string root, CoopServer server, string dbdataSetting, DbDataSync.Fetcher fetch, int timeoutMs = 4000)
		{
			ChannelSyncResult result = new ChannelSyncResult { Slot = server == null ? 0 : server.Slot };
			try
			{
				if (server == null || server.Slot == 0)
				{
					return result;
				}
				string path = CoopServer.PathFor(root, server.Slot);
				result.Before = server.Channels;
				result.ClientVersion = DbDataSync.ReadClientVersion(root);
				result.ServerChannels = Fetch(CandidateUrls(server, dbdataSetting), fetch, timeoutMs, result);
				result.Channels = Fit(server, Wanted(result.ClientVersion, result.ServerChannels));
				result.Log.Add(string.Format("{0}: klient {1}, serwer {2} -> channels={3}", CoopServer.FileName(server.Slot),
					result.ClientVersion ?? "(brak CLIENT_VERSION)", result.ServerChannels.HasValue ? result.ServerChannels.Value.ToString() : "(brak odpowiedzi)", result.Channels));
				if (result.Channels == server.Channels || !File.Exists(path))
				{
					return result;
				}
				// the file as read just now, so a change made meanwhile (the VPS window) is not undone
				CoopServer now = CoopServer.Read(path, server.Slot);
				if (now == null || now.Host != server.Host || now.Channel != server.Channel || now.Auth != server.Auth)
				{
					result.Log.Add("plik zmienił się w międzyczasie - bez zmian");
					return result;
				}
				string text = WithChannels(File.ReadAllText(path, Encoding.GetEncoding(28591)), result.Channels);
				if (text == null)
				{
					return result;
				}
				try
				{
					File.SetAttributes(path, FileAttributes.Normal);
				}
				catch
				{
				}
				DbDataSync.WriteAtomic(path, Encoding.GetEncoding(28591).GetBytes(text));
				result.Changed = true;
				result.Log.Add(string.Format("zapisano channels={0} (było {1})", result.Channels, result.Before));
			}
			catch (Exception exc)
			{
				result.Log.Add("błąd: " + exc.Message);
			}
			return result;
		}
	}
}
