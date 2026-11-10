using MT2009Yohara.Core;
using N2_Patcher.Model;
using System;
using System.Diagnostics;
using System.IO;

namespace MT2009Yohara
{
	// "--cli": the same update without a window (see Entry).
	internal static class Cli
	{
		public static int Run(string[] args)
		{
			PatcherLog.Echo = true;
			bool full = Array.IndexOf(args, "--napraw") >= 0;
			bool noSelf = Array.IndexOf(args, "--bez-samoaktualizacji") >= 0;
			bool play = Array.IndexOf(args, "--graj") >= 0;
			PatcherLog.Write("MT2009 PLUS - Yohara Patcher " + typeof(Cli).Assembly.GetName().Version + " (--cli)");
			UpdateOptions options = Entry.Options(full);
			if (noSelf)
			{
				options.SelfPath = null;
			}
			int lastPercent = -1;
			UpdateResult result = new Updater(new WebHttp(), PatcherLog.Write).Run(options, p => {
				int percent = p.Phase == Phase.Checking
					? (p.Total > 0 ? p.Done * 100 / p.Total : 0)
					: (p.BytesTotal > 0 ? (int)(p.BytesDone * 100 / p.BytesTotal) : 0);
				if (percent / 10 != lastPercent / 10)
				{
					lastPercent = percent;
					PatcherLog.Write(string.Format("  {0}: {1}%", p.Text, percent));
				}
			});
			PatcherLog.Write(string.Format("WYNIK: {0} | wersja {1} | kanał {2} | sprawdzono {3} | pobrano {4} ({5:0.0} MB) | usunięto {6} | błędy {7}",
				result.State, result.Version, result.Channel, result.Checked, result.Downloaded, result.Bytes / 1048576.0, result.Deleted, result.Failed.Count));
			PatcherLog.Write(result.Message ?? "");
			if (!string.IsNullOrEmpty(result.Detail))
			{
				PatcherLog.Write(result.Detail);
			}
			switch (result.State)
			{
				case UpdateState.PatcherUpdated:
					try
					{
						Updater.SwapSelf(Entry.ExePath, result.NewPatcherPath);
						PatcherLog.Write("patcher podmieniony na " + result.NewPatcherVersion + " - uruchom go ponownie");
					}
					catch (Exception e)
					{
						PatcherLog.Write("nie udało się podmienić patchera: " + e.Message);
						return 1;
					}
					return 3;
				case UpdateState.Refused:
					return 2;
				case UpdateState.UpToDate:
				case UpdateState.Updated:
					if (play)
					{
						string exe = Path.Combine(Entry.Folder, Config.GetStartFile());
						Entry.StartExternal(exe);
					}
					return 0;
				default:
					return 1;
			}
		}
	}
}
